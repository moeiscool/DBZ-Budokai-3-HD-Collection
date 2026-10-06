# MIGRATION TO REXGLUE 0.10.0 — STATE AND RESUME POINT

> Updated: 2026-08-25. Working document to resume the ReXGlue SDK migration
> **0.9.0 → 0.10.0** in a future session without losing context.
> **✅ MIGRATION COMPLETE AND VALIDATED IN GAME (2026-08-25)**: SDK 0.10.0
> installed in `rexglue/` (backup `rexglue_0.9/`), dbz3.exe built against 0.10,
> mods and virtual mid-insert working. Only release/README updates remain
> before uploading to GitHub (when the general plan is complete).
>
> **Note (2026-10-06)**: the experimental PS5 build also targets v0.10.0
> (commit `f5337cd`): `ps5/make_ps5.sh` clones the tag, copies
> `patches/rexglue-sdk/` and applies the PS5 patches. See `docs/PS5.md`.

---

## 1. GOAL (P0 of the roadmap)

Move the SDK from `rexglue-sdk` (base **0.9.0**, `CMakeLists.txt`
`VERSION 0.9.0`) to **0.10.0** (stable release `v0.10.0`, tag 2026-08-21,
commit `f5337cd`), re-applying the **runtime patch** (virtual mid-insert +
whole-file override + dbz1 cvars) that is the heart of the mod system.

Expected benefits of 0.10.0: input improvements (`comma-list binds`, `gate mnk
mouse look`), `cvar track value source`, better crash reporting (`report guest
arena base`, APCs per trap frame, cr2-cr4), `imgui style hook`.

---

## 2. WHAT HAS BEEN DONE (COMPLETED) — 2026-08-21

### 2.1 SDK 0.10.0 cloned and submodules
- **Path**: `rexglue-sdk-0.10/` (sibling of `rexglue-sdk/`, NOT the project's
  git repo; it is a git clone of the `v0.10.0` tag).
- Clone: `git clone --branch v0.10.0 --single-branch --depth 1
  https://github.com/rexglue/rexglue-sdk.git rexglue-sdk-0.10`
- Submodules: `git -C rexglue-sdk-0.10 submodule update --init --depth 1` (22
  submodules downloaded OK).

### 2.2 Build configured and compiled (rexruntime)
Same command as 0.9:
```powershell
cmake -G Ninja -S rexglue-sdk-0.10 -B rexglue-sdk-0.10\out\build-win-vulkan `
  -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe" `
  -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe" `
  -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" `
  -DREXGLUE_ENABLE_FIDELITYFX=ON -DREXGLUE_USE_VULKAN=ON `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=x86-64-v3"
```
Config summary: Version 0.10.0, C++23, D3D12=ON Vulkan=ON FidelityFX=ON.

### 2.3 🔴 TWO 0.10.0 BUILD BUGS SOLVED (local workarounds)

**Bug 1 — libmspack (wrappers)**: the `libmspack` submodule in 0.10
restructured `cabextract/mspack/`: the `.c`/`.h` files are now **wrappers**
with a relative path (`../../libmspack/mspack/lzxd.c`) instead of real code.
ReXGlue's CMake compiles `cabextract/mspack/lzxd.c` as a source → fails with
`expected identifier or '('`.
- **Fix**: copy the real code from `thirdparty/libmspack/libmspack/mspack/`
  over `thirdparty/libmspack/cabextract/mspack/` (ReXGlue only needs lzxd.c).

**Bug 2 — FidelityFX .rc UTF-16**: `ffx_api_dll.rc` (in
`out/build-win-vulkan/_deps/fidelityfx-src/ffx-api/src/resource/`) is
**UTF-16 LE with BOM**, and `llvm-rc.exe` does not support it → `fatal error:
UTF-16 byte order mark detected`.
- **Fix**: convert the file to **UTF-8 without BOM**
  (`ReadAllText(Unicode)` + `WriteAllText(UTF8Encoding(false))`).
- ⚠️ Both workarounds are lost if the build is re-cloned/cleaned. They live in
  `out/build-win-vulkan/_deps/` (ffx) and `thirdparty/libmspack` (local).

### 2.4 ✅ Runtime patch PORTED to 0.10 (the 4 files + 3 cvars)

In 0.10 the filesystem was refactored: `src/filesystem/afs.cpp` and
`include/rex/filesystem/afs.h` **NO LONGER EXIST** (they were removed), and
`host_path_file.cpp` (66 lines) / `host_path_entry.cpp` (183 lines) are much
simpler (no AFS/override logic). The full patch is NOT copied as is: **it has
to be ported**. That is already done:

