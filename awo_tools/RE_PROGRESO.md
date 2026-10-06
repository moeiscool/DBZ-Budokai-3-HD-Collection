# RE OF THE #AMO0 → #AWO CONVERTER (phase 3) — PROGRESS

> Working document for the reverse engineering of the HD 360 format (#AWO/#AWG/#AZT)
> compared against PS2 (#AMO0/#AMG/#AMT). Krillin bin 327 (GH PS2 = HD 360).
> Files: `%TEMP%\opencode\b327_ps2.bin` (812 KB #AMB LE) and `b327_hd.bin` (682 KB
> decompressed #AMB BE) — these temp files no longer exist; regenerate them from
> `us/` + `ps2_games/`. Tools: `awo_tools\*.py`.
> Status at the time: STRUCTURE MAPPING IN PROGRESS.
>
> **Reading note:** this is a chronological log, and several early conclusions
> were later refuted inside this same file (e.g. §17/§28 on re-topology, the
> vertex layouts of §18/§27/§38). The current, verified facts are in
> `AGENTS.md` §3.2–§3.4 and `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`.

## 1. SUMMARY OF FINDINGS

- **Same skeleton**: PS2 GH and HD 360 share the same Krillin model
  (51 bones, 18 AMG/AWG, 68 identical bone labels). **There is NO re-rigging**.
- **Same vertex formats**: B5 (`01 B5` LE / `00 00 01 B5` BE), B4, 90.
- **Same number of mesh parts**: bone 0 = 13 parts in both.
- Differences: endianness + renamed magics + section layout.

## 2. RENAMED MAGICS

| PS2 (LE) | HD 360 (BE) | Content |
|----------|-------------|-----------|
| `#AMB ` | `#AMB ` | Container |
| `#AMO0` | `#AWO ` | Model (header 0x30) |
| `#AMG ` | `#AWG ` | Mesh group (header 0x40 HD) |
| `#AMT ` | `#AZT ` | Texture |

## 3. #AMB CONTAINER HEADER

```
+0x00: magic #AMB
+0x0C: number of entries (PS2=3: AMO0+AMT+pad; HD=2: AWO+AZT)
+0x20: entry table (loc+size) × 16 B
```

## 4. MODEL HEADER (#AMO0 vs #AWO) — both 0x30

| Field | PS2 #AMO0 | HD #AWO |
|-------|-----------|---------|
| magic | `#AMO0` | `#AWO ` |
| +0x10 bone_am | 51 | 51 |
| +0x14 bone_loc | 0x80 | 0x30 |
| +0x18 amg_am | 18 | 18 |
| +0x1C | (amg_loc at 0x30) | **AMG offset table = 0x690** |
| +0x20 array_am | 24 | 24 |
| +0x24 | AMO label_loc | **bone labels = 0x6D8** |
| +0x34 | amg_loc2 | 0x42360 (end of area) |

**HD #AWO layout** (offsets relative to the AWO):
```
+0x00: header 0x30
+0x30: bone relation table (51 × 32 B = 0x660) → ends 0x690
+0x690: AMG offset table (18 × 4 B = 0x48) → ends 0x6D8
+0x6D8: bone labels (51 × 32 B = 0x660) → ends 0xD38
+0xD40: first #AWG
```

## 5. BONE RELATION TABLE (32 B/entry) — SAME in both

```
+0:  bone index
+4:  ptr to its axes-array entry (16 B)
+8:  ptr CHILD (to another relation entry)
+12: ptr SIBLING
+16: ptr PARENT
+20..31: padding
```

- PS2: bone_loc=0x80 (rel AMO0). E.g. bone0=[0, 0x6e0, 0xa0, 0, 0]
- HD: bone_loc=0x30 (rel AWO). E.g. bone0=[0, 0x42360, 0x50, 0, 0]
- Pointers are **relative to the AMO/AWO** in both.

## 6. AXES-ARRAY (16 B/entry) — SAME format

```
+0: 0
+4: bone index
+8: ptr to its "axis line" (80 B axis entry)
+12: 0
```

- PS2: bone0 at 0x6e0 → axis_line_ptr=0x5380 (rel AMO0 → abs 0x53C0)
- HD: bone0 at 0x42360 → axis_line_ptr=0x1750 (rel AWO → abs 0x1790)

## 7. AXIS ENTRY (80 B) — SAME format, different relative pointers

```
+0x00..0x2F: transform (identity floats: 0,0,0,1.0 ×2 + 1.0×5)
+0x30: stamp 0x6000020F (LE `0F 02 00 60`, BE `60 00 02 0F`) — IDENTICAL
+0x34: ptr to bone/armature block (PS2 rel AMG / HD rel AWG)
+0x38: ptr CHILD (to another axis)
+0x3C: ptr SIBLING
+0x40: ptr PARENT
+0x44..0x4F: padding
```

- PS2 axis0: +0x34=0x1010 → armature 0x63B0 (rel AMG)
- HD axis0: +0x34=0x1A00 → armature 0x2780 (rel AWG)

**NOTE**: in HD +0x34 is relative to the AWG; in PS2 relative to the AMG. In
both, axis0's armature (0x2780 HD) contains: `[0, mesh_hdr=0x1F80, 0, mesh_end=0x1E00, ...]`.

## 8. BONE / ARMATURE BLOCK (16 B) — SAME format

```
+0:  bone index
+4:  ptr to mesh-group header (rel AMG/AWG) or 0
+8:  ptr to rig data (weights) or 0
+12: ptr to "Mesh End" block (64 B) or 0
```

- PS2 bone0 armature @0x63B0: [0, 0x1020, 0, 0x26CA0] → mesh hdr @0x63C0
- HD bone0 armature @0x2780: [0, 0x1F80, 0, 0x1E00] → mesh hdr @0x2D00

## 9. MESH-GROUP HEADER — DIFFERS (FINE MAPPING PENDING)

- **PS2** @0x63C0: `[mp_amnt=0xD, 0x10, 0, 0, offs...]` + mesh part offset
  table at +16 (relative to the mesh-group header). part0 = +0x50 → 0x6410.
- **HD** @0x2D00: `[0xD, 0, 0, 0, 0, floats...]`. The HD mesh parts are
  **BEFORE** the mesh group (part0 @0x1450 vs mg @0x2D00). Different structure.

## 10. MESH PART — DIFFERENT LAYOUT

**PS2 (header 0xA0=160 B)**: type at +0x00, mesh_size at +0x90, vertices from +0xA0.
```
+0x00: type1 (01 B5) | +0x04: type2 (BD 29) | +0x08: texture | +0x0C: shader
+0x90: 0x60000000 + (mesh_bytes/16)
+0xA0: mesh data (face blocks + vertices)
```
PS2 part0 @0x6410: size=0xA90 → part0 spans 0xB30 (up to 0x6F40 = part1).

**HD (header 0x50=80 B)**: contiguous headers; vertices in a separate block.
```
+0x00: part index (0,1,2...)
+0x04: texture/material number (1,3,6... or 0xFFFFFFFF)
+0x08: type1 (00 00 01 B5)
+0x0C: type2 (00 00 29 BD)
+0x10: 0x44 (68)
+0x14: 0x44 (68)
+0x18..0x1F: 0
+0x20..0x3F: floats 3F800000 (material, pattern 3×1.0+0 repeated)
+0x40: 0
+0x44: 0x5 (count?)
+0x48: 0
+0x4C: 0x5
```
Contiguous HD parts: 0x1450, 0x14A0, 0x14F0, 0x1540, 0x1590, 0x15E0, 0x1630,
0x1680, 0x16D0, 0x1720(B4), 0x1770 — 0x50 (80 B) apart.

## 11. VERTEX FORMAT (confirmed in both)

- **B5** (48 B/vertex): V xyz(12) + pad(4) + VN xyz(12) + pad(4) + VT uv(8) + pad(8)
- **B4** (32 B): V(12) + pad(4) + VT(8) + pad(8)
- **90** (16 B): V(12) + pad(4)
- LE on PS2, BE on HD. Positions/normals match (same geometry).

## 12. HD AWG DATA ZONES (from header +0x28..0x3C)

```
+0x28: 0x2700   (rel AWG)
+0x2C: 0x17868  (rel AWG) → rig/index data
+0x30: 0x19F68  (rel AWG) → triangle indices
+0x34: 0x2826
+0x38: 0x1C790  (rel AWG) → ?
+0x3C: 0x24
```

## 13. CONVERSION STRATEGY

### 13.0 CONFIRMATION: generic 1:1 conversion (verified with 3 characters)

| Character | PS2 GH (bones/AMG) | HD 360 (bones/AMG) |
|-----------|---------------------|---------------------|
| Krillin | 51 / 18 | 51 / 18 ✓ |
| Cell | 54 / 19 | 54 / 19 ✓ |
| Goku | 64 / 19 | 64 / 19 ✓ |
| Janemba (IW) | 48 / 17 | — (does not exist) |

The #AMO0→#AWO conversion is **systematic and generic**: the same character
has the same number of bones/AMGs in both. It does not depend on the character.
Additional decompressed HD bins: `%TEMP%\opencode\b146_hd.bin` (Cell HD),
`b352_hd.bin` (Goku HD), `b146_ps2.bin`/`b352_ps2.bin` for the field-by-field
comparison.

### 13.1 TEMPLATE approach (for characters that already exist in HD)
Since the skeleton and hierarchy are identical:
1. **Template**: use an existing HD #AWO (same base character) as the structure
   template — headers, tables, pointers, axes, hierarchy.
2. **Geometry**: convert the PS2 mesh parts (vertices/indices/textures) to BE
   and replace those of the HD AWO.
3. **Mesh group**: the HD mesh group (13 parts) references its parts via
   contiguous 0x50 B mesh-ref blocks (stamp 0x9000020C/0x8000020C + armature
   ptr + index data ptr + transform ptr).

### 13.2 PORT approach (for IW exclusives like Janemba) — RECOMMENDED
The IW→B3 moveset ports already exist and **use Krillin's rig** (the host
character). The bin `modding resources\Infinite World to Budokai 3 Moveset
Ports\Janemba\B3\unnamed_333.bin` (2.2 MB) is the Janemba model already adapted
to the B3 rig. The bin `unnamed_331.bin` (#AMO0) is a mini-model.

**PENDING** (at the time):
- [ ] Confirm the port model (unnamed_333/331) is compatible with the
      AWO format (same number of bones as Krillin HD)
- [ ] Map the HD mesh group (how it references its 13 parts) — in progress
- [ ] Locate the HD vertex data per part — in progress
- [ ] Map the #AZT vs #AMT texture format
- [ ] Write the converter (endianness + renaming + re-layout)
- [ ] Validate with Krillin (convert GH→HD and compare bytes/render)

## 14. ADDITIONAL HD MESH-REF FINDINGS

The HD mesh group @0x2D00 references its 13 mesh parts via contiguous 0x50 B
blocks (at 0x1ED8 in Krillin). Each block:
```
+0x00..0x17: transform floats (matrix/identity)
+0x18: stamp 0x9000020C / 0x8000020C (part type)
+0x1C: armature ptr (rel AWG): 0x1BCC, 0x1BE0, 0x1BF4... (→ bone structures)
+0x20: index/normal data ptr (rel AWG): 0x1190, 0x11E0, 0x1230...
+0x24: 0
+0x28: transform ptr (rel AWG): 0x10F0, 0x1140...
+material floats after
```

The HD mesh-group header (0x2D00):
```
+0x00: mp_amnt (13)
+0x04..0x0F: 0
+0x10: 0 | +0x14..0x1F: floats | +0x20/0x24: 0
+0x28: ptr to the mesh-ref block table (0x1158 rel AWG → 0x1ED8)
+0x2C: 0x2C (ptr to the AWG bone label zone)
+0x30: 0x5 | +0x34..0x38: 0 | +0x3C: 0x2A | +0x40: 0 | +0x44: 0x48
+0x48+: labels (XKLL_BODY...)
```

## 15. CRITICAL CONCLUSION: GEOMETRY IS NOT 1:1

**The "same blocks in BE" shortcut does NOT work.** Verified:
- The PS2 part0 vertex positions (1.0988, -4.9691, 0.4898...) **do NOT
  exist** as BE floats in HD.
- HD has ~42K position floats vs ~141K in PS2 (fewer vertices).
- HD uses an **index buffer with primitive restart** (0xFFFF separates strips):
  - `AWG+0x30` → 0x1ACE8: u16 triangle indices (values < 64, coherent)
  - `AWG+0x38` → 0x1D510: FFFF restart + line/triangle indices
  - `AWG+0x2C` → 0x185E8: vertex buffer (floats)
  - `AWG+0x34` → 0x35A6: more vertex data

**Implication**: the PS2→HD converter is not a geometry byte-swap. It requires
repacking the expanded PS2 vertices (B5: V+VN+VT per triangle) into the HD
vertex/index buffer format. It is a real geometry converter.

## 16. REMAINING COMPONENTS FOR THE CONVERTER
- [x] Map the HD vertex buffer (layout: stride 0x2C, Z first, VN reordered/Y negated, VT last)
- [x] Map the HD index buffer (triangle list of 5140 u16 without restarts + FFFF restart buffer)
- [x] Understand how each HD mesh part references its geometry (0x50 B mesh-ref blocks)
- [ ] Map the #AZT texture format (vs #AMT)
- [ ] Write the converter (endianness + renaming + re-layout + geometric repacking)
- [ ] Validate with Krillin (convert GH→HD and compare render)

## 17. FINAL GEOMETRY CONCLUSION (IMPORTANT)

**HD geometry is NOT a conversion of the PS2 one — it is a dense re-topology.**

Evidence (Krillin bin 327):
- The PS2 X/Y positions (1.0988, -4.9691) do NOT exist in HD.
- The Z values match only PARTIALLY (~17/56 vertices of part0).
- The main HD AWG has ~2190 vertices; PS2 has ~42 B5 mesh parts across the
  whole model with lower density.
- The shared values (Z=0.49, -0.472, VN=0.7080/0.3271/0.6259, VT=0.4455/0.6194)
  are those of the corners/silhouettes that were preserved.

**Implication**: the HD models were re-topologized (denser, with recomputed
normals/UVs). There is no trivial PS2→HD converter that preserves the geometry
because HD uses ITS OWN geometry.

**Strategic consequence**: to add IW characters (Janemba, Pikkon, etc.),
the converter would have to:
1. Re-topologize/refine the PS2 geometry HD-style, OR
2. Use the PS2 geometry as is inside an AWO (if the HD runtime accepts
   B5 LE→BE vertices without re-topology), OR
3. Check whether another HD version of the model exists in the files (the
   character already exists in HD under another number, e.g. Krillin in bin
   327 vs the IW one).

**NOTE**: although the geometry differs, the STRUCTURE (bones, hierarchy, mesh
groups, mesh-ref blocks, vertex format) is identical and mapped. This allows
building the HD AWO with PS2 geometry if the runtime accepts it.

## Working files
- `awo_tools/parse_model.py` — #AMB → #AMO0/#AMG or #AWO/#AWG parser
- `awo_tools/analyze_awg.py` — analysis of an #AWG
- `awo_tools/analyze_mesh.py` — mesh parts inside an AWG
- `awo_tools/trace_bone.py` — hierarchical bone tracing (PS2 vs HD)

## 18. HD VERTEX LAYOUT (decoded)

The HD vertex (stride 0x2C = 44 B) has attributes at 0x3480:
```
+00: V.z
+04: weight/material ?  (varies per vertex)
+08: weight/material ?
+0C: weight/material ?  (0.5, 0.6, 0.4...)
+10: 0
+14: VN.z
+18: -VN.y   (Y negated)
+1C: VN.x
+20: nan
+24: VT.u
+28: VT.v
```
PS2 vert1 (V=(1.2942,-4.9691,0.002), VN=(0.9849,0.1730,-0.0063), VT=(0.4457,0.6853)):
```
HD: +00=0.002(V.z) +14=-0.0063(VN.z) +18=-0.1730(-VN.y) +1C=0.9849(VN.x) +24=0.4457(U) +28=0.6853(V)
```
The VN and VT fields match EXACTLY (with Y negated). The PS2 X/Y positions do
NOT exist in HD as floats — HD uses positions transformed into the bone's local
space (skinning), stored in a separate position vertex buffer (referenced by
AWG+0x2C).

## 19. DEFINITIVE CONCLUSION — A FULL CONVERTER IS REQUIRED

**The HD and PS2 formats are structurally equivalent but geometrically
different.** Converting a PS2→HD model needs:
1. Parse the PS2 AMO0 (bones, hierarchy, mesh parts, absolute vertices)
2. **Transform each absolute PS2 vertex into its bone's local space**
   (using the PS2 skeleton's skinning matrix)
3. Reorganize into the HD layout: positions (separate buffer) + attributes
   (Z, Y-negated VN, VT) + weights
4. Rebuild the index buffer (triangle list with FFFF restart)
5. Re-map headers and pointers (AWO/AWG, mesh-ref blocks)

It is feasible but it is a complete 3D geometry converter. No byte-swap
shortcut is possible.

**FASTER ALTERNATIVE (to be validated)**: the recomp runtime might accept
B5 vertices without re-topology if the AWO is built with the PS2 geometry
directly (LE→BE without transformation), reusing the HD AWO structure.
This would produce a model with the PS2 geometry (less dense) but functional.
Needs an empirical test loading the result in the game.

## 20. CONVERTER IMPLEMENTED (build_awo.py)

`awo_tools/build_awo.py` was written to convert a PS2 #AMO0 into an HD #AWO:
- Extracts PS2 geometry (extract_geometry.py): 43 mesh parts, 9715 vertices (Krillin)
- Converts each vertex to the HD layout (stride 0x2C): V.z + weights + VN(z,-y,x) + VT
- Builds the AWO: header + relation table + AMG offset table + labels + AWGs
- Wraps it in #AMB and compresses with xbcompress /N:32 (later: /N:2048 is the
  correct setting)

**Validation in progress**: mod `krillin_test` replaces bin 327 (Krillin) in
`out\build\win-amd64-release\mods\krillin_test\us\data_cmn.afs`. The game
boots stably (15 s without a crash). Visual test of Krillin's render pending.

**Possible test outcomes**:
- Krillin deformed/invisible without a crash → structure OK, missing the vertex
  transform into bone-local space (skinning)
- Normal Krillin → converter works, apply to Janemba/Pikkon
- Crash on load → adjust the format (skinning weights, mesh-ref blocks)

**Next steps depending on the outcome**:
1. If the structure is OK but the geometry wrong → implement the skinning
   transform (PS2 bone matrix → local space)
2. If it works → convert Janemba (bin 541) and add it to the roster
3. #AZT texture still to be mapped

## 21. VALIDATION RESULT: CRASH when selecting Krillin

The first converter (build_awo.py, simplified structure) **crashed** when
selecting Krillin. Diagnosis:

**Cause**: my generated AWG was a simplification without the complete
structure the runtime expects. My AWG vs the real AWG:
| Field | My AWG0 | Real AWG |
|-------|---------|----------|
| +0x14 axes_loc | 0x40 | 0xA10 |
| +0x18 axis_lines | 1 | 0xD (13) |
| +0x28 mesh_group | 0x40 | 0x2700 |
| +0x2C vertex buffer | 0 | 0x17868 |
| +0x30 index buffer | 0 | 0x19F68 |
| +0x38 restart | 0x310C0 | 0x1C790 |

The runtime follows the chain `axis → armature → mesh group → mesh-ref blocks →
geometry`. My AWG had no axes (80 B) nor the full chain → crash.

**Real HD AWG0 structure** (Krillin):
```
0x00: header 0x40
0x40: labels (bone x 32 = 0x660) -> ends 0x6A0
0x6A0: labels continue + mesh group sections
0xA10: axes (80 B each)
0x2700: mesh group of XKLL_L00_FACE (face) - sub-group
0x17868: vertex buffer (attributes stride 0x2C)
0x19F68: index buffer (triangle list)
0x2826: intermediate data
0x1C790: restart buffer (FFFF)
```

**HD skinning data**: fields +04..+0C of the vertex (stride 0x2C) are
skinning weights that do NOT derive from the PS2 vertex (V+VN+VT). PS2 stores
the weights in the rig data (weight groups with bone-local coords + offset
to the mesh vertex).

**PS2 rig**: 35 bones have rig data. Each weight group: weight (float),
vvn_am, vvn_loc (32 B entries: local coords + offset to the vertex).
The rig coords ARE ALREADY bone-local positions (ready for HD).
E.g. bone1: weight=1.0, vvn_am=52, coords=(1.338, 1.222, 0.375)...

**Conclusion**: the full converter requires:
1. Rebuilding the complete AWG structure (axes, armatures, mesh groups, mesh-ref)
2. Mapping each PS2 vertex to its bone via the rig data (offset → mesh part)
3. Using the rig coords (bone-local) as HD positions
4. Putting the right weights in the HD vertex
5. Rebuilding the index buffer

This is substantial reverse engineering work (more sessions). The complete AWG
structure and the rig→vertex mapping are documented above.

## 22. ADDITIONAL AWG STRUCTURE MAPPING (comparing Krillin/Cell)

**AWG header (0x40)**: layout confirmed deterministic comparing Krillin and Cell:
```
+0x10: bone_am (51 vs 54) — varies per character
+0x14: axes_loc — varies
+0x18: axis_lines = 0xD (13) — CONSTANT
+0x1C: label_loc = 0x40 — CONSTANT
+0x20: offset after labels (0x6A0 vs 0x700) — starts the mesh part headers
+0x24: number of mesh parts (11 vs 14) — varies
+0x28: mesh group data (materials)
+0x2C: vertex buffer
+0x30: index buffer
+0x34: normals/extra data
+0x38: restart buffer
+0x3C: 0x24 vs 0x1E (size of something)
```

**HD mesh part headers** (stride 0x50, at +0x20):
```
+0x00: 1.0 | +0x04: 1.0 | +0x08: 0
+0x0C: part index (0, 0, 0, 2, 4, 5, 7...)
+0x10: 0x44 (68)
+... (rest of the header)
```

**Materials** (mesh group data at +0x28): ~0x40/0x44 blocks with color/specular
floats + 0xFFFFFFFF (no texture).

**sec3C (rel 0x24)**: AWG offset table repeating the header values:
[count, 0x2700, 0x17868, 0x19F68, 0x2826, 0x1C790, 0x24, "XKLL_BODY"...]

**AWG0 structure (Krillin)**:
```
0xDC0: labels (51×32=0x660) → ends 0x1420
0x1420 (+0x20): mesh part headers (11 × 0x50 = 0x370) → ends 0x1790
0x1790: axes (80 B each)
0x3480 (+0x28): mesh group data (materials)
0x185E8 (+0x2C): vertex buffer (attributes stride 0x2C)
0x1ACE8 (+0x30): index buffer (triangle list)
0x1D510 (+0x38): restart buffer (FFFF)
```

**Pending**: how each HD mesh part header references its index range in the
ib (the material↔geometry link). This is the last AWG puzzle.

## 23. HD MESH PART HEADER (decoded)

The HD mesh part header (stride 0x50, at +0x20 of the AWG) for Krillin:
```
+0x00..0x1C: 1.0, 1.0, 1.0, idx, 1.0, 1.0, 1.0, 0  (idx = part index)
+0x20: 0
+0x24: 5  (attribute count?)
+0x28: 0
+0x2C: 5  (attribute count?)
+0x30: 0
+0x34: tex index (1)
+0x38: type1 (0x01B5 = B5)
+0x3C: type2 (0x29BD)
+0x40: 0x44 (68)
+0x44: 0x44 (68)
+0x48: 0
+0x4C: 0
```
All 11 parts have +0x24=+0x2C=5 constant. The mesh group data (+0x28)
has repeated counts 0x1D=29 (probably indices per part).

**OPEN PUZZLE**: the exact link between the HD mesh part headers, the
mesh group data materials and the index ranges in the index buffer.
Solving it requires tracing how the runtime assigns indices to each part.
(Later solved: the 0x60 descriptors, see `AGENTS.md` §3.4.8.)

## 24. RE STATUS SUMMARY (2026-08-13)

**MAPPED and DOCUMENTED**:
- AWO layout (header + relations + AMG table + labels + AWGs) ✓
- AWG layout (header 0x40 + labels + mesh part headers + axes + mesh group
  data + vb + ib + restart) ✓
- HD mesh part headers (stride 0x50) ✓
- HD vertex (stride 0x2C): V.z + weights + VN(z,-y,x) + VT ✓
- PS2 vertex (B5, 48 B): V+VN+VT ✓
- PS2 rig: per-bone local coords + weights + offset to the vertex ✓
- The PS2/HD skeleton is identical (51 bones, 68 labels) ✓
- HD geometry is re-topologized (denser) — NOT 1:1 ✓
- **#AZT texture format (360) — SOLVED via A3T Analyzer** ✓

**PENDING**:
- Material↔index range link in the AWG (the final puzzle)
- Complete PS2 rig → vertex mapping (offset→part→vertex)
- Working full converter (build_awo.py needs the complete AWG structure)
- Visual validation in game

## 25. #AZT TEXTURE FORMAT (360) — SOLVED

`mod center\A3T Analyzer\A3T Analyzer.py` (Nexus-sama) analyzes the 360
texture format. Verified on Krillin's #AZT (bin 327 HD):
```
+0x10: tex_am (14 textures)
+0x14: index_loc (0x20)
+0x20: texture offset table (14 × 4 B)
Each texture (at its offset):
  +0x00: 0
  +0x04: type (00 00 00 21=[T] compressed, 80 00 00 01=[S] simple, 00 00 00 01=[B])
  +0x08: 01 00 01 00
  +0x0C: width, height (u16 BE each)
  +0x14: data_offset (u32 BE)
  +0x24: 00 00 83 20
  ...
  Palette at data_offset, bitmap at data_offset+128
```
Krillin HD's 14 textures: 256×256, 64×64, 128×128... (composite and simple).

**#AMT (PS2) → #AZT (HD) conversion**: almost 1:1 endianness. Comparing
texture 1: +0x04 type SAME, +0x0C dims SAME, +0x14 data_offset SAME.
Minor differences in bitmap_offset (+0x18: 0x8000 vs 0x10080).
HD uses more bytes (391 KB vs 206 KB) — different compression (DXT).

## 26. FINDING: THE HD INDEX BUFFER IS A CONTINUOUS TRIANGLE STRIP

The AWG0 IB (0x1ACE8, 5140 u16) **has no internal FFFF restarts** — it is a
**continuous triangle strip** (5138 triangles) that draws the whole body.

The HD mesh part headers (stride 0x50) have:
```
+0x30: part index (0, 0, 2, 4, 5, 7, 8, 9, 10, 11, 12)
+0x34: texture (1, 3, 3, 1, 6, 6, 3, 1, 1, 0xFFFFFFFF, 6)
+0x38: type1 (0x01B5) | +0x3C: type2 (0x29BD)
```
The index is not sequential (0,0,2,4,5,7...) — parts are drawn in order
by that index, each with a range of the strip.

**OPEN PUZZLE**: where the limits (start+length) of each mesh part's strip
range are. The +0x24/+0x2C=5 fields are not the sizes.

## 27. DEFINITIVE FINDING: THE HD VERTEX IS THE PS2 ONE REORDERED (VALIDATED)

Exact check by VN+VT: HD vert0 (@0x3480) = **PS2 part0 vert0**
`pos=(1.099, -4.969, 0.490)`. HD vertex layout (stride 0x2C=44 B):
```
+00: V.z (0.4898) — matches PS2 vert0 Z
+04: 0.0752 (bone-local pos X?)
+08: 0.3621 (bone-local pos Y?)
+0C: 0.5000
+10: 0x1D=29 (bone index / weight group)
+14: VN.z (0.7080) — matches
+18: -VN.y (-0.3271) — matches (Y negated)
+1C: VN.x (0.6259) — matches
+20: FFFFFFFF
+24: U (0.4455) — matches
+28: V (0.6194) — matches
```

**Conclusion**: HD uses EXACTLY the same PS2 vertices (identical VN+VT,
identical Z positions), but in a reordered layout with additional skinning
data (+04/+08/+0C/+10). The geometry is NOT re-topologized from scratch —
it is the same mesh with extra fields.

**Implication for the converter**: PS2 → HD vertices is a deterministic
per-vertex transform (reorder fields + add skinning). The challenge is
getting the skinning data (+04/+08/+0C/+10) that HD has per vertex.
It comes from the PS2 rig (per-bone local coords + weights).

**PENDING**: decode exactly what +04/+08/+0C (local pos?) and +10
(bone index/weight) are and how to derive them from the PS2 rig for each vertex.

## 28. VERTEX MATCH REFUTED (2026-08-13, afternoon)

Exhaustive test of 5 HD vertices (0x3480) against the whole PS2 model:
- **NONE matches** by exact VN+VT+UV.
- Only vert0 matched before (PS2 part0 vert0) — it was a shared-corner
  coincidence (Z and VN came from a border vertex that exists in both).

**Final conclusion**: HD geometry is **re-topologized** (vertices in a
different order, with per-corner duplicates and extra skinning fields).
There is no 1:1 vertex→vertex correspondence between PS2 and HD.

**Strategic decision**: converting PS2→HD geometry this way would require
re-modelling/re-topologizing, which is not feasible automatically.
The PS2→HD converter is **not feasible** for producing native HD geometry.

## 29. ALTERNATIVE VIABLE ROUTES (to evaluate)

1. **Use the existing HD AWO as a COMPLETE template** and replace only the
   textures (#AMT→#AZT, solved) + colors/materials, keeping the native HD
   geometry. Good for: color/costume mods, not for new characters.

2. **Use the SDBH WM models (EMD/Xenoverse)** with the
   EmdFbx/FbxEmd + EMD-to-AMG ecosystem: convert Xenoverse models to PS2 AMG,
   then repack into HD AWO. EMDs already carry modern skinning (viable).

3. **Inject the complete PS2 model as an AWO with PS2 geometry** while
   building the complete AWG structure (axes + mesh groups + mesh-ref) —
   the runtime would render the PS2 geometry (less dense) inside the HD
   structure. Risk: crash if the structure is not exact.

4. **Characters that already exist in HD**: for Janemba/Pikkon/etc (which do
   NOT exist in HD), use the IW model directly if the runtime accepts an AWO
   with PS2 geometry without re-topology (requires validating the complete
   AWG structure).

**Recommendation**: route 3 is the most promising for adding IW characters.
It requires rebuilding the complete AWG structure (axes + nested mesh groups +
mesh-ref blocks), which is the open puzzle. The PS2 geometry is used as is
(converted to BE); the runtime should accept it even if less dense.

## 30. MESH PART CHAIN STRUCTURE (discovered)

AWG0 has **13 axes**:
- **axis0** (stamp `60 00 02 0F`): main mesh (XKLL_BODY) with a mesh group
- **axis1-12** (stamps `90 00 02 0C` / `80 00 02 0C`): rig bones (no mesh)

**Mesh group of bone0** (@0x2D00 = awg_hdr + 0x1F80 of the armature):
```
+0x00: count (13)
+0x28: mesh part table (0x1158 rel AWG → 0x1ED8)
+0x2C: 0x2C (vertex stride 44)
+0x30: 5 | +0x3C: 0x2A | +0x44: 0x48
+0x48: bone name ("XKLL_BODY")
```

**Mesh-ref blocks** (13 × 0x50 at 0x1ED8): each one
```
+0x18: stamp (0x9000020C mesh / 0x8000020C rig / 0x204 shadow)
+0x1C: arm (ptr to bones: 0x294C = [0x17,0,0,0, 0,0x18,0,0,0, 0,0x19,0x24E0,0,0x1E80,0,0x1A])
+0x20: dat (ptr to material/normals: 0x1F10 = [floats, 0x8000020C, next_ptr])
+0x28: tr (ptr to transform)
```

**Recursive chain**: each part's `dat` contains at +0x30 a `0x8000020C` stamp
followed by the `arm` and `dat` of the NEXT part. The runtime draws part0
(material from dat, bones from arm), then follows the chain.

**OPEN PUZZLE**: the exact count of indices/triangles each part of the strip
draws. It is not in the mesh-ref blocks nor in the arm. It probably derives
from the `dat` data (materials) or is implicit in the chain.

## 31. CONVERTER v2 (build_awo_v2.py) — complete real AWG template

Fixes the v1 crash: it now uses the HD AWO as a **complete binary template**
(keeps the 13 axes + mesh group + chained mesh-ref blocks + materials)
and replaces ONLY the AWG0 vertex buffer and index buffer with the PS2 geometry.

**Key fixes**:
- The `#AWG` magic is at `AMG_table[0]` (0xD40), the labels at +0x40
- Offsets +0x2C/+0x30/+0x38 are **relative to the start of the AWG**
- The new AWO = header+tables+labels (0 to awg0_off) + new AWG0 + AWGs 1-17

**Validation status**: AWO v2 generated (470 KB), structure verified
(correct #AWG magic, VB with PS2 V.z, IB triangle list, XKLL_BODY labels).
AFS rebuilt, mod `krillin_test` active, game boots stably for 15 s.

**PENDING**: visual test (select Krillin in battle). Possible:
- Deformed/invisible without a crash → structure OK, skinning missing
  (bone-local positions vs absolute PS2)
- Normal → converter ready for Janemba
- Crash → adjust (the mesh-ref blocks draw ranges of the old strip, which may
  not match the new IB)

## 32. CONVERTER v3 (build_awo_v3.py) — fixed sizes (FIXES THE CRASH)

**Cause of the v2 crash**: the runtime reads the VB/IB with the ORIGINAL HD
sizes (VB=9984 B, IB=10280 B). Replacing them with different sizes (PS2 VB=190 KB)
left the AWG internal pointers (relative to the AWG header) invalid →
`0xC0000005` (invalid memory access) while processing the model.

**v3 solution**: keep the original sizes:
- VB: fill the 9984 B with PS2 vertices (as many as fit) + padding
- IB: fill the 10280 B with PS2 indices + 0xFFFF (restart) at the end
- The AWG header offsets do NOT change → the mesh-ref blocks stay valid

**Status**: AWO v3 generated (294 KB, only +3.4 KB vs the original). Offsets
verified identical to HD (vb=0x17868, ib=0x19F68, restart=0x1C790).
AFS rebuilt, mod krillin_test active. Game boots stably for 20 s with no
exceptions in the log.

**PENDING**: visual validation (select Krillin in battle).
NOTE: since the PS2 VB (4331 vertices) does not fit in 9984 B (only ~226
vertices fit), the resulting model will show ONLY the first ~226 PS2 vertices
(geometrically incomplete). This validates the structure; the complete model
needs an AWG re-layout (move vb/ib and update pointers).

## 34. ROOT CAUSE OF THE CRASH FOUND (v4)

**Complete AWO layout** (decoded):
```
0x0000: header (0x30)
0x0030: relation table (bone × 32 B) → 0x690
0x0690: AMG table (amg × 4 B) → 0x6D8
0x06D8: labels (bone × 32 B) → 0xD40
0x0D40: AWG0 ... AWG17 (18 blocks)
0x42360: axes-array (referenced by header +0x34)
0x46FE0: end of the AWO
```

**The v2/v3 bug**: AWO header `+0x34 = 0x42360` is the offset of the
**axes-array** (which sits at the END of the AWO, 51×24=1224 pointers to axes).
My v2/v3 converters grew AWG0 (PS2 geometry), shifting the axes-array,
but did NOT update the `+0x34` pointer. The guest followed `+0x34` and read PS2
vertices instead of axis pointers → crash 0xC0000005.

**v4 solution**: keep AWG0 at the SAME total size (replace vb/ib inside its
original space), so NOTHING shifts and all pointers (+0x34 axes-array, AMG
table, mesh-ref blocks) stay intact.

**Status**: v4 generates an AWO of the same size (290784 bytes), verified with
an assert. Game boots stably. Visual validation PENDING (select Krillin).

NOTE: since only 226 vertices fit in the VB (out of PS2's 4331), the model will
show very incomplete geometry (74 triangles). This validates the structure; the
complete model needs a real re-layout (grow AWG0 + update +0x34).

## 35. ROOT CAUSE #2: THE MOD STRUCTURE IS WRONG

**The runtime does NOT replace the whole AFS.** Reading the SDK code
(`rexglue-sdk/src/filesystem/afs.cpp` and `host_path_file.cpp`):

- `AfsFindModOverride` looks for the override at `mods/<mod>/us/<afs_filename>/<entry_index>`
  (a **loose file** named after the index, NOT a full .afs file).
- `AfsFindEntry` uses the **original** AFS index (cached) to map
  byte_offset → entry.
- `host_path_file.cpp` reads from the mod at `byte_offset - entry_start`.

**My mistake**: I placed `mods/krillin_test/us/data_cmn.afs` (a full 293 MB
file). The runtime expects `mods/krillin_test/us/data_cmn.afs/327` (a loose file
named "327").

**FIX**: the correct mod structure is:
```
mods/<mod>/us/data_cmn.afs/327   <- the LZX-compressed bin (loose)
```

This simplifies everything: there is NO need to rebuild the whole AFS. Just
put the compressed bin as a loose file. (The "AFS rebuild" system we used
before was for the janemba mod with a full file — a wrong approach carried
over from earlier sessions.)

**Size limit**: the guest reads the bin with the original AFS size
(105296 B). The mod can be shorter (the runtime returns EOF at the end, OK)
but if it is longer it gets truncated. (Later: shorter also crashes unless it
is padded to `to_read`, and the virtual mid-insert of 2026-09-09 lifted the
size limit; see `AGENTS.md` §6.)

## 36. ROOT CAUSE #3 (DEFINITIVE): THE #AZT TEXTURE WAS MISSING

**The original bin 327 decompresses to 682528 bytes with TWO entries**:
```
[0] #AWO @0x40 size=290784  (model)
[1] #AZT @0x47020 size=391680  (texture)
```

My v4 converter only generated the AWO (290848 bytes) without the texture. The
guest loads the AWO and then looks for the #AZT (AMB entry 1), which did not
exist → crash.

**Solution**: include the original #AZT texture (copied as is) in the generated
AMB. The final bin has 682528 bytes uncompressed (same as the original)
with 2 entries: AWO (PS2 geometry) + AZT (original texture).

**Verification**: the LZX header of the compressed bin now says `0xA6A20 = 682528`
(the correct uncompressed size). Game boots stably for 30 s.

**Summary of ALL fixed root causes**:
1. Mod structure: loose file `mods/<mod>/us/data_cmn.afs/327`, NOT a full AFS
2. +0x34 pointer (axes-array) at the end of the AWO: v4 keeps the AWG0 size fixed
3. VB/IB size: indices limited to those that fit in the VB
4. **Missing #AZT texture**: the AMB must have 2 entries (AWO + AZT)

## 37. DECISIVE FINDING: TWO VERTEX BUFFERS + COMPLETE AWG0 MAP

**Krillin has 3 model bins** (not 1): 327 (51 bones), 328 (47 bones),
329 (50 bones) — the 3 costumes. Each one is an #AMB with AWO+AZT.

**Complete AWG0 map** (bin 327), offsets relative to the AWG:
```
+0x20 (0x6A0):  mesh part headers (880 B)
+0x14 (0xA10):  axes (7408 B, 80 B each)
+0x28 (0x2700): 294 B (small)
+0x34 (0x2826): MAIN VERTICES (86082 B = 1956 verts stride 44)
+0x2C (0x17868): SECONDARY VERTICES (9984 B = 226 verts)
+0x30 (0x19F68): INDEX BUFFER (10280 B = 5140 indices, max 2189)
+0x38 (0x1C790): 144 B (restart)
```

**The mistake of ALL my converters**: they replaced the `+0x2C` zone (226
secondary vertices) thinking it was the main VB. But the main vertex buffer is
`+0x34` (1956 vertices). The IB indexes 1956+226 = 2189 vertices.

**Ecosystem search (exhaustive)**: there is NO tool, script or documentation
of the 360 format (#AWO/#AWG/#AZT) in mod center, modding resources or
modding resources update. Verified: 1007 files with #AMO0 (PS2), ZERO with
#AWO (360). The only source of truth is the binary PS2↔HD comparison (this
document).

## 38. REAL HD VERTEX LAYOUT (stride 44, aligned +2)

The main vertex buffer (sec34) is **misaligned by 2 bytes** (it starts at
0x3568, not 0x3566). With +2 alignment, the layout of each vertex (44 B):
```
+00: nan (flag/w)
+04: VT.v
+08: VT.u
+12: V.z
+16: pos.x (bone-local)
+20: pos.y (bone-local)
+24: weight/bone
+28: 0
+32: VN.z
+36: -VN.y
+40: VN.x
```

Verified against a PS2 vert (V.z=0.4898, VT=(0.4455,0.6194)): the VT and VN
fields match (with Y negated), as in the secondary buffer.

**Layout conclusion**: the HD vertex contains V.z + bone-local positions
(skinning) + VN (reordered, Y negated) + VT. PS2 has V (absolute)
+ VN + VT. Conversion requires transforming absolute V → bone-local.

> (Later: the bone is at +28 in the sec34 reading of 2026-08-17, and later
> still the whole "sec34" reading was replaced by the window layout — see the
> reading note at the top.)

## 32. BUFFER RE-LAYOUT (2026-08-14) — AWO structure and bugs

### 32.1 REAL AWO STRUCTURE (RE corrections)

**AWO header** (@0x40 of the AMB):
```
+0x10: bone_am (51)     +0x18: amg_am (18)    +0x1C: AMG table ptr (rel AWO)
+0x34: axes-base (0x42360)  <- 51 entries of 0x20 with pointers to the axes zone
     +0x34, +0x54, +0x74, +0x94, ... (every +0x20, up to +0x674)
     Each entry: [ptr_axes, field2, field3, ..., bone_idx at +0x1C]
```

**AMG table** (18 entries): points to the `#AWG` magics of each AWG.
- `AWG0 = 0xD40` (rel AWO). **Internal offsets are relative to the magic**
  (0xD40), NOT +0x40. Earlier mistake: `AWG = awg0_off + 0x40` (crashed everything).

**AWG0** (magic at awg0_off): section offsets are **relative to the magic**:
```
+0x2C: vb2 (secondary buffer)     +0x30: ib (index buffer)
+0x34: sec34 (main buffer)        +0x38: restart
```

**Axes**: AWG `+0x14` = axes_loc (0xA10), `+0x18` = axis_lines (13).
Axis0 holds the main mesh (armature → mesh group). Axes 1-12 = rig bones.

### 32.2 POINTERS TO UPDATE IN A RE-LAYOUT

1. **AWG0 header**: +0x2C (if sec34 grows), +0x30 ib, +0x38 restart.
2. **AMG table**: entries 1-17 (+delta).
3. **51 axes-zone pointers** in the AWO header (≥ axes_base, +delta).
   - **CRITICAL!** Exclude the AMG table from this loop (it is at 0x690-0x6D8,
     inside the 0x34-0x700 range). The AWG16/17 offsets (≥ axes_base)
     received a 2× delta → guest null deref.
4. **AMB header**: entry0 size (AWO) + entry1 loc (AZT). Do not duplicate the header!

### 32.3 FULL-FILE MODE (rebuilt AFS) — VALIDATED ✅

- The launcher copies `mods/<mod>/us/data_cmn.afs` to the `active_region` overlay.
- Rebuilt AFS (ORIGINAL bin 327, recomputed table) **works**.
- Allows bins larger than the slot (per-entry override = limit 106496).
  (Later superseded: full AFS copies are migrated to per-entry overrides and
  the virtual mid-insert handles growth; see `AGENTS.md` §6.)

### 32.4 vb2 RE-LAYOUT RESULT (+536 slots) — BLOCKED

- The model **loads** (it crashed on selection before) ✅
- **The right hand is missing** + **crash when entering battle** ❌
- Filling the padding with valid vertices (copies) does not fix it.

**Data**: the IB uses 234 vb2 slots (indices 1956-2189) but the real vb2 = 226
(9984/44). With the re-layout vb2 grows to 762 slots.

**Hypothesis**: the runtime may use the buffer size (ib - vb2) as the
vertex count, and expects a fixed count. The right hand (indices
1956-2189) gets misaligned with the enlarged buffer.

### 32.5 NEXT STEPS

1. Instrument the runtime (recompile the SDK — no cmake in PATH).
2. Check whether the guest uses the buffer size as the vertex count.
3. Alternative: deduplicate/decimate the PS2 geometry to ≤2190 vertices to
   keep the HD buffers without a re-layout.
