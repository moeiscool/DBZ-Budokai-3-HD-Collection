# Runtime HD textures (outer layer)

> State: **WORKING, opt-in (default OFF)**, cap **x3**. Cvar
> **`dbz3_texture_upscale`** (`1` = off, `2`/`3` = factor; requires a
> restart). In the launcher: "Texture enhancement (experimental)" with two
> levels (**Sharp** = x2 / **Very sharp** = x3); the advanced VRAM setting
> lives in the Dev tab. See §11 for the UX redesign and §12 for the video
> guard. D3D12 only (not available on the Vulkan/Linux/PS5 builds).

---

## 1. Goal

Double/triple/quadruple the resolution of the TEXTURES (not the render
resolution, which `draw_resolution_scale` already provides), **independently of
the window resolution**, with the **lowest possible performance cost**.

## 2. The two possible paths (and why one does not work)

| Path | Description | Result |
|---|---|---|
| **A. Bin override** | Rescale the textures inside the bin's own `#AZT` and serve it via the AFS override (virtual mid-insert). | ❌ **FAILS**: the game has its memory budget for the model/textures; when the `#AZT` grows the guest gets corrupted. |
| **B. Outer layer at runtime** | Do not touch the game: create the host texture at N× and fill it with a GPU upscale pass when loading it. | ✅ Implemented (D3D12). It is the correct path. |

### 2.1 Evidence of why Path A does not work (2026-09-18)

Tool used: `mod center hd/texture_upscale_b3.py` (AI upscale + rebuild of the
`#AZT`/`#AMB`; kept as a reference generator).

| Test | What it is | Result |
|---|---|---|
| `texai4x_327` | Krillin (entry 327) with x4 AI textures (AZT 391,680 B → 6,519,328 B) | **Crash** when entering Practice (before the select). |
| `_texai2x327` | The same with x2 (AZT → 1,559,040 B) | **Deformed model** (sheared torso, legs apart): guest memory overflow stepping on geometry/skinning. |
| `_pad327` | **Control**: ORIGINAL bin byte for byte, but with the override file padded to 200 KB (same AFS table growth) | **Perfect**. ⇒ The *virtual mid-insert* is not the problem; the problem is the **size of the textures** inside the guest's budget. |

⇒ Any pack that grows plays inside the game's own memory: **the override is the
wrong tool to scale textures**.

## 3. What is implemented (Path B, D3D12)

Files (also copied to `github/patches/rexglue-sdk/`):

- `include/rex/graphics/d3d12/texture_cache.h`
  - `GetTextureUpscaleFactor(key)` / `IsTextureUpscaled(key)`.
  - `GetDXGIResourceFormat/GetDXGIUnormFormat(TextureKey)` return the
    **decompressed** format when there is upscale (resource↔SRV↔copy format
    consistency).
  - Members `upscale_root_signature_`, `upscale_pipeline_` and the declaration
    of `InitializeTextureUpscale()` / `UpscaleTextureData()`.
- `src/graphics/d3d12/texture_cache.cpp`
  - Cvar `dbz3_texture_upscale` (1..4, `kRequiresRestart`).
  - **Eligibility** (conservative): 2D, `mip_max_level == 0`, no array, not
    `scaled_resolve`, no separate signed view, with a decompressed variant and
    dimensions ≤ `D3D12_REQ_TEXTURE2D_U_OR_V_DIMENSION / factor`.
  - `CreateTexture`: resource at **N×**, RGBA8 format,
    `ALLOW_UNORDERED_ACCESS`.
  - `GetLoadShaderIndex`: uses the **decompression** load shader.
  - Loading: the scratch buffer is filled at 1× as always and, instead of
    `CopyTextureRegion`, `UpscaleTextureData()` is called: a **bicubic
    Catmull-Rom** compute (16 taps) from the buffer (SRV `ByteAddressBuffer`) to
    the UAV of the N× texture. Once per texture load (not per frame).
  - `Initialize()` calls `InitializeTextureUpscale()` only if the cvar > 1; if
    the pipeline fails, the factor cancels itself (breaks nothing).
