# Texture packs (PCSX2 style)

> A **texture pack** replaces the game's textures with your own versions
> (usually AI-upscaled) **without touching files or the guest's memory**: the
> runtime intercepts each texture as it loads and, if the pack has a version
> of it, uploads that one instead of the game's.
>
> State: **Phase 1 (dump) + Phase 2 (loader) implemented and validated.**
> The loader supports DDS (DXT1/3/5 and uncompressed 32bpp) and PNG, with an
> x1..x4 factor and mip generation.
>
> **v1.2.8.1 — the dump also covers the HUD/UI formats**: besides the
> compressed ones (DXT1/DXT3/DXT5), the UNCOMPRESSED ones the game really uses
> are dumped (RGBA8, RGB565, RGB5A1, RGB655, RGBA4, L8, L8A8, RGBA1010102).
> Before, only the DXT ones were dumped and almost the whole HUD was missing
> from the dump.
> **Replaceable by a pack**: DXT1/3/5 and **RGBA8** (`k_8_8_8_8`); the 8/16-bit
> ones are dumped as a reference but their pack is **not** applied yet.
>
> Packs work on Windows (D3D12), Linux (Vulkan) and the PS5 build (Vulkan;
> copy the pack folder to `/data/dbz3/mods/`). The dev dump is D3D12-only.

---

## 1. How it works (summary)

1. The game has textures in memory. The runtime computes an **XXH3-64 hash**
   of each texture's original bitmap (the same data the `#AZT` stores).
2. A pack is a folder in `mods/` with files named with that hash.
3. When a texture loads, if its hash is in the pack, the pack's image is used
   (decoded to RGBA8) at the file's resolution (x1..x4) and the mips are
   generated. Otherwise the game's texture is used.

There is no file override or repacking: it is a host layer, like the
experimental "HD texture upscale" (with which it does **not** combine: the
pack takes priority).

## 2. Pack format

```
mods/
  MyPack/
    1F1ED618559910C0_256x1024_DXT3.dds     <- x2 upscaled texture
    0129771C81A045B0_128x128_RGBA.dds      <- x2 uncompressed
    04037CE1AFA993E9_1024x512_DXT3.png     <- PNG works too
    pack.json                              <- optional (metadata)
```

