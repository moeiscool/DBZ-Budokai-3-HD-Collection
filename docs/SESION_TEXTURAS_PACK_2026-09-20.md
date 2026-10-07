# PCSX2-style textures — Phase 1: dev dump (2026-09-20)

> Goal: allow PCSX2-style "texture packs". This session implements **Phase 1
> (texture dump/census in dev mode)**, which also validates the identity by
> hash before building the pack loader. The loader (replacement) is Phase 2
> and is not done yet.

**Publication**: on 2026-09-20 21:54 the **Windows asset of the v1.2.6
release was replaced** (`DBZ-Budokai-3-HD-Collection-v1.2.6.zip`,
22,090,591 B, digest `10df4bce…`) to include it, together with the helper
`mod center hd/texture_dump_import.py`. It stays **off by default** (Dev tab).
The v1.2.6 Linux tarball does not change. `verify_release.ps1 -Version v1.2.6` = OK.

---

## 1. The idea and why the bin is NOT touched

- Overriding the bin (a bigger `#AZT`) **was already ruled out**: the guest
  has its own memory budget and when the `#AZT` grows it corrupts
  geometry/skinning (`docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md:24-36`). The
  pack **must not touch files**.
- The interception point is the same one the HD texture upscale uses:
  `D3D12TextureCache::LoadTextureDataFromResidentMemoryImpl`
  (`rexglue-sdk-0.10/src/graphics/d3d12/texture_cache.cpp`).
- The **only** decoding implementation (DXT→RGBA) is the GPU *load shaders*
  (bytecode, no source in the repo), and there is no convenient readback.
  That is why the dump **does not decode**: it writes the original compressed
  bitmap as is, which is exactly the same data as the game's `#AZT`, and the
  PNG conversion is done offline by Python (Pillow).

## 2. Runtime dump (SDK)

File: `rexglue-sdk-0.10/src/graphics/d3d12/texture_cache.cpp`.

- New cvars (category `GPU`):
  - `dbz3_texture_dump` (string, folder path; empty = disabled).
  - `dbz3_texture_dump_max` (int, maximum number of unique textures; 0 = no limit).
- `D3D12TextureCache::DumpTextureToDds()`:
  - Only acts with a non-empty `dbz3_texture_dump`.
  - **Does not run** if the HD texture upscale is on
    (`dbz3_texture_upscale > 1`): they must not overlap.
  - Formats: `k_DXT1`, `k_DXT2_3`, `k_DXT4_5` (and their `AS_16_16_16_16`
    variants). Other formats are silently skipped (to be added later).
  - 2D only (`k2DOrStacked`), a single slice, without `scaled_resolve`.
  - **Excludes the frontbuffer** (the texture the presenter produces).
  - Reads the guest bytes with `shared_memory().memory().TranslatePhysical()`
    (no GPU readback). If the texture is *tiled*, it linearises it with
    `texture_conversion::Untile`; it applies the *endian swap*
    (`texture_conversion::CopySwapBlock`) in both cases.
  - Deduplicates by **XXH3 of the linear bitmap** (`rex::XXHasher`/`XXH3_64bits`).
  - Writes `<folder>/<hash>_<W>x<H>_<FOURCC>.dds` (standard DDS, 128-byte
    header with a legacy FourCC) and appends a line to `<folder>/index.jsonl`.
- The call is inside the load loop, right after computing `guest_address`,
  only for the base level (`is_base && level_first == 0`).

## 3. Launcher UI (Dev tab) and the folder

