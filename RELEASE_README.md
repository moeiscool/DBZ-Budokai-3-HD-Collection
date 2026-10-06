# DBZ Budokai 3 HD Collection — Executable release

Copyright (c) 2026 **NovaPowers**. Released under the MIT License (the PS5
build files in `ps5/` are GPL-3.0-or-later).

This package contains the recompiled executable of *Dragon Ball Z: Budokai 3
HD Collection* (Xbox 360) with the launcher, the mod system and the model
pipeline. It does **NOT include the game files** (copyright): you must supply
those from your legal copy.

## Contents

- `dbz3.exe` — **the only executable** (DUAL US/NA + EU/PAL core + launcher +
  mod system). It contains both recompilations and picks the right one
  according to the `default.xex` you provide.
- `rexruntime.dll`, `rexgpu-xenos.dll`, `amd_fidelityfx_dx12.dll` — runtime in
  the **universal baseline** ISA (SSSE3): it works on ANY x64 CPU (Core 2
  2006+), with no variants. On modern CPUs it is ~5-10% slower in host work
  than the AVX2 runtime; if you notice it, there is the fallback release
  **`v1.1.0-clasico`**.
- `TracyClient.dll` — profiling (required by the runtime).
- `amd_fidelityfx_vk.dll`, `SPIRV-Tools-shared.dll` — utilities of the Vulkan backend.
- `mod center hd/` — modding toolkit (catalogue + scripts + XDK tools).
- `RELEASE_README.md` — this file.

> **A single file**: run `dbz3.exe` and that is it. The core is **dual**
> (US/NA + EU/PAL) and at startup it identifies `default.xex` by its MD5 to use
> the matching code. It works with the US and the EU executable.

## How to install and play (step by step)

The package does **NOT include the game files** (copyright). Supply those from
your **legal copy** in one of these layouts (the launcher detects them all):

