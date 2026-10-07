# Plan 1.4.2: DLSS and FSR 3 (2026-10-05)

Goal requested by the user: real DLSS and FSR3 (temporal upscaling and, if
possible, frame generation), using Burst Limit, Blue Dragon (reblue) and Lost
Odyssey as references.

> On **PS5** (`docs/PS5.md`) none of this applies: the console build is Vulkan
> only and leaves FidelityFX/DLSS out.

## 1. What each reference has (reviewed today)

| Project | GPU base | DLSS | FSR3 | How it gets motion vectors |
|---|---|---|---|---|
| Burst Limit (iExplosiveRage) | rexglue `rexgpu-xenos` | No | SDK stub (no motion) | It does not |
| reblue (zolaware, BSD-3) | its own GPU on plume | No | No | There is no temporal upscaling |
| Lost Odyssey (freefrank, **GPL-3.0**) | its own GPU on plume | Yes: SR, DLAA and FG (Streamline) | Yes: FSR 3.1 SR + FG | **Re-runs every draw** with the previous frame's constants and writes per-pixel velocity ("motion replay") |

- Lost Odyssey is the only reference with DLSS/FSR3 working. Its code is
  GPL-3.0 and ours is MIT: **it is studied, not copied**. The idea is
  reimplemented.
- Change compared with the 2026-09-29 study (`VIABILIDAD_UPSCALING_TEMPORAL`):
  back then we did not build the GPU layer. **Now we do**: `rexgpu-xenos` comes
  from our `rexglue-sdk-0.10` (branch `dbz3-burstlimit`), so the main blocker
  has disappeared.
- The FidelityFX SDK (FSR 3.1 upscaler) is already built and linked
  (`amd_fidelityfx_dx12.dll`). `D3D12Presenter::DispatchTemporalUpscaler`
  exists, but it passes the colour as depth and as motion, with `reset=true`
  every frame. The frame generator is off in `cmake/rexglue_fidelityfx.cmake`.

## 2. How a fight frame is drawn (measured today)

New trace: creating `dbz3_frame_trace.req` next to the exe dumps 3 frames as
`dbz3: ft ...` lines (draws, EDRAM copies and swap). Capture:
`scratchpad/ft_battle.txt` (Goku vs Goku, Tournament).

- Native 1280x720, **no MSAA** in the scene. One colour in EDRAM base 0 and the
  depth at base 1328.
- **d0-d383 = 3D scene:**
  - stage;
  - characters, with several different VS;
  - about 210 quads with z-test and without z-write, then without z: effects
    and particles.
- **copy#384:** the game resolves the **depth** to a 1280x720 texture. We get
  it for free.
- **copy#385 to copy#405:** post-processing.
  - Colour to a buffer that alternates every frame (1F35F000 / 1EFC7000).
  - Reduction to 320x180 and bloom.
  - Composition in 1D991000.
- **d406-d477:** the composition comes back and on top of it **the HUD**: about
  70 quads of 6 vertices, without depth.
- **copy#478, d479 and copy#480:** final pass to the front buffer 1F6F8000 and swap.

Consequence:
- The **scene/HUD boundary is clean and generic**: the scene runs from the
  start of the frame until the first full-resolution depth copy.
- Menus, the select screen and other screens without 3D do not have that copy.
  There, no jitter is applied and the upscaler receives still images.

## 3. Phased plan (each phase is built and tested in game before moving on)

1. **Jitter and depth.**
   - Sub-pixel offset (Halton) in `ndc_offset`, only for the draws of the
     scene phase.
   - The real depth of that phase is passed to the upscaler.
   - FSR 3.1 is tested with camera-only motion, behind a hidden switch.
2. **Motion vectors by re-execution (the big piece).**
   - Each scene draw is recorded: VS, buffers, indices and our own copy of its
     constants.
   - It is paired with the same draw from the previous frame: VS and PS hash,
     position buffer, indices, vertex count and order.
   - At the end of the scene it is drawn again with a VS modification that
     runs the body twice, with the previous and the current constants, and
     writes the difference into an R16G16 RT. The depth test uses the scene's.
   - It is what Lost Odyssey does. The change is in `dxbc_translator.cpp`: the
     body is translated twice and the first pass's position is kept.
3. **HUD mask.**
   - The pre-HUD composition (1D991000) is compared with the final output.
   - The pixels that change form the reactive mask for the upscaler, so the
     HUD does not leave trails.
4. **Real FSR 3.1.** Temporal upscaling with all of the above and an option in
   Launcher → Video and in the F4 menu.
5. **DLSS (SR and DLAA).**
   - Uses the same contract: NGX on D3D12.
   - Requires downloading NVIDIA's official SDK (third-party code: **ask for
     permission**) and redistributing `nvngx_dlss.dll`. Its licence allows it;
     review it before publishing.
6. **Frame generation (optional, if the above turns out well).**
   - FSR 3.1 FG with the FFX SDK's frame-gen provider, off today.
   - DLSS FG requires Streamline and is more work.
   - The game is fixed at 60, so FG would give 120 on fast displays.
7. **Vulkan and Linux:** FSR 3.1 on Vulkan with the same contract. DLSS on
   Linux is optional.

## 4. Known risks

- Re-execution doubles the scene's vertex cost. It is ~380 draws: affordable.
- Alpha-tested draws (hair, crowd) may give velocity where the original
  discarded the pixel. Lost Odyssey reuses the original PS for coverage; we
  will copy that in phase 2b if needed.
- Effects that reuse buffer addresses every frame. The pairing must reject
  anything doubtful and leave zero velocity with the reactive mask.
- The SDK's draw scale is an integer (1x, 2x, 3x). DLSS/FSR's internal
  resolution (Quality, Balanced, Performance) is obtained by rendering at 1x
  or 2x scale and upscaling to the display. The guest's scale does not need
  to change.
