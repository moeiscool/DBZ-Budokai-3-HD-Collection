# Performance analysis — SSGPrinceVegeta's logs (part 2, 2026-09-18)

> Report: the same user with an **RTX 5090 + 9950X3D** (the one with the HD
> menu crash) says that now it runs **VERY slowly** for him. Logs in
> `Logs SSGPrinceVegeta/parte 2/` (`dbz3_012.log` … `dbz3_021.log`, sessions
> from 7 s to 199 s).

## 1. Configuration detected in the logs

| Setting | Observed value |
|---|---|
| Version | **v1.2.1** (path `DBZ-Budokai-3-HD-Collection-v1.2.1`) |
| Backend | `d3d12` |
| Internal scale | **`internal_scale=3x`** (9× pixels) |
| MSAA | `msaa=true` (native 2x) |
| Aniso | `aniso=5` (16x) |
| Effect | `fsr` (quality), `fsr_sharpness=0.2` |
| Vsync / cap | `vsync=true`, `cap=60` (`cap=165` in another session) |
| Preset | `ultra` (which in the launcher is **2x**, not 3x: 3x is manual) |
| Audio | endpoint **`CABLE Input (VB-Audio Virtual Cable)`** |
| Game path | `E:\Game Roms\Old PC Games\...` (drive unconfirmed) |
| Chosen GPU | `NVIDIA GeForce RTX 5090` ✅ (not the iGPU) |

There is not a single `[warning]`/`[error]` in the game sessions (014-021).

## 2. What the logs contain (what can be measured)

Practically **100 % of the lines are AFS reads**:

- `dbz3_020.log`: 1,718 lines / 145 s. Of them, 833 `AFS OVERRIDE MISS` +
  ~830 `AFS OVERRIDE LOOKUP` (330 `data_usi`, 273 `data_cmn`, 201 `adx_usa`,
  26 `lang_usa`).
- **Bursts of up to 480 lines in 10 s** (≈24 AFS reads/s), and during
  transitions an **almost perfect 50 ms cadence** (20 Hz) repeating the same
  entry.
- Median interval between lines: 0.000 s (back-to-back bursts).

In other words: the logs **do not allow quantifying the slowness** (they log
neither FPS nor frame times). They only make clear the game hammers the AFS.

## 3. Actionable findings

### 3.1 The AFS override log was unconditional (fixed)

`AfsFindModOverride` (`rexglue-sdk-0.10/src/filesystem/afs.cpp`) wrote
**2 lines with the full host path for EVERY AFS read**, even without mods and
without diagnostics. With the measured bursts (hundreds of reads per
transition) that is thousands of lines and formatting + I/O per session.

**Change**: the messages (`LOOKUP`/`HIT`/`MISS`/`mod_dir`) are now only emitted
if **`dbz1_diag_logging`** is on (Dev/diagnostic mode). Effect: readable logs
and less work per read. (It was not the main cause of the slowness, but it
was avoidable cost and noise, and it hid any other useful data.)

### 3.2 Performance instrumentation (new)

Cvar **`dbz3_perf_logging`** (default `true` at this date; **the final v1.2.5
changes it to `false`**, opt-in in the Dev tab), measured **at the guest's
real swap** (`D3D12CommandProcessor::IssueSwap`, `rexgpu-xenos`): it writes a
line every 5 s with the game's FPS and the worst frame of the interval:

```
[gpu] dbz3: perf fps=60.0 frames=301 window=5.01s max_frame_ms=20.4
```

⚠️ The first attempt was placed in the **UI presenter**
(`D3D12Presenter::PaintAndPresentImpl`) and **was useless**: that presenter
only paints the launcher (0 lines in game, nor with the window hidden/
off-screen, because the in-game present depends on the
`kConnectedPaintable`/`WM_PAINT` framing). The **guest swap** counter measures
the real game's frame limit and also works **without a visible window**
(essential for automated tests).

Complement: the settings that matter are recorded when the game starts
(`applied runtime settings -> internal_scale=... msaa=...`) and the UI
presenter keeps its own line (with `cap=`) to measure the launcher.

### 3.3 Hypotheses to check with the new log (in order)

1. **Internal scale 3x + MSAA** (a manual config above the "ultra" preset,
   which is 2x). It is the emulator's most direct cost lever: 3x = 9× render
   pixels + EDRAM resolves; with MSAA, more. Test: **1x and 2x**.
2. **Virtual audio device (VB-Audio Virtual Cable)**: a virtual endpoint can
   block the audio thread and drag the guest along. Test: a real audio output
   (or a bigger buffer).
3. **The game's drive (`E:` "Old PC Games")**: if it is an HDD, the AFS
   (286 MB) + streamed `adx_usa` produce stutter/slow loads. Test: SSD.
4. **Backend**: D3D12 is the recommended one (Vulkan is ~6.5× slower in
   `IssueSwap`; see `PLAN_1.1.1.md`).
