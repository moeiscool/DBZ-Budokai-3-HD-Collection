# SESSION 2026-08-26 — THE INJECTION PATH: HD TEMPLATE + CONVERTED PS2 POSITIONS

> **EXECUTIVE SUMMARY**: the PS2→B3 HD port that rebuilds the pool/IB/
> descriptors (pipeline `port_ps2_b3_*`) **breaks the consistency of the
> template's arms** → always amorphous. The path that WORKS is **injection**:
> the COMPLETE HD template intact (pool, IB, descriptors, arms, axes) and ONLY
> rewriting the positions (+12/+16/+20) of the sec34 slots with the PS2
> geometry converted to bone-local space. **VALIDATED IN GAME**: Cell F2 PS2
> looks recognisable (hands, torso, head, leg, silhouette). Current limitation:
> the PS2 has 1880 unique vertices vs 2661 HD slots → filling collapses zones
> ("decimated" look). The way to keep the original quality = resample the PS2
> surface (nearest-point-on-surface) or rebuild the arms.

---

## 1. THE TWO PATHS AND WHY ONLY ONE WORKS

### 1.1 Full port (pool/IB/descriptors rebuilt) = ALWAYS AMORPHOUS

The pipeline `port_ps2_b3_{extract,geometry,decimate,draw,pack}` rebuilds:
- sec34 pool (our order, 1880 verts)
- IB (our consecutive strips)
- A/B descriptors (our ranges)
- vb2, shifted AWG/AZT (internal mid-insert)

The in-game result is **amorphous/indistinguishable**. Root cause (with
evidence):
- The instrumented draw log (`DBZ3_DRAW`, rexgpu-xenos.dll) **PROVED** that
  the guest DRAWS our strips correctly: 23 strips at the exact offsets of our
  `B_start×2` and with count `B_count+2` (the +2 = degenerate padding).
  → The IB/descriptors/pool positioning were **NOT the bug**.
- The problem is in the **template's draw structure** (arms + mesh-ref +
  descriptors + pool interleaved by parts) that the guest uses to SKIN and
  draw. When the pool is rebuilt in a different order, the template's arms
  reference indices that no longer correspond → broken skinning/parsing →
  amorphous.
- Additional negative test: clamping bones (35 and 33), +0x10=9 (body format)
  in all, 0xFFFF→0 in the IB, winding flip → **NONE changed the render**. The
  bin IS served correctly (our pool is at sec_rel).

### 1.2 Injection (full template + positions) = RECOGNISABLE ✅

`test_injection.py` (mod center hd/ports/): takes the COMPLETE HD template
(cell147_hd.bin) and only rewrites +12/+16/+20 of the sec34 slots. It keeps the
IB, descriptors, vb2, other AWGs, axes and arms → the guest draws it with its
structure intact.

- **Injection v1 (model space)**: injected the PS2 positions IN MODEL SPACE
  against bone-local slots → matching in DIFFERENT spaces → recognisable parts
  (hand, right arm, upper face) but mixed/amorphous. It was the test the user
  remembered as "what we did right".
- **Injection v2 (bone-local, same space)**: positions converted to bone-local
  → Cell much more recognisable (hands, torso, part of the head, one leg,
  silhouette).
- **Injection v3/v4 (world matching + threshold)**: matching by NEIGHBOURHOOD
  IN WORLD (the slot's world = world[B]·local, against the PS2 model-space
  verts) with conversion to the slot's bone-local + threshold 2.0 (the worst
  10% keeps the original HD position). → **MUCH MORE Cell** but with a
  "decimated/reduced" look and deformed polygons. **CURRENT STATE OF THE
  PATH.**

## 2. 🔴 KEY FINDINGS OF THE SESSION

### 2.1 THE AXIS PARENT IS AN OFFSET, NOT AN INDEX (corrects everything before)

The axes (80B) at `mg+0x6E0` (48×80 for Cell F2). The `+0x40` field is the
**pointer to the parent axis expressed as an OFFSET relative to AWG0**, NOT a
bone index:

```
parent_idx = (AWG0 + poff - axes_base) // 80    # poff = be32(axis+0x40)
```

