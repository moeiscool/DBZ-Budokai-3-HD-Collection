# PS2 → B3 HD candidate matrix

> Preparation of the next phase: 2026-09-08. No new bin or mod has been
> generated. The selection is based on the rig, not on visual resemblance.
> **Babidi is the technical guinea pig**: he is neither playable nor a slot
> candidate; he is installed temporarily over Krillin to validate the converter.

> **Source blocker found 2026-09-08**: the `data_cmn.afs` files available
> under `ps2_games/Budokai 3 Greatest Hits` and `ps2_games/Budokai 2` return
> big-endian `#AMB/#AWO` entries, not PS2 LE `#AMO0/#AMG`. Do not use those
> entries as a PS2 source until the correct AFS is located/examined.

## Goal

First solve a **structurally 1:1** case to validate the converter. Babidi is a
technical control over Krillin, not a new selectable character. The first
playable model will be a later, separate phase.

## Candidate order

| Priority | Candidate | Origin | HD template | Reason | State |
|---:|---|---|---|---|---|
| 1 | Babidi | B3 PS2 Greatest Hits | HD Babidi, entry 96 → test over Krillin | 1 AWG/41 bones; non-playable control | Rig to be verified |
| 2 | Bulma | B3 PS2 Greatest Hits | HD Bulma → test over Krillin | 2 AWGs; technical control | Rig to be verified |
| 3 | Tien with cape | IW → B3 PS2 (`Tien (With Cape).amo`) | HD Tenshinhan, entry 400 | 42 common labels in the same order; 10 extra cape bones | **Passes the 1:1 base rig** |
| 4 | Pan | Infinite World | compatible HD host | New-content candidate | Do not commit without a scan |
| 5 | Super 17 | Infinite World | compatible HD host | Existing moveset | Do not commit without a scan |
| X | Pikkon | Infinite World | Krillin/KLL | 58 bones and `SKIRT`, different PKH rig | **Discarded** |
| X | Janemba | Infinite World | Krillin/KLL | Incompatible retargeting and structure | **Archived/discarded** |

## Rig acceptance criterion

Before touching geometry, the candidate must produce a report with:

- normalised bone labels;
- number of bones and AWGs;
- hierarchy and bind matrices;
- 1:1 correspondence by label and by order;
- list of bones used by vertices and by `vb2`;
- no extra bones without an HD destination.

The minimum criterion for the first validator is **same labels, same order and
same bone numbering**. A non-1:1 manual mapping is reserved for a later
retargeting phase.

## Test protocol

1. Extract the candidate's PS2 bin from the reference AFS.
2. Run only `port_ps2_b3_extract.py` and keep the JSON.
3. Compare the rig report against the target HD bin.
4. Abort if the rig is not 1:1; do not try to fix it with geometry.
5. Generate bone-local geometry with the existing pipeline.
6. Rebuild the draw structure only when the pool and its references are
   documented; do not reuse descriptors by index without proof.
7. Pack a self-contained bin into an isolated test slot.
8. Run `port_ps2_b3_verify.py` and export an OBJ before the game.
9. Test with a single active mod, the bin's hash recorded and a disposable
   save profile.
10. For Babidi/Bulma, validate loading and rendering on the host; do not
    require select, autonomous fighting or saving.
11. For the first later playable candidate, validate select, loading,
    fighting, animation, transformations and rematch.

## Diagnosis by layers

| Result | Probable interpretation |
|---|---|
| Wrong JSON | PS2 parser/FaceType/rig |
| Wrong OBJ | Geometry, matrices, normals or indices |
| OBJ correct, amorphous in game | Pool/mesh-ref references, zones, arms or descriptors |
| Model correct, animation wrong | Rig/arms/bone order |
| Fighting correct, HD face/legs | `vb2` not converted yet |
| Crash on load | AFS, LZX, padding, self-contained bin or descriptor |

## Decision

Injection over another character's template remains a local-improvement
technique, not a general port. The first technical attempt will be Babidi
over Krillin if he passes the 1:1 scan. Only afterwards will a new playable
IW character or a candidate with its own identity be studied.

## Result executed 2026-09-08

The first real PS2 candidate available was not Babidi, but
`modding resources/All Character Models from IW into AMB format` /
`modding resources update 2/MOD EJEMPLO/Tien With Cape/IW/Tien (With Cape).amo`.

Extraction performed:

```text
PS2: n_bones=52 parts=15 verts=4565 skinned=3346
```

Comparison against HD Tenshinhan entry 400:

- HD: 42 bones.
- PS2: 52 bones.
- All 42 HD labels are present in PS2.
- The 42 common labels keep the same order.
- The 10 PS2 extras are `MANT`, `RMANT` and `LMANT`.
- Verdict: **1:1 base rig approved**, with isolatable extra accessories/cape.

Next step: convert the geometry of Tien with cape using HD Tenshinhan as the
template, initially keeping only the 42 common bones and treating the 10 cape
bones as a separate part. Do not install yet.