5. Guest CPU: the recompiled code runs on one thread; with a 9950X3D it should
   not be the bottleneck, but the perf line will tell (low fps with a stable
   `max_frame_ms` = sustained cost; spikes = load/audio stalls).

## 4. What was changed in the runtime

| File | Change |
|---|---|
| `src/filesystem/afs.cpp` | Override log conditioned on `dbz1_diag_logging` (by name; the cvar lives in another module). |
| `src/graphics/d3d12/command_processor.cpp` | Guest FPS counter in `IssueSwap` (`dbz3_perf_logging`). Real measurement in game and without a window. |
| `src/ui/d3d12/d3d12_presenter.cpp` | UI presenter (launcher) counter with `cap=`. |
| `src/graphics/d3d12/texture_cache.*`, shaders | Texture upscale **disabled** (`dbz3_texture_upscale=1`); see `TEXTURAS_HD_RUNTIME_UPSCALE.md`. |

DLLs rebuilt and installed in `out/build/win-amd64-release/`
(`rexruntime.dll` 10,870,272 B, `rexgpu-xenos.dll` 6,184,448 B) and copied to
`github/patches/rexglue-sdk/`.

## 5. Request to the user (SSGPrinceVegeta)

1. Update to the build with the perf log and **send the logs** of a normal
   session (with the config he usually uses).
2. Try, measuring with the `perf` line: **scale 1x** and **2x** (with and
   without MSAA), and tell us which one runs fine.
3. Say whether "slow" is in **menus, fights, loads or everything**, and
   whether it is an FPS drop or **slow motion**.
4. Try with a **real audio device** (not the virtual cable) and, if the game
   is on an HDD, move it to an **SSD**.

## 6. Synthetic tests (offscreen, 2026-09-18)

Harness: **`tools/hidden_run.ps1`** (launches the game with the window
off-screen —not hidden, because hiding it stops the present—, applies
overrides to `dbz3_user.toml`, waits, kills the process, restores the toml and
summarises the log). Base recipe: `dbz3_skip_launcher=true` (+
`dbz3_perf_logging=true`), 20-45 s per case. **Careful**: text values in the
toml go in quotes (`dbz3_quality_preset="manual"`); without quotes the parser
**discards the whole file** and the game starts with the defaults (the log
only says so with an `[error] Failed to parse config ... expected 'false',
saw 'fs'`).

| Test | Config | Result |
|---|---|---|
| T1b | skip_launcher, diag OFF | 0 `AFS OVERRIDE` lines, 0 errors, 37 log lines |
| T2 | skip_launcher, `dbz1_diag_logging=true` (direct) | 0 lines → **the launcher rewrites the flag** (`dbz1_diag_logging = dbz3_diag_logging && dbz3_dev_mode`) |
| T3 | `dbz3_dev_mode=true` + `dbz3_diag_logging=true` | **16 `AFS OVERRIDE` lines** ✅ (gate OK in both directions) + guest FPS |
| S1-S5 | scale 1x / 2x / 3x / 3x+MSAA / 4x | **60.0 FPS in all** (`max_frame_ms` 19.7-22.4) on the title screen (RTX 4070 SUPER) |
| U1 | `dbz3_texture_upscale=2` | `DBZ3 texture upscale pipeline ready (x2)` + 60 FPS + 0 errors ✅ (the parked feature initialises fine) |
| P1 | `dbz3_perf_logging=false` | 0 `perf` lines ✅ |

**Conclusion of the sweep**: the **title screen is not GPU-bound** even at 4x,
so it does not discriminate between configurations. To really measure it has
to be done **in a fight** (where the cost is): repeat the sweep with the
`perf` line while playing, or ask the user for a fight session with the logs.

## 7. Result in a real fight (2026-09-18, RTX 4070 SUPER)

A complete **CPU vs CPU** fight at `internal_scale=2x` (`dbz3_082.log` with
MSAA ON, `dbz3_083.log` with MSAA OFF; ~6.5 min of fighting each, 78-79
windows of 5 s):

| Session | Config | fps min / median / max | worst frame | windows <58 fps |
|---|---|---|---|---|
| dbz3_082 | 2x + MSAA ON | 50.7 / **59.9** / 60.1 | **782 ms** (once) | 1 |
| dbz3_083 | 2x + MSAA OFF | 51.1 / **60.0** / 60.1 | **773 ms** (once) | 1 |

Conclusions:
- **MSAA changes nothing** on this machine at 2x (both at 60).
- The rest of the fight is a **solid 60.0 FPS** (`max_frame_ms` alternating
  16.7 / 19-20 ms = normal pacing jitter).
- **The only real event**: a **~0.78 s** frame right at the start of the fight
  (the *first* window of each session), i.e. a **one-off load/hitch**
  (textures/models/stage of the fight), not sustained slowness. If users
  report a hitch at the start, investigate that load path.
- Note: in `dbz3_083` the saved toml had `msaa=true`; the user turned it off in
  the launcher and the runtime re-applied it when PLAY was pressed (that is
  why the log has two `applied runtime settings` lines, the second one already
  with `msaa=false`).