Verified: bone 1 parent=3360 (0xD20) → AWG0+0xD20 = 0x19E0 = bone 0's axis.
bone 2 parent=3440 → 0x1A30 = bone 1. etc. (increments of 80).

**Consequence**: ALL the world matrices computed before this finding were
garbage (the offset was used as an index → the parent was not accumulated).
The previous session's `cell_conv` conversion (model→bone-local) was invalid.
With the parent fixed, the template's world traces a coherent body:
- feet y≈-12.6, knees ≈-5, hip ≈0-1, chest 2.8-4.6, shoulders ≈6.6, head
  y≈8.7 (bone 32), skull 8.72 (bone 33).
- **It matches the PS2 model space** (feet -11.5, knees -7.2, chest 3.4-5.5,
  head 9.6) → both bodies are in the SAME world space.

### 2.2 THE HD SEC34 STORES BONE-LOCAL POSITIONS (not model space)

- The template (Cell F2, format A): sec34 = positions in the bone's local
  space (mag_med 1.70, max 6.37). The shader transforms `world[bone]·local`.
- The PS2: the rig assigns **model-space** coords (per-bone centroids trace the
  body: feet -11.5, head 9.6). Feeding model space as bone-local stretches the
  render (amorphous).
- **The correct conversion**: `local = inv(world[bone]) · model`. Verified:
  converted local median 2.15 (≈ template 1.7). With this conversion the
  injection matches in the SAME space and works.

### 2.3 THE PS2 HAS 1880 UNIQUE VERTICES (4938 expanded)

- The PS2 geometry (cell_geometry.json) has **4938 verts** = strip-EXPANDED
  vertices (each triangle stores its 3 verts, with duplicates).
- Voxel dedup (0.05) → **1880 unique** = the real density of the PS2 surface.
- The HD template has **2661 sec34 slots**. → 1880 < 2661 → full filling
  REUSES ~781 vertices → collapsed/flat triangles → "decimated" look.
  **This is the cause of the "decimated and reduced version" look the user
  sees.**

## 3. SESSION TOOLS

| File | Function |
|---|---|
| `mod center hd/ports/test_injection.py` | Per-bone greedy injection (v1/v2). Rewrites +12/+16/+20 of the slots. |
| `mod center hd/ports/port_ps2_b3_inject.py` | **NEW** — world-matching injection + per-slot conversion + threshold (v3/v4). Usage: `python port_ps2_b3_inject.py <template> <geometry.json> <threshold> <output>` |
| `%TEMP%\opencode\cell_conv_geom.json` | PS2 geometry.json with sec34 converted to bone-local. |
| `%TEMP%\opencode\cell147_hd.bin` | Cell F2 HD template (bin 147). |
| `%TEMP%\opencode\cell_geometry.json` | Undecimated PS2 geometry (4938 verts). |
| `%TEMP%\opencode\cell_delta0_geometry.json` | Decimated geometry (1880 verts) used in the port/injection. |

**Test mods (out/build/win-amd64-release/mods/)**: cell_inject2_test (1001
slots, bone-local), cell_inject4_test (2385+276, world matching + threshold 2.0
— **CURRENT**). Documented negative tests: cell_desc_test, cell_bodyfmt_test,
cell_nopad_test, cell_clamp33_test, cell_boneclamp_test, cell_conv_test (broken
matrices).

## 4. HOW TO KEEP THE ORIGINAL QUALITY (next steps)

The "decimated look" comes from filling 2661 slots with 1880 unique positions.
Options, in order of effort:

1. **Nearest-point-on-surface (NPM)**: for each HD slot (world), project to
   the NEAREST point of the PS2 surface (on the mesh triangles, not the nearest
   vertex). It produces 2661 distinct positions on the PS2 surface → no
   collapse, no "decimation". Requires building the PS2 triangle list (from the
   extract: strips per part with FaceType) and a point-triangle distance.
   **This is the recommended path to keep the quality.**
2. **Subdivision/refinement of the PS2**: generate intermediate vertices on the
   PS2 triangles until reaching ~2661. Equivalent to NPM but generating a mesh.