1. **`include/rex/filesystem/afs.h`** — created (copied from the 0.9 patch,
   compatible API: `AfsFindEntry`, `AfsFindModOverride`,
   `AfsFindModFileOverride`, `AfsListMods`, `AfsResetModCache`,
   `AfsSetModEnabled`, `AfsRegionFileName`, `AfsGetVirtualTable`,
   `AfsTranslateOffset`, `AfsModsRoot`).
2. **`src/filesystem/afs.cpp`** — created (copied from the 0.9 patch, compiles
   without changes; uses `rex::path_to_utf8` and
   `rex::filesystem::GetExecutableFolder`, which DO exist in 0.10).
3. **`src/filesystem/CMakeLists.txt`** — `afs.cpp` added to `rexfilesystem`.
4. **`src/filesystem/devices/host_path_file.cpp`** — `ReadSync` logic ported:
   virtual AFS table (mid-insert), `AfsTranslateOffset`, per-entry override
   (`AfsFindModOverride`). The hook is identical to 0.9 (same `ReadSync`).
5. **`src/filesystem/devices/host_path_entry.cpp`** — `Open()` ported: audio
   overrides (`dbz1_audio_jp`), region (`dbz1_region`), diag log and
   `AfsFindModFileOverride` (whole file). The 0.10 `Open()` was simple.

### 2.5 ✅ The 3 dbz1 cvar files restored in 0.10

0.10 removed the 3 files that define the shared cvars (needed to link
`REXCVAR_DECLARE` in host_path_entry.cpp):
- `src/system/dbz1_audio_jp_flag.cpp`
- `src/system/dbz1_diag_flags.cpp`
- `src/system/dbz1_region_flag.cpp`

Copied from SDK 0.9 and added to `src/system/CMakeLists.txt`
(`REXSYSTEM_SOURCES`). **Without them, the rexruntime link fails** with
`undefined symbol: FLAGS_dbz1_*_storage_(void)`.

### 2.6 ✅ Result: rexruntime.dll 0.10.0 BUILT

- `cmake --build rexglue-sdk-0.10/out/build-win-vulkan --target rexruntime` →
  **exit 0**.
- Output: `rexglue-sdk-0.10/out/win-amd64/rexruntime.dll` (**10933248 B**).
- Verified: it contains the patch markers `AfsGetVirtualTable`,
  `AfsTranslateOffset`, `AfsFindModOverride`, `AfsFindModFileOverride`
  (Select-String = True).
- ⚠️ `rexgpu-xenos.dll` (the GPU plugin) and the rest of the full SDK have NOT
  been built yet, nor installed in `rexglue/`.

---

## 3. WHAT IS LEFT (NEXT STEPS IN ORDER)

### 3.1 Build the rest of SDK 0.10 (GPU plugin and tooling)
The game links `rex::gpu-xenos` (rexgpu-xenos.dll) as well as `rex::runtime`.
```powershell
cmake --build rexglue-sdk-0.10/out/build-win-vulkan   # everything (or --target rexgpu-xenos)
```

### 3.2 Install SDK 0.10 into `rexglue/` (the local install the game uses)
The game resolves the SDK like this (verified in
`out/build/win-amd64-release/CMakeCache.txt`):
- `CMAKE_PREFIX_PATH = .../rexglue`
- `rexglue_DIR = .../rexglue/lib/cmake/rexglue`

**Install plan** (do NOT delete `rexglue/` without a 0.9 backup):
1. **Back up** the installed SDK 0.9: rename `rexglue/` → `rexglue_0.9/` (or
   copy) to be able to revert.
2. **Install 0.10**: if SDK 0.10 has an `install` target
   (`cmake --install rexglue-sdk-0.10/out/build-win-vulkan --prefix rexglue`),
   use it. If it does not generate `lib/cmake/rexglue/`, replicate the 0.9
   structure by hand: `bin/` (DLLs), `lib/` (.lib + cmake configs), `include/`
   (headers), `cmake/` (SDL3 configs), `licenses/`, `share/`.
   - Bare minimum to build the game: `rexglue/lib/rexruntime.lib`,
     `rexglue/lib/rexruntime.dll` (or bin/), `rexglue/include/`,
     `rexglue/lib/cmake/rexglue/`, and the libs it links (fmt, spdlog, SDL3,
     mspack, xxhash, simde, etc. — the SDK's `install` exports them
     automatically).
