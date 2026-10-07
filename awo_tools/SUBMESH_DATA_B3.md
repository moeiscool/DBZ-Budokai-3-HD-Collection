# B3 SUBMESH DATA — MAPPED LAYOUT (2026-08-17)

> The missing piece for the complete PS2→HD rebuild (inspired by the B1
> project's SESION11). B3 DOES have the submesh data zone and it is now mapped.

---

## 1. LOCATION

In the AWG0 of Krillin's bin (b327_hd.bin), between the labels/axes zone and
sec34:

```
0x2D49 .. 0x3459  = 19 descriptors (stride 0x60 = 96 bytes)
0x35A6            = start of sec34 (44 B/slot)
```

The body descriptors (0-11) use `XKLL_BODY` as the label + debug `max N m`.
The face descriptors (13-18) use `KLL_L00_LHAND`, `KLL_L00_RHAND`,
`XKLL_M_DTEETH`, `XKLL_M_UTEETH`, `XKLL_L00_FACE` (different layout: material).

---

## 2. LAYOUT OF THE B3 BODY DESCRIPTOR (stride 0x60, 96 bytes)

```
+00..+0F  16-byte label (XKLL_BODY, ...)
+10       u32 constant 0x09000000 (submesh count?)
+14       u32 constant 0x0F000000 (flags?)
+18..+1F  debug string "max N m" (from the developer)
+20..+3F  transform/material floats (quats, pos, scale)
+40       u32 constant 0x00115800 (geometry buffer offset)
+44       u32 constant 0x00002C00 (buffer size)
+48       u32 0x00000500 (count?)
+4C       u32 0
+50       u32 START of range A (contiguous between descriptors)
+54       u32 SIZE of range A
+58       u32 START of range B
+5C       u32 SIZE of range B
```

**DIFFERENCE vs B1**: in B1 the ranges were at `+60/+64/+68/+6C` of the
descriptor (after +0x5F of floats). In B3 the descriptor is shorter (0x60 vs
0x80+) and the ranges are at `+50/+54/+58/+5C`.

---

## 3. CONTIGUITY OF RANGE A (verified, 12/12)

| # | label | +50 (start A) | +54 (size A) | end | contiguous |
|---|-------|----------------|----------------|-----|----------|
| 0 | XKLL_BODY | 0x2A00 | 0x3C00 | 0x6600 | OK |
| 1 | XKLL_BODY | 0x6600 | 0x6D00 | 0xD300 | OK |
| 2 | XKLL_BODY | 0xD300 | 0x8E00 | 0x16100 | OK |
| 3 | XKLL_BODY | 0x16100 | 0x1800 | 0x17900 | OK |
| 4 | XKLL_BODY | 0x17900 | 0x1FE00 | 0x37700 | OK |
| 5 | XKLL_BODY | 0x37700 | 0xC200 | 0x43900 | OK |
| 6 | XKLL_BODY | 0x43900 | 0x1C00 | 0x45500 | OK |
| 7 | XKLL_BODY | 0x45500 | 0x800 | 0x45D00 | OK |
| 8 | XKLL_BODY | 0x45D00 | 0x1400 | 0x47100 | OK |
| 9 | XKLL_BODY | 0x47100 | 0xC600 | 0x53700 | OK |
| 10 | XKLL_BODY | 0x53700 | 0xC300 | 0x5FA00 | OK |
| 11 | XKLL_BODY | 0x5FA00 | 0x1800 | 0x61200 | OK |

The A ranges are **contiguous** (the end of one = the start of the next). They
cover the buffer's geometry (sec34 + IB). This is the pattern B1 described.

---

## 4. IMPLICATION FOR THE REBUILD

To port a character PS2→B3 HD:

1. Parse the PS2 #AMO0 (mesh parts, verts, rig → local coords + bones).
2. Generate sec34 (44 B, REAL layout with BONE@+28) + IB from the PS2 triangles.
3. **Regenerate the submesh descriptors** (one per mesh part):
   - the PS2 part's label
   - +50/+54 = start/size of range A of the geometry buffer (contiguous)
   - +58/+5C = start/size of range B
4. Regenerate the arms (IB ranges per bone).
5. Keep the axes, mesh-part headers and the AWG0 structure of the template
   bin (same skeleton).

**Risk (documented in B1)**: copying the submesh zone from a template over new
geometry → hang (offsets that do not match). The descriptors must be
GENERATED with the new buffers' ranges.

---

## 5. PENDING

- Map the face descriptors (13-18, material layout) and those of the
  hand/face AWGs (1-17).
- Check exactly what range A covers (sec34? IB? both?) to be able to generate
  the correct offsets.
- Adapt B1's `amo0_to_awo.py` to the B3 layout (44-byte vertex with
  BONE@+28, B3 submesh descriptor, different vb2).

