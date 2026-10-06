# COMMUNITY ROADMAP — Community feedback (historical, 2026-08-25)

> **SUPERSEDED by `docs/HOJA_DE_RUTA_2026_09.md`** (2026-09-02). Kept as a
> record of the P0-P5 community demand and its resolution. Rewritten on
> 2026-09-02 to fix the mojibake (§14.19).
> All of P0-P3 was **COMPLETED**; P4 (mod centre) and P5 (long-term vision)
> were absorbed into the current roadmap.

---

## SUMMARY OF THE COMMUNITY DEMAND

| Category | Reports | Perceived impact |
|---|---|---|
| **Startup/running** | Does not open, closes after "Play", "Entrypoint XEX not found" | High (blocks first use) |
| **CPU compatibility** | Requires AVX2 → 0xc0000142 on old CPUs | High (leaves users out) |
| **Performance** | 10 FPS on integrated graphics; the game "sped up" | Medium-high |
| **File structure** | Confusion `default.xex` / `assets/` vs root | Medium (first-use friction) |
| **Controls** | Keyboard/buttons do not respond in game | Medium |
| **New features** | Native Android, online, easy-to-manage mods | Low-medium (future vision) |

---

## PRIORITY 0 — UPDATE TO REXGLUE 0.10.0 (foundation)

### 0.1 ✅ Move the SDK to 0.10.0 — DONE and VALIDATED (2026-08-25)
- **Why**: the project used a 0.9.x base. **0.10.0** had just come out with
  relevant improvements: input (`gate mnk mouse look`, `comma-list binds`,
  `modifier prefixes`, `optional mouse`, `rstick keys`), ui (`imgui style
  hook`), cvar (`track value source`), system (better crash reporting and
  stability of the recompiled code), filesystem (POSIX access mode fix).
- **Risk**: an SDK "in early development" (breaking API). Our own runtime
  patch (virtual mid-insert in `afs.cpp`/`host_path_file.cpp`/
  `host_path_entry.cpp`) and the input/presenter fixes had to be re-applied.
- **Plan carried out**: SDK 0.10.0 built in parallel in `rexglue-sdk-0.10/`
  (without touching 0.9); patch re-applied (9 files); installed into `rexglue/`
  (backup `rexglue_0.9/`); dbz3.exe built against 0.10 (codegen regenerated:
  `REX_WEAK_FUNC` removed in 0.10); **validated in game** (mods + virtual
  mid-insert work).
- **Effort**: Medium-High. **Impact**: High. — **COMPLETED**.

---

## PRIORITY 1 — FIRST USE / STABILITY (blocking bug)

### 1.1 ✅ Automatic layout diagnosis + clear messages — DONE (2026-08-25)
- Validation banner in the launcher (`launcher_state.cpp` OnDraw): green
  `[OK] Game data in: <path>` or red with what is missing (default.xex / us / eu).
- **"Select data folder..."** button: native Windows dialog, validates `us/`/
  `eu/` or `default.xex` (`IsValidGameDataDir`), persists in `dbz3_game_dir`
  and **remounts the game live** (`RelocateGameData` → `RemountGameDrive`
  re-registers `game:/d:` + re-applies the region) without restarting.
- **PLAY blocked** when the assets are missing (`BeginDisabled`); the banner
  says how to fix it.
- `OnConfigurePaths` priority: CLI arg > `dbz3_game_dir` > auto-detection.
  Effective root in `dbz3::EffectiveGameRoot` (region.cpp).
- **Effort**: Low. **Impact**: High. — **COMPLETED**.

### 1.2 ✅ Immediate crash after Play (without a message) — DONE (2026-08-25)
- `src/main.cpp` SetupCrashHandler: minidump capture (`crash_*.dmp`) is kept.
  On an unhandled exception a "DBZ Budokai 3 - Error" window is shown with:
  the exception code, the address, the **log path** (`logs/dbz3_*.log` via
  `LatestLogPath`) and the minidump path. With a debugger attached it defers
  (`EXCEPTION_CONTINUE_SEARCH`). `std::terminate` also shows the window.
- **Effort**: Low-Medium. **Impact**: High. — **COMPLETED**.
- Pending (release): `README_PRIMER_ARRANQUE.txt` in the zip (reinforce the
  RELEASE_README section).

---

## PRIORITY 2 — HARDWARE COMPATIBILITY

### 2.1 ✅ Efficient AVX2 detector + fallback build — DONE (2026-08-25)
- **Key finding**: the game's exe (dbz3.exe) is built WITHOUT `-march`
  (baseline) — AVX2 lives ONLY in the SDK's DLLs. That is why the core is a
  single binary and only the DLLs change.