3. **Check** that `find_package(rexglue)` finds version 0.10.

**Safer alternative** (without touching `rexglue/` yet): reconfigure the game
build with `-DCMAKE_PREFIX_PATH=.../rexglue-sdk-0.10/out/build-win-vulkan` or a
0.10 `install` in a new path, and build `dbz3` against it. That way 0.9 stays
intact and it is easy to revert.

### 3.3 Build the game (dbz3.exe) against 0.10
```powershell
cmake --build "out\build\win-amd64-release"
```
⚠️ **Known lesson (AGENTS §13.6/§14)**: when rebuilding, cmake may overwrite
the build's `rexruntime.dll` with the one installed in `rexglue/bin`. After the
build, copy the correct 0.10 DLL to the build and to `github/release-stage/`.

### 3.4 Re-validate the project's own fixes on 0.10
- **Input**: `input_backend = "xinput"` (fix for the hang with RTSS/OBS) —
  check it still works (0.10 changed input: `gate mnk mouse look`,
  `comma-list binds`).
- **`CallInUIThreadSynchronous` timeout** (windowed_app_context.cpp) — check
  whether 0.10 includes it or it has to be re-applied.
- **Presenter pacing** (`WaitForUITickFromUIThread`) — check.
- **Launcher**: the project links runtime cvars
  (`REXCVAR_DECLARE(bool, dbz1_diag_logging)` in settings.cpp) — confirm that
  the symbol `FLAGS_dbz1_diag_logging_storage_()` is exported the same way in
  0.10.

### 3.5 Test in game (end to end)
- Start the launcher → Play → enter battle.
- Check that mods still work: `tex_91` (entry 91) and some swap (e.g.
  `sw_vegeta424`, entry 327 with virtual mid-insert — it EXERCISES the virtual
  table, the most delicate point).
- Check us/eu region, JP audio, and that NO .bmp files are generated with
  Dev+Diag off.

### 3.6 Update the repo patches (github/patches/)
Once the port is validated, update `github/patches/` with the 0.10 files (now
6: `afs.h`, `afs.cpp`, `host_path_file.cpp`, `host_path_entry.cpp` + the 3
`dbz1_*_flag.cpp`, and the 2 modified CMakeLists) + a patch README explaining
the refactoring. Decide whether to also keep the 0.9 patches for anyone using
0.9.

---

## 4. REFERENCES AND USEFUL DATA

| Item | Path / value |
|---|---|
| Cloned SDK 0.10 | `rexglue-sdk-0.10/` (git tag v0.10.0, commit f5337cd) |
| SDK 0.9 (current) | `rexglue-sdk/` (CMakeLists `VERSION 0.9.0`) |
| Install used by the game | `rexglue/` (CMAKE_PREFIX_PATH → `rexglue/lib/cmake/rexglue`) |
| SDK 0.10 build | `rexglue-sdk-0.10/out/build-win-vulkan/` |
| SDK 0.10 output | `rexglue-sdk-0.10/out/win-amd64/` |
| rexruntime.dll 0.10 (patched) | `rexglue-sdk-0.10/out/win-amd64/rexruntime.dll` (10933248 B) |
| Original patches (0.9) | `github/patches/rexglue-sdk/` (4 files + README) |
| Game build | `out/build/win-amd64-release/` |
| Game build DLLs | `out/build/win-amd64-release/rexruntime.dll`, `rexgpu-xenos.dll` |
| Tools | `C:/Program Files/LLVM/bin/clang++.exe` (22.1.8), `ninja` 1.13.2 |

### Exact flow of the patch (what each file does)
1. `afs.cpp`/`afs.h` → AFS index parsing + mods + virtual mid-insert table.
2. `host_path_file.cpp::ReadSync` → intercepts reads of `data_cmn.afs`: serves
   the virtual table (header+table), translates offsets, or serves the
   override.
3. `host_path_entry.cpp::Open` → whole-file override + JP audio + region.

### Patch verification logs in game (expected format)
```
AFS OVERRIDE HIT (folder): ...\mods\<mod>\us\data_cmn.afs\327\geom.bin
AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=...
```

---

## 5. RISKS AND PENDING DECISIONS

- **Breaking API**: 0.10 is "early development"; the filesystem refactoring
  already broke the patch (it had to be ported). Other subsystems (input,
  presenter) may have changes affecting the launcher fixes.
