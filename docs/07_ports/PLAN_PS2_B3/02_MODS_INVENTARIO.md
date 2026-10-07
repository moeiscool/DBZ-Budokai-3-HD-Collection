# 02 — INVENTORY: mods, tools and resources for the PS2→B3 HD port / face / extra bones

> Inventory session 2026-09-10. Goal: locate EVERYTHING existing related to
> model conversion/port, head/face swap, extra bones (48-63) and vertex
> formats. **No code was modified.**
>
> The pending problem motivating this inventory: the **single-bone AWGs**
> (bones 48-63 in Cell F2; face/hands in Krillin) **have no PS2 equivalent**
> and the vertex injection (Path A) only touches the first AWG0's `sec34`.

---

## 0. EXECUTIVE SUMMARY

1. **There is NO tool (community or ours) that converts PS2→360 HD.**
   Verified by code: all the tools in `mod center/` use `struct.pack('<L')`
   (little-endian → PS2). The only BE one in the collection is `A3T Analyzer`
   (textures only). The PS2→360 jump is a **re-layout of our own** (endianness
   + renamed magics + AMG→AWG offset table). See
   `docs/07_ports/ESTUDIO_ECOSISTEMA_MODS.md` §3.
2. **The HD→HD head swap is half solved and paused**: there is
   `awo_tools/swap_cabeza.py` (block rebuild → **crash**) and
   `awo_tools/swap_cabeza_inplace.py` (in-place injection → **loads and enters
   battle**, with z-fighting). Resulting mod: `mods/goku_armadura` v3.0.
3. **The face blocker is NOT the format**: it is that the **AWG0 draws
   face/hair/teeth** through its own descriptors, in addition to the separate
   face AWGs. Injecting into the face AWGs does not replace the AWG0's face →
   z-fighting.
4. **Extra bones 48-63 (Cell F2)**: confirmed. The HD bin has **17 AWGs**: AWG0
   (48 bones, body) + **16 single-bone AWGs = bones 48-63**. The PS2 only has
   48 bones (0-47) → those 16 AWGs stay HD. Detail in `AGENTS.md` §3.4.2 and
   §10; instruments in `awo_tools/`.
5. **Documented vertex formats**: A and C in the AWG0 (auto-detected), the face
   AWG's own layout (buffer fixed at `h+0x1F0`), and `vb2`'s own layout. The
   pipeline has to auto-detect A/C (`awg0_export.py:detect_format`).

(⚠️ Later correction: all AWGs use one window layout; see
`SESION_DRAW_SEMANTICS_2026-09-11.md` §20.1.)

---

## 1. TOOLS THAT CONVERT/PORT PS2→HD MODELS (or rebuild the format)

### 1.1 `mod center hd/ports/` — named PS2→B3 HD pipeline (ours)

Folder created 2026-08-26 (`docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md`). Each
script is self-contained and outputs intermediate JSON.

| Script | Function | State |
|---|---|---|
| `port_ps2_b3_extract.py` | Parses a PS2 model (`#AMB`/`#AMO0`): mesh by FaceType, rig/skin (bone+weight per vertex), skeleton (80B axes) and labels. Auto-detects the AMG0 and rejects HD. | ✅ DONE |
| `port_ps2_b3_geometry.py` | Local coords + bone → HD buffers (format-A 44B `sec34` + 44B `vb2` + u16 BE IB). | ✅ DONE |
| `port_ps2_b3_draw.py` | [KEY PIECE] HD draw structure (mesh-ref blocks, arms, descriptors, axes). Detects real descriptors (stride `0x2C00`). | 🔴 **The regenerator for a reordered pool does NOT EXIST** (the real blocker) |
| `port_ps2_b3_inject.py` | **Path A (validated)**: HD template intact + rewrites `+12/+16/+20` of the `sec34` with PS2 geometry in bone-local. Flags `--npm`, `--bone-aware`, `--bone-thr`, `--soft`. | ✅ WORKS |
| `port_ps2_b3_pack.py` | Packs a self-contained `#AMB` + LZX + override. Neutralises leftover descriptors (A out of range, B=0). | ✅ |
| `port_ps2_b3_verify.py` | Exports OBJ + bounds/NaN check. | ✅ |
| `port_ps2_b3_decimate.py` | Decimates geometry (44B step). | aux |
| `test_injection.py` | Offline injection test. | aux |

