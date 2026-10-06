# Phase B session — arms, census and test T2 (2026-09-10)

> Goal: close (or confirm) Route B's blocker in the PS2→B3 HD port ("the pool
> order matters" / "hidden consumer by index"). New tools, a census of domains
> and the in-game permutation test T2.

---

## 1. CONTEXT AND QUESTION

Route B (full port, PS2 topology) was blocked by two beliefs inherited from
`SESION_PORT_RE_2026-08-26 §7.1`:
1. "The guest is TIED to the pool order" (the reverse test that deformed).
2. The "arms" define IB ranges to draw (`CONSOLIDADO §13.5.13`).

And a doubt: is there a **hidden consumer** referencing the vertex pool by
index (outside the IB and the A/B descriptors)?

## 2. INSTRUMENTS (in `awo_tools/`)

| Tool | Function |
|---|---|
| `phase_b_census.py` | Parses #AMB→#AWO→AWG0; canonical header; A/B descriptors; arms; census. |
| `phase_b_consumer_scan.py` | Counts references to vertex indices OUTSIDE the IB (the whole AWG0). |
| `phase_b_make_t2.py` | Permutes 2 vertices + remaps the IB + validates offline. |
| `afs_extract_hd.py` | Extracts an entry from the HD AFS (table at offset 8). |

Working bins (extracted from `us/data_cmn.afs`, LZX→`xbdecompress`):
Krillin 327 (682528), Cell F2 147 (715872), Babidi 96 (383904).

## 3. FINDINGS

