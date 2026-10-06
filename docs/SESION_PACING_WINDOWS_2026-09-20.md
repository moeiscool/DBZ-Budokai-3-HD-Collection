# Windows pacing after the Linux fix (2026-09-20)

> Origin: after fixing Linux's Vulkan pacing (`frame_cap` + FIFO by default,
> see `docs/LINUX.md`), we checked whether the lesson applied to the Windows
> (D3D12) build. **Conclusion: there was nothing to bring over.** This document
> records the analysis, what was discarded and why the code stays the same.

## Summary

- Linux (Vulkan) **did** have a real bug: `IMMEDIATE`/`MAILBOX` allowed an
  unbounded presentation loop and Steam's counter measured swapchain presents
  (hundreds/thousands of FPS). It was fixed with FIFO by default and
  `frame_cap` in `vulkan_presenter.cpp`.
- Windows (D3D12) does **not** suffer from that bug. Not a single line changed.
- Moving the `frame_cap` sleep to just before `Present` was considered and
  **discarded**. Reason below.

## Why the Linux bug does not apply to D3D12

1. **There is no present-mode selection.** `IMMEDIATE`/`MAILBOX` are Vulkan
   swapchain concepts. The D3D12 presenter always uses `Present(0)` with
   `DXGI_SWAP_EFFECT_FLIP_DISCARD` (and `ALLOW_TEARING` if VRR is on,
   `d3d12_allow_variable_refresh_rate_and_tearing`).
2. **Presentation is driven by the guest, not by a free loop.** In game,
   `D3D12CommandProcessor::IssueSwap` in `rexgpu-xenos` requests the frame at
   the guest's pace (a fixed 60 Hz, the `vsync` cvar is locked). There is no
   continuous repaint firing unbounded presents.
3. **The real `frame_cap` already existed.** `PaintAndPresentImpl` already
   applies `frame_cap` (`dbz3_frame_cap`, default 60 in game) by sleeping until
   the 1/FPS slot. It is exactly the equivalent of the Linux fix.

So an overlay on Windows (Steam/DXGI) cannot observe the same "inflated
counter" as on Linux.

## Change considered and discarded

Moving the `frame_cap` sleep from the start of `PaintAndPresentImpl` to just
before `IDXGISwapChain::Present`, imitating the position of the Vulkan fix,
was evaluated.

**It was discarded**:

- **It does not change the observable cadence.** The throttle is a fixed rate
  in a serialised loop; moving it earlier or later gives the same
  presents/second.
- **It worsens latency.** With the sleep at the start, the frame is built,
  submitted and presented immediately. With the sleep just before `Present`,
  the frame is built and submitted, and **then** waits; that adds delay
  between submitting the command list and presenting.
- In Vulkan the position matters because `vkQueuePresentKHR` is the boundary
  MangoHud/Steam intercept; in D3D12 the conceptual equivalent (`Present`)
  already comes after the throttle without moving it.

The `d3d12_presenter.cpp` code (SDK and `github/patches/`) stays **identical**
to what was published in v1.2.6.

## What cannot be transferred from Linux

- **MangoHud is a Linux overlay** (`vkQueuePresentKHR`). It does not apply to
  Windows; do not use it as a test of the D3D12 build.
- **FIFO** is a decision exclusive to the Vulkan swapchain.
- An **overlay counter measures host presents**, not the guest's logical
  swaps. For game performance, the reliable reference is the internal
  diagnostic `dbz3: perf fps=... frames=... max_frame_ms=...`
  (`dbz3_perf_logging`, Dev tab), not the overlay.

## Diagnostic notes on Windows

- **In game**: `frame_cap=60` in game (set by the launcher). There is no free
  loop.
- **In the launcher**: `frame_cap` is kept at **0/uncapped** on purpose
  (`settings.cpp`); that is what avoids the hang at >60 Hz documented in the
  history. If Steam's counter shows high FPS **in the launcher** (settings
  menu), that is expected and does not affect the game.
- `fg=0/1` in the `perf` line distinguishes "unfocused window" (Windows/DWM
  halves it, 60→30) from a real "it runs slow".

## Result

- **No code changes on Windows.**
- **No rebuild and the v1.2.6 release untouched** (the exe and the DLLs are
  still the published ones).
- Documentation: this file + the "MangoHud and Steam FPS" section of
  `docs/LINUX.md`.

> The PS5 build (`docs/PS5.md`) uses the Vulkan presenter with DBZ3's
> `frame_cap` pacing kept intact (merged with mcla-recomp's PS5 paint logging).
