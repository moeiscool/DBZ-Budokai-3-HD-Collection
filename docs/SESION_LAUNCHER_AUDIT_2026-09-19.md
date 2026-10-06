# Session 2026-09-19 — Launcher audit (dead controls + update check)

> A scan of the launcher after v1.2.3, compared with **Dusklight**
> (`E:\Games\Dusk`, a native reimplementation of Twilight Princess) to inspire
> effectiveness improvements. Goal: "the launcher working as well as possible".

## 1. Method

**All** the launcher's cvars (`dbz3_*`, 35 definitions in
`src/launcher/settings.cpp`) were cross-checked against the **199 cvars
registered in the SDK** (`REXCVAR_DEFINE_*` in `rexglue-sdk-0.10/src`), and
each one was followed to its real consumer (`ApplyUserSettingsToSdk` /
`ApplyRuntimeSettingsToSdk` / SDK plugins).

## 2. DEAD controls found (fixed)

| Control | Launcher cvar | What it wrote | Result |
|---|---|---|---|
| Master / Music / SFX / Voice volume (4 sliders) | `dbz3_master/music/sfx/voice_volume` | `SetSdkDouble("master_volume")` | **Dead**: the SDK has no `master_volume`/`music_volume`/`sfx_volume`/`voice_volume` (0 hits) |
| (also) | — | a fixed `SetSdkBool("audio_mute", false)` | The launcher **forced audio ON**: it could not be muted from the UI |
| Gamma | `dbz3_gamma` | nothing | **Dead**: there is no gamma cvar in the SDK (`gamma` only appears as a parameter/`gamma_render_target_as_unorm16`) |
| — | — | `SetSdkString("audio_output_device","")` | **Dead**: nonexistent cvar (orphan line) |
| Reset to defaults | — | fixed list | It forgot `dbz3_vrr` and `dbz3_hd_textures` |

**Root cause of the design**: the guest mixes ALL channels into a single
stream, so per-category volume (music/SFX/voice) cannot be separated on the host.

## 3. Changes applied

### SDK (rexruntime) — `src/audio/sdl/sdl_audio_driver.cpp`
- New cvar **`audio_gain`** (double, 0.0-1.0): `gain = GetOutputGain() *
  clamp(audio_gain, 0, 1)` in `SDLCallback`. `audio_mute` already existed.
- Patch archived in `github/patches/rexglue-sdk/src/audio/sdl/sdl_audio_driver.cpp`.

### Launcher
- **Real audio**: the "Master volume" slider → `dbz3_master_volume` → SDK
  `audio_gain`; the "Mute all audio" checkbox → `dbz3_mute` → SDK
  `audio_mute`; both apply instantly (`ApplyRuntimeSettingsToSdk`). The 3 dead
  sliders (music/SFX/voices) and their cvars were removed.
- **Gamma**: slider removed (it was decorative).
- **Reset to defaults**: added `dbz3_vrr=false`, `dbz3_hd_textures=1`,
  `dbz3_mute=false`; removed gamma and the dead volumes.
- **Update check** (`src/launcher/update_check.{h,cpp}`): queries
  `api.github.com/repos/novapowers0/DBZ-Budokai-3-HD-Collection/releases/latest`
  on a background thread (WinHTTP, 8 s timeouts, its own User-Agent), compares
  `tag_name` with the version read from the exe's own VERSIONINFO
  (`src/version.rc` = single source) and shows: green "New version available:
  vX" + a "Download" button (`ShellExecute`), "Version up to date (vX)", or a
  grey note if it fails (it never blocks PLAY). Privacy toggle
  `dbz3_update_check` in the Dev tab. Links `winhttp` + `version` in CMake.
- **i18n**: 10 new strings (ES/IT/DE/FR) in `i18n.cpp`.

## 4. Verification

- SDK build (`rexruntime`) + game OK. **DLL trap confirmed**: after the game's
  `cmake --build`, `rexruntime.dll` goes back to 10,863,616 B (stale) → copy
  the baseline back (**10,873,856 B**, with `audio_gain` + `dbz3_perf_logging`).
- Launcher: capture `launcher_final.png` → shows **"Version up to date
  (v1.2.3)."** (the update check works end to end) and there is **no** Gamma
  slider any more.
- Working audio (log): a test toml with `dbz3_master_volume = 0.35` +
  `dbz3_mute = true` → `dbz3: applied runtime settings -> ... audio_gain=0.35
  mute=true ...`. The cvar exists and is applied (before, the log printed
  `master_vol=0` because it did not exist).
- New tool: `tools/click_window.ps1` (click by client coordinates; in the ImGui
  launcher the synthetic click does not change tab without real focus — the
  Audio tab was verified through the log).

## 5. Dusklight — comparison (what we copy and what not)

| Dusklight | Us |
|---|---|
| `data_location.json` portable/AppData (`previousPath`) | `user_data/` next to the exe; **automatic fallback** to `Documents/dbz3` if the exe folder is not writable (below) |
| `backend.wasPresetChosen` (first-run wizard) | `dbz3_quality_preset=auto` (GPU detection) |
| flat `config.json` with dotted keys | `dbz3_user.toml` with Windows path escaping |
| Update check in prelaunch (checking/available/failed + download) | **implemented** (above) |
| `game.enableFpsOverlay` + configurable corner | FPS counter only in Dev |
| `achievements.json`, `texture_replacements/` | out of scope (our equivalent: Textures/Model Swap) |
| crashpad + pipeline cache | our own minidump + `dbz3_perf_logging` |

