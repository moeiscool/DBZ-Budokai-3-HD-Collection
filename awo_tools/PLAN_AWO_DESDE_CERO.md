# PLAN: BUILD THE HD AWO FROM SCRATCH (add IW characters)

> Planning document (2026-08-14). Goal: add characters from Budokai Infinite
> World (Janemba, Pikkon, Pan, Super 17...) to the B3 recomp.

---

## 1. WHY THE RE-LAYOUT DID NOT WORK (executive summary)

- The B3 runtime expects `sec34_count`/`vb2_count` (derived from the AWG
  header's offsets) to be consistent with the model's whole structure.
- Enlarging a buffer of an EXISTING model (even by +1 vertex) breaks the
  guest's deserialisation → crash (null deref in a fight).
- **BUT**: the runtime accepts VARIABLE counts between different bins
  (Krillin 327: sec34=1956; Krillin 328: sec34=1791; both work).

## 2. THE VIABLE STRATEGY

**Build a COMPLETE HD AWO from scratch** with the target character's correct
counts (do not modify an existing model). A new AWO with a 100% consistent
structure should be accepted by the runtime.

**Reference data**: B1 (the sibling project) handles fight models with
sec34=3729 vertices (Tenshinhan). The AWO format supports large buffers.

## 3. FORMAT REFERENCES (mapped)

### 3.1 AWO (B3's #AMB container)
```
#AMB header (0x40): entry0=AWO (loc 0x40, size), entry1=AZT (loc, size)
#AWO header:
  +0x10: bones (51 Krillin)
  +0x18: amg_count (18)
  +0x1C: amg_table (0x690, rel AWO)
  +0x34: axes_base (axis zone at the end)
  +0x54..0x674: 51 entries of 0x20 with pointers to the axis zone
AMG table (18 entries): points at #AWG magics (rel AWO)
```

### 3.2 AWG0 (magic at awg0_off, offsets rel magic)
```
+0x10: bone_am   +0x14: axes_loc   +0x18: axis_lines
+0x2C: vb2 (secondary)  +0x30: ib (index buffer)
+0x34: sec34 (main)     +0x38: restart
+0x1C: labels (51×32B)  +0x20: sec20 (mesh parts)  +0x28: meshgroup
```

### 3.3 HD vertex (stride 44, aligned +2)
```
sec34:  [nan, VT.v, VT.u, V.z, pos.x_local, pos.y_local, weight, 0, VN.z, -VN.y, VN.x]
vb2:    [pos.x, pos.y, pos.z(1.0), 0,0,0,0, nan, VN.x, VN.y, VN.z] (different layout)
```

### 3.4 Mesh group (bone0)
```
+0x00: count (13)   +0x28: ptr to the mesh-ref block table (0x1ED8)
Each mesh-ref block (0x50): +0x18 seal, +0x1C arm, +0x20 idx, +0x28 tr
Recursive chain: dat@+0x30 → next arm+dat
```

## 4. CONSTRUCTION PLAN (Janemba's AWO)

### Phase A — Prepare Janemba's geometry (IW bin 541)
1. Extract Janemba's #AMO0 (48 bones, 17 AMGs, 4415 unique vertices).
2. Apply skinning (rig with 3056+ entries → per-bone local coords).
3. Convert the vertices to the HD layout (stride 44): sec34 for the body, vb2
   for the head/accessories (as HD does).
4. Deduplicate → N1 vertices for sec34, N2 for vb2.

### Phase B — Build the HD AWO (structure from scratch)
1. AWO header: bones=48, amg_count=17 (Janemba's AMGs), AMG table.
2. 17 AWGs, each with its structure (axes, labels, mesh group).
3. AWG0: sec34 with N1 vertices, vb2 with N2, IB with Janemba's triangles,
   restart buffer.
4. Mesh group + mesh-ref blocks + arms rebuilt for Janemba's geometry
   (grouping triangles by bone/material).
5. Axis zone (axes-array) with the header's 48 pointers.

### Phase C — Pack and validate
1. Pack the #AMB (AWO + AZT). Janemba's AZT is IW bin 542 (converted to HD
   #AZT).
2. Compress with `xbcompress /N:2048`.
3. Place it in a slot (per-entry override or full AFS).
4. Validate: Janemba loads, looks right, fights without crashing.

## 5. RISKS AND MITIGATIONS

| Risk | Mitigation |
|--------|-----------|
| The runtime rejects an AWO with very different counts | Bins 327/328 already have different counts; it will be tested incrementally |
| The rebuilt mesh-refs/arms are not accepted | Validate with a minimal AWG0 first (just the body) |
| Janemba's vertex layout differs | Use the same layout as Krillin (validated by the PS2 skin) |
| Skinning (48 vs 51 bones) | Janemba has its own skeleton; the moveset ports already map Janemba→Krillin |

## 6. IMMEDIATE NEXT STEP

Build the **minimal test AWG0**: AWO header + AWG0 + sec34 with Janemba's
skinned vertices (first 2190) + rebuilt IB, to validate that the runtime
accepts the structure before building all 17 AWGs.