**Key snippet of `port_ps2_b3_inject.py`** (conversion to bone-local and HD
normal):
```python
# ... world_mats(t, awo): the template's axes, parent = (AWG0+poff-axes_base)//80
sec_real = AWG0 + sec_rel + 2
n_slots = (vb2_rel - sec_rel - 2)//44
bone = be32(templ, o + 28)
z, x, y = be_f(templ, o+12), be_f(templ, o+16), be_f(templ, o+20)
slot_world.append(world[bone].dot(np.array([x, y, z, 1.0]))[:3])
...
lc = inv[bone].dot(np.concatenate([pos, [1.0]]))
f32i(templ, o+12, float(lc[2])); f32i(templ, o+16, float(lc[0])); f32i(templ, o+20, float(lc[1]))
# HD normal format: [nz, -ny, nx]
```

- **Documented structural limit (2026-09-10)**: `port_ps2_b3_inject` only
  touches the **first AWG0**'s `sec34`. The **16 single-bone AWGs** (48-63) are
  not PS2-ified (face stays HD). To PS2-ify the face, PS2 bones 33-40 would have
  to be remapped by label to AWGs 48-63 with **vertex formats varying per
  AWG**.

### 1.2 `awo_tools/` — format RE and experiments (reference)

| Script | Function | State |
|---|---|---|
| `awg0_export.py` | Exports AWG0 → OBJ **auto-detecting format A/C** and the buffer location. | ✅ Recommended |
| `awg_to_obj_b3.py` | Exports full B3 bins → OBJ. | ✅ |
| `awg_cara_export.py` | Exports a face AWG (nb=1) → OBJ. | ✅ (used to validate the head swap) |
| `awg_parts.py` / `awg_parts2.py` | Per-AWG parsing. | aux |
| `parse_ps2_mesh.py` | PS2 mesh parser (verts + real IB by FaceType). | ✅ |
| `ps2_rig_skin.py` | PS2 rig: bone+weight per vertex (chunks/sub-chunks). | ✅ |
| `pose_matrix.py` | PS2 bone world matrices. | ✅ |
| `ps2_to_hd_geometry.py` | PS2 → HD buffers (predecessor of `port_ps2_b3_geometry`). | ✅ |
| `build_from_template.py` | Builds a self-contained HD bin using **Cell F2 (147, 48 bones)** as the template. Internal mid-insert. | ✅ (generated `janemba_from_cell`/`janemba_cell48`) |
| `build_awo_autocontenido.py`, `build_awo_desde_cero.py`, `build_awo*.py` | AWO construction. | 🔸 experimental |
| `port_ps2_to_b3.py`, `port_b1_to_b3.py`, `mezclar_ps2_hd*.py` (v1-v6), `inyeccion_awg.py`, `inject_a18*.py`, `relayout_*.py`, `retarget_hd.py` | Previous experiments. | ❌ **Do NOT use as a base** |
| `swap_cabeza.py`, `swap_cabeza_inplace.py` | Head swap (see §2). | ◑ partial (face) |
| `swap_cuerpo_hd*.py` | Body injection. | ❌ failed |
| `phase_b_*.py` | Phase B instruments (census, consumer scan, arms dump, tests T2-T7). | ✅ research |
| `cell_align_check.py`, `cell_dist_stats.py`, `scan_bones.py`, `trace_bone.py`, `analyze_awg*.py`, `analyze_mesh*.py` | Analysis / rigs. | ✅ |

> ⚠️ `analyze_bin_hd.py` is **outdated** (PS3 layout) — do not use.

### 1.3 `mod center/` — PS2 community (36 programs) — **none does PS2→HD**

Model conversion (all LE):
- `OBJ to AMG v0.92` — OBJ→PS2 mesh parts from templates
  (`model_part_header.bin`, `triangle.bin`). 48B vertices expanded per
  triangle, `FaceType=1`.
- `EMD to AMG v0.90` — Xenoverse/SDBH EMD → PS2 AMG.
- `B3-IW AMO Converter + Shadows` — B3/IW→B1 (remaps mesh part headers).
- `Bin to OBJ (English Version) V3` / `AMG to OBJ V2` — PS2 AMG→OBJ.
- `Model Merger Tool (32-Bit)` — merges 2 AMOs (AMO_LGBT).

Rig/bones (relevant for extra bones and face):
- `Model Rig Toolset V0.6` / `Model-Rig Extractor Tool V1.0` — extract the rig
  per bone (32B chunks/16B sub-chunks with a vertex offset at +12) → **rig→mesh
  mapping**.
