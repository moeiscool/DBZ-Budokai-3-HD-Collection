# Session 2026-09-23 — Texture dump: HUD formats + RGBA8 packs (v1.2.8.1)

> Follow-up of **issue #11** ("Error al dumpear texturas"). The dump fix went
> into **v1.2.8**; when testing it, the reporter (`mellisxboxkp`) confirmed it
> now dumped and reported **two more things**:
>
> 1. "not every texture seen on screen is saved, only some, the dump seems to
>    skip most of the HUD textures except some fonts";
> 2. "some textures appear as a black square, which does not happen in PCSX2".
>
> This session fixes (1), explains (2) and extends packs to RGBA8 textures.
> Published in **v1.2.8.1**.

---

## 1. Why textures were missing (cause)

`Dbz3DdsFourCc()` (`src/graphics/dbz3_texture_pack.cpp`) only recognised
**DXT1 / DXT2_3 / DXT4_5**; for any other format it returned `0` and the dump
did a **silent** `return`. Since the game's HUD/UI/menus mostly use
**uncompressed** formats (`k_8_8_8_8`, `k_1_5_5_5`, `k_5_6_5`, `k_8`...), the
dump kept the DXT ones and a few fonts: exactly what the reporter described.

Moreover the dump **warned about nothing**, so it looked as if the game "did
not have" those textures.

## 2. Bit layouts (verified, not guessed)

An uncompressed DDS needs **bit masks**, and since the dump is the **RAW**
bitmap (byte for byte, undecoded), the masks have to be the **guest's**. There
is a trap: in Xenos several formats have **red in the low bits** (`k_5_6_5` =
R in 0-4), contrary to what the name suggests.

Verified against the original source (Xenia, `pixel_formats.xesli`, functions
`XePack*UNorm` and the conversions `XeR5G6B5ToB5G6R5`,
`XeR4G4B4A4ToB4G4R4A4`, `XeR5G5B6ToB5G6R5WithRBGASwizzle`):

| Format | fmt | DDS | bits | R | G | B | A |
|---|---|---|---|---|---|---|---|
| `k_8_8_8_8` | 6 | RGBA8 | 32 | `0x000000FF` | `0x0000FF00` | `0x00FF0000` | `0xFF000000` |
| `k_2_10_10_10` | 7 | RGBA1010102 | 32 | `0x000003FF` | `0x000FFC00` | `0x3FF00000` | `0xC0000000` |
| `k_1_5_5_5` | 3 | RGB5A1 | 16 | `0x001F` | `0x03E0` | `0x7C00` | `0x8000` |
| `k_5_6_5` | 4 | RGB565 | 16 | `0x001F` | `0x07E0` | `0xF800` | — |
| `k_6_5_5` | 5 | RGB655 | 16 | `0x001F` | `0x03E0` | `0xFC00` | — |
| `k_4_4_4_4` | 15 | RGBA4 | 16 | `0x000F` | `0x00F0` | `0x0F00` | `0xF000` |
| `k_8` / `k_8_A` | 2 / 8 | L8 | 8 | `0xFF` | — | — | — |
| `k_8_8` | 10 | L8A8 | 16 | `0x00FF` | — | — | `0xFF00` |

Compressed (unchanged): DXT1/DXT2_3/DXT4_5 (and their `_AS_16_16_16_16`
variants) with their FourCC.

⚠️ **Careful**: Xenia's (old) `texture_dump.cc` writes for `k_8_8_8_8` the
masks `R=0x00FF0000` (BGRA). **That is wrong** for this codebase:
`XePackR8G8B8A8UNorm` packs `R | G<<8 | B<<16 | A<<24` (byte 0 = R), which is
also what `texture_load_32bpb` (passthrough) and the already-validated HD
upscale of native RGBA8 assume. **Do not copy the masks from there.**

## 3. Changes

| File | Change |
|---|---|
| `src/graphics/dbz3_texture_pack.h` | `Dbz3DumpFormat` (suffix + DDS format) + `Dbz3DumpFormatFor()` + `Dbz3PackReplaceableFormat()` |
| `src/graphics/dbz3_texture_pack.cpp` | table of dumpable formats; `Dbz3PackReplaceableFormat` (DXT + `k_8_8_8_8`) |
| `src/graphics/d3d12/texture_cache.cpp` | `Dbz3WriteDds` writes a FourCC **or** masks (and fixes the header); `DumpTextureToDds` uses the table and the suffix; `LinearizeGuestTexture` accepts the new formats; **per-identity version cap**; unsupported-format warning; the pack accepts RGBA8 |
| `src/graphics/vulkan/texture_cache.cpp` | the same gates as D3D12 (`Dbz3DumpFormatFor` / `Dbz3PackReplaceableFormat`) |

### 3.1 DDS header bug

`dwCaps` was written at **+104**, which is **not** `dwCaps` but **`dwABitMask`**
inside `DDS_PIXELFORMAT` (which spans 76..107): `dwCaps` was lost **and** the
alpha mask was overwritten. Harmless for DXT (viewers ignore `dwCaps`), but
**critical** for the uncompressed formats. Now it goes at **+108** and the
masks stay clean. Along the way `DDPF_RGB` / `DDPF_LUMINANCE` are distinguished
(for `L8`/`L8A8`) and `DDPF_ALPHAPIXELS` is set if there is alpha.

