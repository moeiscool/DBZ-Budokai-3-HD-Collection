# PLAN_LINUX — Porting DBZ Budokai 3 HD Collection to Linux

> Strategy for porting the project to Linux, based on a real audit of the code
> (AGENTS §14.21/§3.4 + platform sweep 2026-08-28). The SDK (derived from
> Xenia) is already multiplatform; the work is in `src/` (launcher) and in
> validating Vulkan as the game backend.
>
> **Status (2026-10):** Linux shipped (see `docs/LINUX.md`). The same
> portability work is the basis of the jailbroken-PS5 build (`docs/PS5.md`).

---

## 1. Viability (verdict)

**HIGH.** The SDK (`rexglue-sdk-0.10`) already has:
- An explicit platform layer: `REX_PLATFORM_WIN32 / LINUX / MAC` and pairs of
  `*_win.cpp` / `*_posix.cpp` files (selected by CMake).
- **Vulkan backend ON by default on Linux** (`REXGLUE_USE_D3D12=OFF,
  REXGLUE_USE_VULKAN=ON` in the root CMake); D3D12 is Windows-only.
- SDL3 input/audio (multiplatform), `std::filesystem` filesystem + abstracted
  `FileHandle` (Win32FileHandle vs PosixFileHandle), SEH/POSIX exceptions,
  sockets, mapped memory, DLL/so, etc. — all with their posix pair.
- The game's root CMake already has `WIN32` vs `UNIX` branches.

The real bottleneck was in `src/` (launcher): 6 files with unguarded Win32
APIs. **Phase 1.1.1 already guarded them** (see §3). What remains is
functional (dialogs, spawning, zips) and validating Vulkan as the game backend.

---

## 2. Platform map (audit 2026-08-28)

### 2.1 `src/` — Windows-specific code (before 1.1.1)

| File | Win32 API | State after 1.1.1 |
|---|---|---|
| `src/main.cpp` | `SetUnhandledExceptionFilter`, `CreateFileA`, `MessageBoxA`, `RtlCaptureStackBackTrace`, `OutputDebugStringA` | the crash handler was already Win32-only; `OutputDebugStringA` → no-op outside Windows; portable pre-flight |
| `src/launcher/settings.cpp` | `CryptAcquireContext/CALG_MD5`, `CreateDXGIFactory1/EnumAdapters1`, `EnumDisplaySettingsW`, `WideCharToMultiByte` | **portable MD5 written** (drops CryptoAPI); DXGI guarded with a "medium" tier fallback; refresh already guarded |
| `src/launcher/launcher_state.cpp` | `CoInitializeEx`, `IFileOpenDialog`, `SHCreateItemFromParsingName`, `MultiByteToWideChar` | COM dialogs and UTF-16 guarded; "cancelled" fallback |
| `src/launcher/mod_pipeline.cpp` | `CreateProcessW`, `CreatePipe`, `ReadFile`, `WaitForSingleObject` | guarded; fallback with a clear error |
| `src/mods.cpp` | PowerShell `Expand-Archive` (via `CreateProcessW`) | already had an `#else` fallback (unsupported) |
| `src/region.cpp`, `src/ingame/menu.cpp`, `i18n.*` | — | multiplatform (std::filesystem, ImGui, data) |

### 2.2 SDK — subsystems (summary)

| Subsystem | Linux | Notes |
|---|---|---|
| core (base) | ✅ `*_posix` | threading/clock/seh/memory/dynlib/filesystem/exception/socket/system |
| filesystem | ✅ | `std::filesystem` + `FileHandle` (Win/Posix) |
| graphics | ✅ **Vulkan** | D3D12 Windows-only; Vulkan experimental and slow (perf challenge) |
| ui | ✅ | `surface_gnulinux.cpp`; deps `x11-xcb` + `wayland-client` |
| input | ✅ | SDL by default; XInput Windows-only |
| audio | ✅ | SDL / NOP |
| kernel/ppc | ✅ | `#if REX_PLATFORM` guards; portable codegen (check `ppc/`) |

---

## 3. DONE in 1.1.1 (code foundations)

1. **`settings.cpp`**: portable MD5 (RFC 1321, ~120 lines) for
   `CheckDefaultXex` — drops the CryptoAPI dependency. DXGI GPU detection
   guarded (`GetPrimaryGpu/DetectGpuName/DetectGpuTier`) with a fallback (tier
   medium). Per-platform backend defaults: `dbz3_gpu_backend` =
   `d3d12`/`vulkan`, `dbz3_input_backend` = `xinput`/`sdl`.
