# ReXGlue SDK patches

This project uses the [ReXGlue SDK](https://github.com/rexglue/rexglue-sdk) as
an external dependency (it is not included here). The files in this folder are
**runtime modifications** needed so that override model swaps work with bins
that exceed their AFS slot.

> **Patch version: ReXGlue 0.10.0** (migrated from 0.9.0 on 2026-08-25).
> In 0.10 the filesystem was refactored: `src/filesystem/afs.cpp` and
> `include/rex/filesystem/afs.h` **do not exist** in SDK 0.10 (they were
> removed) and `host_path_file.cpp`/`host_path_entry.cpp` are much simpler (no
> AFS/override logic). That is why the 0.10 patch **recreates**
> `afs.h`/`afs.cpp`, **ports** the logic to the new
> `host_path_file.cpp`/`host_path_entry.cpp`, and also restores the 3 dbz1
> cvars that 0.10 removed (needed to link `REXCVAR_DECLARE`) and modifies 2
> CMakeLists to include the new files.

> **PS5.** The PS5 build applies a second patch on top of this overlay:
> `ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch` (the PS5 platform layer from
> [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp),
> rebased onto this folder). **If you change a file here, check that the PS5
> patch still applies** (`git apply --check` on a clean v0.10.0 checkout with
> this folder copied in); see [`ps5/README.md`](../ps5/README.md).

## What these changes do

### 1. Virtual mid-insert in the AFS table (`afs.cpp`, `afs.h`)

The guest (game) reads each entry of `data_cmn.afs` with a buffer of size
`to_read = ceil(size/0x1000)*0x1000` derived from the AFS table. A mod bin
larger than that to_read (e.g. Goten 107006 B in Krillin's slot, to_read
106496 B) was truncated when served by override -> crash.

Before these changes, the runtime only served an override bin if it fitted in
the slot's to_read. Larger bins required rebuilding the whole AFS (~280 MB per
mod), which made 2+ simultaneous model mods impossible.

The **virtual mid-insert** presents the guest with a CONSISTENT AFS table that
replicates exactly a rebuild with mid-insert:

- `AfsGetVirtualTable()`: builds and caches a virtual table where each entry
  with an override larger than its `to_read` **grows in place** (slot aligned
  to 0x800) and **all later entries are shifted** by the accumulated delta,
  just like a rebuilt AFS.
