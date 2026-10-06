# PHASE C SESSION — The pool's positional consumer (2026-09-10)

> Goal: locate the route that consumes the vertex pool **by position** (Route
> B's blocker: "reordering the pool deforms even when the IB is consistent").
> Result: **mapped**. The pool is **100% partitioned into per-part ranges**
> (no overlaps), declared in the **0x60 descriptors** (field A) and in the
> **arms' part descriptors**. Instruments in `awo_tools/phase_c_*`.

---

## 0. TL;DR

- **A of the 0x60 descriptor = the pool's vertex range `(start,count)`**, not
  the IB's. The 29 "max N m" descriptors + the 7 part descriptors (arms)
  **tile the whole pool** `[0, n_pool)` with **0 overlaps** and **0 real gaps**
  (one table's gaps are covered by the other).
- **B of the descriptor = an IB range**; the IB indices are **global**
  (`min == A_start`, `max == A_start+A_count-1`: they cover all of A).
- The **arms** (`[bone, p1, 0, p2, 0]`): `p1` → **part descriptor** (name +
  vertex range at +0x38/+0x3C); `p2` → **bind-pose matrix**.
- The "2nd table @AWG0+0x1F80" is **NOT a descriptor table**: it is the
  **bind-pose matrix table** (which the `p2` point at). Corrects the earlier
  hypothesis.
- ⇒ For Route B, **pool + A + IB(B) + part descriptors** must be rebuilt; now
  we know exactly where they are.

---

## 1. METHOD (new tools)

| Tool | Function |
|---|---|
| `awo_tools/phase_c_arms_targets.py` | Dumps the arms' targets (`p1`/`p2`) and looks for `(start,count)`. |
| `awo_tools/phase_c_meshgroup.py` | Map of the mesh group + parts scan + `--region OFF LEN`. |
| `awo_tools/phase_c_descriptors.py` | Map of **all** the 0x60 descriptor tables (all AWGs) and of arms→part. |

Working bin: `e147.bin` (Cell F2, 715872 B, AWG0=0xCC0, n_pool=2937, n_ib=6302).

---

## 2. 0x60 DESCRIPTOR FORMAT (verified)

```
+0x00  char  label[]        e.g. "XCEL_BODY", "CEL_L00_LHAND", "XCEL_L00_FACE"
+0x18  char  "max N m"      tag (the census uses it to locate it)
+0x44  u32   type == 0x2C00 (the valid ones; 0x8000003F/0x80000000 = sentinels)
+0x50  u32   A_start << 8   ─┐ pool VERTEX range (start,count)
+0x54  u32   A_count << 8   ─┘
+0x58  u32   B_start << 8   ─┐ IB INDEX range
+0x5C  u32   B_count << 8   ─┘  (bit 0 = flag)
```
> ⚠️ Correction to `AGENTS §3.3`: **A is NOT `[min(B),max(B)+1)`**; A is the
> pool's vertex range `[A_start, A_start+A_count)`.

### 2.1 Coverage (Cell F2, AWG0)
- 36 "max N m" descriptors; 29 with a valid A → 2441/2937 vertices.
- That table's **6 gaps** are exactly the arms' parts:
  `[0,56)`, `[2176,2292)`, `[2399,2515)`, `[2622,2655)`, `[2680,2822)`, `[2904,2937)`.
- **Union (descriptors ∪ arms) = `[0,2937)` without overlaps.** The pool is a
  concatenation of parts.

---

## 3. THE ARMS (verified)

Only **7 bones** of AWG0 have an arm with data: **0, 23, 30, 36, 38, 40, 47**.

```
arm = [bone, p1, 0, p2, 0]
p1 -> part descriptor:
     +0x00 id        +0x38 start      +0x3C count      +0x44 data_off
     +0x10 vec4      +0x28 0x1158     +0x2C 0x2C(=44)  +0x60 "max N m"
     +0x48 char[] label
p2 -> bind-pose matrix (in the matrix table @AWG0+0x1F80)
```

| bone | part (label) | vertex range |
|---:|---|---|
| 0 | XCEL_BODY | [0,56) |
| 23 | CEL_L00_LHAND | [2176,2292) |
| 30 | CEL_L00_RHAND | [2399,2515) |
| 36 | XCEL_M_DTEETH | [2622,2655) |
| 38 | XCEL_M_UTEETH | [2680,2713) |
| 40 | XCEL_L00_FACE | [2713,2822) |
| 47 | CEL_T_TAIL6 | [2904,2948) |

⇒ **The "skinning/arms structure tied to the pool order"** (historical) is,
in reality, **the partition of the pool into part ranges**: this is the
positional consumer. The arms only provide the pointer to the part and its
matrix.

---

## 4. THE "SECOND TABLE @AWG0+0x1F80" (correction)

`AWG0+0x1F80` (abs 0x2C40 in Cell) is a **bind-pose matrix table**:
- a short header (0,0,0,0, 0x2C, 0x2D, 0x2E, 0x2F…) and then **consecutive 4×4
  matrices** (`… 3F800000`) of 64 B.
- The arms' `p2` point here (e.g. bone0 p2=0x1FE0 → matrix at 0x2CA0;
  bone23 p2=0x2020 → 0x2CE0; +0x40 B per bone… really +64 B per matrix).
⇒ It is **NOT the "runtime descriptor table"**: that was a wrong hypothesis
from Phase B. The descriptor table that does matter is the 0x60 one (of the
mesh group).

---

## 5. IMPLICATION FOR ROUTE B (full PS2→HD port)

The blocker stops being an unknown. **Empirical rule (T8)**: the pool is a
**sequence of contiguous bone runs**; the global order of parts/runs is free,
but **each bone must form a contiguous run** (and its internal order can be
permuted within the run: T2). T4/T3 deformed because they **mixed runs**
inside a block.

### 5.1 Invariant the rebuilder must satisfy
`awo_tools/awg_invariants.py` checks on a real bin:
1. the parts (A of the 0x60 descriptors + the arms' ranges) tile the pool;
2. **the vertices are grouped by bone into contiguous runs** (the per-part
   homogeneity check shows the parts are NOT the unit: Krillin 14/18 and Cell
   28/35 parts mix bones ⇒ the unit is the **runs**);
3. the IB indices of each B fall within its A.

### 5.2 Correct rebuild
1. Parse the PS2 model → surfaces per bone.
2. **Order the pool by bone runs** (all of a bone's vertices contiguous; free
   bone order).
3. Assign each descriptor/part an A range **that respects the run
   boundaries** (it may span several complete runs, but must not cut one).
4. **Rebuild the IB** (strip, not list) and rewrite B.
5. Close the descriptor's auxiliary fields (type `0x2C00`, tag `max N m`,
   vec4 `+0x10`, const `0x1158`) and the bind-pose matrices/arms from the PS2 rig.
6. LZX `/N:2048` + per-entry override (1 active mod).

### 5.3 BUGS FOUND in the current Route B pipeline (`mod center hd/ports/`)
- `port_ps2_b3_geometry.py::build_buffers`: assigns global indices by part
  order, but **with vertices shared between parts the indices are not
  contiguous**; moreover it does **NOT guarantee contiguous bone runs** (this
  is the "amorphous" failure). `A=[g_first, n_unique]` is wrong if there are
  shared ones.
- `port_ps2_b3_geometry.py`: builds the IB as a **triangle list**
  (`ib.append` per vertex), but the HD body uses a **triangle STRIP** (§3.2) →
  check the template's `prim_type`.
- `port_ps2_b3_pack.py`: keeps the template's arms/mesh-refs (requires a 1:1
  skeleton) and does not update the **arms' part descriptors**.
