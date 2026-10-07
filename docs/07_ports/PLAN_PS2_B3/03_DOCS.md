# 03 — Consolidated internal documentation: PS2 → B3 HD port

> Documentary analysis report. It extracts from the internal documentation ALL
> the facts, formats, attempts and lessons about the PS2→HD model port of DBZ
> Budokai 3 HD Collection. It generates no bins or code; it only consolidates
> the scattered evidence and cites source/section.
>
> **Report date**: 2026-09-10.
> **Scope**: Path A (injection), Path B (full port), vertex format,
> arms/skinning, descriptors, face/bones 48-63, tests and constraints.
>
> (Later corrections: the "positional consumption" of §1.3 turned out to be a
> tool index-base bug; all AWGs use one window layout; B3 HD skins on the CPU.
> See `SESION_GPU_DRAW_2026-09-11.md` and `SESION_DRAW_SEMANTICS_2026-09-11.md`.)

---

## 1. STATE OF PATHS A and B — THE EXACT REASON FOR THE BLOCKER

### 1.1 State table (verified in game)

| Path | State | Best result | Source |
|---|---|---|---|
| Native B3→B3 swap | ✅ WORKS | `sw_goten_nativo`, `sw_vegeta424` | AGENTS §3.4.1; HISTORICO §3.4.1 |
| **Path A — Injection** (template + PS2 positions) | ✅ WORKS (recognisable) | `cell_npm4` (binary threshold 0.8); refined `cell_npm_fix`; `cell_best` | AGENTS §3.4.1/§10; SESION_INYECCION §5 |
| **Path B — Full port** (PS2 topology) | ⛔ BLOCKED (deformed) | — | AGENTS §3.4.3; SESION_FASE_B §4 |
| HD→HD head swap | ◑ PARTIAL / paused | `goku_armadura` v3 | HISTORICO §13.9/§13.10; AGENTS §3.4.1 |

### 1.2 What each path is

- **Path A — INJECTION** (`mod center hd/ports/port_ps2_b3_inject.py`): the
  COMPLETE, intact HD template is taken (pool, IB, descriptors, arms, axes) and
  ONLY the positions `+12/+16/+20` (and normals `+32/+36/+40`) of the `sec34`
  slots are rewritten with the PS2 geometry converted to **bone-local**.
  (`SESION_INYECCION_2026-08-26.md` §1.2; AGENTS §3.4.3.)
- **Path B — FULL PORT** (pipeline `port_ps2_b3_extract → geometry → draw →
  pack → verify`): rebuilds the `sec34` pool, the IB and the A/B descriptors
  with the PS2 topology. (`HOJA_DE_RUTA_PORT_PS2_B3.md` §1/§2;
  `ESTRUCTURA_DIBUJO_HD.md` §6.)

### 1.3 THE EXACT REASON FOR THE BLOCKER (Phase B synthesis, 2026-09-10)

The blocker is NOT that the IB is unused, nor that the geometry is wrong. It is
that **the vertex pool is consumed POSITIONALLY by a structure that is NOT
descriptor A**. Chain of evidence:

1. **The IB DOES govern connectivity**: test **T7** (`_t7_ibrev`, pool intact,
   whole IB inverted) → **massive deformity** ("head completely deformed").
   (`SESION_FASE_B_ARMS_2026-09-10.md` §3.14.)
2. **The pool order is sacred**: tests **T3** (reverse + IB remapped) and
   **T4** (reverse inside A block + IB remapped, A intact) → **deformed** ("the
   exact same deformities"). **T5** (reverse of the pool WITHOUT touching the
   IB) → **much worse** (face spread over the body).
   (`SESION_FASE_B_ARMS_2026-09-10.md` §3.6/§3.9/§3.10.)
3. **Hard proof that the IB is not enough**: following the IB index by index,
   the vertex records are **IDENTICAL** in T2, T3 and T4 (`IB-follow t2/t3/t4:
   same=5125 diff=0`). A consistent relabelling of the pool + IB remap is a
   **geometric identity** → any consumer resolving ONLY through the IB would see
   the same geometry. If T3/T4 deform ⇒ **there is consumption BY POSITION**.
   (§3.9.)
4. **That positional consumption is NOT descriptor A**: test **T6**
   (`_t6_adesc`, pool and IB intact, only the A ranges ROTATED between
   descriptors) → **NORMAL** ("it looks fine and is the same as always"). ⇒
   **range A does NOT determine the drawn geometry**. (§3.12.)
5. **H3 ("each A block = a unit") is INSUFFICIENT**: each A block contains
   **2–85 bone runs** (the A blocks partition the pool contiguously, for real,
   but they are not "one bone each"). So "free order inside the block" is
   FALSE. (§3.9/§3.8.)
6. **Main suspect (historical)**: the **skinning (arms)/zone structure tied to
   the pool order**. The `DBZ3_DRAW` log proved that the guest draws the correct
   strips (`B_start×2`, `B_count+2` with +2 of degenerate padding) and the
   port's amorphousness came from **skinning (arms) tied to the order**.
   (`SESION_INYECCION_2026-08-26.md` §1.1; `SESION_FASE_B §3.14`.)

