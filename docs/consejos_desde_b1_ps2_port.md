# ADVICE FOR BUDOKAI 3 HD — from the B1 HD project (17/08/2026)

> Transferable lessons from B1's PS2→HD port (native HD Chaozu validated,
> submesh data decoded, B2 PS2→HD 1:1 mapping) that should influence the
> `DBZ Budokai 3 HD Collection` project (adding IW/B2/B3 characters).

---

## 1. THE NATIVE SWAP IS THE PRIMARY ROUTE (validated in B1)

**Principle** (B1 lesson 9/10): the runtime draws the complete `#AWO`/`#AMB`
bin as it is (mesh group + IB + bones + UVs). It does not validate the slot.

**Consequence for B3**: if a character already exists in some HD bin of B3
(or B1), swapping in complete HD bins of the SAME character is the definitive
route — perfect render without converting geometry. In B1, the complete HD
Chaozu (bins 352+353, 3 AWGs = body+hands) in Tenshinhan's slot validated
this 100%.

**Application in B3**:
- For B3→B3 characters (new slots): use the character's HD bin as it is (the
  geom+tex pair of the same character).
- For B1→B3 (if the character exists in B1 HD): B3's `awg_to_obj.py` +
  `port_b1_to_b3.py` already cover the opposite direction.

## 2. FOR CHARACTERS NOT IN HD: REBUILD, DO NOT INJECT

**The most common mistake** (documented in B3's `RE_PROGRESO.md` §15-19 and
confirmed in B1): injecting PS2 positions over a host HD bin **deforms**
because the HD geometry is **re-topologised** (its own IB, reordered
vertices). Nearest-neighbour matching at 98% still deforms arms/hands/head/legs.

**The correct route**: rebuild the COMPLETE HD bin with the PS2 topology:
1. Parse the PS2 `#AMO0` (mesh parts, verts, rig → local coords).
2. Generate sec34 (44 B) + IB from the PS2 triangles.
3. Regenerate the arms (IB ranges per bone).
4. **Regenerate the submesh data zone** (descriptors per mesh part).

## 3. SUBMESH DATA: THE MISSING PIECE (decoded in B1)

In the HD AWGs, between the arms zone and sec34 there is a zone of **submesh
descriptors** (one per mesh part) with:
- transform/material floats
- `c08/c0C` = start/size of range A (contiguous between descriptors)
- `c10/c14` = start/size of range B
- the part's label (X??_BODY, ??_L01_LHAND...) + debug string `max N m`

**Risk**: copying the submesh zone from a template (without regenerating it)
over new geometry → **hang** (the runtime waits for data whose offsets no
longer match). To port, **generate one descriptor per PS2 mesh part** with
the new buffers' ranges.

## 4. B2 PS2 SKELETON = HD 1:1 (verified with Tenshinhan)

B2 PS2 uses the SAME `#AMO0`/`#AMG` format as B1 PS2, and the characters share
their skeleton with HD:

- **Tenshinhan B2 PS2** (entry 282 of data_cmn.afs): 14 mesh parts, 4427
  verts, 2944 skin. The 42 base labels (`TSH_BODY, TSH_WAIST, TSH_STMC...`)
  are **identical and in the same order** as HD TSH. Only the extra
  hand/face labels differ (24 more in PS2, which in HD live in separate AWGs).
- **Application in B3**: the same mapping applies for adding IW/B2/B3
  characters with a different costume: the base skeleton is the character's,
  only the mesh changes. The native HD bin of the same character can be used
  as the structural template (axes, arms, mesh headers, submesh data),
  replacing only the geometry.

## 5. GAMECUBE: NOT A SOURCE FOR MODELS

B1's GC ISO (`DragonBall Z - Budokai [NGC].iso`) uses `#ACO/#ACB/#AMB` formats
(`.act/.aco/.acm/.acb`) — different from PS2 `#AMO0` and HD `#AWO`. File names
do not correspond to characters (the "TSH" entry is Trunks). **Use only the
PS2 AFS files as a model source.**

## 6. RECOMMENDATION FOR THE B3 PIPELINE

1. **Character catalogue**: scan the PS2 AFS files (B1/B2/B3/IW) for
   `X??_BODY` labels (scanning the whole AMO, not just the start) → the same
   catalogue as B1's `launcher_mod_pipeline.py` but multi-game.
2. **Prioritise the native swap** for characters that exist in HD.
3. **PS2→HD port** only for characters without an HD version: complete
   rebuild (sec34+IB+arms+submesh data), using the HD bin with the same
   skeleton as the structural template.
4. **Validate with a test character** before automating (in B1, Tenshinhan
   B2 PS2 is the perfect test case: 1:1 skeleton, different costume).

## 7. REFERENCE FILES

- B1: `docs/re/SESION11_PORT_PS2_METODOLOGIA.md` (complete methodology).
- B1: `conversores/amo0_to_awo.py` (PS2 parser + repacking to extend).
- B1: `mods/test_chz_hd_completo_on_tsh/` (validated native swap).
- B3: `awo_tools/RE_PROGRESO.md`, `AWO_FORMAT.md`, `PLAN_AWO_DESDE_CERO.md`.
- B3: `mod center\B3_IW Model Converter\amb_model.py` (AMB↔AMO/AMT repacking).
