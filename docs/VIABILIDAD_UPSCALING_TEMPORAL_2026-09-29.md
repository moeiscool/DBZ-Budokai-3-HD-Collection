# Viability of temporal upscaling in dbz3 (DLSS / DLAA / FSR3 / Frame Gen)

> Research 2026-09-29, prompted by two sibling recompilations:
> [`zolaware/reblue`](https://github.com/zolaware/reblue) (Blue Dragon) and
> [`freefrank/LostOdysseyRecomp`](https://github.com/freefrank/LostOdysseyRecomp).
> **Short conclusion**: temporal DLSS/DLAA/FSR3/Frame Gen are **not viable
> today** in dbz3 without building the temporal contract (colour at internal
> resolution + depth + motion vectors + jitter) and, in practice, without
> owning the GPU layer. What is usable from those repos has already been
> adopted (DRED + gamecontrollerdb) or remains a candidate (§6).
>
> **Later update:** after this study the project started building
> `rexgpu-xenos` from its own SDK branch and v1.4.2 shipped DLSS/FSR 3 as a
> beta (`docs/PLAN_1.4.2_DLSS_FSR3.md`). None of it applies to the PS5 build.

## 1. Base of each project (why it is not a 1:1 comparison)

| | dbz3 (this project) | reblue | LostOdysseyRecomp |
|---|---|---|---|
| Recompiler | ReXGlue 0.10 | **ReXGlue 0.10** | XenonRecomp + XenosRecomp |
| GPU layer | `rexgpu-xenos.dll` (Xenia), **not its own** | **its own** (`src/gpu/*`, a fork of `plume`) | **its own** (`gpu/*`, `plume`) |
| DLSS / DLAA | — | — | **Yes** (NGX 310.9.1: SR + DLAA) |
| FSR | spatial **FSR1** (EASU/RCAS) + CAS in the presenter | — (MSAA/SSAA only) | FSR 3.1 (upscaler) **+ FSR Frame Gen** |
| Frame Gen | — | — | DLSS-G (Streamline) + FSR FG, **deferred** |
| Own TAA | — | — | experimental |

**Key fact**: reblue starts from **the same SDK as dbz3**
(`reblue_manifest.toml` → `sdk_version = "0.10.0"`, `REXCVAR_*`,
`rexglue_setup_target`) but **replaces the GPU plugin**
(`rexglue_setup_target(<target> [GPU_PLUGINS xenos])`): it uses its own
`src/gpu/` on top of `plume`. That is what lets it do "real" MSAA/SSAA,
`render_scale` below 100 % and output-resolution hooks. **It is not a config
flag: it is another render layer.**

LostOdysseyRecomp does not even use ReXGlue: it is XenonRecomp/XenosRecomp +
plume (the UnleashedRecomp line). It is the one with the complete temporal
pipeline, but on its own GPU.

## 2. Why FSR1 works in dbz3 and FSR3/DLSS do not

- **What we have today**: `rexglue-sdk-0.10/src/ui/presenter.cpp` applies
  **spatial FSR1** (`guest_output_ffx_fsr_easu_ps` + `..._rcas_ps`) and **CAS**
  (`guest_output_ffx_cas_*`) on the guest's already-resolved image. It is a
  **single-frame spatial** filter: it needs no depth, no motion, no jitter.
- **What a temporal upscaler demands** (FSR3/DLSS/DLAA/FG): colour at **render
  resolution** (not presentation), **depth** from the same pass, **motion
  vectors** with the conventional sign (past←present, in render pixels),
  camera **jitter** not applied to UI/shadows/motion, and colour-exposure
  metadata. The presenter delivers none of that today: it only receives the
  final image with the UI already composed.
- **The FFX SDK present includes FSR3/FG**, but the build leaves them out:
  `rexglue-sdk-0.10/cmake/rexglue_fidelityfx.cmake` forces
  `FFX_API_ENABLE_FRAMEGEN_PROVIDER OFF` and only the FSR1 EASU/RCAS + CAS
  shaders are packed. Enabling FSR3 would require, besides the SDK, the inputs
  above.
- **There is already a temporal stub in the SDK, but degraded to spatial**:
  the `DispatchTemporalUpscaler` code exists in
  `src/ui/d3d12/d3d12_presenter.cpp` / `vulkan_presenter.cpp`, but every frame
  it does `reset=true`, passes the colour as depth **and** as motion vectors
  with `jitter=0` (`presenter.cpp` itself warns about it).
  `present_fsr_quality_mode` (FSR2/3) only feeds that path, which is why the
  launcher keeps it hidden. Earlier basis:
  `ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14.md`.

## 3. What LostOdysseyRecomp documents (the most valuable lesson)

Its `docs/notes/temporal-upscaling-feasibility.md` is, literally, the plan of
what we would have to do. Points that apply as is to dbz3:

- Owning the translated shaders, the draw dispatch, the depth surfaces and
  the command lists **is a necessary condition**; dbz3 does **not** own them
  (they live inside `rexgpu-xenos.dll`).
- A **post-presentation** filter "has a substantially weaker contract": it
  cannot give reliable depth/object motion/jitter.
- **"Optical flow and zero vectors are not native motion vectors"**: labelling
  them as such is forbidden by its own acceptance criterion.
- **Risk #1 = scene/UI boundaries and object/skin motion**. In its words:
  "once proven, the SDK's D3D12 adapter is a moderate cost; the high
  uncertainty is the object identity/history and the scene/UI boundary, which
  **require game-specific RE**; no DLL or post-process flag recovers their
  semantics".
- Its real state (2026-09-27): DLSS SR running on an RTX 5080 (Quality
  `1707x960 -> 2560x1440`), but **Gate 3 not passed**, no visual acceptance,
  **Frame Gen deferred** and **NGX redistribution unresolved** (proprietary
  licence). That is: even with its own GPU layer, it is a months-long project
  and still experimental.

**For dbz3 this translates into**: doing DLSS/FG would mean (a) exposing
colour/depth/MV from `rexgpu-xenos`, with guest RE for object/skin identity,
or (b) replacing the GPU backend with one of our own like `plume` (what
reblue did). Neither is "integrating a library".

## 4. The temporal contract that would have to be built (if it is ever resumed)

1. **Scene/UI boundary**: identify the scene resolve (colour+depth) and the
   first UI draw after it, per frame and per scene family.
2. **Depth and projection**: depth from the same pass, the convention (dbz3
   uses reversed-Z in the guest), near/far, and reprojection with the camera.
3. **Motion**: a **backward** motion field in render pixels. Camera only =
   static geometry only; bone/skin motion is needed.
4. **Jitter**: a sub-pixel offset **only** for the scene; never for UI,
   clears, shadows or full-screen triangles.
5. **Colour/exposure**: distinguish HDR/SDR scene and pre-exposure before
   deriving the SDK's constants.
6. **Internal resolution**: render the scene at the mode's internal resolution
   (Quality/Balanced/Performance) and resize viewports, scissors, resolves and
   screen-space constants consistently.

## 5. What CAN be done with what is already there (without touching the GPU)

- **FSR1 + CAS** (already present): spatial output upscaling and sharpness.
- **`draw_resolution_scale`**: real supersampling of the guest (2x/3x). Real
  measured cost: 3x ≈ 51 % GPU vs 1x+FSR ≈ 22 %. That is why `1x` is the default.
- **FXAA/dither** (`swap_post_effect`, `dbz3_present_dither`).
- **HD textures** (`dbz3_hd_textures`) as a sharpness lever without a temporal cost.

## 6. Learnings from reblue adoptable in dbz3

**Already adopted (2026-09-29):**
- **DRED decoupled from the debug layer**: cvar `d3d12_dred` (ON by default).
  The *device lost* report names the queue/list (breadcrumbs) and the page
  fault's allocation nodes. See `github/patches/README.md` §2026-09-29.
- **`gamecontrollerdb.txt`** shipped next to the exe (the runtime already has
  the `hid_mappings_file` cvar): the SDL backend recognises generic pads.

**Already adopted (2026-09-30, launcher QoL — host only):**
- **Button labels (glyphs)**: cvar `dbz3_input_glyphs` (Xbox / PlayStation /
  Switch). The **Controls** tab changes the names next to each keybind (`LT`
  vs `L2` vs `ZL`, `D-Pad Up`, `LS-Up`, ...) using the helper `ButtonGlyph()`
  in `src/launcher/launcher_state.cpp`. It is only cosmetic: it **does not
  touch the runtime's mapping** (unlike reblue's glyph set, which rewrites
  blocks of a guest DDS sheet via hooks).
- **"Repair installation"** (`dbz3::settings::RepairInstallation()`): a button
  in the launcher's footer and a one-shot flag `dbz3_repair` (CLI
  `--dbz3_repair=true` / `REX_DBZ3_REPAIR=1`) that reopens the launcher and
  shows a report in a popup. It quarantines an unreadable `dbz3_user.toml`
  (`*.invalid`) and rewrites clean settings, checks `rexruntime.dll`,
  `rexgpu-xenos.dll`, `amd_fidelityfx_dx12.dll` and `gamecontrollerdb.txt`,
  and makes sure the user data folder exists. **It does not touch `us/eu/`,
  `mods/` or the caches.** Validated at runtime (one of the reports left the
  `.invalid` of a broken toml and regenerated the good one).

