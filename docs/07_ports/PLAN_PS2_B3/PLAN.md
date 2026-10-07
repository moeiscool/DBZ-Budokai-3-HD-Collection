# PLAN — Porting PS2 models → Budokai 3 HD Collection (360)

> **Date**: 2026-09-10. **Origin**: consolidation of 4 subagent reports
> (`01_WEB.md`, `02_MODS_INVENTARIO.md`, `03_DOCS.md`, `04_FORMATO_RE.md`).
> **Test case**: Cell (Semi-Perfect), HD template bin 147 → slot 327.
> **Goal**: decide and order how to improve the port and, if appropriate,
> unblock Path B. This document does NOT carry out changes; it defines the
> roadmap.

---

## 0. EXECUTIVE SUMMARY AND DECISION

There are **two separate problems** that the documentation mixed up:

- **Problem A — injection coverage (low risk, ALREADY specified).**
  Path A only touches the AWG0's `sec34` (body). It leaves intact **16
  single-bone AWGs** that are NOT just face: they are **10 hands + 6 face**
  (bones 48-63). The RE report (`04`) has solved their **vertex layout (6
  families), their space (`world[23]/[30]/[32]`) and the PS2→HD mapping**, and
  shows that the HD geometry is already **<0.1 u** from the PS2 surface. ⇒
  **Extending the same NPM to those 16 AWGs is low risk and of high immediate
  value.**

- **Problem B — the Path B blocker (high risk, research).**
  The pool is consumed **positionally** by a path that is neither descriptor A
  (T6) nor only the IB (T7). The strongest external hypothesis is NVIDIA's
  **"Vertex Offset Method"** (vertices in bone space, positional offsets per
  primitive) and the **2nd descriptor table `AWG0+0x1F80`**. It requires RE of
  the draw loop.

**Proposed decision**: carry out **A now** (Phase 1), instrument **B** in
parallel with a *time-box* (Phase 2), and **decision gates** so as not to get
stuck (Phase 3). Before touching anything, resolve the **documentary
contradictions** (§2).

> ⚠️ **Strategic note**: for Cell (which already has a native HD model), the
> "native HD→HD swap" gives a perfect result without a port. The PS2 port is
> **technology research**, not the optimal way to leave Cell playable. Keep
> both goals separate.

---

## 1. CONSOLIDATED FACTS (with source)

### 1.1 HD model structure
| Fact | Value | Source |
|---|---|---|
| AWGs per bin | Cell F2: 17 = AWG0 (48 bones, 2661 v) + 16 single-bone (48-63) | 03/04 |
| The 16 auxiliaries | **10 hands + 6 face** (corrects the belief "16 face") | 04 §0 |
| AWG header | `+0x14 axes, +0x2C vb2, +0x30 IB, +0x34 sec34 (align+2), +0x38 end` | 03 §2.1 |
| sec34 formats | A (marker+0, bone+28, normal `[nz,-ny,nx]`) and C (marker+12, bone+40) | 03 §2.2/2.3 |
| vb2 | own layout, **absolute positions / no skin**; face and legs in some bins | 03 §2.4 |
| Face AWG (nb=1) | buffer fixed at `h+0x1F0`; IB = triangle list | 03 §2.5 |
| 6 layout families (16 AWGs) | marker/weight/pad/normal/uv/pos offsets per family | 04 §3 |
| Space of the 16 | `world[23]` (left hand), `world[30]` (right), `world[32]` (face) | 04 §4 |
| HD geometry vs PS2 surface | **mean distance <0.1 u** in the 16 AWGs | 04 §0.4 |
| Axes: parent | **relative offset** to the AWG/AMG, not an index | 03 §3.4 |

(⚠️ Later corrections: the "6 families" were wrong — all AWGs use the same
window layout; see `SESION_DRAW_SEMANTICS_2026-09-11.md` §20.1.)