- `AfsTranslateOffset()`: for data reads, translates the virtual offset ->
  physical (subtracts the entry's delta) and serves the override (full bin) or
  reads from the physical file at the translated offset.

Growth criterion: it only grows if the override exceeds `to_read` (what the
guest already allocates), NOT if it exceeds the physical slot. So mods that fit
(e.g. tex_91, 114688 = to_read) shift nothing.

Result: native B3->B3 model swaps weighing ~100 KB per mod, 2+ model/texture
mods active at once, and swaps in any direction (the bin can be larger or
smaller than the slot).

### 2. Whole-file override (`host_path_entry.cpp`, `afs.cpp`, `afs.h`)

Besides replacing individual entries of an AFS, mods can replace **whole
files** (e.g. `opening.sfd`, `adx_usa.afs`, `Ending00.sfd` of the OG music
mod). This lets whole-file mods apply **without staging or duplicating
assets**: the runtime serves them directly from `mods/<mod>/<filename>` (or
`mods/<mod>/us/<filename>` / `mods/<mod>/eu/<filename>`).

- `AfsFindModFileOverride()` (`afs.cpp`): looks for a full replacement of a
  file by name, in alphabetical mod order.
- `HostPathEntry::Open()` (`host_path_entry.cpp`): if there is a full
  replacement for the file the guest opens, it opens the mod's file instead.

This is what lets the game use the assets folder (`game_data_root`) directly
without an `active_region` overlay that hardlinks/copies the files. The region
(us/eu) is mounted separately (see the app section).

### 3. Read translation in the file device (`host_path_file.cpp`)

`HostPathFile::ReadSync` now:

1. If the request falls in the header+table region of `data_cmn.afs`, it
   serves the virtual table (completing from the real file if the request
   crosses the end of the table, because the guest rounds to 0x8000).
2. If the request falls in data and the AFS has grown entries, it calls
   `AfsTranslateOffset` to serve the full override or read from the physical
   file at the translated offset.
3. If there are no grown entries, the classic per-entry override (no virtual
   table) is used as before.

### 4. Mods root with walk-up (`afs.cpp`, `settings.cpp`, `mod_pipeline.cpp`)

In the release, the game executable used to live in a subfolder
(`dbz3_avx2/` or `dbz3_legacy/` — see the ISA bootstrap in
`src/bootstrap.cpp`) while the mods stay next to the game data
(`<root>/mods`). `AfsModsRoot()` (runtime) and the launcher's
`ModsRoot()`/`ModsOutDir()` walk up to 3 levels from the executable looking for
a `mods/` folder and use the first one found (in dev it is the exe's own, no
change). On PS5 the executable path comes from `REX_EXECUTABLE_PATH`
(`/data/dbz3/dbz3`), so the mods root is `/data/dbz3/mods`.

### 5. Input: configurable deadzone and rumble (`input_system.cpp`)

SDK 0.10 removed the `deadzone`/`rumble` cvars that 0.9 had. This patch
restores them and makes them REAL (the launcher controls used to be placebo):
- `REXCVAR_DEFINE_DOUBLE(deadzone, 0.1, ...)` — applied in
  `InputSystem::GetState` on the merged state (all stick axes are zeroed if
  their magnitude is below `deadzone * INT16_MAX`). Covers the 3 drivers
  (XInput, SDL and MnK) at the single output point to the guest.
- `REXCVAR_DEFINE_BOOL(rumble, true, ...)` — in `InputSystem::SetState`
  accepts the vibration without reaching any pad when disabled.
- The launcher writes both by name (`SetFlagByName`); the cvar registry of
  `rexruntime.dll` is shared with the exe (it exports them), so the
  propagation reaches the runtime.

### 6. Real presenter frame cap (`d3d12_presenter.cpp`)

SDK 0.10 **removed the `frame_cap` cvar** from 0.9 (game pacing is now done by
the guest's vblank via `vsync`). The launcher's "Frame cap" option was
therefore a placebo. This patch truly restores it in the D3D12 backend:
- `REXCVAR_DEFINE_INT32(frame_cap, 0, "UI/Presenter", ...)` (0 = no limit).
- In `D3D12Presenter::PaintAndPresentImpl`, before painting/presenting, it
  waits for the next `frame_cap` FPS slot with `std::chrono::steady_clock` +
  `rex::thread::Sleep`. Painting is serialised (a single owner), so a
  file-scope timestamp is safe.
- It only affects the host presentation rate (30 = half load on integrated
  GPUs); it does NOT touch the guest's vblank or the game speed (that is the
  `vsync` cvar, which the launcher forces to 60 Hz).
- The launcher propagates it with `SetSdkInt("frame_cap", ...)` ONLY in game
  mode (the launcher keeps its repaints unlimited).
- It also adds a diagnostic log of the first `Present` (`dbz3: first present
  OK (...)`) to measure from the log how long the launcher's black screen lasts
  on slow machines (how long device/swapchain init takes).

### 6.b Frame cap and safe mode of the Vulkan presenter (`vulkan_presenter.cpp`)

SDK 0.10's Vulkan presenter could pick `IMMEDIATE` or `MAILBOX` by default and
did not share the D3D12 presenter's `frame_cap` cvar. On Linux this is a
problem with MangoHud and Steam, which intercept every `vkQueuePresentKHR`: an
unlimited present loop could happen, causing severe stutter with MangoHud and
making Steam show hundreds or thousands of FPS even though the guest's logical
cadence stayed at 60 Hz.

The patch:

- restores `frame_cap` in the Vulkan presenter and applies the same host
  pacing as D3D12;
- forces FIFO when a cap is configured;
- makes `IMMEDIATE`, `MAILBOX` and `FIFO_RELAXED` opt-in, leaving FIFO as the
  safe default;
- does not alter the guest's vblank or logical speed.

(The PS5 patch keeps this pacing and adds its paint logging after it.)

### 7. Legacy variant build (SDK CMakeLists, optional)

To build the SDK without AVX2 (`-march=x86-64-v2`) in a separate directory
without overwriting `out/win-amd64`, the SDK's root CMakeLists accepts the cache
var `REXGLUE_OUTPUT_DIR` (if left empty it uses the default). It is not a
runtime change; it is a build aid to generate `out/win-amd64-legacy`.

### 8. Presenter UI tick timeout (`presenter.cpp`)

The UI thread waits for the monitor's vblank (via the `DXGIUITickThread`
thread) before painting each frame, so as not to saturate the GPU. If that
vblank stops arriving (lost/stale monitor, stuck `WaitForVBlank`, display mode
change), `WaitForUITickFromUIThread` waited forever: the window went black and
"Not responding", and closing the window (Alt+F4) was not processed.

Patch: the wait uses `condition_variable::wait_for(50 ms)` instead of an
indefinite `wait()`. If no tick arrives in time, the UI paints anyway (drop to
~20 FPS at most). The UI thread never blocks, the launcher always appears and
window messages are always processed.

### 9. Asynchronous SDL driver initialisation (`sdl_input_driver.{h,cpp}`)

`SDL_InitSubSystem(SDL_INIT_GAMEPAD)` can block indefinitely when capture
software is loaded (RTSS/OBS) or joystick enumeration is slow. The SDL driver
called it synchronously from `OnWindowAvailable` (via
`CallInUIThreadSynchronous`), so the launcher stayed black + "Not responding"
on open (reproduced: startup hung in `AttachWindow`).