- **🔴 Key discovery**: the GPU plugin (`rexgpu-xenos.dll`) has its **own cvar
  registry**, separate from the executable; `SetFlagByName` from the exe does
  **not** reach the plugin. The plugin does read `dbz3_user.toml` at startup,
  so **the TOML is the bridge**. That is why the launcher defines a cvar with
  the **same name** as the plugin's (`dbz3_texture_dump`, in
  `src/launcher/settings.cpp`): it is persisted to the TOML and the plugin
  reads it. *(Later corrected: the registry is shared and the plugin reads the
  launcher's value via `REXCVAR_QUERY` — see `SESION_FIX_VOLCADO_2026-09-21.md`.)*
- `src/launcher/settings.{h,cpp}`: `TextureDumpEnabled()`, `TextureDumpDir()`,
  `SetTextureDumpDir()`, `SetTextureDumpEnabled()` and `DefaultTextureDumpDir()`.
- **The folder does NOT live on the installation disk**: it can take hundreds
  of MB, so the user chooses it (`dbz3_texture_dump`) and it is remembered. By
  default `D:\Proyectos IA\DBZ B3 DDS` is suggested.
- `src/launcher/launcher_state.cpp` (**Dev** tab): checkbox
  "Texture dump for mods (dev)" + folder field + "Choose folder..." button.
  Needs a restart (the cvar is `kRequiresRestart`).
- i18n: new entry in `src/launcher/i18n.cpp`.

## 4. Importing the dump and organising it (offline)

Tool: `awo_tools/texture_dump_import.py`.

```powershell
python awo_tools\texture_dump_import.py <dump_dir> <out_dir> --afs us\data_cmn.afs
# options: --catalog "mod center hd\catalog_b3.cat" --bins 70-95 --limit N
#          --max-bins N  --no-match
```

- Converts each DDS to PNG (Pillow).
- If given `--afs`, it **identifies the character and the texture index** by
  scanning the catalogue's bins and matching the `#AZT` bitmap byte for byte
  (md5). It places the PNG in `<out>/<character>/<texNN>_<WxH>.png`; those
  that do not match go to `<out>/_unknown/`.
- Without `--afs` (or with `--no-match`) it groups by `<WxH>`.
- Writes `manifest.json` with the mapping.

This is what gives the **per-character/material folders**; the fine material
name (which mesh uses each texture) can be derived later by crossing the
texture index with the `#AWO`'s mesh part.

## 5. Collateral SDK change: duplicate `frame_cap`

When rebuilding the SDK a duplicate symbol `FLAGS_frame_cap_storage_` showed
up: the `frame_cap` cvar was defined **in the D3D12 presenter and in the
Vulkan one**, and on Windows both backends are compiled. The **definition**
was moved to `src/ui/presenter.cpp` (a file common to all backends) and the
two presenters now **declare** it (`REXCVAR_DECLARE(int32_t, frame_cap)`).
`SharedMemory::memory()` is exposed as `public` to read guest memory from the
texture cache.

## 6. Known limits (Phase 1)

- DXT1/3/5 only; the other formats (native RGBA8, DXN, packed…) not yet.
- Level 0 only (no mip chain).
- *Render-target* (dynamic) textures may be dumped with unfinished content;
  the hash dedupe makes it noisy but harmless.
- Matching against the `#AZT` depends on the guest bytes matching the file
  (linearised + endian); if a character does not match, it goes to `_unknown`
  (a sign that there is different tiling/endian to review).
- Dev-only and OFF by default.

## 7. Next phases

- **Phase 2 (pack loader)**: at the same seam, if the guest texture's hash
  matches a pack entry, upload the pack's DDS instead of the guest data. Start
  with the same size/format (trivial) and then HD (Nx resource).
- **Phase 3 (launcher + conflict)**: enable/disable a pack and **mutual
  exclusion with a strong warning** if there is both an HD texture pack and
  the runtime HD texture upscale (the dump's overlap is already avoided; the
  pack's is missing).

## 7.bis VALIDATION (2026-09-20)

With `dbz3_texture_dump = "D:\\...\\run4"` in the TOML and `skip_launcher`:

- **138 DDS written** (all DXT3, `fmt=19`), **3.4 MB**, within seconds of
  loading the intro/title. `index.jsonl` with 137 lines (hash, dims, format,
  `tiled`, mips, guest address). Valid DDS header.
- The importer converted 137 DDS → PNG without error.
- With `--afs us\data_cmn.afs --bins 70-110 --max-bins 25` (19 bins scanned):
  **7 textures identified** against the `#AZT` and placed in their character
  folder. Confirms the whole chain: dump (DDS) → match by bitmap hash → PNG
  organised by character.
- **C: untouched**: the whole dump goes to the chosen folder (D:).

## 8. Files touched

- SDK: `src/graphics/d3d12/texture_cache.cpp`,
  `include/rex/graphics/d3d12/texture_cache.h`,
  `include/rex/graphics/shared_memory.h`,
  `src/ui/presenter.cpp`, `src/ui/d3d12/d3d12_presenter.cpp`,
  `src/ui/vulkan/vulkan_presenter.cpp`.
- Launcher: `src/launcher/settings.{h,cpp}`, `src/launcher/launcher_state.cpp`,
  `src/launcher/i18n.cpp`.
- Tool: `awo_tools/texture_dump_import.py`.
- Regenerated DLLs: `rexruntime.dll` 10,910,720 B, `rexgpu-xenos.dll`
  6,246,400 B (copied next to the exe after building).
