# RE of the B3 HD AWO format — towards a universal OBJ→AWG HD converter

> 2026-08-18. Reverse engineering of the Budokai 3 HD bin to build a
> universal converter that turns ANY 3D model + textures into a compatible HD
> `.bin`. End goal: a "Budokai HD .bin transformer" (the equivalent of the
> community's `OBJ to AMG v0.92`, but producing HD AWGs).
>
> **Later correction (2026-09-13 / 2026-10-03):** the "sec34" vertex layout in
> §1.5 (`FFFF@0`, `bone@28`, align +2) turned out to be wrong for these bins.
> All 17 AWGs use the **window layout** (`pos@0`, `w@12`, `bone@16`, `nrm@20`,
> `FFFFFFFF@32`, `uv@36`, stride 44) over `[ib − g(0x2C), ib)`. See `AGENTS.md`
> §3.4.10 and `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`.

---

## 1. HD BIN STRUCTURE (`#AMB` → `#AWO` + `#AZT`)

A character's HD bin (e.g. Krillin, 682528 B) is an `#AMB` container:

| Offset | Content |
|---|---|
| 0x00 | `#AMB` header (count, table) |
| 0x40 | `#AWO` (the 3D model, big-endian) |
| 0x47020 | `#AZT` (the textures, big-endian) |

### 1.1 `#AWO` header (relative to 0x40)

| Field | Offset | Krillin | Meaning |
|---|---|---|---|
| magic | +0x00 | `#AWO` | |
| bones | +0x10 | 0x33 (51) | number of bones |
| | +0x14 | 0x30 | |
| n_awg | +0x18 | 0x12 (18) | number of AWGs |
| awg_tbl | +0x1C | 0x690 | AWG offset table (rel AWO) |
| | +0x20 | 0x18 | |
| labels | +0x24 | 0x6D8 | bone labels (rel AWO) |
| bones_tbl | +0x34 | 0x42360 | bone zone table |

### 1.2 Krillin's 18 body AWGs

The bin does NOT have a single AWG — it has **18 separate AWGs**:

| AWG | Label | Role | bones | sec34 | vb2 | ib |
|---|---|---|---|---|---|---|
| AWG0 | XKLL_BODY | body | 51 | 1956 | 226 | 5140 |
| AWG1-5 | KLL_L0X_LHAND | left hand | 1 | ~120-163 | 10 | ~408-600 |
| AWG6-10 | KLL_L0X_RHAND | right hand | 1 | ~120-163 | 10 | ~408-600 |
| AWG11-17 | XKLL_*_FACE | face | 1 | ~148-164 | 14 | 510 |

> The body is AWG0 (51 bones). Hands and face are separate AWGs
> (1 bone each). A new character will need its own AWG structure.

### 1.3 `#AWG` header (relative to the `#AWG` magic)

| Field | Offset | Krillin AWG0 | Meaning |
|---|---|---|---|
| magic | +0x00 | `#AWG` | |
| n_bones | +0x10 | 0x33 (51) | |
| axes | +0x14 | 0xA10 | axes zone (rel AWG) |
| groups | +0x18 | 0x0D (13) | number of mesh groups |
| | +0x1C | 0x40 | |
| | +0x20 | 0x6A0 | mesh table? |
| | +0x24 | 0x0B | |
| | +0x28 | 0x2700 | |
| vb2_rel | +0x2C | 0x17868 | vb2 offset (rel AWG) |
| ib_rel | +0x30 | 0x19F68 | IB offset (rel AWG) |
| sec34_rel | +0x34 | 0x2826 | sec34 offset (rel AWG) |
| end_rel | +0x38 | 0x1C790 | end offset |
| | +0x3C | 0x24 | |
| labels | +0x40 | XKLL_* | bone labels (16 B each, even bones) |

### 1.4 AWG0 zones (relative to the AWG)

| Zone | Offset | Size | Content |
|---|---|---|---|
| labels | 0x40 | ~0x9D0 | labels 16 B × 51 |
| axes | 0xA10 | 51×80=0xFF0 | quat+pos+arm_ptr(+0x34) |
| mesh group | 0x1200 | 13×0x50 | mesh-ref blocks |
| (extra mesh) | 0x1610 | ~0x3F0 | more mesh blocks |
| arms | 0x1A00 | 51×0x14=0x3FC | arms [bone,end,0,start,0] |
| bone table | 0x1BF4 | ~0x208 | bone indices per part |
| descriptors | 0x1DFC | ~0x830 | 19 × 0x60 descriptors |
| sec34 | **0x2828** | 1956×44 | vertices (align +2) |
| vb2 | 0x17868 | 226×44 | static vertices |
| ib | 0x19F68 | 5140×2 | u16 indices |
| end | 0x1C790 | | |

> **⚠️ CRITICAL ALIGN +2**: the real sec34 starts at `sec34_rel + 2`
> (not at `sec34_rel`). The `FFFFFFFF` marker of the first vertex is at
> `sec34_rel+2`. The 2 bytes at `sec34_rel` are padding.

### 1.5 sec34 vertex (stride 44, big-endian, align +2)

```
+0x00  FFFFFFFF (marker)
+0x04  u (float)
+0x08  v (float)
+0x0C  z_local
+0x10  x_local
+0x14  y_local
+0x18  weight
+0x1C  BONE (u32)
+0x20  nz
+0x24  -ny
+0x28  nx
```

## 2. SUBMESH DESCRIPTORS (19 × 0x60 in AWG0)

Located between the arms and sec34 (0x1DFC..0x2826). Each 0x60 descriptor:

| Field | Offset | Meaning |
|---|---|---|
| label | +0x00 | 16 B (XKLL_BODY, ...) |
| | +0x10 | const 0x09000000 |
| | +0x14 | const 0x0F000000 |
| | +0x18 | debug "max N m" |
| | +0x20..0x3F | material/transform |
| | +0x40..0x4F | consts |
| range A start | +0x50 | (offset<<8) |
| range A size | +0x54 | (size<<8) |
| range B start | +0x58 | (offset<<8) |
| range B size | +0x5C | ((size<<8)\|1) |

**⚠️ KEY PROBLEM**: Krillin's AWG0 A ranges point to sec34 offsets
up to 4440, but the geometry of a rebuilt character with FEWER vertices
(e.g. 734 after decimation) leaves the descriptors **out of bounds (OOB)** →
the body deforms / flickers.

**A correct rebuild must regenerate the descriptors with the real ranges of the
new character's sec34/IB** (not Krillin's).

