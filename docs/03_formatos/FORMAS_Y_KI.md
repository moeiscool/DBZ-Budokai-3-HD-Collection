# Forms, ki, physics and transformation of the new characters

`personaje.toml` keys added on 2026-10-06 (forms agent; full guide in
`D:\DBZ3HD\work\ghf\formas\CLAVES.md`). They are implemented by
`mod center hd/roster_build.py`, `mod center hd/capsulas.py` and
`src/roster_ext.cpp`. They are edited in the Mod Kit: **Characters →
"Forms, physics and appearance"** and in the capsule list (**"Set ki"**).

## Game rules (RE of B3, as adult Gohan)

- Transforming **does not spend ki**: it requires **having** N bars (1 bar = 1000; maximum 7).
- P+K+G jumps to the highest form for which there is enough ki and capsules.
- With less than 1 bar, a hit sends you back to the normal form.
- Each form has a ki level it drifts to while idle (`ki_base`).
- The runtime can only **reduce** the donor's forms (it copies each form's record).

## `[personaje]`

| Key | Value | Default | What it does |
|---|---|---|---|
| `formas` | 1..8 | the donor's | number of forms (no more than the donor) |
| `modelos_por_traje` | integer | 1 | models of each costume, in order (4 forms, 1 costume: `modelos = [normal, ssj, ssj2, pu]`) |
| `modelo_forma` | list | see note | the costume model each form uses, e.g. `[0, 1, 2, 3]`. Not needed if there are as many models per costume as forms |
| `ki_base` | list of bars 0..7 | the donor's | bars each form drifts to; adult Gohan `[3, 4, 4, 5]` |
| `fisica` | `"donante"` or ID | none | chain physics for the hair and the belt tails. **Without it new models stay rigid** |
| `transformacion` | `"donante"` | — | puts the donor's P+K+G (0x2E0/0x3E0, flash, shout) into the character's own moveset and **removes** Shin Budokai's down+E |
| `moveset` | list | the donor's | with a single file, every form uses it |

## Transformation `[[capsula]]`

| Key | Value | What it does |
|---|---|---|
| `tipo` | `"transformacion"` | |
| `forma` | 1.. | the form it leads to; requires the previous capsule in the list |
| `ki` | bars 0..7 | bars you must **have** (byte +15 of the `#SKC`, in tenths). Without the key, those of the donor's native capsule for that form (5 if it has none) |
| `equipada` | `false` | left out of the "Original" list (maximum 7 capsules) |

Command line (the Mod Kit uses it):
```
python roster_build.py capsulas --mod port_gohan_futuro --ki 6 5        # capsule 6 needs 5 bars
python roster_build.py capsulas --mod port_gohan_futuro --anadir "Super Saiyan" transformacion 1
```

## Chain physics (what the model needs)

- Belt tails: `*_LOBI1 → *_LOBI2 → *_LOBI3 (→ 4)` chained by **first child**,
  hanging from `*_OBI`; the same with ROBI. Hair (`HAIR1-3`) is optional: if
  missing, that chain is skipped.
- `WAIST`, `LLEG1`, `LLEG2` bones for collisions. They are looked up by
  **suffix**.
- The physics starts from the model's rest pose (PSP tails are horizontal:
  not checked in game).

## Example: Future Gohan (4 forms)

```toml
[personaje]
donante = 4
modelos = ["modelos/t1_normal.bin", "modelos/t1_ssj.bin", "modelos/t1_ssj2.bin", "modelos/t1_pu.bin"]
modelos_por_traje = 4
formas = 4
ki_base = [3, 4, 4, 5]
fisica = "donante"
transformacion = "donante"

[[capsula]]
nombre = "Super Saiyan"
tipo = "transformacion"
forma = 1
ki = 4
```

The importer (`importar.py`, sources `sb1`/`sb2`/`sdbh`) already writes
`formas`, `transformacion`, `fisica` and the transformation capsules with the
donor's capsule names when the Shin Budokai moveset is ported with
`sbport.py`.

Requires the exe with the new `roster_ext.cpp`; an older one ignores
`modelo_forma`, `ki_base` and `fisica` without crashing.
