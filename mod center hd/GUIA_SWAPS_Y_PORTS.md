# MODEL SWAPS AND PORTS GUIDE — DBZ Budokai 3 HD Collection

> 2026-08-17. Living document for the B3 project. It consolidates the knowledge
> validated in the sister project **B1** (same ReXGlue runtime, SAME HD format)
> and adapts it to B3. Before anything else: **read the B1 lessons in the B1
> project's `AGENTS.md`** (especially lessons 8-15) — this document is the
> operational summary.

---

## 1. EXECUTIVE SUMMARY

| Swap | State | Tool |
|---|---|---|
| **B1 → B1** (inside B1) | ✅ **100% WORKING** (Android 19 → Tenshinhan) | `swap_b1.py` (B1 project) |
| **B3 → B1** (model port) | ✅ **100% WORKING** (Dr. Gero → Tenshinhan) | `install_b3_to_b1.py` + `launcher_mod_pipeline.py` (B1 project) |
| **B3 → B3** (inside B3) | ✅ **100% WORKING** (Cell Form 2 → Krillin, 2026-09-10) | `swap_b3.py` |
| **B1 → B3** (reverse port) | 🔬 Not tried yet; same principle + reverse seal conversion | Roadmap §7 |

**The finding that changed everything** (B1 lesson 9, 16/08): the HD runtime
**does NOT validate fixed slot counts**. Install a COMPLETE `#AWO` bin of
another character and the runtime draws it as is (mesh group, IB, bones, UVs).
The only requirement: that **geom (`#AWO`/`#AMB`) and tex (`#AZT`) belong to
the SAME character**.

---

## 2. HOW MODEL SWAPS WORK (the principle)

### 2.1 What the runtime does

When a battle loads a character, the runtime reads its bins from the AFS and
renders them **without reinterpreting them**: it uses the mesh group, the
index buffer, the bones and the UVs **that come inside the installed bin**.
That is why:

- **Full-bin swap** (the correct path): the new model looks perfect because
  its topology/IB travel inside the bin.
- **Partial injection** (the old path, DISCARDED): overwriting only the sec34
  coordinates of a native bin → the runtime draws the **host's topology** on
  the new coordinates → **deformation**.
- **Rebuild from scratch with its own IB** (B3 v20/v22): chaos, the runtime
  uses its own IB.

### 2.2 Swap requirements

1. **geom + tex pair of the SAME character**: the geometry bin and its texture
   must correspond to the same character. An `#AWO` of X with an `#AZT` of Y →
   **crash 0xC0000005** (texture mismatch).
2. **Correct bin seals** for the target game:
   - B1: AWG flag `+0x0C` = `0x2`; mesh type2 = `0x1BD`/`0x11BD`; shadow
     `0x190`.
   - B3: AWG flag `+0x0C` = `0x4`; mesh type2 = `0x29BD`.
   - Porting B3→B1 requires converting the seals (see §5).
3. **Compatible materials** (B3→B1 only): scale 4×128.0 + weights
   `0.85/0.80/0.70/1.0` (torso) or `0.85/0.85/0.80/1.0` (limbs) + type2
   `0x11BD` for the specular shader.
4. **Opaque texture** (B3→B1 only): the B1 runtime expects an AZT with DXT3
   alpha at `0xFF` (B3 uses variable alpha → black body).

### 2.3 The runtime animates by labels

The B1/B3 runtime animates **by matching labels** between the slot's `#AWO`
(model) and `#ACM` (skeleton). AWO bones without a matching label stay in bind
pose. For Gero ported to the Tenshinhan slot, the rig labels do not match the
slot's `#ACM` → some bones (mouth, hair) are not animated perfectly. **It does
not block the swap** (the model renders), but it limits the animation.

---

## 3. THE HD FORMAT (same in B1 and B3 — verified 17/08)

### 3.1 Character files (data_cmn.afs / data_sp.afs)