### 1.2 Drawing / skinning / blocker
| Fact | Value | Source |
|---|---|---|
| Two descriptor tables | mesh group `~0x2D49` (0x60) + **`AWG0+0x1F80`** (flat u32, runtime) | 03 §3.3 |
| A/B descriptor | A=vertices, B=indices; B⊂A; A partitions contiguously | 03 §3.3 |
| The IB DOES rule | T7 (inverted IB) → massive | 03 §4.1 |
| Range A is NOT used | T6 (rotate A) → normal | 03 §4.1 |
| Positional consumption | T4/T5 deform with a consistent IB; IB-follow `same=5125 diff=0` | 03 §4.1 |
| Arms | `[bone, ptr, 0, ptr_mat4x4, 0]`, armature +64 B/bone | 03 §3.1 |
| T7/T6/T4/T5, bone0 | see table | 03 §4.1/4.2 |
| External hypothesis | NVIDIA **Vertex Offset Method** (4 offsets/vertex in bone space) | 01 §0.2/2.3 |
| Equivalent PS3 port | `gnome41/dbz-budokai-hd` (EDGE/SPU, #A3T) → pipeline mirror | 01 §1.2 |

### 1.3 Face — where it is drawn (to resolve, §2.1)
- AWG0 has **its own** face/hair/teeth **descriptors** (`X*_L00_S00_FACE`,
  `HAIR`, `DTEETH`, `UTEETH`) → 02 §0.3.
- The **6 single-bone AWGs** (58-63) are the detailed face → 04 §6.
- The **facial descriptors have A in `vb2`** → 03 §3.3.
⇒ The face may be spread over THREE places. It must be surveyed (§2.1).

### 1.4 Ecosystem / tools
- **There is no public PS2↔HD converter** (neither wiki nor Noesis) → 01
  §0.1/2.1.
- Best PS2 tool: `SamuelDBZMAAM/Budokai-Modding-Tool` (face AMG, AMO0) → 01
  §1.3.
- **In-place** head swap WORKS (z-fighting); neutralising descriptors leaves
  holes → 02 §2.2/03 §5.4.
- Retargeting: Blender Shrinkwrap + Data Transfer; R3DS Wrap; Houdini Topo
  Transfer → 01 §4.
- AFS/LZX/mid-insert/1-mod-per-test constraints → 03 §6.

---

## 2. CONTRADICTIONS AND UNKNOWNS TO RESOLVE (before coding)

1. **Where exactly does the face live?** (AWG0 descriptors vs 6 AWGs 48-63 vs
   vb2). *Action*: survey of the AWG0's descriptors + material/`#AZT` per mesh
   group.
2. **If the HD is already <0.1 u from the PS2 surface (04), how much does the
   injection really change in the 16 AWGs?** If the change is marginal, the
   face's visual "before/after" may be minimal → adjust expectations.
3. **The sheets' "stretching"**: is it triangle stretch (guard) or legitimate
   HD geometry? Confirm with a reliable render (see §4.0).
4. **Reliable render**: our own render does not use the real matrices (arms),
   that is why it comes out amorphous. A correct viewer is needed to iterate
   without opening the game.
5. **`sec34` only bones 0-35 / legs in vb2** (03 §5.2) vs `04` (16 AWGs with
   their own geometry) — reconcile the real distribution of pieces.

---

## 3. PLAN BY PHASES

### PHASE 0 — Stop and documentation ✅ (this session)
- [x] 4 subagent reports (`01..04`).
- [x] This plan (`PLAN.md`).
- [ ] Reconcile §2.1 (face survey) and fix the "piece map".

### PHASE 1 — Path A extended to the 16 AWGs (hands + face) — LOW RISK
**Goal**: PS2-ify hands and face with the same validated scheme, without
touching sizes or topology.
- T1.1 Implement `port_ps2_b3_inject_aux.py` per the `04 §7` spec:
  - per AWG: locate the layout (family), the parent's `world` (23/30/32), the
    PS2 region.
  - nearest-point-on-surface + bone-local conversion; threshold face 0.8 /
    hands 1.0.
  - **do not touch** weight/pad/marker/uv/IB/descriptors/arms.
- T1.2 Validate offline: recompute the mean distance to the surface (must be
  ≈0) and export OBJ (`awg_cara_export.py`) checking bounds/NaN.
- T1.3 Pack `cell_best2` (LZX `/N:2048`, exact pad) and test **ONLY ONE mod**.
- T1.4 Tune per family/per AWG according to the result; consider "projecting
  only along the tangent" for the 6 face layers (avoid skin/eyes/mouth
  overlap).

**Gate G1**: if `cell_best2` improves face/hands → consolidate as the Path A
delivery. If it gets worse → revert to `cell_best` and document.

