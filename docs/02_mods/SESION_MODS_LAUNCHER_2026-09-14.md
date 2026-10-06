# Session: mod cleanup + closing/polishing the HD↔HD Model Swap (2026-09-14)

Closing of the model-swap block. The user's goals: (1) sweep the mods,
(2) leave the **native B3 HD↔HD swap** closed/polished, (3) make clear that
**`.iso` files do not benefit from the mod system**, (4) refactor/modernise the
mods section (QoL + visuals).

## 1. Mod sweep

`out/build/win-amd64-release/mods/` had **90 mods** (almost all experimental
tests over time). **83 were moved to
`out/build/win-amd64-release/mods_archivo/`** (nothing deleted) and **7 useful
ones** were kept:

| Kept | What it is |
|---|---|
| `cell_native` | Native HD↔HD swap Cell Form 2 (147) → Krillin (327). Validated. |
| `sw_goten_nativo`, `sw_vegeta424` | Validated native HD↔HD swaps. |
| `cell_best2`, `cell_win2` | PS2→HD port (Route A, approximate) — reference. |
| `goku_armadura` | HD↔HD head swap (partial). |
| `og_music` | Real content (original music). |

- All are left **disabled** (vanilla game by default).
- `mods/README.md` (guide + table) and `mods_archivo/README.md` (categories)
  added.
- `mods_archivo/` is **outside `mods/`**, so the runtime never scans it and the
  release packager never includes it.

## 2. B3 HD↔HD Model Swap — closed and polished

Pipeline already validated (`swap_b3.py` + `catalog_b3.cat` + virtual
mid-insert). Polish:
- **Combos with a search box** (183 characters): text filter inside the
  drop-down, each row shows `[bin N]` and `[NOT PLAYABLE]`.
- **Preview card** (source/target, bin/slot, not-playable warnings).
- **Source==target guard** (in the UI and in `mod_pipeline.cpp`).
- **Notice in ISO mode** + swap button **disabled** (the mod would not apply).
- `swap_b3.py` now writes the manifest with **catalogue names**
  (`name=Cell Forma 2 en Krillin`, `type=swap_b3`, `source`/`target` with name
  and bin) instead of just numbers.
- Removed the temporary diagnostic log `pipeline_cmd.log`.

## 3. Disc mode (ISO) — mods are NOT applied

When playing from the `.iso`, the per-AFS-entry overrides resolve to host
files of the extracted folder → **no mod has any effect**. It was made
explicit:
- Validation banner (already existed) + **amber notice in the Mods tab** +
  **amber notice in Model Swap**.
- The **"Swap B3→B3" button is disabled** in ISO mode.
- i18n in the 5 languages (verified: **0 gaps** with a key audit).

## 4. Mod centre refactor

`src/launcher/launcher_state.cpp` (`DrawModsTab`):
- **Cached list** (`mods_cache_` + `mods_loaded_`): it no longer re-scans the
  disk (and counts files recursively) every frame; it is invalidated after
  toggles, installing, editing, applying a profile or pressing "Refresh".
- **Search** by name/title/description/author/source/target/type.
- **Enable all / Disable all / Refresh / Open folder**.
- Coloured **type badges** (pill) + green `ON`.
- **Alternating rows** (`ImGuiTableFlags_RowBg`) and empty / no-results state.
- New helpers: `IContains`, `DrawBadge`, `CharacterCombo` (combo with a
  filter, reused in Model Swap and Textures).

## 5. Files touched

- `src/launcher/launcher_state.h` — mod cache + search buffers.
- `src/launcher/launcher_state.cpp` — helpers + `DrawModsTab` / `DrawModelSwapTab`
  / `DrawTexturesTab`.
- `src/launcher/i18n.cpp` — new translation entries (ES/IT/DE/FR).
- `src/launcher/mod_pipeline.cpp` — remove the temporary log + source==target guard.
- `mod center hd/swap_b3.py` — manifest with names.
- `mods/README.md`, `mods_archivo/README.md` (new).

## 6. Verification

- Release build **without warnings**; `rexruntime.dll` 10863616 and
  `rexgpu-xenos.dll` 6165504 (canonical, no instrumentation).
- i18n audit: 209 call-site keys, **0 missing** in the table.
- `swap_b3.py --origen 147 --dest 327` generates the mod and the expected manifest.
- No mods active by default.