- `src/graphics/shaders/texture_upscale_cs.hlsl` + bytecode
  `bytecode/d3d12_5_1/texture_upscale_cs.h` (compiled with `fxc /T cs_5_1`).
  ⚠️ `dxcompiler.dll` is NOT deployed next to the exe, so it is compiled
  offline and embedded (do not use runtime compilation with DXC).

### 3.1 How to resume (steps)

1. `dbz3_texture_upscale = 2` in `dbz3_user.toml` (or expose it in the
   launcher).
2. Start and check in the log:
   `D3D12TextureCache: DBZ3 texture upscale pipeline ready (x2)`.
3. Compare 1 / 2 / 3 / 4 using the performance log (see
   `ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md`): FPS and `max_frame_ms`.
4. Pending / next steps:
   - Fine exclusion of problematic textures (UI/atlas/render targets) if
     artefacts appear when sampling them with texel offsets.
   - **Vulkan**: not implemented (same design, another backend).
   - Mips: only mip 0 today; adding a mip chain would reduce shimmering.
   - Evaluate the **AI assets** variant: the hook point
     (`UpscaleTextureData`) allows replacing the GPU pass with loading an
     AI-generated DDS (same benefit as an emulator pack, without touching the
     game). It is the highest-quality path; the GPU one is the "zero disk" one.

### 3.2 Known risks / limits

- **VRAM**: the target is RGBA8 (a UAV cannot be BC), so N× means up to ~16×
  the original VRAM at x4. Acceptable per character, watching the LRU
  (`texture_cache_memory_limit_soft/hard`).
- Only **single-mip DXT/BC textures** are scaled (characters/stages); UI and
  fonts **are not touched** (good: avoids breaking pixel-exact content).
- The quality is **magnification sharpness, not new detail** (it is not AI).

---

## 4. References

- Offline tool from attempt A: `mod center hd/texture_upscale_b3.py`
  (`--list`, `--scale`, `--skip-ai`, `--bin-out`).
- Evidence mods (disabled): `_pad327`, `_texr1x327`, `_texai2x327`,
  `texai4x_327` in `out/build/win-amd64-release/mods/`.
- Measurement of the real texture volume: 8,056 DXT3 textures / 182.3 MB of
  payload in `data_cmn.afs`; characters (bins 70-505) 3,558 tex / 95.9 MB
  (⇒ x4 = 1.53 GB of bitmap). Detail in the session history.

## 5. Verification state (2026-09-18) - NOTHING HAS BEEN SCALED YET

After the `upx=` counter (number of scaled textures, in the `dbz3: perf` line)
and the `upscale skip [...]` / `upscale ACCEPT` diagnostics:

- In **all** recorded sessions (including 6 with the x2/x3 pipeline
  initialised): **0 `upscale ACCEPT` lines and 0 occurrences of `upx=`** -> the
  upscale **has never been applied to a single texture**.
- The only ones queried so far were **1280x720 video/frontbuffer** textures
  (`no_uncompressed` / `scaled_resolve`); on the title no character DXT
  textures are loaded. Battle/select screens are needed.
- The user's visual test: **not applicable** — their session (`dbz3_090`,
  23:11) ran with the pipeline **NOT initialised** (x1), so there was nothing to
  compare.
- **Trap**: on exit, the launcher rewrites `dbz3_user.toml` and **deletes the
  cvars that only exist in the SDK** (`dbz3_texture_upscale`,
  `native_2x_msaa`, `dbz3_perf_logging`). To test it you must (a) expose it in
  the launcher (so it persists and can be toggled) or (b) re-apply the toml
  just before launching.

**Consequence**: the feature is implemented but **not validated end to end**.
For it to have visible value there are two paths: (1) finish the validation in
battle (and tune eligibility if the character textures do not get in either),
or (2) the **AI assets** variant (same hook point, real detail, not just
magnification sharpness).

## 6. IT WORKS (2026-09-18, night) - enabled from the launcher