**Discarded (with a reason):**
- **PSO precache/predictor/recorder** (reblue `src/gpu/pipeline/pso_*`): the
  predictor and the precache discipline are agnostic, but each PSO's *build*
  depends on **plume** (`RenderGraphicsPipelineDesc`,
  `CreateHostGraphicsPipeline`). Against `rexgpu-xenos` (Xenia) `Build` and
  the cache format would have to be reimplemented; it is not a launcher task.
- **Output-resolution hooks** (reblue `src/gpu/hooks/output.cpp`): guest RE
  with concrete Blue Dragon addresses (`0x82DDA670`, viewports,
  `VisualRender::ctor`, ...). It does not apply to DBZ3; it would require
  locating the Budokai engine's equivalents (research, not QoL).
- **`frame_interp`** (reblue `src/engine/frame_interp.cpp`, 3,000+ lines):
  decouples rendering from the guest's 30 Hz simulation with dozens of gates.
  It is per-game guest RE; DBZ3 already runs at a fixed 60 Hz.
- **UI language vs voices**: reblue separates `bd_language` (`user_language`,
  boot) from `bd_opt_voice_type` (an in-game option against `[Voice]` of
  `bd_boot.ini`). In DBZ3 the text language is already controlled
  (`dbz3_language`); the voice one lives in the guest's engine and would
  require locating its option (RE).