Patch: `OnWindowAvailable` only attaches the window and launches a
`std::thread` that does the whole SDL init (events + gamepad + mappings) in the
background. SDL init is thread-safe; controllers appear via events when the
thread finishes, and `EnumerateDevices` returns nothing until then. The init
flags become `std::atomic<bool>` (read by the input thread). The thread is left
detached (never joined): if it is still blocked in `SDL_InitSubSystem` at
shutdown, a `join()` would hang the shutdown (the game hard-exits on close
anyway).

### 10. Guest language = launcher language (`xam_info.cpp`)

The game (guest) picks its text language via `XGetLanguage`. It used to return
a fixed English (based on region). Now it returns `user_language`, the cvar the
launcher already propagated from `dbz3_language` in `ApplyUserSettingsToSdk`
(`REXCVAR_SET(user_language, Language())`). So the "Launcher and game
language" selector ALSO controls the game's text, not just the launcher UI.

`XGetLanguage_entry` reads `REXCVAR_GET(user_language)`. Mind the scope:
`user_language` is defined with `REXCVAR_DEFINE_UINT32` in `xam_user.cpp`
BEFORE the namespaces are opened, so its accessor lives at GLOBAL level — this
file's `REXCVAR_DECLARE(uint32_t, user_language)` must also go outside
`namespace rex::kernel::xam` (otherwise the link fails with
`undefined symbol: rex::kernel::xam::FLAGS_user_language_storage_`).

### 11. Collecting unregistered functions (`function_dispatcher.cpp`)

`InvalidFunctionTrap` (what the runtime runs when the guest calls an indirect
function that is not in the table) now, if the environment variable
`DBZ3_COLLECT_UNREGISTERED` exists, writes each address to
`dbz3_unregistered.txt` and continues instead of aborting with `REX_FATAL`.
Without the variable, the behaviour is identical (it aborts). It is a
diagnostic aid for the EU/PAL variant (second recompilation): if the guest
reaches an unregistered function in battle, the addresses are collected and
declared in `dbz3_config_eu.toml`.

In addition, each unregistered indirect call logs (critical level) the target,
the guest's `caller_lr` and registers r3/r4/r11 — it helped locate the root
cause of the EU DEMO battle crash (v1.0.11): virtual calls to vtable/
mid-function blocks misclassified as jump tables (see AGENTS 14.16 in
HISTORICO_AGENTS). The same diagnosis applies to a first PS5 boot.

### 12. Game launch diagnostics (`rex_app.cpp`)

`ReXApp::LaunchModule` (the deferred lambda that starts the guest on the UI
thread) is wrapped in a try/catch that logs `e.what()` and rethrows. It turns
the intermittent startup `std::terminate` (0xC0000409) into a log with the
exception message. It is compiled into the game (not into rexruntime.dll) from
`rexglue/share/rexglue/rex_app.cpp` — the patch goes to the SDK source.

### 13. Hardening guest pacing at 60 Hz (`graphics_system.cpp`)

The `GraphicsSystem` "GPU VSync" worker marks the guest's vblank with an
interval derived from the video mode (60 Hz) when the `vsync` cvar is ON, but
with the cvar OFF it collapsed it to ~1 ms (1000 Hz) and the game logic ran
~16x faster ("sped-up game", reported by users who disabled V-Sync). The
launcher already forced `vsync=true` at startup, but any path that turned it
off at runtime (toml, config, leftover cvar) sped the game up again.

The patch **clamps the interval** in the worker itself:

```cpp
uint64_t interval_ticks = std::max(
    REXCVAR_GET(vsync) ? vsync_interval_ticks : no_vsync_interval_ticks,
    vsync_interval_ticks);
```

so the guest's vblank can never be shorter than a 60 Hz frame and
`vsync=false` becomes a no-op (the game always runs at its own speed). It lives
in **rexgpu-xenos.dll** (not rexruntime.dll): after applying the patch,
`rexgpu-xenos` must be rebuilt in both variants (v3 and v2) and the DLLs
copied. (The PS5 patch keeps this clamp and adds mcla-recomp's resync after a
backwards guest tick.)

## How to apply (ReXGlue 0.10.0)

> **Since v1.4.0** it is enough to copy the whole folder over a clean checkout
> of the `v0.10.0` tag (that is what the Linux CI and `ps5/make_ps5.sh` do):
>
> ```
> git clone --branch v0.10.0 https://github.com/rexglue/rexglue-sdk.git rexglue-sdk-0.10
> cp -a patches/rexglue-sdk/. rexglue-sdk-0.10/        # PowerShell: Copy-Item -Recurse -Force
> ```
>
> The list below is the historical one (patches 1-13, v1.0-v1.3); the detail of
> what was added in v1.4.0 is in the last section of this README.

Copy the 19 files over the SDK (paths relative to the SDK root):