**Operational conclusion**: Path B requires rebuilding the WHOLE drawing system
consistently with the new pool (mesh-ref + zone matrix + bboxes + descriptors +
**arms/skinning**), not just the IB and A/B. `HOJA_DE_RUTA_PORT_PS2_B3.md`
§5.1; `ESTRUCTURA_DIBUJO_HD.md` §7 (port conclusion); AGENTS §3.4.2.3.

### 1.4 Corrections to previous beliefs

- **"The pool order does NOT matter"** (`SESION_PORT_RE §4.1`) was **FALSE**: it
  came from a CONTAMINATED test (an active `cell_npm8_test` served the
  injection, not the reverse). Re-tested on its own (`§7.1`) → "a series of
  impressive deformities". It coexists with: the transform uses the vertex's
  bone (`+28`), BUT the structure references the pool by its original order.
  (`SESION_PORT_RE §4.1` vs `§7.1`; HISTORICO §3.4.2.3.)
- **"The structure is tied to mesh-ref/zones"** → nuanced by Phase B: it is not
  descriptor A (T6), probably **arms/skinning** (Phase B §4).
- **The port's "wrong A"** (`A = [first_vertex, n]` assuming contiguity) was
  corrected to `A = [min(B), max(B)+1)`. The `cell_port_Afix_test` fix gave "NO
  VISUAL CHANGE" (but contaminated; pending re-validation on its own).
  (`SESION_PORT_RE §4.2`; `HOJA_DE_RUTA_PORT §5.2`.)

---

## 2. VERTEX FORMAT OF THE AWGs (variants A/B/C and the "face AWG")

> ⚠️ **DOCUMENTED DISCREPANCY**: `docs/03_formatos/BIN_LAYOUT.md` §3 and
> `AMO_AWO.md` §4 are **WRONG** (they swap `sec34`/`vb2` and say
> `sec34=+0x30`, `IB=+0x38`). The correct offsets are **`vb2=+0x2C, IB=+0x30,
> sec34=+0x34, end=+0x38`** (verified empirically). Source: `SESION_FASE_B
> §3.1`; `AWO_FORMAT.md` §4.6/§5 also carries the old layout.

### 2.1 AWG header map (canonical, verified)

```
+0x10 n_bones   +0x14 axes (== rigging_data_ptr)
+0x2C vb2       +0x30 IB        +0x34 sec34      +0x38 end
```
(`SESION_FASE_B §3.1`; `RE_AWO_HD_CONVERSOR.md` §1.3; `CONSOLIDADO.md`
§13.5.1.)

### 2.2 Format A — "standard" sec34 (Cell F2, Krillin; stride 44, align +2)

```
+0  0xFFFFFFFF (nan marker)
+4  u            +8  v
+12 z_local      +16 x_local      +20 y_local
+24 weight (0.1-1.0)               +28 BONE (u32, 0-35 in the template)
+32 nrm.z        +36 nrm.y negated +40 nrm.x
```
Verified: 36 unique bones 0-35, normals |mag|≈1, weight 0.1-1.0, FFFF at +0.
**The bone is at +28, NOT at +0x10** (the old tools wrote at +4/+16 → deformed
mass). (`AGENTS §3.2`; `CONSOLIDADO §13.5.16`; HISTORICO §65.1e.)

- **CRITICAL ALIGN +2**: the real `sec34` starts at `sec34_rel + 2`; the first
  vertex's marker is at `sec34_rel+2`; the 2 previous bytes are padding.
  (`RE_AWO_HD_CONVERSOR.md` §1.4/§5.)
- The descriptor's `+0x2C`/`+0x34` is the buffer's **SIZE in bytes** (not an
  offset): number of vertices = size/44. (`AGENTS §3.2`.)

### 2.3 Format C — most bins (Goku 264, Vegeta 424, Babidi, Goten; stride 44 WITHOUT align)

```
+0  x | +4  y | +8  z (bone-local, [-1,1])
+12 0xFFFFFFFF
+16 u | +20 v | +24 n.x | +28 n.y | +32 n.z | +36 weight | +40 BONE
```
**In format C the bone is NOT at +28, it is at +40.** The marker/flag is NOT
necessarily FFFFFFFF and **there is no +2 align**. The pipeline MUST
auto-detect format A vs C. (`AGENTS §3.2`; `SESION_FASE_B §3.5`;
`DICTAMEN_GPT6 §0.1`; HISTORICO §13.8/`sw_vegeta424` validated in game.)

### 2.4 vb2 — variants