**Careful**: the feature DOES work. All the conclusions of section 5 were
false: the game build **overwrote `rexruntime.dll` with the stale version**
from `rexglue/bin` (AGENTS section 7) -> the runtime lost `dbz3_perf_logging`
(the `perf fps` lines disappeared and it looked like a hang) and got back the
unconditional AFS log. The game never hung. ALWAYS verify after building the
game: `Select-String rexruntime.dll -Pattern dbz3_perf_logging` must say
PRESENT (size 10,870,272 B in baseline).

What was implemented:
- **Control in the launcher**, first tab (Video, next to the internal scale):
  `HD textures` with Off / x2 / x3 / x4 (cvar `dbz3_hd_textures`, persists in
  `dbz3_user.toml`). It is forwarded to the SDK cvar `dbz3_texture_upscale` at
  startup (requires a restart).
- **Generated mip chain**: the host resource is created at Nx with the same
  chain as the guest; level 0 is scaled with bicubic (Catmull-Rom) from the 1x
  buffer and the following levels are generated by averaging 2^level blocks of
  level 0 in the same shader (`texture_upscale_cs`, parameter `level`). The
  guest's packed mips are not read (complicated layout): they are regenerated.
- **Eligibility**: 2D, no array, not scaled-resolve, not signed-separate, with
  a decompressed variant and dimensions <= 16384/factor. Any number of mips is
  allowed.
- **Diagnostics**: lines `dbz3: upscale ACCEPT fmt=.. dim=.. WxH factor=..`
  (unique combinations) and `dbz3: upscale skip [reason] ...`; and in the
  performance line, `upx=<n>` = accumulated scaled textures.

Measured (RTX 4070 SUPER, opening, x3): 6 textures scaled (128x512, 128x128,
256x256, 1024x512, 1024x256, 256x128), **stable 60.0 FPS** with a single load
hitch at the start (`max_frame_ms` 724 ms in the first window; the cost is
generating the mips of the large textures). Still to be measured in battle.

Performance note: the initial hitch can be reduced by generating only the first
mip levels (or limiting the averaging block).

## 7. User's verdict and final state (2026-09-19)

In-game test with x3: **some improvement is noticeable in the intro**, but it
causes **continuous hitches** ("it affected the whole ecosystem"); the user asks
to leave it as **WIP and OFF by default**. Done:
- Launcher cvar `dbz3_hd_textures` with **default 1 (Off)** and the label "HD
  textures (WIP)" + an amber warning; the value is persisted and forwarded to
  the SDK cvar `dbz3_texture_upscale` at startup (requires a restart).
- The feature stays implemented and documented (sections 3 and 6).

Probable cause of the hitches (next steps to resume it):
1. **Cost of generating mips**: levels > 0 are generated by averaging 2^level
   blocks of level 0 in the shader; for large textures at a low level that is a
   very long loop (the opening showed a ~724 ms hitch). Mitigate: generate only
   the first levels (or limit the block size) and leave the high levels to the
   guest, or generate the chain in a separate step.
2. **VRAM**: the target is RGBA8 Nx (x3 = 9x texels, ~16x the guest's bitmap
   at x4) -> pressure on the cache's LRU -> more reloads/evictions and hitches
   when entering new zones. Watch `texture_cache_memory_limit_soft/hard`.
3. Possible underlying solution: precomputed AI assets on the same hook (lower
   cost per load, higher quality), or scaling only specific atlases.

## 8. FIXING THE HITCHES — mip block sample limit (2026-09-19)

**Diagnosis (root cause confirmed).** `texture_upscale_cs.hlsl` generated each
mip level by averaging the WHOLE `2^level x 2^level` block of level 0 in each of
the 16 Catmull-Rom taps: `16 * 4^level` reads IN SERIES per output texel. At
high mips the dispatch is left with very few threads (e.g. level 9 of a
1024x512 texture -> ~18 threads, each with 16 x 512x512 = 4.2M iterations
chained after a dependent accumulator) -> the memory latency is paid in full
and the frame rises to hundreds of ms. It is the cause of the "hitches when
loading new textures" being reported (and of the tester with an RTX 5090
seeing drops to 30 fps: the cost is not GPU-bound, a faster GPU does not help).