- Name: **`<hash:16 hex>_<Width>x<Height>_<suffix>.dds`** (or `.png`).
  - `hash` = the one from the dev dump (identifies the ORIGINAL texture).
  - `Width`/`Height` = the size of **this** image (the pack's).
  - `suffix` = free (`DXT3`, `RGBA8`, `PNG`...); informative.
- The **factor** is deduced: `factor = pack_width / original_width`, and it
  must be an integer, the same in X and Y, and between **1 and 4**.
- Supported formats: **DDS** (DXT1/BC1, DXT3/BC2, DXT5/BC3, or uncompressed
  32bpp) and **PNG**. Anything else is ignored with a warning in the log.
  Since the pack is always uploaded as **RGBA8**, the normal thing is to export
  PNG (so factor and content are free) or 32bpp DDS.
- `pack.json` (optional):
  ```json
  { "name": "My pack", "author": "your name", "version": "1.0",
    "description": "Faces and stages at 4x" }
  ```

## 3. How to create a pack (step by step)

### 3.1 Dump the game's textures (dev mode)

1. Launcher → **Development** tab → turn on **"Texture dump for mods (dev)"**
   and choose a folder (default `D:\Proyectos IA\DBZ B3 DDS`).
2. Restart and play. The DDS files + `index.jsonl` (hash, size, format, DDS
   suffix, mips) of each unique texture are written. The file name carries the
   format's suffix: `DXT1`/`DXT3`/`DXT5` (compressed) or `RGBA8`, `RGB565`,
   `RGB5A1`, `RGB655`, `RGBA4`, `L8`, `L8A8`, `RGBA1010102`.

Dump notes:

- **Unsupported formats**: skipped, leaving **one warning per format** in the
  log (`dbz3: volcado: formato k_24_8 (fmt=22) no soportado, texturas omitidas`).
  That way you can see at a glance what is pending (today: `k_DXN`/normals,
  `k_DXT5A`/alpha, `k_24_8`, 16_16_16_16...).
- **Video/render targets**: a texture whose content changes on every use (the
  intro video) is dumped at most **4 versions** and then no longer dumped
  (warning in the log). Without that cap the dump filled up with frames
  (measured: 4096 files / 1.4 GB in 5 min; with the cap, 194 / 51 MB).
- **Total limit**: `dbz3_texture_dump_max` (default 4096, `0` = no limit) in
  the Dev tab.

### 3.2 Convert and organise

```powershell
python awo_tools\texture_dump_import.py "D:\Proyectos IA\DBZ B3 DDS" "D:\pack_png" --afs us\data_cmn.afs
```

Converts the DDS files to PNG and places them in `<character>\texNN_WxH.png`;
those that match no `#AZT` go to `_unknown\`.

> **Black squares**: some of the game's textures have the alpha channel
> **all zero** (the game draws those textures ignoring their alpha, but a
> viewer shows them transparent, i.e. black). It is not a dump bug: the DDS is
> the game's exact data. If you want to see/use them, add **`--opaque-alpha`**
> and the PNG is written opaque (and `manifest.json` marks `alpha_all_zero`).
> In a pack it does not matter: the game already ignores that alpha.

### 3.3 Upscale

Run the PNGs through your favourite upscaler (waifu2x, Real-ESRGAN, Topaz...).
Keep **the same file name**; only the content and the size change.

### 3.4 Package

Create `mods\MyPack\` and save there the upscaled images **renamed to the pack
format**: `<hash>_<newWidth>x<newHeight>_<suffix>.dds` (or `.png`). The hash
and the factor come from `index.jsonl` / the original name:

```
original:  1F1ED618559910C0_128x512_DXT3.dds
x2:        mods\MyPack\1F1ED618559910C0_256x1024_DXT3.dds
```

### 3.5 Validate

```powershell
python "mod center hd\texture_pack.py" validar "mods\MyPack" --dump "D:\Proyectos IA\DBZ B3 DDS"
```

Checks names, that the file's dimensions match the name and, if you pass the
dump, that the hash exists and that the factor is valid (1..4).

### 3.6 Enable

Launcher → **Mods** tab: the folder appears as a mod (can be enabled/
disabled). The launcher detects it as a pack (it contains `.dds` with the right
name) and passes it to the runtime. Restart.

## 4. Rules and limits

- Only **2D single-slice** textures (no cubemaps/3D/arrays), like the HD
  upscale. The **frontbuffer** (the presented image) is never replaced.
- **Replaceable formats**: DXT1/DXT3/DXT5 and **RGBA8** (`k_8_8_8_8`). The
  8/16-bit formats (`k_8`, `k_8_8`, `k_5_6_5`, `k_1_5_5_5`, `k_4_4_4_4`...)
  **are** dumped (reference/editing) but their pack is **ignored**: their host
  resource is not RGBA8 and their swizzle is format-specific. It is the next
  pending step (see `docs/SESION_VOLCADO_FORMATOS_2026-09-23.md`).
- The pack **takes priority** over the runtime "HD texture upscale"; it is
  recommended not to turn both on at once.
- **Conflicts**: if two packs define the same hash, the first by alphabetical
  folder order wins; the runtime warns in the log.
- Packs are **not applied in disc (ISO) mode**: they need the extracted
  folder (like every other mod).
- The maximum factor is **x4**. A file whose size is not an integer multiple
  of the original is ignored (warning in the log).
- VRAM: the replacement is uploaded as **RGBA8** (4 bytes/texel). An x4 pack
  of a 1024x1024 texture is ~64 MB with mips; a complete x4 pack can ask for
  several GB. Start with x2 and with specific textures.

## 5. Diagnostics

In `logs\dbz3_NNN.log`:

```
dbz3: pack de texturas 'MyPack' -> 12 texturas
dbz3: pack 'MyPack' reemplaza 128x512 (fmt 19) -> 256x1024 (x2)
dbz3: pack 'MyPack' subido 256x1024 (10 niveles, 1441280 B)
```

- `packs cvar = ''` → the launcher detected no pack (check the folder).
- `no es multiplo de ...` → the file's size does not fit the original.
- `factor invalido` → the factor is not an integer or exceeds x4.
- `no se pudo decodificar` → unsupported format or corrupt file.

And from the dump:

```
dbz3: volcado de texturas activado en '...'
dbz3: volcado: formato k_24_8 (fmt=22) no soportado, texturas omitidas
dbz3: volcado: textura en 0x1D633000 (960x720, fmt=2) cambia de contenido en cada uso
      (video/render target): solo se volcaron 4 versiones
dbz3: volcado de texturas: alcanzado el limite de 4096 texturas
```

## 6. Files involved

- Runtime (SDK): `rexglue-sdk-0.10/src/graphics/dbz3_texture_pack.{h,cpp}`
  (a module COMMON to both backends: index, table of dumpable formats
  `Dbz3DumpFormatFor`, `Dbz3PackReplaceableFormat`, DDS/BC decoding) and
  `d3d12/texture_cache.cpp` + `vulkan/texture_cache.cpp` (hash, factor,
  upload, and the dev dump in D3D12).
- Launcher: `src/launcher/settings.cpp` (`RefreshTexturePacks`, cvar
  `dbz3_texture_packs`), `src/launcher/launcher_state.cpp` (Mods tab).
- Tools: `awo_tools/texture_dump_import.py` (DDS→PNG and organisation),
  `mod center hd/texture_pack.py` (validate/list).
- Runtime cvar: `dbz3_texture_packs` (folders separated by `;`).