```
patches/rexglue-sdk/include/rex/filesystem/afs.h      ->  rexglue-sdk/include/rex/filesystem/afs.h
patches/rexglue-sdk/include/rex/input/sdl/sdl_input_driver.h
                                                      ->  rexglue-sdk/include/rex/input/sdl/sdl_input_driver.h
patches/rexglue-sdk/src/filesystem/afs.cpp           ->  rexglue-sdk/src/filesystem/afs.cpp
patches/rexglue-sdk/src/filesystem/devices/host_path_file.cpp
                                                      ->  rexglue-sdk/src/filesystem/devices/host_path_file.cpp
patches/rexglue-sdk/src/filesystem/devices/host_path_entry.cpp
                                                      ->  rexglue-sdk/src/filesystem/devices/host_path_entry.cpp
patches/rexglue-sdk/src/input/input_system.cpp      ->  rexglue-sdk/src/input/input_system.cpp
patches/rexglue-sdk/src/input/sdl/sdl_input_driver.cpp
                                                      ->  rexglue-sdk/src/input/sdl/sdl_input_driver.cpp
patches/rexglue-sdk/src/kernel/xam/xam_info.cpp    ->  rexglue-sdk/src/kernel/xam/xam_info.cpp
patches/rexglue-sdk/src/ui/presenter.cpp            ->  rexglue-sdk/src/ui/presenter.cpp
patches/rexglue-sdk/src/ui/d3d12/d3d12_presenter.cpp -> rexglue-sdk/src/ui/d3d12/d3d12_presenter.cpp
patches/rexglue-sdk/src/graphics/graphics_system.cpp  ->  rexglue-sdk/src/graphics/graphics_system.cpp
patches/rexglue-sdk/src/system/dbz1_audio_jp_flag.cpp  ->  rexglue-sdk/src/system/dbz1_audio_jp_flag.cpp
patches/rexglue-sdk/src/system/dbz1_diag_flags.cpp     ->  rexglue-sdk/src/system/dbz1_diag_flags.cpp
patches/rexglue-sdk/src/system/dbz1_region_flag.cpp    ->  rexglue-sdk/src/system/dbz1_region_flag.cpp
patches/rexglue-sdk/src/system/function_dispatcher.cpp ->  rexglue-sdk/src/system/function_dispatcher.cpp
patches/rexglue-sdk/src/ui/rex_app.cpp                 ->  rexglue-sdk/src/ui/rex_app.cpp
patches/rexglue-sdk/src/core/logging.cpp               ->  rexglue-sdk/src/core/logging.cpp
patches/rexglue-sdk/src/filesystem/CMakeLists.txt      ->  rexglue-sdk/src/filesystem/CMakeLists.txt
patches/rexglue-sdk/src/system/CMakeLists.txt          ->  rexglue-sdk/src/system/CMakeLists.txt
```

The 2 CMakeLists add the new files to the targets (`afs.cpp` to
`rexfilesystem`, the 3 `dbz1_*_flag.cpp` to `REXSYSTEM_SOURCES`). Without them
the rexruntime link fails with `undefined symbol: FLAGS_dbz1_*_storage_(void)`.

Then rebuild the runtime and copy the DLLs to the game build:

```powershell
cmake --build rexglue-sdk/out/build-win-vulkan --target rexruntime
cmake --build rexglue-sdk/out/build-win-vulkan --target rexgpu-xenos
Copy-Item rexglue-sdk/out/win-amd64/rexruntime.dll out/build/win-amd64-release/
Copy-Item rexglue-sdk/out/win-amd64/rexgpu-xenos.dll out/build/win-amd64-release/
```

> Patch 13 (`graphics_system.cpp`) lives in **rexgpu-xenos.dll** (not
> rexruntime.dll): rebuild `rexgpu-xenos` in both variants (v3 and v2) and copy
> the DLLs.

⚠️ In 0.10 the game compiler must be `C:/Program Files/LLVM/bin/clang++.exe`
(MSVC target). The retcomm toolchain (MinGW/libstdc++) does NOT compile the
`rex/chrono/chrono.h` header (missing `std::chrono::clock_time_conversion`).

The scripts `mod center hd/swap_b3.py` and `mod center hd/texture_b3.py`
generate the overrides with the correct padding (to the slot's to_read, or to
the virtual to_read if the bin is larger) and the runtime serves them with the
virtual mid-insert.

## Changes 2026-09-18 (performance + HD textures)

- **`src/graphics/d3d12/texture_cache.cpp` + `include/rex/graphics/d3d12/texture_cache.h`**
  and the shaders **`src/graphics/shaders/texture_upscale_cs.hlsl`** /
  **`bytecode/d3d12_5_1/texture_upscale_cs.h`**: outer layer of runtime texture
  upscaling (Nx host resource + bicubic pass). Cvar
  **`dbz3_texture_upscale`** (1 = off). The launcher controls it with
  `dbz3_hd_textures` (Video -> "HD textures (WIP)", x2/x3/x4; it also generates
  the mip chain by averaging level-0 blocks). **WIP and OFF by default**: it
  works, but causes hitches when new textures load. See
  `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md`.
