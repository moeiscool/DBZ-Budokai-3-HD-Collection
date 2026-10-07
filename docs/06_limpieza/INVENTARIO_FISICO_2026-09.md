# Physical and artefact inventory — 2026-09-08 (UPDATED 2026-09-09)

> Measurement of the working tree. This document does not authorise deletions:
> it separates functional data, historical references and regenerable artefacts.

## Summary (after the 2026-09-09 cleanup: ~46 GB → ~28.4 GB)

| Area | Approx. size | Initial decision |
|---|---:|---|
| `ps2_games/` | 10.58 GB | Keep: PS2/NGC/PSP references used for RE |
| `out/` | 5.10 GB | Clean per subfolder, never delete globally |
| `rexglue-sdk-0.10/` | 2.35 GB | Keep: active SDK and its builds |
| `us/` | 2.29 GB | Keep: original US assets |
| `modding resources/` | 2.23 GB | Keep: modding resources |
| `eu/` | 2.08 GB | Keep: original EU assets |
| `mod center/` | 1.60 GB | Keep: external tools |
| `modding resources discord/` | 0.86 GB | Inventory; do not delete duplicates yet |
| `modding resources update 2/` | 0.65 GB | Inventory; do not delete duplicates yet |
| `modding resources update/` | 0.27 GB | Inventory; do not delete duplicates yet |
| `rexglue/` | 0.12 GB | Keep: installed SDK 0.10 (the game build links it) |

## Deletion carried out 2026-09-09 (approved by the user)

| Item | Size | Reason |
|---|---:|---|
| `out/analysis/corpus/.work/` | 16.18 GB | Cache of extracted bins (81.3k); regenerable with `corpus_scan.py`. `corpus_all.db` + JSONs kept |
| `rexglue-sdk/` (historical 0.9) | 1.66 GB | Superseded by `rexglue-sdk-0.10/`; the canonical avx2 DLLs live in 0.10/out/win-amd64 |
| `rexglue_0.9/` | 0.20 GB | Backup of SDK 0.9, already migrated |
| `out/build/_archivo_builds/` | 0.25 GB | Old regenerable builds (sdk-test, relwithdebinfo) |
| `out/build/_archivo_dlls/` | 0.06 GB | Obsolete DLL backups |
| Exact duplicates in `modding resources discord/tutorials/` | ~5 MB | PDF/DOCX already present in `update 2` |

## `out/`

| Subfolder | Approx. size | State |
|---|---:|---|
| `build/win-amd64-release/` | 2.44 GB | Main build; keep (includes `mods/` with 50+ disabled mods, useful as reference) |
| `build/_archivo_mods/` | 2.49 GB | Archive of experiments; kept by the user's decision |
| `build/win-amd64-dual/` | 0.11 GB | Dual build; keep until the release is validated |
| `analysis/` | ~0.02 GB | Corpus: only DB + JSONs (bins are regenerated on demand) |

## Regenerable artefacts found

- `out/build/win-amd64-release/`: 5 AFS, 3 SFD, 6 DLL, 3 EXE, small logs and
  dumps. The AFS/SFD are functional and must not be deleted as cleanup.
- 8 BMP, 71 logs, 10 TMP and 1 BAK were found in the measured tree. Logs and
  TMP are candidates for rotation after keeping the relevant ones.
- The largest individual files are `ps2_games` images/discs, `us/`/`eu/`
  assets and already-archived copies of mods. Size alone does not make them
  garbage.

## Next safe physical cleanup

1. Compare hashes of `out/build/_archivo_mods/` against the active mods and
   compress the archive, without deleting it yet.
2. Review `out/build/_archivo_builds/` and delete only builds that are not in
   the validation matrix.
3. Rotate old logs and delete only BMP/TMP with no diagnostic value.
4. Audit duplicates in `modding resources*` before moving or deleting any
   resource.

## Prohibitions

- Do not delete `us/`, `eu/`, `ps2_games/`, `rexglue-sdk-0.10/` or `mod center/`.
- Do not delete `out/build/win-amd64-release/` or its functional AFS/SFD.
- Do not modify `active_region/` if it appears: it is regenerated at startup.
