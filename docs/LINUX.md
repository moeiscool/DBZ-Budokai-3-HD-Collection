# Native Linux

Linux support was added in the v1.2.6 branch in response to issue
[#10](https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/issues/10).
It uses Vulkan, SDL3 and the same dual US/EU core as Windows. It does not
need Wine.

## Dependencies

On Ubuntu 22.04 or derivatives:

```bash
sudo apt install clang-18 libc++-18-dev libc++abi-18-dev cmake ninja-build pkg-config libvulkan-dev \
  libsdl3-dev libx11-xcb-dev libwayland-dev wayland-protocols \
  libasound2-dev libpulse-dev libpipewire-0.3-dev unzip zenity
```

`kdialog` also works as an alternative file picker to `zenity`.

## Local build

The SDK is built first and installed into `rexglue-linux/`. Then the game is
configured against that installation:

```bash
cmake --preset linux-amd64 -S rexglue-sdk-0.10 \
  -DREXGLUE_ENABLE_FIDELITYFX=OFF \
  -DCMAKE_INSTALL_PREFIX="$PWD/rexglue-linux"
cmake --build rexglue-sdk-0.10/out/build/linux-amd64 --config Release --parallel
cmake --install rexglue-sdk-0.10/out/build/linux-amd64 --config Release
cmake --preset linux-amd64-release -DCMAKE_PREFIX_PATH="$PWD/rexglue-linux"
cmake --build out/build/linux-amd64-release --config Release --parallel
```

The preset enables Vulkan and `DBZ3_DUAL_REGION=ON`. The published build uses
`-march=x86-64-v2`, Clang 18 and libc++ 18; FidelityFX is disabled on Linux
because the Vulkan backend did not need it for the first published build.
Before building the SDK, run `bash tools/patch_rexglue_linux.sh`; it fixes the
missing `std::chrono::clock_time_conversion` in Ubuntu 22.04's libstdc++.
CI uses libc++ 18 because Ubuntu 22.04 ships libstdc++ 12, which does not
expose a complete `std::expected` for this C++23 SDK.

## Private codegen

The generated code derives from `default.xex` and is not published. CI gets it
from the private repository `novapowers0/DBZ-Budokai-3-HD-Collection-generated`,
using an SSH deploy key stored in the `DBZ3_GENERATED_SSH_KEY` secret. That
repository contains only:

- `us/`: `sources.cmake`, init/register and the USA generated sources.
- `eu/`: `sources.cmake`, init/register and the EU generated sources.

For a local build, put those two folders in place as `generated/` and
`generated_eu/`. Never add `.xex`, `.afs`, ISOs or user data.

## Functional differences

- Folder/file dialogs use `zenity`, then `kdialog` as a fallback.
- The Model Swap pipeline runs Python through `posix_spawn` and captures its
  output without opening an interactive shell.
- Installing ZIP mods uses the system's `unzip` command.
- Model Swap's LZX compression still depends on the Windows XDK binary; the
  base game and already-built mods do work on Linux. Porting LZX to
  `libmspack` is separate from the first playable build.
- **Texture packs (PCSX2 style) also work on Linux/Vulkan**: the same pack in
  `mods/` that Windows uses is applied here (the image is uploaded to the GPU
  with a staging buffer and `vkCmdCopyBufferToImage`, with the pack's
  dimensions and RGBA8 format). The launcher's pack detection is identical.
- **Two D3D12-layer features do not exist on Linux** (Vulkan): the
  experimental **HD texture upscale** (`dbz3_hd_textures`,
  `dbz3_upscale_min_size`) and the **dev texture dump** (`dbz3_texture_dump`).
  The rest is in the Linux build: the presenter's FXAA/dither
  (`swap_post_effect`/`present_dither`), internal scale
  (`draw_resolution_scale`) and the Development tab's GPU diagnostic levers
  (`async_shader_compilation`, `occlusion_query_enable`). Texture packs do
  **not** depend on the D3D12 layer.

## Data package

The tarball does not include the game. Put the legal `default.xex` and `us/`
or `eu/` next to `dbz3`, as on Windows. The `mods/` folder is created next to
the executable. The package must include `librexruntime.so`,
`librexgpu-xenos.so` and the LLVM libc++/libc++abi/libunwind libraries used by
the CI build. This keeps the binary from failing before opening the launcher
on distributions such as Arch or CachyOS because `librexruntime.so` or
`libunwind.so.1` is missing.

## MangoHud and Steam FPS

The Linux build uses a Vulkan swapchain. MangoHud and Steam's counter
intercept presentation (`vkQueuePresentKHR`), not the game's 60 Hz logical
cadence. The presenter applies the presentation limit configured in the
launcher and uses FIFO by default; that way overlays do not get an unbounded
presentation loop or count hundreds or thousands of presents per second.

`IMMEDIATE`, `MAILBOX` and `FIFO_RELAXED` remain available as advanced
options, but are not recommended with external overlays. The limit only
regulates the host's output: it does not change the game's logical speed.

To check the behaviour, start first without MangoHud and then with
`mangohud ./dbz3`. If MangoHud still produces stutter, try FPS and frametime
only, without temperature, power or load sensors; those extra queries let you
separate the cost of the Vulkan hook from the cost of telemetry.

## Relation to Windows

This problem is exclusive to the Vulkan path. The Windows build uses D3D12,
where presentation is driven by the guest (`IssueSwap`, 60 Hz) and there is
no present-mode selection, so there is no unbounded present loop nor an
equivalent code change. Full analysis in
`SESION_PACING_WINDOWS_2026-09-20.md`.

## Relation to PS5

The jailbroken-PS5 build (`docs/PS5.md`) is also Vulkan, built on an Arch
Linux host with the PS5 payload toolchain. It reuses the same POSIX runtime
paths plus a PS5 platform layer (`ps5/patches/`); it is single-region and has
no launcher.
