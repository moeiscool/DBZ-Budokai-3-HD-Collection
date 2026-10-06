# Future Gohan at 100 %: exploration (2026-10-06)

Done by 5 agents in parallel. None of them opened the game or touched the
project. Each folder has its complete `informe.md`, the scripts and the
evidence images. The large extractions (ISO, ELF, caches) are in
`D:\DBZ3HD\explore\` and the complete copy of the 5 folders in
`D:\DBZ3HD\explore\informes_2026-10-06\`.

## Real state of the current port (`mods/port_gohan_futuro`)

- **Models** (`traje1-4.bin`): they come from our `awo_tools/psp_amo.py`
  applied to `BCGHFB00-03.amb` (Another Road, `data_btl_cmn.afs` 71-74).
  - B00 = Normal, B01 = SSJ, B02 = SSJ2 (slightly different hair), B03 =
    Potential Unleashed (carries the Z Sword).
  - Today they are 4 **costumes**: he always fights in normal form (`formas = 1`).
- **Moveset and camera**: the "community port" `ghf_365/367` is a byte-for-byte
  copy of Shin Budokai 2's `BCGHF.amb`, unconverted.
  - SB uses 20-byte AP lines and 160-byte HR blocks; B3 reads them as 16 B and
    128 B. That is why hits, damage, effects and voices are read misaligned
    from the 2nd line on.
  - It has no hyper mode (no ultimate) and its `#ACC` (cameras) is empty.
  - In SB, cond 0x0004 is a special; in B3 it is "transform".
- **Techniques**: `tecnicas.bin` is SB2's BSP run through `ps2hd` (it is
  commented out for a reason). `#AME` is another particle system, `#ASE` has
  0xB0 blocks (B3: 0xD0) and uses AST 0x15E/0x15F, which B3 reserves for ki
  blasts.
- **Shading**: all his textures have alpha 255, which in the shader means
  "unshaded". He comes out flat, only with the HD rim light, and his bad
  normals cause blotches.
- **Belt sash**: the belt tails and the hair in B3 move with chain physics (a
  per-model table in the XEX). `roster_ext.cpp` sets the new models' physics
  to 0 and their rest pose leaves the tails horizontal.

## New facts that correct earlier notes

- **Toon shader**: PS `5F27AACEB38B1088` **subtracts** the ramp
  (`color = base − ramp`) and a high alpha in the base means "unshaded".
  "base × (1 − ramp)" is only exact with white bases.
- **Ultimates**: they are P+K+G+E in hyper mode → HR type 3 → SPX slot 0, with
  their animations at 0x4A0+. SPX slot 20 is the throw (in all 38 characters).
  This contradicts part of the `b1port` note (0x4A0 = throws): it must be
  confirmed in game before rewriting that note.
- **`#SKC` capsules**: +15 = ki in tenths of a bar (fits 169 of 191); +14 = forms.
- **Transforming does not spend ki**: it requires having N bars (1 bar = 1000;
  max 7). P+K+G jumps to the highest possible form; with less than 1 bar, a
  hit sends you back to the normal form.
- **Beam struggle**: BCM bit 0x2000 + line `c0=0x68`; the response goes with
  cond2 0x4000 and `c0=0x69` (35 of 38 characters). Basis for the switch
  Discord asked for.
- **SB → B3**: B3 damage = 0.85 × SB (median of 8,847 hits).
  - Attack codes: 0x4xx/0x6xx → 0x2xx/0x3xx, transformation 0x500 → 0x2E0,
    throw 0x800 → 0x480.
  - Common animation store: 206 of 265 match (tables in
    `01_moveset/engine_map.json`, `global_map_sb*.json`, `t7_maps.json`).

## Decisions taken (can be changed)

| Topic | Decision | Reason |
|---|---|---|
| Forms | 4 (Normal, SSJ, SSJ2, Potential Unleashed), each with its Another Road model | The original game has them; the user asked for them |
| Ki | SSJ ≥4 bars, SSJ2 ≥5 (requires SSJ), Potential ≥6 (requires SSJ2); base level 4/4/5 | The same rules as adult Gohan in B3 |
| Name of the 3rd capsule | "Potential Unleashed" | In his future there is no Elder Kai |
| Ultimate | Giant beam = Super Kamehameha, with adult Gohan's cinematic | In SB2 it is an exact twin of adult Gohan's |
| Magenta wave | Strong special | A second cinematic is not worth it |
| Beam struggle | Yes, on the Kamehameha | Like adult Gohan |
| Technique names | Decode them from SB2's menu textures | They are official |
| Studio | Its own window launched from the Mod Kit; Blender optional via glTF | Blender 5.2.1 is already installed; glTF needs no add-on |

## Phased plan

1. **`sbport.py`** (generic converter for Shin Budokai 1/2 movesets):
   - AP 20 → 16 B and HR 160 → 128 B; damage × 0.85;
   - remapping of codes and of the common store;
   - graft hyper mode, Dragon Rush, throw and launches from the donor.

   Validated outside the game with the adult Gohan SB2/B3 pair, which shares hits.
2. **Forms**:
   - `formas = 4`;
   - a `ki` key per capsule in `roster_build`;
   - P+K+G and grafting of 0x2E0/0x3E0 from the donor with `csk_graft`;
   - `modelo_forma` in `roster_ext.cpp` for his own SSJ2.
3. **Polish the model**:
   - belt physics: copy the donor's or hang the tails at rest;
   - alpha 0 + a ramp per material, to get toon shading;
   - smooth normals;
   - AI ×2 textures with chaiNNer (already installed, AnimeSharp model), not
     exceeding ~800 KB per costume.
4. **Techniques**:
   - hybrid BSP: the donor's + SB's AST/ASE renumbered + textures;
   - recoloured particles;
   - hyper + cinematic ultimate;
   - beam struggle;
   - capsules with ki and forms.
5. **Studio, first version**: technique camera editor, with a timeline,
   templates (orbit, dolly, shake), toon preview and a round trip to Blender.
   An in-game capture session is needed first (camera orientation and
   mirroring, wait/clip relationship).
6. **Generalise `sbport.py`** to SSJ Gogeta, Vegito, Gotenks, Pikkon, etc.
7. **Optional**: a new model from Super Dragon Ball Heroes World Mission
   (`model/bcghf`). It has 3,449 triangles, a mouth, 7 faces, its own ramps and
   B3's skeleton, but does not bring the SSJ2. See `03_modelo/sdbh_vs_psp.png`.

## What to test in game (per phase)

- **Phases 1-2:**
  - the hits connect and take normal health;
  - with 3 bars he does not transform; with 4 he goes SSJ; with 5 from normal
    he jumps to SSJ2; with 6 to Potential;
  - a hit with less than 1 bar sends him back to normal;
  - the pause sheet says 4/5/6;
  - the CPU transforms.
- **Phase 3:**
  - the belt at rest, walking and in throws;
  - the toon shading, and that the model does not come out black;
  - the outline;
  - the HD rim light at 0 and at 1;
  - Future Gohan against himself with ×2 textures (memory).
- **Phase 4:**
  - specials S1-S6, hyper mode and the ultimate;
  - the beam struggle;
  - that the ki blast stays normal;
  - Edit Skills.
