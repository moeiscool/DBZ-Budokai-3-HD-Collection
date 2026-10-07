# HISTORICO_RELEASES - Detail extracted from AGENTS.md (2026-09-26)

> File generated on 2026-09-26 while compacting AGENTS.md to
> <=60 KB. It holds the VERBATIM DETAIL of the longest blocks that were
> moved out of the operational reference. Do NOT load by default: read
> it only when you need the detail of a release, of the PS2->B3 port
> research or of the launcher. The operational reference is `AGENTS.md`.
> Complements `01_estructura/HISTORICO_AGENTS.md` (history prior to
> the 2026-09-02 compaction).
>
> **Translation note (2026-10-06):** originally written in Spanish and
> translated to English. Launcher UI strings are quoted in English where the
> launcher shows an English label; the Spanish originals live in
> `src/launcher/i18n.cpp`. Releases after v1.2.9 (v1.3.0 → v1.4.2.2) and the
> experimental **PS5 build** (`ps5/`, `docs/PS5.md`, 2026-10-06) are covered in
> `CHANGELOG.md` and `AGENTS.md` §14, not here.

---

## A. Release narrative and launcher/runtime work (1.1.3 -> 1.2.9)

> Verbatim copy of the `## 3. ESTADO ACTUAL` (current status) block of AGENTS.md before the 2026-09-26 compaction. It holds the release-by-release account (v1.1.3, v1.1.4 EX, v1.2.0..v1.2.9) with diagnoses, causes, measurements and DLL sizes. The per-release session docs are in `docs/`.

- **(2026-09-26) v1.2.9 PUBLISHED (Latest)**: **diagnostics that explain
  themselves**, prompted by SSGPrinceVegeta's latest logs (part 4: **zero
  errors**, but three things invisible in the log): (1) **undetectable mixed
  install** (a `...v1.2.1` folder with new DLLs: a whole round was lost
  working out which build produced the log); (2) **sustained 31 fps** with
  `upx` flat = vsync at **half rate** (frame > 16.7 ms with `3x`+MSAA+HD
  textures), not a bug; (3) **slow disk** (`io SLOW 42614us` with `pre=12us`, on
  `E:\Game Roms\...`). Implemented: (a) **runtime build stamp** in the DLLs
  (`rex/dbz3_build.h` -> cvars `dbz3_runtime_build`/`dbz3_gpu_build`, because the
  DLLs **have no VERSIONINFO**) + **mixed install detection** in the
  launcher (orange banner + `[warning]` + a line in Dev; a component without a
  stamp also counts) + line **`dbz3: entorno os=... ram=... dbz3.exe=... ...`**;
  (b) **`vram=usage/budget`** and **`lim=`** (0/1/2 = streak/VRAM) in the
  `perf` line, read from `IDXGIAdapter3::QueryVideoMemoryInfo` (the adapter is
  kept alive in `D3D12Provider`: the device **does not implement
  `IDXGIDevice`**, hr `E_NOINTERFACE`); (c) **VRAM guard** (>= 92 % of the local
  heap -> no new upscales granted, decision cached per key); (d)
  **sustained-fps warning** and **slow-disk warning**, ALWAYS on (they do not
  depend on `dbz3_perf_logging`/`dbz3_io_logging`; the normal log stays clean and
  the line only appears when there is something actionable); (e) warning about the
  **combination** internal scale + texture enhancement in the Video tab; (f)
  `tools/copy_sdk_dlls.ps1` (the stale-DLL trap from `rexglue/bin` invalidated
  two tests in this session) and `verify_release.ps1` checks the stamp.
  Validated: coherent environment without a false warning; **real mix** (1.2.9 exe +
  `rexgpu-xenos.dll` 1.2.8.2 taken from the zip) -> warning; match at 3x+MSAA+`hd_tex=3`
  = 60.0 fps / 0 errors / `vram=2171MB/11231MB lim=0`; forced VRAM guard ->
  `lim=2` + `upx=0`; warnings forced with temporary thresholds -> they fire once.
  FileVersion `1.2.9`. Canonical DLLs: `rexgpu-xenos.dll` **6355456 B**,
  `rexruntime.dll` 10917888 B. Doc: `docs/SESION_DIAGNOSTICO_2026-09-26.md`.
- **(2026-09-24) v1.2.8.2 PUBLISHED (Latest)**: **texture enhancement no longer
  tanks FPS** (follow-up on FPS-drop reports with the feature
  enabled; SSGPrinceVegeta's `part 4` logs, RTX 5090). **Diagnosis**: the
  reporter's EXACT config (3x + MSAA + hd_tex 3x + area 1M) gives **60.0 fps** on
  an RTX 4070 SUPER ⇒ it is not load. The real difference is the **re-scaling
  rate**: their `upx` rose to ~665 (~1 texture re-scaled per frame)
  while FPS dropped to 31. **Cause**: `LoadTextureDataFromResidentMemoryImpl`
  regenerated the **full mip chain** (12 levels) on EVERY reload; each
  level is 2 barriers + single-use descriptors + a pipeline change +
  dispatch, **serialized** in the command list ⇒ a **command/CPU cost, not a
  GPU one** (which is why a 5090 does not help and it does not show in GPU usage).
  The existing budget (`UpscaleBudgetAllows`) only bounds **new** grants, not
  reloads of already-granted keys. **Fix**: a texture is marked **dynamic**
  (base-only reload over the SAME resource, or **4+ reloads in 1.5 s** via an
  identity counter) and **only level 0 is regenerated**; the mips are kept
  (`upscale_chain_resources_` forces the whole chain if the resource is new after
  an eviction). Static ones keep the full chain. The factor **CANNOT be
  un-granted** (the Nx resource already exists and the upload path reads the
  same factor) ⇒ the size decision stays stable; the fill gets cheaper.
  **New diagnostic** in the `perf` line: `cfg=scale:3x3 msaa:true
  hdtex:3 area:1048576 min:16 aniso:5` + `upx_dyn=` + `texload=` (texture loads
  per window; measured 120-210/s in the intro ⇒ the game streams
  aggressively). Validated: smoke test with a temporary threshold (`count>=1`)
  running the new path on ALL textures with mips (**0 errors**, 60 fps, `upx_dyn`
  114) + 3 sessions with the reporter's config (60.0 fps, 0 errors,
  `upx_dyn=0` locally). Doc: `docs/SESION_PERF_TEXTURAS_2026-09-24.md`.
  FileVersion `1.2.8.2`. Canonical DLL: `rexgpu-xenos.dll` **6346240 B**,
  `rexruntime.dll` 10910720 B.
