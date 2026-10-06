# Session 2026-09-24 — The texture upscale stops sinking the FPS (v1.2.8.2)

> Follow-up of the reports of **FPS drops with "Texture upscale
> (experimental)"** on (SSGPrinceVegeta's logs, RTX 5090/9950X3D, in
> `Logs SSGPrinceVegeta/parte 4/`). The feature's path:
> `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md`.

## 1. The report

- `parte 4/dbz3_036.log` (launcher) and `dbz3_037.log` (game). Active config
  (read from the startup line itself): `internal_scale=3x`, `msaa=true`,
  `hd_tex=3x`, `vrr=true`, `fsr=quality`, `aniso=5`, D3D12 backend, audio
  output VB-Audio Virtual Cable. The area hook accepts `1024x1024` and
  `2048x512` → `dbz3_hd_texture_max_texels` = **1048576 (High)**, not the default.
- Symptom: the presenter (`[core]`) stays at 60, the guest swap (`[gpu]`)
  starts at ~59 and **degrades down to 31** as the `upx` counter rises
  (16→48→71→109→310→534→…→**665**), stays flat at **~31 fps with
  `max_frame_ms` 34-38** (narrow distribution: no spikes) and **recovers to
  ~55 fps after losing/regaining focus** (22:02:53-57) without `upx` changing.
- `parte 3` (19/09, `hd_tex=4x`): FPS **oscillating 30/60**. `parte 2` (v1.2.1)
  predates `upx`/`fg=`. ⇒ the phenomenon is **not a regression** of a version.

## 2. The reproduction (and why it was not the load)

Three local sessions with **the reporter's exact configuration**
(`dbz3_hd_textures=3`, `dbz3_hd_texture_max_texels=1048576`, 3x scale + MSAA)
on an **RTX 4070 SUPER** (slower than the 5090):

| Run | fps min/max | final `upx` | `fmt=22` (3D scene) |
|---|---|---|---|
| `dbz3_248` | 59.8 / 60.2 | 48 | no |
| `dbz3_249` | 59.6 / 60.1 | 194 | no |
| `dbz3_250` | 59.2 / 60.2 | 328 | no |

- **It does not reproduce**: a constant 60.0 fps with `max_frame_ms` 19-20.
- Texture cache *thrash* ruled out: forcing
  `texture_cache_memory_limit_soft=128; _hard=256`, `upx` rises 153→163 at
  ~1.5/s and stays at **60.0 fps**.