### PHASE 2 — RE of the positional consumption (Path B) — RESEARCH (time-box)
**✅ LOCATED + LIMIT (Phase C, 2026-09-10)**: the pool is partitioned by **part
ranges** (A of the 0x60 descriptors + arms); `AWG0+0x1F80` was the
**bind-pose matrix** table. In-game tests: **T8** (moving whole parts) =
IDENTICAL; **T9** (reordering single-bone runs inside a block) = **DEFORMED**.
There is no position→bone table in the bin and `+28` IS used ⇒ the dependency
is in the **draw/vertex fetch (GPU)**, not observable offline.
⇒ **Path B requires RE of the draw at GPU level** (instrument the vertex fetch
/ the draw loop in `rexgpu`/`generated`). Detail:
`docs/07_ports/SESION_FASE_C_CONSUMER_2026-09-10.md`.
**2026-09-11 — GPU RE started**: draw instrumented (`command_processor.cpp`) →
capture of 318 draws **all indexed**, **derived vec4** vertex buffer, global
indices (max 8490). Next: log the `vfetch` (offset/stride/format). See
`docs/07_ports/SESION_GPU_DRAW_2026-09-11.md`.
**Remaining goal**: GPU instrumentation; then a pool/A/B/IB rebuilder.
- T2.1 ✅ Descriptor survey (A = vertices, B = IB):
  `awo_tools/phase_c_descriptors.py`.
- T2.2 ✅ Tests T8/T9 (`awo_tools/phase_c_make_t8.py`, `phase_c_make_t9.py`).
- T2.2 Apply the **Vertex Offset hypothesis** (01 §2.3): look for arrays of
  offsets per bone/primitive pointing to `sec34+k*44` near arms/mesh-ref.
- T2.3 Instrument the **draw loop** in `generated/dbz3_recomp.*.cpp` (look for
  accesses to `sec34`, the IB and the `0x1F80` table).
- T2.4 New tests **T8/T9** (1 active mod): touch ONLY the 2nd table (rotate
  A/B) and see whether the render changes; and touch the per-bone offsets.
- T2.5 PS3 mirror: compare the layout of `gnome41/dbz-budokai-hd` vs 360.

**Gate G2 (time-box)**: if the consumer is identified → design a regenerator
(real Path B). If not → close Path B as "not viable in the short term".

### PHASE 3 — Alternatives / strategic decision (if G2 fails)
Ordered by cost/benefit:
- **A3.1 Native HD→HD swap** (for characters with an HD model): perfect,
  already validated. It is the right option for Cell if the goal is
  "playable".
- **A3.2 Retarget by bake** (01 §4): Blender Shrinkwrap + Data Transfer to
  *bake* the PS2 shape onto the **HD topology** (keeps the pool order) → turns
  "reordering the pool" into "moving vertices" (what the guest accepts).
- **A3.3 In-place transplant** (02 §2.2, validated): copy face/hand buffers
  between HD bins without moving offsets, + neutralise the AWG0's descriptors.
- **A3.4 Close the case** and archive it (like Janemba/Pikkon) if nothing
  convinces.

### PHASE 4 — Verification, packaging and documentation
- V4.1 In-game verification with **a single active mod** (anti-contamination
  rule).
- V4.2 `tools/make_release.ps1` / `verify_release.ps1` if it is published.
- V4.3 Update `AGENTS.md §3.4/§10` and `docs/07_ports/` with results and
  corrections to the outdated docs (`BIN_LAYOUT.md`, `AMO_AWO.md`,
  `AWO_FORMAT.md` `/N:32`).

---

## 4. CROSS-CUTTING TASKS (enablers)

### 4.0 RELIABLE VIEWER (priority)
The current render does not use the real matrices (arms) → amorphous. Without a
correct viewer it is not possible to iterate offline. Options:
- (a) RE of the arms' matrices and apply them in our own render;
- (b) export OBJ per bone (`Tutorial12.rtf` style: bone at scale 0 and export)
  and compose;
- (c) use Blender/Noesis with the OBJ + skeletons to preview.
**Without this, each iteration costs a gaming session.**

### 4.1 Piece and material map
Survey of descriptors (AWG0 and `0x1F80`) + material index → `#AZT` block, to
know which mesh corresponds to eyes/mouth/teeth and which texture it uses.