---

## 6. 🔴 COMPLETE STRUCTURAL MAP OF THE B3 AWG0 (2026-08-17, verified)

### 6.1 AWG0 layout (bin b327_hd.bin, Krillin)

```
AWG0 @0xD80 (abs), magic '#AWG' at +0:
  +0x04: 0x40 (header size)
  +0x0C: 0x4 (B3 flag)
  +0x10: 0x33 = 51 bones
  +0x14: 0xA10 = axes loc (rel AWG0) -> axes @0x1790
  +0x18: 0xD = 13 mesh groups
  +0x1C: 0x40 = name offset
  +0x20: 0x6A0 = mesh group zone (rel)
  +0x24: 0xB = mesh parts count?
  +0x28: 0x2700 = sec34 rel? (the current code uses +0x34)
  +0x2C: 0x17868 = vb2 rel -> vb2 @0x185E8
  +0x30: 0x19F68 = IB rel -> IB @0x1ACE8
  +0x34: 0x2826 = sec34 rel -> sec34 @0x35A6
  +0x38: 0x1C790 = end rel -> end @0x1D510
  +0x40: 'XKLL_BODY' (16-byte root label)

Axes: 51 axes of 0x50 (80 B) @0x1790..0x2780
  +0x00..+0x0C: local quaternion [x,y,z,w]
  +0x10..+0x1C: local position [px,py,pz]
  +0x30: seal (0x9000020C mesh / 0x204 shadow / 0x6000020F root)
  +0x34: arm_ptr (rel AWG0) -> arm block
  +0x38: child_ptr | +0x3C: sibling_ptr | +0x40: parent_ptr

Arms: 51 blocks of 0x14 (20 B) @0x1A00..0x1DF0
  [bone, end, 0, start, 0] where bone=index, start/end = BYTE offsets in the IB
  Bones with mesh (start/end != 0): 0, 18, 25, 32, 35, 36
    bone 0:  [0, 8064, 0, 7680, 0] -> IB idx [3840..4032]
    bone 18: [18, 9328, 0, 7744, 0] -> IB idx [3872..4664]
    bone 25: [25, 9440, 0, 7808, 0] -> IB idx [3904..4720]
    bone 32: [32, 9552, 0, 7872, 0] -> IB idx [3936..4776]
    bone 35: [35, 9760, 0, 7936, 0] -> IB idx [3968..4880]
    bone 36: [36, 9872, 0, 8000, 0] -> IB idx [4000..4936]
  ⚠️ The arms' ranges [3840-4936] are the SHADOWS zone of the IB.
  The real IB is drawn WHOLE (5140 indices); the arms do NOT define what to
  draw (they are skinning refs/other info). AGENTS item 27.

Mesh group @0x1420 (13 groups of 0x40): headers with type2=0x29BD (B3 seal)
  - The real mesh-part header has +38=0x1B5 (type1) +3C=0x29BD (type2)
  - Pattern per bone with mesh: 5,5,1,0x1B5,0x29BD (shadow/extra blocks)
  - The other headers: 4x4 identity matrices (material)

Submesh data zone @0x2CD9..0x34D9 (19 descriptors of 0x60): see §2-3
  - Body descriptors (0-11): label XKLL_BODY, contiguous range A +50/+54
  - Face descriptors (13-18): KLL_L00_LHAND/RHAND, XKLL_M_DTEETH/UTEETH,
    XKLL_L00_FACE (different material layout)

sec34 @0x35A6: 1956 slots of 44 B (REAL layout, see AGENTS §3.2)
vb2 @0x185E8: 226 slots (head/faces, own layout, bone=0xFFFFFFFF)
IB @0x1ACE8: 5140 u16 indices (references sec34 0-1955 + vb2 1956-2181)
```

### 6.2 Key finding of the session

**vb2 covers 15.4% of the IB** (789 of 5140 indices = head/faces) with its OWN
layout (positions 0..2, not world). PS2 injection only touches sec34 →
head/legs/knee/foot CANNOT be fixed by injection. For that the complete bin,
including vb2, has to be rebuilt.

---

## 7. REFERENCES

- B1: `DBZ Budokai HD\docs\re\SESION11_PORT_PS2_METODOLOGIA.md` §3.
- B1: `DBZ Budokai HD\mod center hd\conversores\amo0_to_awo.py`.
- B3: `awo_tools\SESION_2026-08-17.md` §6.
- B3: `docs\VIABILIDAD_MODELOS_EXTERNOS.md`.