**Fix.** `XeLoadLevelTexel` samples a grid of at most `kXeMaxBlockSamples = 8`
per axis (uniform step over the block). For low levels (block <= 8) it is
EXACT; for high ones it is an approximation (high mips are blurry
minification, imperceptible). It reduces the work per thread from millions of
iterations to <= 64. Just recompile the shader and rebuild `rexgpu-xenos`:

```
fxc /nologo /T cs_5_1 /E main /Vn texture_upscale_cs /O3 ^
    /Fh bytecode\d3d12_5_1\texture_upscale_cs.h texture_upscale_cs.hlsl
```

**Measurement (RTX 4070 SUPER, `hd_tex=4x` + `3x` + MSAA + cap 60, config
identical to the tester's):**

| | windows | fps min | <58 fps | frames >100 ms | worst frame |
|---|---|---|---|---|---|
| Before (`dbz3_144`) | 32 | 41.7 | **10** | **14** | 905 ms |
| After (`dbz3_146`) | 73 | 52.6 | **1** | **1** | 634 ms\* |

\* the only remaining hitch was NOT from the upscale: `io SLOW 205127us` on
`adx_usa.afs` (a 205 ms disk read, an I/O problem unrelated to the feature).

With the fix the session scaled **1614 textures** (vs 274 before) without
upscale hitches. **Pending: user's visual validation** (the high mips are
approximate).

**FSR vs internal scale note (important for the launcher).** With
`present_effect=fsr`, the presenter only uses FSR EASU if the guest's
frontbuffer is SMALLER than the output (`src/ui/presenter.cpp:1054-1131`); if
the internal scale makes the frontbuffer >= the output, it falls back to
**CAS** (supersampling/downscale) and the FSR settings are inert. That is,
"internal scale 3x" improves the render (supersampling) but does not change the
displayed resolution; for FSR to really upscale, the internal scale must stay
below the output.

## 9. REAL SCOPE — ONLY DXT WAS BEING SCALED (and why it was not noticeable)

**Symptom**: the user (SSGPrinceVegeta) enabled HD Textures at 4x and "did not
notice any texture improvement", even though the hitches were gone after §8.
The logs explain it.

**Diagnosis with the instrumented catalogue** (`dbz3_147`, hd_tex=4x):

```
upscale ACCEPT fmt=19 ...      <- fmt=19 = k_DXT2_3 (DXT3)  -> was being scaled
upscale skip [no_uncompressed] fmt=6 ...   <- fmt=6 = k_8_8_8_8 (native RGBA8)
upscale skip [no_uncompressed] fmt=6 ... 1024x1024 / 1024x512 / 256x2048 ...
```

`GetTextureUpscaleFactor` required `host_format.dxgi_format_uncompressed`,
which **is only filled in for DXT** (to decompress). The **native RGBA8
textures (`fmt=6`)** -the LARGEST in the game: faces, clothes, stages- have
that field at `DXGI_FORMAT_UNKNOWN` and were ALL discarded. Result: ~650
textures were scaled (DXT3, almost always small UI/effects ones) and the effect
was barely noticeable on characters/stages.

## 10. EXTENSION TO NATIVE RGBA8 (2026-09-19, v1.2.6-WIP)

**Goal**: also scale the RGBA8 ones (`fmt=6`), which are the ones that really
make the visual jump.

**Requirement**: the upscale shader writes an RGBA8 UAV and reads the source as
`uint32` (`R|G<<8|B<<16|A<<24`). So only an explicit RGBA8 host format
(`R8G8B8A8_UNORM`) with a load shader producing RGBA8
(`bytes_per_host_block == 4`) is valid.

**Changes** (`texture_cache.{cpp,h}`):
1. `GetTextureUpscaleFactor`: if there is no `dxgi_format_uncompressed`, it uses
   `dxgi_format_unsigned` **only if it is `R8G8B8A8_UNORM`** and the standard
   load produces RGBA8. The rest is rejected (`not_rgba8` / `load_not_rgba8`)
   so as not to corrupt textures of other formats (`k_8`, `k_8_8`,
   `k_4_4_4_4`, `k_24_8`).