| Magic | Role | B1 slots (e.g. TSH) |
|---|---|---|
| `#ACM` | skeleton + expressions | 2445 |
| `#CCM` | commands/moveset | 2446 |
| `#CSK` | animation table (2037, same IDs in all) | 2448 |
| `#AWO` | model (mesh group + IB + bones + UVs) | 2450 |
| `#AZT` | textures | 2451 |

In **B3**, the model lives in an `#AMB` container that includes `#AWO` +
`#AZT` together (a single AFS entry). Verified: Gero B3 = bin 91 (`#AMB` with
`X20G_BODY`, 2501 verts, 16 AWGs, 46 bones).

### 3.2 Vertex (stride 44) — MODEL VERIFIED 2026-09-11 (GPU windows)

> ✅ The GPU does NOT draw with "A/B descriptors + separate sec34/vb2" (§3.3/§3.4
> are metadata, not the drawing). The vertex buffer is a **VERBATIM copy of the
> contiguous region `[vb0, ib)` of the AWO** (`vb0 = ib - N*44`,
> `ib = AWG0+g(0x30)`), of **N self-contained 44 B windows**, and the **IB**
> (`AWG0+g(0x30)`) indexes windows. Confirmed in game: permuting windows +
> remapping the IB = **total** identity (geometry + textures, T11). Tool:
> `awo_tools/awg_vertex_buffer.py`.

```
+00 pos.x  +04 pos.y  +08 pos.z   (3 float32 BE)   vfetch fmt 57 (32_32_32_FLOAT)
+12 weight (float32, ~1.0)                          fmt 36 (32_FLOAT)
+16 BONE   (u32; 1 byte used)                       fmt 6  (8_8_8_8)
+20 nrm.x  +24 nrm.y  +28 nrm.z   (3 float32)        fmt 57
+32 0xFFFFFFFF
+36 uv.x   +40 uv.y               (2 float32)        fmt 37 (32_32_FLOAT)
```
`N = max(IB index) + 1`. The IB is int16 BE, window indices 0..N-1.

> ⚠️ The "sec34" layout below (`+36 blend, +40 uv`) is NOT the GPU's; the uv
> is at **+36**. The `sec+2` grid is misaligned by +428 B relative to the
> windows (hence the old "UV skew"). See
> `docs/07_ports/SESION_GPU_DRAW_2026-09-11.md` §6-8.

### 3.2b (historical) the tool's sec34 — metadata, not drawing

```
+00 pos.x  +04 pos.y  +08 pos.z          (BE floats)
+12 weight (0.7/0.8/0.9/1.0)
+16 BONE index (u32, valid 1-46)
+20 nrm.x  +24 nrm.y  +28 nrm.z
+32 0xFFFFFFFF
+36 blend/scale
+40 uv
```
`n_sec = sec_size // 44`.

> ⚠️ We used to use an old layout `[nan,u,v,z,x,y,weight,bone,nz,-ny,nx]` (B1
> session 5). It was CORRECTED in v10. **Do not use the old layout.**

### 3.3 AWG0 header offsets (+0x50) — RELATIVE to AWG0

```
+0x28 sec_off   → sec_abs = AWG0 + val     (n_sec = sec_size//44)
+0x2C sec_size
+0x30 post_off  → post_abs = AWG0 + val    (u16 IB + sub-mesh)
+0x34 post_size → n_ib = post_size//2
+0x38 next zone (REL AWG0)
+0x3C bones count   +0x40 name (16B)
```

> ⚠️ The old B3 scripts read `sc=+0x34`, `vb=+0x2C`, `ib=+0x30` (pre-v10
> format). **CORRECTED** in `awg_to_obj.py` (17/08).

### 3.4 Mesh group and arms

- Each `#AWG` has: header (local quat, local pos, seal, arm_ptr, child/
  sibling/parent) + mesh parts (type2, stride, materials).
- The `arm`s (20B: `[bone, end, 0, start, 0]`) point to IB ranges.
- Shadow mesh parts (`0x190`/`0x204`) mark IB limits.

---