3. **Rebuild the arms** (a real full port): RE of the template's arms format
   and regenerate them for our pool → the guest skins with the correct
   structure and accepts our pool/IB. It is the "real port" but requires
   decoding the arms format (per-bone skinning structure, not yet 100% mapped).
4. **Lower the threshold / refine the matching**: incremental improvement
   (less stretching) but does NOT remove the collapse caused by too few
   vertices.

**Fact for NPM**: the full PS2 surface (4938 expanded) has ALL the positions;
the triangles are rebuilt from the extract's parts (consecutive strip,
alternating winding, degenerates). Expanded vertex i of the part → the surface.
Projecting each HD slot (world) to the nearest PS2 triangle gives the position
of the PS2 surface at the closest point → 1:1 density with the HD.

## 5. ✅ IN-GAME RESULTS (2026-08-26 afternoon) — A STRICT THRESHOLD = THE KEY

**Progression of tests and results (user)**: see §5.1.

### 5.1 FULL PROGRESSION OF THE INJECTION

| Mod | Method | In-game result |
|---|---|---|
| inject2 (1001 slots) | per-bone greedy, bone-local | Recognisable Cell: hands, torso, part of the head, one leg. |
| inject4 (2385+276) | world matching + threshold 2.0 | More Cell but "decimated/reduced" + deformed polygons. |
| npm (2443+218) | NPM (density fix) | Practically the same as inject4. |
| npm2 (geometric normals) | NPM + triangle normal | Brighter (B3HD specular), Cell silhouette, but amorphous in mouth/tail/hands/arms. |
| npm3 (smoothed normals) | NPM + interpolated vertex normal | Practically the same; the bad hand improved "slightly". |
| **npm4 (1821+840)** | **NPM + normals + STRICT threshold 0.8** | ✅ **SIGNIFICANT IMPROVEMENT**: torso, upper head, lower waist, legs, feet, arms, hands. Mouth improved slightly. Still not perfect. |
| npm6 (2443+218) | NPM + normals + **soft[0.5,2.0]** | ❌ **MAJOR DEFORMITY**: only feet/waist/partial legs. The soft blend re-injected the limbs (0.5-2.0) with partial weights → half-way positions → stretched. |
| npm7 (1821+840) | NPM + normals + **soft[0.3,0.8]** | ❌ WORSE than npm4: only the upper head normal. Partial weights inside the core (0.3-0.8) break the full positions. |

### 5.2 🔴🔴 LESSON: BINARY YES, BLEND NO

Both blend tests (npm6 and npm7) were WORSE than the binary npm4. **Full
injection of the well-aligned slots works; any partial weight (blend) produces
half-way positions (neither PS2 nor HD) → amorphous.** The binary threshold is
the correct mechanism. The only parameter to tune is the threshold VALUE.

### 5.3 🔴 ANALYSIS FINDINGS (match distances per bone)

The shape mismatch between the PS2 and the HD is NOT uniformly distributed:

| Zone | bones | med dist | p90 | max | Aligns? |
|---|---|---|---|---|---|
| Core body (BODY/WAIST/CHEST/RCHN) | 0,1,15,19 | 0.33-0.75 | 1.0-1.2 | 1.7 | ✅ YES |
| Legs (LLEG1/RLEG1/RFOOT) | 5,9,10,11 | 0.4-0.65 | ~1.0 | 2.4 | ✅ YES |
| OBI / leg rotation | 3,4 | 0.9-1.17 | 3.3-4.3 | 4.9 | ❌ bad |
| bone 13/14 | 13,14 | 1.5-1.95 | 2.0-2.4 | 2.8 | ❌ bad |
| Hands/arms (LHAND/RARM/RHAND) | 18,20,21 | 0.67-1.63 | 2.5-8.7 | **8.9** | ❌ VERY bad |
| Head | 32,33 | 1.0-1.25 | 2.4-2.6 | 2.7 | ◑ medium |

**Conclusion**: threshold 2.0 injected the limbs (distance 2-8.9) with badly
matched positions → stretched → amorphous (mouth/tail/hands/arms). **Threshold
0.8** only touches the well-aligned body (core + legs), leaving the limbs with
the correct HD shape → significant improvement. **The threshold is the
critical parameter of the injection.**