- The bootstrap `dbz3.exe` (`src/bootstrap.cpp`) checked CPUID and launched
  `dbz3_avx2\` or `dbz3_legacy\`. SDK v2 build with `-march=x86-64-v2` +
  `REXGLUE_OUTPUT_DIR`. Mods walk-up (`AfsModsRoot`/`ModsRoot`/`ModsOutDir`).
  Release with dbz3.exe + variants.
- **NOTE (2026-08-28, v1.1.1)**: the bootstrap was **REMOVED** (§9.1): now the
  whole SDK is built at baseline `-march=x86-64 -mssse3` → a single universal
  dbz3.exe (Core 2 2006+). The `v1.1.0-clasico` fallback (avx2 runtime)
  remains as a non-Latest release. Detail in `AGENTS.md` §9.
- **Effort**: Medium. **Impact**: High. — **COMPLETED** (evolved).

### 2.2 ✅ Backends / performance on modest machines — DONE (2026-08-25)
- **Reality**: Xenia/ReXGlue does NOT support OpenGL or D3D11 — only **D3D12
  and Vulkan** (fragment shader interlock / rasterizer-ordered views). D3D12 is
  ALREADY the MOST compatible backend. → **Do NOT pursue OpenGL/D3D11**.
- **What is practical**: per-GPU quality presets (`dbz3_quality_preset`
  auto/low/medium/high/ultra/manual; Auto detects the GPU via DXGI and applies
  a profile), a REAL **frame_cap** at 30 FPS (the `d3d12_presenter.cpp` patch
  restores the `frame_cap` cvar). Tracy profiling (build win-amd64-tracy) as
  optional fine-tuning.
- **Effort**: Low-Medium. **Impact**: Medium. — **COMPLETED**.

### 2.3 ✅ Frame pacing ("the game runs sped up") — DONE (2026-08-25)
- **Finding**: in SDK 0.10 the guest's pacing is done by the `vsync` worker of
  `GraphicsSystem`. With `vsync` OFF the vblank runs at ~1000 Hz → the logic
  runs ~16x = "sped up". The 0.9 `frame_cap` cvar no longer existed.
- **What was done**: `vsync` forced to true (the guest MUST run at 60 Hz; the
  placebo checkbox removed → "Game speed: fixed 60 FPS"). Real `frame_cap`
  restored (host presentation throttle). `dbz3_frame_cap` default 60.
- **Effort**: Low. **Impact**: Medium. — **COMPLETED**.
- Pending: validate in game the frame cap and the auto preset on a machine
  with integrated graphics; optional Tracy profiling.

---

## PRIORITY 3 — CONTROLS

### 3.1 ✅ Robust keyboard and controller (SDL compatibility) — DONE (2026-08-25)
- **Diagnosis**: the SDK's MnK driver existed complete but `mnk_mode` was
  `false` by default → the keyboard did nothing. The launcher's deadzone/rumble
  sliders were placebo (SDK 0.10 removed those cvars).
- **What was done**: `dbz3_mnk_mode` default **TRUE** (the keyboard emulates the
  controller out of the box). Controller via **XInput** (avoids the hang with
  RTSS/OBS); SDL as a selector for generic controllers (with a warning about
  the risk). **Configurable mapping** in the Input tab: 24 keybinds (syntax
  `Key`, commas = alternatives, `Shift+/Ctrl+/Alt+` = modifiers). **REAL
  deadzone/rumble** (`input_system.cpp` patch with `deadzone`/`rumble` cvars;
  rexruntime.dll's cvar registry shared with the exe).
- **Effort**: Medium. **Impact**: Medium-High. — **COMPLETED**.

---

## PRIORITY 4 — EASIER-TO-MANAGE MODS

### 4.1 Mod centre in the launcher — DONE (absorbed)
- **Install a mod from a `.zip`** (PowerShell Expand-Archive via base64
  `-EncodedCommand`; normalises a one-folder wrapper).
- **Mod profiles** (`mods/profiles.txt`, cvar `dbz3_mod_profile`).
- The Mods tab lists/enables/disables and edits manifests; vanilla core by
  default. Detail in `AGENTS.md` §8.
- **Effort**: Medium. **Impact**: Medium.

---

## LONG-TERM VISION (more effort, lower priority)

### 5.1 Native Android port
- Retarget the ReXGlue recompiler + GPU (Vulkan already on Android) to ARM64 +
  the launcher as an app. A big project. — Not started.

### 5.2 Online play
- Netplay (deterministic rollback-style sync) on top of the recompiler. Very
  complex. — Not started.

### 5.3 D3D9/10/11 compatibility
- **Not recommended / not viable**: rendering is D3D12/Vulkan by the SDK's
  design (§2.2). Better to invest in optimising D3D12 + tuning Vulkan.

### 5.4 Consoles (2026-10-06)
- A **jailbroken PS5** build now exists (Vulkan, adapted from mcla-recomp):
  see `docs/PS5.md`. Experimental, not yet run on a console.

---

## REFERENCES

| Topic | Where |
|---|---|
| Current roadmap (2026-09) | `docs/HOJA_DE_RUTA_2026_09.md` |
| Migration to Rexglue 0.10.0 | `docs/MIGRACION_REXGLUE_010.md` |
| Runtime patch (SDK) | `github/patches/` |
| Modding roadmap | `docs/HOJA_DE_RUTA.md` (historical) |
| Current state | `docs/01_estructura/ESTADO.md` |
| Session history | `docs/01_estructura/HISTORICO_AGENTS.md` |
| PS5 build | `docs/PS5.md` |
