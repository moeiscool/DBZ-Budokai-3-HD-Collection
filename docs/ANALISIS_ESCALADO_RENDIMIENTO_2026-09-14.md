# Analysis: upscaling (FSR3/DLSS), performance and repo state (2026-09-14)

The user's questions: (1) is it viable to add FSR3 or DLSS?; (2) there are
user reports of poor performance; (3) if these take a long time, publish the
current changes as a new release.

> **Later update:** v1.4.2 shipped DLSS/FSR 3 as a beta (see
> `docs/PLAN_1.4.2_DLSS_FSR3.md`); this document records the analysis as it
> stood on 2026-09-14.

---

## 1. FSR3 / DLSS — viability

### What ALREADY exists in the SDK today (0.10)
- **FSR1 (EASU + RCAS) and CAS: REALLY IMPLEMENTED** (vendored shaders +
  `ffx_api`). It is the upscaling the launcher uses (`present_effect=fsr|cas`).
  - `rexglue-sdk-0.10/src/ui/presenter.cpp:45` (cvars), `:1069-1147` (pass
    chain), `src/ui/d3d12/d3d12_presenter.cpp`.
- **"Temporal" FSR2/FSR3: present but DEGRADED to spatial.** The code exists
  (`DispatchTemporalUpscaler`) but every frame it does `reset=true` and passes
  the colour as depth **and** as motion vectors, with `jitter=0`
  (`d3d12_presenter.cpp:165-192`; `vulkan_presenter.cpp:366-403`). The code
  itself warns about it (`presenter.cpp:236-243`).
- **Vendored FidelityFX**: fork `rexglue/FidelityFX-SDK`, SDK **1.1.3**,
  upscaler **FSR 3.1.4** (`cmake/rexglue_fidelityfx.cmake:52-53`).
- **Frame Generation: NOT compiled** —
  `FFX_API_ENABLE_FRAMEGEN_PROVIDER OFF` (`cmake/rexglue_fidelityfx.cmake:107`).
- **DLSS/NGX/XeSS: ABSENT** (empty grep across the whole SDK).

### The underlying blocker (common to temporal FSR3, FSR3 FG and DLSS)
The renderer is **translation/replay of Xenos commands**, not an engine with
its own G-buffer. **There are no motion vectors or jitter** in `src/graphics`
(search: 1 irrelevant match). A temporal upscaler (FSR3/DLSS/XeSS/FG) needs
**depth + motion vectors + jitter**; today they are not captured. Without
them, `fsr2/fsr3` are an expensive alias of FSR1.

### Verdict

| Goal | Viable now | Effort |
|---|---|---|
| Spatial FSR1 / CAS | ✅ already works | — |
| Real temporal FSR3.1 upscaler | ⚠️ | **weeks-months** (export depth+motion+jitter) |
| FSR3 Frame Generation | ❌ | **very high** (FG off + proxy swapchain + temporal inputs) |
| DLSS (SR/FG) | ❌ | **very high** (vendor NGX/Streamline + temporal inputs) |
| XeSS | ❌ | **very high** |

**Conclusion**: it is **NOT** viable in the short term. The "administrative"
part (ffx_api) is already there; the real bottleneck is **exporting the
temporal inputs** from `src/graphics` to the presenter. It is a large research
project, not a release task.

**Pragmatic route (without touching the SDK)**: use what is already there —
internal scale `draw_resolution_scale` 2x-3x + FSR1 + CAS + aniso. That is what
the launcher offers.

### Improvement applied in this session
The launcher wired `dbz3_fsr_sharpness` and `dbz3_cas_sharpness` but **did not
expose them**. Now the **Upscaling** tab shows:
- FSR → **RCAS sharpness** slider [0,2] (`present_fsr_sharpness_reduction`).
- CAS → **Additional sharpness** slider [0,1] (`present_cas_additional_sharpness`).

Both are **real** FSR1/CAS knobs (unlike `present_fsr_quality_mode`, which
only affects fsr2/fsr3 and so stays hidden).

---

## 2. Performance — reports and state

### Reports reviewed (repo issues, 2026-09-02..09-10)
- **#1 (v1.0.4, Linux/AMD)**: *"broken frame cap: it did not hold
  60/120/240"* and *"slowdowns outside Uncapped"*. **Already addressed**: the
  presenter's real `frame_cap` (`d3d12_presenter.cpp:571-588`, cvar
  `frame_cap`, launcher `dbz3_frame_cap` with `SafeFrameCap`) and the guest
  speed fixed at 60 Hz.
- **#3 (v1.1.1, Mac/CrossOver)**: reports **locked 60 FPS, ~4 ms frame time**
  (good performance). Its 2 findings: EU region by default (there is already
  `ResolveRegion`) and a red channel in a splash (a 16-bit texture format
  under D3DMetal, cosmetic). The backend switch it asked for **already exists**
  in 1.1.2+ (`dbz3_gpu_backend` → cvar `gpu_backend`).

### Current performance levers
- Internal scale (`draw_resolution_scale_x/y`, 1..8) + per-GPU presets
  (low/medium/high/ultra) in the launcher.
- FSR1/CAS/bilinear; MSAA 2x; anisotropic; `frame_cap` (0/15-1000); VRR.
- **D3D12** backend (recommended) vs **Vulkan** (experimental, ~6.5× slower in
  `IssueSwap`; see `docs/PLAN_1.1.1.md`).

### Performance conclusion
There is no open, actionable problem in the current versions: the hard report
was the `frame_cap` (already solved) and the rest are modest machines (that is
what the presets are for) or Vulkan (experimental). **No large pending
optimisation is identified** without RE of the renderer.

---

## 3. What is done about it
- **FSR3/DLSS**: documented as **out of scope in the short term** (this doc).
  The practical route is the one already implemented (internal scale +
  FSR1/CAS), now with adjustable sharpness.
- **Performance**: no large action pending.
- **Release**: the accumulated changes/improvements are published (mod
  launcher, HD↔HD Model Swap, ISO notice, mod cleanup, reference texture mod).
