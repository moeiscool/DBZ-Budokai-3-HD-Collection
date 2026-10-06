# Future Gohan (Shin Budokai) in B3 HD — state of the model, gap to the native HD ones and how to improve it

Exploration and reverse engineering, with no changes to the project and without starting the game (2026-10-06).
Folder: `scratchpad/explore/03_modelo/` (scripts + PNG). Large extractions: the exploration work folder (`03_modelo\`).

---

## 0. Summary

1. **Exact origin.** `traje1-4.bin` do NOT come from a community conversion. They are
   `awo_tools/psp_amo.py → convert_model()` applied to `BCGHFB00..03.amb`, which are entries 71-74 of
   `PSP_GAME/USRDIR/data_btl_cmn.afs` of the *Another Road* ISO. Reconverting gives **byte-for-byte
   identical** results. The moveset (`anm_forma1.bin`) and the camera come from `BCGHF.amb` (entry 70, via
   `sb_amm.py` + `ps2hd`). They are identical to `scratchpad/ghf/ghf_anm_hd.bin` and `ghf_cam_hd.bin` from
   the 04-10 session.
2. **Quality.** It is a PSP model passed through as is.
   - Mesh: 1505 triangles versus 2459 for HD Adult Gohan.
   - Textures: 3 of 16 colours (256², 256², 128²) with the shading painted in.
   - A "neutral" ramp and alpha 255 everywhere, so **in game it gets no toon shading**: the PS treats high
     alpha as "unshaded".
   - Body normals quite a lot worse than the native ones, which stains the HD rim shine.
   - No mouth (there are no M_* bones) and only 2 expression faces.
3. **"Belt strip": cause located.** The PSP belt tails come out **horizontally forwards** in the model's
   rest pose. In B3 the tails (and the hair) **are not animated**: they are moved by a chain physics
   simulation (an XEX table by model fid). `roster_ext` sets the physics pointer of new models to **0**, and
   SB's moveset only brings OBI rotation in **1 of 143** animations. Result: a rigid "board" coming out of
   the belt (see `cinturon_reposo.png`).
4. **A much better source on disk.** SDBH World Mission ships `model/bcghf`: Dimps' Future Gohan in
   EMD/EMB.
   - 3449 triangles, DXT1 textures up to 512² and **64×64 toon ramps** (the same concept as the HD).
   - Mouth with `f_jaw`/`f_*mouth*` bones, **B3's 7 faces** (L00, L01, L04, L05, L06, L09, L18) and a belt
     of 4 links per side.
   - Its skeleton is B3's with Z mirrored: same suffixes and same local axes.

---

## 1. What the 4 costumes contain (evidence)

Commands: `analiza.py` → `analiza_out.txt`, `analiza_trajes234.txt`; `draw_oracle.py` (lint OK).

| | costume1 (B00) | costume2 (B01) | costume3 (B02) | costume4 (B03) | HD Adult Gohan (225) |
|---|---|---|---|---|---|
| Bin | 351,616 B | 354,656 | 357,248 | 383,712 | 814,816 |
| AWO / AZT | 199,232 / 152,320 | 202,272 / 152,320 | 204,864 / 152,320 | 214,752 / 168,896 | 278,624 / 536,128 |
| Bones | 43 (GHF) | 44 | 44 | 43 | 54 (GHL) |
| AWG (body + variants) | 13 | 12 | 12 | 14 | 19 |
| AWG0 windows / indices | 1525 / 3932 | 1778 / 4034 | 1828 / 4010 | 1536 / 3950 | 2107 / 5100 |
| Triangles drawn | 1505 | 1539 | 1515 | 1511 | 2459 |
| Draws / materials | 8 / 3 | 8 / 3 | 8 / 3 | 8 / 3 | 20 / 15 |
| Textures | 256²,256²,128² + 64² ramp | same | same | + 1×128² | 20 (six of 256², ramps per material) |
| Face | NOR | **SS** (SSJ, blond) | **SS** (SSJ) | SENZAI | S00 + 5 expressions |
| Mouth / teeth | no (no M_*) | no | no | no | M_JAW, M_*MOUTH*, teeth |

- **The original PSP** (`BCGHFB00`): 43 bones, 13 AMG, an AMG0 of 2749 strip vertices and 1505 triangles.
  The textures are **4 bpp (16 colours)**. The converter loses no geometry: the 1505 triangles survive and
  the windows are welded 2749 → 1525. The `#RPT` child (2.8 KB) is discarded.
- **The textures** carry the colour and shading painted in (`psp_tex0/1/2.png`). The native HD ones are
  almost white (with lines) and the colour comes from the ramp.
- **Costumes 2 and 3 are the SSJ** (`trajes_ghf.png`). The "pending SSJ" is registering them as a form,
  not a costume. Probable pairing: (B00, B01) and (B03, B02). It must be confirmed with AR's table.
- **Label oddities.** Costume 2 uses `GHL_L00_LHAND/RHAND` hands (Adult Gohan's prefix) and costume 3 an
  `XGF_NLA` bone. Linking by suffix works, but the hand pose change (fist) of costume 2 must be watched in
  game.
- **Normals** (`render_normales.py`):

  | | Mean deviation versus the smooth normal | Normals > 45° | Inverted normals |
  |---|---|---|---|
  | GHF body (PSP skin normals) | 15° | 22 % | 5 % |
  | GHF knees, feet, hip and shoulders | 36-52° | | |
  | GHF head and hands (recomputed by psp_amo) | 0° | | |
  | Native HD | 4-9° | ~0 % | |

### Images
- `trajes_ghf.png`: the 4 costumes.
- `ghf_vs_ghl.png`: GHF versus HD Adult Gohan, body and face (`render_hoja.py vs`).
- `malla_densidad.png`: wireframe of GHF (1505), HD (2459) and SDBH (3449).
- `normales_rim.png`, with three columns: GHF as is, GHF with smooth normals and HD.
  - Row 1: Lambert lighting. The rectangular stains on the trousers are bad normals.
  - Row 2: approximate mask of the HD rim shine.

---

## 2. The HD's real shading (from the shader dumps)

From the shader dump folder (`shaders_dump`):

**Toon PS `5F27AACEB38B1088`:**
- `color = base − ramp[u = ½·N·L + ½, v = c1.x]`.
- If `base.a > c255.z`, `color = base` (unshaded).
- Then it adds the rim shine `c39.x · (½(1−|N·V|)² + step((1−|N·V|)⁶ ≥ ½))`. The constant c255.x = ½ is an
  assumption.

**VS `F3AC1AA2FE3EA253`:**
- The palette has 48 B per bone. The window's weight blends the bone with another transformation of the
  same palette entry.
- `o2.w = c39.x` only if the normal ≠ 0. The native ones set a null normal on what is "unlit".

**Consequences:**
- GHF's textures have **alpha 255 everywhere**, so in game **all of GHF comes out without toon shading**:
  only flat painted colour plus rim shine. The native ones use alpha 0, with alpha 255 only in the whites of
  the eyes.
- The ramp `psp_ramp.npy` was designed to multiply: it is white and grey, and white = no change.
  **Subtracted, it would turn the model almost black** if someone removed the alpha without changing it.
- The memory note "color = base × (1 − ramp)" is equivalent to subtracting only with a white base. The
  shader **subtracts**, and that matters for colour bases such as GHF's.
- **Unchecked:** the black outline. The native ramp reserves rows 56-63 (black/white). If the outline pass
  uses this same PS, GHF's alpha 255 would also remove its outline. See §6.

---

## 3. The "belt strip"

**Evidence** (`render_cinturon.py` → `cinturon_reposo.png`; the first two are the current state at rest,
front and side; the last two, with the fix):
- **GHF's rest pose.** `OBI` is at (0, 2.18, 1.26), in front. `ROBI1-3` and `LOBI1-3` have identity rotation
  and advance in **+Z up to z = 4.83**, i.e. horizontally forwards.
- **HD Adult Gohan** also has horizontal tails at rest (towards +X, with a side knot). Its moveset (234)
  **has no OBI or HAIR bones**: the physics moves them.
- **The physics is in the XEX** (decrypted US image):

  | Address | Content |
  |---|---|
  | `char96` + 8 (0x8234ABB8 + 96·ID) | List of 12 B models: `[fid, physics chains pointer, cache]` |
  | Adult Gohan's fid 225 | → 0x823389A0: 5 chains, HAIR1-3, LOBI1 and ROBI1 |

  Each chain record, 0x180 B:
  - Name of the root bone.
  - +0x1F: number of joints (3, i.e. chains of 4 bones).
  - Limits per joint in radians.
  - Damping and gravity.
  - Collision spheres WAIST, LLEG1 and LLEG2.
- **The bug.** `roster_ext.cpp` deliberately writes `+4 physics chains = 0` (lines ~311 and ~500) for the
  models of new characters and costumes, so **GHF has no physics**. Its tails stay at rest except in the
  single animation that carries OBI keys (1 of 143).

**Possible fixes:**
- **A (the simplest, no C++).** In the 4 costumes, rotate the local bind of `ROBI1`/`LOBI1` on the AWG's
  axis by about +80° around X (the tails hang). The windows are local to the bone, so the mesh follows.
  Also remove or rebuild the OBI tracks of that animation 136 of the ACM.
  - Checked offline with `altura.py`'s FK and the real rest pose: columns 3-4 of `cinturon_reposo.png`.
  - Rigid tails, no swing.
- **B (like the native ones).** A key in `roster.toml` to give the model a chains pointer: copy the donor's
  or write own records.
  - With the PSP model (3 bones per side) the donor's records expect 4: records with +0x1F = 2 must be
    written.
  - With the SDBH model (4 per side) Adult Gohan's record fits as is.

---

## 4. Improvement options, ordered by quality/effort

| # | Option | Gain | Effort | Limit / blocker |
|---|---|---|---|---|
| 1 | **Quick fixes on the PSP port:** belt (A), alpha 0 + ramps per material (body: subtracted grey; skin: warm ramp), smooth normals, AI textures ×2 | Medium: toon shading appears, the HD rim is clean, sharp lines | **~1 day** (changes in `psp_amo.convert_amt` and a normals pass; offline verification with draw_oracle/model_render) | The bin size must be respected (§5). The silhouette is still PSP. |
| 2 | **Rebuild from SDBH WM (`bcghf`)** | **High**: 3449 triangles, 512² textures, own ramps, scar, mouth and 7 faces, 4-link belt (donor physics) | **3-5 days**: EMD/ESK adapter in `b3_gateway`; Z mirror; HD ramp = 1 − XV ramp (flat colour per material); scale and hip with `altura.py`; hands | **Hands.** SDBH skins them to fingers and B3 uses rigid variants L01..L22. Options: bake the poses or reuse the PSP/GHL variants. The texture budget forces reducing some 512². Costumes b00, b01, b03 (whether there is an SSJ is unknown). |
| 3 | Kitbash with HD Adult Gohan pieces (hands and variants) | Low-medium | 0.5-1 day | GHF and GHL hands both have 187 windows (same lineage) and the wristband hides the seam. **Head and hair do not work**: GHF has another haircut and the scar. |
| 4 | Mesh subdivision or smoothing | Low (rounds but blurs the toon spikes) | 1-2 days | Only 1 bone + weight per window (with the parent): new vertices between non-parent bones crack. u16 IB; what is validated is 5148 windows / 8376 indices. **Not recommended.** |
| 5 | Hand repainting | High on faces/textures | Days of artist work | No tool: only worth it on top of option 2. |
| 6 | Runtime upscale (`dbz3_texture_upscale` ×2/×3) | Sharpness only (Catmull-Rom) | 0: it already exists and applies by itself to GHF's DXT3 | No new detail; optional for the user. |

**Other sources reviewed:**
- B3, IW and B2 do not have Future Gohan.
- Shin Budokai 1: its `data_btl_cmn.afs` has 206 entries, none GHF.
- Only AR (PSP) and SDBH WM (PC) exist.

**AI on disk** (without installing anything):
- `realesrgan-ncnn-vulkan.exe` **is not there** (`texture_upscale_b3.py` looks for it in
  `%TEMP%\opencode\realesrgan` or in `mod center hd\tools\realesrgan`).
- **chaiNNer** is installed (`%LOCALAPPDATA%\chaiNNer`). Its Python carries torch 2.7 cu128 and spandrel
  0.4.1.
- The user has upscaling models in a local texture-tools folder: 4x-AnimeSharp, 2x-AnimeSharpV4_RCAN,
  4x-UltraSharpV2, 4xNomos8kDAT, RealESRGAN_x4plus and others.
- Test done: `upscale_ia.py`, on the GPU, with a few seconds of compute → `upscale_ojos.png`.
  - **4x-AnimeSharp and 2x-AnimeSharpV4_RCAN** leave the lines clean.
  - Lanczos only smooths.
- In-memory mock-up: `mejoras_cara.png` / `mejoras_cuerpo.png`, with four columns:
  - A: as is.
  - B: AI ×2.
  - C: AI + smooth normals + alpha 0 + subtracted grey ramp.
  - D: native.

---

## 5. Format and engine limits that constrain each option

- **Bin size.** When the `#AZT` grows the guest's memory gets corrupted: Krillin ×2 (1.56 MB of AZT)
  deforms and ×4 closes (`docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` §2.1).
  - The native ones reach about 948 KB of bin (Goku 264) and 610 KB of AZT.
  - Safe rule: **each GHF costume ≤ ~800 KB and AZT ≤ ~600 KB**.
  - AI ×2 on body and head (512²) and 256² hands gives about 603 KB of AZT and ~800 KB of bin: at the
    native limit. Leaving the hands at 128², about 545 / 745 KB.
- **AWG0.** u16 IB (≤ 65535 windows); tested in game up to 5148 windows / 8376 indices. The palette TABLE
  must go right after the IB (`grow()` already does this). `B_count` = primitives. Lint:
  `draw_oracle.py`.
- **Skin.** 1 bone per window plus a blend weight in the VS. There are no 4-bone weights (SDBH has up to
  4): collapse to the dominant one.
- **Normals.** Null ones switch off the rim shine (`o2.w = 0`). The shine depends a lot on |N·V|, so bad
  normals show up as stains.
- **Base texture alpha.** High alpha = no toon shading (that is what all of GHF does today). The eyes need
  alpha 255; the rest, 0.
- **Ramp.** It is subtracted. SDBH/Xenoverse ones multiply (skin = a skin-colour gradient), so they must be
  converted: HD ramp ≈ the material's flat colour × (1 − XV ramp).
- **Physics.** The chains go by model fid and root bone name, and `roster_ext` nulls it in new models.
- **Mouth.** Without M_* bones there is no lip sync. The missing standard slots point to slot 12's marker
  (note of 04-10).

---

## 6. Recommended plan

**Phase 1: fix and polish the current PSP port** (~1 day, low risk, all offline except the final test).
1. Belt (fix A): rotate the bind of `ROBI1`/`LOBI1` in the AWG0 and in the auxiliary AWGs that carry them,
   in the 4 costumes, and clean the OBI keys of animation 136. Verification: FK with `posar.py` at rest,
   walking and hitting.
2. Toon shading: alpha 0 in the base textures (255 only in the whites of the eyes, detectable by colour)
   and a ramp per material.
   - Body: Adult Gohan's ramp 6, subtracted grey.
   - Head and hands: a skin ramp computed as `PSP_skin − target_shadow`.
   - Ramps per material: the bin already has 3 materials, no need to split draws.
3. Smooth normals welded by position in the skinned parts. It is what `psp_amo._smooth_normals` already
   does for the rigid ones.
4. AI textures: 4x-AnimeSharp with chaiNNer's Python, reduced to 512/512/128 (or 256), DXT3, without going
   over budget.
5. SSJ: register (B00, B01) and (B03, B02) as 2 forms (`formas = 2`, 2 models per costume), coordinated
   with the transformations report.

**Phase 2: rebuild from SDBH WM** (3-5 days, the best quality).
1. `--emd` adapter for `b3_gateway` (base: `sdbh_stats.py` / `render_sdbh.py`), with the GHL template
   (225). Z mirror; axes and suffixes already match (§7).
2. Ramps: 1 − XV ramp weighted by each material's flat colour. 512 textures → fit to the budget.
3. Faces L00..L18 to AWG variants; mouth and teeth to the template's M_* bones, so that lip sync works with
   the donor's mouth.
4. Hands: reuse the PSP/GHL variants (fast) or bake the finger poses (slow).
5. Physics: add a key such as `fisica = "donante"` in `roster_ext` that copies the donor model's +4 pointer
   (compatible 4-bone chains).

**What has to be checked in game** (in the background, with the save protected):
- Belt at rest, walking, on the heavy hit and in grabs (the GOK_ set).
- That toon shading appears and that **the model does not turn black** (if it does, the ramp is wrong).
- Black outline before and after changing the alpha (open, §2).
- HD shine with `dbz3_hd_rim_light` at 0 and 1.
- Select and battle with **GHF versus GHF** (two copies in memory) and ×2 textures: no deformation (the
  Krillin ×2 symptom).
- Hand pose (fist) of costume 2, which has `GHL_` labels.
- With SDBH: height (feet on the ground), elbows and knees, and lip sync.

**Risks:**
- Memory budget when the textures grow: the largest costumes must be measured.
- Exact alpha threshold and outline shape: deduced from the PS, unverified in game.
- Resemblance to the official look: the user demands a native look; compare with the official ones
  (match-official-assets).
- SDBH is a more modern model: it may look more "Xenoverse" than B3.
- Licence and origin: SDBH's assets come from another game, like the rest of the ports.

---

## 7. Loose technical notes

- **SDBH skeleton.** `bcghfb00.esk` carries 96 bones in B3's Z. The local positions and quaternions match
  GHL's when applying the mirror z → −z, q(x, y, z, w) → (−x, −y, z, w): larmrot, larm1, lhandrot, llegrot,
  lfoot1, obi and lobi1/2 checked.
  - B3 bones: `waist ... f_jaw, f_lmouth1/2, f_rmouth1/2, f_dteeth/uteeth, xghf_obi, xghf_lobi1-4,
    xghf_robi1-4`.
  - Fingers `LIndex1..` and faces `xghf_L00..L18_face`.
- **EMD (version 0x9300, LE).** Triangle lists; 48 B vertices (flags 0x207: pos, normal, uv, 4 bone
  indices and 3 weights). Each submesh carries 2 texdefs: [base texture, 64² ramp] of the EMB.
- **Moveset.** `anm_forma1.bin`: ACMs 1, 2 and 3 have 143, 3712 and 257 animations; only number 1 carries
  GHF_OBI tracks with data, and only in one animation.
- **Files in the work folder** (`03_modelo\`):
  - `BCGHFB00-03.amb`, `BCGHFM1.amb` (from the AR ISO);
  - `gohan_hd_225/228.bin` (decompressed);
  - `reconv_traje1-4.bin` (identical to the mod's).

**Scripts** (all in this folder, read-only on the project):

| Script | What it does |
|---|---|
| `analiza.py` | Bin statistics |
| `posar.py` | FK with an ANM |
| `render_cinturon.py` | Belt rest pose and fix A |
| `render_hoja.py` | Costumes and GHF versus GHL |
| `render_normales.py` | Lambert and rim shine |
| `render_mejoras.py` | Phase 1 mock-up (ramp subtracted like the PS) |
| `upscale_ia.py` | Upscale with chaiNNer's Python |
| `sdbh_stats.py`, `render_sdbh.py`, `render_malla.py` | SDBH model and mesh density |
