# HD DRAW STRUCTURE — Verified map (Babidi bin 96, format C)

> Date: 2026-08-26. Investigation of the HD bin's draw structure using the
> SIMPLEST template in the game (Babidi, bin 96: 1 AWG, 41 bones, format C) to
> close the gap of the PS2→B3 HD converter (ESTUDIO_ECOSISTEMA_MODS §4.2).

---

## 1. EXECUTIVE SUMMARY

**The HD draw structure is fully mapped and REGENERABLE.** It is not a
fundamental block (as it seemed), but a problem of regenerating the layout
CONSISTENTLY. The pieces:

| Piece | Contents | Regeneration |
|---|---|---|
| **Mesh-ref blocks** (mesh parts) | Vertex type (B5/B4) + texture/shader per part | From the PS2 mesh parts (type + tex/shader) |
| **Axes** (41×80B) | quat+pos (bind pose) + seal + arm_ptr | **Copy from the HD template** (1:1 skeleton) or from PS2 (same seals) |
| **Arms** | Per-bone data (offsets+counts → matrices/weights) | **Copy from a 1:1 template** or generate from the PS2 rig |
| **Descriptors** (0x60) | label + `max N m` + range A (vertices) + range B (IB) | **Compute** from the built buffers |
| **sec34 / vb2 / IB** | Geometry buffers | Already solved (`ps2_to_hd_geometry.py`) |

**Implication**: for a character with a **1:1** skeleton with an existing HD
bin (Babidi PS2→HD), the converter = use the HD bin as the structural template
(copy axes/arms/structure) and regenerate only geometry + descriptors +
mesh-ref blocks. **It is exactly the approach of `build_from_template.py`**
(the one that generated `janemba_from_cell`) — which is why **re-testing
`janemba_from_cell` is the cheap critical experiment**.

---

## 2. MESH GROUP LAYOUT (Babidi's AWG0)

```
AWG0 @0xAC0:  n_bones=41  axes=0x7E0  groups=7  mg_off=0x560  mg_size=0x1F20
             sec34=0x2610(1934)  ib=0x17294(4872 u16)  end=0x198A4

Mesh group (mg=0x1020, size 0x1F20):
  0x0000  header (0x80 B): floats 3D8AD927×3, 1.0×3, 0s,
          0xFFFFFFFF×2, 0x190/0x190 (counts), 0x44/0x44 ...
  0x0080  mesh-ref blocks (mesh parts) ×7, each 0x50:
            id/sub, 00 00 01 B5 (type B5) or 00 00 01 B4 (facial), 00 00 29 BD (tex)
            0x44 ×2 (vert count / byte len), matrices 1.0/0.0, 00 00 00 05 marker
          → parts: 0x80, 0xD0, 0x120, 0x170, 0x1C0, 0x210(B4), 0x260
  0x02B0..  axes (41 × 80B): axis0 @0x12A0 (seal 0x6000020F, arm 0x14B0 rel AWG)
  0x1F70    arms (per-bone data): (offset, count) → matrices/quat+pos
  0x2439    descriptors (0x60 each): label + 'max N m' + A/B ranges
```

---

## 3. SUBMESH DESCRIPTOR (0x60 bytes) — SEMANTICS CONFIRMED

Descriptor layout (first XBAB_BODY @0x2439):

```
+00  label (bone name, null-terminated)      XBAB_BODY
+0x18 "max N m" (string)                     max 12 m
+0x50 range A start (u32) >> 8   → 0x77   = 119
+0x54 range A count (u32) >> 8   → 0x09   = 9
+0x58 range B start (u32) >> 8   → 0xED   = 237
+0x5C range B count (u32) >> 8   → 0x0E   = 14
```

**A = range of VERTICES in the pool (sec34)**: [start, start+count).
**B = range of IB INDICES** (triangle strip): [start, start+count).

**Verified by correlation** (descriptor 1 XBAB_BODY): the IB in range B
[237,251) is `125,125,126,119,121,120,121,122,123,124,124,126,126,121` → the
vertex indices 119-126 fall EXACTLY within range A [119,128). ✓

**Babidi has 14 descriptors**: 9×XBAB_BODY, BAB_L00_RHAND, 2×XBAB_M_DTEETH,
XBAB_M_UTEETH, BAB_L00_LHAND.

**INERT descriptor** (the "neutralised" pattern, §13.10): A points beyond
sec34 (e.g. 4440 > 1934) and B=(x,0) → it does not draw. The mg header's A
field is 4440/44 — the same pattern.

---

## 4. MESH-REF BLOCK (mesh part, 0x50)

```
+00  id (u32) / sub (u32)
+08  00 00 01 B5   ← vertex type (B5 = skinned body, 48 B PS2)
+0C  00 00 29 BD   ← texture/shader
+10  00 00 00 44 ×2 (0x44 = 68: count/bytes)
+18..+3F  matrices (1.0/0.0)
+40  00 00 00 05   ← marker
```

Facial parts use `00 00 01 B4` (and `00 00 01 B4` ×2). The number of mesh-ref
blocks = `groups` of the AWG0 header (7 in Babidi).

---

## 5. AXES (80 B per bone) and ARMS

```
Axis (80B):
  +00..+2F  quat+pos / matrices (bind pose; 3×4 floats)
  +0x30  seal: 0x6000020F (body), 0x9000020C (sub-bone), 0x8000020C, 0x00000204 (shadow)
  +0x34  arm_ptr (rel AWG0)
  +0x38  another ptr (p38)
```
Axes verified: 41 (equal to the number of PS2 bones → the same skeleton, §12.2).