- `Bone Addition Tool v1.02` — **adds a bone** to the AMO (80B axis +
  child/sibling/parent + labels). Useful as a reference to generate extra
  bones.
- `Model Part Editor` — converts mesh parts B3⇄B1 (headers/shader/rgb_lines).
- `Axis Line Tool`, `BoneAxis Display` — axes/bones.

Packing / compression:
- `AFS Toolset v0.90`, `AMB Tool`, `AMBStudio`, `Budokai AMB Packer-Unpacker`,
  `AMB_AMT.Manipulator 1.5`, `B3_IW Model Converter` (only packs AMB).
- `Xbox 360 Compression - Decompression tool from the XBOX Development Kit` →
  **`xbcompress.exe /N:2048`** (critical).

Others: `A3T Analyzer` (BE textures), `Budokai3_SLUS_Editor_v08`,
`SLXS Editor v0.50`, `LST Event Editor 0.7`, `PSound`, `CRI ADX Tools`,
`Set Unlimited Fusion`, `Transformation Input Stuff`, `Shin Budokai 2 Tools
0.4`, `Zero Devs' Tool`, etc.

> **`mod center\Binary Templates` does NOT exist** in this repo. The binary
> templates are in: `mod center\<tool>\Files\Templates\`,
> `modding resources discord\research\B3_AMB_PS3.bt` (010 Editor, big-endian)
> and `modding resources update 2\lean bone tutorial\Budokai Toolset\Files\AMG\*.bin`.

### 1.4 Other folders
- `SDBH_body/` — only **DDS textures** (`DATA000.dds`… `FACE_W`, `HAIR`, etc.)
  and `embFiles.xml`. No model tool.
- `portforge/` — only a forge launcher config (`.forge.json`,
  `.mediaitem.json`). Not relevant to the port.
- `tools/` — project utilities (build/release/codegen): `fix_eu_bctr.py`,
  `prefix_eu_codegen.py`, `make_release.ps1`, `verify_release.ps1`,
  `sync_github.ps1`, `lab_f0.ps1`, `cleanup.ps1`, `find_jtables.cpp`,
  `extract_jt.cpp`. **They are not model tools.**

---

## 2. HEAD / FACE SWAP — how they work

### 2.1 `awo_tools/swap_cabeza.py` — block rebuild ❌ (crash)

It takes the bin of **armoured Vegeta (424, base)** and replaces its block of
face AWGs (`AWG19-25, XVGT_Lxx_S00_FACE`) with **Goku's (16-22,
XGOK_Lxx_S00_FACE)** by **numeric label** correspondence (`L09→L00_S09` and
`L42→L44` with an alias).

**How it works (code `awo_tools/swap_cabeza.py`):**
1. `get_awg_labels()`: walks the AWG table (`AWO+0x1C`, count at `AWO+0x18`),
   reads the mesh group (`h + u32(h+0x20)`) and applies the regex
   `X?[A-Z0-9]{3}_L([0-9A-Z]+)_S[0-9A-Z]+_FACE` to extract the label number.
2. `read_awg_cara()`: header `0x1F0`; descriptor at `h+0x180` (`+0x1C`
   n_verts, `+0x24` n_tris); **vertex buffer ALWAYS at `h+0x1F0`** (stride 44);
   IB at `h+ib_rel` (`+0x30`), size at `+0x34`.
3. `build_awg_cara()`: repacks **Vegeta**'s header + **Goku**'s geometry:
   ```python
   ib_rel = 0x1F0 + buf_size - 32          # the IB OVERLAPS the buffer by 32 B
   end_rel = ib_rel + n_idx*2
   data = buf_bytes[:buf_size - 32] + ib_bytes
   ```
4. Replaces the whole face block at once, rewrites the offsets of later AWGs +
   `AZT` (offset 0x30) + AWO size (+0x24).

**Result**: structurally valid (0 NaN, 148-156 tris) but **the guest CRASHES**
(`0xC0000005`, GPU thread, no `AFS327 READ`). Probable cause: **the AWG0
references the face AWGs by offsets that break when the block moves**. →
`mods/goku_armadura` v1.

### 2.2 `awo_tools/swap_cabeza_inplace.py` — in-place injection ◑ (works with defects)

**It starts from Vegeta's bin (which already works) and copies Goku's geometry
into Vegeta's EXISTING face AWG buffers**, by label. **No mid-insert, no moving
offsets, no touching the AWG0.** If Goku's buffer is smaller → pads with
`0xFF`; if larger → **truncates to Vegeta's capacity**. Updates the
descriptor's `n_verts`/`n_tris`.

**In-game result (v2.0)**: it loads and enters battle (armoured Vegeta with
Goku's head). **BUT z-fighting on the forehead/eyes** because Vegeta's
face/hair/teeth are still drawn **from the AWG0** (descriptors
`XVGT_L00_S00_FACE`, `XVGT_HAIR`, `XVGT_M_DTEETH/UTEETH`).

**Fix v3.0** (`mods/goku_armadura`): **neutralise** those AWG0 descriptors by
setting `A_size/B_size = 0` (2×`XVGT_HAIR`, 2×`XVGT_M_DTEETH`,
1×`XVGT_M_UTEETH`; 20 descriptors kept). `RESULT`: parts of the hair disappear,
but **it is still not Goku's complete face**; the z-fighting was reduced but
not solved.

**Conclusion (HISTORICO §13.10, 2026-08-19)**: for a complete face the
**face/hair geometry of the AWG0's `sec34` must also be replaced** (not just
neutralised, which leaves holes), which requires **remapping vertices between
formats A/C**. Paused.

### 2.3 Resulting mod
- `out/build/win-amd64-release/mods/goku_armadura/` — manifest:
  ```
  type=swap_cabeza_inplace
  description=Goku con armadura saiyan v3: cuerpo Vegeta 424 + cabeza Goku
              + cara/cabello de Vegeta neutralizada
  source=Vegeta 424 + Goku 264   target=327
  ```
  (The manifest text is the original; it reads "Goku with Saiyan armour v3:
  Vegeta 424 body + Goku head + Vegeta's face/hair neutralised". Currently
  `.disabled`.)

### 2.4 Face AWG layout (nb=1) — solved
`HISTORICO_AGENTS.md` §13.9 and `awo_tools/awg_cara_export.py`:
```
+0  u32 0xFFFFFFFF (marker)
+4  u | +8  v            (UV)
+12 x | +16 y | +20 z    (position in the head bone's LOCAL space)
+24 weight (=1.0) | +28 pad 0.0
+32 nx | +36 ny | +40 nz (unit normal)
```
Face AWG header (rel `h`): `+0x10 n_bones=1`, **`+0x2C` = buffer SIZE
(n*44)**, `+0x30` ib_rel, **`+0x34` = IB SIZE (bytes, not an offset!)**,
`+0x38` end. Descriptor at `h+0x180`. Buffer ALWAYS at `h+0x1F0`. IB =
**triangle list** (every 3 = 1 tri), not a strip. Key: Goku's and Vegeta's
faces share the head bone's local space (almost identical bounds) → 1:1 copy
without transformation.

---

## 3. DOCUMENTED VERTEX FORMATS AND VARIANTS

### 3.1 AWG0 `sec34` — two auto-detected formats (stride 44)

From `awo_tools/awg0_export.py:detect_format` and `AGENTS.md` §3.2:

**Format A** (Krillin 327, Cell F2 147), buffer at `sec_rel+2`:
```
+0   FFFFFFFF | +4 u | +8 v | +12 z_local | +16 x_local | +20 y_local
+24  weight   | +28 BONE (u32) | +32 nz | +36 -ny | +40 nx
```

**Format C** (Goku 264, Vegeta 424, Babidi 96, Goten, armoured Krillin 329),
buffer at `sec_rel` (or `fin_mg`):
```
+0 x | +4 y | +8 z | +12 FFFFFFFF | +16 u | +20 v | +24 nx | +28 ny | +32 nz
+36 weight | +40 BONE (u32)
```

`detect_format` tries 3 buffer locations (`sec_rel+2`, `sec_rel`,
`mg+mg_size`) × 7 marker offsets (`0,2,12,16,24,38,40`) and picks the one with
≥50% `FFFFFFFF` markers. ⚠️ The `sec34` location **varies per bin** (Goku at
`sec_rel`, Vegeta at `fin_mg`, Krillin at `sec_rel+2`).

### 3.2 `vb2` (stride 44) — own layout (static, bone=0xFFFFFFFF)
```
[x, y, z, 0, 0, 0, weight=0, 0xFFFFFFFF@+28, nx, ny, nz]
```
It covers the **head/faces (and legs in some bins)** and the PS2 injection does
**NOT touch it** (→ face/legs are not fixed by Path A). In Krillin: 226 slots,
15.4% of the IB. Cell F2's `vb2` = layout B (not yet emitted correctly by the
port).

### 3.3 PS2 formats (source) — `port_ps2_b3_extract.py:VERT_STRIDE`
```python
VERT_STRIDE = {0xBD:48, 0xFD:48, 0x3D:48, 0xB5:48, 0xB6:48, 0xF5:48,
               0x199:32, 0xB4:32, 0xA4:32, 0x99:32, 0x92:32, 0x19:32,
               0x90:16}
```
Detail in `modding resources update 2/INFORME_modding_resources_update_2.md`
§3: `B5`=standard 48B character; `B4/BD`=32B facial; `0x90`=16B shadows. **The
PS2 IB is implicit** (FaceType 1=strip, 0=triplet), not an index list.

### 3.4 AWG (HD) headers — canonical offsets
From `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md` §3.1 (⚠️
`docs/03_formatos/BIN_LAYOUT.md` and `AMO_AWO.md` are **WRONG**):
```
+0x14 axes | +0x2C vb2 | +0x30 IB | +0x34 sec34 (align +2) | +0x38 end
```
Submesh descriptor (0x60): `A=+0x50/+0x54` (vertices), `B=+0x58/+0x5C` (IB
indices), all `<<8` and flag `0x01` in the 2nd table. **There are TWO
descriptor tables**: mesh group @`AWG0+~0x2D49` (0x60) and **`AWG0+0x1F80`**
(flat u32: `42,60,74,126`…), probably the one the draw consumes at runtime.

---

## 4. EXTRA BONES 48-63 / SINGLE-BONE AWGs / CELL & SEMI-PERFECT

### 4.1 Cell F2 (bin 147) = 48-bone template
- `awo_tools/build_from_template.py`: uses **Cell Form 2 (bin 147)** as a valid
  HD template; generates `janemba_from_cell`/`janemba_cell48` with Janemba's
  geometry.
- `AGENTS.md` §10 and §3.4.2: Cell F2's HD bin has **17 AWGs** = AWG0 (48
  bones, 2661 verts, body) + **16 single-bone AWGs = bones 48-63**
  (face/details). The PS2 only has **48 bones (0-47)** → those 16 AWGs **have
  NO PS2 equivalent** and stay HD (that is why the face comes out HD).
- `HISTORICO_AGENTS.md` §1796 (table): `Cell F2 | 147 | 17 | 48 | FFFF at +0 |
  format A`.
- Test mod `mods/cell_best` (manifest): *"Cell F2 PS2->HD: extractor fixed +
  NPM 0.8, hands in real HD (template) + anti-stretch guard (68 verts)"*.
- `mods/cell_npm4_test`: the best historical injection (NPM + normals +
  threshold 0.8).
- Related test mods (all `.disabled`): `cell_npm2/3/6/7/8`, `cell_bone0_test`,
  `cell_clamp33_test`, `cell_boneclamp_test`, `cell_conv2_test`,
  `cell_desc_test`, `cell_ps2_port`, `cell_port_Afix_test`,
  `cell_reverse_test`, `cell_bodyfmt_test`, `cell_delta0_test`,
  `cell_nopad_test`, `cell_inject*_test`, etc.

### 4.2 Extra bones in other contexts
- **Tien with cape (IW→PS2)**: `docs/07_ports/SESION_TIEN_RIG_2026-09-08.md` —
  42 common labels in the **same order** as Tenshinhan HD (entry 400) + **10
  extra cape labels** (`XTSH_MANT*`, `XTSH_RMANT`, `XTSH_LMANT`). **Passes the
  base rig 1:1**; the cape is isolated as a second experiment. → active
  candidate for Path B.
- **Pikkon IW** — discarded: PKH skeleton (58 bones with skirt) ≠ KLL → not
  1:1.
- **IW model → AMB** — `modding resources/All Character Models from IW into AMB
  format/` (241 `.amb`, incl. Janemba 48 bones/17 AMGs same as IW bin 541).

---

## 5. COMMUNITY DOCS / TUTORIALS (porting models, bones, face, skinning)

### 5.1 Own reports (the most useful, already extracted)
- `modding resources update 2/INFORME_modding_resources_update_2.md` — a
  **full technical report** of PS2 formats and tools (contains §2 vertex
  format, §3 `meshType` tables, §4 rig/axis lines, §7 tools, §8 hex editing).
- `awo_tools/HALLAZGO_COMUNIDAD.md` — the IW→B3 PS2 ecosystem is already
  solved; the gap is PS2→HD.
- `awo_tools/RE_AWO_HD_CONVERSOR.md` — RE of the HD AWO, map of Krillin's 18
  AWGs (AWG11-17 = `XKLL_*_FACE`), `sec34` layout, descriptors and mesh-ref
  blocks.
- `awo_tools/SUBMESH_DATA_B3.md` — descriptor layout (0x60), contiguity of
  range A, structural map of the AWG0. Note: the `vb2` covers 15.4% of the IB
  (head/faces).
- `awo_tools/CONSOLIDADO.md`, `awo_tools/RE_PROGRESO.md` — historical RE.

### 5.2 Community tutorials (paths)
In `modding resources update 2/`:
- `SB2 Breakdowns/SB2_-Transplanting_head_from_one_model_to_another_By_Lean_and_Cueliton.docx`
  — **head transplant** (SB2). The closest to the face problem.
- `lean bone tutorial/` — `Tutorial12.rtf` (**per-bone re-rigging**, scale a
  bone to 0 and export OBJ per bone), `budokai_updated.ms` (**AMO/AMG
  importer**, documents the **implicit IB**: FaceType 1=strip, 0=triplet),
  `Rig Data Tool`, `Budokai Toolset` (Nexus: `amg_c`, `amo_s`, `amo_lgbt`,
  `axis_e`, `b1_i_e`, `m_p_e`…), `OBJ to AMG v0.92`.
- `- Budokai OBJ Editing Tutorial 2/` and `- Tutorial de Edición de OBJ para
  Budokai/` — edit mesh parts in Blender and rebuild with OBJ→AMG (PS2 UVs
  "upside down", use Mirror Y).
- `Tutorial #1 Añadir AMG manualmente (Español latino)/Tutorial.docx` — add an
  AMG by hex (edit length, number of parts, axis lines, target bone).
- `Acidicionando partes do personagem.docx` — add parts, detection `01..46`,
  remapping axis lines.

In `modding resources discord/tutorials/`:
- `SB2_-Transplanting_head...`, `CREATE_AMG_WITH_...`, `AMG_and_adding_m...`,
  `Adding_Model_Par...`, `How_to_combine_m...`, `Inject_and_debug...`,
  `SLXS Edit Tutorial` (1-1 model data blocks, 1-2 adding models to costumes),
  `Tutorial_anadir...`, `Tutorial_remove...`, `LGBT_Method.zip`, etc.

In `modding resources update 2/`:
- The `SLXS Edit Tutorial - Lesson 1-1..4-1` series (B3 GH and IW) — character
  data blocks, model bin list, face AMM, adding transformations, select.
- `DBZ B3 (X360) - Lesson 1` (LZX `/N:2048`), `DBZ B3HD - Lesson 2` (AZT/DDS
  textures).

> ⚠️ **No community tutorial covers PS2→360 HD**: only PS2→PS2 (B1⇄B3, IW→B3,
> EMD→AMG, OBJ→AMG) or editing the HD with 010 Editor + a template.

---

## 6. RELEVANT INSTALLED MODS (`out/build/win-amd64-release/mods/`)

A mod is active if it does NOT have `.disabled`. `AfsFindModOverride` serves
the **first** active mod in alphabetical order → **one mod per test**.

| Mod | Type | Description | State |
|---|---|---|---|
| `cell_best` | port_b3 | Cell F2 PS2→HD, NPM 0.8 + HD hands + anti-stretch guard (68 verts) | **ACTIVE** |
| `goku_armadura` | swap_cabeza_inplace | Vegeta 424 body + Goku 264 head; Vegeta's face neutralised | `.disabled` |
| `sw_goten_nativo` | native swap | Native Goten (validated) | `.disabled` |
| `sw_vegeta424` | native swap | Armoured Vegeta format C (validated) | `.disabled` |
| `swap_96_on_327` | native swap | Babidi over Krillin | `.disabled` |
| `cell_npm4_test` | port_b3 | Best historical NPM injection | `.disabled` |
| `cell_npm_fix` / `cell_npm_fix_nohand` | port_b3 | Injection with the axis-parent fix; without hand | `.disabled` |
| `janemba_cell48` / `janemba_from_cell` | port | Janemba IW→B3 via the Cell F2 template (48 bones) | `.disabled` |
| `tien_ps2_on_krillin` | port | PS2 Tien over Krillin | `.disabled` |
| `_t2_swap` / `_t3_reverse` / `_t4_inpart` / `_t5_noremap` / `_t6_adesc` / `_t7_ibrev` | Phase B tests | Pool/IB permutations (see §8) | all `.disabled` |
| `tex_*`, `krillin_*`, `janemba_v2`, `nappa_portrait`, etc. | various | Textures / experiments | `.disabled` |

There is no mod called `swap_cabeza*`; the result of the head swap is
`goku_armadura`.

---

## 7. THE REAL BLOCKER (reference for the plan)

From `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md` and `AGENTS.md` §3.4:

- **Path A (injection, keeps the pool order)** is the only validated delivery
  (`cell_npm4`, threshold 0.8).
- **Path B (full port, PS2 topology)** is blocked: even though the IB is
  remapped consistently (T3/T4) the render **deforms** → there is a
  **POSITIONAL consumption of the pool** that is NOT descriptor A (T6 normal)
  and NOT only the IB (T7 deforms). It is probably the **skinning structure
  (arms)/zones** tied to the pool order. (Later: it was a tool bug, see
  `SESION_GPU_DRAW_2026-09-11.md` §6-8.)
- **Two descriptor tables**: mesh group (0x60) and `AWG0+0x1F80` (flat u32).
- Phase B instruments in `awo_tools/phase_b_*.py` (census, consumer scan, arms
  dump, make_t2..t7, ab_compare, deep_scan).

---

## 8. THE MOST REUSABLE PIECES FOR THE FACE / BONES 48-63 PROBLEM

| Piece | Path | Why it is reusable |
|---|---|---|
| Face AWG layout (nb=1) + `awg_cara_export.py` | `awo_tools/awg_cara_export.py` | Already exports/validates the face AWGs; layout solved (buffer fixed `0x1F0`, IB triangle list). |
| In-place face geometry swap | `awo_tools/swap_cabeza_inplace.py` | The only method that **loads and enters battle** without moving offsets. |
| Neutralising AWG0 descriptors | `HISTORICO_AGENTS.md` §13.10 (v3.0) | Pattern to disable the AWG0's face/hair/teeth (A/B_size=0). |
| A/C format auto-detection + buffer location | `awo_tools/awg0_export.py:detect_format` | Needed to remap vertices between formats A/C (AWG0 face). |
| Bone-local NPM injection (Path A) | `mod center hd/ports/port_ps2_b3_inject.py` | Rewrites `sec34` with PS2 geometry; flags `--npm --bone-aware --bone-thr`. |
| Generating a self-contained bin from a 48-bone template | `awo_tools/build_from_template.py` | Cell F2 (147) template with 16 single-bone AWGs 48-63. |
| Full PS2 parsing (mesh+rig+skeleton) | `mod center hd/ports/port_ps2_b3_extract.py` | Detects the `#AMB`/`#AMO0` base, `VERT_STRIDE`, axis parent. |
| Community bone tool | `mod center/Bone Addition Tool v1.02/` | Reference to **add bones** (80B axis + child/sibling/parent + labels). |
| Per-bone rig extractor | `mod center/Model Rig Toolset V0.6/` | Documents the rig→mesh mapping (chunks/sub-chunks, vertex offset at +12). |
| HD AWO map (18 AWGs, face=11-17) | `awo_tools/RE_AWO_HD_CONVERSOR.md` | Identifies the face AWGs and their role. |
| Descriptor layout + two tables | `awo_tools/SUBMESH_DATA_B3.md` + `SESION_FASE_B_ARMS` §3.15 | Base for a future regenerator (Path B). |

### Detected gaps (what does NOT exist)
1. **Remapping PS2 bones 33-40 → HD AWGs 48-63** with vertex formats varying per
   AWG. No tool.
2. **Replacing the face/hair geometry of the AWG0's `sec34`** between formats
   A/C (required for a complete face without z-fighting). No tool.
3. **HD draw-structure regenerator** (mesh-ref + arms + 2 descriptor tables)
   consistent with a reordered pool (Path B). It does not exist.
4. **#AMT (PS2) → #AZT (HD) converter**. Only `texture_b3.py` (AZT→PNG→AZT).