- **(2026-09-23) v1.2.8.1 PUBLISHED (non-Latest after 1.2.8.2)**: **the dump covers
  the HUD/UI formats and packs accept RGBA8** (follow-up on issue #11). The
  reporter confirmed that v1.2.8 already dumped, and added two things: almost
  all HUD textures were missing (only some fonts came out) and some came out as
  a "black square". Cause of the first: `Dbz3DdsFourCc` only recognized DXT1/3/5,
  so everything **uncompressed** (`k_8_8_8_8`, `k_1_5_5_5`, `k_5_6_5`, `k_8`...)
  was silently skipped. Now `Dbz3DumpFormatFor()` dumps them with the correct
  DDS (guest masks verified against Xenia) and unsupported ones **warn** once in
  the log. The "black squares" are DXT3 with alpha **all zero** (the game draws
  those textures ignoring their alpha): the DDS is faithful, and the importer
  gains `--opaque-alpha` to view them. Also: **cap of 4 versions per identity**
  (the intro's video texture was dumped frame by frame: 4096 files/1.4 GB in
  5 min -> 194/51 MB) and the pack now accepts **`k_8_8_8_8`**
  (`Dbz3PackReplaceableFormat`), so the HUD that is now dumped **can** be
  replaced (validated on D3D12). Doc:
  `docs/SESION_VOLCADO_FORMATOS_2026-09-23.md`. FileVersion `1.2.8.1`.
  Canonical DLL: `rexgpu-xenos.dll` **6342656 B**, `rexruntime.dll` 10910720 B.
- **(2026-09-21) v1.2.8 PUBLISHED (non-Latest after 1.2.8.1)**: **texture dump fix**
  (issue #11: "Error dumping textures"). The cvar registry is
  **SHARED** between `dbz3.exe` and `rexgpu-xenos.dll` (the exe loads first),
  so the plugin's duplicate definition of `dbz3_texture_dump` was
  discarded (`duplicate registration ... second registration ignored`) and the
  plugin read **its own storage** (always empty) -> it never dumped anything.
  Now the plugin reads the path with **`REXCVAR_QUERY`** (like
  `dbz3_texture_packs`) and no longer redefines the cvar; the duplicate
  definition of `dbz3_texture_packs` was also removed (the log no longer has
  errors). Measured with the same harness: published v1.2.7 DLL = **0 DDS** vs
  fix = **96 DDS** + packs OK. Doc: `docs/SESION_FIX_VOLCADO_2026-09-21.md`.
  FileVersion `1.2.8.0`. Canonical DLL: `rexgpu-xenos.dll` **6340096 B**,
  `rexruntime.dll` 10910720 B.
- **(2026-09-21) v1.2.7 PUBLISHED (non-Latest after 1.2.8)**: **complete texture packs
  (PCSX2 style)**: dev dump (already in v1.2.6) + **runtime loader**
  (folder in `mods/` with `<hash>_<W>x<H>_<suffix>.dds|.png`; factor x1..x4
  inferred from the size; RGBA8 + mips via box filter; priority over the HD
  enhancement). Implemented on **D3D12 and Vulkan** (shared module
  `dbz3_texture_pack.{h,cpp}`; on Vulkan VMA staging + `vkCmdCopyBufferToImage`).
  Detection from the launcher (`RefreshTexturePacks()` -> `SetFlagByName`;
  the plugin reads with `REXCVAR_QUERY`) + a line in the Mods tab. Tool
  `mod center hd/texture_pack.py` and guide `docs/02_mods/PACKS_DE_TEXTURAS.md`.
  **Visually validated on both backends** (magenta pack: characters in the
  select menu in magenta). Release with a Windows zip + **Linux v1.2.7 tarball**
  (the Vulkan port is part of the Linux CI). FileVersion `1.2.7.0`.
  Canonical DLLs (at the time): `rexgpu-xenos.dll` **6346752 B**,
  `rexruntime.dll` 10910720 B.
- **(2026-09-20) v1.2.6 PUBLISHED (non-Latest after 1.2.7)**: release
  `…/releases/tag/v1.2.6` (`DBZ-Budokai-3-HD-Collection-v1.2.6.zip`, ~22 MB;
  `verify_release.ps1 -Version v1.2.6` = VERIFICATION OK; exe from the **dual**
  build, FileVersion `1.2.6.0`; PortForge `defaultVersion 1.2.6`). Bundles the
  **unpublished** HD texture work (commit `f2f8f4e`) + the **TOML/UX repair**
  (commit `05745ab`): (a) **Texture enhancement (experimental)**: stutter fix
  (constant-time mips, `kXeMaxBlockSamples=8`), native RGBA8 coverage, x3 cap
  and area in the Dev tab; (b) **clean HUD** (`dbz3_upscale_min_size`=16 +
  anti-ringing clamp in `texture_upscale_cs.hlsl`); (c) **anti-abuse UX for the
  internal scale**: warning + "Back to native (1x)" button, presets that do
  **not** raise the scale; (d) **TOML self-repair** (`ConfigLoadState`
  kOk/kRepaired/kInvalid, green/red notice above the tabs, `.bak` if
  unrepairable) — covers Prince Vegeta's logs (v1.2.1). Doc:
  `docs/SESION_TOML_Y_UX_2026-09-20.md`. Title: "1.2.6 - Polished HD texture
  enhancement + self-repairing settings".
  **Windows asset replaced 2026-09-20 21:54** (same tag; zip 22,090,591 B,
  digest `10df4bce…`) to include the **dev texture dump** (selectable folder,
  a user-chosen default path; helper `texture_dump_import.py` in
  `mod center hd/`) — see `docs/SESION_TEXTURAS_PACK_2026-09-20.md`. The v1.2.6
  Linux tarball does not change.
- **(2026-09-19) v1.2.5 PUBLISHED (non-Latest after 1.2.6)**: release
  `…/releases/tag/v1.2.5` (`DBZ-Budokai-3-HD-Collection-v1.2.5.zip`; exe from the
  **dual** build, FileVersion `1.2.5.0`; PortForge `defaultVersion 1.2.5`).
  Deep investigation of the **read path** (`HostPathFile::ReadSync` is
  synchronous) + focus QoL. Content: (a) **`dbz3_io_logging`** (I/O summary
  every 5 s with percentiles + a line per slow read; `dbz3_io_slow_ms`=25) and a
  **fast path without mods** (no override lookup nor virtual table copy per
  read) + `AfsGetVirtualTableFast` + an open counter;
  (b) **read-ahead** (`dbz3_io_readahead`/`_kb`=2048; only without mods;
  helps on mechanical disks, neutral on SSD); (c) **`fg=` in the `perf` line**:
  DWM limits a visible unfocused window to HALF (60→30 exactly) — now
  "alt-tab" can be told apart from "running slow"; (d) **QoL on focus loss**:
  `dbz3_mute_unfocused` (default ON; the SDL callback mutes using
  `dbz3_window_focused`, written by the app) and `dbz3_dim_unfocused` (default ON;
  full-screen overlay "Game in background"); **no real pause** (there is no
  safe mechanism); (e) **i18n round**: 2 keys that showed in English in
  IT/DE/FR + 13 new strings + `GpuTierLabel`/`ModTypeLabel` translated.
  (f) **final v1.2.5 (asset replaced, same tag)**: diagnostics become
  **OFF by default** (`dbz3_io_logging`, `dbz3_perf_logging`; opt-in in
  the Dev tab, with a new performance checkbox) and `logging.cpp` **prunes**
  old `dbz3_NNN.log` files (`log_max_files`=20) — before they piled up (138).
  New section **"When leaving the window"** at the top of the Video tab. Release
  title: "1.2.5 - Launcher improvements (focus and disk)". Doc:
  `docs/SESION_IO_FOCO_2026-09-19.md`. Canonical DLL: `rexruntime.dll`
  **10,910,208 B**.
- **(2026-09-19) v1.2.4 EX PUBLISHED (non-Latest after 1.2.5)**: commit `43b4da4`, release
  `https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/releases/tag/v1.2.4-EX`
  (`DBZ-Budokai-3-HD-Collection-v1.2.4-EX.zip`; `verify_release.ps1 -Version
  v1.2.4-EX` = VERIFICATION OK; exe from the **dual** build with FileVersion `1.2.4.1`;
  PortForge `defaultVersion 1.2.4-EX`). **Second batch of the launcher
  audit** (see `docs/SESION_LAUNCHER_AUDIT_2026-09-19.md` §6): (a) **FXAA**
  (`dbz3_fxaa` -> SDK `swap_post_effect`: none/fxaa/fxaa_extreme; runs before the
  upscaler and combines with FSR/CAS) and **dither** (`dbz3_present_dither` ->
  `present_dither`) in the Upscaling tab; (b) **mouse sensitivity**
  (`dbz3_mnk_sensitivity` -> `mnk_sensitivity`, 0.1-5.0, visible with the mouse
  enabled) in Controls; (c) **GPU diagnostic levers** in Dev:
  `dbz3_async_shaders` -> `async_shader_compilation` and `dbz3_occlusion_queries` ->
  `occlusion_query_enable`; (d) **writable user data**: `UserDataRoot()`
  and `UserSettingsPath()` fall back to `Documents/dbz3` (with a real cached
  probe and the path visible in Dev) if `<exe_dir>` is not writable (before,
  saving failed silently); (e) i18n +17 strings and a broader Reset. **Release
  title fixed and asset replaced** (same tag `v1.2.4-EX`) with the polished
  update check: repack-aware (`7a96385`), installed version always visible
  (`CurrentVersionLabel()`) + "Check for updates"/"Retry" button
  (`RequestUpdateCheck()`), short title "…1.2.4 EX - Launcher improvements" and
  stale version rows in the GitHub READMEs fixed (`7db1e81`).
  `verify_release.ps1` now accepts versions with a suffix (`-EX`/`-clasico`).
  Verified by log (`fxaa=fxaa_extreme ... mnk_sens=2.5` read from the SDK
  registry) and by a fallback test with a denied ACL. Canonical DLLs: `rexruntime.dll`
  **10,873,856 B**, `rexgpu-xenos.dll` **6,202,368 B** (corrected in §7).
- **(2026-09-19) v1.2.4 published (non-Latest, superseded by 1.2.4 EX)**: commit `fed62fc`, release
  `https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/releases/tag/v1.2.4`
  (`DBZ-Budokai-3-HD-Collection-v1.2.4.zip`, ~21.99 MB; `verify_release.ps1
  -Version v1.2.4` = VERIFICATION OK; exe from the **dual** build; version.rc `1.2.4`;
  PortForge `defaultVersion 1.2.4`). **Launcher audit** cross-checking the 35
  `dbz3_*` cvars against the SDK's 199: **DEAD controls** were found.
  Content: (a) **REAL volume** — new `audio_gain` cvar in the runtime
  (`sdl_audio_driver.cpp`, applied in the SDL callback) + Volume slider and
  Mute checkbox in the Audio tab (applied live); (b) **new version
  notice** (`src/launcher/update_check.{h,cpp}`, WinHTTP on a background thread,
  compares with the exe's VERSIONINFO; toggle `dbz3_update_check`); (c) removed
  the Gamma slider and the music/SFX/voice ones (dead: the guest mixes everything
  into one stream) and the `audio_output_device` line; (d) "Reset values" now
  also restores VRR and HD Textures; (e) i18n +12 strings; (f) new tools
  `tools/long_run.ps1`, `press_key.ps1`, `grab_window.ps1`,
  `click_window.ps1`. Canonical DLL: `rexruntime.dll` **10,873,856 B** (with
  `audio_gain` + `dbz3_perf_logging`). Doc:
  `docs/SESION_LAUNCHER_AUDIT_2026-09-19.md`.
- **(2026-09-18) v1.2.3 published (non-Latest)**: commit `7a3e058`, release
  `https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/releases/tag/v1.2.3`
  (`DBZ-Budokai-3-HD-Collection-v1.2.3.zip`, 21.99 MB; `verify_release.ps1
  -Version v1.2.3` = VERIFICATION OK; exe from the **dual** build; version.rc
  `1.2.3`; PortForge `defaultVersion 1.2.3`). Content: in-game performance
  counter (`dbz3_perf_logging`), AFS override log silenced and
  **HD Textures (WIP, OFF by default)**. Docs:
  `docs/ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md` +
  `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md`.
- **(2026-09-19) HD Textures — COVERAGE FIXED (native RGBA8) + UX + video
  guard (pending the user's visual validation)**: besides the stutter fix
  (§ below), the user reported "I didn't notice any texture improvement" with
  `hd_tex=4x`.
  **Cause**: `GetTextureUpscaleFactor` required `dxgi_format_uncompressed`, which
  is ONLY filled in for DXT → **every native RGBA8 (`fmt=6`, the largest ones:
  faces/clothes/stages) was discarded**; only small DXT3 ones were scaled.
  **Fix**: also accept native RGBA8 (`dxgi_format_unsigned ==
  R8G8B8A8_UNORM` + a load shader that produces RGBA8), new helper
  `GetTextureUpscaleRgba8Format` (bug: the resource was created with format UNKNOWN
  → thousands of `Unsupported texture formats`) and **frontbuffer exclusion**
  (`swap_texture_key_`; without it the swap resource was created at Nx → presenter
  crash).
  **🔴 BRUTAL CONSUMPTION (user feedback, 2026-09-19)**: with the feature on
  the GPU went to **80 % / 133 W / 3.1 GB**. Cause: the intro/SFD rewrites the
  video texture ~60 times/s and each rewrite regenerated the mip chain
  (`upx` reached **32182**; ~700 in battle). **Fix**: `UpscaleBudgetAllows`
  (sliding window; >24 upscales in 0.5 s ⇒ stop granting for 3 s; decision
  **cached per key** so it is stable, otherwise the Nx resource stays unfilled
  → `device removed 0x887A0001`). Measured: upx **32182→237**, GPU
  **80→39 %**, 133→34 W, 3.1→1.95 GB; x3 battle = 689 textures, 0 errors,
  60 FPS, <25 % GPU.
  **UX redesign** (user request): cap **x3** (was x4), the "Mpx
  limit" moves out of the normal view into the **Dev tab** in plain language
  (Low/Medium/High), the option is named **"Texture enhancement (experimental)"**
  with **Sharp (x2) / Very sharp (x3)**, default area 1 M→**0.5 M** texels,
  and **reworded quality presets**
  (Automatic/Performance/Balanced/Quality/Custom, **none raises the internal
  scale**; the old names low/medium/high/ultra are aliases).
  **🔴 BLURRY HUD (user feedback, 2026-09-19b)**: the life bar "little squares"
  came out dirty. Cause: they are **quads with a tiny UI texture**
  and pure bicubic *rings* at contrast edges. **Fix**: new cvar
  **`dbz3_upscale_min_size`** (default **16**; smaller textures are not scaled) +
  **anti-ringing clamp** in `texture_upscale_cs.hlsl` (result clamped to the
  min/max of the 16 samples). Measured (`dbz3_170`, x3 + 0.5 M): 0 errors,
  min fps 54.7, GPU **39 % / 33 W / 1.67 GB**.
  **🔴 THE COST IS SUPERSAMPLING, NOT HD TEXTURES (2026-09-19c)**: the
  high consumption (80 %/132 W) in the user's capture was from the **old version
  (x4 HD)**; with the current one, measured at 3x internal WITHOUT HD textures = 51 %/50 W, and at
  **1x+FSR = 22-23 %/29-30 W**. `draw_resolution_scale` makes the guest
  really render at Nx (true supersampling; FSR stays inert). **There is no bug**.
  Action (user request "keep 3x but warn loudly"): orange warning
  when `scale>1` + **"Back to native (1x)" button** + cost labels on the
  scale combo + preset/MSAA tooltips clarifying that **no preset raises the
  scale**. `1x` is the default and recommended. **⚠️ An out-of-range cvar value
  invalidates the WHOLE toml** (the old `dbz3_texture_upscale=4` broke it).
  (Later: an out-of-range cvar now only rejects that cvar; see `AGENTS.md` §3.0b.)
  Detail: `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` §9-§16.
- **(2026-09-19) HD Textures — CAUSE OF THE STUTTER FIXED (pending the
  user's visual validation)**: reproduced locally with the tester's EXACT config
  (`hd_tex=4x` + `3x` + MSAA + cap 60). **Root cause**: the shader
  `texture_upscale_cs.hlsl` generated each mip by averaging the
  `2^level × 2^level` block of level 0 (16·4^level SERIAL reads per texel; at
  high mips very few threads remain → hundreds of ms per frame). **Not
  GPU-bound** (which is why an RTX 5090 does not help: same or worse). **Fix**:
  `XeLoadLevelTexel` samples a grid of ≤ `kXeMaxBlockSamples=8` per axis
  (EXACT up to level 3, approximate above; high mips are blurry
  minification). Local measurement (`dbz3_144`→`dbz3_146`): windows <58 fps **10→1**,
  frames >100 ms **14→1** (the only remaining one is a DISK `io SLOW 205127us`
  in `adx_usa.afs`, unrelated to the feature), with scaled `upx` 274→1614. The
  shader is recompiled with `fxc /T cs_5_1 /E main /Vn texture_upscale_cs /O3 /Fh …`
  and `rexgpu-xenos` is rebuilt (patches in `github/patches/`). Detail and FSR/scale
  note in `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` §8.
- **(2026-09-18) Performance + HD textures**: slowness report from the user
  with an RTX 5090 (logs in `Logs SSGPrinceVegeta/parte 2/`; v1.2.1 with
  `internal_scale=3x` + MSAA + VB-Audio Virtual Cable audio). Actions:
  (a) **HD Textures (WIP, OFF by default)**: runtime texture upscaling
  (outer layer, D3D12) **WORKS** —Nx host resource, bicubic and generated mip
  chain, without touching files or guest memory— and it is chosen in the
  launcher's first tab (`dbz3_hd_textures`, Video → "HD Textures (WIP)",
  x2/x3/x4; with `hd_tex>1` the slider "HD texture size limit
  (Mpx)" appears → `dbz3_hd_texture_max_texels` → SDK `dbz3_upscale_max_texels`).
  Scales DXT **and native RGBA8** (2026-09-19) without stutter; the cost is VRAM
  (see §3). It stays **disabled by default** (opt-in); detail + next steps in
  `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` (including why overriding
  the bin does NOT work: it overflows guest memory);
  (b) the **AFS override log** (`AFS OVERRIDE LOOKUP/HIT/MISS`: 2 lines with
  the full path per read) is now **gated by `dbz1_diag_logging`**
  (before unconditional → thousands of lines per session);
  (c) **new instrumentation**: cvar `dbz3_perf_logging` (default true at the time;
  **final v1.2.5 makes it false**) →
  `dbz3: perf fps=… frames=… max_frame_ms=…` every 5 s **on the guest's real
  swap** (`D3D12CommandProcessor::IssueSwap`, rexgpu-xenos; the UI presenter
  only paints the launcher and is useless in a match). Analysis, offscreen
  synthetic tests (harness `tools/hidden_run.ps1`) and next steps:
  `docs/ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md`.
- **v1.2.2 EX published (Latest, 2026-09-17)**: **guaranteed boot — the
  launcher finds the executable by itself** (same base as v1.2.2, which was
  withdrawn: EX adds the missing ISO-mode fixes). Reason: the logs of
  a user (SSGPrinceVegeta, RTX 5090/9950X3D) and of issue #7 (RTX 5080, original
  ISO) showed "I press Play and nothing happens"; ALL died with
  `XThread::Execute - No function registered at 820D54C8` / `0x820D54A8` because
  the **HD Collection menu** was being booted (the `default.xex` at the disc
  ROOT, 3317760 B) instead of `DBZ3/yae3_xenon.xex` (4890624 B). Fixes:
  (a) `ClassifyXexFile` + `XexStatus::kHdMenu` (detects the menu) and
  `XexStatusLabel`; (b) **`FindGameExecutable`**: finds the real executable by
  **size+MD5** in the chosen folder (bounded scan: depth ≤3) and in the
  conventional locations of neighbouring roots (`root`, `DBZ3`, `assets`,
  `assets/DBZ3`); (c) **`EnsureXexCache`**: prepares it as
  `user_data/dbz3/xex_cache/default.xex` (never writes into the user's
  folder); (d) **`ResolveBootSource`/`CurrentBootSource`** = single source of
  truth (xex + data root + status + redirect) + diagnostic logs;
  (e) device shims in `region.cpp` (`GameDataHostDevice` in folder mode
  and `RegionDiscDevice` in ISO) that serve `game:\default.xex` from the cache and,
  on a retail ISO, resolve `us\...` under `DBZ3\` with fallbacks;
  (f) `ExtractGameXexFromIso` tries `default.xex`, `DBZ3/yae3_xenon.xex`,
  `DBZ3/yae3_xenon_eu.xex`… and records it in `source.stamp`; (g) launcher banner
  with "Executable detected: … (nothing needs renaming)", a block with a
  specific HD-menu message, a DBZ1 block and an amber warning for an unknown xex;
  (h) **TOML fix**: `SaveUserSettings` escapes `\`/`"` (idempotent) → no more
  `unknown escape sequence '\G'` that lost the settings with Windows paths.
  **EX adds (2026-09-17, validated with a synthetic XDVDFS ISO)**:
  (i) **`NormalizeGuestPath`** in `RegionDiscDevice::ResolvePath` — the VFS
  hands over the path with the leading separator (`\us\data_cmn.afs`) and the
  region remap + the `DBZ3\` prefix required it not to start with `\` → **on a
  retail ISO NO data was read** (`NtCreateFile FAILED 'D:\us\data_cmn.afs' ->
  0xc000000f`); (j) **folder→ISO fallback**: if the chosen folder has `us/` +
  the menu as `default.xex` (retail dump copied as is), the launcher **uses the
  `.iso` next to it** automatically; (k) ISO mode is not entered if the disc does
  not yield US/EU (`iso_boot.usable()`), and (l) `tools/make_test_iso.py` (test
  XDVDFS generator). Tests: retail layout (root=menu + `DBZ3/`) and ISO mode
  auto-detected and via fallback → **the game boots** (validated locally and
  reported by the user). See `docs/SESION_AUTODETECCION_XEX_2026-09-17.md`
  (§4 and §4.bis).
- **v1.2.1 published (2026-09-14)**: launcher hotfix — (a) **crash on
  close after Model Swap/Textures** (the pipeline thread was left unjoined →
  `std::terminate`; now `~ModPipeline` does `join`); (b) inverted FSR sharpness
  label; (c) the mod list refreshes when the pipeline finishes
  (`ModPipeline::Generation()`); (d) reading the textures folder without
  exceptions. On top of the
- **v1.2.0 published (2026-09-14)**: renewed Mod Center (cached
  list, search, enable/disable all, type badges, alternating rows),
  polished HD↔HD Model Swap (searchable combos, preview, source==target
  guard, manifest with catalog names), adjustable FSR/CAS sharpness,
  ISO-mode notice in Mods and Model Swap. Cleanup: 83 test mods archived
  (release with an empty `mods/`). New docs:
  `docs/ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14.md` (**FSR3/DLSS not viable
  short term**: the renderer exposes no motion vectors/jitter; FSR1/CAS yes) and
  `docs/02_mods/SESION_MODS_LAUNCHER_2026-09-14.md`. Binary 1.2.0; zip
  `DBZ-Budokai-3-HD-Collection-v1.2.0.zip`.
- **v1.1.4 EX published (2026-09-10)**: hotfix of v1.1.4 that closes
  the community issues. (a) **EU crash when starting ANY battle**
  (`0xC000001D`, `ctr=0x820F24D8`): the re-codegen again classified as a
  1-case "jump table" the `bctr`s of `sub_820F2370` and `sub_820BB8C8`
  (dispatch via a function pointer table); any case != 0 fell into
  `__builtin_trap()`. Fix applied to the EU codegen + **`tools/fix_eu_bctr.py`
  rewritten** (it used to fail silently with the new `dbz3eu_sub_*` prefix).
  ⚠️ **ALWAYS run `python tools/fix_eu_bctr.py --apply generated_eu generated`
  after a re-codegen** and check "NO PATCH"/0 sites. (b) **xex detection by
  entry point**: fallback in `CheckDefaultXex` when the MD5 is
  unknown (modified dump/other print run): entry `0x8221DDB0`=US,
  `0x8221C570`=EU (read from the XEX2 header, offset 0x18, key 0x00010100).
  Prevents the dual build from falling back to the US config with an EU xex →
  `No function registered`. (c) **ISO xex cache invalidated** (`EnsureIsoXexCache`):
  stores path+size+date of the source disc in `iso_cache/source.stamp` and
  re-extracts when the ISO changes. Binary `1.1.4.1`; zip
  `DBZ-Budokai-3-HD-Collection-v1.1.4-EX.zip`.
- **v1.1.3**; v1.1.3 "The ISO patch" (2026-09-09):
  source selector always visible (extracted folder / ISO), detection and
  blocking of the DBZ1 xex, fully audited i18n (0 gaps), messages for
  non-technical users, polish to 0 warnings and a stricter packager. Includes
  v1.1.2 (community issue fixes: EU crash `sub_820F2398`
  registered, incomplete regions with `ResolveRegion()`, real Vulkan backend
  with the `gpu_backend` cvar, and **disc mode (ISO)** — plays directly from the
  `.iso`).
- **EU Dragon Universe crash fix (v1.1.4, 2026-09-10)**: `0x8215B378`
  registered manually in the EU codegen (11792 functions, +1). Same pattern
  as `0x820F2398` (function folded as a dead fall-through, only reachable via a
  function pointer). ⚠️ **OPERATIONAL RULES for the EU codegen**: (1) fixes are
  applied MANUALLY to the codegen (the current recompiler generates symbols WITHOUT
  the `dbz3eu_` prefix → collision with US in the dual build; the tested codegen
  came from an earlier rexglue.exe); (2) entries in `dbz3_config_eu.toml` must
  ALWAYS go inside `[functions]`, BEFORE the first `[[switch_tables]]` (otherwise
  the recompiler ignores them and they are lost on every re-codegen); (3) the
  `dbz1_diag_logging` cvar lives in `rexruntime.dll` — if the SDK is reinstalled
  and the dual build fails to link `roster_trace.cpp`, rebuild the baseline
  runtime (`rexglue-sdk-0.10/out/build-win-vulkan-baseline`, targets
  `rexruntime rexgpu-xenos`) and reinstall DLL+lib in `rexglue/`.
  Very functional game: D3D12 main, Vulkan
  experimental, XInput default, keyboard by default (mnk_mode=true), quality
  presets per GPU, real frame_cap, language→game (ES/EN/IT/DE/FR + JP), US
  and EU regions with a **dual core** (a single dbz3.exe detects the xex by MD5).
- **A single universal executable**: SDK built at baseline `-march=x86-64
  -mssse3` (Core 2 2006+); NO ISA bootstrap or variants (§9). Fallback
  `v1.1.0-clasico` (avx2 runtime) published as a non-Latest release.
- **Controller**: `input_backend = "xinput"` (avoids a hang with RTSS/OBS); SDL
  available as a selector.
- **Mods**: per-AFS-entry override + virtual mid-insert (§8). Native HD→HD
  swaps validated (Goten, Vegeta 424, Babidi, Bulma).

---

## B. PS2->B3 HD port research: detail (Phases B/C and GPU)

> Verbatim copy of `### 3.4` (subsections 3.4.1-3.4.9) of AGENTS.md before the 2026-09-26 compaction: table of ways, validated facts, chronology of attempts T2-T11, blockers and draw semantics. It is the detail of why the full port (Way B) does NOT render yet.
>
> **Later corrections:** on 2026-09-30 the bind/skin was found identical to the
> native one (offline oracle), on 2026-10-01 the VB served to the GPU was
> confirmed verbatim, and on 2026-10-03 it was shown that **B3 HD does not skin
> on the GPU** (skinning is CPU-side). See `AGENTS.md` §3.4.6/§3.4.10 and
> `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` §21–§24.

> SINGLE reference for the port. Detailed history: §3.1, `docs/07_ports/` and
> `docs/01_estructura/HISTORICO_AGENTS.md`.

#### 3.4.1 CURRENT STATUS (verified in game 2026-08-26)

| Way | Status | Best result | Notes |
|---|---|---|---|
| Native B3→B3 swap | ✅ WORKS | sw_goten_nativo, sw_vegeta424 | complete #AMB bin in someone else's slot |
| Injection (template + PS2 positions) | ✅ WORKS (recognizable) | **cell_npm4** (binary threshold 0.8) | PS2 body + HD limbs/head |
| Full port (PS2 topology) | ❌ DOES NOT RENDER (2026-09-11) | geometry + **draw CORRECT** (1 strip draw, VB+IB verbatim); **skinning** missing | After §3.4.9 the root cause (list-vs-strip) and the 2nd source (arms) are solved; see §3.4.9 |
| HD→HD head swap | ◑ partial | goku_armadura v3 | z-fighting, paused by decision |

#### 3.4.2 VALIDATED FACTS (how the guest renders)

1. **It draws by the `B` of the 0x60 descriptors + the prim PER DESCRIPTOR
   (proven 2026-09-11, §3.4.9)**: each draw's `(dma-0x1BD00000)//2` == the
   descriptor's `B_start`; the IB is used **verbatim** (33/33 body draws
   match `AwgVertexBuffer.load(port).indices()`). The draw's prim is
   per descriptor: body = `prim=6` (Xenos raw = strip), hands/face = `prim=4`
   (list); it correlates with descriptor field **`+0x48`** (`0x500`=strip,
   `0x400`=list; D3D enum `kTriangleList=4/kTriangleStrip=5`) and with `+0x30` of
   the arms' part descriptors (5/4). **Vertex fetch is GLOBAL**
   (`VF[95] 0x1BD04000 size=5148×44`), so **the `A` ranges are NOT used for
   the fetch**; only `B` + prim matter.
   ⇒ **🔴 ROOT CAUSE of the port (Way B)**: `port_b3_windows.py` emits the IB as a
   **LIST**, but the guest draws the body as a **STRIP** ⇒ wrong triangulation
   ⇒ "explosion". Fix: **emit the IB as a strip** (§3.4.9).
2. **It uses the vertex's bone (+28) for the transform** (bone0 test: bones→0
   collapses EVERYTHING to the feet; upper face and one hand survive → they live in vb2).
3. ~~**There IS a POSITIONAL consumption of the pool (not only via the IB)**~~ ⇒ **🔴
   REFUTED 2026-09-11** (T10: the GPU buffer is a verbatim copy of the pool and the
   guest uses the file's IB ⇒ a consistent relabeling is identity; the
   T3/T4/T9 deformation was an **index-base bug in the tool**, not a
   positional consumer — see §3.4.6.1 and `SESION_GPU_DRAW_2026-09-11.md` §6-7).
   Historical context of Phase B (2nd iteration 2026-09-10), now superseded:
   - **Hard proof**: following the IB index by index, the vertex records
     are **IDENTICAL** in T2, T3 and T4 (`IB-follow same=5125 diff=0`). A
     consistent relabeling (permute the pool + remap the IB) is a
     **geometric identity** → that is why T2 (swap) is identical.
   - **But T3** (pool reverse + remapped IB + recomputed A/B) and **T4**
     (reverse inside each A block, A intact) render **DEFORMED** (the
     user: "exactly the same deformities"). ⇒ the guest does **NOT draw only via
     the IB**: some structure references the pool by position/offset.
   - **H3 (A block = unit) is INSUFFICIENT**: each A block contains 2–85
     **bone runs** (it is not "one block = one bone").
   - **Ruled out**: not a load failure (`AFS OVERRIDE HIT` logs on 327), nor
     compression, nor an IB remap bug (validated by IB-follow).
   - The positional consumption does **not appear** as a raw u16/u32 index in AWG0
     nor with encodings `v*44`, `v*44+sec`, `v<<2`, `v<<8` (scans `phase_b_consumer_
     scan` + `phase_b_deep_scan`). 15 IB entries out of range (2182–2189,
     8 beyond the pool) at the end of the IB → possible additional buffer/pool.
   - **Test T5** (`mods/_t5_noremap`): reverse the pool **without** touching the IB →
     **MUCH WORSE** + face texture stretched over the body.
   - **Test T6** (`mods/_t6_adesc`): pool and IB intact, **rotate ONLY the A
     ranges** between descriptors → **NORMAL**. ⇒ **the A range is NOT used to draw**
     (it is not the positional path).
   - ⇒ **the pool is consumed POSITIONALLY by a path that is NOT A** (T4/T5
     deform with a changed pool; T6 normal with the pool intact). T5≫T4 may just
     be a worse permutation (it does not prove the IB matters).
   - **Test T7** (`mods/_t7_ibrev`): pool intact, **whole IB reversed** →
     **MASSIVE DEFORMITY** (head destroyed, one hand fine, silhouette wrong). ⇒ **the
     IB DOES govern connectivity**. But T4 (consistent IB) deformed ⇒ **there is
     an additional POSITIONAL consumption that is NOT A** (T6).
   - **Historical**: the `DBZ3_DRAW` log proved the guest draws the right
     strips (B_start/B_count) and the amorphous shape came from the **skinning
     structure (arms) tied to the pool order** (`SESION_INYECCION_2026-08-26.md`).
     Consistent with everything: T2 (intra-bone swap) OK, T4 (crosses bones)
     deformed, T6 (A) normal, T7 (IB) deformed.
   - **Two tables** (CORRECTED in Phase C, 2026-09-10): what looked like a 2nd
     descriptor table at `AWG0+0x1F80` is the **bind-pose matrix table**
     (pointed to by the arms' `p2`). The real descriptor table is the
     mesh group's 0x60 one. **A = vertex range of the pool** (§3.4.8) and the
     arms' part descriptors complete the **pool partition**.
4. **The "arms" are pointers to part descriptors (Phase C, 2026-09-10)**:
   `arm = [bone, p1, 0, p2, 0]`; `p1` → **part descriptor** (label + vertex
   range `(start,count)` at `+0x38/+0x3C` + `data_off` at `+0x44`); `p2` →
   **4×4 bind-pose matrix** (64 B) in the `AWG0+0x1F80` table. Refutes
   `CONSOLIDADO §13.5.13` and `port_ps2_to_b3.py` (corrupt pointers). Only 7
   AWG0 bones have an arm with data (0,23,30,36,38,40,47).
5. **sec34 layout** (§3.2): stride 44. The template uses ONLY bones 0-33 in
   sec34 (34-47 go to vb2/other AWGs). ⚠️ **Format C** (Babidi): the marker
   is NOT FFFFFFFF, there is no align +2 and the bone is NOT at +28 (it is at +40). The
   pipeline must AUTODETECT format A vs C.
6. **Cell F2's vb2** = layout B (§3.2) — not yet emitted correctly by the port.
7. **The bin is SELF-CONTAINED** (each character with its A/B/C format; the guest
   autodetects). The number of AWGs/bones varies per character (Krillin 18 AWG/51
   bones; Bulma 2/43; Babidi 1/41).
8. **PS2→bone-local conversion**: `local = inv(world[bone])·model` (verified).

#### 3.4.3 THE TWO WAYS

- **Way A — INJECTION (WORKS)**: keep the template's pool ORDER
  and rewrite +12/+16/+20 (and normals `[nz,-ny,nx]`) with the PS2 geometry
  converted to bone-local. Critical parameter: **binary threshold** (0.8 good,
  2.0 bad; blends/soft ALWAYS bad). Limitation: it is not the PS2 topology.
- **Way B — FULL PORT (❌ DOES NOT RENDER, 2026-09-11)**: the "positional consumption"
  (T3/T4/T9) was an index-base bug in the tool; the GPU draws by the IB over
  the windows (§3.4.9). **Solved**: (a) emit the IB as a **strip**
  (`mod center hd/ports/port_b3_strip.py`); (b) the **2nd draw source** = the
  **arms' part descriptors** (`+0x40/+0x44`), already zeroed. After that only
  **1 draw** remains with a correct VB+IB, **but it is still deformed** ⇒ **underlying
  blocker = SKINNING/RIG** (PS2 skin vs HD animation; `--hd-skin` makes it worse). HD
  is a **REWORK** of the rig, not 1:1. Pipeline: `port_b3_windows.py` +
  `port_b3_strip.py` (+ `--fit` or `grow`). `grow()` OK (tested with `_grow_tpl`).
  ⚠️ Do NOT use as a deliverable.
  **Way A** (injection) is still available but its permutation `(lc[2],lc[0],lc[1])`
  is wrong (natural order); it is kept as a reference.

#### 3.4.4 CHRONOLOGY OF ATTEMPTS (so as not to repeat them)

| Date | Attempt | Result | Lesson |
|---|---|---|---|
| 14/08 | Janemba IW→B3 (v4-v10) | deformed mass | the PS2 parser did not read the real IB (FaceType) |
| 14/08 | Krillin PS2→HD (v1-v7) | silhouette but deformed | HD is a REWORK (0 % match), not 1:1 |
| 17/08 | Native B3→B3 swap | ✅ WORKS | the guest accepts self-contained bins |
| 17/08 | Injection v5-v7 | recognizable, partly deformed | the bone is at **+28** |
| 18/08 | Self-contained bins | PS2 rig solved (chunks) | the HD bin is self-contained |
| 19/08 | Vertex formats | different A/B/C formats | the guest autodetects each bin |
| 26/08 | NPM injection + normals + threshold | **cell_npm4 = BEST** | binary threshold 0.8; blends bad |
| 26/08 | Full port (conv2) | amorphous | wrong A descriptor + reordered pool |
| 26/08 | Reverse test (pool reversed) | deforms | lesson **CONFIRMED** by Phase B (not an artifact) |
| 26/08 | bone0 test (bones→0) | collapses to the feet | **the guest uses the vertex's bone** |
| 10/09 | Phase B: census + T2 (swap 2 verts) | **IDENTICAL** | consistent relabeling + OK IB = geometric identity |
| 10/09 | Phase B: clean T3 reverse | **DEFORMED** | the pool order DOES matter |
| 10/09 | Phase B: T4 reverse within A block | **DEFORMED (same as T3)** | **there is POSITIONAL consumption; the IB is not enough** |
| 10/09 | Phase B: IB-follow T2/T3/T4 | **same=5125 diff=0** | hard proof: the guest does NOT draw only via the IB |
| 10/09 | Phase B: bones in A | 2–85 runs per block | **H3 insufficient** (A is not "one bone") |
| 10/09 | Phase B: T5 (pool rev, IB intact) | **MUCH worse** (face stretched) | a changed pool breaks the render |
| 10/09 | Phase B: T6 (rotate A only) | **NORMAL** | **A is NOT used to draw** |
| 10/09 | Phase B: T7 (IB rev, pool intact) | **MASSIVE** (head broken) | **the IB IS used**; there is extra positional consumption |
| 10/09 | Phase B: "2nd descriptor table @AWG0+0x1F80" | it was the bind-pose matrix table | corrected in Phase C (real: 0x60 descriptors) |
| 10/09 | Phase C: descriptors + arms | **A = VERTEX range; tiles the pool** | **positional consumer = part ranges** |
| 10/09 | Phase C: **T8** permute 2 whole parts (hands) + IB | **IDENTICAL** | **permuting parts is SAFE; each bone run must stay contiguous** |
| 10/09 | Phase C: **T9** reorder mono-bone runs within a block + IB | **DEFORMED** (face/arm) | intra-block order matters; no position→bone table → GPU dependency |

#### 3.4.5 KNOWN BLOCKERS AND ERRORS

1. **The pool is PARTITIONED by part ranges (LOCATED in Phase C,
   2026-09-10)**: the pool cannot be freely reordered because its vertices are
   split into **`(start,count)` ranges per part**, declared in **A of the
   0x60 descriptors** (`+0x50/+0x54`) and in the **arms' part descriptors**
   (`+0x38/+0x3C`). The union of both **tiles the whole pool `[0,n_pool)`
   with no overlaps or gaps** (Cell F2: 29 descriptors + 7 parts = 2937/2937). The
   IB indices (range B) are **global**. This is the "positional consumer".
   The "2nd table @AWG0+0x1F80" was actually the **bind-pose matrix table**.
   See `docs/07_ports/SESION_FASE_C_CONSUMER_2026-09-10.md`. The **fine
   mechanism** remains to be pinned down (T4 deforms even with consistent A+IB) → test T8.
   **✅ T8 (2026-09-10)**: permuting **whole parts** (2 hands) + remapping the IB
   → **IDENTICAL in game**. ⇒ **the GLOBAL order of parts is free**, but each
   **bone run must stay contiguous** (T4 deformed by mixing runs within
   a block; T2 was identical because it did NOT cross runs). ⇒ **Way B = engineering**
   (coherent pool/A/B/IB emission), no longer a mystery.
   **Verified** (`awo_tools/awg_invariants.py`): parts are **NOT** bone-homogeneous
   (Krillin 14/18 and Cell 28/35 mix bones).
   **✅ T9 (2026-09-10)**: reordering the **mono-bone runs WITHIN a block** +
   remapping the IB (geometric identity) → **DEFORMED** (face/arm). ⇒ **intra-block
   order matters**; the "run" is NOT enough. A **position→bone table** was searched
   for (`phase_c_find_bonemap.py`, u8/u16/u32) and it does **NOT exist**; and `+28`
   **is** used (bone0). ⇒ the dependency is **not in the bin**: it belongs to the
   **draw/vertex fetch (GPU)**. ⇒ **Way B cannot be rebuilt blindly**: it requires
   **RE of the draw at GPU level**. The only safe thing is **moving whole parts** (T8).
2. **H3 insufficient**: A blocks contain 2–85 bone runs; they are not
   "one bone per block". The contiguous A partition is real but not the cause.
3. **vb2 layout B** of Cell F2: not yet emitted correctly by the port.
4. **`port_ps2_b3_inject.py` hardcodes `axes_base = mg+0x6E0`** (Cell F2 only).
   It must use the AWG `+0x14` field. `port_ps2_b3_pack.py` keeps the template's
   arms/mesh-ref (contradicts the correct Way B).
5. **⚠️ Test contamination**: `AfsFindModOverride` serves the FIRST active
   mod (alphabetical order). A forgotten mod invalidates tests on the same slot.
   → **ONE active mod per test**.
6. **AWG0/sec34 growth**: in excess → crash 0x856AC389 (historical §27).
   For the port use counts ≤ template or solve the growth.
7. Soft/blends (npm6/npm7) and threshold 2.0 ALWAYS make it worse vs npm4.
8. **PS2 source**: the `ps2_games/*/data_cmn.afs` ARE authentic LE #AMO0/#AMG
   (B3 GH 558 #AMO0 / 0 #AWO). The "source block" of
   `SESION_BABIDI` was an error of the tool that inspected the entry.

#### 3.4.6 NEXT STEPS (order of progress)

0. **RE of the draw at GPU level (2026-09-11) — DONE**. Instrumented
   `rexglue-sdk-0.10/src/graphics/command_processor.cpp` (log `dbz3_draws.log` +
   `dbz3_vf.bin` next to the exe; marker `dbz3_drawlog.on`). Captures: indexed
   draws (`src=0`, int16), the vertex buffer is a **VERBATIM copy** of the
   `[vb0, ib)` region of the AWO. Detail: `docs/07_ports/SESION_GPU_DRAW_2026-09-11.md`.
   ✅ **Instrumentation REVERTED (2026-09-12)**: the `command_processor.cpp` edit
   was undone (`rexglue_dbz3_path` + the `kDMA` case logging block), baseline
   `rexgpu-xenos` was rebuilt (6165504 B, no `dbz3_draws.log` marks) and
   reinstalled in the game build; test artifacts archived in
   `%TEMP%\opencode\draw_evidence\`. The canonical DLL is **NOT** instrumented anymore.
1. **Way B — ❌ DOES NOT RENDER (2026-09-12)**. The GPU vertex buffer is a
   **VERBATIM copy of the `[vb0, ib)` region of the AWO** (`ib = awg0+g(0x30)`;
   `vb0 = ib - g(0x2C)`; `g(0x2C)` = **buffer SIZE in bytes**), made of
   **N self-contained 44 B windows**:
   ```
   +0 pos.xyz(3f) | +12 w | +16 bone(u32,1B) | +20 nrm.xyz(3f) | +32 FFFFFFFF | +36 uv.xy(2f)
   ```
   The IB (`g(0x30)`, int16/u16 BE) references window indices (0..N-1). **T11**
   (reverse of the windows + `IB'=perm[IB]`) → **totally identical** (consistent
   relabeling is identity). The "positional consumer" of T3/T4/T9 was an
   index-base bug in the tool (`sec+2` grid misaligned by +428 B).
   **Canonical tool**: `awo_tools/awg_vertex_buffer.py` (`info`/`permute`/
   `roundtrip`/`grow`/`selftest`; `bind_worlds()`/`bone_labels()`/
   `window_from_model()`; API `load().vertices/.indices/.emit()`).
   **SEMANTICS**: `pos = inv(world[bone])·model` and
   `nrm = inv(world[bone]).R·model_nrm`, **NATURAL order (x,y,z)**.
   ⚠️ **The template's IB is NOT a list but a STRIP (prim=6) on the body** →
   see **§3.4.9 (definitive, 2026-09-11)**.
   **Converter**: `mod center hd/ports/port_b3_windows.py <extract.json> <tpl.bin>
   <out> [--fit|--no-grow|--hd-skin]` (maps bones by label).
   **🔴 REAL STATUS → SEE §3.4.9**: the port has **geometry + draw CORRECT**
   (1 draw `prim=6` strip, VB+IB verbatim) and the remaining blocker is
   **SKINNING/RIG**. The old hypothesis "the A/B ranges and the mesh-refs must be
   rebuilt" was **SUPERSEDED** by §3.4.9.
   **`grow(new_n,new_nib)`** enlarges windows+IB. **2 bugs fixed 2026-09-12**:
   (a) the AWG table (relative to `awo`) was readjusted **twice** in the
   `#AWO` header loop → 16 entries pointed to garbage → `#AMB` parser crash; (b)
   **`AWG0+0x2C`** (buffer size) **was not updated** → the GPU only fetched
   the old windows. It still **does not render well** after both fixes.
   Test: PS2 Cell → template `e147` → mod `cell_viab`/`cell_viab_grow` (147),
   `_grow327` (port in Krillin slot 327). `cell_native` (327) = native swap
   (renders perfectly, but it is NOT the port).
   ⚠️ The old pipeline `mod center hd/ports/port_ps2_b3_{geometry,draw,pack}.py`
   used A/B descriptors + separate buffers (WRONG model) → rebuild
   on top of `awg_vertex_buffer.py`. Detail: `SESION_GPU_DRAW_2026-09-11.md` §6-9 +
   `SESION_VIA_B_RENDER_2026-09-12.md`.
2. **Way A (practical)**: re-enable/refine `cell_npm4` (NPM injection, threshold
   0.8). It is the validated deliverable.
3. Fix the pipeline (if resumed): `geometry.py`, `inject.py` (`axes_base`
   `+0x14`), autodetect A/C.
4. Close `vb2` (layout B) for face/legs.
5. For a playable state now: **re-enable `cell_npm4`** (Way A, best injection).

#### 3.4.7 REFERENCES

- `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md` (Phase B: arms, census, T2/T3/T4).
- `docs/07_ports/SESION_FASE_C_CONSUMER_2026-09-10.md` (Phase C: pool partition
  by part ranges; correction of the "2nd table").
- `docs/07_ports/SESION_GPU_DRAW_2026-09-11.md` (GPU RE of the draw: instrumentation,
  capture of 318 indexed draws, derived buffer; next steps).
- `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` (**definitive + RESUME §0**:
  the guest uses the port's IB verbatim, draws by the descriptors' `B`, prim per
  descriptor at `+0x48`; list-vs-strip = root cause; **2nd draw source** =
  arms part-desc. `+0x40/+0x44`; attempts `_desc_one`/`_strip2`/`_strip3`/
  `_hdskin_strip`; **remaining blocker = SKINNING**; repro commands and
  next step in §0).
- Instruments: `awo_tools/awg_vertex_buffer.py` (⚠️ **canonical for Way B**: window
  model + IB; `info`/`permute`/`roundtrip`), `awo_tools/phase_c_make_t10.py`
  (sec34 reverse, guest base), `awo_tools/phase_c_make_t11.py` (permute windows),
  `awo_tools/phase_c_descriptors.py`, `phase_c_arms_targets.py`,
  `phase_c_meshgroup.py`, `phase_b_census.py`, `phase_b_consumer_scan.py`,
  `phase_b_make_t2.py`, `phase_b_make_t3.py`, `phase_b_make_t4.py`,
  `phase_b_make_t5.py`, `phase_b_make_t6.py`, `phase_b_make_t7.py`,
  `phase_b_desc_detail.py`, `phase_b_deep_scan.py`, `phase_b_ab_compare.py`,
  `phase_b_arms_dump.py`, `afs_extract_hd.py`.
- Test mods: `mods/_t2_swap` (identical), `mods/_t3_reverse`/`_t4_inpart`
  (deformed), `mods/_t5_noremap` (much worse), `mods/_t6_adesc` (normal),
  `mods/_t7_ibrev` (massive). ONE active at a time.
- `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md`, `SESION_INYECCION_2026-08-26.md`,
  `SESION_PORT_RE_2026-08-26.md`, `SESION_VIA_B_RENDER_2026-09-12.md`,
  `HOJA_DE_RUTA_PORT_PS2_B3.md`.
- Pipeline in `mod center hd/ports/` (`port_ps2_b3_extract/geometry/draw/pack/
  verify.py` + `port_ps2_b3_inject.py`).

#### 3.4.8 0x60 DESCRIPTORS AND POOL PARTITION (Phase C, 2026-09-10)

**0x60 descriptor** (located by the ASCII tag `"max N m"` at `+0x18`):
```
+0x00 label[]     +0x18 "max N m"   +0x44 type==0x2C00
+0x50 A_start<<8  +0x54 A_count<<8     A = pool VERTEX range
+0x58 B_start<<8  +0x5C B_count<<8     B = IB INDEX range
```
- **A tiles the pool** `[0, n_pool)` **without overlaps**; the IB indices (B) are
  **global** (`min==A_start`, `max==A_start+A_count-1`).
- The part descriptors (arms) have the range at `+0x38/+0x3C` + label at
  `+0x48`; they **fill the gaps** of the main table.
- **Total partition (Cell F2)**: `[0,2937)` = 29 descriptors + 7 parts, 0
  overlaps, 0 gaps. `awo_tools/phase_c_descriptors.py` builds the map.
- 4×4 bind-pose matrix (64 B) of each arm in the `AWG0+0x1F80` table (the `p2`).

#### 3.4.9 DRAW SEMANTICS AND ROOT CAUSE OF THE RENDER (2026-09-11)

> Full detail: `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`.

- **The guest uses the port's IB VERBATIM** (33/33 body draws match
  `AwgVertexBuffer.load(port).indices()` at `(dma-0x1BD00000)//2`). ⚠️ The earlier
  note "the guest's IB ≠ file" was a comparison **offset error**.
- **Draws = 0x60 descriptors**: `(dma-0x1BD00000)//2 == B_start` (exact match).
- **Prim PER DESCRIPTOR**: body `prim=6` (strip), hands/face `prim=4` (list);
  descriptor field **`+0x48`** (`0x500`/`0x400`) and `+0x30` of the arms'
  part-desc. (5/4). SDK enum: `kTriangleList=4`, `kTriangleStrip=5`.
- **GLOBAL vertex fetch** (`VF[95] 0x1BD04000 size=5148×44`); **the A ranges
  are not used for the fetch**.
- **🔴 ROOT CAUSE**: the port emitted the IB as a **LIST** but the guest draws the
  body as a **STRIP** ⇒ explosion. The port's geometry (windows + IB) is
  **correct** (perfect offline render: `%TEMP%\opencode\phaseb\view_port.png`).
- **Fix in progress**: emit the IB as a **strip preserving winding**
  (tool `mod center hd/ports/port_b3_strip.py`; validates `orient_mal=0`).
- **Attempts and results (do NOT repeat)**:
  - `_desc_one` (1 descriptor `B=[0,n_ib)`, `+0x48=4` list, the rest `B_c=0`):
    **still explodes** ⇒ `+0x48` is **not** enough to change the draw's prim.
  - `_strip2` (IB as a strip + 1 descriptor): **the deformity changed** (head/
    torso/arm are recognizable) **but it still exploded** (flap) ⇒ there was
    **another draw source** (solved in `_strip3`: the arms `+0x40/+0x44`).
  - **`_strip3`** (strip + `desc[0]` + zero the arms' `+0x3C` **and `+0x44`**):
    "log all" capture ⇒ **ONE real draw remains** (`prim=6 idx=8726 off=0`); the
    guest's VB is a **verbatim** copy of the file and the IB matches ⇒ geometry/draw OK.
    **But it is still deformed ⇒ the remaining blocker is SKINNING.**
  - **🔴 2nd DRAW SOURCE LOCATED (2026-09-11)**: the **arms' part descriptors**
    hold `+0x38 vert_start`, `+0x3C vert_count`, **`+0x40 idx_start`,
    `+0x44 idx_count`** and a label at `+0x48`. The `+0x40/+0x44` produce EXTRA
    draws (hands/face) at the template's offsets. Zeroing only `+0x3C` is NOT
    enough: `+0x44` must **also** be zeroed. (`port_b3_strip.py` already does it.)
  - **Skinning = underlying blocker**: the mesh carries the **PS2 skin**; the HD
    animation deforms it (in bind it is not visible). ~66 % of bones differ from the
    nearest HD neighbour, and **`--hd-skin` by nearest vertex MAKES IT WORSE**
    (`_hdskin_strip`, tested). It is the underlying problem: **HD is a REWORK of the
    rig**, not 1:1. Next: (1) restrict to bones 0-33 (body) to isolate hands/face;
    (2) a better HD skin transfer than nearest; (3) port by regions in AWG1-16.
  - **ISOLATION + GPU EXPERIMENT (2026-09-13)**: the AWG0 template uses ONLY
    bones 0-33; the port puts 1638 refs to 34-47. Test `_body33` (≤33) → **also
    explodes** ⇒ it is not (only) 34-47. The runtime was instrumented to dump per draw
    the **`fc=94` palette + VB + IB** (`dbz3_capture.bin`): **the guest's VB is a
    VERBATIM COPY of the bin** and **the palette is IDENTICAL between the port
    (explodes) and the native `_grow_tpl` (renders PERFECTLY)** ⇒ **the palette/draw/IB
    are NOT the problem**. 🔴 **The fault is in the windows' `(pos, bone)` data (the
    PS2 skin).** The palette (128×48 B/draw) has an **undecoded** `bone→slot` mapping
    (it is not indexed by the raw bone). Next: fix the PS2 skin
    (weight tables, 2 influences — see `INVESTIGACION_PS2_HD_2026-09-13.md`).
    Instrumentation **REVERTED**; clean DLL reinstalled. Mods: `_body33`,
    `_nottail`; session detail §8/§10. Usable deliverable = `cell_best2` (Way A).
  - **SKIN AUDIT + `_bone0port` (2026-09-13b, session §12)**: the PS2 skin
    (`port_ps2_b3_extract.py extract_skin`) only covers **3922/5148 verts** (the
    rest, hands/face, fall onto the PART's bone); weights 0.2–1.0 are **2
    influences collapsed into 1**. `port_b3_windows.py` assigns `hb=bmap[ps2_bone]`
    (for Cell F2 PS2 labels==HD ⇒ identity). Test `_bone0port` (everything rigid to
    bone 0) → **CRASHES**; consistent with the **captured palette's record 0
    being ALL ZEROS** ⇒ **the palette slot is NOT indexed by the raw bone** (undecoded
    `bone→slot` remap; the 48 B layout is not the naive 3×vec4 either).
    **Next**: decode the layout + `bone→slot` of `fc=94` with the saved captures
    (`%TEMP%\opencode\port3\capture_native\`), validating against the
    NATIVE; then the PS2 skin (2 influences). ⚠️ **Do NOT retry `_bone0port`**.
  - **🔴🔴 IB BUG SOLVED — the "explosion" was NOT the skin (2026-09-13c)**:
    crossing the captures showed that the IB the guest uses **diverges from the bin
    at index 6301**: from there on there is GARBAGE (`0xAAAA`, `0xFFFF`, indices up to
    63891). Cause: **`awg+0x34` = IB SIZE in bytes** (`== 2*n_ib` in ALL the
    template's AWGs: AWG1 816=2*408, …) and **`grow()` did NOT update it**
    → it stayed at 12602 (the original template's IB) → the guest only served 6301
    indices and the rest was garbage → out-of-range vertex fetch → **explosion**.
    **FIX**: `awg_vertex_buffer.grow()` now does
    `set32(awg0+0x34, new_nib*2)`. Rewrites the render: **it NO LONGER explodes** — a
    connected Cell comes out (though deformed). Pipeline (windows+IB+draw+palette+grow)
    **VALIDATED**: test `_strip4r1` (EVERYTHING rigid to bone 1, pos=inv(world[1])·model)
    → **PERFECT Cell Form 2 in T-pose with textures** ⇒ the pipeline is fine.
    **REMAINING = SKIN/ANIMATION**: with the real PS2 bones (`_strip4`) or with a
    skin transferred from HD (`_strip4hds`) it is still deformed; with **`w=1.0`**
    (`_strip4w1`) it improves (leg+waist fine, torso/arms wrong). The PS2==HD `world`
    (48/48) and labels 48/48 ⇒ skeleton and mapping correct. ⚠️ Earlier skin
    conclusions (made with the broken IB) are INVALID. Working mods:
    `_strip4` (ps2 skin), `_strip4r1` (rigid bone1 = OK), `_strip4w1`, `_strip4hds`,
    `_strip4b33`, `_strip4nt`. Docs: `SESION_DRAW_SEMANTICS_2026-09-11.md` §13.
  - **🔴🔴 SKINNING VS DECODED (2026-09-13e, session §15)**: enabled the
    **`dump_shaders`** cvar (already in the SDK; `flags.cpp`/`translator.cpp:339`/
    `shader.cpp:122 DumpUcode`; any cvar in `dbz3_user.toml` is applied via
    `rex::cvar::LoadConfig`) → `%TEMP%\opencode\shaderdump\` with 91 VS + 54 FS
    (`.ucode.vert`, Xenos). The **skinning VSs** are those that fetch **Stride=11
    (VB) and Stride=12 (palette)**: 6 files. **Palette (48 B/bone)** =
    `[T.xyz][qA.x][qB.xyz][qA.y][qC.xyz][qA.z]` (3 interleaved vec4); skinning
    `model = R(qA)·pos + T`. `pos` (off 0) = **bone-local**; `bone` (off 4 dw =
    byte 16) = **DIRECT index into the palette** (`vf1+bone*48`, NO remap or 2nd
    bone); `weight` (off 3) = **intra-bone blend** (weight=1 ⇒ rigid); no
    scale. Then `c0..c3` = world·view·proj. Validated (native ⇒ coherent humanoid
    with the decoded palette).
    **🔴 REAL BUG**: the palette has **NaN on bones 42-49** (the game does NOT
    define them; the template's AWG0 only animates certain bones). The **native does
    not use them**; the **port DOES use 43-47 (tail)** → `R·pos+T = NaN` → flying
    geometry. Remapping those bones ⇒ finite bbox, **but the render is still
    fragmented** ⇒ there is ANOTHER cause. **Next**: (1) remap/clone the port's
    bones 42-49; (2) with the decoded palette, compare `R(qA)·pos+T` port vs native
    vertex by vertex.
    ⚠️ **REMOVE `dump_shaders` from `dbz3_user.toml`** when done. Script:
    `%TEMP%\opencode\port3\decode_pal_repro.py`. Detail: session §14/§15.
    (Later refuted on 2026-10-03: no VS indexes constants dynamically and the body
    VS is a rigid transform with one matrix; B3 HD skins on the CPU. See
    `AGENTS.md` §3.4.10.)
  - **🔴🔴 ROOT CAUSE: OUR `world` IS WRONG (2026-09-13f, session §16)**:
    rebuilding the **NATIVE** model with **our `world`** (`world_ours[b]·pos`,
    with the correct LIST triangulation) gives a **WRECKED** render; with the game's
    palette (`R(qA)·pos+T`) it gives a coherent humanoid. The palette's `T` (real bone
    origin) do NOT match our `world`: bone 1 (waist) palette
    `(0.92,7.23,-0.11)` vs ours `(0,0,0)`; bone 2 palette y=7.80 vs ours y=0.65.
    ⇒ **`awg_vertex_buffer.bind_worlds()` does NOT give the real bind**: the AWG axes
    (stride 80) have **~0 translations** → accumulating through the parent gives
    wrong frames. ⚠️ **The offline bind render is ALWAYS clean** (`world·inv(world)·model
    = model`, self-consistent) → it does **NOT validate `world`**; nor does the rigid
    test (`_strip4r1`) (a single global transform keeps the model coherent).
    **Consequence**: `window_from_model` does `pos = inv(world_ours)·model` in a
    WRONG frame → the guest (`R_anim·pos+T_anim`) shifts each piece → **the
    deformation** (affects **Way B and Way A**). The PS2 skin was NOT the problem.
    **Next**: find the real bind (identity animation frame; an alternative axis
    convention; zones `AWG0+0x1F80`/`+0x2000`; or derive it from the
    animation's frame 0). Files: `nat_world_LIST.png` (wrecked) vs
    `dec_native.png` (coherent) in `%TEMP%\opencode\port3\`.
  - **`_grow_tpl`** (NATIVE Cell F2 template passed through `grow()` to 5148/8724,
    touching nothing else): **renders PERFECTLY** ⇒ **`grow()` is FINE**;
    ❌ **do NOT blame `grow()`**. The port's flap comes from a **2nd draw source**
    or from the port's data.
  - `_fit_strip` (`--fit`): **invalid** — `cluster_fit` decimates and deforms the
    mesh; useless for validating the render.
  - **🔴 BIND INVESTIGATION (2026-09-13g)** — see `SESION_DRAW_SEMANTICS_2026-09-11.md` §17.
    Verified: (1) window layout correct; (2) AWG0 uses bones 0-33 with
    correct labels; (3) the `+0x40 rel awg0` hierarchy of `bind_worlds()` is
    CORRECT; (4) **NO axis convention rebuilds the bind** (exhaustive
    search; border-edge metric ≥3.0 for a ~13 u character);
    (5) **there is NO bind matrix table** in the file; (6) the `fc=94` palette
    (128×48 B, `model=R(qA)·pos+T`) is IDENTICAL port/native = the only reliable
    source and `P = M_anim·M_bind^-1`; (7) **`P[b]` is NOT bone `b`'s transform**
    ⇒ the palette's **`bone→slot` mapping** remains to be decoded; (8) raw `pos`
    also comes out spiky ⇒ it is bone-local and needs the bind.
    **Next (decisive)**: dump per draw the palette + the raw `bone` per
    vertex and correlate `bone→slot` with the native's correct render; or RE the
    PPC function that fills the palette. Short path to a render: bake the captured
    palette as bind (`pos_port = P_ref[b]^-1·model_ps2`).
    **🔴 CORRECTION (2026-09-13g, part 2)**: rendering ONLY the origins of
    `bind_worlds()` (bone→parent lines, `skel_worldT.png`) shows a **PERFECT
    T-POSE skeleton** ⇒ **`world`=bind and the `bind_worlds()` hierarchy is
    CORRECT** (it had been wrongly assumed broken). `skel_paletteT.png` is NOT a T-pose
    ⇒ **the palette = `M_anim` (select pose)**, not the bind. But `world·pos` is still
    deformed even with the correct STRIP triangulation ⇒ **the missing link is the
    mapping `vertex bone index → skeleton bone` (σ)**, not the bind.
    A greedy edge solve (`nat_world_solvedsigma.png`) lowers the distortion but
    falls into a local minimum. **Best next step**: dump from the guest the **real
    inverse-bind buffer** (or the `M_bind` matrix), or solve σ with a better init.
- **🔴 Tool bug fixed**: `awo_tools/awg_vertex_buffer.py` `_parse` used the
  **max IB index** for `n`/`vb0`; in files grown with `grow` (an IB that
  does not reference the new stretch) it computed `vb0` wrongly. It now uses
  **`g(0x2C)//44`** (the real size of the window buffer, the one the guest uses).

---

## C. Launcher: complete functional detail

> Verbatim copy of `## 8. LAUNCHER` of AGENTS.md before the 2026-09-26 compaction: executable resolution, ISO mode, TOML, video/scale, audio, update check, stamp/mixed install, input, diag.


- Tabs: Video / Upscaling / Audio / Input / Mods / Model Swap / Textures / Dev.
  Footer with a **green PLAY always visible** (the tabs reserve their height) +
  summary "Start: region-backend-scale-effect-language" + region selector.
- **Language** (`dbz3_language`): ES/EN/IT/DE/FR + JP (launcher via i18n.cpp
  `kTable[]`; the game via `XGetLanguage`). The i18n file is GENERATED by a
  script (if strings are added, regenerate with `extract_i18n.py`/`gen_i18n.py`).
  (Later: those scripts are not versioned; the table is maintained by hand, see
  `AGENTS.md` §8.)
- **Model Swap (HD↔HD, closed/polished 2026-09-14)**: catalog
  `mod center hd/catalog_b3.cat` (183) → **searchable** combos HD source →
  target slot, **preview card**, warning if source==target, and
  `swap_b3.py` extracts the #AMB bin, compresses LZX /N:2048 and installs it as a
  per-entry override (virtual mid-insert if it exceeds `to_read`). The generated
  manifest uses **catalog names** (`name=Cell Forma 2 en Krillin`,
  `type=swap_b3`, source/target). Disabled in ISO mode (see below).
  `texture_b3.py` extract (PNG) / build (re-encodes DXT3/BC2, keeps the size)
  + target `--slot` + `--dir`.
- **Mod Center (refactor 2026-09-14)**: **cached** list (does not rescan the
  disk every frame), **search** (name/author/source/type), **Enable
  all / Disable all / Refresh** buttons, colored type badges, alternating
  rows and an empty state. Install a mod from a `.zip` (PowerShell Expand-Archive
  via base64 `-EncodedCommand`, immune to spaces; normalizes a single-folder
  wrapper), profiles (`mods/profiles.txt`, cvar `dbz3_mod_profile`), "Open
  folder".
- **⚠️ Disc mode (ISO) — mods are NOT applied**: when playing directly from the
  `.iso`, the per-AFS-entry overrides resolve to host files of the extracted
  folder, so **no mod takes effect**. The Mods and Model Swap tabs show an
  **amber warning** and the swap button is **disabled**.
  To use mods: source "Extracted folder".
- **Dev**: FPS counter, diag logging gated by `DevMode() && DiagLogging()`
  (the .bmp files only with both ON), minidump on crash.
- **Validation banner (v1.2.2)**: uses `CurrentBootSource()` (single source of
  truth), with a blue note "Executable detected: … (nothing needs renaming)",
  a "Select data folder..." button (remounts live via
  `dbz3::RelocateGameData`), PLAY blocked if `!assets_ready` (a single gate:
  button + Enter). Crash window with the code + log path.
- **Executable resolution (v1.2.2)**: `ResolveBootSource()` =
  `CheckDefaultXex` on the canonical path (`<root>/default.xex`, `<root>/assets/…`)
  and, if there is no valid executable there, `FindGameExecutable()` (by **size+MD5**:
  4890624=US, 4890624+MD5=EU; bounded scan of the chosen root depth ≤3 + the
  conventional spots of the neighbouring roots `root`/`DBZ3`/`assets`/`assets/DBZ3`) →
  `EnsureXexCache()` copies it to `user_data/dbz3/xex_cache/default.xex`
  (only if needed) and sets the data root. `GameDataHostDevice` (folder) and
  `RegionDiscDevice` (ISO) serve that `default.xex` to the VFS and prefix `DBZ3\`
  when the data lives there. ⚠️ The `OnConfigurePaths` logs are lost (logging
  starts later), so the diagnosis appears at Play
  (`RelocateGameData`).
- **Source selector ALWAYS visible**: two highlighted buttons
  ("Extracted folder" / "ISO (.iso)") that choose the data source at
  ANY time, not only when assets are missing (the active one is highlighted; choosing
  the other switches the game drive instantly). The launcher tells games apart:
  `ClassifyXexFile` knows DBZ3 US/EU (`A53E...`/`C37E...`, 4890624 B), the
  DBZ1 executable (`5A6AB28A...`, 4464640 B, same for US/EU) → status
  `kDbz1` blocks PLAY with the message "use the dbz1.exe launcher", and the **HD
  Collection menu** (3317760 B) → `kHdMenu` blocks with a specific message. An
  unknown xex (`kUnknown`) warns in amber but does **not** block (modified dump).
  The dbz1 launcher (sibling project) does not tell anything apart yet.
- **Disc mode (ISO, v1.1.2 + v1.2.2 EX)**: cvar `dbz3_iso_path` + an always
  visible "ISO (.iso)" selector.
  Plays directly from the `.iso` (GDFX = **raw XDVDFS**: volume descriptor
  at sector 32 with the magic `MICROSOFT*XBOX*MEDIA`) without extracting anything:
  `OnConfigurePaths` extracts ONLY the executable (a few MB) to
  `user_data/dbz3/iso_cache/` — `ExtractGameXexFromIso` tries `default.xex`,
  `DBZ3/yae3_xenon.xex`, `DBZ3/yae3_xenon_eu.xex`, `yae3_xenon.xex`… and records
  which one in `source.stamp` — and at Play `RemountGameDrive` mounts a
  `DiscImageDevice` (already in the SDK) as `game:`.
  The region is remapped INSIDE the device (`RegionDiscDevice`: `us\`→`eu\`),
  avoiding VFS shadowing (devices are resolved by first prefix match and
  registration order matters). ⚠️ **`ResolvePath` normalizes the path
  first** (`NormalizeGuestPath`): the VFS hands it over with the leading separator
  (`\us\data_cmn.afs`) and without that the region remap and the `DBZ3\` prefix
  were not applied (the guest read NO data: `0xc000000f`). The device serves
  `game:\default.xex` from the cache and, on a retail ISO, resolves `us\...` under
  `DBZ3\` (falling back to the original path). If the disc does not yield US/EU, ISO
  mode is **not** entered (`iso_boot.usable()`). **Folder→ISO fallback**: if the
  chosen folder has no bootable executable (`kHdMenu`/`kMissing`) and there is an
  `.iso` next to it or to the exe, the ISO is played. Mods require the extracted folder.
- **XexStatus**: `ClassifyXexFile` (portable RFC 1321 MD5 + entry point as a
  fallback, size as reinforcement) — US
  `A53E324B5D2A65EBCBF648E4F85A7271`, EU `C37EB979B762DA0AB5B8C9BA8037CE4E`,
  DBZ1 `5A6AB28A4911851FCA955B5925CDFEBB`, HD menu 3317760 B. `XexStatusLabel()`
  gives the text for the UI/logs. With the dual core it accepts US and EU.
- **TOML fix (v1.2.2 + self-repair 2026-09-20)**: `rex::cvar::SaveConfig`
  writes raw values (a path like `E:\Game Roms\…` broke parsing with
  `unknown escape sequence '\G'` and ALL settings were lost).
  `SaveUserSettings` runs the file through `EscapeTomlStrings` (escapes `\`/`"`
  inside quoted values; **idempotent** because `SaveConfig` does not
  rewrite if nothing changed). **On top of that `LoadUserSettings` now SELF-REPAIRS**:
  it validates the file with toml++ (`TomlParses`, reading the TEXT and not the path —
  a folder with non-ASCII characters would break `parse_file`) and, if it does not
  parse, applies `EscapeTomlStrings` and reloads. The state is exposed (`ConfigLoadState`:
  `kOk/kRepaired/kInvalid`) and the launcher shows a notice above the tabs (green
  "recovered" / red "invalid"); if it is still invalid it **does not load** and saves a
  `dbz3_user.toml.bak` copy before the on-close autosave overwrites it.
  ⚠️ `LoadUserSettings` runs TWICE per boot (OnConfigurePaths +
  OnPreSetup) → the `kRepaired`/`kInvalid` state is preserved (otherwise the second
  pass overwrites it with `kOk` and the notice does not appear). `<toml++/toml.hpp>`
  must be included (provided by `rex::runtime`). Covers Prince Vegeta's logs (v1.2.1).
  ⚠️ An **out-of-range** value does NOT break the file: only that cvar is rejected
  (warning `Config: invalid value for cvar`).
- **Video**: presets (`dbz3_quality_preset` **auto/performance/balanced/quality/
  manual**; `auto` detects the GPU via DXGI — the dGPU with the most VRAM — and
  applies a profile; **no preset raises the internal scale**, cap 1x; the old names
  low/medium/high/ultra are accepted as aliases), internal
  scale (draw_resolution_scale_x/y), MSAA, aniso, FSR/CAS, REAL frame_cap
  (0/15-1000; 30 for integrated GPUs), VRR (`dbz3_vrr`), "Game speed: fixed 60".
  In **Upscaling** also: **FXAA** (`dbz3_fxaa` -> SDK `swap_post_effect`;
  none/fxaa/fxaa_extreme; runs BEFORE the upscaler, combines with FSR/CAS and is
  the cheap AA path) and **dither** (`dbz3_present_dither` -> `present_dither`).
  **Texture enhancement (experimental)**: `dbz3_hd_textures` (Off/**Sharp x2**/
  **Very sharp x3**), and the advanced VRAM setting
  (`dbz3_hd_texture_max_texels`, Low/Medium/High) in the Dev tab.
  (v1.2.9) With internal scale > 1x **and** the enhancement enabled, an orange
  warning appears on the option itself: it is the combination of the two expensive
  levers and the most common source of the "it runs at 30" report (frame > 16.7 ms ->
  vsync at half rate). The Dev tab lists the **versions** of the installed files (see stamp).
- **Audio (real since 2026-09-19)**: `dbz3_master_volume` -> SDK **`audio_gain`**
  (SDL callback gain) and a **Mute** checkbox -> SDK `audio_mute`;
  both applied live on change (`ApplyRuntimeSettingsToSdk`). The
  music/SFX/voice sliders were **removed** (the guest mixes everything into a single
  stream: they cannot be separated) and so was the **Gamma** slider (there is no
  gamma cvar in the SDK; it was decorative).
- **Update check** (`src/launcher/update_check.{h,cpp}`, 2026-09-19): on open, a
  background thread queries `api.github.com/.../releases/latest` (WinHTTP) and compares
  with the exe's VERSIONINFO version (4 components, `VersionNewer`:
  `1.2.4-EX` > `1.2.4` but < `1.2.5`, and a local build > 0 counts as a repack ⇒
  an installed EX does not self-notify and 1.2.4 does get the notice); the header
  ALWAYS shows the **installed version** (`CurrentVersionLabel()` =
  "1.2.4 EX") next to the status + a **"Check for updates"** / "Retry" button
  (`RequestUpdateCheck()`, ignored if a request is already in flight); it shows
  "New version available: vX" + a Download button, "Up to date." or a grey note if it
  fails (never blocks PLAY). Toggle `dbz3_update_check` in the Dev tab. Requires
  linking `winhttp` + `version` (CMake).
- **Mixed install / version stamp** (v1.2.9, `update_check.cpp`): the runtime
  DLLs **have no VERSIONINFO**, so they publish their build via cvar
  (`dbz3_runtime_build` in rexruntime, `dbz3_gpu_build` in rexgpu-xenos, from
  `rex/dbz3_build.h`) and the launcher compares major.minor.patch with the exe. If a
  component does not match (or **cannot be identified**: no stamp = earlier
  build) an **orange banner** appears at the top (with the culprit file, a tooltip with
  the fix), a `[warning] instalacion mixta: ...` in the log and the line in the
  Dev tab. Also, **a line `dbz3: entorno os=... ram=... dbz3.exe=...
  rexgpu-xenos=... rexruntime=... amd_fidelityfx_dx12.dll=...`** when the
  launcher starts (real OS via `RtlGetVersion`, RAM and ALL the versions), which is
  what makes a user report conclusive. AMD FidelityFX is listed but
  not compared (third-party). `verify_release.ps1` checks that the stamp
  matches `src/version.rc`.
- **Input**: `dbz3_input_backend` (xinput/sdl), `dbz3_mnk_mode` (keyboard,
  default TRUE), `dbz3_mnk_mouse`, **mouse sensitivity**
  (`dbz3_mnk_sensitivity` 0.1-5.0 -> SDK `mnk_sensitivity`; slider only visible
  with the mouse enabled), deadzone/rumble, 24 keybinds
  (`dbz3_keybind_*`, format `Key`/commas/Shift+/Ctrl+/Alt+).
- **Dev — GPU diagnostic levers** (2026-09-19): `dbz3_async_shaders` ->
  `async_shader_compilation` (off = compile shaders immediately: no stutter,
  slower initial load) and `dbz3_occlusion_queries` -> `occlusion_query_enable`
  (off = no occlusion waits, more overdraw). They help separate a shader
  compilation stutter / an occlusion wait from a real performance problem
  without recompiling.
- **Writable user data** (`settings.cpp`, 2026-09-19): `UserDataRoot()`
  and `UserSettingsPath()` use `<exe_dir>/user_data/dbz3` and `<exe_dir>/
  dbz3_user.toml` (portable) **if writable**; otherwise (Program Files,
  network share, blocked OneDrive) they fall back to `Documents/dbz3` (the SDK's
  `GetUserFolder()` = `FOLDERID_Documents`, the runtime default with an empty
  `user_data_root`). Real probe (create + write/delete `.dbz3_write_test`), cached; the
  Dev tab shows the chosen path. Without this, saving failed silently.
  (The PS5 build pins these under `/data/dbz3/`; see `docs/PS5.md`.)
- **Autosave**: changes are persisted when marked + `SaveUserSettings`
  in OnClose (does not depend on "Save settings").
- **QoL on focus loss (v1.2.5)**: section **"When leaving the window"** at the
  top of the Video tab with two checkboxes. `dbz3_mute_unfocused` (default ON)
  reaches the SDL callback through the `dbz3_window_focused` cvar, which the app writes in
  `Dbz3App::OnWindowFocusChanged` (`src/main.cpp`); `dbz3_dim_unfocused`
  (default ON) paints a full-screen ImGui overlay from
  `DebugOverlayDialog::OnDraw` ("Game in background" + notice). **There is NO
  real pause**: no safe mechanism exists (suspending guest threads can
  hang); the game keeps running. Standard in other emulators
  (Dolphin/RetroArch/PCSX2).
- **I/O diagnostics (v1.2.5)**: `dbz3_io_logging` (default **OFF** since the
  final v1.2.5; checkbox in the Dev tab) emits every 5 s
  `dbz3: io reads=… phys=… cache=… mb=… pre_avg_us=… read_avg_us=… p95_us=…
  p99_us=… max_us=… slow=… opens=…` from `HostPathFile::ReadSync`, plus a
  line per read > `dbz3_io_slow_ms` (25). It separates "slow disk"
  (high read_ns) from "host overhead" (high pre_ns). `dbz3_io_readahead`
  (default ON, `_kb`=2048) reads ahead on sequential accesses **only if there are
  no mods**; it helps on mechanical disks. The `perf` line also carries **`fg=`**
  (window focus): Windows/DWM limits a visible unfocused window to HALF (60→30
  exactly) — it is not the game being slow. Also, `logging.cpp` **prunes old
  `dbz3_NNN.log` files** at startup (`log_max_files`=20), so logs do not
  pile up (138 → 20 in the test).

---

---

## D. Verbatim snapshot of AGENTS.md before the compaction (2026-09-26)

> The original Spanish file kept here a COMPLETE copy of the v1.2.9 AGENTS.md
> (117 KB, 1685 lines) exactly as it was before the 2026-09-26 compaction, so
> that nothing from that document could be lost.
>
> **In this English version the snapshot is not reproduced.** Its content is
> already covered three times over: §A–§C above carry the long blocks that were
> moved out, the current English `AGENTS.md` carries everything still
> operational, and `HISTORICO_AGENTS.md` carries the earlier history. The
> untouched Spanish snapshot remains available in git history: run
> `git show 1dbccb17a243713cf98cfca850cbc21c3fb843be:docs/01_estructura/HISTORICO_RELEASES.md`
> and look for the heading `## D. Snapshot verbatim del AGENTS.md previo a la
> compactacion (2026-09-26)`.

---

## E. RELEASE_README - verbatim changelog (v1.0.5 -> v1.2.8.2)

> Verbatim copy of the `Novedades de esta release` (what's new) + `Historial de
> versiones` (version history) blocks of `github/RELEASE_README.md` before its
> compaction (2026-09-26). The per-version detail is kept here; the compact
> version (installation + notes of the latest release + history table) is what
> ships with the game. Do NOT load by default. (Releases v1.3.0 onwards are in
> `CHANGELOG.md`.)

## What's new in this release

### v1.2.8.2 - Texture enhancement no longer tanks FPS (2026-09-24)

Follow-up on the reports of **FPS drops with "Texture enhancement"
enabled**. The first thing was to rule out the obvious: on a test machine with
**exactly the same configuration** (internal scale 3x + MSAA + HD textures
3x + area 1M) the game holds **60.0 FPS**, so it was not "the GPU
can't" — the way the work was spread out was the problem.

- **Cause**: every time a texture is uploaded again, the feature regenerates its
  **full mip chain** (12 levels for a 4K texture). Some textures are
  **rewritten every frame** by the game (the intro video, effect render
  targets): regenerating 12 levels **serially** per frame costs
  **command/CPU** time, not GPU time — which is why **a more powerful card does not
  help** and it does not show in GPU usage. The reporter's logs showed the
  `upx` counter rising to ~665 (**~1 texture re-scaled per frame**)
  while FPS dropped to 31.
- **Fix**: a texture that is re-scaled many times in a short period (or that
  is reloaded only at its level 0) is marked **dynamic**, and from then on **only
  level 0 is regenerated**: the visible image is exact (mips only
  affect minification, and they are kept). Normal (static) textures
  keep being scaled **with their whole mip chain**, as before.
- **Diagnostics in the `perf` line itself**: it now includes the active settings
  (`cfg=scale:3x3 msaa:true hdtex:3 area:1048576 min:16 aniso:5`) and counters
  (`upx=`, `upx_dyn=`, `texload=`). With this **a single log says what you have
  configured and whether the game is re-scaling dynamic textures**, without asking
  for more data.
- **What does NOT change**: static texture quality, texture packs,
  the dump and everything from v1.2.8.1.

If your machine is slow with texture enhancement enabled: update, enable
**"Performance log (every 5 s)"** in the **Dev** tab, play up to the
point where it is slow and attach the most recent `dbz3_NNN.log` (the `perf` line
already carries the configuration and the counters).

### v1.2.8.1 - The dump covers the HUD and packs accept RGBA8 (2026-09-23)

Follow-up on issue #11. Testing v1.2.8, the reporter confirmed it already
dumped and added two things: **almost all HUD textures were missing** (only
some fonts came out) and **some came out as a black square**.

- **The dump now covers uncompressed formats** (RGBA8, RGB565, RGB5A1,
  RGB655, RGBA4, L8, L8A8, RGBA1010102). Before only **DXT** was dumped, so
  the whole HUD/UI (which uses uncompressed formats) was skipped **silently**.
  Measured in the intro: **51 → 194 files** (96 DXT3 + **26 RGBA8** + 72 L8).
- **Unsupported formats now warn** once in the log
  (`dbz3: volcado: formato k_24_8 (fmt=22) no soportado, texturas omitidas`).
- **Packs accept RGBA8 textures** (the HUD ones): before only DXT worked.
  Validated: `pack '...' reemplaza 128x1024 (fmt 6) -> 128x1024 (x1)` and
  `subido 128x1024 (11 niveles)`. 8/16-bit formats are dumped as
  reference, but their pack is **not yet** applied (next step).
- **Cap of 4 versions per texture**: the intro's video texture was
  dumped **frame by frame** (4096 files / **1.4 GB** in 5 min). Now
  it stops with a notice in the log: **194 files / 51 MB** in the same test.
- **The "black squares" are not a bug**: they are DXT3 textures whose alpha channel
  is **all zero** (the game draws those textures ignoring their alpha, but a
  viewer shows them transparent). The DDS is the game's exact data; the
  importer gains **`--opaque-alpha`** to view and use them.
- Includes everything from v1.2.8 (dump fix), v1.2.7 (texture packs on
  D3D12 and Vulkan) and v1.2.6.

### v1.2.8 - Texture dump now works (2026-09-21)

- **Fixed the texture dump (dev)**: when enabling it in the
  **Development** tab, choosing a folder and playing, textures are really written
  (before **nothing was dumped**: the chosen folder never reached the graphics
  engine, so the dump stayed silently disabled). It is the starting point
  for creating your own **texture packs**.
- **Clean log**: the `duplicate registration` warnings for
  `dbz3_texture_dump` and `dbz3_texture_packs` that appeared at every boot are gone.
- Includes everything from v1.2.7 (PCSX2-style texture packs on D3D12 and
  Vulkan) and v1.2.6.

### v1.2.7 - Texture packs (PCSX2 style) (2026-09-21)

- **Texture packs**: you can replace the game's textures with your own
  (for example, AI-upscaled) **without touching the game files or its
  memory**. A pack is a **folder inside `mods/`** with files
  `<hash>_<Width>x<Height>_<suffix>.dds` (or `.png`). The launcher detects them and
  the game applies them on the fly; the **factor (x1..x4) is inferred from the size**,
  no manifest needs writing.
- **Supported formats**: DDS (DXT1/BC1, DXT3/BC2, DXT5/BC3 and uncompressed
  32 bpp) and PNG. Mipmaps are generated automatically (box filter).
- **Works on both backends**: D3D12 and Vulkan (the same pack works for
  both).
- **They take priority over the experimental HD texture enhancement**; they are
  not combined. If something does not fit, the game ignores that file with a
  warning in the log instead of failing.
- **How to create a pack**: enable the **texture dump** in the
  Development tab, play for a while and you will have the textures as DDS. The helper
  `mod center hd/texture_dump_import.py` converts them to PNG and organizes them by
  character; then you upscale them and save them with the pack name.
  `mod center hd/texture_pack.py` validates and lists your packs. Full guide in
  `docs/02_mods/PACKS_DE_TEXTURAS.md`.
- Remember that packs (like all mods) need playing from an
  **extracted folder**; in disc mode (ISO) they are not applied.

### v1.2.6 - Polished HD texture enhancement + self-repairing settings (2026-09-20)

- **Texture enhancement (experimental) really usable**: the
  **stutter** when enabling it was fixed (the mipmap computation walked huge
  blocks; it is now constant time, no stutter) and it also scales **large
  textures** (faces, clothes, stages), not just small ones. It is now
  called "Texture enhancement (experimental)" with **Sharp (x2)** and **Very
  sharp (x3)**; the advanced area setting moved to the Development tab.
- **Clean interface**: the life bar's "little squares" no longer come out
  blurry. A **minimum size** was added (the interface's tiny textures
  are not scaled) and an **anti-ringing clamp** in the filter.
- **The internal scale warns about its cost**: when raising the render scale
  (2x/3x/4x, real supersampling) a **warning** appears plus a one-click
  **"Back to native (1x)"** button. **Quality presets no longer raise the scale**
  (none of them); 1x is the default and recommended value. The high consumption is in
  the scale, **not** in the textures.
- **If the settings file gets damaged, you no longer lose your configuration**: at
  startup `dbz3_user.toml` is validated; if it was broken (for example, a Windows
  path saved unescaped that broke the whole file), it **repairs
  itself** and shows a green notice; if it cannot be repaired, a
  `dbz3_user.toml.bak` copy is kept and a red notice is shown.

### v1.2.5 - Less work per read + what to do when leaving the window (2026-09-19)

- **When leaving the window** (new, at the top of the Video tab): **mute the
  audio** and **dim the screen** while the game is in the background. The game
  keeps running (it is not a pause); when you come back, sound and image are
  restored automatically. It is the usual behaviour in emulators
  (Dolphin/RetroArch/PCSX2) and avoids being bothered by the opening or the music.
- **Disk diagnostics**: `dbz3_io_logging` writes a summary of the reads every 5 s
  (`dbz3: io reads=… mb=… p95_us=… p99_us=… max_us=… slow=…`) and one
  line per slow read. It is the way to see whether a stutter comes from the disk or
  something else, instead of guessing.
- **Focus record in the performance counter**: the `perf` line includes
  `fg=`. Windows limits the presentation of a **visible unfocused** window to HALF
  (60 -> 30 exactly): so a log with `fg=0` reads as "the player
  alt-tabbed", not as "the game is slow".
- **Less work per read** (with no mods installed): the work done on every AFS
  read even without mods (override lookup and a full copy of the
  container table) was removed, and **read-ahead** was added
  (`dbz3_io_readahead`) for mechanical disks: it reads a bigger block
  at once and serves the following reads from memory. On SSD it makes no difference.
- **Translations**: 2 messages that showed in English in Italian/German/French
  (executable detection and the HD menu warning), and the GPU tier ("High"/
  "Medium"/"Low") and mod types, now translated.

### v1.2.4 EX - GPU knobs + portable user data (2026-09-19)

> Replaces v1.2.4 (same content + what follows).

- **FXAA** (Upscaling): cheap edge smoothing that combines with FSR/CAS.
- **Dither** (Upscaling): less banding in gradients.
- **Mouse sensitivity** (Controls): real control of the right stick.
- **GPU diagnostic levers** (Development): compile shaders in the background
  and the game's occlusion queries (to isolate stutters/waits without recompiling).
- **Truly portable user data**: if the game folder is not
  writable, settings and saves move to `Documents/dbz3` instead of failing
  silently (the Development tab shows the path).
- **Clearer version notice**: the installed version always in the header,
  a button to re-check, and a notice that understands repacks (`-EX`).
- Includes v1.2.4: real volume in the launcher, new version notice from
  GitHub, removal of the dead controls (gamma and per-category volume).

### v1.2.4 - Real volume + update notice (2026-09-19)

- **Real volume in the launcher**: the "Master volume" slider and the
  "Mute all audio" switch now really work (before they wrote a
  variable the runtime did not recognize). The runtime adds output
  gain (`audio_gain`) applied in the audio callback.
- **New version notice**: when opening the launcher the latest GitHub release
  is queried and, if there is a newer one, "New version available: vX" appears with
  a download button (never blocks PLAY; can be disabled in the Dev tab).
- **Dead controls removed**: Gamma and music/SFX/voice sliders
  (not applicable: the game mixes everything into a single track). "Reset values"
  now also restores VRR and HD Textures.

### v1.2.3 - Measurable performance + clean logs (2026-09-18)

- **In-game performance counter**: cvar `dbz3_perf_logging` (ON by default)
  writes a line every 5 s to the log with the game's real FPS and the worst frame
  of the interval (`dbz3: perf fps=... max_frame_ms=...`), measured at the guest's swap
  (also works without a visible window).
- **AFS override log silenced**: it stops writing 2 lines with the full path
  on EVERY AFS read (thousands of lines per session). The detail can be recovered with
  `dbz1_diag_logging` (Dev tab).
- **HD Textures (WIP, OFF by default)**: an emulator-style internal filter that rescales
  the game's textures at runtime (x2/x3/x4), without touching its files or its memory
  (it also generates the mip chain). It works and is noticeable in the intro, but it causes
  stutter when loading new textures, so it stays experimental and **disabled
  by default**. Chosen in Video -> "HD Textures (WIP)".
- Base: v1.2.2 EX (executable auto-detection + ISO mode fixes).

### v1.2.2 EX — Guaranteed boot: the launcher finds the executable by itself (2026-09-17)

- **No more renaming or placing anything in a specific way**: the launcher
  looks for the Budokai 3 executable by **size + checksum** (whatever its name:
  `yae3_xenon.xex`, `yae3_xenon_eu.xex`, …) in the folder you choose and in
  the typical locations (`DBZ3\`, `assets\`, `assets\DBZ3\`). It prepares it by
  itself in an internal cache (`user_data\xex_cache\`), **without writing anything to your
  game folder**.
- **Fixed the "I press Play and nothing happens" case** (original disc dump
  not reorganized): before, the **HD Collection menu** at the disc root was
  booted, which is not in the Budokai 3 core, and the game died with a
  cryptic error (`No function registered`). Now the right executable is used and the
  `DBZ3\` folder is mounted as the game drive, so the data (`DBZ3\us\`)
  loads correctly.
- **Disc mode (ISO) with the complete original ISO, validated**: the Budokai 3
  executable is extracted from inside the disc (not the menu) and the data is
  resolved under `DBZ3\` automatically. A path normalization bug that prevented
  reading the data from the disc even with the right executable was also fixed.
  Already repacked ISOs keep working the same.
- **ISO fallback**: if your folder has the data (`us\`) but the executable
  is the collection menu (disc dump as is), the launcher **uses the
  `.iso` you have next to `dbz3.exe`** and boots, instead of blocking.
- **Clear messages**: if you point it at the HD Collection menu, the launcher
  detects it and explains it; if you point it at a DBZ1 executable, it sends you to its
  launcher; an unknown executable (modified dump) warns but lets you play.
- **Fixed a configuration bug**: with `\` in the folder or ISO path, `dbz3_user.toml`
  was saved wrongly (`unknown escape sequence`) and the settings were lost on every
  boot. It is now escaped correctly.
- **Boot diagnostic log**: executable path, size, checksum,
  status, data folder and warnings.

### v1.2.1 — Launcher hotfix (2026-09-14)

- **Crash when closing the launcher after using Model Swap or Textures**: the
  Python pipeline thread was left unjoined and, when the launcher was destroyed
  (pressing PLAY or closing), `std::terminate()` was called. It is now joined
  properly on close.
- **FSR sharpness label fixed**: it showed the scale backwards (0 = sharpest,
  2 = softest).
- **The mod list refreshes by itself** when a swap/texture job finishes (the new
  mod appears without pressing "Refresh"); the "Reset values" button invalidates it.
- **Robustness**: the textures folder is read without exceptions.

### v1.2.0 — Renewed Mod Center + polished HD↔HD Model Swap (2026-09-14)

- **Renewed Mod Center (QoL + visual)**: **cached** list (no longer rescans
  the disk every frame), **search** (by name, author, source or type),
  **Enable all / Disable all / Refresh / Open folder** buttons,
  **colored type badges**, alternating rows and a clear empty state.
- **Polished B3 HD↔HD Model Swap**: **searchable** character dropdowns
  (183 characters, with `[bin N]` and a `[NOT PLAYABLE]` note), a source→target
  **preview card**, warning and block if source==target. The generated mod
  is now named with the **catalog names** (e.g. "Cell Forma 2 en
  Krillin") and enables itself.
- **Adjustable sharpness in Upscaling**: sliders for FSR's **RCAS sharpness** and
  CAS's **extra sharpness** (they were wired but hidden before).
- **Disc mode (ISO)**: explicit amber notice in the Mods and Model Swap tabs
  (mods are **not** applied when playing from the `.iso`); the swap button is
  disabled in that mode.
- **Cleanup**: the 83 test mods were archived (out of the release). The
  release ships with an **empty** `mods/` (README only).
- **Documentation**: new upscaling analysis (**FSR3/DLSS**: the temporal
  upscaler and frame generation are **not** viable short term without exporting
  depth/motion from the renderer; FSR1/CAS are) and performance analysis.

> Performance: the community reports were reviewed. The hard problem
> (a frame cap that did not lock 60) is solved; the rest are modest machines
> (use the per-GPU quality **presets**) or the Vulkan backend (experimental).
> With FSR1 + 2x-3x internal scale it looks good at 1080p+.

### v1.1.4 EX — Hotfix: crash when starting a battle (EU) + xex detection (2026-09-10)

- **Fix for the crash when starting ANY battle (EU)**: the v1.1.4 re-codegen
  had again classified as a single-case "jump table" two `bctr`s that
  actually dispatch through a function pointer table
  (`sub_820F2370` and `sub_820BB8C8`). Case 0 was valid, but any other
  pointer fell into `__builtin_trap()` → exception `0xC000001D` (`ctr=0x820F24D8`)
  when starting a battle, in every mode. Fixed in the EU codegen and the **fixer
  hardened** (`tools/fix_eu_bctr.py`), which failed silently with the new symbol
  prefix (`dbz3eu_sub_*`). **ALWAYS re-run after a re-codegen.**
- **xex detection by entry point (fallback)**: if `default.xex` does not match
  the retail MD5 (modified dump, other print run, recompressed image) the
  dual core fell back to the US config and booted an EU executable with US code →
  `No function registered at <addr>` on the first thread. Now the XEX entry point
  is read (`0x8221DDB0`=US, `0x8221C570`=EU) when the MD5 is unknown, so a
  valid copy of the right variant is detected anyway.
- **ISO-mode xex cache invalidated when the disc changes**: the `default.xex`
  extracted from the ISO was cached under a fixed name and NEVER regenerated; when
  switching ISOs (e.g. US→EU) the old xex was reused and the wrong region/core was
  picked. Now the identity of the source disc (path + size +
  date) is stored and it is re-extracted when it changes.

### v1.1.4 — Fix for the Dragon Universe crash (EU) + preventive thunks (2026-09-10)

- **Fix for the Dragon Universe crash (EU)**: function `0x8215B378` of the
  EU core was not registered (the recompiler had folded it as a dead
  fall-through inside `sub_8215B368`, only reachable via a function
  pointer). When selecting a character in Dragon Universe, the indirect vtable
  dispatch (`caller_lr=0x8209F390`) reached an unregistered address →
  `UNREGISTERED indirect call` crash. Registered as `dbz3eu_sub_8215B378`
  (11792 EU functions, +1). Same treatment as `sub_820F2398` (v1.1.2).
- **15 preventive thunks registered (EU)**: the function pointer tables of the
  EU xex were analyzed and 15 **C++ adjustor thunks** were found
  (`addi r3,r3,-4; b target`) that the guest calls via dispatch tables and that
  were not registered either — the same pattern that caused the crash. All of them
  were registered (`0x82290EE0`, `0x82290F00`, `0x822A6040`, etc.; 11807 EU
  functions in total). This prevents future `UNREGISTERED indirect call`s in menus
  that use those tables.
- **EU codegen rule fixed**: the entries of `dbz3_config_eu.toml`
  must ALWAYS go inside `[functions]` (before `[[switch_tables]]`); a
  misplaced entry is silently lost on every re-codegen (it was the reason
  `0x820F2398` came back). Verified: re-codegen + prefix produces the
  tested codegen + the thunks (0 functions lost).

### v1.1.3 — The ISO patch (2026-09-09)

- **Source selector always visible**: two highlighted buttons in the launcher
  ("Extracted folder" / "ISO (.iso)") to choose the data source at
  ANY time, not only when assets are missing. The active one is highlighted and
  switching changes the mode instantly (persists between sessions).
- **Wrong-game detection**: if you put the `default.xex` of *DBZ Budokai
  HD Collection* (DBZ1, sibling project) by mistake, the launcher recognizes it
  by its MD5 and blocks Play with the message "use the dbz1.exe launcher" — before,
  the DBZ3 core crashed with another game's xex.
- **Fully audited translation**: ALL launcher strings were extracted and verified
  (ES/EN/IT/DE/FR). Fixes: the "ISO (.iso)" button key had no entry and an FPS
  tooltip fell back to English because of a mistyped accent. Result: 0
  untranslated strings, 0 orphans, 0 suspicious ones; verified with a test that
  compiles the real table.
- **Ready for non-technical users**: actionable messages without jargon,
  hints when the wrong folder is chosen ("did you choose `us/`? choose the
  folder that CONTAINS it"), tooltips on the selector, and clear notes when
  disc mode does not support mods.
- **Code polish**: `-Wall -Wextra` across the launcher with 0 warnings;
  4 unused fields and 1 unused constant removed. The release packager now
  rejects run leftovers (`user_data/`, `logs/`, `iso_cache/`,
  `dbz3_user.toml`) in the ZIP.

### v1.1.2 — Community issue debugging + disc mode (2026-09-09)

- **Fix for the Dragon Universe / pause menu crash (EU)**: function
  `sub_820F2398` of the EU core was not registered (the recompiler had
  folded it as dead code inside `sub_820F2370`; it is only reachable via
  the event/battle pointer table `0x8201E348`). It is now extracted and
  registered as `dbz3eu_sub_820F2398`. Closes the crash
  `UNREGISTERED indirect call: target=0x820F2398` when selecting a character in
  Dragon Universe or pressing START during a battle.
- **Fix for incomplete regions (only `eu/` or only `us/`)**: the launcher now
  resolves the effective region with `ResolveRegion()` — if the selected
  region's folder does not exist, it automatically falls back to the one that does.
  Works out of the box with EU-only or US-only data.
- **Backend selector fix (Vulkan)**: the launcher sent its choice to
  a `gpu_backend` cvar that **did not exist** in SDK 0.10 → always D3D12.
  The cvar was added in `rex_app.cpp` (SDK) and wired to `LoadGpuPlugin`.
  Selecting **Vulkan** now really requests the Vulkan backend (verified in
  the published DLL).
- **Disc mode (ISO)**: plays directly from the `.iso` without extracting anything.
  The launcher detects the disc, extracts only `default.xex` (a few MB) and
  mounts the rest from the image. Mods require the extracted folder.
- **Code polish**: warning-free builds, cleanup of temporary debugging
  traces, and a display fix (the footer summary shows "Japanese" when
  Japanese is chosen).

### v1.1.1 — Debugging + Linux groundwork (2026-08-28)

- **No more crash without game data**: if `default.xex` is missing, the game
  tells you clearly how to place your files (instead of opening the
  window and dying with an odd close).
- **Boot diagnostics**: the log records how many milliseconds each
  boot phase takes (if the launcher is slow to appear, the log says where).
- **The `default.xex` MD5 no longer uses Windows CryptoAPI** (portable
  implementation) — first step of the Linux port, no behaviour change.
- **Linux groundwork**: the launcher now conceptually compiles on Linux
  (GPU detection, dialogs and script launching guarded per
  platform; nothing changes on Windows). See `docs/PLAN_LINUX.md`.
- **Internal process**: automatic repo sync (`sync_github.ps1`)
  and package verification before publishing (`verify_release.ps1`).

### v1.1.0 — A single universal executable (2026-08-28)

- **A single `dbz3.exe` for everyone**: the variant launcher and the
  `dbz3_avx2\` / `dbz3_legacy\` folders were removed. The runtime is now
  compiled for the **universal baseline** ISA (SSSE3) → the same package
  works on ANY x64 CPU (Core 2 from 2006 onwards), with nothing to choose.
- **Goodbye to the 0xC000001D on old CPUs**: before, the "compatible" variant
  had to be launched; now there are no variants. One file, one
  folder, one double click.
- **Goodbye to the antivirus false positive**: the executable is NO longer
  compressed with UPX (a pattern typical of malware). Bigger package, no scares.
- All the v1.0.10 fixes are kept (Duel/Start, PLAY button with the
  mouse, EU/PAL, dedicated GPU on laptops).

### v1.0.9 — Guest pacing hardening (V-Sync) + mod center

- **Bug closed: "the game runs super fast when V-Sync is disabled"**. The cause
  was the guest's vblank worker: with the `vsync` cvar OFF the vblank dropped to
  ~1000 Hz and the logic ran ~16x. Now the SDK **clamps the interval** in
  `graphics_system.cpp` (patch #13): the guest's vblank can never be shorter
  than one 60 Hz frame, whatever the cvar state → `vsync=false`
  is a no-op and the game always runs at its speed. Shipped in
  `rexgpu-xenos.dll` (avx2 + legacy).
- **Mod center (Mods tab)**:
  - **Install a mod from a `.zip`**: "Install mod (.zip)..." button → native
    dialog, unzips (native PowerShell, no window) and normalizes the layout
    to `mods/<name>/`.
  - **Mod profiles**: combo to save/apply/delete sets of active mods
    at once; "vanilla" disables all of them (original game).
  - **Open folder** per mod from the list.

### v1.0.8 — Unified names + bilingual documentation

- **`dbz3_core.exe` is now `dbz3.exe`**: the executable inside `dbz3_avx2\`
  and `dbz3_legacy\` has the same name as the root launcher. You only run the
  root `dbz3.exe`; it opens the one inside the variant by itself.
- **Bilingual README**: the repository has `README.md` (Spanish) and
  `README_EN.md` (English), linked to each other. (Since 2026-10-06 the
  repository docs are English-only; `README_EN.md` points to `README.md`.)
- **Polished package documentation**: `README_PRIMER_ARRANQUE.txt` explains the
  two `dbz3.exe` files for a surprise-free first install.

### v1.0.7 — Fix for the EU demo battle crash + dual core + smaller size

- **Fixed the close while the DEMO plays** (the "attract" mode that kicks in
  if you leave the "Press start" menu untouched: on reaching the 3D battle the
  game crashed with `0xC000001D` or *"Call to invalid or unregistered
  function"* in the EU/PAL variant). Causes: three wrong recompiler
  classifications of the EU code (function pointers treated as single-case jump
  tables → UD2 instruction) and a virtual table function that
  had not been compiled. All registered with their exact sizes and validated in
  the full DEMO battle.
- **Dual core**: the package used to carry two separate cores (US/NA and
  EU/PAL). Now `dbz3.exe` (the one in each variant folder) is ONE binary
  that contains BOTH recompilations and picks the right one based on the `default.xex`
  you supply. This simplifies the package (2 CPU variants instead of 4).
- **Lighter**: the compressed dual core goes from ~33.9 MB to ~7 MB per
  variant (UPX -9, verified threat-free by Windows Defender).
- **Reliable boot verified**: opening the package without touching anything
  shows the launcher with its options and the game does NOT start until Play is
  pressed (`default.xex` is detected automatically; region and language are chosen in the
  launcher).
- **Stronger diagnostics**: on every unregistered indirect call the
  target, the guest's `caller_lr` and registers r3/r4/r11 are logged; the crash handler
  dumps the context and the guest registers — all only logged on a crash.

### v1.0.6 — Fix for the close at the intro (0xC0000409 / unregistered function)

- **Fixed the close on reaching the game's intro** reported by several
  users with `0xC0000409` and, in the logs, the message *"Call to invalid or
  unregistered function at guest address 0x82292A58"*. It was a **virtual table
  dispatch function** (vtable thunk, offset +0x14) that the
  EU/PAL executable calls indirectly during the intro and that **was not
  compiled** in the recompiled port. It was registered with its exact size,
  the codegen regenerated and the EU/PAL core rebuilt. **Validated**: the intro
  passes without a close (before it crashed ~1:30 after boot).
- **Stronger boot diagnostics**: if an unhandled exception happens
  when launching the game (the intermittent close that also produces `0xC0000409`),
  the log (`logs/`) now includes **the exception message and the thread's
  stack** so it can be pinpointed in future versions.
- The US/NA core was also validated at the intro (no close).

### Accumulated changes (1.0.5 EX → 1.0.6)

- **Controls (Input tab)**: **the keyboard works out of the box** (emulates the
  controller; menus + battle). You can **remap the 24 keys** (field "Keyboard
  (MnK) mapping", format `Key`, commas = alternatives, `Shift+/Ctrl+/Alt+` =
  modifiers) and enable the mouse as the right stick. Controller: XInput/SDL
  selector, **deadzone** and **rumble** with a real effect (sliders in the tab).
- **Fixed game speed**: the game ALWAYS runs at its correct speed
  (60 logical FPS, synced to the guest's vblank). It can no longer be
  "sped up" by accident.
- **Frame cap** (Video tab): limits your PC's presentation rate
  (60 = default, smooth; **30 = half load** recommended for integrated
  graphics; 0 = no limit). It does NOT change the game speed.
- **Per-GPU quality presets** (Video tab, "Quality preset"): `Auto`
  detects your graphics card (name + VRAM) and applies the recommended profile at every
  boot. Manual profiles: Low / Medium / High / Ultra. Installs
  with hand-made settings are kept intact (marked as "Manual").
- **Machines without AVX2**: the `dbz3.exe` launcher detects your CPU and uses the
  right variant (`dbz3_avx2\` for modern CPUs, `dbz3_legacy\` for the
  rest).
- **Reliable boot**: the launcher no longer stays black/Not responding when
  opening. The cause was the SDL controller init (which can block
  with capture software such as RTSS/OBS); it is now initialized in the background
  and the game boots instantly.
- **Reliable close (Alt+F4 / X button)**: closing the game no longer leaves it hung
  in "Not responding"; it exits instantly.
- **Executable detection**: if you supply the EU/PAL `default.xex`, the launcher
  detects it and boots the matching EU/PAL core (same with US/NA); if
  you put a core with the wrong executable, it warns you and blocks Play so you
  do not see an odd close. The data folder is also detected even if you only
  have `eu/` (no `us/`).
- **Launcher in your language (and the game too)**: the "Language" selector translates
  the WHOLE launcher (Spanish, English, Italian, German, French; the rest use
  English) **and sets the game's text** to the same language.
- **PLAY always visible**: the PLAY button is big and green, always on
  screen with no scrolling needed, with a summary of the configuration
  about to be launched (region, engine, scale, effect, language). The region
  selector is in the bottom bar.
- **Compact UI**: the whole interface fits in the window without scroll
  bars (Video and Controls tabs in columns; long help texts
  are shown on hover).
- **Visible presets**: the Video tab shows which quality profile is
  active and what values it resolves to (e.g. "Auto → High: 1x, MSAA ON...").

## Mods (WIP)

> 🚧 **Status: in development (WIP).** The mod system is experimental and may
> change. Use it with backups.

Mods are managed from the launcher's **Mods**, **Textures** and **Model Swap**
tabs. They **do not modify** the game files: they apply an overlay on
specific AFS entries, so each mod weighs only ~100 KB.

- **Model swap**, native B3→B3: replaces the whole character (geometry +
  textures) with another from the catalog (183 characters). Works in any
  direction, even if the new bin is larger than the original slot
  (virtual mid-insert).
- **Textures**: extracts a character's textures to editable PNGs; you
  edit them and rebuild the mod.
- **Music** (`og_music`): replaces the audio AFS per region.

## Release status (WIP)

Story mode and the alternate modes were verified in a full pass
**with no errors, crashes or known issues** using the default configuration
(D3D12 + 2x upscaling + 60 FPS). The mod system is the experimental part:
swaps and textures work, but since they are customizable, use them with
a backup of your AFS files.

## Known bugs

- **Universal runtime (SSSE3) vs classic (AVX2)**: the universal executable is
  ~5-10 % slower on modern CPUs than the AVX2 runtime. If you notice it on your
  machine, use the fallback release `v1.1.0-clasico`.
- **Experimental Vulkan**: the Vulkan backend works but 3D rendering is
  ~6.5x slower than D3D12. Use **D3D12** (default).
- **PS2/IW→B3 character port**: injection (PS2 geometry in the HD
  template) works and gives recognizable silhouettes; the port with exact PS2
  topology is still under research (it requires rebuilding the draw structure; see
  `docs/`).

## Version history

- **v1.1.3** (2026-09-09): **The ISO patch** — source selector
  always visible, detection and blocking of the DBZ1 xex, fully audited i18n
  (ES/EN/IT/DE/FR, 0 gaps), messages for non-technical users, polish
  `-Wall -Wextra` (0 warnings), stricter packager.
- **v1.1.2** (2026-09-09): EU crash fix (Dragon Universe / START, `sub_820F2398`
  registered), incomplete regions fix (`ResolveRegion()`), Vulkan backend fix
  (real `gpu_backend` cvar in the SDK), **disc mode (direct ISO)**, code
  polish (0 warnings).
- **v1.1.1** (2026-08-28): debugging (no data → clear message, boot
  markers), Linux groundwork (portable launcher), internal process (sync +
  release verification).
- **v1.1.0** (2026-08-28): **a single universal executable** — baseline runtime
  (SSSE3) for any x64 CPU, no variants or folders, no UPX.
- **v1.0.10** (2026-08-28):
  - **0xC000001D crash in Duel/Start fixed** (US codegen): the vtable
    dispatch `sub_820BB938` was misclassified as a 1-case jump table →
    UD2 when entering battle. It is now a real indirect call.
  - **PLAY button with the mouse fixed**: an unknown `default.xex` or one from the
    other region disabled the button (Enter worked around it). Now only an xex of
    a known but wrong variant is blocked; an unknown one warns but does
    not block, and Enter respects the same gate.
  - **GPU detection on Optimus laptops**: the adapter with the most
    dedicated VRAM is chosen (before, the first non-software one = integrated).
  - **Antivirus**: the package is NO longer compressed with UPX (UPX packers
    give virus false positives). Bigger download, no scares.
  - **Clearer bootstrap error message** (real log path
    `dbz3_legacy\logs` + cause of the 0xC000001D on old CPUs).
- **v1.0.9** (2026-08-26): mod center (install .zip + profiles),
  VERSIONINFO, hardened V-Sync fix.
- **v1.0.8** (2026-08-26): i18n EN/ES/IT/DE/FR, compact UI without scrollbars.
- **v1.0.7** (2026-08-26): dual US+EU core, EU demo battle fix (crash
  0xC000001D).
- **v1.0.6** (2026-08-26): fix for the close at the intro (0xC0000409 /
  0x82292A58), stronger diagnostics.