### 3.1 Canonical AWG map (verified empirically)
`+0x14` = axes (== rigging_data_ptr). Correct offsets:
`vb2=+0x2C, IB=+0x30, sec34=+0x34, end=+0x38` (sec34's +2 align).
⚠️ `docs/03_formatos/BIN_LAYOUT.md` and `AMO_AWO.md` are **WRONG** (they say
sec34=+0x30, IB=+0x38); the pipeline and `CONSOLIDADO` are correct.

### 3.2 A/B descriptor — confirmed
The IB indices in range B ALWAYS fall within range A:
Krillin 13/13, Cell 29/29, Babidi 10/10 OK.

### 3.3 Arms — "arms = IB ranges" REFUTED
Dump of each arm's targets:
- each arm is `[bone, ptr, 0, ptr_matrix, 0]`;
- `arm+12` → **float data (a 4×4 matrix, ending in `3F800000`)** and it grows
  **exactly +64 B** per bone (the 64-byte "Mesh End" block);
- `arm+4` → small arrays.
→ They are an **armature with pointers**, not draw ranges. That is why
`port_ps2_to_b3.py`, which regenerated them as ranges, **crashed** (corrupt
pointers), not because of a format limit.

### 3.4 Census: there is NO hidden consumer
Number of vertex indices referenced **only by the IB** (with no u16/u32
reference anywhere else in AWG0):

| Bin | n (sec34+vb2) | IB only |
|---|---:|---:|
| Krillin | 2182 | **1866** |
| Cell F2 | 2937 | **2356** |

Those with external references are small values (0,1,2,5,11,13…) that match
bone indices and constants; they do not form lists.

### 3.5 Test T2 in game — IDENTICAL ✅
`_t2_swap`: 2 vertices of the SAME bone/descriptor swapped + IB remapped
(validated offline: identical geometry by construction, both indices without
an external reference). **Result in game (user): it renders IDENTICAL to
normal Krillin.** ⇒ the order WITHIN a descriptor/bone is free.

The **format C of Babidi** was also confirmed: marker != FFFFFFFF, no +2
align, bone NOT at +28 (it goes at +40) → the pipeline must auto-detect
format A/C.

### 3.6 Test T3 in game — DEFORMED ❌ (but it reveals the mechanism)
`_t3_reverse`: reverse of the sec34 pool + **IB remapped** + **A/B
recomputed** (13/13, validated offline). **Result in game (user): "the
silhouette is understandable and some things stay in place, but deformed".**

⇒ The "clean reverse" (with correct invariants) **DOES** deform. The earlier
lesson "there is no binding / the reverse was an artefact" is **INCOMPLETE**:
the order matters **when vertices cross descriptors**.

### 3.7 Descriptor analysis — the key
Dump of A/B vs B's indices (Krillin/Cell):

| Fact | Evidence |
|---|---|
| The A ranges **partition the pool CONTIGUOUSLY** | Krillin: A=42→102→211→353→377→887→1080→…; each `A_start` = the previous `A_start+A_count` |
| A ≈ `[min(B), max(B+1))` | Krillin 11/13, Cell 20/29 exact |
| The pool is **NOT** contiguous per bone | 412 bone blocks (fragmented) |
| The face/hand descriptors have A in **vb2** (bones-in-A empty) | XCEL_L00_FACE, XKLL_M_DTEETH |

### 3.8 Hypothesis H3 (the one reconciling T2 vs T3)
**The guest treats each descriptor's range `A=[A_start, A_start+A_count)` as
a CONTIGUOUS pool BLOCK.** The order WITHIN the block is free (T2), but mixing
vertices between blocks breaks the partition → deformed (T3).

Probable mechanism: per descriptor, the guest dumps/skins block A and draws its
range B with **indices local to the block** (or a bone palette derived from the
block). When A is recomputed as `[minB,maxB+1)` after the reverse, one
descriptor's block ends up containing others' vertices → deformed.

### 3.9 Test T4 in game — THE SAME DEFORMITY as T3 ❌❌ (hard finding)
`_t4_inpart`: reverse the vertices **INSIDE** each A block (12 blocks, 1512
verts) + IB remapped, **A intact**. **Result (user): "exactly the same
deformities as before"** (identical to T3).

**Mathematical proof (offline)**: following the IB index by index, the vertex
records are **identical** in T2, T3 and T4:
```
IB-follow  t2: same=5125 diff=0
IB-follow  t3: same=5125 diff=0
IB-follow  t4: same=5125 diff=0
```
That is, **any consumer that resolves through the IB sees exactly the same
geometry**. A consistent relabelling of the pool + IB remap is a GEOMETRIC
IDENTITY (that is why T2 is identical). **If T3/T4 deform, the guest does NOT
resolve the geometry (only) through the IB: there is a consumption BY
POSITION.**

**Ruled out**: (a) the mod DID load (logs: `dbz3_010`=_t2_swap,
`dbz3_011`=_t3_reverse, `dbz3_012`=_t4_inpart, all `AFS OVERRIDE HIT` on entry
327 at fight time); (b) T3 and T4 are different bins (68,989 diffs between
them); (c) it is not an IB remap bug (validated by IB-follow). (d) **H3 is
insufficient**: each A block contains **2–85 bone runs** (it is not "one block
= one bone"), so "order within the block is free" is FALSE.

### 3.10 Test T5 in game — MUCH WORSE (the IB does matter) ✅
`_t5_noremap`: reverse the sec34 pool **without touching the IB**. **Result
(user): "much more deformity; one of the textures (the face?) spread over a
large part of the body".**

⇒ **T5 ≫ worse than T4** ⇒ the **IB DOES control the geometry** (remapping it
in T4 improved things). But T4 **still** deforms ⇒ there is a **second
POSITIONAL route** besides the IB. The stretched face texture = body triangles
taking vertices from the face zone (the IB points at indices whose record is
no longer the right one; in T5 sec34 contains the face, descriptor 2 bones
28-35/A=[211,353)).

### 3.11 A vs B analysis (offline)
`phase_b_ab_compare.py`: triangulation of A (as a list and as a strip) vs the
IB's range B (as a strip). Partial overlap 45–78% (not identical), the IB
barely sequential (26–89% of ±1 pairs). Not conclusive on its own.

### 3.12 Test T6 in game — NORMAL ✅ (A is NOT used for drawing)
`_t6_adesc`: pool and IB **intact**, only the **A ranges are rotated** among
the 12 sec34 descriptors. **Result (user): "it looks fine and it is the same
as always".**

⇒ **The A range does NOT determine the drawn geometry.** It is not the
positional route.

### 3.13 State of the puzzle (2026-09-10)
| Test | Change | Render |
|---|---|---|
| T2 | swap 2 records (same block) + IB remap | identical |
| T3 | reverse pool + IB remap + A/B recomputed | deformed |
| T4 | intra-A-block reverse + IB remap | deformed |
| T5 | reverse pool, IB UNTOUCHED | MUCH worse (stretched face) |
| T6 | only rotate the A ranges (pool+IB intact) | **normal** |
| IB-follow | T2/T3/T4 | same=5125 diff=0 |

**Reading**: pool intact ⇒ normal (T6). Pool changed ⇒ deformed (T4/T5), even
if the IB is consistent (T3/T4) ⇒ **the pool is consumed POSITIONALLY** (and
that route is NOT descriptor A). The IB might be auxiliary; **T5≫T4 could
have been just a worse permutation**, not proof that the IB matters.

**Decisive test T7** (`_t7_ibrev`): pool intact, **whole IB reversed**.
- Normal → the IB is **not** used for drawing ⇒ **POSITIONAL drawing** ⇒ the
  pool order is sacred ⇒ **Route B (reordering) incompatible; Route A = the
  only route**.
- Deformed → the IB is used ⇒ review the remap (T4 should have been identical).

### 3.14 Test T7 in game — MASSIVE DEFORMITY ✅ (the IB IS used)
`_t7_ibrev`: pool intact, **whole IB reversed**. **Result (user): "much more
massive, head completely deformed, only one hand looks fine, silhouette of
legs/torso present but WRONG".** Image: a mesh with triangles connecting the
wrong vertices.

⇒ **The IB DOES govern connectivity.** But then T4 (consistently remapped IB
+ reordered pool) should have been identical… and it was not.
⇒ **The pool is consumed POSITIONALLY by a structure that is NOT descriptor
A** (T6). History (`SESION_INYECCION_2026-08-26.md`): the **draw log**
(`DBZ3_DRAW`) proved the guest draws the right strips (B_start/B_count) and the
port's amorphous result came from the **SKINNING structure (arms) tied to the
pool order**. That fits EVERYTHING: T2 (intra-bone swap) OK; T4 (reordering
across bones) deformed; T6 (A) normal; T7 (IB) deformed.

### 3.15 🔴 FINDING: there are TWO descriptor tables
- **Mesh group @AWG0+~0x2D49**: 0x60 entries with label + `max N m` + A/B
  encoded `<<8` (+0x50/+0x54/+0x58/+0x5C, flag 0x01). It is the one edited in T6.
- **AWG0+0x1F80**: a SECOND table (PLAIN u32) with the SAME values:
  `42,60,74,126`… (+0x1158, +0x2C const). Probably the **runtime table** the
  guest consumes at draw time ⇒ **T6 (which only touched the 1st) had no
  effect**.
⇒ Pending: confirm which table the draw uses and whether it references the
pool by position. *(Later corrected in Phase C: +0x1F80 is the bind-pose
matrix table — see `SESION_FASE_C_CONSUMER_2026-09-10.md` §4.)*

## 4. CONCLUSIONS (revised a 5th time)

1. **The IB is used** (T7 massive) **and the pool must be in its original
   order** (T4/T5) ⇒ there is a consumption **by position**.
2. **It is not descriptor A** (T6) — it is probably the **skinning
   structure (arms)/zones** tied to the order (history: draw log + arms).
   There are **two** descriptor tables (mesh group + AWG0+0x1F80).
3. **Route B (PS2 topology) = multi-session RE**: rebuild skinning/arms +
   tables consistent with the new pool. **Route A (NPM injection, keeps the
   order) = the validated PRACTICAL port** (`cell_npm4`, threshold 0.8).

## 5. IMPLICATIONS / NEXT

- **Practical option (recommended)**: re-enable/refine `cell_npm4` (Route A).
- **Research option**: map the **arms/skinning** format (arm = `[bone, ptr,
  0, ptr_mat4x4, 0]`; +0x1F80 matrix/data) and the runtime descriptor table;
  then a new coherent pool can be emitted (real Route B).
- New instrument: `awo_tools/phase_b_arms_dump.py` (dump arms + regions 0x1E00/0x1F80).

## 6. REPRODUCE

```
python awo_tools/afs_extract_hd.py 327 147 96        # -> e*.comp
xbdecompress e327.comp e327.bin
python awo_tools/phase_b_census.py e327.bin
python awo_tools/phase_b_consumer_scan.py e327.bin
python awo_tools/phase_b_desc_detail.py e327.bin      # A/B + bones per block
python awo_tools/phase_b_deep_scan.py e327.bin        # scaled refs
python awo_tools/phase_b_ab_compare.py e327.bin       # A vs B (triangulation)
python awo_tools/phase_b_make_t2.py e327.bin e327_t2.bin
python awo_tools/phase_b_make_t3.py e327.bin e327_t3.bin
python awo_tools/phase_b_make_t4.py e327.bin e327_t4.bin
python awo_tools/phase_b_make_t5.py e327.bin e327_t5.bin
python awo_tools/phase_b_make_t6.py e327.bin e327_t6.bin
python awo_tools/phase_b_make_t7.py e327.bin e327_t7.bin
```
Pack: `xbcompress /N:2048 e327_tX.bin geom.raw` → pad to 106496 →
`out/build/win-amd64-release/mods/_tX/us/data_cmn.afs/327/geom.bin`.

**Test mods (ONE active at a time)**:
`_t2_swap` (identical), `_t3_reverse`/`_t4_inpart` (deformed), `_t5_noremap`
(much worse), `_t6_adesc` (normal → A is not used), **`_t7_ibrev` (ACTIVE,
decisive IB test)**.
⚠️ `AfsFindModOverride` serves the FIRST active mod in alphabetical order:
disable the rest (`.disabled`).
