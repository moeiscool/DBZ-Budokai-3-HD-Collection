# VIABILITY: PUTTING EXTERNAL 3D MODELS INTO DBZ BUDOKAI 3 HD

> 2026-08-17 night. A documented answer to: "is something like this viable, or
> in general putting in external 3D models?" Based on in-game feedback on the
> `krillin_ps2` mod (v7) and on the docs of the sibling project DBZ Budokai HD.

---

## 1. SHORT ANSWER

**YES it is viable, but NOT by injecting positions into slots** (that has
already reached its limit). The route validated by the B1 project is to
**REBUILD the complete bin** from PS2 (sec34 + IB + arms + submesh data
regenerated), or to use the **native swap** for characters that already exist
in HD.

---

## 2. WHAT THE krillin_ps2 MOD SHOWED (v7 with threshold 0.3)

| Result | Zones | Diagnosis |
|-----------|-------|-------------|
| ✅ Perfect | Hands, right arm, upper face | PS2/HD coords match |
| ✅ Very good | Rest of the body | Threshold 0.3 leaves the original HD |
| ❌ Fail | Ear, back of head, mouth | Face in bones 29-37 + vb2 → almost nothing rewritten |
| ❌ Fail | Right shoulder, belt | 15-38% rewritten → visible HD+PS2 mix |
| ❌ Fail | Right knee, left foot | **0 slots in sec34 → they live in vb2, NOT touchable** |

**v7 is the MAXIMUM of slot injection**: Krillin's HD is a decimated rework
with 0% vertex correspondence. Only ~197 slots (10%) have a real world
correspondence with PS2.

---

## 3. WHY INJECTION CANNOT GO FURTHER (3 causes)

1. **HD is re-topologised** (its own IB, reordered vertices). Injecting PS2
   coords over the host's IB connects triangles that do not correspond →
   deformation in the zones without an exact match.
2. **Legs/knee/foot live in vb2** (secondary buffer, ABSOLUTE positions,
   bone=0xFFFFFFFF). Injection only touches sec34. vb2 uses a different layout:
   `[pos.x, pos.y, pos.z, ...]` with z=1.0, without the +2 marker.
3. **34% of the slots (bones 36-50) have no PS2 coords** for sec34.

---

## 4. THE CORRECT ROUTE (validated in B1, transferable to B3)

### 4.1 Native swap (for characters that ALREADY exist in HD)
The runtime draws the complete #AWO/#AMB bin as it is (mesh group + IB + bones
+ UVs). It does not validate the slot. **B3 already has it: `sw_goten_nativo`
(Goten→Krillin, 100% functional)**. To add B3 characters that exist in other
slots, just install their geom+tex pair.

### 4.2 Complete rebuild (for characters WITHOUT an HD version: IW)
Based on B1's SESION11 methodology:

```
1. Extract the #AMO0 from the PS2 AFS (IW/B2/B3) + parse mesh parts/verts/rig
2. Check a 1:1 skeleton with the HD host (labels, the same labels)
3. Use the native HD bin with the SAME skeleton as the structural TEMPLATE
4. Rebuild sec34 (44 B) + IB from the PS2 triangles (FaceType)
5. Regenerate the arms (IB ranges per bone)
6. Regenerate the SUBMESH DATA ZONE (descriptors per mesh part)  ← key
7. Convert the PS2 #AMT texture → HD #AZT
8. Compress ≤106496 → mid-insert → validate in a fight
```

**The missing piece = SUBMESH DATA** (decoded in B1):
```
+00..+5F transform/material floats
+60 c08 = start of range A (contiguous between descriptors)
+64 c0C = size of range A
+68 c10 = start of range B
+6C c14 = size of range B
+70 16-byte label (X??_BODY, ??_L01_LHAND...)
+80 debug string "max N m"
```
Copying this zone from a template over new geometry → **hang**. One descriptor
per PS2 mesh part has to be GENERATED with the new buffers' ranges.

---

## 5. B3'S STATE FOR THE REBUILD

**✅ Verified in B3 (today)**:
- The sec34 vertex layout is `[0xFFFFFFFF, u, v, z, x, y, weight, BONE@+28,
  nrm.z, -nrm.y, nrm.x]` (stride 44, align +2).
- HD pose matrices == PS2 (47/47 identical) → the same world space.
- **The submesh data zone EXISTS in B3**: labels XKLL_BODY, KLL_L00_LHAND,
  KLL_L00_RHAND, XKLL_M_DTEETH, XKLL_M_UTEETH, XKLL_L00_FACE + `max N m`
  strings at 0x2D61-0x3471 of AWG0 and in each hand/face AWG.
- The PS2 parser (parse_ps2_mesh.py) reads mesh parts + rig correctly.

**⏳ Pending**:
- **Map the EXACT layout of the B3 submesh descriptor** (the c08/c0C/c10/c14
  offsets are NOT at +0x60 as in B1 — they differ). It is the only blocker to
  adapting B1's rebuild pipeline.
- Adapt `amo0_to_awo.py` (B1) to the B3 layout (BONE@+28, relative AWG
  offsets, different vb2).

---

## 6. RECOMMENDED CHARACTERS FOR THE FIRST REAL PORT

