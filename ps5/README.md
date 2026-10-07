# ps5/ — PS5 port (jailbroken consoles)

This folder builds **DBZ Budokai 3 HD Collection** for a **jailbroken PS5** as an
installable homebrew title. The user guide is [`docs/PS5.md`](../docs/PS5.md);
this file describes how the pieces fit together.

> **Licence.** Everything in `ps5/` is **GPL-3.0-or-later** (see
> [`ps5/LICENSE`](LICENSE)). It is adapted from
> [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp)
> (GPL-3.0-or-later), which ported another ReXGlue-recompiled game to the PS5,
> and the title links the GPL-3 PS5 Vulkan driver
> ([mihawk-99/PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan)). The rest of
> the repository stays MIT; the MIT code is GPL-compatible, so a PS5 build as a
> whole is distributed under GPL-3. As with every build of this project, a PS5
> build contains code recompiled from the user's own copy of the game and must
> not be shared.

## Pipeline

```
your ISO / game folder
   │  stage_game.py      find the Budokai 3 xex by checksum (US or EU),
   │                     copy default.xex + us/ eu/ into ps5-game/
   ▼
rexglue codegen          dbz3_manifest.toml (US) or dbz3_manifest_eu.toml (EU)
   │                     with the PATCHED recompiler (its PCH template knows PS5)
   ▼
generated/ or generated_eu/
   │  build_game.sh      PS5 toolchain (prospero-clang, znver2, large code model)
   │                     + DBZ3 host sources + main_ps5.cpp
   ▼
title_build.sh           link with RADV (PS5_Vulkan), convert + sign → eboot.bin
   ▼
/data/homebrew/<TITLEID> on the console, game data in /data/dbz3/game
```

`make_ps5.sh` runs all of it (nine resumable steps) on an Arch Linux host.

## The SDK patches

The ReXGlue SDK v0.10.0 is patched in three layers, in this order:

1. **`patches/rexglue-sdk/`** (repository root) — DBZ3's own runtime: AFS
   virtual mid-insert and mod overrides, texture packs, audio gain, input, etc.
   Whole files copied over the checkout (the same as the Windows/Linux builds).
2. **`ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch`** — the PS5 platform layer
   from mcla-recomp (`patches/rexglue-v0.10.0-mcla.patch`), rebased onto layer 1:
   platform detection, libc/libc++ differences, anonymous shared memory with a
   kernel-chosen base, 16 KiB host pages, signals without realtime signals,
   VK_KHR_display presentation, static runtime/GPU libraries, the vblank resync
   and the shared-memory tuning cvars. Two hunks conflicted with DBZ3 and were
   merged by hand:
   - `src/graphics/graphics_system.cpp`: DBZ3's 60 Hz vblank clamp is kept and
     mcla-recomp's resync after a backwards guest tick is added after it.
   - `src/ui/vulkan/vulkan_presenter.cpp`: DBZ3's `frame_cap` pacing is kept
     and the PS5 paint logging follows it.
   One DBZ3 addition: `GetExecutablePath()` on PS5 honours the
   `REX_EXECUTABLE_PATH` environment variable (there is no `/proc` and the
   title folder is read-only). `main_ps5.cpp` sets it to `/data/dbz3/dbz3`, so
   everything DBZ3 keeps "next to the executable" (`dbz3_user.toml`, `mods/`,
   `mods_nativos/`, `user_data/`) lives in `/data/dbz3`.
3. **`ps5/patches/rexglue-ffmpeg-ps5-config.patch`** — FFmpeg's PS5 config
   header (unchanged from mcla-recomp).

**If you change a file in `patches/rexglue-sdk/`**, check that layer 2 still
applies (`git apply --check` on a clean v0.10.0 checkout with layer 1 copied
in). If it does not, regenerate it: apply mcla-recomp's patch with
`git apply --3way`, resolve, and `git diff` against the layer-1 commit.

## Files

| File | What it is |
|---|---|
| `make_ps5.sh` | The one command (Arch Linux, root). See `docs/PS5.md`. |
| `stage_game.py` | Stages the user's game from an ISO or folder; picks US/EU by checksum. |
| `build_game.sh` | Compiles the codegen, the DBZ3 host sources and `main_ps5.cpp`; calls `title_build.sh`. |
| `main_ps5.cpp` | The PS5 host: settings, Vulkan presentation, runtime, game mount, launch. No launcher. |
| `ps5_pad_input.h` | DualSense via `scePad`, presented as an Xbox 360 pad. (mcla-recomp) |
| `ps5_audio.h` | Audio via `sceAudioOut`, stereo. (mcla-recomp) |
| `title_log.h`, `log_fd_sink.h` | Log to `/data/dbz3/dbz3-play.log` (play build) or over TCP (test build). (mcla-recomp) |
| `title_log_client.py` | PC side of the test-build log connection. (mcla-recomp) |
| `title_build.sh`, `title_support.c`, `title_stub_system_service.c` | Link, convert and sign the title with the PS5 Vulkan driver. (mcla-recomp) |
| `build_ps5_vulkan_driver.sh` | Builds the PS5 toolchain and RADV driver (≈20 min). (mcla-recomp) |
| `make_title_art.py` | Tile/background from the disc's `nxeart` dashboard art. (mcla-recomp) |
| `patches/` | SDK patches, see above. |

## What the PS5 build leaves out

- The **ImGui launcher** and the in-game ImGui menu: the game boots directly
  (like `dbz3_skip_launcher=true` on PC). Settings are read from
  `/data/dbz3/dbz3_user.toml`, the same file the PC launcher writes, so a file
  made on PC can be copied over.
- **Model Swap / mod pipeline** tools (they need Python and the XDK
  compressor). Ready-made mods work: put them in `/data/dbz3/mods/`, exactly as
  on PC (`mods/<mod>/us/<afs>/<entry>`); the runtime serves them the same way.
- **D3D12-only features** (HD texture upscale, texture dump, DLSS/FSR 3,
  FidelityFX): the console has Vulkan only. Texture packs work (they have a
  Vulkan path).
- **Dual region**: a PS5 build is single-region, made from the executable you
  supply (US → `generated/` + hooks and roster extensions; EU →
  `generated_eu/`, as the PC single-EU build).

## Status

- Verified here: the merged SDK patch applies cleanly to a fresh v0.10.0 +
  DBZ3 overlay, and `rexruntime` + `rexgpu-xenos` configure and compile for the
  PS5 target with the pinned payload SDK and clang 21.
- **Not yet verified on a console.** The game itself could not be built or run
  here (no game executable / codegen available in this environment, no
  console). Expect to iterate on the first boot: missing indirect-call targets
  go in `dbz3_config*.toml` as on PC, and `/data/dbz3/dbz3-play.log` holds the
  warnings and the crash report of the last start.