## 3. MESH-REF BLOCKS (13 × 0x50 in AWG0)

| Field | Offset | Meaning |
|---|---|---|
| scale | +0x00..0x0C | 4× float 1.0 |
| stamp | +0x10 | 0x204 shadow / 0x20C mesh |
| bones ptr | +0x14 | offset to the part's bone table |
| | +0x1C | offset (sometimes) |
| | +0x20 | offset |

## 4. ARMS (51 × 0x14 in AWG0)

```
[bone, end, 0, start, 0]   (u32 each, 20 bytes)
```
- arm 0: `[0, 8064, 0, 7680, 0]` — the body, IB range start=7680 end=8064 (bytes).
- arms 1-50: `[bone, 0, 0, 0, 0]` — bone only, no range.

## 5. THE ALIGN +2 BUG (found 2026-08-18)

Earlier scripts (`port_ps2_to_b3.py`, `mezclar_ps2_hd.py`) wrote the sec34
vertices at `sec34_rel+0`, but the real format is `sec34_rel+2`.
This misaligned the `FFFFFFFF` marker → the runtime read garbage coords
→ giant/deformed model. **Fixed to `sec34_rel+2`.**

## 6. LESSONS FROM THE IN-GAME EXPERIMENTS

| Mod | What it did | Result |
|---|---|---|
| krillin_rec_test | rebuild with regenerated desc/arms (uniform) + wrong align | CRASH |
| krillin_rec_diag | rebuild without touching desc/arms + wrong align | giant, no crash |
| krillin_rec_align | rebuild with regenerated desc/arms + align +2 | CRASH |
| krillin_align2 | rebuild without touching desc/arms + align +2 | **hands fine, body deformed OOB, no crash** |

**Conclusion**: the bin structure is accepted without a crash if the
descriptors/arms are NOT touched. The deformed body comes from OOB descriptors
(they point past the vertices of the rebuilt sec34). The hands look fine because
their AWGs (1-10) are Krillin's, untouched.

## 7. TOWARDS THE UNIVERSAL OBJ→AWG HD CONVERTER

Inspired by `OBJ to AMG v0.92` (which builds PS2 AMGs from OBJ with
templates), the HD converter must:

1. **Parse the source model** (OBJ, or convert any format to OBJ
   via Blender/FBX).
2. **Build the HD geometry**: sec34 (stride 44, align +2, layout §1.5)
   + vb2 (static) + IB (triangles).
3. **Generate the AWG structure**: header, axes (1 per bone), mesh-ref blocks
   (1 per mesh part), arms (per bone), descriptors (with the REAL ranges of the
   character's sec34/IB, not OOB).
4. **Build the `#AWO`** with N AWGs (1 per mesh group).
5. **Convert the texture** to HD `#AZT`.
6. **Pack the `#AMB`** + LZX `/N:2048` compression + install as a per-entry
   override (the virtual mid-insert allows bins of any size).

### The 3 pieces missing / in progress

1. **✅ AWG format mapped** (this document): header, zones, vertex,
   mesh blocks, arms, descriptors, align +2.
2. **❓ How to generate coherent descriptors/arms/mesh-blocks** for new
   geometry (avoid OOB and crashes). The PS2 community (OBJ to AMG,
   Budokai Toolset) generates PS2 AMGs with templates; the pattern has to be
   replicated in HD.
3. **❓ #AMT → #AZT conversion** (textures). Partially documented.

### Community tools that can guide the converter

- `mod center/OBJ to AMG v0.92/source code.zip` — builds PS2 AMG from OBJ
  (Python, binary templates: amg_header, model_part_header, triangle).
- `modding resources update 2/lean bone tutorial/Budokai Toolset/` — AMG_C,
  AMO_S, AMB_C + `b3_amg_*.bin` templates + presets.
- `mod center/B3-IW AMO Converter + Shadows/` — AMO converter.
- `github.com/SamuelDBZMAAM/Budokai-Modding-Tool` — AMG Creator + AMB Combiner.

---

## 8. 🔴 KEY FINDING OF THE 2026-08-18 SESSION: SELF-CONTAINED HD BINS

**The native HD→HD swap works** (the user managed to put Bulma and Babidi in
Krillin's slot). This proves that **the HD bin is SELF-CONTAINED**: each
character carries its skeleton, geometry, textures and complete draw
structure. The runtime accepts it in any slot.

**Comparative analysis of 3 HD bins** (Krillin 327, Bulma 110, Babidi 96):

| Character | bones | AWGs | structure |
|---|---|---|---|
| Krillin (327) | 51 | 18 | AWG0 body + 17 hand/face AWGs |
| Bulma (110) | 43 | 2 | AWG0 body + 1 separate AWG |
| Babidi (96) | 41 | 1 | a single AWG0 |

→ **The number of AWGs and bones varies per character.** There is no fixed
structure. Each HD bin is independent.

**PS2 (#AMO0) and HD (#AWO) share structure** (verified with Janemba and
Krillin): the **80 B axes are identical** (same stamps: axis 0 =
0x6000020F, sub-bones = 0x9800020C/0x9800020E/0x9000020C). The skeleton is the
same. The B3 vertex layout is correct (verified: 1956/1956 markers,
bones, weights; normals |mag|≈1).

**Diagnosis of the Janemba/Krillin failure**: both were attempted by injecting
PS2 geometry into **Krillin's template** (fixed counts, Krillin's
descriptors/arms). This ALWAYS fails with deformed polygons because the HD draw
structure (mesh parts + descriptors + arms) does not match the injected
geometry.

**✅ THE RIGHT WAY**: build Janemba's HD bin as a **SELF-CONTAINED** bin
(like Bulma/Babidi), re-laying out its PS2 #AMO0 into the HD #AWO, with its own
structure of AWGs, axes, descriptors and arms. Do NOT inject into Krillin's
template.

### The universal converter (OBJ/PS2 → self-contained HD bin)

Pipeline (analogous to SamuelDBZMAAM's `amg_c.py`, which builds PS2 AMGs from
scratch with templates):
1. **Parse the source model** (PS2 #AMO0, OBJ, or any format→OBJ).
2. **Build the HD AWGs**: header + labels + axes (reuse the PS2 ones,
   same stamps) + mesh parts + descriptors + arms + buffers
   (sec34/vb2/IB).
3. **Convert the geometry** PS2 (48 B, rig→bone) → HD (44 B skinned sec34 +
   44 B static vb2 + IB).
4. **Convert textures** #AMT→#AZT.
5. **Pack the #AMB** + LZX /N:2048 compression + per-entry override
   (the virtual mid-insert allows bins of any size).

### What is missing / in progress
1. **✅** HD format mapped (header, AWG, vertex, axes, descriptors, arms).
2. **✅** Confirmed that PS2 and HD share structure (re-layout, not a new format).
3. **❓** The **PS2 rig** (bone→vertex mapping) to assign the right bone to
   each PS2 vertex in the HD sec34. See Model-Rig Extractor + parse_ps2_mesh.
4. **❓** Generate coherent HD descriptors/arms/mesh-parts for new
   geometry (the `amg_c.py` pattern in HD).
5. **❓** Pose retargeting if the character's skeleton differs from the host's.

## 9. 🔴 HD DRAW STRUCTURE (mesh group) — ANALYSIS (2026-08-18)

The mesh group (mg_off in AWG header +0x20) contains the WHOLE HD draw
system: axes + arms + mesh parts + descriptors. Analyzed on Babidi (the
simplest case, 1 AWG, 7 mesh groups).

**Axes (rel AWG, at +0x14)**: each 80 B axis has:
- +0x30 = stamp (0x6000020F body / 0x9800020C / 0x9000020C / 0x8000020C).
- +0x34 = **arm** (ptr into the arms table).
- +0x38 = **p38** (ptr to the body mesh part / 0 if the bone has no part).

**Arms** (table at the axes' arm offsets): link each bone to its
range. Babidi axis 0 arm=0x14B0, axis 1 arm=0x14C4... (each +0x14).

**Mesh parts**: the B5/B4 headers in the mesh group (pattern `00 00 01 B5
00 00 29 BD`), each with texture/shader and offsets to its geometry.

**Descriptors**: the 0x60-byte blocks with labels + A (sec34) + B (IB) ranges,
which connect each mesh part to the vertices/indices it draws. Babidi: 15
descriptors (8 body ones with real ranges + 7 hand/face ones with `A=4440`).

**The structure is an interconnected system** (axes → arms → mesh parts →
descriptors). Rebuilding it for new geometry requires generating ALL
fields coherently. This is step 3 of the converter (in progress).

**Tool**: `awo_tools/analyze_meshgroup.py` — breaks down the mesh group
of an HD AWG (axes/arms/mesh parts).

## 10. 🔴 SELF-CONTAINED BIN CRASH — REAL MESH GROUP STRUCTURE

**The self-contained Janemba bin CRASHED on load** (2026-08-18). The
`janemba_autocontenido` mod was disabled (the game worked again). Cause:
**the HD mesh group is a CONTAINER that holds axes + arms + mesh-ref blocks
+ descriptors ALL together** (the axes are INSIDE the mesh group, not outside).
My bin put them outside and used a minimal descriptor → the runtime rejected the
structure.

**Babidi's mesh group map** (rel AWG, the simplest, 1 AWG):

| Zone | Offset (rel AWG) | Size | Content |
|---|---|---|---|
| mesh-ref blocks | 0x560 | ~0x280 | draw structure (mesh parts with textures/shader) |
| axes | 0x7E0 | 41×80=0xCD0 | skeleton (quat+pos+stamp+arm_ptr) |
| arms | 0x14B0 | ~0x4C9 | IB ranges per bone |
| descriptors | 0x1979 | 15×0x60 | label + stride 44 + A(sec34)/B(IB) ranges |
| (padding) | 0x2499 | | up to sec34 |
| sec34 | 0x2610 | | vertices |

**Implication for the converter**: rebuilding the self-contained bin requires
building the COMPLETE mesh group (not a minimal descriptor): mesh-ref blocks +
axes (inside) + arms + descriptors. The axes must point (arm_ptr) to valid
arms, and the descriptors to sec34/IB ranges.

**PENDING (refined step 3)**: replicate Babidi's mesh group structure as a
template, with the JNB axes (48 bones) and Janemba's descriptors/arms. The
number of bones differs (48 vs 41) → the axes/arms must be re-laid out.

> Note: the Janemba (IW→B3) port was later abandoned as a documented failure
> (see `AGENTS.md` §3.1). Model swaps and ports are PC-side tooling; the PS5
> build (`ps5/`, `docs/PS5.md`) consumes the same per-entry mod overrides but
> has no tooling of its own.