## 4. THE CHARACTER CATALOGUE (the base of every swap)

The B1 project scans the AFS and generates a catalogue:
`mod center hd/cache/characters.cat`:

```
game|label|name|slot_geom|slot_tex|slot_acm|slot_csk|verts|awgs
B1|XTSH_BODY|Tenshinhan|2450|2451|2449|0|4272|23
B3|X20G_BODY|Dr. Gero|91|0|0|0|2501|16
```

- **B1**: 26 playable characters (`XGOK_BODY`=Goku, `XTRX_BODY`=Trunks,
  `X19G_BODY`=Android 19...).
- **B3**: 56 characters (`XGOK_BODY`, `XVGT_BODY`, `XPIC_BODY`, `XTSH_BODY`,
  `XFRZ_BODY`, `XCEL_BODY`...). B3's `slot_geom` = the index of the `#AMB`.

Generation: `python launcher_mod_pipeline.py catalog` (a B1 project script,
reusable — it points at both AFS). (B3 now has its own catalogue:
`mod center hd/catalog_b3.cat`, 183 entries.)

---

## 5. HOW TO DO THE SWAPS (step-by-step pipeline)

### 5.1 B3 → B1 port (VALIDATED: Gero → Tenshinhan)

```
python launcher_mod_pipeline.py port --b3 X20G_BODY --dest 2450 --tex 2451 --mod my_port
```
1. Extracts the `#AMB` of the B3 bin (91) and decompresses it.
2. `extract_amb_awo.py` → `#AWO` + `#AZT` of the AMB.
3. `install_b3_to_b1.py`:
   - `port_b3_to_b1_v2.py`: AWG flag `0x4→0x2`, type2 `0x29BD→0x1BD`/`0x11BD`,
     B1 materials (scale 4×128, weights, shadow `0x190`).
   - AZT DXT3 alpha → `0xFF`.
   - LZX compression `/N:2048` + padding to the slot + verified round-trip.
   - Installs into `mods/<mod>/us/data_sp.afs/<2450>/geom.bin` and
     `2451/tex.bin` and enables the mod.
4. Restart the game → the new model renders in battle.

### 5.2 B1 → B1 swap (VALIDATED: Android 19 → Tenshinhan)

```
python launcher_mod_pipeline.py swap --origen X19G_BODY --dest 2450 --tex 2451 --mod my_swap
```
Extracts the source's geom+tex pair (49/48 or 45/46), compresses, pads and
installs it in the target's slots.

### 5.3 B3 → B3 swap — ✅ VALIDATED (Cell Form 2 → Krillin, 2026-09-10)

B3's `#AMB` already contains AWO+AZT of the SAME character → a swap inside B3
is **replacing the AFS entry** (X's AMB in Y's entry). The runtime draws the
whole new AMB (mesh group, IB, bones, UVs), 100% working (mouth included).

```powershell
python "mod center hd\swap_b3.py" --list
python "mod center hd\swap_b3.py" --origen 147 --dest 327 --mod cell_native
```

- `--origen`/`--dest` = **bin number = AFS entry index**
  (`catalog_b3.cat`: `bin|name|label|variant|playable`).
- Installs `mods/<mod>/us/data_cmn.afs/<dest>/geom.bin` (per-entry override,
  ~120 KB; the runtime applies the virtual mid-insert if it exceeds
  `to_read`).
- Full detail: `docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md`.
- ⚠️ **Only one active mod per slot** (the runtime serves the first in
  alphabetical order).
- Mods made this way also work on the PS5 build (copy them to
  `/data/dbz3/mods/`); the swap tool itself runs on the PC.

> **Note**: this is a *native HD→HD swap*, NOT a *PS2→HD conversion*. For
> models that do not exist in HD, see `docs/07_ports/PLAN_PS2_B3/PLAN.md`.

### 5.4 B1 → B3 port (reverse, not tried)

Same principle with reverse seal conversion:
- AWG flag `0x2→0x4`, type2 `0x1BD/0x11BD→0x29BD`, B3 materials (scale 1.0),
  AZT with variable alpha (do not force to 0xFF).