- **Krillin's "static" vb2**: `[pos.x_abs, y, z, 0,0,0, weight=0,
  0xFFFFFFFF@+28, nx, ny, nz]` — **ABSOLUTE** positions, bone=FFFF = no skin.
  (`AGENTS §3.2`; `awg_to_obj_b3.py` docstring; HISTORICO §13.5.18.)
- **Cell F2's vb2 (layout B, 276 slots)**: `[1.0, 0, 0, ?, ?, ?, nan@+20,
  U@+24, V@+28, nrm@+32]` — WITHOUT clear positions.
  (`AGENTS §3.2/§3.4.2.5`; `SESION_PORT_RE §4.4`.)
- ⚠️ The `sec2C`/`vb2` has `nan` at `+28` (a DIFFERENT layout from sec34).
  (`CONSOLIDADO §12.1`.)

### 2.5 FACE / hand AWG (n_bones = 1) — OWN layout

Solved in `HISTORICO §13.9` (2026-08-19). **Vertex (44B, FFFFFFFF marker at
+0)**:

```
+0  0xFFFFFFFF (marker)
+4  u | +8  v
+12 x | +16 y | +20 z   (POSITION in the head bone's LOCAL space)
+24 weight (=1.0) | +28 pad 0.0
+32 nx | +36 ny | +40 nz  (direct unit normal)
```
Verified: `normal·(pos−centroid) > 0` in 100%.

**Face AWG structure (offsets rel the #AWG header, h)** — the fields mean
SOMETHING ELSE than in AWG0:
```
+0x10 n_bones (=1) | +0x2C = vertex buffer SIZE (n*44)
+0x30 ib_rel = IB offset | +0x34 sec_rel = IB SIZE in bytes
+0x38 end_rel
Descriptor at h+0x180: +0x1C = n_verts, +0x24 = n_tris
Vertex buffer ALWAYS at h+0x1F0
```
- In a face AWG, `sec_rel` (+0x34) **is NOT an offset: it is the IB size**.
  The vertex buffer is NOT at `sec_rel` but at a **fixed h+0x1F0**.
- The face IB is a **triangle list** (every 3 indices = 1 triangle,
  quad-strip), not a strip with alternating winding.
- **Buffer/IB overlap**: the IB starts at `ib_rel = 0x1F0 + n*44 - 32` (they
  overlap by 32 B); `end_rel = ib_rel + n*2`. (`HISTORICO §13.10`.)
- **The head bone's local space is shared** between characters (Goku and
  Vegeta have almost identical bounds) → the geometry is copied 1:1 without
  transformation. (`HISTORICO §13.9`.)
- Tools: `awo_tools/awg_cara_export.py` (exports), `awg0_export.py`
  (auto-detects A/C), `awg_to_obj_b3.py` (full bins). (`AGENTS §10`;
  `ESTADO.md`; `ESTRUCTURA_DIBUJO_HD.md`.)

---

## 3. THE "ARMS"/SKINNING STRUCTURE AND THE TWO DESCRIPTOR TABLES

### 3.1 Arms — FINAL REVIEW (Phase B, 2026-09-10): they are a framework, NOT IB ranges

**Refuted "arms = IB ranges"** (`CONSOLIDADO §13.5.13` and
`port_ps2_to_b3.py`). Dump of `phase_b_arms_dump.py`:
- each **arm** is `[bone, ptr, 0, ptr_matrix, 0]`;
- `arm+12` → **float data (4×4 matrix) ending in `3F800000`** and growing by
  **exactly +64 B per bone** (the 64 B "Mesh End");
- `arm+4` → small arrays.
⇒ It is an **armature with pointers**. That is why `port_ps2_to_b3.py`, which
regenerated them as ranges, **crashed** (corrupted pointers), not because of a
format limit. (`SESION_FASE_B §3.3`; `CONSOLIDADO §13.5.13`;
`RE_AWO_HD_CONVERSOR §4`.)

**Historical interpretation** (the one documenting the blocker): the arms are
**per-bone skinning** data (PS2-rig style with chunks+weights), NOT IB ranges
to draw. In the original Krillin the 5140 indices are all in `[0,3904)`; the
shadows' ranges `[3904,4936)` were **EMPTY** → the IB is drawn whole and the
arms define other information. (`CONSOLIDADO §13.5.14` point 5;
`SESION_INYECCION §1.1`; `ESTRUCTURA_DIBUJO_HD §5`.)
- Intermediate history (`CONSOLIDADO §13.5.13`): "arms zone = 20 B blocks
  `[bone_idx, offA_bytes, 0, offB_bytes, 0]`, only those with the 0x204 seal
  define IB limits in bytes; the runtime draws `[previous_offset, offset_bone)`".
  **This was REFUTED** by Phase B §3.3 (the drawing offsets are empty).
- `RE_AWO_HD_CONVERSOR §4` form: `[bone, end, 0, start, 0]` (20 B), arm0 =
  `[0, 8064, 0, 7680, 0]`.

### 3.2 Mesh-ref blocks (0x50) — `X` = descriptor index, `Y` = primary bone

```
+00 id/sub
+08 00 00 01 B5 (type B5, body) | 00 00 01 B4 (B4, face) | 0x1F5 (F5)
+0C 00 00 29 BD (texture/shader)
+10 00 00 00 44 ×2 (0x44=68: count/bytes)
+18..+3F matrices (1.0/0.0)
+40 marker
```
- Number of mesh-ref blocks = the AWG0 header's `groups` (7 in Babidi, 13 in
  Krillin; Cell F2 = 17 B5 + ~4 B4). (`ESTRUCTURA_DIBUJO_HD §2/§4`;
  `SESION_PORT_RE §2`.)
- Cell F2: `X = descriptor index` (several mesh-refs per descriptor), `Y =
  primary bone`. (SESION_PORT_RE §2.)

### 3.3 Submesh descriptors (0x60) — A/B encoding confirmed

```
+00 label (8 chars, e.g. "XCEL_BODY"/"XKLL_BODY")
+10 0x09 | +14 0x0F (constants)
+18 "max N m" (string)
+24 0x34 (offset to the range)
+40 0x1158 (pool offset const) | +44 0x2C (stride 44) | +48 0x05
+50 A_start <<8 | +54 A_count <<8 | +58 B_start <<8 | +5C B_count <<8
   flag 0x01 at +0x5C (B_count)
```
**A = VERTEX range of the pool (sec34); B = INDEX range of the IB.** Verified:
the IB indices in range B ALWAYS fall inside A (Krillin 13/13, Cell 29/29,
Babidi 10/10; direct correlation Cell 22/22). (`ESTRUCTURA_DIBUJO_HD §3/§7`;
`SESION_PORT_RE §3`; `SESION_FASE_B §3.2`.)

- **A partitions the pool CONTIGUOUSLY**: each `A_start` = the previous
  `A_start+A_count`. `A ≈ [min(B), max(B+1))`. The pool is NOT contiguous per
  bone (412 fragmented bone blocks). (`SESION_FASE_B §3.7`.)
- **INERT ("neutralised") descriptor**: A points beyond sec34 (e.g. 4440 >
  1934) and B=(x,0) → it does not draw. (`ESTRUCTURA_DIBUJO_HD §3`; HISTORICO
  §13.10, neutralising Vegeta's face.)
- The face/hand descriptors have A in **vb2** (bones-in-A empty):
  `XCEL_L00_FACE`, `XKLL_M_DTEETH`. (`SESION_FASE_B §3.7`.)
- **⚠️ THERE ARE TWO DESCRIPTOR TABLES** (Phase B §3.15):
  1. **Mesh group @AWG0+~0x2D49**: 0x60 entries (label + `max N m` + A/B `<<8`,
     +0x50/+0x54/+0x58/+0x5C, flag 0x01) = the one T6 edits.
  2. **AWG0+0x1F80**: a SECOND table (flat u32) with the SAME values
     (`42,60,74,126…`, +0x1158, +0x2C const). Probably the **runtime table**
     the guest consumes when drawing ⇒ T6 (which only touched the 1st) had no
     effect. (Later: `AWG0+0x1F80` turned out to be the bind-pose matrix
     table.)

### 3.4 Axes (80 B) and the PARENT as an OFFSET (not an index)

```
+00..+2F quat+pos / 3×4 floats (bind pose)
+30 seal: 0x6000020F (body) | 0x9800020C / 0x9000020C (sub-bone) | 0x8000020C | 0x00000204 (shadow)
+34 arm_ptr (rel AWG)
+38 child   +3C sibling   +40 PARENT
```
- **The parent (+0x40) is an OFFSET relative to AWG0, NOT a bone index**:
  `parent_idx = (AWG0 + poff − axes_base) // 80`. Fixing this invalidates all
  the world matrices computed before (the `cell_conv` conversion was invalid).
  (`SESION_INYECCION §2.1`; addendum §7 for PS2: `+0x40` offset rel AMG,
  `axes_rel=0x20`.)
- With the parent fixed, the template's world traces a coherent body that
  **matches the PS2 model space** (feet, knees, hip, chest, head).
  (`SESION_INYECCION §2.1`.)

### 3.5 Zone matrix, bboxes and the mesh group box (Cell F2)

| Region | Off rel AWG0 | Size | Content |
|---|---|---|---|
| mesh-ref blocks | 0x640 | 0x6E0 | drawing parts (block 0 = 0x40 + 21×0x50) |
| axes | 0xD20 (axes_base) | 48×0x50 | quat+pos+scale + seal + arm/child/sibling/parent |
| zone matrix | 0x1C20 (0x28E0) | 48×0x10 | diagonal of bone indices + pointers to bboxes |
| bboxes | 0x1FE0 (0x2CA0) | 0x40 each | AABB per zone (min/max vec4), model space |
| descriptors | 0x2209 (0x2EA9) | 0x60 each | drawing A/B |

(`SESION_PORT_RE §1`; `ESTRUCTURA_DIBUJO_HD §7`.) The HD mesh group is a
**CONTAINER** that includes axes + arms + mesh-ref + descriptors TOGETHER; the
axes are INSIDE the mesh group (they must point to valid arms). Putting them
outside → crash. (`RE_AWO_HD_CONVERSOR §10`.)

---

## 4. ALL THE TESTS, ATTEMPTS AND THEIR LESSON

### 4.1 Permutation matrix (DICTAMEN_GPT6 §2.3) vs real execution

The assessment proposed T0–T6. The real execution (Phase B + sessions) was:

| Test | Change | In-game render | Lesson | Source |
|---|---|---|---|---|
| **T0** | Original | reference | — | DICTAMEN §2.3 |
| **T1** | Round-trip without changes | (not run as such) | serialiser errors | DICTAMEN §2.3 |
| **T2** | swap 2 vertices of the SAME bone + IB remapped | **IDENTICAL** ✅ | the order INSIDE a descriptor/bone is free | FASE_B §3.5 |
| **T3** | reverse of the pool + IB remapped + A/B recomputed | **DEFORMED** ❌ | the clean reverse DOES deform | FASE_B §3.6 |
| **T4** | reverse INSIDE each A block + IB remapped (A intact) | **DEFORMED = T3** ❌❌ | there is consumption BY POSITION; the IB is not enough | FASE_B §3.9 |
| **T5** | reverse of the pool, IB NOT touched | **MUCH WORSE** (face spread) ❌❌ | T5≫T4 ⇒ the IB controls geometry; a 2nd positional path | FASE_B §3.10 |
| **T6** | only rotate A ranges (pool+IB intact) | **NORMAL** ✅ | **range A is NOT used for drawing** | FASE_B §3.12 |
| **T7** | pool intact, whole IB inverted | **MASSIVE** (broken head) ✅ | **the IB DOES govern connectivity** | FASE_B §3.14 |
| **IB-follow** | T2/T3/T4 | `same=5125 diff=0` | identical records ⇒ the guest does NOT draw by IB only | FASE_B §3.9 |

**Census / consumer scan** (`phase_b_census.py`, `phase_b_consumer_scan.py`):
there is NO hidden raw u16/u32 consumer. IB-only: Krillin 1866/2182, Cell
2356/2937. Positional consumption does not appear with the encodings `v*44`,
`v*44+sec`, `v<<2`, `v<<8`. 15 IB entries out of range (2188–2189, 8 beyond the
pool) at the end of the IB → a possible additional buffer/pool. (`FASE_B §3.4`;
AGENTS §3.4.2.3.)

### 4.2 Bone0 test (the guest uses the vertex's bone)

`cell_bone0_test`: template with ALL the sec34 bones = 0 (positions intact) →
**collapses EVERYTHING to the feet**; the upper face and one hand survive (they
live in vb2). ⇒ **the guest USES the vertex's bone (+28) for the transform**.
**VALID** (not contaminated). (`SESION_PORT_RE §4.5/§7`; HISTORICO §3.4.2.2.)

### 4.3 Injection v1–v7 and NPM (threshold = critical parameter)

| Mod | Method | Result |
|---|---|---|
| inject2 (1001 slots) | per-bone greedy, bone-local | Recognisable Cell (hands, torso, part of the head, one leg) |
| inject4 (2385+276) | world matching + threshold 2.0 | more Cell but "decimated/reduced" + deformed polygons |
| npm (2443+218) | NPM (density fix) | ≈ inject4 |
| npm2 | NPM + triangle normal | brighter, amorphous in mouth/tail/hands/arms |
| npm3 | NPM + vertex normal | ≈ same; the bad hand improves "slightly" |
| **npm4 (1821+840)** | **NPM + normals + STRICT threshold 0.8** | ✅ **BEST**: torso, upper head, waist, legs, feet, arms, hands |
| npm6 (2443+218) | NPM + normals + **soft[0.5,2.0]** | ❌ major deformity (partial blends) |
| npm7 (1821+840) | NPM + normals + **soft[0.3,0.8]** | ❌ WORSE than npm4 |

(`SESION_INYECCION §5.1`.)

**Master lesson**: **BINARY YES, BLEND NO**. Full injection of the well-aligned
slots works; any partial weight (blend) produces half-way positions (neither
PS2 nor HD) → amorphous. The only parameter to tune is the threshold VALUE.
(`SESION_INYECCION §5.2`.)

**Per bone (match distances)**: the core (bones 0,1,15,19) and legs (5,9,10,11)
align well; OBI (3,4) and bones 13/14 badly; **hands/arms (18,20,21) very
badly, up to max 8.9**; head medium (1.0–1.25). Threshold 2.0 injected badly
matched limbs → stretched. (`SESION_INYECCION §5.2`.)

**Normals**: HD format `[nz, -ny, nx]` at +32/+36/+40; 100% unit length.
Writing only positions left HD normals → broken specular. Geometric vs
interpolated normal did not change the main cause. (`SESION_INYECCION §5.3`.)

**PS2 extractor bug (addendum 2026-09-10)**: the "L00" parts (hands bones
23/30, face 40, teeth 36/38, tail 43–47) are in the bone's **LOCAL space**; the
extractor treated them as model space. Fix in `compute_worlds()` +
`parse_parts(..., worlds)`: NPM 0.8 goes from 1821→**1962 injected**; LHAND
alignment 12.41→**0.15**. Mod `cell_npm_fix`. (`SESION_INYECCION §7`.)

### 4.4 Janemba (IW→B3) — DOCUMENTED FAILURE, archived

- v4–v10 (14/08): parse→skin→decimate→build → **deformed mass**; initial
  cause: the PS2 parser did not read the real IB (FaceType). (`AGENTS
  §3.4.4`.)
- v6 (14/08): enters battle without a crash with Krillin's EXACT counts
  (sec34=1956, IB=5140) → deformed mass due to JNB→KLL re-rigging.
  (`CONSOLIDADO §13.5.14`.)
- v7: recognisable body; v8 (fingers→18/25, faces→36): **CRASH**. State v7
  (corrupted). (`CONSOLIDADO §13.5.16`.)
- **Root cause of the system**: Krillin's arms/mesh-ref pointed to the wrong
  ranges when Janemba's geometry was injected with a different IB.
  (`CONSOLIDADO §13.5.11`.)
- **User's decision**: delete/archive the Janemba work
  (`awo_tools/historial_fallidos/`). **Do NOT retry without a validated full
  converter.** (`AGENTS §3.1`; HISTORICO §11.1.) (Later, v1.4.0 shipped Janemba
  as a new character via the importer.)

### 4.5 Pikkon (IW) — DISCARDED because of the skeleton

PKH with `SKIRT`, 58 bones, different from KLL → NOT 1:1. v7 (threshold 0.3):
the body "remarkably good" but 7 zones fail (ear, back of the head, mouth,
right shoulder, belt, right knee, left foot). Knee/foot **live in vb2**
(absolute positions) → the injection only touches sec34 → they ALWAYS stay HD.
To fix face/legs the whole bin must be rebuilt. (`AGENTS §3.1`; HISTORICO
§65.1f; `MATRIZ_CANDIDATOS` §order.)

### 4.6 Test contamination (critical operational lesson)

`cell_npm8_test` (injection threshold 1.4 on the head) stayed ACTIVE during the
whole port RE session. `AfsListMods` + `AfsFindModOverride`: active mods go
first in ALPHABETICAL order and the **FIRST mod with an entry for that slot** is
served. With npm8 active: `cell_reverse_test` and `cell_port_Afix_test` served
npm8 (**INVALID** tests); `cell_bone0_test` (bone0 < npm8 alphabetically) was
VALID. **Fix**: disable npm8. **RULE**: ONLY ONE active mod per test; check with
`Get-ChildItem mods | Where {-not .disabled}`. (`SESION_PORT_RE §7`; AGENTS
§3.4.5.4.)

### 4.7 Other relevant tests

- **Reverse** (inverted pool): re-tested on its own → deformities. The pool
  order matters. (`SESION_PORT_RE §7.1`.)
- **Port conv2** (PS2 pool + IB + A/B): amorphous. `cell_port_Afix_test` (A
  fixed): no visual change. (`SESION_PORT_RE §4.1/§4.2`; HOJA_DE_RUTA §5.)
- **Negative tests with no effect** (full port): clamping bones (35/33),
  `+0x10=9` in all, `0xFFFF→0` in the IB, winding flip → **NONE changed the
  render**. The bin WAS being served. (`SESION_INYECCION §1.1`.)
- **Buffer re-layout**: sec34 **+1 CRASHES** in battle; vb2 **+1 enters
  battle** (with lag/missing hand). ⇒ `sec34_count` is a FIXED parameter, vb2
  tolerant. AWG0 cannot shrink (v5 does not start) nor grow excessively (v4
  battle crash). Exact `sec34=1956/IB=5140` = the key of v6. (`CONSOLIDADO
  §13.5.7/§13.5.8/§13.5.14`.)
- **HD→HD head swap**: `swap_cabeza.py` (block rebuild) → CRASH 0xC0000005 (the
  AWG0 references the face AWGs by offsets that break when the block moves).
  `swap_cabeza_inplace.py` (in place, keeps sizes) → **WORKS in game** but with
  **z-fighting** on forehead/eyes. v3 neutralises Vegeta's face descriptors →
  parts of the hair disappear, still not Goku's face. **PAUSED by the user's
  decision.** (`HISTORICO §13.9/§13.10`.)

---

## 5. FACE, BONES 48-63 AND HEAD SWAP

### 5.1 Path A's structural limit: 16 single-bone AWGs (48-63)

**Cell F2 (2026-09-10)**: the HD bin has **17 AWGs**:
- **AWG0**: 48 bones, 2661 verts (body).
- **16 single-bone AWGs = bones 48-63** (face/details).

The **PS2 only has 48 bones (0-47)** → the 16 extra AWGs **have NO PS2
equivalent** and stay HD (that is why the face comes out HD). The current
injection only touches the first AWG0's `sec34`; the global bone of each
single-bone AWG is read in its arm `+0x34` → struct[0]. To PS2-ify the face,
PS2 bones 33-40 must be **remapped by label to AWGs 48-63** (vertex formats
varying per AWG: `FFFF@0/@12/@28/@32`). (`AGENTS §10`.)

- Mod `mods/cell_best` = corrected body + **hands in real HD**.
  ⚠️ The previous test `cell_npm_fix_nohand` reverted to npm4 (NOT to the
  template); npm4 already had mangled hands (bone 23 with 228 slots moved). It
  includes an anti-stretch guard (reverts triangles with an injected area >3×
  the HD one; ~68-115 verts). (`AGENTS §10`.)

### 5.2 Why face/legs stay HD (general mechanism)

- The template's `sec34` uses **only bones 0-35** (36 bones); legs (38-50) and
  face go to **vb2** (no skin, absolute positions). In HD Krillin
  `sec34=1956` only bones 0-35; vb2=226 with bone=0xFFFFFFFF. (`AGENTS §3.2`;
  HISTORICO §13.5.18; HISTORICO §3.3.)
- The injection only rewrites `sec34` → **face/legs ALWAYS stay 100% HD**.
  Inherent to Path A. (`HISTORICO §65.1f`; MATRIZ_CANDIDATOS.)

### 5.3 Face AWG (nb=1) — structure and swap (see §2.5)

Confirmed map: Goku AWG16-22 = `XGOK_L01/L18/L09/L04/L05/L06/L42_S00_FACE` ↔
Vegeta AWG19-25 = `XVGT_L01/L18/L00_S09/L04/L05/L06/L44_S00_FACE`.
Correspondence by numeric label. Shared head-bone local space → geometry
copyable 1:1. (`HISTORICO §13.9`.)

### 5.4 State of the head swap

- **in place WORKS** but with z-fighting (Vegeta's face/hair is still in the
  AWG0, overlapping). Neutralising Vegeta's face descriptors leaves holes.
  "Goku's complete face" is not achieved. Paused. (`HISTORICO
  §13.9/§13.10`.) For a complete face the AWG0's pieces (face/teeth/HAIR) would
  ALSO have to be replaced. (`HISTORICO §2098`.)

---

## 6. CRITICAL CONSTRAINTS

### 6.1 AFS / override / virtual mid-insert

- The runtime's AFS table is read at **offset 8** (magic "AFS"3B + pad1B +
  count4B; then `(addr u32, size u32)×8B`), **NOT at 0x10** (the off-by-one
  served bin N+1 → crash). (`AGENTS §5`; FASE_B §2.)