### 4.2 PS2 tools to cannibalise
`SamuelDBZMAAM/Budokai-Modding-Tool` (`amo_s.py`, `amg_c.py`, "Removing face
AMGs") as a map of the PS2 face structure (bones 33-41).

### 4.3 Ask on ResHax
Publish the vertex layout already deduced (#AWO/#AWG) on
`https://reshax.com/` to validate it with third parties.

---

## 5. RISKS

| Risk | Mitigation |
|---|---|
| The 6 face AWGs share a bbox/centroid → blind projection overlaps layers | Project only along the tangent / keep the local component / use the material to separate |
| PS2 teeth (b36/b38) without a dedicated HD AWG | Locate them in vb2/AWG0 or treat them separately |
| Path B without a located consumer | Time-box + Gate G2 + Phase 3 alternatives |
| Test contamination | ONE active mod per test; check `.disabled` |
| Budget/crash due to counts | use counts ≤ template; LZX `/N:2048`; exact pad |
| Outdated docs lead to errors | Fix `BIN_LAYOUT.md`/`AMO_AWO.md`/`AWO_FORMAT.md` |

---

## 6. SUCCESS CRITERIA

1. **Phase 1**: `cell_best2` with PS2 hands and face without new artefacts;
   visible improvement vs `cell_best`.
2. **Phase 2**: ✅ SOLVED 2026-09-11 — there is NO positional GPU consumer: the
   buffer is a verbatim copy of the pool and the IB is the file's; the T4/T9
   deformation was a tool index-base bug (T10 = identical geometry). Pending: UV
   skew (+1). Evidence: `SESION_GPU_DRAW_2026-09-11.md` §6-7.
3. A reliable **offline viewer** (reduces iterations).
4. **Documentation** corrected and a traceable plan.

---

## 7. RECOMMENDED EXECUTION ORDER (next session)

1. §4.0 **reliable viewer** (unblocks fast iteration).
2. §2.1 **face/materials survey** (resolves the contradiction).
3. **Phase 1** T1.1-T1.4 (`cell_best2`).
4. **Phase 2** T2.1-T2.2 (`0x1F80` table + Vertex Offset hypothesis) in
   parallel.
5. Gate G2 → Phase 3 if appropriate.

---

### Appendix — source reports
`01_WEB.md` (ecosystem, no converter exists, Vertex Offset, retargeting) ·
`02_MODS_INVENTARIO.md` (tools, head swap, holes) ·
`03_DOCS.md` (Paths A/B, formats, tests, constraints) ·
`04_FORMATO_RE.md` (layout and mapping of the 16 AWGs, implementation spec).

---

## 8. PHASE 1 RESULT (2026-09-10) AND KEY FINDING

Implemented `mod center hd/ports/port_ps2_b3_inject_aux.py` (spec `04 §7`): it
injects the 16 auxiliary AWGs (10 hands + 6 face). **3079/3085 vertices,
distances →0, no NaN** (mods `cell_best2`, `cell_face_only`).

**In-game result: practically no change.** Expected, and the data explain it:

| Part | Distance HD geometry ↔ PS2 surface |
|---|---|
| **Body (AWG0, 48 bones)** | **mean 0.69 · max 5.31** |
| Hands/face (16 single-bone AWGs) | mean 0.01‑0.21 |

**Conclusions**:
1. The **HD body was re‑modelled** (it does not match the PS2). The **AWG0 is
   the only part where the injection adds something… and it is exactly where it
   deforms** (it moves vertices 0.7 on average, up to 5.3 → flat sheets /
   hybrid).
2. HD hands and face **already are the PS2 model** → extending Path A there is
   a no‑op.
3. ⇒ For a character **with an HD model** (Cell, Krillin, etc.), Path A is a
   **step back** compared with the **native HD→HD swap** (perfect result).
4. Path A only makes sense for characters **without an HD model** (candidates:
   Janemba-like, caped Tien, or PS2‑only models) — and only if the PS2 body
   fits better than the HD of the chosen template.

**Gate G1 (revised)**: the "Cell PS2→HD" delivery is closed as a **technical
demonstration** of Path A; to leave Cell playable, use `cell_hd_only` (native).
See the comparison mod `mods/cell_hd_only` (bin 147 as is).

**Reframing of the plan**: prioritise (a) the **native swap** as the delivery
path, (b) Path A only for PS2‑only, (c) Phase 2 (Path B RE) as research.

**CLOSURE (2026-09-10)**: the **native HD→HD swap** (Cell Form 2 → Krillin) was
validated in game as **100% working** (mouth included) with
`mod center hd/swap_b3.py --origen 147 --dest 327`. Detail:
`docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md`.

⇒ **Answer to "is PS2→B3 HD ready?"**: **NO**. What is ready is **HD→HD
(native swap)**. PS2→HD (converting a model that does not exist in HD) is still
open: Path A deforms (HD body re‑modelled, dist. 0.69/5.31) and Path B is
blocked. Porting effort PS2→HD only makes sense for **characters that do not
exist in HD**. (Since v1.4.0 the launcher's importer brings B1/B2/IW
characters into new select cells; see `README.md`.)