2. `GetLoadShaderIndex` and `GetDXGIResourceFormat`/
   `GetDXGIUnormFormat(TextureKey)`: a new helper
   `GetTextureUpscaleRgba8Format` returns the correct RGBA8 (decompressed for
   DXT, `dxgi_format_unsigned` for native RGBA8). **Bug fixed**: before, they
   returned `dxgi_format_uncompressed`, which for `k_8_8_8_8` is `UNKNOWN` ->
   the resource was created with an invalid format and the game spat out
   thousands of `Unsupported texture formats used in the frame: k_8_8_8_8
   resource`.
3. **Frontbuffer exclusion** (`swap_texture_key_`): `RequestSwapTexture`
   registers the presentation texture's key BEFORE creating it, and
   `GetTextureUpscaleFactor` rejects it (`swap_texture`). **Bug fixed**: without
   this, the 1280x720 swap texture was created at Nx (2560x1440) and the
   presenter failed to create the guest output ("Failed to create a command
   allocator" / 3840x2160) - the crash of the first attempt.
4. **Area limit** (cvar `dbz3_upscale_max_texels`, default 1 M texels =
   1024x1024): avoids scaling huge textures (2048x1024+ = 32 MB+ at x4 per
   texture), which would blow up VRAM. `0` = no limit. Exposed in the launcher
   as "HD texture size limit (Mpx)".

**Result (RTX 4070 SUPER, `hd_tex=2x`/`4x` + `3x` + MSAA + cap 60):**

| | accepted | errors | fps min | frames >100 ms | worst frame |
|---|---|---|---|---|---|
| DXT only (`dbz3_147`) | 12 types | 0 | 50.9 | 14 | 905 ms |
| DXT mips fix (`146`) | 12 types | 0 | 52.6 | 1 | 634 ms |
| **+RGBA8 (`152`/`153`)** | **41 types** | **0** | **57.6** | **0** | **55 ms** |

With `dbz3_154` (intro+menu+demo, 52 windows): **1515 textures** scaled, fps
min 57.4, **0 frames >100 ms**, 0 errors, 0 slow disk reads. VRAM holds (~3 GB
used of 12 GB). The `swap_texture` gate works (1 exclusion logged, frontbuffer
intact).

  **Pending**: user's visual validation (sharpness of characters/stages with
  `hd_tex=4x`). The high mips are still approximate (§8).

## 11. UX REDESIGN + x3 CAP (2026-09-19, user feedback)

User feedback: the feature "can be abused a lot without understanding it", the
"HD texture size limit (Mpx)" is incomprehensible for the average user and in
general the controls are not user-friendly. Changes:

- **Hard x3 cap** (before x4): the cvar `dbz3_texture_upscale` goes to range 1-3
  and the launcher only offers Off / x2 / x3. x4 multiplied VRAM and GPU with
  almost no visible gain over x3.