- **mspack/FFX workarounds**: if the 0.10 build is deleted the 2 fixes (§2.3)
  must be re-applied. Document them in the patch README.
- **Decision**: install 0.10 over `rexglue/` (with a `rexglue_0.9/` backup) vs
  use a separate install. Recommended: **install into `rexglue/` with a
  backup** because the project flow is already configured that way (fixed
  CMAKE_PREFIX_PATH).
- **Do not touch yet** `rexglue-sdk/` (0.9): it remains the project's working
  SDK until 0.10 passes in-game validation.

---

## 6. STATE SUMMARY

- [x] Release 0.10.0 confirmed (v0.10.0, 2026-08-21)
- [x] SDK 0.10 cloned + submodules
- [x] Build configured (D3D12+Vulkan+FFX, clang 22, x86-64-v3)
- [x] 2 build bugs solved (mspack wrappers, ffx .rc UTF-16)
- [x] Runtime patch ported (afs.h/afs.cpp recreated, host_path_* ported)
- [x] 3 dbz1 cvars restored + CMake
- [x] **rexruntime.dll 0.10.0 built with the patch (10933248 B, markers OK)**
- [x] **rexgpu-xenos.dll 0.10.0 built (6207488 B) + full SDK (rexglue.exe, libs)**
- [x] **SDK 0.10 installed in `rexglue/` (0.9 backup → `rexglue_0.9/`) — PACKAGE_VERSION 0.10.0**
- [x] **dbz3.exe built against 0.10 (17298432 B, 2026-08-25)** — see §7
- [x] **Own fixes re-validated: both SDK ones are native in 0.10** — see §7.3
- [x] **✅ VALIDATED IN GAME (user, 2026-08-25)**: mods `swap_96_on_327`
      (simple override) + `tex_91` OK, and **virtual mid-insert OK**
      (`sw_vegeta424`, bin 126976 > to_read 106496). **Migration COMPLETE.**
- [x] **Update github/patches/ (9 files 0.10) + README** — done 2026-08-25
- [ ] **When the general plan is complete**: update release/README + README for
      SDK 0.10 before uploading to GitHub

---

## 7. SESSION 2026-08-25 — FULL SDK, INSTALL AND GAME BUILT

### 7.1 What was done
1. `cmake --build rexglue-sdk-0.10/out/build-win-vulkan --target rexgpu-xenos`
   → rexgpu-xenos.dll 0.10 (6207488 B). Full SDK build → rexglue.exe also
   built.
2. **Install**: `rexglue/` → renamed to `rexglue_0.9/` (backup), then
   `cmake --install rexglue-sdk-0.10/out/build-win-vulkan --prefix rexglue`.
   Verified: `rexglueConfigVersion.cmake` PACKAGE_VERSION = "0.10.0",
   `rexglue/bin/{rexruntime,rexgpu-xenos,amd_fidelityfx_dx12,TracyClient}.dll`,
   `rexglue/lib/rexruntime.lib` (5997310 B) with the 3 dbz1 symbols exported
   (llvm-nm: `FLAGS_dbz1_{diag_logging,audio_jp,region}_storage_` = T).
3. **Build dbz3 against 0.10**:
   - The game build was configured against the **sister project dbz1's SDK**
     (`DBZ Budokai HD Collection/rexglue-sdk/out/install/win-amd64`, Debug) —
     rexglue_DIR hardcoded in the cache. It was reconfigured cleanly (deleted
     CMakeCache.txt + CMakeFiles) with `CMAKE_PREFIX_PATH=.../rexglue` and
     `CMAKE_BUILD_TYPE=Release`.
   - **🔴 ROOT CAUSE of the build failure (2 errors)**:
     a) `cmake --preset win-amd64-release` resolved `clang` through PATH to the
        **retcomm toolchain (x86_64-w64-windows-gnu, libstdc++)**, which does
        NOT have `std::chrono::clock_time_conversion` → error in
        `rex/chrono/chrono.h`. Fix: use `C:/Program Files/LLVM/bin/clang++.exe`
        explicitly (MSVC target). The original build already used LLVM's
        clang.
     b) The generated code (0.9) used `REX_WEAK_FUNC`, a macro **removed in
        0.10** (the 0.10 template `pch_h.inja` emits `DEFINE_REX_FUNC` without
        it). Fix: **regenerate `generated/` with the 0.10 codegen**:
        `cmake --build out/build/win-amd64-release --target dbz3_codegen`
        (previous backup of `generated/` in %TEMP%). 94 files written,
        `dbz3_manifest.toml` auto-stamped `sdk_version = "0.10.0"`, now 44
        `dbz3_recomp.*.cpp` files.
   - Build OK: dbz3.exe (17298432 B). `rexglue_configure_target` staged the
     0.10 DLLs automatically (rexruntime.dll 10933248, rexgpu-xenos.dll
     6207488). `amd_fidelityfx_dx12.dll` (5420544, 0.10) and
     `TracyClient.dll` were also copied from the install.
   - ⚠️ In 0.10 there is NO `amd_fidelityfx_vk.dll` (DX12 only). Experimental
     Vulkan without Vulkan FFX.
