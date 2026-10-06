# SESSION 2026-09-10 — NATIVE B3 HD→B3 HD SWAP VALIDATED (Cell Form 2 → Krillin)

> Result verified in game by the user: **100% functional** (mouth included).
> Mod `cell_native`. Tool `mod center hd/swap_b3.py`.
> This document closes the "Cell in Krillin's slot" arc and **separates** what
> a *native HD→HD swap* is (solved) from a *PS2→HD port* (pending).

---

## 0. RESULT

- **HD Cell Form 2 (bin 147) renders perfectly in Krillin's slot (327)**, with
  every function (mouth included). No buts.
- Generated mod: `out/build/win-amd64-release/mods/cell_native/`
  (`us/data_cmn.afs/327/geom.bin`, per-entry override, ~120 KB).
- Binary check: the decompressed `geom.bin` is **identical** (MD5) to source
  bin 147 extracted from `us/data_cmn.afs`.

---

## 1. WHAT IT IS AND WHAT IT IS NOT (critical)

| | Native B3 HD→B3 HD swap | PS2→B3 HD port |
|---|---|---|
| What it moves | A HD character's **COMPLETE** `#AMB` (AWO+AZT) into another slot | The **PS2** model's geometry into the HD bin |
| Topology | The bin's own (it travels with it) | HD's (injection) or rebuilt (Route B) |
| State | ✅ **100% FUNCTIONAL** | ⛔ Route A deforms · Route B blocked |
| Use | Any character that **already exists in HD** | Characters that **only** exist on PS2/IW |

> **What was achieved today is a native HD→HD swap, NOT a PS2→HD conversion.**
> Cell Form 2 already existed in HD (entry 147); we placed it in Krillin's
> slot. That is why it comes out perfect: the runtime draws the bin as it is.

---

## 2. REPRODUCIBLE RECIPE

```powershell
# 0) List the catalogue (bin = AFS entry index)
python "mod center hd\swap_b3.py" --list

# 1) Native swap: SOURCE bin -> TARGET slot
python "mod center hd\swap_b3.py" --origen 147 --dest 327 --mod cell_native
```

- **Source/target**: numbers from the catalogue `mod center hd/catalog_b3.cat`
  (format `bin|name|label|variant|playable`). **bin == AFS entry**
  (147 = Cell Form 2, 327 = Krillin).
- **Default AFS**: `<root>/us/data_cmn.afs` (293,423,104 B).
- **Output**: `out\build\win-amd64-release\mods\<mod>\us\data_cmn.afs\<dest>\geom.bin`.
- **No `.disabled`** = mod active. ⚠️ **Only one active mod per slot** (the
  runtime serves the first in alphabetical order).

### Verification (recommended)
```powershell
python "mod center hd\swap_b3.py" --origen 147 --dest 327 --mod check
# and check that the decompressed geom.bin == the source bin (MD5)
```

---

## 3. MECHANICS (why it works)

1. The HD `#AMB` contains `#AWO` (mesh) + `#AZT` (textures) of the **same
   character** → they move together, without mismatch.
2. The runtime **does not validate fixed slot counts**: it draws the mesh
   group, IB, bones and UVs **that come inside the installed bin**.
3. It is served as a **per-AFS-entry override** (lightweight): the mod only
   contains the bin, not the whole AFS (293 MB).
4. **LZX `/N:2048` compression** + padding; if the compressed bin exceeds the
   slot's `to_read`, the runtime's **virtual mid-insert** grows the entry in
   place and shifts the later ones (in memory).
5. Animation/expressions go through **label matching** between the model and
   the slot's `#ACM`; being the same game, the labels match (mouth OK).

---

## 4. CHARACTER CATALOGUE

- File: `mod center hd/catalog_b3.cat` (183 entries).
- Columns: `bin | name | label | variant | playable`.
- **bin = AFS entry index**. Examples:
  `146/147/148 = Cell Form 1/2/3`, `149/150/151 = Cell Form 1/2/3 alt`,
  `327/328/329 = Krillin (bald/with hair/armour)`.