- Per-entry override: `mods/<mod>/us/<afs>/<entry_index>[/file]`
  (`AfsFindModOverride`; supports a folder). (`AGENTS §6`; ESTUDIO §1.1.)
- **VIRTUAL MID-INSERT** (`AfsGetVirtualTable`): if the override exceeds
  `to_read`, the entry grows in place (0x800-aligned) and later ones shift by
  the accumulated delta, all in memory (`AfsVirtualRange`). **NO giant files**.
  Criterion: it grows only if `override > to_read`, NOT for exceeding the
  physical slot. (`AGENTS §6`.)
- **`--append` DISCARDED**: the guest uses **binary search** over the table
  (assumes increasing offsets); append disorders it → returns the wrong entries
  → `0xC0000005`. (`AGENTS §6`; HISTORICO §65.2.) (Later, v1.4.0 added safe
  appended entries *after the last one*; see `patches/README.md`.)
- **🔴 Correct DLL**: the game build OVERWRITES `rexruntime.dll` with the stale
  one from `rexglue/bin`. After `cmake --build` the canonical DLL must be
  re-copied. Check `Select-String rexruntime.dll -Pattern
  "AfsGetVirtualTable"`. (`AGENTS §7`; ESTUDIO §5.6.)
- **The correct entry**: visible Krillin = **entry 327** (105296 B → padded
  106496). (`AGENTS §6`; note: `CONSOLIDADO §13.5.14` historically said e326
  because of the off-by-one, later corrected to 327.)

