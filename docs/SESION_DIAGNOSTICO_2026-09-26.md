# Session 2026-09-26 - Self-explanatory diagnostics (v1.2.9)

> Starting point: **SSGPrinceVegeta's latest logs** (`Logs
> SSGPrinceVegeta/parte 4/`, 2026-09-23). The user's goal: *"an iteration of
> improvements, polish and optimisation so that errors like the ones he had
> do NOT happen again"*.

## 1. What those logs really say

A sweep of ALL the `[warning]`/`[error]` lines of the 4 parts (24 files):

| Line | N | State |
|---|---|---|
| `XThread::Execute - No function registered at 820D54C8` | 4 | Fixed in v1.2.2 EX (it was the root `default.xex` = HD menu) |
| `Failed to parse config ...: unknown escape sequence '\G'` | 1 | Fixed in v1.2.2 (escaping) + v1.2.6 (self-repair) |

In other words: **part 4 (the latest) has not a single error**. What it has
is three subtler things, and those three are what was tackled here:

1. **The installation cannot be identified** (the underlying problem of the
   whole analysis): lines 2-3 say
   `user settings loaded from ...\DBZ-Budokai-3-HD-Collection-v1.2.1\dbz3_user.toml`,
   but the log contains messages that **do not exist in v1.2.1** (`fg=` ->
   v1.2.5, `upscale pausado` -> v1.2.6). That is: a v1.2.1 folder with new
   DLLs. A whole round of diagnosis was lost working out *which build*
   produced that log.
2. **FPS stuck at a sustained 31** (`upx` flat at 665, `max_frame_ms` 34-50
   with `cap=60`): exactly half the limit = **vsync at half rate** (the frame
   does not make 16.7 ms). With `internal_scale=3x` + MSAA + texture upscale
   (3x) in a heavy scene. The log does not say so anywhere.
3. **Slow disk**: `dbz3: io SLOW 42614us afs=data_usi.afs ... pre=12us` (42 ms
   of physical read with only 12 us of host work) + `read_avg_us` of 1.9-9.6 ms
   and `p95_us=8388` repeating. The game is in
   `E:\Game Roms\Old PC Games\...` (a mechanical disk). Nothing in the log
   points it out.

In addition, the **stale DLL trap** was re-confirmed: the game's
`cmake --build` copies the DLLs from `rexglue/bin` (avx2 and old) into its
output folder, so any test launched without copying the canonical ones back
measures another runtime (it happened twice during this session).

## 2. What has been implemented

### Runtime (rexgpu-xenos) - `command_processor.cpp` / `texture_cache.cpp`

- **VRAM telemetry** in the `perf` line: `vram=usage/budget` in MB, read from
  `IDXGIAdapter3::QueryVideoMemoryInfo` (1 s cache). Implementation note: this
  runtime's device **does not implement `IDXGIDevice`** (hr `E_NOINTERFACE`),
  so the adapter is kept alive in `D3D12Provider` (`GetAdapter()`; before, it
  was released after creating the device).
- **VRAM guard** (`lim=2`): with the local heap at 92 % or more **no new
  upscales are granted** (one line `upscale limitado por VRAM (uso X MB de Y MB)`).
  With the decision cached per key, like the rest of the budget: if it changed
  between creating the Nx resource and its reloads, the resource would be left
  unfilled.
- **`lim=` in `perf`**: the reason for the budget's last block (0 = none,
  1 = reload/video burst, 2 = VRAM). A user's log now says *why* it stopped
  upscaling textures.
- **Sustained-fps warning** (ALWAYS on, max 3 per session): if the fps stays
  below 55 % of the effective limit (`frame_cap`, or 60) for 3 windows in a
  row **and** expensive settings are on (scale > 1x, MSAA or texture upscale),
  it prints `dbz3: aviso - fps 31.0 sostenido con limite 60 (config: escala 3x3
  msaa=1 mejora_texturas=1) - el frame no llega al intervalo de presentacion
  (vsync a media tasa); baja la escala interna a 1x, ...`. Without expensive
  settings it does not warn: on a modest machine running below 60 is
  expected, not an error.

### Runtime (rexruntime) - `afs.cpp` / `host_path_file.cpp`

- **Slow-disk warning** (ALWAYS on, ONE line per session, does not depend on
  `dbz3_io_logging`): counts physical reads >= 50 ms and at the fifth one it
  warns with the volume and the worst case: `dbz3: aviso - 5 lecturas de disco
  lentas (peor caso 42000 ms, volumen E:) ...`. The read's clock is always
  taken (2 calls of ~20 ns per physical read); read-ahead cache hits do not
  count.
- This covers case 3 without the user having to turn anything on: the normal
  log stays clean and the line only appears when there is something actionable.

### Launcher - `update_check.cpp` + `launcher_state.cpp`

- **Runtime version stamp**: the DLLs **carry no VERSIONINFO**, so each one
  publishes its build through a cvar (`dbz3_runtime_build` / `dbz3_gpu_build`)
  from the new `rex/dbz3_build.h` (`DBZ3_RUNTIME_BUILD`). The cvar registry is
  shared, so the launcher reads them directly.
- **Mixed-installation check**: compares major.minor.patch of the exe with
  each component; a component without a stamp (an old build) **also** counts
  as mixed (it is exactly the "new exe over an old folder" case). If mixed: an
  orange banner at the top (with the culprit file) + `[warning]` in the log + a
  line in the Dev tab. AMD FidelityFX is listed but not compared (third party).
- **`dbz3: entorno ...` line** (one, when the launcher starts): the real
  system (`RtlGetVersion`, not `GetVersionEx`), RAM and **all** the installed
  versions: `dbz3: entorno os=10.0.26200 ram=32589MB dbz3.exe=1.2.9.0
  rexgpu-xenos=1.2.9 rexruntime=1.2.9 amd_fidelityfx_dx12.dll=1.0.1.0`. A
  report becomes conclusive without asking for another round.
- **Dev tab -> "Versions"**: the same versions on screen, with the mixed
  warning if any.
- **Combination warning** in Video: with internal scale > 1x **and** texture
  upscale on, the option itself explains that the cost multiplies and that if
  it drops to 30 the scale should stay at 1x (it is the most common cause of
  the "slow with HD textures" report).

### Tools

- `tools/copy_sdk_dlls.ps1`: copies the canonical DLLs of the baseline SDK to
  the build and warns if the stamp is missing. It exists so the stale-DLL trap
  does not repeat (it cost two invalid tests in this session).
- `tools/verify_release.ps1`: checks that `DBZ3_RUNTIME_BUILD` matches
  `src/version.rc` and that the stage's DLLs carry the stamp (otherwise the
  mixed-installation detection would warn on ALL new installations).

## 3. Evidence (local, RTX 4070 SUPER)

| Test | Result |
|---|---|
| Consistent installation (all 1.2.9) | `dbz3: entorno ... dbz3.exe=1.2.9.0 rexgpu-xenos=1.2.9 rexruntime=1.2.9` and **no** mixed warning |
| REAL mix: exe 1.2.9 + `rexgpu-xenos.dll` from 1.2.8.2 (extracted from the release zip) | `rexgpu-xenos=? rexruntime=?` + `[warning] instalacion mixta: rexgpu-xenos no coincide con dbz3.exe ...` + banner |
| Game with texture upscale (3x + MSAA + `hd_tex=3`) | 60.0 fps, 0 errors, `vram=2171MB/11231MB lim=0 upx_dyn=0 texload~1050` |
| VRAM guard (temporary brute force) | `upscale limitado por VRAM (uso 545 MB de 11231 MB)` + `lim=2` + `upx=0`, 60 fps with no errors |
| Disk/fps warning (temporary thresholds) | `5 lecturas de disco lentas (peor caso ... ms, volumen C:)` (once; with the real threshold the worst case would be >= 50 ms) and the fps warning 3 times at most |

## 4. Known limits (honest)

- The fps warning **does not distinguish** "vsync at half rate" from "GPU
  truly saturated": it says the frame does not make the presentation interval
  and to lower scale/MSAA/textures. With `perf` on, `vram=`+`lim=`+`texload=`
  let you separate VRAM / commands / GPU.
- Mixed detection only works **from 1.2.9 on**: a file without a stamp is
  reported as "cannot be identified" (which is already a useful warning), but
  its version cannot be told.
- The stamp is bumped by hand together with `src/version.rc`;
  `verify_release.ps1` is what watches it.
- The disk warning cannot be tested locally with the real threshold (SSD): it
  was validated with a temporary 1 us threshold and the 50 ms one restored.

> The PS5 build (`docs/PS5.md`) links these runtime warnings too; they end up
> in `/data/dbz3/dbz3-play.log` on the console.

## 5. How to check it

```powershell
# 1) Copy the canonical DLLs (ALWAYS after building the game)
powershell -ExecutionPolicy Bypass -File tools\copy_sdk_dlls.ps1
# 2) Consistent installation: `entorno` line with the three versions equal
powershell -ExecutionPolicy Bypass -File tools\long_run.ps1 -Action Start -Seconds 45 `
  -Label entorno -Overrides "dbz3_skip_launcher=false"
# 3) Game with the upscale on: `vram=`/`lim=` in the perf line
powershell -ExecutionPolicy Bypass -File tools\long_run.ps1 -Action Start -Seconds 180 `
  -Label hd -Overrides "dbz3_texture_upscale=3;dbz3_hd_textures=3"
powershell -ExecutionPolicy Bypass -File tools\long_run.ps1 -Action Status
```