## 4. The video flood (and the per-identity cap)

Once the uncompressed formats were accepted, the **intro video texture**
(`k_8`, 480x360 / 960x720, no mips) entered the dump. Since its **content
changes every frame**, the hash dedup did not stop it: **4096 files / 1.4 GB
in 5 minutes** (the 4096 limit was exhausted and almost all were frames).

Fix: a cap of **versions per IDENTITY** (guest address + format + size),
`kDbz3DumpMaxVersionsPerTexture = 4`. The hash dedup is kept (so a reused pool
address with other content **is** dumped), but the video churn is cut:

| | before | with the cap |
|---|---|---|
| files (5 min) | 4096 (limit) | 194 |
| size | 1.4 GB | 51 MB |
| video frames | 4080+ | 36 (9 identities x4) |

Warning in the log only once:
`dbz3: volcado: textura en 0x... cambia de contenido en cada uso (video/render target): solo se volcaron 4 versiones`.

## 5. The "black squares" (NOT a dump bug)

Checked on the real dump: the textures that look black are **DXT3 whose alpha
channel is ALL zero** (`00 00 00 00 00 00 00 00 | <valid colour>` in every
block). The colour is right; what is missing is the alpha. The game **draws
those textures ignoring their alpha** (that is why they look fine in game),
but a viewer shows them **transparent** → a black square. It does not happen
in PCSX2 because there the dump is of the PS2 assets, which are different.

The data is not touched (the dump is faithful). To see/use them,
`texture_dump_import.py` gains **`--opaque-alpha`**: if the DDS alpha is all
zero, it writes the PNG opaque and marks it (`alpha_all_zero`) in
`manifest.json`.

## 6. Packs: replaceable formats

The replacement always uploads **RGBA8**, so only formats whose **host
resource is RGBA8** qualify:

- **DXT1/DXT3/DXT5** (decompressed to RGBA8) — it already worked;
- **`k_8_8_8_8` (native RGBA8, identity swizzle)** — **new**: before, the
  pack's gate required DXT, so the HUD textures now being dumped could not
  have been replaced. It is the case that matters most.

The 8/16-bit formats (`k_8`, `k_8_8`, `k_5_6_5`, `k_1_5_5_5`, `k_4_4_4_4`)
are **dumped as a reference** but their pack is **ignored** (their host
resource is not RGBA8 and their swizzle is format-specific). Enabling them
needs an RGBA8 resource for the pack + an identity swizzle in the fetch's hot
path → **next step**, not a patch. The rule lives in
`Dbz3PackReplaceableFormat()` (common to both backends, so that Windows and
Linux behave the same).

## 7. Verification (measured)

Harness `%TEMP%\opencode\dump_test.ps1` (direct boot with
`dbz3_skip_launcher`, dump to `%TEMP%\opencode\dump_test`,
`dbz3_texture_dump_max=600`):

- **Dump (240 s, intro)**: **194 DDS / 51 MB** — 96 DXT3, **26 RGBA8**, 72 L8.
  Before (DXT only): 51 DDS. Log: `formato k_24_8 (fmt=22) no soportado` +
  the video-cap warning.
- **Pillow reads all three**: DXT3 128x512 RGBA, **RGBA8 128x1024 RGBA with
  real colours** (e.g. `(39,133,213)`), L8 960x720 mode L.
- **Pack end to end** (`mods/_packtest`, magenta DXT3 + green RGBA8):
  ```
  dbz3: pack '_packtest' reemplaza 128x512 (fmt 19) -> 128x512 (x1)
  dbz3: pack '_packtest' subido 128x512 (10 niveles, 523776 B)
  dbz3: pack '_packtest' reemplaza 128x1024 (fmt 6) -> 128x1024 (x1)
  dbz3: pack '_packtest' subido 128x1024 (11 niveles, 1048064 B)
  ```
  ⇒ the **RGBA8 (fmt 6)** pack is applied (new) and the DXT3 one is
  unchanged, with no errors or `Unsupported texture formats`.
- No regression: the DXT DDS is still byte for byte as before (same FourCC
  masks, same hash).

## 8. Pending

1. **Packs for 8/16-bit formats** (the HUD's case if it turns out to be
   `k_5_6_5`/`k_1_5_5_5`): an RGBA8 resource for the pack + identity swizzle
   in `GetHostFormatSwizzle` (hot path: measure first).
2. Formats not dumpable yet: `k_DXN` (normals, BC5), `k_DXT5A` (alpha, BC4),
   `k_DXT3A`, `k_24_8` (depth), `k_16_16_16_16`.
3. Confirm with #11's reporter that the HUD now shows up in the dump.

## 9. Files touched

- `rexglue-sdk-0.10/src/graphics/dbz3_texture_pack.{h,cpp}`
- `rexglue-sdk-0.10/src/graphics/d3d12/texture_cache.cpp`
- `rexglue-sdk-0.10/src/graphics/vulkan/texture_cache.cpp`
- `awo_tools/texture_dump_import.py` (`--opaque-alpha`)
- `docs/02_mods/PACKS_DE_TEXTURAS.md`
- Canonical DLLs: `rexgpu-xenos.dll` **6342656 B**, `rexruntime.dll` 10910720 B.