- **Profiles**: reblue uses one directory per profile (`profiles/<name>` with
  its toml/saves/mods). Our launcher already has **mod** profiles
  (`dbz3_mod_profile` + `mods/profiles.txt`); a complete settings-profile
  system is a data redesign, not a one-day improvement.

**Next candidates (medium cost, without redoing the GPU):**
- **PSO precache adapted to Xenia** (only if touching `rexgpu-xenos` is decided).
- **Settings profiles** (named snapshots of `dbz3_user.toml`).

## 7. Risks and licences

- **NVIDIA NGX/DLSS**: proprietary SDK; LostOdysseyRecomp leaves the
  redistribution of `nvngx_dlss.dll` **unresolved**. Do not package it without
  resolving that.
- **FSR**: redistributable under the AMD FSR/FidelityFX SDK licence (we
  already ship `amd_fidelityfx_dx12.dll`).
- **Third-party code**: reblue is **BSD-3-Clause**, LostOdysseyRecomp is
  **GPLv3**. If code is reused, respect licence and attribution. (The PS5
  port, adapted from the GPL-3 mcla-recomp, is kept in the GPL-3 `ps5/` folder
  for this reason.)
- **GameControllerDB**: zlib (https://github.com/mdqinc/SDL_GameControllerDB).

## 8. Recommendation

Keep the **spatial** strategy (FSR1/CAS/FXAA + internal scale + HD textures)
as the deliverable. Treat temporal upscaling as **bounded research** with the
phases in §4, and **only** resume it if it is decided to (a) instrument
`rexgpu-xenos` for colour/depth/MV with guest RE, or (b) migrate to our own
GPU backend. Do not promise DLSS/FSR3/Frame Gen to the user.

## 9. References

- `zolaware/reblue` — `src/gpu/settings.cpp`, `src/gpu/output*.cpp`,
  `src/gpu/dred.*`, `src/gpu/pipeline/pso_*`, `config/hooks/*.toml`.
- `freefrank/LostOdysseyRecomp` — `LostOdysseyRecomp/gpu/temporal_upscaler.h`,
  `upscaling_plan.h`, `dlss_ngx*.cpp`, `fsr_upscaler*.cpp`,
  `frame_generation_*.cpp`, `streamline_runtime.cpp`,
  `docs/notes/temporal-upscaling-feasibility.md`,
  `docs/notes/native-dlss-validation.md`, `cmake/Lo{Dlss,Fsr,Streamline}.cmake`.
- Local (only while the clone exists): `%TEMP%\opencode\repos\`.
- Ours: `rexglue-sdk-0.10/cmake/rexglue_fidelityfx.cmake`,
  `rexglue-sdk-0.10/src/ui/presenter.cpp`.