```
Arm (at the axis's arm_ptr, e.g. @0x1F70):
  (offset1, offset2) + counts (1, 2, 3...)  → point at per-bone data blocks:
  4×float matrices + quat+pos (e.g. @0x22B0, @0x23F0).
```
The arms are **per-bone skinning** data (PS2 rig style with chunks+weights),
NOT IB ranges to draw (the descriptors do that). That is why in Krillin the
"shadow ranges" were empty (§13.8): the arms do not define the draw.

---

## 6. REGENERATION FOR THE CONVERTER (PS2→B3 HD port)

Given a PS2 model (Babidi PS2 GH, 1 AMG, 41 bones, 3403 verts/2219 tris) and
the HD template (bin 96, 1 AWG, 41 bones):

1. **sec34/vb2/IB**: generate with `port_ps2_b3_geometry` (already solved).
2. **Descriptors**: after building the IB, group the indices by mesh part
   (PS2 material/bone) → per group: `A = (min_vert, count)`,
   `B = (min_idx, count)` → emit a 0x60 descriptor (bone label, `max N m`,
   A/B). **Direct computation.**
3. **Mesh-ref blocks**: per PS2 mesh part → a 0x50 block with the type (B5/B4
   by vtype) and the PS2 part's texture/shader. **Direct computation.**
4. **Axes + arms**: copy from the HD template (1:1 skeleton = the same bone
   order). If the skeleton differs, use `retarget_hd.py` or generate from the
   PS2 rig.
5. **Pack** #AMB + LZX + override (`port_ps2_b3_pack`).

**Pending verification in game**: if `janemba_from_cell` (Cell template with
48 bones + Janemba's geometry, already built and with the correct DLL)
renders, a template with the same number of bones accepts foreign geometry →
the table route is VALIDATED and the converter reduces to the mechanics above.

---

## 7. LINK WITH THE HISTORY

- The hangs of `build_awo_v2-v5` and Janemba's "deformed mass" were NOT the
  draw structure itself: they were (a) a fake IB (not FaceType), (b) the bone
  at +28 (real layout), (c) inconsistent counts/layout (sec34/vb2/IB out of
  range vs descriptors), (d) injection into ANOTHER character's template
  (Krillin) with re-topologised geometry. See ESTUDIO_ECOSISTEMA_MODS §5.
- `SUBMESH_DATA_B3.md` already documented the descriptor (0x60, A/B ranges);
  this session confirms A=vertices / B=IB by direct correlation and adds the
  layout of the mesh-ref block, the axes and the arms.

## 7. COMPLETE RE OF THE MESH GROUP (Cell F2, 2026-08-26) — what the port was missing

**AWG0 layout (Cell F2 bin 147, format A)**: mesh group at +0x640 (0x1300),
size 0x2F90. It contains, in order:

| Region | Off rel AWG0 | Size | Contents |
|---|---|---|---|
| mesh-ref blocks | 0x640 | 0x6E0 (first block 0x40 + 21×0x50) | draw parts |
| axes | 0xD20 (axes_base) | 48×0x50 | quat+pos+scale + seal 0x6000020F + **+0x34 arm_ptr, +0x38 child, +0x3C sibling, +0x40 parent** |
| zone matrix | 0x1C20 (0x28E0) | 48×0x10 | diagonal of bone indices + pointers to bboxes |
| bboxes | 0x1FE0 (0x2CA0) | 0x40 each | AABB per zone (min/max vec4) in model space |
| descriptors | 0x2209 (0x2EA9) | 0x60 each | **A/B confirmed** |

**Mesh-ref block (0x50, blocks 1+; block 0 is 0x40 without a prefix)**:
[0x44, 0x44, 0, 0][identity 0x20][0, 5, 0, 5][X, Y][0x1B5, 0x29BD].
X = part/zone index, Y = primary bone. The B4 (face) ones = [0x1B4, 0x1B4].
17 B5 blocks + ~4 B4 (pattern 0x1B5/0x1B4, texture 0x29BD).

**Descriptor (0x60)** — ENCODING CONFIRMED (verified: the IB indices in range B
fall in range A):
```
+00 label (8 chars, "XCEL_BODY")
+10 0x09 | +14 0x0F (constants)
+18 "max N m"
+24 0x34 (offset to the range?) | +28/+2C/+30 floats | +34 0x80000000
+3C 1/2/2 (varies per part)
+40 0x1158 (pool offset const) | +44 0x2C (stride 44) | +48 0x05
+50 A_start <<8 | +54 A_count <<8 | +58 B_start <<8 | +5C B_count <<8 | 0x01 (flag)
```
Check: A=[56,138) A=[138,559) A=[559,583)... B indices ALWAYS fall in A (OK).
The XCEL_BOD descriptors use MIXED bones (each part draws several bones); the
mesh-ref Y values are each part's primary bone.

**🔴🔴 CONCLUSION FOR THE PORT**: the guest DRAWS the strips correctly with any
correct IB+descriptors (proven by the draw log). The port's amorphous result
(conv2, reordered pool) comes from the NEW pool breaking the link with the
mesh-refs/zones/bboxes (the pool is tied to the structure by ORDER). Injection
(npm4) keeps the template's pool order → it works.

**Implication**: a port with the EXACT PS2 topology (new IB + reordered pool)
requires rebuilding the WHOLE draw structure (mesh-refs + zone matrix +
bboxes + descriptors) consistently with the new pool. It is a multi-session RE
project. Injection is the PRACTICAL port (PS2 geometry in the template's
structure, the template's topology).

**Zone matrix (0x28E0, 48×0x10)**: each row = a bone zone. The diagonal
carries bone indices 0-47 in a rotating pattern; the rows with pointers point
at the bboxes (0x1FE0→0x2CA0, 0x2020→0x2CE0, 0x2060→0x2D20, ...). Axis
+0x38/+0x3C/+0x40 = child/sibling/parent (tree).
