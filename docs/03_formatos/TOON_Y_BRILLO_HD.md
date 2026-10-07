# Toon shading of the HD characters and the HD rim light

RE from 2026-10-04/06 on the shader dumps (`dump_shaders` → `D:\DBZ3HD\shaders_dump`, with the
ucode disassembly) and calibrated against the 38 official icons and portraits. Equivalent offline
render: `mod center hd/model_render.py`.

## The toon shader (PS `5F27AACEB38B1088`)

```
u = ½·(N·L) + ½              (left = shadow, right = light)
v = c1.x                     (ramp row: chosen by the ALPHA of the base texture)
color = base − ramp[u, v]    (SUBTRACTION)
if base.a > c255.z  ->  color = base          ("unshaded")
color += c39.x · ( ½·(1 − |N·V|)²  +  step((1 − |N·V|)⁶ ≥ ½) )     (HD rim light)
```

- **It subtracts, it does not multiply.** The old formula in the notes,
  `base × (1 − ramp)`, only matches white bases. With coloured bases (the PSP
  ones) the difference shows.
- **AWG0 material** (0x50 B): `+0x00` diffuse RGB colour, `+0x30` base texture,
  `+0x34` 64×64 **ramp**. Texture `FFFFFFFF` = flat colour (Goku/Goten hair
  mass); flag `0x80000000` = translucent.
- **The ramp stores the complement of the tone**: human skin = bluish ramp,
  Ginyu = green ramp.
- **Ramp rows:** bands of 4 rows chosen by the base's DXT3 alpha (16 levels).
  Rows 56–63 are reserved (black/white); it is still to be confirmed whether
  the outline uses them.
- **Native models:** almost-white bases with the lines drawn in, the colour
  comes from the ramp; **alpha 0** everywhere except the whites of the eyes
  (alpha 255 = unshaded).

## Consequences for imported models

| Source | State | What to do |
|---|---|---|
| PSP (Shin Budokai, `psp_amo.py`) | 16-colour textures with the shadow **painted in** and **alpha 255 everywhere** → in game it looks **flat**, only with the rim light; worse normals (blotches in the rim) | alpha 0 + a ramp per material; smooth normals. **Careful:** the neutral ramp `psp_ramp.npy` was meant for multiplying: subtracted, it would darken the model |
| Heroes World Mission (`sdbh_model.py`) | coloured bases + their own toon ramps | use the template's **native ramps** (skin = Gohan's, clothes and hair = grey), alpha 0 on the bases and 255 only on eyes, mouth and teeth |
| PS2 community (`ps2hd`, `amo2awo`) | depends on the model | check the textures' alpha if it looks flat |

If a character comes out **black**: the ramp is too dark for a coloured base
(the subtraction saturates). If it comes out **flat**: high alpha in the base.

## HD rim light

- Its intensity comes from the vertex shader: **`o2.w = c39.x`**, only if the
  normal is non-zero (native models set a null normal on what is not lit).
  Every model VS has that line.
- **Native switch** (2026-10-06): the SDK scales `c39.x` when uploading it,
  only in shaders whose ucode contains `o2.___w, c39.x`.
  - Game variable: **`dbz3_hd_rim_light`** (0–1). SDK one: `dbz3_rim_light_scale`.
  - Launcher → "Native mods" tab → **"HD character rim light"** (checkbox + 5–100 %).
  - In game: quick menu **F1** → "HD rim light". Applies immediately.
- It affects every character equally (native and new): it is not a property
  of the mod.
- With bad normals, the rim light draws blotches: it is the fastest way to see
  whether an imported model needs smooth normals (set the rim light to 100 %).

## Checking without the game

`mod center hd/model_render.py` (icons and portraits of the new characters,
Mod Kit and Studio preview) still uses the **product** form
`base × (1 − ramp)`: exact with the native white bases, approximate with
coloured bases (PSP). Switching it to subtraction is pending.