- **`src/filesystem/afs.cpp`**: the override log
  (`AFS OVERRIDE LOOKUP/HIT/MISS`) becomes conditional on
  `dbz1_diag_logging`; before, it was written on EVERY AFS read (thousands of
  lines per session).
- **`src/ui/d3d12/d3d12_presenter.cpp`**: cvar **`dbz3_perf_logging`**
  (default true) with a line every 5 s `dbz3: perf fps=... frames=...
  max_frame_ms=... cap=...`.
- Rebuilt DLLs (baseline): `rexruntime.dll` 10,870,272 B,
  `rexgpu-xenos.dll` 6,180,864 B (2026-09-18).

### 2026-09-18 (cont.) - performance counter on the guest swap

- **`src/graphics/d3d12/command_processor.cpp`** (rexgpu-xenos):
  `Dbz3LogGuestPerformance()` at the start of `D3D12CommandProcessor::IssueSwap`
  -> cvar `dbz3_perf_logging` (read by name via `rex::cvar::GetFlagByName`,
  defined in the runtime) and a line every 5 s with the game's `fps`, `frames`
  and `max_frame_ms`. It is the valid in-game measurement and works with the
  window off-screen (the UI presenter only paints the launcher).
- **`src/system/dbz1_diag_flags.cpp`**: shared definition of
  `dbz1_diag_logging` (rexruntime), used to gate the AFS override logs and the
  read trace.
- Offscreen test harness: **`tools/hidden_run.ps1`**.
- Final canonical DLLs (2026-09-19): `rexgpu-xenos.dll` **6,202,368 B**,
  `rexruntime.dll` **10,870,272 B** (both with the `dbz3_perf_logging` marker).
  ⚠️ Building the game overwrites `rexruntime.dll` with the stale one from
  `rexglue/bin` -> re-copy from the baseline after every build (AGENTS 7).
- **`src/audio/sdl/sdl_audio_driver.cpp`** (rexruntime, 2026-09-19): cvar
  `audio_gain` (double, 0.0-1.0) multiplied in the SDL callback
  (`gain = GetOutputGain() * clamp(audio_gain, 0, 1)`); `audio_mute` already
  existed. It is the launcher's REAL volume: before, the sliders wrote
  `master_volume`, a cvar that **does not exist** in the SDK, so they did
  nothing (and the launcher forced `audio_mute=false`, so muting was not
  possible either).
- **Canonical DLLs (2026-09-19)**: `rexruntime.dll` **10,873,856 B** (with
  `audio_gain` + `dbz3_perf_logging`), `rexgpu-xenos.dll` **6,202,368 B**,
  `amd_fidelityfx_dx12.dll` **5,413,888 B** (the one in `rexglue-sdk-0.10/bin/`
  is regenerated differently on build: do NOT copy it).

### 2026-09-19 (cont.) - diagnostic logs become opt-in

Diagnostics shipped enabled: anyone who did not touch the Dev tab ended up with
log lines they had not asked for, and the log created a new file per run
without deleting the old ones.