4. **Smoke test**: dbz3.exe starts, D3D12 init (RTX 4070 SUPER), guest arena
   mapped, "launcher shown, waiting for Play". No crash.
5. **Validation of own fixes** (§3.4):
   - **CallInUIThreadSynchronous timeout**: ALREADY included in 0.10
     (`windowed_app_context.cpp` lines 97-132, with a timeout message).
   - **Presenter pacing** (`WaitForUITickFromUIThread`): ALREADY included in
     0.10 (`presenter.cpp` lines 1629-1646, `ui_tick_last_paint_time_` +
     sleep_until).
   - **REXCVAR dbz1**: symbols exported by the 0.10 lib and the exe links
     fine.
   - **Input xinput**: project cvar, flow unchanged; validate in game.

### 7.2 State of the game build (win-amd64-release) after the migration
- dbz3.exe 17298432 B (25/08 12:58) — Release, linked against 0.10.
- rexruntime.dll 10933248 B (0.10, patch verified: AfsGetVirtualTable /
  AfsFindModOverride / AfsFindModFileOverride = True).
- rexgpu-xenos.dll 6207488 B (0.10).
- amd_fidelityfx_dx12.dll 5420544 B (0.10).
- Active mods: `swap_96_on_327` (simple override, exactly 106496 B) and
  `tex_91`.
- **Cleanup done (25/08)**: removed the ~28 diagnostic `black_*.bmp`/
  `frontbuf_*.bmp` (~880 MB) and the obsolete debug DLLs (`rexruntimerd.dll`,
  `rexgpu-xenosrd.dll`, `TracyClientrd.dll`, `SPIRV-Tools-sharedrd.dll`,
  `amd_fidelityfx_*drel.dll`). `amd_fidelityfx_vk.dll` remains (9332432 B,
  0.9): experimental Vulkan still uses it (0.10 has no Vulkan FFX).

### 7.3 ⚠️ Notes for future sessions
- The game build uses `CMAKE_PREFIX_PATH=.../rexglue` (0.10). Do NOT use
  `cmake --preset` without `-DCMAKE_CXX_COMPILER=...LLVM/clang++.exe`.
- If SDK 0.10 is re-cloned, the 2 build workarounds (§2.3) and the 9 patch
  files (github/patches/) must be re-applied.
- SDK 0.9 (`rexglue-sdk/`) is NOT touched; the `rexglue_0.9/` backup allows
  reverting if something fails (it is no longer the default).

---

## 8. ✅ IN-GAME VALIDATION (2026-08-25, user) — MIGRATION COMPLETE

The user tested the game built against 0.10 and everything worked:

1. **Simple override mods**: `swap_96_on_327` (Babidi→Krillin, geom.bin =
   106496 B = the slot's exact to_read) → Krillin shows Babidi. OK.
2. **Texture mod**: `tex_91` (Dr. Gero) → textures applied. OK.
3. **Virtual mid-insert**: `sw_vegeta424` (Vegeta Saiyan armour, bin 126976 B
   > to_read 106496 of slot 327) → Vegeta enters battle correctly with Krillin.
   **The virtual mid-insert was finally validated in game** (in 0.9 it was left
   unvalidated because the build's DLL was stale — see AGENTS §13.6).

**Conclusion**: the 0.9.0 → 0.10.0 migration is COMPLETE. The ported runtime
patch (afs.h/afs.cpp recreated + host_path_* refactored + 3 dbz1 cvars) works
identically to 0.9, and the SDK fixes that were our own in 0.9 are native in
0.10.

**Future pending (NOT urgent, when the general plan is complete)**:
- Update `release/README.md` + `README.md` for SDK 0.10 (version bump, mention
  of the validated virtual mid-insert).
- Upload to GitHub (the `github/` repo already has updated patches and docs
  locally, uncommitted).
