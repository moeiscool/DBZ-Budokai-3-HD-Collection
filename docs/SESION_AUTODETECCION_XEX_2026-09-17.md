# Session 2026-09-17 — Executable auto-detection (v1.2.2)

> Goal: make the launcher **always** boot the game, with the executable under
> any name/location (retail disc dump, original ISO, nested folders), without
> the user having to rename or understand anything.

---

## 1. Symptom and root cause

A user (RTX 5090 / 9950X3D) reported **"I press Play and nothing happens"**. In
his logs, ALL attempts died the same way:

```
XThread::Execute - No function registered at 820D54C8
```

Diagnosis (from `docs/07_ports/PLAN_PS2_B3/01_WEB.md`, which documents the
disc's contents):

| Disc file | Size | What it is |
|---|---|---|
| `default.xex` (root) | 3,317,760 B | **HD Collection MENU** (pick: B1/B2/B3) |
| `DBZ1/yae1_xenon.xex` | 4,464,640 B | Budokai 1 |
| `DBZ3/yae3_xenon.xex` | 4,890,624 B | **Budokai 3 (ours)** |

The launcher booted `game:\default.xex` (the disc root → the **menu**) and the
recompiled core (Budokai 3 only) does not have that executable's entry
function → the guest died with a cryptic error.

Secondary findings of the same session:

1. **ISO mode useless with a retail ISO**: `ExtractGameXexFromIso` only tried
   `default.xex` (the menu) and mounted the root, but the data lives in `DBZ3\`.
2. **An unknown xex did not block** the Play button.
3. **Nothing about the xex was logged** (`OnConfigurePaths` runs before
   logging is initialised → its lines are lost).
4. **`dbz3_user.toml` did not parse**: `rex::cvar::SaveConfig` writes raw
   values, so a path `E:\Game Roms\…` produced `unknown escape sequence '\G'`
   and **ALL settings were lost** on every start.

---

## 2. Design of the solution

**Single source of truth**: `ResolveBootSource()` returns a `BootSource`
{ `xex` (what is served as `default.xex`), `data_root`, `status`, `redirect`,
`note` } used by the pre-flight, the VFS (device shims) and the UI.

Flow inside the launcher:

1. `CheckDefaultXex(<root>)` on the canonical paths (`<root>\default.xex`,
   `<root>\assets\…`). If the status is valid → **nothing is copied**.
2. If there is no valid executable → `FindGameExecutable(<root>)`:
   - conventional spots of the neighbouring roots: `root`, `DBZ3`, `assets`,
     `assets/DBZ3` (and `default.xex`);
   - a **bounded** scan of the chosen root: depth ≤ 3, a cap of 4000
     directories, skipping `user_data`/`logs`/`mods`/`$RECYCLE.BIN`/…;
   - identification by **size + MD5** (US/EU), not by name.
3. `EnsureXexCache()` copies the found executable to
   `user_data/dbz3/xex_cache/default.xex` (**only if needed**; the user's
   folder is never written to) and sets the data root (`DBZ3\` if the xex came
   from there).
4. `RegionDiscDevice` (ISO) and `GameDataHostDevice` (folder) serve
   `game:\default.xex` from the cache and resolve `us\…`/`eu\…` under `DBZ3\`
   when the data lives there (with a fallback to the original path).
5. In ISO mode, `ExtractGameXexFromIso` tries in order:
   `default.xex`, `DBZ3/yae3_xenon.xex`, `DBZ3/yae3_xenon_eu.xex`,
   `yae3_xenon.xex`, `yae3_xenon_eu.xex`… and records which one was used in
   `iso_cache/source.stamp` (with the ISO's path+size+date to invalidate).

**Executable states** (`XexStatus`): `kUs`, `kEu`, `kDbz1`, **`kHdMenu`**
(new: the HD Collection menu, 3,317,760 B), `kUnknown`, `kMissing`.
`kHdMenu` and `kDbz1` **block** Play with a specific message; `kUnknown` warns
in amber but lets you play (it may be a modified dump).

**UI**: a banner based on `CurrentBootSource()` with a blue note
"Executable detected: `yae3_xenon.xex` → `default.xex` (nothing needs
renaming)"; PLAY is enabled by a single gate (`assets_ready`, which also
covers the Enter key).

**Config**: `SaveUserSettings` passes `SaveConfig`'s file through
`EscapeTomlStrings`, which escapes `\` and `"` inside quoted values and is
**idempotent** (if `SaveConfig` rewrites nothing, the second pass does not
double the backslashes).

> The PS5 build (`docs/PS5.md`) solves the same problem at build time:
> `ps5/stage_game.py` finds the Budokai 3 executable by checksum (SHA-256 or
> MD5) in the ISO or folder and stages it as `default.xex`.

---

## 3. Files touched

| File | Change |
|---|---|
| `src/launcher/settings.h/.cpp` | `XexStatus::kHdMenu`, `ClassifyXexFile` (+ public), `XexStatusLabel`, `GameExecutable`, `FindGameExecutable`, `EnsureXexCache`, `XexCacheDir`, `BootSource`, `ResolveBootSource`/`CurrentBootSource`/`SetCurrentBootSource`, `ExtractGameXexFromIso` (candidate list), `IsoXexSourcePath`, `EscapeTomlStrings`, extended `IsValidGameDataDir` |
| `src/main.cpp` | `FindGameRoot` accepts `DBZ3`/`assets/DBZ3`; `OnConfigurePaths` resolves+sets the boot source and logs the diagnosis; pre-flight on `boot.xex`; the `skip_launcher` guard uses the resolved status |
| `src/region.cpp` | `GameDataHostDevice` (folder mode: serves the cached xex + remaps to `DBZ3\`), extended `RegionDiscDevice` (xex redirect + `DBZ3\` prefix with fallbacks), `MountIsoDrive`/`RemountGameDrive`/`RelocateGameData` use the boot source |
| `src/launcher/launcher_state.cpp` | Banner with `CurrentBootSource`, HD menu message, amber warning for unknown, "Executable detected" note |
| `src/version.rc` | 1.2.1 → **1.2.2** |
| Docs | `AGENTS.md` (§3, §8, §9.2), `docs/README.md`, `docs/01_estructura/ESTADO.md`, `docs/HOJA_DE_RUTA_2026_09.md`, `RELEASE_README.md`, `README.md`/`README_EN.md`, `README_PRIMER_ARRANQUE.txt`, `portforge/.forge.json` |

---

## 4. Verification (local, 2026-09-17)

Environments assembled in `%TEMP%\opencode\` with **junctions** to `us/`
(deleted at the end; the assets stayed intact: 15 files in `us/`).

| Scenario | Result |
|---|---|
| **Retail dump**: root `default.xex` = menu 3,317,760 B (filler) + `DBZ3\yae3_xenon.xex` (real) + `DBZ3\us\` | `FindGameExecutable: found yae3_xenon.xex (US/NA) … -> data root …\disc\DBZ3` → `staged at user_data\dbz3\xex_cache\default.xex` → `RemountGameDrive: MOUNTED …\disc\DBZ3` → **the game boots** (guest thread + AFS reads from `DBZ3\us\`); process alive at 20 s, without `No function registered` |
| **Classic layout**: `default.xex` + `us\` at the root | Canonical path; **copies nothing**; boots as before |
| **HD menu only** (nothing bootable) | Nothing is cached; no crash. With `skip_launcher` the SDK fails cleanly ("Failed to load XEX"); with the launcher, red banner + PLAY disabled |
| **TOML escaping** | Pass 1 escapes `E:\Game Roms\…` → `E:\\Game Roms\\…`; pass 2 **identical** (idempotent); quotes and integers intact |
| `skip_launcher` (dev) | New guard: if the status is not US/EU, it does not boot and warns |

**Pending verification**: ISO mode with a **real retail ISO** (none was
available; the logic is implemented and is the same as folder mode's, gated so
as not to affect already-repacked ISOs).

---

## 4.bis ISO mode — VALIDATED (v1.2.2 EX, 2026-09-17)

Without an original ISO at hand, it was validated by mounting a **synthetic
XDVDFS** with `tools/make_test_iso.py` (a new generator: it packs a folder with
the retail layout — `default.xex` = menu 3317760 B at the root, the real
`DBZ3/yae3_xenon.xex` and `DBZ3/us` with the 15 data files, 2.3 GB).

Tests (all with the dual exe 1.2.2.1):

| Scenario | Result |
|---|---|
| **A** — only the `.iso` next to `dbz3.exe` (no folder) | The launcher auto-detects the ISO, extracts `DBZ3/yae3_xenon.xex` (rejects the menu), mounts the disc with `prefix_dbz3=yes`, creates the guest thread and **the game boots** (alive at 45 s, without `No function registered`). |
| **B** — a "valid" folder but with the **menu** as `default.xex` + an ISO next to it (the user's case) | It jumps to the ISO by itself (`folder cannot boot (...) - using the disc image`), mounts it the same way and **boots**. |

**2 real bugs found and fixed by these tests** (any retail-ISO user would have
hit them):

1. **`RegionDiscDevice` did not normalise the path**: the VFS hands over the
   path with the mount prefix removed but **with the leading separator**
   (`\us\data_cmn.afs`), and the region remap + the `DBZ3\` prefix required it
   not to start with `\` → they were never applied → the guest failed with
   `NtCreateFile FAILED: path='D:\us\data_cmn.afs' -> 0xc000000f`. Fix:
   `NormalizeGuestPath()` on entering `ResolvePath` (the `default.xex`
   redirect already did it, which is why the module did load and only the
   data failed).
2. **ISO mode with a disc without a bootable executable**: if the candidates
   do not give a US/EU one, ISO mode is now **not** entered
   (`iso_boot.usable()`); the folder is kept and the banner explains why
   (before, it booted a file the runtime could not load →
   `Unknown module magic: 00000000`).

Note: the capture still shows an `NtCreateFile FAILED: path='D:\us\'` (a
directory request the VFS canonicalises to the drive's root); it is harmless —
the game continues and reaches the menu.

---

## 5. Notes for the future

- **`tools/make_test_iso.py <out.iso> <folder>`** generates a test XDVDFS from
  a folder (to validate disc mode without a real ISO). The runtime reads raw
  XDVDFS: volume descriptor at sector 32 with the `MICROSOFT*XBOX*MEDIA`
  magic, 14-byte directory entries + name linked as a tree whose pointers are
  in 4-byte units. If more files are added to a folder, remember each
  directory must fit in one sector.
- **The folder→ISO fallback** (v1.2.2 EX) kicks in when the folder has no
  bootable executable (`kHdMenu`, `kMissing`) and there is an `.iso` next to
  the data folder or the executable. If the user wants mods, in the launcher
  they can switch back to "Extracted folder" (that clears `dbz3_iso_path`).
- ⚠️ **The release exe is built from `out\build\win-amd64-dual`** (verified:
  the SHA-256 of the v1.2.1 zip's `dbz3.exe` matches that build dir's).
  `tools/make_release.ps1` already takes it from there.
- `OnConfigurePaths`'s logs are lost (logging starts later): the xex
  diagnosis appears when Play is pressed (`RelocateGameData`). If the full log
  is ever needed, the early lines must be buffered.
- `FindGameExecutable` only scans recursively in the **first** root (the
  chosen folder); in the neighbouring roots it only looks at the conventional
  spots (bounded cost).
- An xex from another print run with a different MD5 → `kUnknown` (warning,
  not a block). If more print runs are identified, add their MD5 to
  `ClassifyXexFile` (and to `ps5/stage_game.py`).