Pending (not done): `present_safe_area_x/y` (TV overscan) and the configurable
corner of the FPS counter.

## 6. Second batch (same date) — GPU knobs + user data (v1.2.4 EX)

Implemented what was left noted above (except overscan and the FPS corner).
Five new controls in the launcher, all wired to REAL SDK cvars, plus the
user-data fallback.

### New controls

| Launcher | Launcher cvar | SDK cvar | Where |
|---|---|---|---|
| Edge smoothing (FXAA) | `dbz3_fxaa` (`none`/`fxaa`/`fxaa_extreme`) | `swap_post_effect` | Upscaling |
| Colour dithering | `dbz3_present_dither` | `present_dither` | Upscaling |
| Mouse sensitivity | `dbz3_mnk_sensitivity` (0.1-5.0) | `mnk_sensitivity` | Controls (only with the mouse on) |
| Compile shaders in the background | `dbz3_async_shaders` | `async_shader_compilation` | Development |
| The game's occlusion queries | `dbz3_occlusion_queries` | `occlusion_query_enable` | Development |

FXAA runs **before** upscaling (`swap_post_effect`), so it combines with
FSR/CAS: it is the cheap antialiasing route for GPUs that cannot handle the
internal scale or MSAA. The two GPU toggles (async shaders, occlusion queries)
are **diagnostic levers** for the reported performance problem: they let you
rule out (or confirm) stutter from shader compilation and occlusion waits
without recompiling anything.

### Writable user data (`settings.cpp`)

`UserDataRoot()` decides where saves/memory cards + caches live
(`user_data/dbz3`, `xex_cache`, `iso_cache`) and `UserSettingsPath()` where
`dbz3_user.toml` goes:

1. If `<exe_dir>/user_data/dbz3` (or the exe folder, for the toml) is writable
   → **portable**, as before (no change for anyone).
2. If not (installed in `Program Files`, a network share, a blocked OneDrive)
   → `Documents/dbz3` (the SDK's `GetUserFolder()` = `FOLDERID_Documents`,
   which is exactly the runtime's default when `user_data_root` is empty).

The check is a real probe (create a folder + write/delete
`.dbz3_write_test`), cached (only once per process; the Dev tab shows the
path and whether it is portable). Without this, in a read-only folder saving
failed **silently** and settings/saves were lost.

> On **PS5** the executable folder resolves to `/data/dbz3` (through
> `REX_EXECUTABLE_PATH`), so `dbz3_user.toml` and `user_data/dbz3` live there
> (see `docs/PS5.md`).

### Third pass — the update check, polished (same tag `v1.2.4-EX`)

The version notice was the only visible part of the release the user could
not control, so the same asset was replaced with:

1. **Repacks** (commit `7a96385`, already in the previous asset):
   `VersionNewer` compares 4 components and `IsRepack()` marks a tag with a
   suffix (`1.2.4-EX`) or a FileVersion with build > 0 (`1.2.4.1`) ⇒
   **1.2.4 < 1.2.4-EX < 1.2.5**; an installed EX compares equal and does not
   self-notify, a 1.2.4 does get the notice. Before, the notice did not tell
   repacks apart (a 1.2.4 would never see the EX).
2. **Installed version always in the header**: `CurrentVersionLabel()`
   (`"1.2.4 EX"`) + state + buttons, via `ImGui::TextDisabled` + `SmallButton`.
3. **Manual re-check**: `RequestUpdateCheck()` ("Check for updates" button
   when up to date, "Retry" if it failed) with a `g_inflight` guard (one
   request at a time); `StartUpdateCheck()` keeps the per-frame idempotence
   (`g_autostarted`). The state goes back to "Checking for updates..." on repeat.
4. i18n: +3 strings and the `Version actualizada (vX)` variant removed (now
   redundant with the installed-version line).

### Verification

- **Functional (log)**: a toml with `dbz3_fxaa="fxaa_extreme"`,
  `dbz3_present_dither=true`, `dbz3_async_shaders=false`,
  `dbz3_occlusion_queries=false`, `dbz3_mnk_sensitivity=2.5` →
  `dbz3: applied runtime settings -> ... fxaa=fxaa_extreme dither=true
  async_shaders=false occ_queries=false mnk_sens=2.5 ...`. The values are read
  from the **SDK's** cvar registry (not the launcher's), so they confirm the
  wiring reaches the runtime. 0 errors.
- **Fallback**: `icacls <user_data/dbz3> /deny javie:(W)` → the game created
  `Documents/dbz3/cache` and kept working without errors. ACL removed and test
  folder deleted afterwards.
- **UI**: launcher capture OK. The header became `Installed version: v1.2.4 EX
  | Version up to date. | [Check for updates]` (image
  `%TEMP%\opencode\launcher_ua.png`), i.e. the installed EX does **not**
  self-notify and the running version is always in view. No `[error]`/
  `Assert` in `logs/dbz3_011.log`. The synthetic click still does not change
  tab (ImGui + real focus), so the new tabs were not captured as images.
- ⚠️ **DLLs**: the build overwrites `rexruntime.dll`/`rexgpu-xenos.dll` with the
  stale ones (`rexglue/bin`); after building, the baseline ones must be copied
  back. The CURRENT canonical baseline ones are `rexruntime.dll`
  **10,873,856 B** and `rexgpu-xenos.dll` **6,202,368 B** (the 6,165,504 B AGENTS
  §7 quotes is old). `verify_release.ps1` compares by SHA256 against that baseline.
