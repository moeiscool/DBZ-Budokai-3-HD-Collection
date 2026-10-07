# Project tree — what each folder is

> Updated: 2026-08-14 (+ `ps5/`, 2026-10-06). Paths relative to `C:\Users\javie\Desktop\PROYECTOS IA\DBZ Budokai 3 HD Collection\`.

---

## GENERAL TREE

```
DBZ Budokai 3 HD Collection/
├── src/                     ← Launcher and game code (main.cpp, launcher/, ingame/)
├── ps5/                     ← PS5 (jailbroken) port: host, build scripts, SDK patches (GPL-3) — see docs/PS5.md
├── rexglue-sdk-0.10/        ← SDK SOURCE 0.10 (runtime, GPU, filesystem, kernel) — buildable
├── rexglue/                 ← INSTALLED SDK (bin/lib/include) — what the game build uses
├── generated/               ← Recompiled guest code (dbz3_recomp.*.cpp) — 23 files ~2 MB each
├── out/build/               ← Game builds (4 configurations, see below)
├── docs/                    ← THIS documentation (organised by topic)
├── us/                      ← US region assets (the game's AFS, ~2.4 GB)
├── eu/                      ← EU region assets (the game's AFS, ~2.2 GB)
├── afs_out/                 ← DECOMPRESSED character bins from the AFS (for RE)
├── ps2_games/               ← AFS of B1, B2, B2V, B3 GH, IW (PS2 references, ~8.4 GB)
├── SDBH_body/               ← Super Dragon Ball Heroes extractions (EMD models)
├── awo_tools/               ← RE and conversion SCRIPTS (parse_model.py, build_*.py...)
├── mod center/              ← Community tools (36 programs, ~1.7 GB)
├── mod center hd/           ← HD tools adapted/created by us
├── modding resources/       ← Modding documentation + resources (models, lists, art)
├── modding resources update/       ← Inbox for new files from the user
├── modding resources update 2/     ← More resources (tutorials, models)
├── modding resources discord/      ← Resources downloaded from the community Discord
├── default.xex / yae3_xenon.xex    ← Game images (US/EU)
├── CMakeLists.txt, CMakePresets.json ← Build config
├── dbz3_config.toml, dbz3_manifest.toml ← Game config/metadata
├── bin/ tools/             ← Miscellaneous utilities
```

---

## out/build/ — The builds

| Build | Use | Size | Needed |
|---|---|---|---|
| `win-amd64-release` | **The main build** (dbz3.exe, playable game) | 4.5 GB | ✅ YES |
| `win-amd64-tracy` | Instrumented with Tracy (profiling) | 10.7 GB | 🔸 Occasional |
| `_archivo_builds/` | Archived builds (relwithdebinfo, sdk-test) | 266 MB | 🗄 Archive |
| `_archivo_dlls/` | DLL backups | 62 MB | 🗄 Archive |
| `_archivo_mods/` | Mods from past experiments | 2.7 GB | 🗄 Archive |

> See [06_limpieza/PLAN_LIMPIEZA.md](../06_limpieza/PLAN_LIMPIEZA.md) for details.
> The PS5 build lives outside this tree: `/root/dbz3` on the Arch host, the
> packaged title in `out/ps5-title/` (see `docs/PS5.md`).

---

## out/build/win-amd64-release/ — The main build

```
win-amd64-release/
├── dbz3.exe              ← The game (launch from here)
├── dbz3_user.toml        ← User CONFIG (mods, region, GPU backend, frame cap)
├── rexruntime.dll        ← Runtime (the mod hook lives here) — updated from rexglue-sdk-0.10/out/win-amd64-baseline/
├── rexruntimerd.dll      ← Debug runtime (for Tracy)
├── rexgpu-xenos.dll      ← GPU backend
├── amd_fidelityfx_*.dll  ← FidelityFX (FSR/CAS)
├── mods/                 ← MODS (see below)
├── active_region/        ← Region overlay mounted as game: (rebuilt at every start)
├── logs/                 ← Runtime logs (dbz3_001.log...)
├── user_data/            ← Save data
├── *_backup*.bmp / frontbuf_*.bmp / black_*.bmp ← FRAMEBUFFER DUMPS (debug, ~1 GB) — CAN BE CLEANED
├── _backup_d3d12/ _backup_pre_opt/ _backup_tracy/ ← DLL backups
├── crash_*.dmp           ← Crash dumps
```

---

## out/build/win-amd64-release/mods/ — The mods

| Mod | Contents | State |
|---|---|---|
| `og_music` | Original music (ADX/SFD) — us/ only (eu deduplicated) | ✅ Works (enable it: remove `.disabled`) |
| `janemba_v10` | AFS with the ORIGINAL Krillin bin (reference) | ✅ It is the untouched AFS |
| `goten_body` | Goten's body injected into Krillin (via override) | 🔴 Crashes (under investigation) |

> Old mods (janemba, krillin_*, afstest, janemba_v11) are archived in
> `out/build/_archivo_mods/` — outside `mods/` so the runtime does not scan them.

---

## awo_tools/ — RE scripts (ours)

| Script | Function |
|---|---|
| `analyze_bin_hd.py` | Historical PS3 parser; obsolete, do not use for B3 HD bins |
| `awg_to_obj_b3.py` | Export complete B3 HD bins to OBJ |
| `awg0_export.py` | Export AWG0 with auto-detection of formats A/C |
| `awg_cara_export.py` | Export face AWGs |
| `build_awo_desde_cero.py` | Parse Janemba.amb → AMGs (extraction) |
| `build_janemba_final.py` | Inject Janemba's geometry into Krillin's slots |
| `swap_cuerpo_hd.py` | Inject Goten's body into Krillin |
| `parse_ps2_mesh.py` | PS2 mesh parser (submeshes, FaceType) |
| `pose_matrix.py` | World matrices of PS2 bones |
| `rig_mapeo.py` | JNB→KLL remapping by labels |
| `build_janemba2.py`, `build_afs.py`, `mezclar_ps2_hd.py` | Earlier experiments |