The 241 IW→B3 PS2 models already exist in
`modding resources\All Character Models from IW into AMB format\`:

| Character | Why |
|-----------|---------|
| **Pikkon** (583-586) | ⚠️ DISCARDED: PKH skeleton different from KLL (58 bones with a SKIRT) → NOT 1:1 |
| **Pan** (566-569) | Small, would easily fit in the slot |
| **Super 17** (606-609) | A moveset port already exists |

⚠️ **2026-08-17**: the character's skeleton must be 1:1 with a B3 HD host (the
same labels in the same order). Pikkon is NOT. The right search: an
alternative costume of a character that already exists in HD (as B1 used B2
Tenshinhan with a 1:1 skeleton). See `SESION_2026-08-17.md` §2.7.

Requirement: the character must NOT have an HD version in B3 (those that do →
native swap). See `docs/PERSONAJES_BINS.md`.

---

## 7. REUSABLE RESOURCES FROM THE B1 PROJECT

| Resource | Use |
|---------|-----|
| `DBZ Budokai HD\mod center hd\conversores\amo0_to_awo.py` | PS2 parser + repacking (adapt to B3) |
| `DBZ Budokai HD\mod center hd\conversores\obj_to_awg_hd.py` | Retopology with threshold + inv_rigid (already = v7) |
| `DBZ Budokai HD\mod center hd\conversores\port_b3_to_b1_v2.py` | B3↔B1 seal conversion |
| `DBZ Budokai HD\docs\re\SESION11_PORT_PS2_METODOLOGIA.md` | Complete methodology of the PS2→HD port |
| `DBZ Budokai HD\docs\re\RECONSTRUCCION_PORT_GERO_B3_B1.md` | Binary analysis of the port between games |

---

## 8. FINAL CONCLUSION

1. **For characters that already exist in HD**: native swap (done, works).
2. **For new characters (IW)**: REBUILD the complete bin from PS2, using the HD
   bin with the same skeleton as the structural template. The route is the
   same one B1 validated 100% (Gero B3→B1, Chaozu HD→TSH).
3. **Current blocker**: the layout of the B3 submesh descriptor (an afternoon
   of RE, following the B1 method). Once mapped, the first real port (IW
   Pikkon or Pan) is the definitive validation.
4. **Slot injection (krillin_ps2) is NOT the way for external models** — it is
   a "local improvement" technique for HD, already at its limit.

---

## 9. STATE OF THE REBUILD ROUTE (2026-08-17 night)

### 9.1 RE progress (all verified on the real bin)

| Piece | State |
|-------|--------|
| sec34 vertex layout | ✅ `[0xFFFFFFFF, u, v, z, x, y, weight, BONE@+28, nrm.z, -nrm.y, nrm.x]` (44 B, align+2) |
| HD==PS2 pose matrices | ✅ 47/47 identical → the same world space |
| B3 submesh data zone | ✅ **MAPPED** (see `awo_tools/SUBMESH_DATA_B3.md`): descriptor 0x60, contiguous range A at +50/+54, range B at +58/+5C |
| B3 mesh group | ✅ Partial: 13 groups, 0x40-byte headers with type2=0x29BD (B3 seal) |
| B3 arms | ⏳ Pending precise mapping (IB ranges per bone) |
| vb2 layout | ⏳ Pending: face buffer, positions 0..2, bone=0xFFFFFFFF |
| PS2 parser (verts+tris+skin) | ✅ `parse_ps2_mesh.py` (FaceType, strides) |

### 9.2 The real blocker of injection (confirmed)

The **vb2** (secondary buffer) covers **15.4% of the IB** (789 of 5140
indices) = head/faces. It has its own layout (positions 0..2, not world).
Injection only touches sec34 → head/legs/knee/foot ALWAYS stay HD. That is why
v7 looks good on the body but fails on the ear/mouth/back of the head/knee/foot.

### 9.3 The optimal route to follow (ordered)

1. **Native swap** for characters that exist in HD (B3→B3): **done**.
2. **Map B3's arms + vb2** (RE, 1-2 sessions) to complete AWG0's structural
   map. **Arm already mapped** (51 blocks of 0x14, bones with mesh:
   0/18/25/32/35/36 → IB ranges). **vb2 partial** (own layout, positions 0..2,
   bone=0xFFFFFFFF).
3. **Find a character with a 1:1 skeleton** with a B3 HD one (an alternative
   costume of an existing character, like B1's B2 Tenshinhan). Pikkon
   discarded (different PKH skeleton).
4. **Adapt B1's `amo0_to_awo.py` to B3**: B3 vertex layout + B3 submesh
   descriptor (+50/+54/+58/+5C) + relative AWG offsets + vb2.
5. **First real port** of the 1:1 character → bin from scratch with PS2
   topology + regenerated submesh → validate in a fight.
6. **Automate** for the rest.

### 9.4 Resources ready

- `awo_tools/SUBMESH_DATA_B3.md` — layout of the B3 submesh descriptor.
- `awo_tools/parse_ps2_mesh.py` — PS2 parser (verts+tris with FaceType).
- `awo_tools/mezclar_ps2_hd_v6.py` — world+threshold injection (v7, the limit).
- `DBZ Budokai HD\mod center hd\conversores\amo0_to_awo.py` — B1 pipeline to adapt.