- **No "Mpx" in the normal view**: the area limit moved to the **Dev tab** as an
  advanced setting, in non-technical language ("Low/Medium/High: how much to
  spend"), explained by *what it does*, not by megapixels.
- **Result-oriented names**: the texture option goes from "HD textures (WIP)
  x2/x3/x4" to **"Texture enhancement (experimental)"** with **"Sharp (light
  use)"** and **"Very sharp (demanding)"**; the warning says clearly that it
  raises GPU consumption and that a restart is needed.
- **More conservative area default**: `dbz3_upscale_max_texels` goes from 1 M
  to **0.5 M texels** (1024x512 / 512x1024), which leaves out the large stage
  textures and cuts the default cost.
- **Quality presets reworded** (see §13): no longer called Low/Medium/High/
  Ultra, but **Performance / Balanced / Quality**, and **none raises the
  internal scale** (that was the other source of excessive consumption). The
  old names are accepted as aliases when loading.

## 12. VIDEO GUARD — cause of the brutal consumption (2026-09-19)

**Symptom**: with `hd_tex` enabled the GPU consumption shot up (80 % / 133 W /
3.1 GB on the dev's RTX 4070 SUPER, MSI Afterburner overlay capture) and
graphics glitches appeared, even with factor x2.

**Diagnosis**: the `upx` counter (scaled textures) reached **32182** in ~35 s
during the intro, versus ~700 in battle. The intro plays video (SFD) rendered
as a texture that is **rewritten ~60 times per second**; each rewrite marks the
texture as *outdated*, triggers a full load and with it **regenerates the whole
mip chain**. That is: the video was being re-scaled frame by frame, with no gain
at all (it is content that changes every frame).

**Fix** (`UpscaleBudgetAllows`): sliding window; if more than 24 upscales are
granted in 0.5 s, granting stops for 3 s (probably video). The decision is
**cached per key** (`upscale_granted_keys_`) because it must be stable: the
resource is created at Nx at the start and its reloads must keep treating it as
Nx (otherwise the Nx resource stays unfilled -> `device removed: 0x887A0001`).
The user does not have to understand anything: the feature slows itself down
when it adds nothing.

**Measurement** (`hd_tex=2x`, 0.5 M limit, 1x scale, same stretch of intro):

| | upx | GPU | power | VRAM |
|---|---|---|---|---|
| Without guard (`dbz3_160`) | **32182** | 80 % | 133 W | 3.1 GB |
| **With guard (`dbz3_162`)** | **237** | 39 % | 34 W | 1.95 GB |

With `hd_tex=3x` and real battle (`dbz3_163`): **689 textures**, 0 errors, 0
`device removed`, 60 FPS, GPU < 25 % / 35 W / 1.9 GB. The guard triggers once
per session (when passing the intro) and does not affect battle.

## 13. QUALITY PRESETS REWORDED (2026-09-19)

The presets (Video tab) go from `Auto/Low/Medium/High/Ultra/Manual` to:

| Preset | Scale | MSAA | Aniso | Effect |
|---|---|---|---|---|
| **Automatic** (recommended) | detects GPU (1x) | by tier | by tier | by tier |
| **Performance** | 1x | no | no | bilinear |
| **Balanced** | 1x | no | 4x | fsr |
| **Quality** | 1x | yes | 16x | fsr |
| **Custom** | whatever the user sets | | | |

Keys of the change:
- **No preset raises the internal scale** (always 1x). "Ultra" asked for 2x
  supersampling: exactly the case that multiplies the GPU for little benefit,
  so it was removed (whoever wants it raises the scale by hand). The "high"
  tier's cap was already 1x.
- The names **describe the result** the user is after, not an abstract level.
- The combo always shows **which values it resolves to** ("Active: Quality ->
  1x, MSAA ON, aniso 16, fsr") so that "Automatic" is not a black box.
- **Migration**: `low`->`performance`, `medium`->`balanced`, `high`/`ultra`->
  `quality` (aliases in `QualityConfigForPreset`; they stay in `.allowed()` so
  an old `dbz3_user.toml` does not invalidate the file).

## 14. BLURRED HUD FIX (2026-09-19b, user feedback)

**Symptom**: on the battle health bar, the "little squares" representing the
health segments came out **blurred/dirty** (user's capture, RTX 4070 S, 80 % /
133 W before the iteration). It was not the intro video: it is **HUD content**.

**Cause**: the health bar segments are **tiny quads with a small texture** (UI
glyphs: 1x1..16x16), and the pure **bicubic Catmull-Rom** kernel *rings*
(over/undershoot) on strong-contrast edges → a dirty halo perceived as blur.
Scaling an 8x8 texture adds nothing anyway.

**Fix (two layers)**:
1. **Minimum size** (`dbz3_upscale_min_size`, default **16**): textures whose
   width or height is smaller than 16 texels are not scaled. It removes the
   HUD/icon micro-textures at the root and leaves the useful catalogue intact
   (the accepted ones range from 16x32 to 512x1024). `1` = no minimum
   (advanced).
2. **Anti-ringing clamp** in `texture_upscale_cs.hlsl`: the bicubic result is
   clamped to the `[min, max]` of the kernel's 16 samples. It keeps the
   sharpness without the overshoot on edges (glyphs, letters, hard edges).

**Measurement** (`hd_tex=3x` + 0.5 M, Quality preset, `dbz3_170`): **0
errors**, fps min 54.7, upx 508, GPU **39 % / 33 W / 1.67 GB**. The shader
bytecode was regenerated with `fxc /T cs_5_1 /E main /Vn texture_upscale_cs
/O3 /Fh ...`.

**Pending**: user's visual validation of the HUD (it needs an on-screen window;
`long_run.ps1` moves it off-screen and `PrintWindow` does not capture the 3D).

## 15. UX — "so it cannot be abused" (2026-09-19b)

Principles applied to the feature (explicit user request):
- **Safe defaults**: off by default; max area 0.5 M; minimum 16; presets that
  do not raise the internal scale.
- **No jargon in the normal view**: no "Mpx", "factor", "texels". The main
  control is a combo with a **result** ("Sharp" / "Very sharp") and the
  technical settings live in the **Dev** tab, explained by what they do.
- **Hard x3 cap** in the cvar, not only in the UI (even if the toml is edited,
  there is no x4).
- **Visible cost**: when the enhancement is enabled an orange warning appears
  in the tab itself ("more detail at the cost of more GPU and VRAM use").
- **Presets named by intent** (Performance/Balanced/Quality) and an "Active:
  …" summary always visible so that "Automatic" is not a black box.
- **Invisible internal safeguards**: the video guard (§12) and the minimum size
  (§14) have no control: they stop misuse by themselves.

## 16. PERFORMANCE — THE COST IS SUPERSAMPLING, NOT HD TEXTURES (2026-09-19c)

**Confusion to resolve**: the user reported "it felt very smooth but it used
too much" (80 % / 132 W) with THEIR config. **That capture was from the old
version (x4 HD)**; with the current version, that consumption comes from the
**internal scale 3x**, not from the HD textures (which are OFF in their toml).

**Measured (RTX 4070 SUPER, battle, `dbz3_175..178`)**:

| Config | GPU | Power | VRAM |
|---|---|---|---|
| **1x + FSR** (native) | **22-23 %** | **29-30 W** | 1.35 GB |
| 3x internal (supersampling) | 51 % | 50 W | 2.9 GB |
| 3x + HD x4 (old version) | **80 %** | **132 W** | 3.1 GB |

**Conclusion**: `draw_resolution_scale` makes the **guest really render at
Nx** (real supersampling, `command_processor.cpp`), it is not a cheap upscale.
Each scale step costs ~double. At 1x the port uses **30 W / 23 %**, which is
what to expect from a native port at 720p. **There is no bug nor waste**: at 3x
the FSR/CAS is inert (frontbuffer >= output) and no extra pass is added
(verified in `presenter.cpp:1065`).

**Action (user's request: "keep 3x but warn loudly")**:
- A visible orange warning when `scale > 1` ("the GPU will work much
  harder...").
- **One-click "Back to native (1x)" button** (sets scale 1x and persists).
- Labels on the scale combo with the cost ("uses more GPU" / "much more").
- The preset tooltip clarifies that **none raises the scale**.
- The MSAA tooltip: moderate cost, can be removed if you raise the scale.
- `1x` is the default and the recommended one (marked in the option itself).

**The tester's (SSGPrinceVegeta) config is kept** in the local toml (`manual` +
3x, their original intention) but the launcher presents it with the warning and
the one-click way to lower it.

**FIX for out-of-range values**: the tester's toml had
`dbz3_texture_upscale = 4` (old value, no longer exists) and
`dbz3_hd_textures = 3` with `dbz3_skip_launcher = true`. An out-of-range value
**invalidated the WHOLE file** in the parser (`could not determine value
type`) and the user lost all their settings. The toml was cleaned up; remember
that the new ranges are HD textures 1-3, area 0..64M, minimum 1..4096. (Later,
an out-of-range cvar only rejects that cvar: AGENTS §3.0b.)