### 6.2 Compression and padding

- **LZX `/N:2048`** (NOT `/N:32`). `xbcompress /N:2048 <src> <dst>` /
  `xbdecompress`. (`AGENTS §4/§6`; ESTUDIO §1.2.)
  ⚠️ `AWO_FORMAT.md` §2.3 says `/N:32` → **OUTDATED** (keep only as history).
- **Padding to the EXACT `to_read`** the guest reads. If it is shorter → crash.
  (`AGENTS §6`; ESTUDIO §5.5.)
- Log verification: `AFS OVERRIDE HIT (folder)` + `AFS MOD READ: ...
  got=to_read`; if `got < to_read` → padding missing. (`AGENTS §6`.)

### 6.3 Buffer sizes / counts

- `sec34_count`/`vb2_count` are FIXED parameters derived from the AWG header
  offsets; changing them (even +1) breaks the parsing → null deref.
  (`CONSOLIDADO §13.5.8`.)
- Excessive growth of the AWG0/sec34 → crash **0x856AC389**. (`AGENTS
  §3.4.5.5`.)
- Keep buffers the SAME size or use counts ≤ the template.
- Janemba v6: padding to Krillin's EXACT counts with empty slots (sec34=1956,
  IB=5140) is the key. (`CONSOLIDADO §13.5.14`.)