- `port_ps2_b3_draw.py`: merges groups and recomputes `A=[min,max]` (breaks
  contiguity). Correct: `A` = the run's/part's contiguous range.

### 5.4 Open unknown
With A tiling the pool and a global IB, a **consistent** reordering should be
a geometric identity; T8 confirms it for whole parts. The exact mechanism of
the consumer (does it assign matrices per run?) is inferred, not observed; it
does not block because the run rule is already met by construction.

---

## 6. TEST T8 — ✅ RESULT: IDENTICAL (a whole part is permutable)

**Tool**: `awo_tools/phase_c_make_t8.py <in.bin> <out.bin>` — a reusable
engine for Route B: it detects the parts (A ranges of the 0x60 descriptors +
ranges of the arms' part descriptors) and **swaps two parts of equal size**
(complete pool blocks), updating their ranges and remapping the IB. It is a
**geometric identity** (validated offline: 5125 triangles → the same records).

**Mod tested**: `mods/_t8_partswap` (entry 327 = Krillin; swaps both hands,
187 v each). The runtime sorts mods alphabetically (`afs.cpp` `std::sort`) ⇒
`_t8` wins the override.

**✅ Result (user): IDENTICAL to normal Krillin.**

### 6.1 CONCLUSION — Route B's rule

- **Moving/permuting WHOLE parts is SAFE** (identity).
- **Reversing INSIDE a block (T4) deforms**: it mixes bone *runs*.
- **T2** (swap 2 vertices of the SAME bone) was identical: within a bone run
  the order is free.
- **T7** (reversed IB) deforms: the IB governs connectivity.

⇒ **Correct model**: the pool is a sequence of **contiguous bone runs**; the
GLOBAL order of the parts/runs is free, but **each bone run must stay
contiguous and in its internal order**. That is the "positional consumer".
⇒ **Route B is now an ENGINEERING problem** (emit a coherent pool/A/B/IB from
PS2), not a mystery. T4 failed because it mixed runs; T6 (metadata A) did not
matter because A is not the draw index but the description of the run.

### 6.2 Test T9 — ✅ RESULT: DEFORMED (localised)

`awo_tools/phase_c_make_t9.py` reorders the order of the **single-bone runs
inside an A block** (keeping each run intact) + remaps the IB (geometric
identity validated). Mod `mods/_t9_runs` (entry 327 = Krillin; block
`[377,887)`, 75 runs).

**Result (user): DEFORMITY in the face/head and one arm, not severe.**

### 6.3 REVISED CONCLUSION (the run is NOT enough)

- **T8** (move whole parts) = **identity**.
- **T9** (reorder runs inside a block) = **deformed**.
- **T2** (swap 2 vertices of the SAME bone) = identity.
- **T4** (reverse inside a block) = deformed.
- **T7** (reversed IB) = deformed; **T6** (metadata A) = normal.

⇒ The vertex's `+28` **is used** (bone0 test: bones→0 collapses), but the
**intra-block order also matters**. A **position→bone table** was searched for
(`phase_c_find_bonemap.py`, u8/u16/u32) in the AWG and it does **NOT exist**.
⇒ The dependency **is not data in the bin**: it is in the **fetch/draw (GPU)**
or in the interpretation of the IB/strip at pipeline level. **It is not
observable offline.** ⇒ Route B CANNOT be rebuilt by blind engineering: **RE
of the draw at GPU level** is needed (instrument the vertex fetch / the draw
loop).

**State**: `mods/_t9_runs` withdrawn (`cell_native` is back). The solid
deliverable is still the **native HD→HD swap**; Route B stays as open
research with the next step defined (GPU instrumentation).

---

## 7. REPRODUCE

```
python awo_tools/phase_c_descriptors.py  <bin>          # all 0x60 tables
python awo_tools/phase_c_arms_targets.py <bin> 16       # arms p1/p2
python awo_tools/phase_c_meshgroup.py    <bin>          # mesh group + parts
python awo_tools/phase_c_meshgroup.py    <bin> --region 0x1F80 0x100   # matrices
```

---

## 8. STATE AND NEXT

- **Route A** (injection): unchanged (deliverable for PS2-only).
- **Route B**: **unblocked at the map level** (we know what to rebuild). Next:
  (a) close the descriptor's auxiliary fields; (b) T8 for the mechanism;
  (c) write the pool/A/IB rebuilder from the PS2 model.
- **Native HD→HD swap**: still the delivery route (perfect) for characters
  that already exist in HD.

### References
- `AGENTS.md §3.4` (Route A/B, tests T2–T7).
- `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md` (tests T2–T7, arms).
- `docs/07_ports/PLAN_PS2_B3/PLAN.md` (plan) and `04_FORMATO_RE.md`.
- `docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md` (native swap).