- ⚠️ **Local runs never reach the 3D demo** (`fmt=22`, depth resolve, which
  the reporter's log does have): key automation (`tools/press_key.ps1`) **does
  not navigate** the game's SDL3 menus. The scene comparison is not 1:1; what
  is comparable is the feature's **mechanics**.

## 3. The cause

`D3D12TextureCache::LoadTextureDataFromResidentMemoryImpl`
(`src/graphics/d3d12/texture_cache.cpp`): when the load brings level 0, it
regenerates **the whole mip chain** with `UpscaleTextureData` level by level.
Each level costs **two barriers + two single-use descriptors + a pipeline
change + a dispatch**, all **serial** inside the command list.

There are textures the game **rewrites every frame** (intro video, effect
render targets). With the feature on, 12 levels are regenerated per reload ⇒
**~1 texture re-upscaled per frame** (the log's `upx`) ⇒ a **command/CPU** cost,
not a GPU one:

- It explains why **a more powerful GPU does not help** (and why it does not
  show in GPU usage or VRAM).
- It explains the flat `max_frame_ms` (uniform cost, no spikes).
- The existing guard (`UpscaleBudgetAllows`) bounds the **granting of new
  textures** (24 per 0.5 s + a 3 s pause), but **did not touch reloads** of an
  already-granted key, which is the reporter's case (repeated identities).

## 4. The fix

When loading level 0, a **complete** fill is distinguished from a **cheap** fill:

1. **Base-only reload on the SAME resource** (`load_mips == false` and the
   chain was already generated on that `ID3D12Resource*`).
2. **Chronic reload**: the same identity 4+ times in 1.5 s (per-key counter).

In both cases the texture is **dynamic** and only **level 0** is regenerated:

- The visible image is exact (level 0 is the complete texture).
- The mips are kept from the last complete generation (they only affect
  minification; a one-frame lag is not visible).
- `upscale_chain_resources_` guarantees that, **after an eviction** (new
  resource, uninitialised mips), the whole chain is regenerated.
- **Static** textures are still upscaled with **their whole chain**, as
  before. A warning is logged once per identity
  (`dbz3: upscale textura dinamica WxH fmt=F mips=M - solo nivel 0 por recarga`).

⚠️ **The factor of an already-upscaled texture cannot be "un-granted"**: the Nx
resource exists and the upload path reads the same factor (if it changed, 1x
would be filled into an Nx resource → garbage). The **size** decision remains
stable per key; what becomes cheaper is the **fill**.

## 5. New diagnostics in the `perf` line

```
dbz3: perf fps=60.0 frames=300 window=5.00s max_frame_ms=20.1 fg=1
       cfg=scale:3x3 msaa:true hdtex:3 area:1048576 min:16 aniso:5 upx=137 upx_dyn=0 texload=602
```

- `cfg=` the settings that weigh most (internal scale X/Y, MSAA, texture
  upscale, maximum area, minimum size, anisotropic), read from the **shared
  registry** (`rex::cvar::GetFlagByName`) every 5 s window.
- `upx_dyn=` dynamic-texture reloads regenerated at level 0 (cumulative).
- `texload=` texture loads in the window. In the local intro it comes out at
  **600-1055 per 5 s (120-210/s)**: the game is very aggressive texture
  *streaming*, which is why the feature has to be cheap on reloads.

With this, **a single user log** tells what is configured and whether the game
is re-upscaling dynamic textures: the case can be closed in one round.

## 6. Validation

- **Smoke test of the new path** (temporary build with the threshold at
  `count >= 1`, so that *every* texture with mips ran it): `upx_dyn` = 114, a
  per-identity warning per texture, **0 errors**, 60 fps, `max_frame_ms` 19-20.
  It proves the level-0 fill breaks neither the resource nor the presenter.
- **Final build** (`count > 3`) with the reporter's config: 3 sessions,
  **60.0 fps**, `max_frame_ms` 19.2-20.4, **0 errors/warnings**, `upx_dyn=0`
  (the reporter's scenario is not reached locally), `texload` 600-1055/5 s.
- `verify_release.ps1 -Version v1.2.8.2` = **VERIFICACION OK**.

## 7. Release

- `src/version.rc` → `1.2.8.2` (same convention: a follow-up of the same PATCH
  bumps BUILD). **Latest** release with a Windows zip (**22,147,958 B**) + the
  CI's Linux tarball.
- Canonical DLL: `rexgpu-xenos.dll` **6,346,240 B**, `rexruntime.dll`
  **10,910,720 B** (SSSE3 baseline).
- PortForge: `defaultVersion 1.2.8.2` (visible 1.2.8.2 / 1.2.8.1 / 1.2.8;
  1.2.7 goes to the archive in `portforge/archive/`).
- SDK patches updated (`patches/rexglue-sdk/.../{texture_cache.cpp,
  texture_cache.h,d3d12/command_processor.cpp}`); they are D3D12 files, so the
  Linux (Vulkan) build does not change functionally.
- `github/RELEASE_README.md` + `release-stage/RELEASE_README.md`: new v1.2.8.2
  section.

## 8. Pending

- **Confirm with the reporter's log** (turning on "Performance logging"): if
  `upx_dyn` rises and the FPS are fine → closed; if `upx_dyn` rises and it is
  still slow → the cost is in level 0 and the dispatch would have to be made
  cheaper; if `upx_dyn=0` and it stays at 31 → **another cause** (ask for
  CPU/GPU: clocks, temperatures, load %, and the `dbz3_user.toml`).
- Reaching the **3D demo** locally is still not possible by automation (the
  keys do not reach SDL3): if needed, it has to be done by hand.
- The local 3D demo measured 60 fps at 2x/3x + MSAA (2026-09-19, without
  `hd_tex`), so measuring `hd_tex` in the demo with the fix is still pending.