### 5.4 🔴 NORMALS — SECOND FINDING

The v4/NPM injection only wrote +12/+16/+20 (positions). The normals
(+32/+36/+40) stayed from the HD → shading was still computed for the HD shape
→ "deformed polygons" with broken specular. When writing the PS2 surface
normals:
- **GEOMETRIC triangle normal** (edge cross product): the B3HD specular works
  (brighter, clear Cell silhouette) but faceted → localised amorphousness
  (mouth/tail/hands/arms).
- **Interpolated VERTEX normal** (barycentric, smoothed): improves the bad hand
  "slightly"; the rest the same. Faceting was not the main cause.

HD normal format: `[nz, -ny, nx]` (y negated) at +32/+36/+40. Verified: 100%
unit length (med 1.000, 0 outside [0.8,1.2]).

### 5.5 WHAT REMAINS (perfecting)

- **Seams**: the transitions between the injected (PS2) zones and the HD
  (limb) ones create seam blends. A SOFT threshold (linear blend by distance)
  could smooth them.
- **Head/mouth**: medium mismatch (1.0-1.25) → the mouth improved only
  slightly. Requires aligning the head or injecting it with a dedicated
  threshold.
- The full port (PS2 topology + rebuilt arms) remains the final goal to
  reproduce the exact PS2 Cell.

## 6. NUMERIC VERIFICATION (for reproduction)

```
Cell F2 HD template (bin 147): sec34=2661 slots (align +2), bones 0-33,
  coherent world with the parent fixed.
PS2 geometry: 4938 expanded → 1880 unique (voxel 0.05) → 2661 slots with
  ~781 reused.
Match distances (slot world ↔ PS2 surface): med 0.62, p90 2.02, max 8.91.
Threshold 2.0 → 276 HD slots | 0.8 → 840 HD slots | 1.2 → 560 HD slots.
NPM: 2908 PS2 triangles (36 parts).
npm4 injection (threshold 0.8): 1821 injected + 840 HD.
```

---

**Links**: `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md` (descriptors/mesh-ref/axes/
arms), `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md`, AGENTS §3.4.

---

## 7. 🔴 ADDENDUM 2026-09-10 — PS2 EXTRACTOR BUG (local space of the "L00" parts)

**Cause of the injection deformities** (hands/face/teeth): the PS2 extractor
treated ALL vertices as model space, but the "L00" parts (hands bones 23/30,
face 40, teeth 36/38, tail 43-47) are in the bone's **LOCAL space** and must
be transformed by the bone's world.

- **PS2 axis structure (80B LE)**: `+0x14` of AMG0 = axes base (=**0x20**);
  `+0x40` = **PARENT** as an offset rel AMG → `parent = (poff - 0x20)//80`.
  (The parent was not read before.)
- **Check**: left hand (bone 23) local verts centroid (1.15,0.09) → transformed
  by `world[23]` (parent 21 LHANDROT) → **(10.64,6.23)** = the real hand. The
  body (bone 0, identity world) was already in model space.
- **Fix applied** to `port_ps2_b3_extract.py`: `compute_worlds()`
  (qmat/mmul/mvec) + `parse_parts(..., worlds)` transforms pos and normal by
  `world[part_bone]`. Adds `parents` + `worlds` to the JSON.
- **Effect**: NPM threshold 0.8 goes from **1821→1962 injected**; LHAND from
  228→373; median distance 0.43→0.38; per-bone alignment LHAND
  12.41→**0.15**, teeth on the skull. `cell_align_check.py` verifies it.

⚠️ With the skin fixed, **bone-aware matching (`--bone-aware`) becomes viable
again** (it failed before because of the bug). Test mod: `mods/cell_npm_fix`
(`cell_npm_fix08.bin`, extract `cell_extract2.json`).

**Usage**: `port_ps2_b3_extract.py <186.amo> cell_extract2.json` and then
`port_ps2_b3_inject.py e147.bin cell_extract2.json 0.8 out.bin --npm`.
