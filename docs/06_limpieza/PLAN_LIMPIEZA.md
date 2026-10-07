# CLEANUP AND REORGANISATION PLAN

> Updated: 2026-08-14. This document catalogues the pending cleanup.
> **NOTHING HAS BEEN DELETED YET** — this is the plan; it will be carried out
> with your approval.

---

## 1. SUMMARY OF THE MESS FOUND

| Area | Problem | Space |
|---|---|---|
| Builds | 4 builds, some doubtful | ~19 GB |
| Debug BMPs | ~30 frontbuf_*.bmp + black_*.bmp (31.5 MB each) | ~1 GB |
| DLL backups | _backup_d3d12/_backup_pre_opt/_backup_tracy | ~50 MB |
| Old mods | 5 mods with full AFS (293 MB each) from past experiments | ~1.5 GB |
| og_music | EU and US duplicated (same ADX/SFD) | ~3 GB (redundant) |
| modding resources | 4 folders with possible duplicates | ~4.3 GB |
| Crash dumps | 8 crash_*.dmp files | ~2.4 MB |

---

## 2. PLAN PER AREA

### 2.1 Debug BMPs (safe to delete — already gated by Dev mode, 2026-08-19)
**What**: `frontbuf_*.bmp`, `black_*.bmp` (31.5 MB each, ~30 files) in the release build.
**What they are**: framebuffer dumps from the shader dump / debug.
**Action**: delete them. They do not affect the game.
**Risk**: none.
**State**: ✅ the 28 .bmp files (~840 MB) were already deleted on 2026-08-19.
In addition, the "GPU diagnostic logging" toggle now ONLY generates these
dumps if **Dev mode** is also on (fix in `src/launcher/settings.cpp`:
`dbz1_diag_logging` is propagated as `DiagLogging() && DevMode()`), so they do
not reappear in normal play even if the checkbox is left on by accident.

### 2.2 Crash dumps (safe to delete)
**What**: `crash_*.dmp` (8 files).
**Action**: delete them (they are from today's tests).

### 2.3 DLL backups
**What**: `_backup_d3d12/`, `_backup_pre_opt/`, `_backup_tracy/`, `rexruntime.dll.bak_afstest`.
**Action**: keep ONLY `.bak_afstest` (runtime reference). Archive or delete
  the others after confirming the current runtime works.

### 2.4 Redundant builds
| Build | Proposed action |
|---|---|
| `win-amd64-release` | KEEP (main) |
| `win-amd64-tracy` | KEEP (profiling) |
| `win-amd64-sdk-test` | CHECK whether it is used; if not, archive |
| `win-amd64-relwithdebinfo` | CHECK; probably archivable |

### 2.5 Old mods (experiments)
| Mod | Contents | Action |
|---|---|---|
| `janemba_v10` | AFS with ORIGINAL Krillin | KEEP (reference of the untouched AFS) |
| `og_music` | Music (works) | KEEP, deduplicate EU/US |
| `janemba` | Old Janemba AFS | Archive |
| `krillin_1byte` | Krillin AFS variant | Archive |
| `krillin_afs` | Krillin AFS variant | Archive |
| `krillin_control` | Krillin AFS variant | Archive |
| `krillin_test` | Texture | Archive |
| `krillin_texture` | Texture | Archive |
| `afstest` | Test override | Archive |
| `goten_body` | Goten's body (crashes) | KEEP (active research) |

**Proposal**: move the archived ones to `mods/_archivo/` (outside `mods/` so
the runtime does not scan them), or simply keep them `.disabled`.

### 2.6 og_music (deduplication)
- `us/adx_jpn.AFS` == `eu/adx_jpn.afs`? (728 MB each, probably identical)
- `us/` and `eu/` have the same 4 files.
- **Proposal**: check hashes; if equal, keep only the variant for the region
  in use (us).

### 2.7 modding resources (4 folders)
| Folder | Contents |
|---|---|
| `modding resources` | Base (models, lists, SDBH) — KEEP |
| `modding resources update` | The user's inbox — KEEP |
| `modding resources update 2` | New tutorials/models — KEEP |
| `modding resources discord` | Discord downloads — KEEP |

**Action**: create an INVENTORY of what is in each one (avoid future
duplicates). Do NOT move the contents yet (risk of breaking script paths).

---

## 3. DOCUMENTATION REORGANISATION (already done)

The `docs/` structure was created:
```
docs/
├── README.md                  ← general index
├── 01_estructura/
│   ├── ARBOL.md               ← what each folder is
│   └── ESTADO.md              ← what works / what fails
├── 02_mods/
│   ├── COMO_HACER_MODS.md     ← mod pipeline
│   └── MODEL_SWAP.md          ← model swap research
├── 03_formatos/
│   ├── AMO_AWO.md             ← PS2 vs HD format
│   └── BIN_LAYOUT.md          ← bin layout field by field
├── 04_herramientas/
│   └── TOOLS.md               ← tool inventory
├── 05_build/
│   └── COMO_COMPILAR.md       ← building the game/SDK
└── 06_limpieza/
    └── PLAN_LIMPIEZA.md       ← this document
```

---

## 4. CLEANUP TASKS (by priority)

- [x] **A**: Delete debug BMPs + crash dumps (1 GB, no risk) — *they were already gone*
- [x] **B**: Check og_music EU/US hashes and deduplicate — *3/4 identical, duplicates archived*
- [x] **C**: Archive old mods (move to `out/build/_archivo_mods/`) — *8 mods archived*
- [x] **D**: Check the sdk-test/relwithdebinfo builds (are they used?) — *moved to `out/build/_archivo_builds/`*
- [x] **F**: Move DLL backups to a central place — *`out/build/_archivo_dlls/`*
- [x] **E**: Create the modding resources inventory (4 folders) — *`INVENTARIO_MODDING.md`*

### 4.1 Result of the cleanup carried out (2026-08-14)

```
out/build/
├── win-amd64-release/          ← MAIN BUILD (4.5 GB, works)
├── win-amd64-tracy/            ← Tracy build (10.7 GB)
├── _archivo_builds/            ← relwithdebinfo + sdk-test (266 MB)
├── _archivo_dlls/              ← DLL backups (62 MB)
└── _archivo_mods/              ← mods from past experiments (2.7 GB)
```

- The release build went from 8.3 GB → 4.5 GB.
- Mods kept: `goten_body` (research), `janemba_v10` (original reference AFS), `og_music` (works).
- Verified: dbz3.exe, runtime with the override fix, toml intact.

---

## 5. IMPORTANT

- **The game works NOW** (all mods disabled). Do not break it.
- **`active_region/` is rebuilt at every start** — do not touch it.
- **`us/` and `eu/`** are the original assets — do NOT delete.
- The scripts in `awo_tools/` reference absolute paths — do NOT move them
  without updating.