### 6.4 Mod contamination (repeated because it is critical)

`AfsFindModOverride` serves the FIRST active mod in alphabetical order. A
forgotten mod invalidates the tests of the same slot. **ONLY ONE active mod per
test**; use `.disabled`. (`AGENTS §3.4.5.4`; FASE_B §6; SESION_PORT_RE §7.)

### 6.5 Mods / activation

- A mod is active if it does NOT have the `.disabled` marker (`IsModEnabled`).
  The cvar `dbz3_enabled_mods` is DEAD CODE. (`AGENTS §6`.)
- `AfsFindModFileOverride`: whole-file replacement in `mods/<mod>/<filename>`
  or `mods/<mod>/us|eu/<filename>`. (`AGENTS §6`.)

### 6.6 Format / engineering

- The **HD bin is SELF-CONTAINED**; the guest auto-detects format A/B/C. Do not
  force Krillin's format A. (`AGENTS §3.4.2.7`; ESTUDIO §5.7.)
- **`bone@+28` only for sec34/format A**; format C uses `+40`. Choose the layout
  per AWG, never a global offset. (`DICTAMEN §0.1`; AGENTS §3.2.)
- Descriptor A: `A = [min(B), max(B)+1)`, NEVER assume contiguity (parts share
  deduped vertices). (`AGENTS §3.4.5.3`; SESION_PORT_RE §4.2.)
- The PS2 IB is implicit through **FaceType** (1=strip, 0=triplet), not an
  index list. (`ESTUDIO §5.4`; `AMO_AWO §6.2`.)
- The HD vertex's bone is at +28 (format A) — do NOT copy the B1 layout
  (bone@+16). (`ESTUDIO §5.3`.)
- `mid-insert` enlarges an existing AFS entry; **it does NOT add new AFS
  indices**. (`DICTAMEN §0.1`; HOJA_DE_RUTA_2026_09 §3.6.)

---

## 7. INVENTORY OF KEY FACTS (quick reference)

| Fact | Value / result | Source |
|---|---|---|
| Krillin PS2 GH = HD 360 | 51 bones, 18 AWG, 68 identical labels, NO re-rigging | AWO_FORMAT §5; CONSOLIDADO §1.2 |
| Number of AWGs/bones varies | Krillin 18/51, Bulma 2/43, Babidi 1/41, Cell F2 17 (48+16) | RE_AWO §8; AGENTS §10 |
| sec34 stride | 44 B, align +2 (format A) | AGENTS §3.2; RE_AWO §1.4 |
| A/B descriptor | A=vertices, B=IB indices; B⊂A always | ESTRUCTURA_DIBUJO §3 |
| 2 descriptor tables | mesh group @~0x2D49 + AWG0+0x1F80 (runtime) | FASE_B §3.15 |
| Arms | `[bone, ptr, 0, ptr_mat4x4, 0]`, +64 B/bone, armature | FASE_B §3.3 |
| Axis parent | offset rel AWG/AMG, not an index | SESION_INYECCION §2.1/§7 |
| The guest uses bone +28 | bone0 test collapses to the feet | SESION_PORT_RE §4.5 |
| The IB is used | T7 test massive | FASE_B §3.14 |
| Range A is NOT used | T6 test normal | FASE_B §3.12 |
| Positional consumption | T4/T5 deform with a consistent IB | FASE_B §3.9/§3.10 |
| Best injection | cell_npm4 / cell_npm_fix (binary threshold 0.8) | SESION_INYECCION §5 |
| Face = 16 AWGs 48-63 | no PS2 equivalent | AGENTS §10 |
| Head swap | partial, z-fighting, paused | HISTORICO §13.10 |
| Janemba | archived failure | HISTORICO §11.1; AGENTS §3.1 |
| Pikkon | discarded (skeleton not 1:1) | AGENTS §3.1 |
| Reverse | deforms (pool order matters) | SESION_PORT_RE §7.1 |
| sec34 +1 | battle CRASH | CONSOLIDADO §13.5.8 |
| vb2 +1 | enters battle (tolerant) | CONSOLIDADO §13.5.8 |
| Compression | LZX /N:2048 + pad to to_read | AGENTS §6 |
| Mods | 1 active at a time; `.disabled` marker | AGENTS §3.4.5.4 |

---

## 8. GAPS / UNKNOWNS PENDING (for future sessions)

1. **Locate the pool's positional consumption**: it is not descriptor A (T6);
   suspect = arms/skinning + runtime table @AWG0+0x1F80. RE of the draw loop in
   `generated/dbz3_recomp.*.cpp`.
2. **Arms/skinning format** not 100% mapped (per-bone skinning structure);
   `phase_b_arms_dump.py` is the instrument.
3. **Confirm which descriptor table the draw uses** (mesh group vs 0x1F80).
4. **Cell F2's vb2 layout B** not yet emitted correctly by the port.
5. **Remap PS2 bones 33-40 to AWGs 48-63** to PS2-ify the face (vertex formats
   varying per AWG).
6. **Pending 1:1 rig**: Babidi PS2 from the GH AFS returns BE #AMB/#AWO (not LE
   #AMO0) → real PS2 source not located. Tien with cape (IW) passes the base
   rig 1:1 (42 common labels + 10 cape). (`SESION_BABIDI`; SESION_TIEN;
   MATRIZ_CANDIDATOS.)

---

### Sources read

`AGENTS.md` (§3.4, §6, §10); `docs/07_ports/`: `ESTRUCTURA_DIBUJO_HD.md`,
`SESION_INYECCION_2026-08-26.md`, `SESION_FASE_B_ARMS_2026-09-10.md`,
`SESION_PORT_RE_2026-08-26.md`, `HOJA_DE_RUTA_PORT_PS2_B3.md`,
`ESTUDIO_ECOSISTEMA_MODS.md`, `MATRIZ_CANDIDATOS_PS2_HD.md`,
`SESION_BABIDI_VALIDACION_2026-09-08.md`, `SESION_TIEN_RIG_2026-09-08.md`;
`docs/03_formatos/`: `AMO_AWO.md`, `BIN_LAYOUT.md`, `ACM_FORMAT.md`;
`AWO_FORMAT.md`; `docs/DICTAMEN_GPT6_ASTRA.md`;
`docs/HOJA_DE_RUTA_2026_09.md`; `awo_tools/CONSOLIDADO.md`,
`awo_tools/RE_AWO_HD_CONVERSOR.md`, `awo_tools/RE_PROGRESO.md` (greps);
`docs/01_estructura/HISTORICO_AGENTS.md` (§3.3, §3.4, §13.5.x, §13.9, §13.10,
§65.1e/§65.1f).