1. **Unzip** the ZIP into a folder, for example `C:\Games\DBZ3\`.
2. Place the game files in one of these ways:
   - **Option A — next to `dbz3.exe`**: `default.xex` + `us/` (and/or `eu/`).
   - **Option B — inside `assets/`**: `assets/default.xex` + `assets/us/`
     (and/or `assets/eu/`).
   - **Option B2 — the disc dump as it is** (no renaming or moving):
     `DBZ3/yae3_xenon.xex` + `DBZ3/us/` (and/or `eu/`). The launcher finds the
     executable **by size and checksum**, whatever it is called.
   - **Option C — play straight from the `.iso`** (without extracting
     anything): leave the `.iso` next to `dbz3.exe` or use "Select ISO...".
     Only the Budokai 3 executable is extracted (`DBZ3\yae3_xenon.xex`, a few
     MB) and the rest is mounted from the image. It works with the **complete
     original ISO** (with the HD Collection menu at the root of the disc).
     ⚠️ **Mods need the extracted folder** (A/B); in disc mode the game is
     played as is.
3. **Inside `us/`** copy the data from your legal copy: `data_cmn.afs`,
   `data_eng/fra/ger/ita/spn/usi.afs`, `data_yah.afs`, `adx_jpn/usa.afs`,
   `lang_jpn/usa.afs`, `opening.sfd`, `Ending00/01.sfd`. The PAL variant goes
   in `eu/`.
4. **Copy the game's executable as `default.xex`** next to `us/` (that is,
   next to `dbz3.exe` in Option A, inside `assets/` in B; **never** inside
   `us/`). The US/NA one (`yae3_xenon.xex`) or the EU/PAL one
   (`yae3_xenon_eu.xex`) both work: the launcher picks the right core, and
   region and language are chosen in the launcher.
5. **Run `dbz3.exe`** (double click).
6. Choose **Region** (USA / EU PAL), **Language**, **Video**, **Audio** and
   **Input** and press **Play**.

> If something fails, check that `default.xex` and `us/` (or `eu/`) are in the
> SAME folder, or both inside `assets/`.
> To extract the files from your **legal ISO** use `extract-xiso` (Xbox 360
> FATX). Sizes and SHA-256 of each file in `baserom.md`.

## PS5 (jailbroken consoles) — experimental

There is no ready-made PS5 package (the executable contains code recompiled
from your own copy of the game). Build and install it yourself from the
source repository with one command on an Arch Linux host (WSL2 works):

```bash
bash ps5/make_ps5.sh --iso /path/to/your.iso --console <console ip>
```

Full guide: `docs/PS5.md` in the repository. It is adapted from
[holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp); the
runtime and host compile for PS5 but it has **not yet been run on a console**.

## What is new in this release — v1.4.1 (2026-10-05)

- **Performance**: high-resolution timing (real 1 ms sleeps on Windows 11) and
  the game no longer enters Windows' power-saving mode (efficiency cores),
  against the 30 FPS stuck on powerful machines (issue #8).
- **DRED off by default**: it is armed only in the session after a
  `device removed`.
- **Logging**: the `perf` line adds `gpu_wait=`/`syncs=`/`cp_wait=`; frames
  over 50 ms leave a `tiron` line; the low-FPS warning only suggests the
  settings that are on and tells CPU from GPU.
- **New characters**: fixed the crash in the select when changing costume
  (Janemba) and the silent music with a music pack + the characters mod;
  without the kit, the launcher no longer tries to rebuild `_roster` when
  PLAY is pressed.
- **Launcher**: a notice about new characters with the EU/PAL game.
- **Modding Kit 1.4.1**: Diagnostics page (`diagnostico.py`).
- Runtime DLLs: `rexruntime.dll` 11,039,744 B and `rexgpu-xenos.dll`
  6,385,152 B, stamp 1.4.1. The characters pack is still the 1.4.0 one
  (Google Drive).

## Previous release — v1.4.0 (2026-10-04)

**Quick menu, live video, new launcher and new characters.**

- **In-game quick menu**: **F1** or **Back + Start** (can be changed to
  L3 + R3 or keyboard only). Picture, sound and controller, display and "All
  settings" (F4). Applied at once and saved by itself.
- **"More FPS with FSR"** (Native / Quality / Balanced / Performance / Ultra
  performance): the game is drawn below the resolution and FSR upscales it.
  In the quick menu and in the upscaling tab.
- **New FPS panel (F3)**: game FPS, display FPS and a graph.
- **Live video**: internal resolution, upscaling, sharpness and FXAA without
  restarting.
- **Redesigned launcher**, opens in **under 1 s** (before ~31 s) and is
  driven **with the controller**: LB/RB or Ctrl+Tab change tab, START = Play,
  and the hint bar shows keys or buttons (Xbox / PlayStation / Switch).
- **New characters** in their own select cells (**New characters** tab) and
  an **importer** from Budokai 1, Budokai 2, Infinite World and community
  models. See "Mods" below.
- **Fixes**: crash when using the quick menu (reading the controller without
  a lock), launcher stuck at "working…" with tools that write a lot, black
  screen with FSR2/FSR3.
- **New DLLs** (`rexruntime.dll` 11,034,624 B, `rexgpu-xenos.dll`
  6,372,864 B, stamp 1.4.0): do not mix them with those of earlier versions.

If your machine runs slowly: update, reproduce the problem, close the game and
attach `logs\dbz3_NNN.log`: it already carries the system, RAM, versions,
configuration, VRAM and warnings. For performance detail, turn on **Dev →
"Performance logging"**.

## Version history

| Version | Date | Summary |
|---|---|---|
| v1.4.1 | 2026-10-05 | Performance (precise timing, no Windows power saving, DRED only after a failure), logging of waits and hitches, EU notice for new characters, Kit with Diagnostics |
| v1.4.0 | 2026-10-04 | In-game quick menu (F1 / Back+Start), "More FPS with FSR", F3 FPS panel, live video, redesigned launcher with controller support and <1 s start, new characters and importer |
| v1.3.0 | 2026-09-30 | Repair installation, button labels (Xbox/PS/Switch), DRED by default, `gamecontrollerdb.txt`, texture extractor fix (#13), launcher polish and optimisation |
| v1.2.9 | 2026-09-26 | Self-explanatory diagnostics: always-on warnings (fps, disk, mixed installation), `vram`/`lim` in `perf`, VRAM guard |
| v1.2.8.2 | 2026-09-24 | The texture upscale stops sinking fps (level 0 only for dynamic textures) + `cfg`/`upx_dyn`/`texload` in `perf` |
| v1.2.8.1 | 2026-09-23 | The dump covers the uncompressed HUD/UI; RGBA8 packs; a cap of 4 versions per texture (issue #11) |
| v1.2.8 | 2026-09-21 | Texture dump fix: the chosen folder now reaches the plugin (`REXCVAR_QUERY`) |
| v1.2.7 | 2026-09-21 | PCSX2-style texture packs (D3D12 and Vulkan) |
| v1.2.6 | 2026-09-20 | Polished HD texture upscale (no stutter, RGBA8, anti-ringing min-size) + self-repair of `dbz3_user.toml` |
| v1.2.5 | 2026-09-19 | QoL on losing focus (mute/dim), disk diagnostics (`dbz3_io_logging`) and read-ahead |
| v1.2.4 / EX | 2026-09-19 | Real volume, new-version notice, FXAA/dither, GPU levers, portable user data |
| v1.2.3 | 2026-09-18 | Performance counter (`dbz3_perf_logging`) and AFS log silenced |
| v1.2.2 EX | 2026-09-17 | The launcher finds the executable by itself + ISO mode fixes + TOML fix |
| v1.2.1 | 2026-09-14 | Launcher hotfix (pipeline join, FSR label, mod list refresh) |
| v1.2.0 | 2026-09-14 | Renewed mod centre + polished HD↔HD Model Swap + FSR/CAS sharpness |
| v1.1.x | 2026-09 | Dual US+EU core, a single universal exe (SSSE3), disc mode (ISO), EU fixes, i18n |
| ≤ v1.0.x | 2026-08 | Initial stabilisation (intro/Demo/Duel fixes, mod centre, dual core) |

> Per-version detail in `docs/01_estructura/HISTORICO_RELEASES.md` (§E) of the
> repository.

## Mods (WIP)

> 🚧 **State: in development (WIP).** The mod system is experimental and may
> change. Use it with backups.

Mods are managed from the launcher's **Mods**, **Textures** and **Model Swap**
tabs. They **do not modify** the game files: they apply an overlay on specific
AFS entries, so each mod weighs only ~100 KB.

- **Model swap** native B3→B3: replaces the complete character (geometry +
  textures) with another one from the catalogue (183 characters), in any
  direction (virtual mid-insert).
- **Textures**: extract a character's textures to editable PNGs, edit them
  and rebuild the mod.
- **Texture packs**: replace textures with yours (e.g. AI-upscaled) **without
  touching the game's files or its memory**.
- **Music** (`og_music`): replaces the audio AFS files per region.
- **New characters** (v1.4.0, experimental, USA version): their own cells in
  the select without replacing anyone. Optional downloads:
  - `DBZ3HD-1.4.0-Personajes.zip` (Google Drive: https://drive.google.com/file/d/1zpwuuU7ITKZlC43nsTbp6s2wceBcwO85/view?usp=sharing) — Janemba, Android 19, Zarbon, Dodoria,
    Guldo, Jeice and Burter. Copy its `mods` folder next to `dbz3.exe`.
  - `DBZ3HD-1.4.1-Kit-Modding.zip` — tools to create and import characters
    (requires Python 3.11+; run `instalar_requisitos.bat` once).

## Release state

Story mode and the alternative modes have been verified in a complete
playthrough **with no known errors, crashes or failures** with the default
configuration (D3D12 + 2x upscaling + 60 FPS). The mod system is the
experimental part: swaps and textures work, but since they are customisable,
use them with a backup of your AFS files.

## Known bugs

- **Universal runtime (SSSE3) vs classic (AVX2)**: the universal one is ~5-10%
  slower on modern CPUs than the AVX2 runtime. If you notice it, use the
  fallback release `v1.1.0-clasico`.
- **Experimental Vulkan**: the Vulkan backend works but 3D rendering is ~6.5x
  slower than D3D12. Use **D3D12** (default).
- **New characters (experimental)**: some Budokai 1 throw technique comes out
  as a normal hit and some effect may not be perfect. They need the USA
  version and the data in a folder (not ISO mode).
- **New texts of v1.4.0** (launcher and quick menu): in Spanish and English;
  in Italian, German and French they show in English for now.

## Legal

An unofficial, non-profit research and preservation project. Not affiliated
with or endorsed by Bandai Namco, Shueisha, Toei Animation or any holder of
the Dragon Ball rights. No `.xex`, AFS or game data is distributed. The game
files are from your legal copy.

Repository: https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection
