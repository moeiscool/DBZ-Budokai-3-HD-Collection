# Full-port RE session — 2026-08-26

**Goal**: rebuild the HD draw structure for a reordered pool (exact PS2
topology). The user's decision: commit to the full port.

## 1. AWG0 DRAW STRUCTURE MAPPED (Cell F2, bin 147)

```
AWG0 = 0xCC0 (rel bin: 0x40 + AWG table)
mesh group at +0x640 (0x1300), mg_size 0x2F90
```

| Region | Off rel AWG0 | Contents |
|---|---|---|
| mesh-ref blocks | 0x640 | 22 draw-part blocks |
| axes | 0xD20 (axes_base) | 48×0x50: quat+pos+scale, seal 0x6000020F, +0x34 arm_ptr, +0x38 child, +0x3C sibling, +0x40 parent |
| zone matrix | 0x1C20 (0x28E0) | 48+ rows of 0x10: diagonal of bone indices + pointers to bboxes |
| bboxes | 0x1FE0 (0x2CA0) | 0x40 each: AABB min/max per zone (model-space) |
| descriptors | 0x2209 (0x2EA9) | 0x60 each: draw A/B |
| sec34 | +0x34 (0x313A+2=0x3DFC) | 2661 slots × 44 |
| vb2 | +0x2C (0x20770) | 276 slots × 44 (layout B) |
| IB | +0x30 (0x23700) | 6302 u16 BE indices |

## 2. MESH-REF BLOCKS (0x50, blocks 1+; block 0 is 0x40)

```
[0x44, 0x44, 0, 0][identity 0x20][0, 5, 0, 5][X, Y][type u16, texture u16]
```
- **X = descriptor index** (several mesh-refs per descriptor).
- **Y = the part's primary bone**.
- type: 0x1B5 (B5, body), 0x1B4 (B4, face), 0x1F5 (F5).
- The 22 blocks (X=descriptor, Y=bone):
  (0,1) (2,1) (2,7) (3,4) (3,6) (3,1) (5,6) (5,1) (8,FF) (9,6) (9,7) (9,1)
  (10,4) (11,13) (11,7) (12,4) (12,6) (12,1) (14,4) (14,7) (14,1) (8,FF)

## 3. DESCRIPTOR (0x60) — A/B ENCODING CONFIRMED

```
+00 label (8 chars, "XCEL_BODY")
+10 0x09 | +14 0x0F
+18 "max N m"
+24 0x34 | +28/+2C/+30 floats | +34 0x80000000
+3C 1/2/2 (varies)
+40 0x1158 (pool off const) | +44 0x2C (stride 44) | +48 0x05
+50 A_start <<8 | +54 A_count <<8 | +58 B_start <<8 | +5C B_count <<8 | 0x01 flag
```
**Verified**: the IB indices in range B ALWAYS fall in range A (direct
correlation). Cell F2: 22 XCEL_BOD descriptors (contiguous A 56→1551) +
hands/face/tail that live in OTHER AWGs.

## 4. 🔴🔴 FINDINGS OF THE SESSION

### 4.1 THE POOL ORDER DOES NOT MATTER (reversed-pool test)

`cell_reverse_test`: the sec34 pool is REVERSED (same positions/bones, new
order), IB remapped, A/B recomputed, mesh-ref/zones/bboxes UNTOUCHED.
**RESULT IN GAME: it renders correctly (normal Cell).**

→ The guest reads the pool through the A/B descriptors + IB, NOT through the
mesh-refs/zones/bboxes by index. The port CAN use any pool order.

*(⚠️ Later invalidated — see §7 and §7.1: this test was contaminated.)*

### 4.2 🔴 THE PORT'S BUG: DESCRIPTOR A

The port (port_ps2_b3_geometry.py) computed `A = [first_vertex, n_vertices]`
assuming contiguity. BUT the parts SHARE vertices (dedup) → each part's strip
references MUCH wider indices:
```
conv2 desc1: A=[48,60) but indices[47,107]  → 22 of 23 A descriptors wrong
```
Fix: `A = [min(B's indices), max+1)`. `cell_conv2_fixA` → 22/22 correct.
**RESULT IN GAME: NO CHANGE (it looks exactly the same)** → A was NOT the
visual bug (although the encoding was wrong).

### 4.3 THE PORT'S GEOMETRY IS CORRECT (point by point)

conv2 transformed by the world matrices (corrected parent) = the EXACT PS2 model:
```
bbox conv2: min[-9.66,-12.45,-8] max[10.66,13.5,3.57]
bbox PS2  : min[-9.66,-12.45,-8] max[ 9.66,13.5,3.57]
nearest PS2: med 0.000 p90 0.689 max 1.518  →  100% correct geometry
```

### 4.4 CONFIRMED DIFFERENCES conv2 vs template (possible causes of the amorphous result)

1. **New IB**: conv2 uses the PS2 topology's IB (6298/6302 different indices,
   4298 padding 0xFFFF). The template uses the original IB.
2. **Bones 34-47 in sec34**: conv2 has 293 slots (11%) with bones 34-47
   (face/tail) in sec34. The template uses ONLY bones 0-33 in sec34.
3. **vb2 with a DIFFERENT layout**:
   - Template (Cell F2 layout B): `[1.0, 0, 0, ?, ?, ?, nan@+20, U@+24, V@+28, normal@+32]` — WITHOUT clear positions (276 slots).
   - Port (geometry.py): `[x, y, z, 0,0,0, 0, FFFFFFFF, nx, ny, nz]` — a different layout.