- The geom (`#AWO` B1) + tex (`#AZT` B1) pair of the SAME character → pack into
  `#AMB` or install per entry.

---

## 6. B3 PROJECT TOOLS — STATE AND DIAGNOSIS

### 6.1 State table (17/08)

| Tool | State | Problem |
|---|---|---|
| `awg_to_obj.py` | ✅ **FIXED** (17/08) | Used old header offsets (`+0x34`/`+0x2C`/`+0x30`) and the old vertex layout (`nan,u,v,z,x,y...`). Fixed to `+0x28..+0x34` and the v10+ layout. Detects direct `#AWO` or `#AMB`. Verified: Gero → 2501 verts / 5443 IB / 1814 faces. |
| `obj_to_awg.py` | 🔧 needs a fix | Same offsets/layout bug. Also, the retopology path it uses is **superseded** (not needed if you use the native swap). |
| `build_awo_v20/v22.py` | ❌ superseded | Tried to rebuild with "fixed counts" (sec34=1956, IB=5140). The runtime does NOT require fixed counts (lesson 9). |
| `build_awo_from_json.py` | ❌ superseded | Binary retargeting with matrices → shear/deformation (lessons 10-12). |
| `inject_a18.py` / `inject_a18_v21.py` | ❌ superseded | Partial coordinate injection → deforms (the runtime uses its topology). |
| `empaquetar_v20.py` | ❌ superseded | Packs old sec34/vb2/ib. |
| `emd_to_awo_hd.py` | 🔬 incomplete | Half-done SDBH EMD parsing; the EMD path is no longer needed (B3 HD already has the models in `#AMB`). |
| `json_to_obj.py` / `fbx_*.py` | 🔬 helper | Auxiliary utilities for the old flow. |

### 6.2 Bug common to ALL the old scripts

1. **Wrong AWG0 header offsets** (B1 lesson 8): they read sec34 from `+0x34`
   (which is really `post_size`). The correct header is: `sec_off=+0x28`,
   `sec_size=+0x2C`, `post_off=+0x30`, `post_size=+0x34`, **relative to
   AWG0**.
2. **Wrong vertex layout** (lesson 5→v10): the correct layout is
   `pos(0/4/8) weight(12) bone(16) nrm(20/24/28) 0xFFFFFFFF(32) blend(36)
   uv(40)`.

---

## 7. ROADMAP TO MAKE B3 WORK (suggested order)

### Step 1 — B3 mod system (per-AFS-entry override) [essential]

Today B3 only replaces **whole files** (`PrepareRegionData` copies
`mods/<mod>/us/<file>` over `us/`). Model swaps need the **per-AFS-entry**
override that B1 already has. (Done later: AGENTS §6.)

Options:
- **A (quick)**: copy B1's `src/mods.cpp`/`mods.h` to B3 + B1's Mods tab UI.
  The entry override lives in the SDK
  (`rexglue-sdk/src/filesystem/devices/host_path_file.cpp` →
  `AfsFindModOverride`) — if B3 uses the same SDK with that change, the hook
  already works; check that B3's `rexruntime.dll` includes it.
- **B (without rebuilding the SDK)**: pack the AFS with the replaced entry (AFS
  packer tools) and use the existing whole-file override. Slower to iterate,
  but does not touch the runtime.

### Step 2 — `swap_b3.py` tool (swap inside B3)

New script (or extension of `launcher_mod_pipeline.py`):
- `catalog --b3` (already exists → 56 characters).
- `swap3 --origen <label> --dest <bin>`: extracts the source's `#AMB` from B3's
  `data_cmn.afs`, compresses `/N:2048`, pads to the target slot's size and
  installs into `mods/<mod>/us/data_cmn.afs/<bin>/geom.bin`.
- Validate with a known swap (e.g. Android 19 → Krillin) at runtime.

### Step 3 — Fix the rest of B3's extractors

