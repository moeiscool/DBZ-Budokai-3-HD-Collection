# 04_FORMATO_RE — Vertex layout and space of the 16 auxiliary AWGs (bones 48–63)

> Date: 2026-09-10. Author: RE engineer (opencode).
> Bin analysed: `e147.bin` (#AMB, BE, 715872 B) = Cell (Semi-Perfect) slot 147.
> PS2 source: `cell_extract2.json` (36 `parts`, 48 labels, `skin`, `worlds`).
> **Scope**: empirical work with temporary scripts in `%TEMP%\opencode\phaseb\`.
> No file of the repo was modified. `awo_tools\awg0_export.py`
> (`detect_format`) and `mod center hd\ports\port_ps2_b3_inject.py`
> (`world_mats`, `closest_point_triangles`, `barycentric`) are reused.
>
> ⚠️ **Later correction (2026-09-13)**: the "6 layout families" of §2-§3 were
> an artefact of reading on a misaligned grid. All 17 AWGs use the SAME 44 B
> window layout (`pos@0, w@12, bone@16, nrm@20, FFFFFFFF@32, uv@36`) over
> `[ib − g(0x2C), ib)`. See `SESION_DRAW_SEMANTICS_2026-09-11.md` §20.1. The
> spaces (§4) and the PS2→HD mapping (§6) remain valid.

---

## 0. EXECUTIVE SUMMARY

1. **Premise correction**: of the 16 single-bone AWGs (global bones 48–63) **NOT
   all 16 are face**. They are **10 hands** (48–57) + **6 face** (58–63):
   - 48–52 `CEL_L01/L02/L04/L05/L10_LHAND`, 53–57
     `CEL_L01/L02/L04/L05/L10_RHAND`.
   - 58–63 `XCEL_L01/L18/L09/L04/L05/L06_FACE`.
2. **6 layout families** (stride 44 in all) with the `0xFFFFFFFF` marker at +0,
   +12, +20, +24, +28 or +32; weight/pad in different positions; **the position
   is detected by the arm's bbox** (`arm field[3]` = 6 floats min/max) →
   identifies the 3 position columns **and their component order**.
3. **Confirmed space**: the 16 AWGs have **identity** axes (no rotation) and
   their vertices are in the **parent bone's local** space:
   - left hands → `world[23]` (CEL_L00_LHAND) — mean distance to the PS2
     surface **0.12**.
   - right hands → `world[30]` (CEL_L00_RHAND) — **0.12**.
   - face → `world[32]` (CEL_HEAD; identity + translation y=8.466) —
     **0.01–0.09**.
   (vs. identity 0.22–0.26 and neighbouring bones 0.44–0.58 → the statement's
   hypothesis **verified**).
4. **The HD geometry is already <0.1 u from the PS2 surface** → the HD is a
   **denser re-mesh of the same PS2 model**. Rewriting positions with
   *nearest-point-on-surface* is therefore **low risk** (it is not rebuilding
   topology, it is a fine local projection).
5. **PS2→HD mapping**: the 3 PS2 hand `parts` (`bone 23` / `bone 30`) feed **5
   HD AWGs each**; the PS2 face `XCEL_L00_FACE` (`bone 40`) feeds **the 6 face
   AWGs**. The PS2 teeth (`b36`/`b38`) **have no dedicated single-bone HD AWG**
   in this bin.

---

## 1. LAYOUT DETECTION METHOD

For each AWG (indices 0–16):

1. Read the header: `n_bones +0x10`, `axes +0x14`, `mg +0x20`, `sec +0x34`,
   `ib +0x30`, `end +0x38`.
2. The vertex buffer of the single-bone AWGs takes **[sec, ib)** with **stride
   44** and **one `0xFFFFFFFF` per record**. The pair `(r, mo)` (record start
   offset `r∈[0,43]` and marker offset `mo`) that makes **100 % of the
   records** have the marker is searched for. Number of vertices = number of
   markers.
3. Identify columns by statistical invariants over all records:
   - **weight**: column == `1.0` in 100 %;
   - **pad**: column == `0.0` in 100 %;
   - **normal**: a triple of consecutive floats with |n|≈1 in ≈100 %;
   - **position**: the 3 columns whose `(min,max)` match exactly `arm
     field[3]` (6 floats = min/max). The component order (x,y,z) comes from the
     same match.
   - **uv**: the 2 remaining columns (values in [0,≈2]).
4. Checking the normal's component order: each permutation of the triple was
   compared with the projected PS2 normal; **the identity permutation (0,1,2)
   always wins** (dot 0.45–0.92), i.e. the normal is written in the **same
   order its offsets appear** and **without negation/swizzle** (unlike the
   AWG0's sec34, which uses `[nz,-ny,nx]`).

> Reuse: `awg0_export.detect_format` only covers the AWG0's A/C; for these 16 a
> detector by invariants (above) was needed. The `arm field[3]` (bbox) is the
> key piece: it gives the list and order of the position columns without
> ambiguity.

---

## 2. GENERAL TABLE OF THE 17 AWGs

Offsets relative to the start of the `#AWG`. `rec.sec` = `sec_rel..ib_rel`.
`marker/weight/pad/normal/uv/pos` in bytes inside the 44 B record. `r` = delay
bytes of the first record (align). All BE.

| AWG | bone | label | n_vert | rec.sec | marker | weight | pad | normal (x,y,z) | uv (u,v) | pos (x,y,z) | r |
|----:|:-----:|:------|------:|--------:|-------:|-------:|----:|:--------------:|:--------:|:-----------:|:-:|
| AWG0 | 0–47 (body) | XCEL_BODY… | 2661 | +0x313A..+0x1FAB0 | +0 | +24 | — | +32/+36/+40 | +4/+8 | z+12/x+16/y+20 | +2 |
| AWG1 | 48 | CEL_L01_LHAND | 192 | +0x330..+0x2430 | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |
| AWG2 | 49 | CEL_L02_LHAND | 196 | +0x390..+0x2564 | +24 | +4 | +8 | +12/+16/+20 | +28/+32 | +36/+40/+0 | 0 |
| AWG3 | 50 | CEL_L04_LHAND | 187 | +0x420..+0x245C | +12 | +36 | +40 | +0/+4/+8 | +16/+20 | +24/+28/+32 | 0 |
| AWG4 | 51 | CEL_L05_LHAND | 167 | +0x330..+0x1FE4 | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |
| AWG5 | 52 | CEL_L10_LHAND | 214 | +0x4B0..+0x2984 | +0 | +24 | +28 | +32/+36/+40 | +4/+8 | +12/+16/+20 | 0 |
| AWG6 | 53 | CEL_L01_RHAND | 196 | +0x330..+0x24E0 | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |
| AWG7 | 54 | CEL_L02_RHAND | 200 | +0x390..+0x2614 | +24 | +4 | +8 | +12/+16/+20 | +28/+32 | +36/+40/+0 | 0 |
| AWG8 | 55 | CEL_L04_RHAND | 191 | +0x420..+0x250C | +12 | +36 | +40 | +0/+4/+8 | +16/+20 | +24/+28/+32 | 0 |
| AWG9 | 56 | CEL_L05_RHAND | 167 | +0x330..+0x1FE4 | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |
| AWG10 | 57 | CEL_L10_RHAND | 214 | +0x4B0..+0x2984 | +0 | +24 | +28 | +32/+36/+40 | +4/+8 | +12/+16/+20 | 0 |
| AWG11 | 58 | XCEL_L01_FACE | 190 | +0x3E4..+0x24B4 | +28 | +8 | +12 | +16/+20/+24 | +32/+36 | +40/+0/+4 | 0 |
| AWG12 | 59 | XCEL_L18_FACE | 173 | +0x3C0..+0x219C | +20 | +0 | +4 | +8/+12/+16 | +24/+28 | +32/+36/+40 | 0 |
| AWG13 | 60 | XCEL_L09_FACE | 203 | +0x438..+0x271C | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |
| AWG14 | 61 | XCEL_L04_FACE | 198 | +0x40E..+0x2640 | +28 | +8 | +12 | +16/+20/+24 | +32/+36 | +40/+0/+4 | **2** |
| AWG15 | 62 | XCEL_L05_FACE | 194 | +0x40E..+0x2590 | +28 | +8 | +12 | +16/+20/+24 | +32/+36 | +40/+0/+4 | **2** |
| AWG16 | 63 | XCEL_L06_FACE | 203 | +0x438..+0x271C | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0/+4/+8 | 0 |

Notes:
- `AWG0` is included for reference; its sec34 uses **format A** documented in
  `AGENTS §3.2` (with `+2` align, bone at `+28`, normal `[nz,-ny,nx]`). Its
  vertex buffer ends at **`vb2`** (`+0x1FAB0`), NOT at `ib`; and its axes are
  NOT identity (real skeleton).
- **AWG14/15 have `r=2`**: the first record starts at `AWG+sec_rel+2`.
- The single-bone AWGs **have no `bone` field in the vertex**: the bone is
  implicit in the AWG (read in the arm: a struct of 5 u32 at
  `awg + be32(axis+0x34)`, `struct[0]` = global bone; `struct[3]` = offset
  relative to the AWG of the min/max bbox).
- The single-bone axes (`awg + be32(awg+0x14)`, 80 B record) have an
  **identity quaternion and zero translation**.

---

## 3. LAYOUT FAMILIES

| Family | AWGs | marker | weight | pad | normal | uv | pos (x,y,z) |
|:-------:|:-----|:------:|:------:|:---:|:------:|:--:|:-----------:|
| **F1** | 1, 4, 6, 9, 13, 16 | +32 | +12 | +16 | +20/+24/+28 | +36/+40 | +0 / +4 / +8 |
| **F2** | 2, 7 | +24 | +4 | +8 | +12/+16/+20 | +28/+32 | +36 / +40 / +0 |
| **F3** | 3, 8 | +12 | +36 | +40 | +0/+4/+8 | +16/+20 | +24 / +28 / +32 |
| **F4** | 5, 10 | +0 | +24 | +28 | +32/+36/+40 | +4/+8 | +12 / +16 / +20 |
| **F5** | 11, 14, 15 | +28 | +8 | +12 | +16/+20/+24 | +32/+36 | +40 / +0 / +4 |
| **F6** | 12 | +20 | +0 | +4 | +8/+12/+16 | +24/+28 | +32 / +36 / +40 |

Observed structure: the record is a **rotation of a 10-field template**
(`pos(3) + weight + pad + normal(3) + marker + uv(2)`), with a different
starting point per AWG (the 360 vertex declarator allows any order). F3 and F6
are the most "canonical"; F5 is a permutation of F6 (pos `(x=+40,y=+0,z=+4)`).
(This "rotation" is exactly the symptom of reading the window grid from a
shifted start; see the correction at the top.)

---

## 4. SPACE/WORLD — QUANTITATIVE VERIFICATION

For each AWG its local geometry was read (with the §3 layout), each candidate
world matrix was applied and the mean distance to the **full PS2 surface**
(2908 triangles, model space) was measured. Lower = better.

**Face AWGs (11–16), mean distance to the PS2 surface:**

| AWG | world[32] CEL_HEAD | world[0] (identity) | world[23] LHAND | world[30] RHAND |
|----:|:------------------:|:--------------------:|:---------------:|:---------------:|
| 11 | **0.09** (max 0.59) | 0.25 | 0.54 | 0.44 |
| 12 | **0.01** (max 0.07) | 0.23 | 0.58 | 0.47 |
| 13 | **0.01** (max 0.06) | 0.22 | 0.54 | 0.43 |
| 14 | **0.09** (max 0.66) | 0.24 | 0.55 | 0.44 |
| 15 | **0.09** (max 0.54) | 0.24 | 0.55 | 0.44 |
| 16 | **0.03** (max 0.18) | 0.22 | 0.56 | 0.46 |

**Hand AWGs** (sample; `world[23]` wins on the left and `world[30]` on the
right):

| AWG | world[23] | world[30] | world[32] | world[0] |
|----:|:---------:|:---------:|:---------:|:--------:|
| 1 (L01) | **0.12** | 0.16 | 0.25 | 0.26 |
| 5 (L10) | **0.16** | 0.22 | 0.34 | 0.24 |
| 6 (R01) | 0.16 | **0.12** | 0.25 | 0.26 |
| 10 (R10) | 0.22 | **0.15** | 0.31 | 0.21 |

**Conclusion**: `world[32]` (CEL_HEAD) is **the** space of the 6 face AWGs (the
statement's hypothesis confirmed); `world[23]`/`world[30]` for the hands.
`world[32]` has identity rotation and translation `(0, 8.466, 0)`; so for the
face `local = model − (0, 8.466, 0)`.

Resulting model-space centroids (applying the parent's world):

| AWG | local centroid | model centroid | PS2 reference |
|----:|:--------------:|:--------------:|:------------------|
| 1–5 | ≈ (0.8–1.1, 0, 0) | ≈ (10.3–10.6, 6.2–6.4, 0.05) | b23 LHAND c=(11.5,6.1,0.1) |
| 6–10 | same | ≈ (−10.3..−10.6, 6.2–6.4, 0.05) | b30 RHAND c=(−11.5,6.1,0.1) |
| 11–16 | ≈ (0.04, 0.75, 1.14) | ≈ (0.04, 9.2, 1.14) | b40 FACE c=(0,9.5,1.13)/(0,9.0,1.04) |

---

## 5. PS2 GEOMETRY OF BONES 32–41 (`cell_extract2.json`)

`parts` with bone 32–41 in **model space**. Only 3 bones have `parts`; the rest
(33,34,35,37,39,41) have no separate geometry of their own (their vertices live
inside `b40` and/or `b0`).

| part idx | bone | PS2 label | n_vert | centroid (model) | notes |
|:--------:|:-----:|:----------|------:|:------------------|:------|
| 29 | 36 | XCEL_M_DTEETH | 58 | (0.03, 8.38, 1.24) | lower teeth |
| 30 | 36 | XCEL_M_DTEETH | 54 | (0.00, 8.41, 1.10) | lower teeth |
| 31 | 38 | XCEL_M_UTEETH | 54 | (−0.01, 8.46, 1.24) | upper teeth |
| 32 | 40 | XCEL_L00_FACE | 160 | (0.00, 9.47, 1.13) | **main face** |
| 33 | 40 | XCEL_L00_FACE | 22 | (−0.01, 8.81, 1.42) | small patch (forehead/nose) |
| 34 | 40 | XCEL_L00_FACE | 94 | (−0.02, 8.97, 1.04) | lower face (mouth/chin) |
| 35 | 47 | CEL_T_TAIL6 | 94 | (−0.04,−12.06,−7.69) | tail (not face) |

- **33 XCEL_M_JAW, 34/37 LMOUTH1/2, 35/39 RMOUTH1/2, 41 XCEL_NH**: **no
  `parts`** in the extract (the mouth/lips mesh is inside `b40`; the teeth are
  `b36`/`b38`).
- PS2 hands: `b23` ×3 parts (166+130+44) and `b30` ×3 parts (180+126+44).

---

## 6. PROPOSED PS2 → HD AWG MAPPING

The relationship is **not 1:1**: the HD subdivides the same PS2 surface into
more sub-meshes (5 per hand, 6 per face). The mapping is done **by surface
region**, not by vertex counts.

### 6.1 Mapping table (HD ← PS2)

| HD AWG | HD bone | HD label | world (parent) | Target PS2 region | Evidence (mean dist.) |
|:------:|:--------:|:---------|:-------------:|:--------------------|:-----------------------:|
| 1–5 | 48–52 | CEL_L01/L02/L04/L05/L10_LHAND | `world[23]` | `bone 23` (b23, 3 parts) | 0.12–0.16 |
| 6–10 | 53–57 | CEL_L01/L02/L04/L05/L10_RHAND | `world[30]` | `bone 30` (b30, 3 parts) | 0.12–0.15 |
| 11, 14, 15 | 58, 61, 62 | XCEL_L01/L04/L05_FACE | `world[32]` | `bone 40` (b40) | 0.09 |
| 12, 13 | 59, 60 | XCEL_L18/L09_FACE | `world[32]` | `bone 40` (b40) | 0.01 |
| 16 | 63 | XCEL_L06_FACE | `world[32]` | `bone 40` (b40) | 0.03 |

### 6.2 Justification

- **Label name**: `***_LHAND`/`***_RHAND` fixes the side (the 10 hand ones);
  `XCEL_***_FACE` fixes the face. It matches the PS2 labels `CEL_L00_LHAND`
  (b23), `CEL_L00_RHAND` (b30), `XCEL_L00_FACE` (b40).
- **Position/centroid**: the 10 hand AWGs fall at `x≈±10.5, y≈6.3, z≈0` (the 6
  PS2 hand parts), and the 6 face ones at `(0, 9.2, 1.14)` (b40). See §4.
- **Bone-aware / nearest-surface**: 100 % of the hand vertices match PS2
  triangles of `bone 23`/`bone 30`; the face ones with `bone 40` (never with
  teeth 36/38). This confirms that the HD↔PS2 split is by region.

### 6.3 Semantic hypothesis of the 6 face AWGs (best effort)

The 6 share a bbox and centroid; **they cannot be separated by position**. By
**protrusion** relative to the PS2 surface (`dist > 0.10`) the following is
proposed:

| HD AWG | label | mean dist | profile | hypothesis |
|:------:|:------|:----------:|:-------|:----------|
| 12 | XCEL_L18_FACE | 0.01 | on the surface | **skin/main face** |
| 13 | XCEL_L09_FACE | 0.01 | on the surface | **skin/main face** (2nd layer) |
| 11 | XCEL_L01_FACE | 0.09 | 55 verts +z (0.06–0.09) | **detail** (brows/lashes/eyes) |
| 14 | XCEL_L04_FACE | 0.09 | 59 verts +z | **detail** |
| 15 | XCEL_L05_FACE | 0.09 | 53 verts +z | **detail** |
| 16 | XCEL_L06_FACE | 0.03 | 14 central verts y 0.5–0.9, \|x\|<0.6, z 1.0–1.4 | **mouth/nose** (central patch) |

> The exact eyes/mouth/teeth assignment **requires the material/texture** (the
> mesh group's material index → `#AZT` block; e.g. AWG16 contains the `#AZT`
> table with several `DDS|DXT3`). Geometry alone does not determine it. The PS2
> teeth (`b36`/`b38`) have no dedicated HD AWG in this bin: they must be looked
> for in the `vb2`/AWG0 or handled separately.

---

## 7. IMPLEMENTATION SPECIFICATION

Goal: rewrite **only position and normal** of the 16 auxiliary AWGs from the
PS2 surface (*nearest-point-on-surface*), converting to the parent's
bone-local. Do **not** touch weight, pad, marker, uv, IB, descriptors or arms
(the template is kept, just like Path A).

### 7.1 Inputs / constants

- Template `templ` (#AMB) and the PS2 `extract` (`parts` + vertex normals per
  face).
- `world, AWG0 = world_mats(templ, 0x40)` (from `port_ps2_b3_inject.py`).
- AWG → parent bone (world) map:
  - AWG 1–5 → 23; AWG 6–10 → 30; AWG 11–16 → 32.
- AWG → PS2 surface region map (set of `p['bone']`):
  - left hands `{23}`; right hands `{30}`; face `{40}` (optionally
    `{36,38,40}` if the teeth are wanted).
- Layout families (§3) with: `r` (start delay), `mo` (marker), `pos[3]`
  (offsets x,y,z in order), `nrm[3]` (offsets n x,y,z in order), `weight`,
  `pad`.
- Threshold `THR`: face 0.8, hands 1.0 (loose; the real errors are ≤0.66). If
  `d>THR` the original HD position is **kept** (avoids jumps in holes of the PS2
  surface).

### 7.2 PS2 surface per region

```python
def build_region_surface(extract, bones):
    T, N = [], []
    for p in extract['parts']:
        if p['bone'] not in bones: continue
        V  = [v[1:4] for v in p['verts']]   # model-space
        NV = [v[4:7] for v in p['verts']]
        for (a,b,c) in p['tris']:
            T.append([V[a], V[b], V[c]])
            N.append([NV[a], NV[b], NV[c]])
    return np.array(T), np.array(N)          # (tri,3,3), (tri,3,3)
```

### 7.3 Injection algorithm per AWG

```python
world, AWG0 = world_mats(templ, 0x40)
HOST = {1:23,2:23,3:23,4:23,5:23, 6:30,7:30,8:30,9:30,10:30,
        11:32,12:32,13:32,14:32,15:32,16:32}
REGION = {23:{23}, 30:{30}, 32:{40}}         # surface region per parent

awg_tbl = 0x40 + be32(templ, 0x40 + 0x1C)
def awg_off(i): return 0x40 + be32(templ, awg_tbl + i*4)

for i, host in HOST.items():
    awg   = awg_off(i)
    lay   = LAYOUT[i]                         # from the §3 table (r, mo, pos[3], nrm[3])
    sec   = awg + be32(templ, awg + 0x34) + lay['r']
    ib    = awg + be32(templ, awg + 0x30)
    n     = (ib - sec) // 44                  # number of records (see note)

    T, N  = build_region_surface(extract, REGION[host])
    W     = world[host]                       # 4x4 local->model
    Rm, tm = W[:3,:3], W[:3,3]
    invW  = np.linalg.inv(W)

    for k in range(n):
        o = sec + k*44
        # 1) read the local position (x,y,z order of the layout)
        p_loc = np.array([be_f(templ, o+lay['pos'][0]),
                          be_f(templ, o+lay['pos'][1]),
                          be_f(templ, o+lay['pos'][2])])
        p_mod = Rm.dot(p_loc) + tm
        # 2) nearest-point-on-surface (model space)
        cp   = closest_point_triangles(p_mod, T)
        d2   = ((cp - p_mod)**2).sum(1); kk = int(np.argmin(d2))
        d    = float(np.sqrt(d2[kk]))
        if d > THR:            # keep HD
            continue
        target_mod = cp[kk]
        # 3) interpolated PS2 normal (model space)
        a,b,c = T[kk,0], T[kk,1], T[kk,2]
        u,v,w = barycentric(target_mod, a, b, c)
        n_mod = u*N[kk,0] + v*N[kk,1] + w*N[kk,2]
        n_mod /= (np.linalg.norm(n_mod) + 1e-12)
        # 4) convert to local and write
        lc  = invW.dot(np.append(target_mod, 1.0))
        for c in range(3):
            f32i(templ, o + lay['pos'][c], float(lc[c]))
        n_loc = invW[:3,:3].dot(n_mod)       # rotation only
        for c in range(3):
            f32i(templ, o + lay['nrm'][c], float(n_loc[c]))
```

### 7.4 Critical points / rules

1. **Do not touch** `weight`, `pad`, `marker`, `uv`, nor the
   `ib`/`end`/descriptors/arms: Path A keeps the whole drawing structure. Only
   3 position floats and 3 normal floats per vertex are overwritten, inside the
   44 B record itself (sizes do not change → AFS slots do not break).
2. **The component order** is the detected one (pos from the bbox; normal
   identity). Do **not** apply the AWG0 sec34's swizzle (`[nz,-ny,nx]`): here
   `(nx,ny,nz)` is written as is.
3. **Normal**: rotate with `invW[:3,:3]` **without translation** and
   renormalise. The write order is `nrm[0],nrm[1],nrm[2]` (identity verified).
   There is no `y` negation.
4. **AWG14/15**: remember `r=2` (first record at `sec_rel+2`).
5. **n**: use `(ib−sec)//44` when it is exact; if not (e.g. AWG2 leaves 36 B at
   the end), use the **count of `FFFF` markers** at `mo` so as not to invent a
   partial record.
6. **Threshold**: if `d>THR` keep the original HD position and normal (avoids
   "stretching" in holes).
7. **Subsequent compression** (if packed as an override): LZX `/N:2048` and
   padding to the slot's `to_read` (AFS rules of `AGENTS §6`).
8. **Verification without opening the game**: export to OBJ with
   `awo_tools/awg_to_obj_b3.py` / `awg_cara_export.py` and check bounds/NaN
   before packing. A useful binary test: for each AWG, recompute the mean
   distance to the PS2 surface after the injection; it must be ≈0 (except the
   vertices discarded by the threshold).

---

## 8. FEASIBILITY

- **High**. The HD geometry is already <0.1 u from the PS2 surface under
  `world[32]/[23]/[30]`; the injection does not change sizes or topology, it
  only moves local positions/normals. It is the same **Path A** scheme that
  already works (injection into `sec34`), extended to the 16 AWGs.
- **Main risk**: the 6 face AWGs share a bbox and centroid; a blind projection
  may overlap layers (skin/eyes/mouth) on the same surface. Mitigation: keep
  the non-projected local component (or the normal) to keep the "layer" and
  project only along the tangent direction; and, if fine semantics are wanted,
  read each mesh group's **material index → `#AZT`** (pending, outside this
  analysis).
- **Pending to close face/teeth**: locate the teeth geometry (b36/b38) in the
  HD (probably in the `vb2`/AWG0 or in AWG16's `#AZT`) and map it separately.
- **Direct reuse**: the loop is practically a clone of `npm_surface_mapping` +
  `npm_boneaware_mapping` from `port_ps2_b3_inject.py`, applied to the 16 AWGs
  with their layout and their parent's `world` instead of to the AWG0's
  `sec34`.

---

### Cross-references
- `docs/07_ports/PLAN_PS2_B3/01_WEB.md`, `02_MODS_INVENTARIO.md`,
  `03_DOCS.md`.
- `docs/07_ports/SESION_INYECCION_2026-08-26.md` (Path A),
  `ESTRUCTURA_DIBUJO_HD.md`, `AGENTS §3.2/§3.4/§10`.
- Instruments: `awo_tools/awg0_export.py`, `awo_tools/awg_to_obj_b3.py`,
  `mod center hd/ports/port_ps2_b3_inject.py`.
- Temporary scripts of this analysis (`%TEMP%\opencode\phaseb\`): `ana.py`,
  `markers.py`, `detect2.py`, `final.py`, `report_data.py`,
  `step2.py`–`step8.py`, `table_out.py`.