- **`src/filesystem/afs.cpp`**: `dbz3_io_logging` goes from `true` to
  **`false`** by default (still switchable from the launcher's Dev tab).
- **`src/ui/d3d12/d3d12_presenter.cpp`**: `dbz3_perf_logging` goes from `true`
  to **`false`** by default (new "Performance log (every 5 s)" checkbox in the
  Dev tab; `Dbz3IsOurWindowForeground` still provides the `fg=`).
- **`src/core/logging.cpp`** (NEW patch): `NextSequentialLogPath` prunes the
  oldest `dbz3_NNN.log` files at startup, honouring `log_max_files` (default
  20). Before, the cap of 20 did not apply across runs because each run uses a
  new sequential name (138 files accumulated in testing; verified 138 -> 20).
- **Canonical DLLs (2026-09-19, final v1.2.5)**: `rexruntime.dll`
  **10,910,208 B**, `rexgpu-xenos.dll` **6,202,368 B**,
  `amd_fidelityfx_dx12.dll` **5,413,888 B**.

### 2026-09-19 (cont.) - HD textures: hitch fix + RGBA8 coverage

> Full detail: `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` §8-§10.

- **`src/graphics/shaders/texture_upscale_cs.hlsl`** + **`bytecode/d3d12_5_1/
  texture_upscale_cs.h`**: `XeLoadLevelTexel` samples a grid of at most
  `kXeMaxBlockSamples = 8` per axis (before, it averaged the whole
  `2^level x 2^level` block = `16 * 4^level` reads IN SERIES; at high mips few
  threads remain -> frames of hundreds of ms). Rebuild with
  `fxc /nologo /T cs_5_1 /E main /Vn texture_upscale_cs /O3 /Fh
  bytecode/d3d12_5_1/texture_upscale_cs.h texture_upscale_cs.hlsl`.
- **`src/graphics/d3d12/texture_cache.cpp` + `include/rex/graphics/d3d12/
  texture_cache.h`**: the upscale now also covers **native RGBA8** (`fmt=6`),
  not just DXT:
  - `GetTextureUpscaleFactor`: accepts `dxgi_format_unsigned == R8G8B8A8_UNORM`
    when the load shader produces RGBA8 (`bytes_per_host_block == 4`); rejects
    other formats (`not_rgba8`/`load_not_rgba8`) so as not to corrupt textures.
  - **Frontbuffer exclusion** (`swap_texture_key_`): `RequestSwapTexture`
    registers the key BEFORE creating it and the upscale rejects it
    (`swap_texture`). Without this the presentation resource was created at Nx
    and the swap failed.
  - New helper `GetTextureUpscaleRgba8Format` for `GetDXGIResourceFormat` /
    `GetDXGIUnormFormat(TextureKey)` (before, they returned
    `dxgi_format_uncompressed`, which for `k_8_8_8_8` is `UNKNOWN` -> thousands
    of `Unsupported texture formats used in the frame`).
  - New cvar **`dbz3_upscale_max_texels`** (default `1 << 19` texels = 0.5 M,
    max area 1024x512 / 512x1024; `0` = no limit) to bound VRAM. The launcher
    exposes it as an **advanced** setting in the Dev tab ("HD textures:
    spending", Low/Medium/High) -> cvar `dbz3_hd_texture_max_texels`.
  - **Video guard** (`UpscaleBudgetAllows`): the intro/SFD rewrites the video
    texture ~60 times/s and each rewrite regenerated the mip chain (`upx`
    reached **32182**, GPU at 80 % / 133 W). Sliding window: >24 upscales in
    0.5 s -> stop granting for 3 s. The decision is **cached per key**
    (`upscale_granted_keys_`) so it is stable between the creation of the Nx
    resource and its reloads (otherwise the Nx resource stays unfilled ->
    `device removed 0x887A0001`). Measured: upx 32182->237, GPU 80->39 %,
    133->34 W.
  - **x3 cap** (`dbz3_texture_upscale` range 1-3, before 1-4): x4 multiplied
    VRAM/GPU with almost no visible gain.
  - **Minimum size** (`dbz3_upscale_min_size`, default **16**): textures
    smaller than 16 texels wide/high are not scaled. They are HUD/UI (health bar
    segments, icons) and bicubic blurred them. Fix for the dirty HUD (user
    feedback).
  - **Anti-ringing clamp** in `texture_upscale_cs.hlsl`: the Catmull-Rom kernel
    result is clamped to the `[min, max]` of the 16 samples, without overshoot
    on edges (glyphs/letters). Bytecode regenerated with `fxc /T cs_5_1 /E main
    /Vn texture_upscale_cs /O3 /Fh ...`.
- **Measurement** (`hd_tex=3x` + 0.5 M limit, Quality preset, RTX 4070 SUPER,
  real battle): **0 errors**, fps min 54.7, GPU **39 % / 33 W / 1.67 GB**.
- **Canonical DLLs (2026-09-19b, HD textures: RGBA8 + guard + min-size)**:
  `rexgpu-xenos.dll` **6,227,456 B** (baseline; SHA256 varies per build),
  `rexruntime.dll` **10,910,208 B**, `amd_fidelityfx_dx12.dll` **5,413,888 B**.

### 2026-09-29 - DRED active in release + gamecontrollerdb

Two things learned from the sister recompilation **reblue** (ReXGlue 0.10, same
base as this project): DRED was only armed when `d3d12_debug=ON`, and the
`gamecontrollerdb.txt` the runtime already knows how to read **was not
shipped**. The two files below are now part of the patch tree.

- **`src/ui/d3d12/d3d12_provider.cpp`** (rexruntime): DRED moves out of the
  `if (d3d12_debug)` and gets its own cvar **`d3d12_dred`** (default
  **true**). `ID3D12DeviceRemovedExtendedDataSettings` is obtained with
  `D3D12GetDebugInterface`, which does **not** require the debug layer (that
  one is heavy and stays OFF by default): arming DRED in release is free and is
  the only thing that, when the device is lost, names the failing operation
  (auto-breadcrumbs) and the allocation at the page-fault VA.
- **`src/graphics/d3d12/command_processor.cpp`** (rexgpu-xenos):
  `LogDeviceRemovalDiagnostics` enriches the report:
  - each breadcrumb also prints the name (SetName) of the **command queue** and
    the **command list** it was executing;
  - from the page fault, the `D3D12_DRED_ALLOCATION_NODE` nodes (existing +
    recently freed) are dumped with their type and name.
- **`gamecontrollerdb.txt`** (~608 KB, root + mirror in `github/`): community
  controller database (SDL_GameControllerDB, zlib). The runtime already has the
  cvar **`hid_mappings_file`** (default `gamecontrollerdb.txt`) and loads the
  file with `SDL_AddGamepadMappingsFromFile`; what was missing was **shipping**
  it next to the exe. `CMakeLists.txt` copies it in POST_BUILD,
  `tools/make_release.ps1` puts it in the zip and `tools/sync_github.ps1`
  versions it. Benefit: the SDL backend recognises generic controllers that do
  not go through XInput. (The PS5 host sets `hid_mappings_file=""`: the
  DualSense goes through scePad.)
- **Canonical DLLs (2026-09-29)**: `rexruntime.dll` **10,920,448 B**,
  `rexgpu-xenos.dll` **6,360,064 B**, `amd_fidelityfx_dx12.dll` **5,413,888 B**.

## 2026-10-04 - v1.4.0: quick menu, live FSR, deferred VFS, new characters

From v1.4.0 this folder is the **FULL overlay** of our SDK over ReXGlue
**v0.10.0** (`git diff v0.10.0` of the local branch `dbz3-burstlimit`):
copying `patches/rexglue-sdk/.` over a clean v0.10.0 checkout leaves the tree
identical to the one that builds the canonical DLLs. In addition to the patches
in the previous sections, it adds `CMakeLists.txt` (SDK root:
`REXGLUE_OUTPUT_DIR`), `src/core/CMakeLists.txt`, `src/ui/CMakeLists.txt`,
`include/rex/rex_app.h` (the dual core's `ResolveImageInfo` and
`OnConfigureQuickMenu`) and the rest of the files listed below.

### Features adapted from Burst Limit Recompiled (iExplosiveRage)

Cherry-picks from the `burstlimit` branch of
[iExplosiveRage/rexglue-sdk](https://github.com/iExplosiveRage/rexglue-sdk)
(the *DBZ Burst Limit Recompiled* project), which descends from the same
`v0.10.0` (original commits 0f57cc6, 284e15b, 5f3abd4, be4bdb0, 9296733,
156a164, d197cd7, 431266b, 3360458, 0f1ae03 + minimal port of 1fc298c). The
SDK licence (BSD-3) is intact in the headers.

- **Controller quick menu** (`ui/overlay/quick_menu.{h,cpp}`,
  `rex_app.{h,cpp}`): F1 or the `quick_menu_buttons` combo (Back+Start by
  default; L3+R3 or keyboard only). The app fills it with
  `ReXApp::OnConfigureQuickMenu`. Adapted to DBZ3: the launcher's
  orange/blue palette, header band, translatable texts, action items
  (`kAction`), `on_changed` (save to `dbz3_user.toml`) and `can_open` (in game
  only).
- **Input blocking for the UI** (`input/input_system.{h,cpp}`): opening combo
  and *input blockers*; with a dialog open the guest receives no keys or
  buttons.
- **Restyled F3 FPS panel** (`ui/overlay/debug_overlay.{h,cpp}`,
  `overlay_text.{h,cpp}`, `perf/frame_rate.{h,cpp}`): game FPS (guest swaps
  per second) and display FPS, frame-time graph, configurable corner
  (`debug_overlay_position`).
- **Live video settings** (`ui/presenter.cpp`, `ui/d3d12/d3d12_presenter.cpp`,
  `graphics/d3d12/command_processor.{h,cpp}`, `graphics/graphics_system.cpp`):
  `present_effect`, FSR/CAS, sharpness, FXAA (`swap_post_effect`) and
  `draw_resolution_scale` apply without restarting; the FidelityFX upscaler is
  not freed while a paint uses it.
- **FSR below native resolution** (`present_fsr_quality_mode`): the
  quality/balanced/performance modes render below `draw_resolution_scale` (real
  FPS). In DBZ3 it is exposed by the cvar `dbz3_fsr_render` ("More FPS with
  FSR").
- **Black screen fix** with `present_effect` fsr2/fsr3.
- **Valid TOML saving** (`core/cvar.cpp`, test in
  `tests/unit/core/cvar_test.cpp`).
- Not ported (specific to their game): vblank FPS cap, FOV/photo mode,
  texture-pack mips/preload.

### Own v1.4.0 changes

- **Input lock** (`input/input_system.cpp`): `GetCapabilities`, `SetState`,
  `GetKeystroke` and `RefreshDevices` take the `InputSystem` mutex. The quick
  menu reads the controller from the UI thread while the game reads it from its
  own; without the lock there was heap corruption (0xC0000374 in
  `RefreshDevices`).
- **Deferred VFS** (`filesystem/devices/host_path_device.cpp`,
  `host_path_entry.{h,cpp}`, `filesystem/entry.{h,cpp}`):
  `HostPathDevice::Initialize` no longer walks the whole game folder (30 s
  cold); directories are listed on demand (`EnsureChildrenListed` when
  enumerating, exact lookup when opening). The cvar `vfs_eager_scan=true`
  restores the old mode. `dbz3 startup:` stamps in the log
  (`system/runtime.cpp`). Launcher: from ~31 s to <1 s.
- **Appended AFS entries** (`filesystem/afs.{h,cpp}`, `host_path_file.cpp`):
  mods can APPEND entries after the last one of any AFS
  (`mods/<mod>/us/<afs>/<N>` with `N` >= number of entries: `data_cmn`,
  `data_usi`, `lang_*`... for the new characters); `AfsVirtualSize` presents the
  container's virtual size to the guest. Capability published by the cvar
  `dbz3_afs_append` (if missing, the launcher disables `mods/_roster` so the
  game starts).
- **RXADPC yells** (`audio/xma_context.cpp`): `Decode()` accepts
  `"RXADPC\x01"` packets (8 B header + up to 7 IMA ADPCM blocks of 260 B / 512
  samples) and decodes them without FFmpeg. It is the battle-yell gateway of
  the new characters (there is no XMA encoder).
- **Optional diagnostics** (`graphics/pipeline/shader/translator.cpp`,
  `graphics/pipeline/texture/cache.cpp`, `graphics/command_processor.cpp`):
  vertex-fetch layout log (only with `DBZ3_LOG_DRAWS=1` or the marker
  `dbz3_drawlog.on`) and guest swap counters for the FPS panel.
- **Version stamp**: `include/rex/dbz3_build.h` -> `1.4.0`.
- **Canonical v1.4.0 DLLs (2026-10-04)**: `rexruntime.dll` **11,034,624 B**,
  `rexgpu-xenos.dll` **6,372,864 B**, `amd_fidelityfx_dx12.dll`
  **5,413,888 B** (unchanged). `tools/verify_release.ps1` checks the hash
  against the SDK baseline and these reference sizes.

## 2026-10-05 - v1.4.1: performance and diagnostics

- `src/core/threading_win.cpp` (Windows only, not in the Linux overlay):
  `timeBeginPeriod(1)` + power-throttling opt-out (EcoQoS and
  IGNORE_TIMER_RESOLUTION) the first time it sleeps, and `Sleep`/
  `AlertableSleep` with a per-thread high-resolution waitable timer (fallback to
  `::Sleep`). Reason: issue #8 (30 FPS lock with i9-14900K + RTX 4090).
- `src/graphics/command_processor.cpp` + `include/rex/graphics/command_processor.h`:
  counter `g_dbz3_regmem_wait_us` (time slept in WAIT_REG_MEM).
- `src/graphics/d3d12/command_processor.cpp`: timed fence waits
  (`gpu_wait=`/`syncs=`/`cp_wait=` in the `perf` line), `tiron` lines for guest
  frames over 50 ms (max 30/session) and a low-FPS warning that only suggests
  active settings and distinguishes CPU from GPU.
- `src/ui/d3d12/d3d12_provider.cpp`: `d3d12_dred` becomes **false** by
  default; the game arms it for the session after a `D3D12 device removed`
  (`src/launcher/settings.cpp`, `ArmGpuCrashDiagnostics`).
- `src/graphics/d3d12/pipeline_cache.cpp` (D3D12 only): counter
  `g_dbz3_sync_shader_work` (translations/pipelines done on the emulated GPU's
  thread) that the `tiron` line shows as `shaders +N`.
- `include/rex/dbz3_build.h`: stamp `1.4.1`.
- `src/filesystem/devices/host_path_file.cpp` + `host_path_entry.cpp`: the
  virtual table of an AFS (mods that append/enlarge entries) is computed on the
  file actually opened. With a music pack that brings its own `adx_usa.afs`
  (whole-file override) and the characters mod adding voices to that AFS, the
  pack was read with the original's offsets and the music came out silent
  (reproduced with a reordered pack: menu at 0.000 without the fix, music with
  it).
- `src/audio/sdl/sdl_audio_driver.cpp`: line `dbz3: audio pico=... rms=...`
  every 5 s with `dbz3_perf_logging` (guest mix level, before mute/volume).
- `src/graphics/vulkan/command_processor.cpp`: `perf` line (backend=vulkan)
  and `tiron` lines on Vulkan/Linux too.

## 2026-10-06 - PS5 build (experimental)

No file in this folder changed for the PS5 port. The PS5 platform layer is a
separate patch applied **after** this overlay:
`ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch` (mcla-recomp's PS5 patch rebased
onto this overlay, plus `GetExecutablePath()` honouring `REX_EXECUTABLE_PATH`
and a `__PROSPERO__` byte-order branch in `thirdparty/crypto/sha256.cpp`) and
`ps5/patches/rexglue-ffmpeg-ps5-config.patch`. Of the files here, the PS5 patch
touches `graphics_system.cpp` (keeps patch 13's clamp, adds the backwards-tick
resync) and `vulkan_presenter.cpp` (keeps patch 6.b's pacing, adds paint
logging). Keep those two in mind when editing them. Details:
[`ps5/README.md`](../ps5/README.md), [`docs/PS5.md`](../docs/PS5.md).