4. **Decimation**: the port uses decimated geometry (1880 verts, voxel 0.05) →
   stretched triangles (p90 5.06) → "badly polygonised".

### 4.5 DISCRIMINATOR IN PROGRESS: DOES THE GUEST USE THE VERTEX'S BONE?

`cell_bone0_test`: template with ALL sec34 bones = 0 (positions intact).
- If it DEFORMS → the guest USES the vertex's bone → conv2's bones 34-47 are
  the cause → map/clamp them.
- If it stays THE SAME → the guest uses the mesh-ref/structure → the vertex's
  bone is not the cause → the amorphous result is vb2/topology/decimation.

## 5. PARTIAL CONCLUSION

The port is VERY close: correct geometry + corrected A/B + free pool order.
The amorphous result persists because of (2) bones 34-47 in sec34 and/or (3)
the vb2 layout. The bone0 test discriminates the bone hypothesis. Pending:
decide the vb2 fix (replicate layout B or keep the template's vb2 as the
injection does).

## 7. 🔴🔴🔴 TEST CONTAMINATION — cell_npm8_test WAS LEFT ACTIVE (2026-08-26)

**Critical discovery while analysing dbz3_038.log**: `cell_npm8_test`
(injection with threshold 1.4 on the head, from the previous session) **was
left active during the whole port RE session**. It was never given a
`.disabled`.

**Runtime mechanism** (`afs.cpp` `AfsListMods` + `AfsFindModOverride`): the
ACTIVE mods go first (alphabetical order) in `g_mod_dirs_cache`, and the
override serves the **FIRST mod with an entry for that slot**. With npm8 active:

| Test | Cache (alphabetical) | Mod served | Real result |
|---|---|---|---|
| cell_reverse_test | [**npm8**, reverse] | **npm8** (injection) | ❌ "practically the same" = INVALID (saw the injection) |
| cell_port_Afix_test | [**npm8**, Afix] | **npm8** (injection) | ❌ "exactly the same" = INVALID (saw the injection) |
| cell_bone0_test | [**bone0**, npm8] | **bone0** | ✅ "collapsed to the feet" = VALID |

**Consequences**:
- "The pool order does NOT matter" (reverse) — **NOT VALIDATED**.
- "The A fix changes nothing" (Afix) — **NOT VALIDATED**.
- "The guest uses the vertex's bone" (bone0) — **VALID**.

**Fix applied**: `cell_npm8_test` disabled. Only one mod active at a time.
⚠️ **LESSON**: before each test, check that ONLY the test mod is active
(`Get-ChildItem mods | Where -not .disabled`). The launcher enables/disables by
marker; a forgotten mod contaminates every test of the same slot.

**PENDING RE-VALIDATION**: `cell_reverse_test` (reversed pool) and
`cell_port_Afix_test` (port with corrected A) NOW on their own.

## 7.1 🔴🔴🔴 REAL RESULT OF THE REVERSE — THE POOL ORDER DOES MATTER (2026-08-26)

**cell_reverse_test re-tested ON ITS OWN** (npm8 disabled, it was the only one
active): **"a series of impressive deformities"**.

**CORRECTED CONCLUSION**: the claim in §4.1 ("the pool order does NOT matter")
was FALSE — it came from the contaminated test (npm8 was being served, not the
reverse). **The guest IS tied to the pool order** through the mesh-refs/zones
(a structure that references the pool by the original index). A reordered pool
(even with the same vertices/bones) deforms the render.

**Reconciliation with bone0 (valid)**:
- bone0 (bones→0): collapses → the guest USES the vertex's bone (+28) for the transform.
- reverse (reordered pool): deforms → the guest is ALSO tied to the pool order
  (mesh-ref Y per part / zones per bone in the original order).

Both are true: the transform uses the vertex's bone, BUT the draw structure
(mesh-refs/zones) references the pool by its original order. **The port with a
reordered pool requires rebuilding the WHOLE structure (mesh-refs + zone matrix
+ bboxes + descriptors) consistently with the new pool.** Injection works
because it keeps the template's pool order → a valid structure.

**State of the session (the user's decision: do not create new versions, hand
over to another session)**:
- Active mod: `cell_reverse_test` (the last one tested, DEFORMED — not a good
  play state, diagnostic only).
- `cell_npm8_test` disabled (it caused the contamination).
- The best injection result is still `cell_npm4` (binary threshold 0.8,
  "silhouette improved significantly") — re-enable it for a playable state if
  desired.
- **Pending for the next session**: (a) re-validate `cell_port_Afix_test` on
  its own (the port with corrected A — now without npm8); (b) decide whether
  the port rebuilds the complete structure (mesh-refs/zones/bboxes) or
  injection is accepted as the practical port.

## 6. TOOLS / FILES

- `%TEMP%\opencode\pool_reorder_test.py` — pool reordering test.
- `%TEMP%\opencode\cell_reverse.amb` — reversed pool (works in game).
- `%TEMP%\opencode\cell_conv2.amb` — original port (A wrong).
- `%TEMP%\opencode\cell_conv2_fixA.amb` — port with A corrected (no visual change).
- `%TEMP%\opencode\cell_bone0.amb` — bone discriminator.
- Mods: cell_reverse_test (ok), cell_port_Afix_test (no change), cell_bone0_test (ACTIVE).
