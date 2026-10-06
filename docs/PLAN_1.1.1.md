# v1.1.1 DESIGN PLAN — Debugging, internal improvement and Linux foundations

> Design document of the v1.1.1 phase (successor of the universal v1.1.0).
> Goal: close the loose ends from feedback, harden the runtime, tidy the
> internal process and **lay the foundations of a Linux port**.
> State: design approved by AGENTS §3.4/§14 (consolidated) — phases in progress.

---

## 1. Context and principles

v1.1.0 left the project with **a single universal executable** (SSSE3
baseline) and a clean GitHub (v1.1.0 Latest + v1.1.0-clasico as fallback).
User feedback (v1.0.6 → v1.1.0) is practically closed; what remains is:

- **Robustness loose ends** (error paths, startup, teardown).
- **Internal process improvements** (the fragility of `github/` as a mirror repo).
- **Portability foundations** (the SDK is already multiplatform; `src/` is not).

Principles of the phase: (1) the current Windows build must never break,
(2) every change is validated with a smoke test, (3) do not touch the
hard-won "single exe" architecture, (4) the PS2→B3 model port is **paused**
(parallel work, it does not block 1.1.1).

---

## 2. Phase A — Debugging (robustness, open feedback)

### A1. ✅ No assets → clear message, no crash (DONE in 1.1.1)
- **Symptom**: with the data folder empty, the process opened the window and
  died with 0xC0000005 (teardown after `Runtime::Setup` failed).
- **Fix applied** (`src/main.cpp`): pre-flight in `OnPreSetup` — if there is no
  `default.xex` in the effective data folder, a clear MessageBox is shown (how
  to place the assets) and it exits cleanly (`_Exit(1)`). Validated: exit 1
  without a crash; the happy path still reaches the launcher at ~880 ms.

### A2. ✅ Startup timing markers (DONE in 1.1.1)
- **Reason**: reports of a "slow black screen before the launcher" (§14.10).
- **Fix applied**: `PhaseLog()` records ms since start in every override
  (`OnPreSetup/OnPostSetup/OnCreateDialogs/OnPreLaunchModule/OnPostLaunchModule`).
  With this, a user's log settles whether the bottleneck is the D3D12/swapchain
  init (gap until `first present OK`) or something earlier.

### A3. Pending — intermittent `std::terminate` in `LaunchModule` (mitigated, not reproduced)
- §14.14: try/catch + stack dump added; the exact throw is still not located
  (it does not reproduce cold). The measure is diagnostic: if a user hits it,
  the log will bring `LaunchModule deferred threw std::exception: <msg>` + the
  stack. **1.1.1 action**: analyse that message if it arrives; if not, close
  as "mitigated".

### A4. Pending — teardown/crash window after guest failures
- Check that the failure paths (`ConstructRuntime`, a hung guest thread,
  `OnGuestThreadExit`) do not leave a zombie process or a crash without a
  window. Verify with tests without assets, with half regions (us/ without
  eu) and with an unknown xex.

### A5. Pending — validate the EU core in real fights
- §14.13/14.16: the EU boot is stable and the demo passes, but the deep paths
  (real fights, events, skills) could reveal unregistered functions.
  **Action**: a play session with the dual core and
  `DBZ3_COLLECT_UNREGISTERED=1` to collect; iterate on `dbz3_config_eu.toml`.

### A6. Pending — Japanese in the selector
- The launcher translates EN/ES/IT/DE/FR; the game has 6 languages (JP
  included). Decide whether the launcher is translated to JP or clearly marked
  "not available".

---

## 3. Phase B — Internal improvement (process)

### B1. ✅ `tools/sync_github.ps1` (DONE in 1.1.1)
- `github/` is a versionable mirror repo; the manual sync (§9.1) was fragile.
- **Fix**: a script that replicates the process (src/docs/awo_tools/mod center
  hd/tools + root files), respects `.gitignore` (keeps the canonical
  `tools/*.exe`, does not touch `mods/`), with `-DryRun`. It reminds that
  `patches/` is manual.