- List: `python "mod center hd\swap_b3.py" --list`.

---

## 5. IMPLICATIONS

### 5.1 What IS ready
- **Native B3 HD→B3 HD model swap**: 100% functional and validated
  (Cell F2 → Krillin). It lets you put any HD model in any slot, completely
  playable.
- Tools: `swap_b3.py` (swap), `swap_matrix.py` (move blobs between
  slots/regions), `texture_b3.py` (textures), catalogue.

### 5.2 What is NOT ready
- **PS2 → B3 HD conversion**. State (2026-09-10):
  - **Route A (injection)**: technically works but **deforms the body**,
    because the HD body was **remodelled** (mean HD↔PS2 distance **0.69**, max
    **5.31**); HD hands/face are already PS2 (dist. 0.01‑0.21) → injecting them
    is a no-op. `cell_best2`/`cell_face_only` confirm it does not improve.
  - **Route B (full port)**: blocked (positional consumption of the pool;
    NVIDIA "Vertex Offset Method" hypothesis + 2nd table `AWG0+0x1F80`).
    Needs RE.
- **Decision rule** (new):
  1. Does the character **exist in HD**? → **native swap** (perfect).
  2. Does it only exist on **PS2/IW**? → Route A (limited) or Route B RE (pending).

### 5.3 Strategic consequence
The PS2→HD port **only adds value for models that do not exist in HD** (e.g.
Infinite World characters / custom models). For B3's roster, the native swap
covers everything. RE effort (Route B) should go to those cases, not to
characters already present in HD.

---

## 6. TOOL STATE (reproducibility)

| Tool | State | Use |
|---|---|---|
| `swap_b3.py` | ✅ (`--origen/--dest/--mod/--list`) | Native HD→HD swap |
| `swap_matrix.py` | ✅ | Move any blob between slots/regions |
| `texture_b3.py` | ✅ | AZT textures (extract/build) |
| `port_ps2_b3_inject.py` | ◑ research | Route A (injection) |
| `port_ps2_b3_inject_aux.py` | ◑ research | Route A extended (16 AWGs) |
| `catalog_b3.cat` | ✅ | Catalogue (bin|name|label|variant) |
| `mod center\Xbox 360 ...\xbcompress.exe` | ✅ | LZX `/N:2048` |

Supporting RE instruments: `awo_tools/awg0_export.py` (auto-detects format
A/C), `awo_tools/awg_to_obj_b3.py`, `awo_tools/cell_align_check.py`.

---

## 7. MODS FROM THIS SESSION (`out/build/win-amd64-release/mods/`)

| Mod | State | Contents |
|---|---|---|
| **`cell_native`** | **ACTIVE** | Validated native swap: Cell F2 (147) in slot 327 |
| `cell_hd_only` | disabled | Same as `cell_native` (made by hand) |
| `cell_best2` | disabled | Route A extended to 16 AWGs (no improvement) |
| `cell_face_only` | disabled | Route A face only (fallback) |
| `cell_best` | disabled | Route A + anti-stretch guard |
| `cell_npm_fix` / `cell_npm4_test` / rest | disabled | Route A history |

---

## 8. ANSWER TO "IS PS2 → B3 HD READY?"

**No.** What is ready is the **native HD→HD swap**.

- **HD→HD** (same engine, `#AWO` format): ✅ 100% (this).
- **PS2→HD** (converting a model that is not in HD): ⛔ no. Route A deforms
  (HD body remodelled), Route B blocked. It is an open problem, with a plan in
  `docs/07_ports/PLAN_PS2_B3/PLAN.md`.

---

### References
- `docs/07_ports/PLAN_PS2_B3/PLAN.md` (the PS2→HD port plan) and its 4 reports.
- `mod center hd/GUIA_SWAPS_Y_PORTS.md` (swap guide; updated).
- `AGENTS.md` §3.1 (state), §3.4 (Route A/B), §10 (pipeline).