2. **`launcher_state.cpp`**: `PickFolder`/`PickFile` (COM) and `Utf8ToWide`/
   `WideToUtf8` under `#if REX_PLATFORM_WIN32`; outside Windows they return
   "cancelled" (the launcher keeps the default paths).
3. **`mod_pipeline.cpp`**: the script launcher (`CreateProcessW`) guarded with
   a clear-error fallback.
4. **`mods.cpp`**: already portable (fallback for the zip installer).
5. **`main.cpp`**: `OutputDebugStringA` no-op outside Windows; portable
   pre-flight (MessageBox on Windows / stderr elsewhere).

With this, `src/` **conceptually compiles on Linux** (no mandatory Win32
dependencies in build paths).

---

## 4. Pending for a real Linux build

Recommended order of work:

### 4.1 Build toolchain
1. **Linux CMake preset** in `CMakePresets.json`: clang compiler, baseline
   flags `-march=x86-64 -mssse3`, Vulkan mandatory and
   `DBZ3_DUAL_REGION=ON`. The preset does not depend on an exact Clang version.
2. **Dependencies** (apt/pacman): vulkan (libvulkan-dev), SDL3, X11-xcb,
   wayland-client, xdg. The SDK's CMake already covers them.
3. **Rebuild the codegen**: `generated/` (US) and `generated_eu/` (EU) are
   regenerated with `rexglue codegen` (the recompiler is portable). The
   decrypted `.xex` are the same → the `dbz3_config*.toml` work the same.
4. **DLLs → .so**: the GPU plugin is loaded by name (`gpu_plugin_loader.cpp`
   already distinguishes `.dll/.dylib/.so`). The Linux runtime produces
   `librexruntime.so`, `librexgpu-xenos.so`, FFX vk.

### 4.2 Pending functionality (launcher)
1. **Portable file dialogs**: implemented with `zenity` and a `kdialog`
   fallback; with neither, the launcher keeps the cancel behaviour.
2. **Portable script spawning**: implemented with `posix_spawn` and a pipe to
   capture stdout/stderr, keeping Windows' asynchronous pipeline.
3. **Zip installation**: implemented with `unzip` and the same layout
   normalisation; the dependency is documented as a system package.
4. **Handling `mod center hd/`**: the scripts (`swap_b3.py`, `texture_b3.py`)
   call `xbcompress.exe`/`xbdecompress.exe` (XDK binaries, Windows only). On
   Linux we must: (a) port the LZX compression (the SDK already has
   `mspack`/`libmspack` — see whether it exposes LZX), or (b) run via Wine, or
   (c) mark the tools as Windows-only in the launcher.

### 4.3 Validating Vulkan as the game backend (the challenge)
- Vulkan already exists and renders, but it is **6.5x slower than D3D12 in
  IssueSwap** (§3 / AGENTS). The whole Linux port depends on Vulkan being
  smooth.
- **Plan**: profiling with Tracy (build `win-amd64-tracy`/Linux equivalent),
  look for bottlenecks in the command processor / barriers / fences of the
  Vulkan path, and apply the already-hardened pacing fix (§14.17 vsync clamp
  at 60 Hz) the same way.
- If Vulkan does not reach the performance, alternatives: DXVK does not apply
  (the render is native); the Vulkan path would have to be reviewed in depth
  (it is in the SDK).

### 4.4 Checks
- Fine sweep of the SDK's `ppc/` and `codegen/` for residual Win32 (not found
  in the initial grep, to confirm).
- Smoke test on Linux: launcher shown + first present OK (Vulkan log) + guest
  intro without FATAL.

---

## 5. Scope by phase

| Phase | Contents | Result |
|---|---|---|
| **1.1.1 (done)** | Platform guards in `src/` + portable MD5 + per-platform defaults + docs | `src/` portable; strategy documented |
| **1.2 (next)** | Linux CMake preset + dual-core build on Linux + portable dialogs/spawn/zips | First Linux binary that starts the launcher |
| **1.3** | Smooth Vulkan (profiling + optimisation) | Game playable on Linux |
| **1.4** | Modding toolkit on Linux (portable LZX or Wine) + Linux release | Public Linux release |

---

## 6. Risks and open decisions

- **Vulkan performance** (critical): without smooth Vulkan there is no Linux release.
- **Controller**: SDL by default (XInput does not exist on Linux) — a generic
  USB/Bluetooth controller should work; validate deadzone/rumble (§14.7) on Linux.
- **Distribution**: AppImage/Flatpak vs a tar.gz with documented dependencies.
  Decide when the first playable binary exists.
- **The model port and modding depend on the LZX compression tools**: it is
  the feature-parity blocker, not the base game's.