### B2. ✅ Single-source version (DONE in 1.1.1)
- The version lived in 3 places (version.rc, make_release.ps1, RELEASE_README).
- **Fix**: `make_release.ps1` reads `VERSION_MAJOR/MINOR/PATCH` from
  `src/version.rc` by default (override with `-Version` for suffixes like
  `-clasico`).

### B3. Pending — clean up obsolete tools/documents
- `awo_tools/analyze_bin_hd.py` is OUTDATED (§13.2, the 010 "PS3" layout is
  wrong for X360) → mark or fix.
- `docs/HOJA_DE_RUTA_COMUNIDAD.md` has mojibake (§14.19) → rewrite.
- `tools/make_release.ps1` already warns NOT to use UPX (§14.20) — docs OK.

### B4. Pending — release CI-lite (repeatable verification)
- A `tools/verify_release.ps1` script that, given the stage, checks: hashes of
  the canonical DLLs, presence of the V-Sync clamp (string in rexgpu), the
  exe's VERSIONINFO, absence of game assets in the zip. Reusable before
  uploading.

### B5. Pending — note in RELEASE_README about the fallback
- Add to RELEASE_README the existence of `v1.1.0-clasico` and when to use it.

---

## 4. Phase C — Linux foundations (see `docs/PLAN_LINUX.md` for the detail)

Summary of the state after the phase (audit + guards):

- **The SDK is already portable**: `REX_PLATFORM_WIN32/LINUX/MAC`, `*_win/*_posix`
  pairs, Vulkan ON by default on Linux, SDL input/audio, `std::filesystem`
  filesystem + abstracted `FileHandle`. The bottleneck was `src/`.
- **DONE in 1.1.1 (platform guards in `src/`)**:
  - `settings.cpp`: **portable** MD5 (drops CryptoAPI) for `CheckDefaultXex` +
    DXGI GPU detection guarded with a fallback ("medium" tier) + per-platform
    backend defaults (`d3d12`+`xinput` on Windows, `vulkan`+`sdl` elsewhere).
  - `launcher_state.cpp`: COM dialogs (PickFolder/PickFile) and UTF-16
    conversions guarded with a "cancelled" fallback (portable dialog pending).
  - `mod_pipeline.cpp`: `CreateProcessW` guarded (fallback with a clear error).
  - `mods.cpp`: it already had a non-Windows fallback for the zip installer.
  - `main.cpp`: `OutputDebugStringA` as a no-op outside Windows; the crash
    handler was already Win32-only; portable pre-flight.
- **Pending for the real Linux build**:
  1. Portable file dialogs (SDL/GTK/zenity) for the launcher.
  2. Portable script spawning (`posix_spawn`) in `mod_pipeline.cpp`.
  3. Portable zip extraction (libzip/minizip) in `mods.cpp`.
  4. Check that the SDK's `ppc/` and `codegen/` have no residual Win32.
  5. CMake `linux-*` preset + dependency installation (Vulkan, SDL3, X11-xcb,
     Wayland) and validate Vulkan as the game backend (experimental today:
     6.5x slower than D3D12 in IssueSwap — the port's performance challenge).

> Those portability guards are also what lets the DBZ3 host sources
> (`settings.cpp`, `region.cpp`, `mods.cpp`, …) compile for the PS5 target
> (`docs/PS5.md`).

---

## 5. 1.1.1 acceptance criteria

1. The Windows build (dual + release) compiles without new warnings and the
   package smoke test passes (launcher shown + first present OK + no FATAL).
2. No assets → clear message and clean exit (never 0xC0000005).
3. The startup log allows diagnosing the "black screen" (A2 markers).
4. `tools/sync_github.ps1` syncs in a single command and `make_release.ps1`
   generates the zip with the version from `version.rc`.
5. `src/` conceptually compiles on Linux (guards in place); `PLAN_LINUX.md`
   defines the port's order of work.
6. Release 1.1.1 packaged (universal) + `-clasico` fallback updated.

---

## 6. Work not included in 1.1.1 (parallel or later)

- PS2→B3 model port (pipeline `port_ps2_b3_*`): **paused by the user's
  decision** (AGENTS §3.4/§15). It does not block 1.1.1.
- The Vulkan backend's performance challenge (needs a profiling session on
  Linux).
- A publishable Linux version (it is the long-term goal; 1.1.1 only lays the
  code foundations).