- `obj_to_awg.py`: apply the same offsets/layout fix as `awg_to_obj.py`
  (useful if manual retopology is ever wanted, although it is no longer the
  path).
- Mark the `build_awo_*`/`inject_*` scripts as obsolete (move them to
  `mod center hd/obsoletos/`).

### Step 4 — B1 → B3 port (reverse)

Create `port_b1_to_b3.py`:
- Reverse seal conversion (flag `0x2→0x4`, type2 `0x1BD→0x29BD`, B3 materials
  scale 1.0, AZT with original alpha).
- Pack the B1 AWO+AZT into `#AMB` or install per entry.
- Test with a playable B1 character (e.g. Tenshinhan HD) in a B3 slot.

### Step 5 — Integrate everything into the B3 launcher

Port B1's "Mods → Model pipeline" tab (catalogue + combos + port/swap button)
to B3. Reuse B1's `mod_pipeline.{h,cpp}`.

### Step 6 — (Optional) Moveset ports

The B3 → B1 moveset was discarded (lesson 13: the slot's `#ACM` cannot be
replaced without full RE of its poses). This is NOT needed for model swaps.

---

## 7b. PS2→B3 HD PORT — PATH B (windows + IB) ❌ DOES NOT RENDER (2026-09-12)

For models that **do NOT exist in HD** (if they exist → native swap, §5).
⚠️ **State**: the geometry is emitted **exactly** and reaches the GPU, but the
model **explodes** when rendered (the guest splits the IB by the template's
descriptors/part ranges, which do not match the PS2 topology). **Do NOT use as
a delivery**; the A/B ranges + mesh-refs still need rebuilding. (Later
findings: AGENTS §3.4.10 — B3 HD skins on the CPU.)

1. Extract the PS2: `python ports/port_ps2_b3_extract.py <ps2.amb|amo0>
   <extract.json>` (model space + skin + labels).
2. Choose an HD template with the **same skeleton (labels) and texture**.
3. Port: `python ports/port_b3_windows.py <extract.json> <template.bin>
   <out.amb> [--fit|--no-grow]` → emits **44 B windows + IB** (maps bones by
   label). `--fit` = cluster-decimate if it does not fit; without `--fit` it
   grows (`grow`, experimental).
4. Pack: LZX `/N:2048` + pad to `ceil(comp/0x1000)*0x1000` (see `swap_b3.py`),
   override in `mods/<mod>/us/data_cmn.afs/<entry>/geom.bin`.

**Vertex buffer model** (see §3.2): the GPU draws a verbatim copy of
`[vb0, ib)`, N windows of 44 B (`pos@0,w@12,bone@16,nrm@20,marker@32,uv@36`) +
IB (list, prim=4). Semantics: `pos=inv(world[bone])·model` and
`nrm=inv(world[bone]).R·model_nrm`, **natural order**. Canonical tool:
`awo_tools/awg_vertex_buffer.py`.
⚠️ **NOT validated in game** (2026-09-12): the port renders **exploded** even
though the geometry is exact and reaches the GPU (see
`SESION_VIA_B_RENDER_2026-09-12.md`).

## 8. REFERENCES

- **Swap methodology** (B1): `docs/tutoriales/MODEL_SWAPS_METODOLOGIA.md`.
- **Gero B3→B1 port session**: `docs/re/SESION10_PORT_B3_B1_FUNCIONAL.md`.
- **B1→B1 swaps session**: `docs/re/SESION9_MODEL_SWAPS_B1_B1.md`.
- **HD animations/movesets**: `docs/re/ANIMACIONES_MOVESETS_HD.md`.
- **Key lessons**: the B1 project's `AGENTS.md` (lessons 1-15).
- **Character catalogue**: `mod center hd/cache/characters.cat` (B1).
- **Working pipeline (B1)**: `mod center hd/launcher_mod_pipeline.py`,
  `mod center hd/swaps/swap_b1.py`,
  `mod center hd/conversores/install_b3_to_b1.py`.

(The references in this section are paths in the B1 project.)
