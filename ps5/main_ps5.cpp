// DBZ Budokai 3 HD Collection - PS5 host.
//
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Adapted from the PS5 host of holdmysocks/mcla-recomp (ps5/game/main_ps5.cpp,
// GPL-3.0-or-later), which runs another ReXGlue-recompiled game on jailbroken
// PS5 consoles. See ps5/README.md.
//
// The desktop host (src/main.cpp) goes through rex::ReXApp, which is built
// around a window, the ImGui launcher and an event loop. None of that exists
// on the console, so this drives rex::Runtime directly, in the order ReXApp
// does (and with the same DBZ3 steps Dbz3App adds to it):
//
//   settings      dbz3_user.toml from /data/dbz3 (same file and cvars as PC)
//   presentation  SDL's offscreen video driver standing for the display; the
//                 Vulkan presenter makes a VK_KHR_display surface on it
//   runtime       Setup with the console's pad and audio drivers
//   game data     /data/dbz3/game (default.xex + us/ and/or eu/), mounted
//                 through dbz3::RelocateGameData so the region device and the
//                 AFS mod overrides work exactly as on PC
//   launch        guarded mods (roster.toml), XEX, guest heap, main thread
//
// The launcher is not there: the game boots straight away (what the PC build
// does with dbz3_skip_launcher=true). Settings are edited in the TOML file.
//
// Build: ps5/build_game.sh (called by ps5/make_ps5.sh) with -DDBZ3_TITLE for
// an installable title. DBZ3_PLAY selects a build for playing (log to a file
// on the console, warnings only) rather than one that waits for
// ps5/title_log_client.py.

#include <rex/image_info.h>

// Each region's codegen defines PPCImageConfig (a single-region build: US
// from generated/, EU from generated_eu/ with -DDBZ3_EU_VARIANT). Declared
// here instead of including the generated headers, as src/main.cpp does.
extern const rex::PPCImageInfo PPCImageConfig;

#include <signal.h>
#include <ucontext.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <memory>
#include <string>
#include <thread>

#include <rex/audio/audio_driver.h>
#include <rex/audio/sdl/sdl_audio_system.h>
#include <rex/cvar.h>
#include <rex/input/device_assignment.h>
#include <rex/input/input_system.h>
#include <rex/input/nop/nop_input_driver.h>
#include <rex/kernel/crt/heap.h>
#include <rex/kernel/init.h>
#include <rex/logging.h>
#include <rex/ppc/function.h>
#include <rex/runtime.h>
#include <rex/system/gpu_plugin.h>
#include <rex/system/kernel_state.h>
#include <rex/system/xthread.h>
#include <rex/thread.h>
#include <rex/ui/presenter.h>
#include <rex/ui/window.h>
#include <rex/ui/windowed_app_context_sdl.h>

#include "launcher/settings.h"
#include "region.h"
#ifndef DBZ3_EU_VARIANT
#include "roster_ext.h"
#endif

// As a title (-DDBZ3_TITLE) the log goes to a file on the console (play
// builds) or over a TCP connection from the PC (test builds).
#include "title_log.h"
#include "log_fd_sink.h"
#ifdef DBZ3_TITLE
#include "ps5_audio.h"
#include "ps5_pad_input.h"
#endif

#ifndef DBZ3_PS5_ROOT
#define DBZ3_PS5_ROOT "/data/dbz3"
#endif

REXCVAR_DECLARE(uint32_t, rexcrt_heap_size_mb);

// The console's shell draws its launch splash over a title until the title
// asks for it to be hidden.
#ifdef DBZ3_TITLE
extern "C" int sceSystemServiceHideSplashScreen(void);
#endif

// The Xenos GPU plugin's factory. On the other platforms the plugin is a
// shared library found by name at run time; here it is linked in.
extern "C" rex::system::IGraphicsSystem* rex_gpu_create(uint32_t abi_version,
                                                        const rex::system::GpuCreateInfo* info);

// External kernel imports the codegen refers to (as in src/main.cpp).
REX_EXTERN(__imp__IoInvalidDeviceRequest);
REX_EXTERN(__imp__ObReferenceObject);
REX_EXTERN(__imp__IoDeleteDevice);
REX_EXTERN(__imp__IoCompleteRequest);
REX_EXTERN(__imp__NtWriteFileGather);
REX_EXTERN(__imp__RtlUpcaseUnicodeChar);
REX_EXTERN(__imp__ObIsTitleObject);
REX_EXTERN(__imp__IoCheckShareAccess);
REX_EXTERN(__imp__IoSetShareAccess);
REX_EXTERN(__imp__IoRemoveShareAccess);
REX_EXTERN(__imp__XeCryptBnQwBeSigVerify);
REX_EXTERN(__imp__XeKeysGetKey);
REX_EXTERN(__imp__XeCryptRotSumSha);

namespace {

// --- Early crash reporter ---------------------------------------------------------
//
// Installed from a constructor that runs ahead of the runtime's static objects.
// Prints the signal, fault address and instruction pointer straight to the log
// and exits. The runtime's own fault handler takes over SIGSEGV/SIGBUS/SIGILL
// later and hands a fault nobody claims back to this one.

void EarlyWrite(const char* text) { (void)!write(g_dbz3_log_fd, text, std::strlen(text)); }

void EarlyHex(const char* label, uint64_t value) {
  char buffer[96];
  static const char digits[] = "0123456789abcdef";
  size_t n = 0;
  while (*label) buffer[n++] = *label++;
  buffer[n++] = '0';
  buffer[n++] = 'x';
  for (int shift = 60; shift >= 0; shift -= 4) buffer[n++] = digits[(value >> shift) & 0xF];
  buffer[n++] = '\n';
  (void)!write(g_dbz3_log_fd, buffer, n);
}

int EarlyAnchor() { return 0; }

void EarlyCrash(int signal_number, siginfo_t* info, void* context) {
  EarlyWrite("CRASH\n");
  EarlyHex("  signal ", static_cast<uint64_t>(signal_number));
  EarlyHex("  fault address ", reinterpret_cast<uint64_t>(info->si_addr));
  // The machine context is 0x40 bytes into the signal context on firmware
  // 13.42, whatever the SDK's ucontext_t says (found by mcla-recomp).
  auto* machine = reinterpret_cast<mcontext_t*>(static_cast<uint8_t*>(context) + 0x40);
  const uint64_t anchor = reinterpret_cast<uint64_t>(&EarlyAnchor);
  EarlyHex("  instruction pointer ", static_cast<uint64_t>(machine->mc_rip));
  EarlyHex("  address of EarlyAnchor ", anchor);
  EarlyHex("  rsp ", static_cast<uint64_t>(machine->mc_rsp));
  // Code addresses on the stack, for a rough backtrace (symbolise on the PC
  // against the linked ELF).
  const uint64_t* stack = reinterpret_cast<const uint64_t*>(machine->mc_rsp);
  const uint64_t low = anchor > 0x20000000 ? anchor - 0x20000000 : 0x1000;
  int printed = 0;
  for (int i = 0; i < 1024 && printed < 16; ++i) {
    const uint64_t word = stack[i];
    if (word > low && word < anchor + 0x20000000) {
      EarlyHex("  stack code pointer ", word);
      ++printed;
    }
  }
  _exit(100 + signal_number);
}

void ReportExit() { EarlyWrite("EXIT: the process is leaving through exit()\n"); }

__attribute__((constructor(101))) void InstallEarlyCrashReporter() {
  // Files that sit next to the executable on PC (dbz3_user.toml, mods/,
  // mods_nativos/, user_data/) live in DBZ3_PS5_ROOT: a title's own folder is
  // read-only. The PS5 runtime patch reads this in GetExecutablePath().
  setenv("REX_EXECUTABLE_PATH", DBZ3_PS5_ROOT "/dbz3", 1);
  Dbz3TitleLogConnect();
  atexit(ReportExit);
  struct sigaction action;
  std::memset(&action, 0, sizeof action);
  action.sa_sigaction = EarlyCrash;
  action.sa_flags = SA_SIGINFO;
  sigemptyset(&action.sa_mask);
  for (int signal_number : {SIGSEGV, SIGBUS, SIGILL, SIGABRT, SIGFPE, SIGSYS, SIGTRAP, SIGTERM,
                            SIGHUP, SIGQUIT, SIGPIPE, SIGXFSZ}) {
    sigaction(signal_number, &action, nullptr);
  }
}

void Line(const char* format, ...) {
  char text[512];
  va_list args;
  va_start(args, format);
  std::vsnprintf(text, sizeof text - 1, format, args);
  va_end(args);
  const size_t length = std::strlen(text);
  text[length] = '\n';
  (void)!write(g_dbz3_log_fd, text, length + 1);
}

// Printed before an operation, so the last "NEXT" line names what was running
// if the output stops.
#define NEXT(...) Line("NEXT " __VA_ARGS__)

[[noreturn]] void Finish(const char* what, int code) {
  Line("dbz3-ps5 stops: %s", what);
  rex::FlushLogging();
  std::fflush(stdout);
  // No teardown: guest threads may still be running.
  _exit(code);
}

// --- Audio ----------------------------------------------------------------------
//
// The game must always get an audio driver. On the console the pad library's
// sibling, sceAudioOut, is used (ps5_audio.h); if that port cannot be opened
// it falls back to SDL and then to a silent driver that paces the guest at
// the real-time rate (after mcla-recomp's src/audio_fallback.cpp).

constexpr auto kFramePeriod = std::chrono::nanoseconds(256ull * 1'000'000'000ull / 48000ull);

class SilentAudioDriver : public rex::audio::AudioDriver {
 public:
  SilentAudioDriver(rex::memory::Memory* memory, rex::thread::Semaphore* semaphore)
      : AudioDriver(memory), semaphore_(semaphore), worker_([this] { Run(); }) {}
  ~SilentAudioDriver() override {
    running_ = false;
    worker_.join();
  }
  void SubmitFrame(uint32_t) override { ++pending_; }

 private:
  void Run() {
    auto next = std::chrono::steady_clock::now();
    while (running_) {
      next += kFramePeriod;
      std::this_thread::sleep_until(next);
      if (pending_.load() > 0) {
        --pending_;
        semaphore_->Release(1, nullptr);
      }
    }
  }
  rex::thread::Semaphore* semaphore_;
  std::atomic<int> pending_{0};
  std::atomic<bool> running_{true};
  std::thread worker_;
};

class Ps5AudioSystem : public rex::audio::sdl::SDLAudioSystem {
 public:
  using SDLAudioSystem::SDLAudioSystem;

  rex::X_STATUS CreateDriver(size_t index, rex::thread::Semaphore* semaphore,
                             rex::audio::AudioDriver** out_driver) override {
#ifdef DBZ3_TITLE
    {
      auto driver = std::make_unique<Ps5AudioDriver>(memory_, semaphore);
      if (driver->Initialize()) {
        platform_driver_ = driver.release();
        *out_driver = platform_driver_;
        return X_STATUS_SUCCESS;
      }
      REXLOG_WARN("audio: the console's audio port did not open, trying SDL");
    }
#endif
    if (SDLAudioSystem::CreateDriver(index, semaphore, out_driver) == X_STATUS_SUCCESS) {
      return X_STATUS_SUCCESS;
    }
    REXLOG_WARN("audio: no usable output device, running silent");
    *out_driver = new SilentAudioDriver(memory_, semaphore);
    return X_STATUS_SUCCESS;
  }

  void DestroyDriver(rex::audio::AudioDriver* driver) override {
    if (driver == platform_driver_) {
      platform_driver_ = nullptr;
      delete driver;
      return;
    }
    if (auto* silent = dynamic_cast<SilentAudioDriver*>(driver)) {
      delete silent;
      return;
    }
    SDLAudioSystem::DestroyDriver(driver);
  }

 private:
  rex::audio::AudioDriver* platform_driver_ = nullptr;
};

std::unique_ptr<rex::system::IAudioSystem> CreatePs5AudioSystem(
    rex::runtime::FunctionDispatcher* function_dispatcher) {
  return std::make_unique<Ps5AudioSystem>(function_dispatcher);
}

#define DBZ3_STRINGIZE_(x) #x
#define DBZ3_STRINGIZE(x) DBZ3_STRINGIZE_(x)

}  // namespace

int main() {
  setvbuf(stdout, nullptr, _IONBF, 0);
  Line("dbz3-ps5 starts, pid %d", getpid());

  const std::filesystem::path root = DBZ3_PS5_ROOT;
  const std::filesystem::path game_root = root / "game";
  std::error_code ec;

  NEXT("check the game folder %s", game_root.c_str());
  if (!std::filesystem::is_regular_file(game_root / "default.xex", ec)) {
    Finish("default.xex is not in " DBZ3_PS5_ROOT "/game (see docs/PS5.md)", 2);
  }

  NEXT("initialise cvars and logging");
  char program[] = "dbz3";
  char* arguments[] = {program, nullptr};
  rex::cvar::Init(1, arguments);
  rex::InitLoggingEarly();
  rex::LogConfig log_config;
  log_config.log_to_console = false;
  log_config.extra_sinks.push_back(std::make_shared<Dbz3FdSink>(g_dbz3_log_fd));
#ifdef DBZ3_LOG_LEVEL
  log_config.default_level = spdlog::level::from_str(DBZ3_LOG_LEVEL);
#endif
  log_config.flush_level = spdlog::level::trace;
  rex::InitLogging(log_config);

#ifdef DBZ3_TITLE
  // The Vulkan driver reports on standard error, which in a title goes
  // nowhere: point the C library's stderr at the log.
  if (FILE* log_stream = fdopen(g_dbz3_log_fd, "w")) {
    setvbuf(log_stream, nullptr, _IOLBF, 0);
    stderr = log_stream;
  }
#endif

  // The user's settings: the same dbz3_user.toml as on PC, in DBZ3_PS5_ROOT.
  NEXT("load %s", dbz3::settings::UserSettingsPath().c_str());
  try {
    dbz3::settings::LoadUserSettings();
    dbz3::settings::ApplyUserSettingsToSdk();
  } catch (const std::exception& e) {
    Line("settings not applied (%s); defaults", e.what());
  }
  // What the console needs whatever the settings say.
  rex::cvar::SetFlagByName("gpu_backend", "vulkan");
  rex::cvar::SetFlagByName("input_backend", "sdl");
  rex::cvar::SetFlagByName("video_driver", "offscreen");
  // No controller mapping file on the console: an exception from the lookup
  // would otherwise end the title (mcla-recomp, ps5/game/main_ps5.cpp).
  rex::cvar::SetFlagByName("hid_mappings_file", "");
  rex::cvar::SetFlagByName("fullscreen", "false");
  rex::cvar::SetFlagByName("mnk_mode", "false");
  // Shared-memory tuning measured on the console by mcla-recomp
  // (docs/ps5-port-plan.md there): watch guest physical memory coarsely, do
  // not watch pages rewritten every frame, trust the write watches instead of
  // re-uploading everything each frame, submit once per frame.
#ifndef DBZ3_WATCH_GRANULARITY
#define DBZ3_WATCH_GRANULARITY 0
#endif
#ifndef DBZ3_REQUEST_GRANULARITY_LOG2
#define DBZ3_REQUEST_GRANULARITY_LOG2 16
#endif
#ifndef DBZ3_HOT_PAGE_FAULTS
#define DBZ3_HOT_PAGE_FAULTS 4
#endif
  rex::cvar::SetFlagByName("physical_watch_granularity", DBZ3_STRINGIZE(DBZ3_WATCH_GRANULARITY));
  rex::cvar::SetFlagByName("shared_memory_request_granularity_log2",
                           DBZ3_STRINGIZE(DBZ3_REQUEST_GRANULARITY_LOG2));
  rex::cvar::SetFlagByName("shared_memory_hot_page_faults", DBZ3_STRINGIZE(DBZ3_HOT_PAGE_FAULTS));
  rex::cvar::SetFlagByName("shared_memory_hot_page_ms", "10000");
  rex::cvar::SetFlagByName("shared_memory_invalidation_pages_log2", "4");
  rex::cvar::SetFlagByName("clear_memory_page_state", "false");
  rex::cvar::SetFlagByName("vulkan_submit_on_primary_buffer_end", "false");

  NEXT("SDL application context on the offscreen video driver");
  rex::ui::SDLWindowedAppContext app_context;
  if (!app_context.Initialize()) {
    Finish("the SDL application context did not initialise", 9);
  }
  NEXT("create the Xenos graphics system (Vulkan backend)");
  rex::system::GpuCreateInfo gpu_create_info;
  gpu_create_info.struct_size = sizeof gpu_create_info;
  gpu_create_info.backend = "vulkan";
  std::unique_ptr<rex::system::IGraphicsSystem> graphics(
      rex_gpu_create(rex::system::kGpuPluginAbiVersion, &gpu_create_info));
  if (!graphics) {
    Finish("the GPU plugin returned no graphics system", 7);
  }
  NEXT("SetupPresentation with the application context");
  if (XFAILED(graphics->SetupPresentation(&app_context)) || !graphics->presenter()) {
    Finish("graphics setup failed", 8);
  }
  NEXT("create and open the window, attach the presenter");
  auto window = rex::ui::Window::Create(app_context, "dbz3", 1280, 720);
  if (!window || !window->Open()) {
    Finish("no window", 10);
  }
  window->SetPresenter(graphics->presenter());
#ifdef DBZ3_TITLE
  Line("sceSystemServiceHideSplashScreen returned 0x%08X",
       static_cast<unsigned>(sceSystemServiceHideSplashScreen()));
#endif

  const std::filesystem::path user_root = dbz3::settings::UserDataRoot();
  const std::filesystem::path cache_root = user_root / "cache";
  std::filesystem::create_directories(cache_root, ec);

  NEXT("construct rex::Runtime (game %s, user data %s)", game_root.c_str(), user_root.c_str());
  auto runtime = std::make_unique<rex::Runtime>(game_root, user_root, std::filesystem::path(),
                                                cache_root, std::filesystem::path());
  runtime->set_app_context(&app_context);
  runtime->set_display_window(window.get());

  rex::RuntimeConfig config;
  config.audio_factory = &CreatePs5AudioSystem;
  config.kernel_init = rex::kernel::InitializeKernel;
  config.graphics = std::move(graphics);
#ifdef DBZ3_TITLE
  // The console's own pad library (ps5_pad_input.h): SDL has no gamepad
  // backend here. Without a controller an idle one is kept present so the
  // game does not wait for one forever.
  config.input_factory = [](bool) -> std::unique_ptr<rex::system::IInputSystem> {
    auto input = std::make_unique<rex::input::InputSystem>(nullptr);
    auto pad = std::make_unique<Ps5PadInputDriver>();
    if (pad->Setup() == rex::X_STATUS(0)) {
      input->AddDriver(std::move(pad));
    } else {
      input->AddDriver(std::make_unique<rex::input::nop::NopInputDriver>(nullptr, 0));
    }
    input->SetDeviceAssignment(std::make_unique<rex::input::SlotAssignment>());
    return input;
  };
#else
  config.input_factory = REX_INPUT_BACKEND(rex::input::CreateDefaultInputSystem);
#endif

  rex::PPCImageInfo image = PPCImageConfig;
  NEXT("Runtime::Setup (guest memory, function table, kernel state, file systems)");
  auto status = runtime->Setup(image, std::move(config));
  if (XFAILED(status)) {
    Line("Runtime::Setup failed: %08X", static_cast<unsigned>(status));
    Finish("setup failed", 3);
  }
  if (image.register_modules) {
    image.register_modules(runtime->kernel_state());
  }
  if (runtime->input_system()) {
    static_cast<rex::input::InputSystem*>(runtime->input_system())->AttachWindow(window.get());
  }

  // The game drive as Dbz3App::OnConfigurePaths/OnPreLaunchModule leave it:
  // game:\ on the data folder, game:\us served from us/ or eu/ by dbz3_region,
  // AFS entries and whole files overridden from /data/dbz3/mods.
  dbz3::SetEffectiveGameRoot(game_root);
  NEXT("mount the game data (region %s)", dbz3::settings::ResolveRegion(game_root).c_str());
  if (!dbz3::RelocateGameData(game_root)) {
    Line("RelocateGameData failed; the runtime's own game:\\ mount is used");
  }

  NEXT("Runtime::LoadXexImage game:\\default.xex");
  status = runtime->LoadXexImage("game:\\default.xex");
  if (XFAILED(status)) {
    Line("LoadXexImage failed: %08X", static_cast<unsigned>(status));
    Finish("XEX load failed (is it the executable this build was recompiled from?)", 4);
  }
  if (image.rexcrt_heap) {
    if (!rex::kernel::crt::InitHeap(REXCVAR_GET(rexcrt_heap_size_mb), runtime->memory())) {
      Finish("guest heap creation failed", 5);
    }
  }
  // Dbz3App::OnPostSetup.
  rex::cvar::SetFlagByName("gpu_allow_invalid_fetch_constants", "true");
  dbz3::settings::ApplyRuntimeSettingsToSdk(false);
  rex::cvar::SetFlagByName("vsync", "false");

  // Dbz3App::OnPreLaunchModule.
#ifndef DBZ3_EU_VARIANT
  dbz3::roster::GuardGeneratedMod();
#endif

  auto launch = [&runtime]() -> rex::system::object_ref<rex::system::XThread> {
    auto main_thread = runtime->PrepareModuleLaunch();
    if (!main_thread) return main_thread;
    if (auto* gs = runtime->graphics_system()) {
      if (const uint32_t title_id = runtime->kernel_state()->title_id()) {
        gs->InitializeShaderStorage(runtime->cache_root(), title_id, true);
      }
    }
#ifndef DBZ3_EU_VARIANT
    dbz3::roster::ApplyAtLaunch(runtime->memory());
#endif
    main_thread->Resume();
    return main_thread;
  };

  NEXT("launch the main guest thread");
  auto main_thread = launch();
  if (!main_thread) {
    Finish("could not create the main guest thread", 6);
  }
  Line("PASS game running");

  // As Dbz3App::OnGuestThreadExit: the main thread ends on a module
  // transition, and the module is launched again.
  std::thread watcher([&runtime, &app_context, main_thread, &launch]() mutable {
    for (int relaunches = 0;; ++relaunches) {
      main_thread->Wait(0, 0, 0, nullptr);
      REXLOG_WARN("dbz3-ps5: the main guest thread exited; relaunching the module");
      if (relaunches >= 8) break;
      main_thread = runtime->LaunchModule();
      if (!main_thread) break;
    }
    app_context.CallInUIThread([&app_context]() { app_context.QuitFromUIThread(); });
  });
  watcher.detach();

  app_context.RunMainMessageLoop();
  Finish("the message loop ended", 0);
}
