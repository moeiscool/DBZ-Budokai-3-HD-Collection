# How to build

> Updated: 2026-08-14. For the PS5 build see `docs/PS5.md`; for Linux,
> `docs/LINUX.md`.

---

## 1. BUILD THE GAME (release)

```powershell
cmake --build "out\build\win-amd64-release"
```

The build uses the SDK **installed** in `rexglue\` (not the `rexglue-sdk\` source).

---

## 2. BUILD THE SDK (rexglue-sdk) → produces rexruntime.dll

```powershell
cmake -G Ninja -S rexglue-sdk -B rexglue-sdk\out\build-win-vulkan `
  -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe" `
  -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe" `
  -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" `
  -DREXGLUE_ENABLE_FIDELITYFX=ON -DREXGLUE_USE_VULKAN=ON `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=x86-64-v3"

# Build only the runtime (fast, incremental)
ninja -C rexglue-sdk\out\build-win-vulkan rexruntime
```

The resulting DLL is in `rexglue-sdk\out\win-amd64\rexruntime.dll`.

### Install it into the game build
```powershell
Copy-Item "rexglue-sdk\out\win-amd64\rexruntime.dll" "out\build\win-amd64-release\rexruntime.dll" -Force
```

> ⚠️ If you modify `rexglue-sdk-0.10/src/filesystem/afs.cpp` (the mod hook), you
> have to rebuild the SDK AND copy the DLL into the build. The game build is
> NOT rebuilt by itself for SDK changes.

---

## 3. COMPRESS/DECOMPRESS BINS (LZX)

Tools in `mod center\Xbox 360 Compression - Decompression tool from the XBOX Development Kit\`.

```powershell
# Compress (use /N:2048! the game's block size)
xbcompress.exe /N:2048 <src.bin> <dst.lzx>

# Decompress
xbdecompress.exe <src.lzx> <dst.bin>
```

---

## 4. TRACY BUILD (profiling)

```powershell
cmake --build "out\build\win-amd64-tracy"
```
- Uses instrumented DLLs (rexruntimerd.dll, rexgpu-xenosrd.dll, TracyClientrd.dll).
- To profile: `tracy-capture.exe -o out.tracy` while playing, then
  `tracy-csvexport.exe` for analysis.

---

## 5. PACKAGE A RELEASE

```powershell
cmake --build "out\build\win-amd64-dual"          # ⚠️ the release exe comes from HERE (dual core)
powershell -ExecutionPolicy Bypass -File tools\sync_github.ps1
powershell -ExecutionPolicy Bypass -File tools\make_release.ps1      # reads the version from src\version.rc
powershell -ExecutionPolicy Bypass -File tools\verify_release.ps1 -Version v1.2.2
```
- Version: bumped in `src/version.rc` (VERSION_PATCH + DBZ3_VERSION_STR).
- The stage (`github\release-stage\`) and the zip come from the **dual build**;
  the DLLs from `rexglue-sdk-0.10\out\win-amd64-baseline\`.
- `verify_release.ps1` checks VERSIONINFO, DLL hashes vs the SDK, an empty
  `mods/`, and that the zip carries no game assets or run leftovers.
- Publish: `gh release create vX.Y.Z <zip> --notes-file <notes> --latest`.

---

## 6. PS5 BUILD

The jailbroken-PS5 build is separate and runs on an Arch Linux host:
`bash ps5/make_ps5.sh --iso <your.iso> [--console <ip>]`. It clones the SDK,
copies in `patches/rexglue-sdk/`, applies `ps5/patches/`, recompiles the game
from your own executable and packages a homebrew title. Full guide:
`docs/PS5.md`; internals: `ps5/README.md`.

---

## 7. CAUTION

- The release build is the one used for playing. Modify the SDK carefully.
- Back up `rexruntime.dll` before replacing it (there is already a `.bak_afstest`).
- See `docs/01_estructura/ARBOL.md` for where everything lives.
