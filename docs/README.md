# DBZ Budokai 3 HD Collection — Project documentation

> An accessible guide for agents and humans. Consolidates the project's state,
> folder structure, how to make mods, formats, tools and builds.
> Updated: 2026-10-06 (all documentation translated to English; **PS5 port**
> added). Before that: 2026-09-26 (after **v1.2.9**, with the compaction of
> `AGENTS.md` to ≤60 KB: the verbatim detail moved to
> `01_estructura/HISTORICO_RELEASES.md`).
>
> File names are kept as they were (many are Spanish words, e.g.
> `COMO_HACER_MODS` = "how to make mods", `FORMATOS` = "formats",
> `HERRAMIENTAS` = "tools", `LIMPIEZA` = "cleanup", `SESION` = "session",
> `HOJA_DE_RUTA` = "roadmap") so that existing links keep working.

---

## INDEX

| Folder | Contents |
|---|---|
| [PS5](PS5.md) | **PS5 (jailbroken) build**: one command from your ISO to an installed homebrew title; adapted from holdmysocks/mcla-recomp (internals in [`../ps5/README.md`](../ps5/README.md)) |
| [HOJA_DE_RUTA_ACELERADA](HOJA_DE_RUTA_ACELERADA.md) | **Active roadmap**: accelerated execution (swap-first, reader-first, corpus, roster via memory) with sprints S0-S4 and automation |
| [HOJA_DE_RUTA_2026_09](HOJA_DE_RUTA_2026_09.md) | Post-1.1.1 maturity (superseded by the accelerated one) |
| [EVALUACION_2026_09_PLAN_DEPURACION](EVALUACION_2026_09_PLAN_DEPURACION.md) | **Project evaluation + superb debugging plan** (EU crash #4, issues, D0-D4) |
| [RE_MASTER_2026_09](RE_MASTER_2026_09.md) | **Governing plan for end-to-end RE**: lab, layers, phases and validation |
| [DICTAMEN_GPT6_ASTRA](DICTAMEN_GPT6_ASTRA.md) | **External opinion (GPT-6 Astra)**: plan 0-7 for native slots + PS2→B3 port (current guide) |
| [BRIEFING_GPT6_ASTRA](BRIEFING_GPT6_ASTRA.md) | Technical briefing that led to the opinion |
| [HOJA_DE_RUTA](HOJA_DE_RUTA.md) | Original modding plan (historical, superseded) |
| [HOJA_DE_RUTA_COMUNIDAD](HOJA_DE_RUTA_COMUNIDAD.md) | Community feedback P0-P5 (historical, all completed) |
| [SESION_AUTODETECCION_XEX_2026-09-17](SESION_AUTODETECCION_XEX_2026-09-17.md) | **v1.2.2 EX**: executable auto-detection (retail disc dump, original ISO, `DBZ3\`), xex states and the TOML fix |
| [ANALISIS_RENDIMIENTO_LOGS_2026-09-18](ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md) | **Performance**: analysis of the logs of the "runs VERY slowly" report (RTX 5090) + `dbz3_perf_logging` instrumentation + gating of the AFS log |
| [SESION_LAUNCHER_AUDIT_2026-09-19](SESION_LAUNCHER_AUDIT_2026-09-19.md) | **v1.2.4/1.2.4 EX**: launcher audit (dead controls, real `audio_gain`, update check, FXAA/dither, GPU levers, portable data) |
| [SESION_IO_FOCO_2026-09-19](SESION_IO_FOCO_2026-09-19.md) | **v1.2.5**: read path (`dbz3_io_logging`, read-ahead) + QoL on losing focus (`fg=`, mute/dim) |
| [SESION_TOML_Y_UX_2026-09-20](SESION_TOML_Y_UX_2026-09-20.md) | **v1.2.6**: TOML self-repair + UX against misuse of the internal scale |
| [SESION_PACING_WINDOWS_2026-09-20](SESION_PACING_WINDOWS_2026-09-20.md) | **Windows pacing**: why Linux's Vulkan fix does not apply to D3D12 (no code changes) |
| [SESION_TEXTURAS_PACK_2026-09-20](SESION_TEXTURAS_PACK_2026-09-20.md) | **PCSX2-style texture packs (Phase 1, dev)**: DDS dump + importer to PNG per character |
| [SESION_FIX_VOLCADO_2026-09-21](SESION_FIX_VOLCADO_2026-09-21.md) | **v1.2.8**: texture dump fix (issue #11) - shared cvar registry, `REXCVAR_QUERY` |
| [SESION_VOLCADO_FORMATOS_2026-09-23](SESION_VOLCADO_FORMATOS_2026-09-23.md) | **v1.2.8.1**: dump of the uncompressed HUD/UI formats + RGBA8 packs + per-identity version cap (issue #11) |
| [SESION_PERF_TEXTURAS_2026-09-24](SESION_PERF_TEXTURAS_2026-09-24.md) | **v1.2.8.2**: the texture upscale stops sinking the FPS (level 0 only on dynamic reloads) + `cfg=`/`upx_dyn=`/`texload=` in the `perf` line |
| [SESION_DIAGNOSTICO_2026-09-26](SESION_DIAGNOSTICO_2026-09-26.md) | **v1.2.9**: self-explanatory diagnostics (sustained-fps, slow-disk and mixed-installation warnings; `vram=`/`lim=` in `perf`; VRAM guard; `entorno` line with versions) |
| [LINUX](LINUX.md) | Native Linux build with Vulkan, SDL3 and CI using private codegen |
| [ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14](ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14.md) | Upscaling/performance: FSR1/CAS yes; FSR3/DLSS not viable in the short term (later shipped as a beta in 1.4.2) |
| [VIABILIDAD_UPSCALING_TEMPORAL_2026-09-29](VIABILIDAD_UPSCALING_TEMPORAL_2026-09-29.md) | **DLSS/DLAA/FSR3/Frame Gen**: real viability after analysing `reblue` and `LostOdysseyRecomp`; what we adopted (DRED, gamecontrollerdb) and what not |
| [PLAN_1.4.2_DLSS_FSR3](PLAN_1.4.2_DLSS_FSR3.md) | The 1.4.2 plan for real DLSS and FSR 3 (motion replay) |
| [07_ports/TEXTURAS_HD_RUNTIME_UPSCALE](07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md) | **Runtime HD textures (PARKED)**: outer D3D12 layer, evidence of why overriding the bin does not work and how to resume it |
| [07_ports/UNIVERSAL_MODDER_2026-09-30](07_ports/UNIVERSAL_MODDER_2026-09-30.md) | **universal-modder (evaluation)**: what it is, what is reused (RE method with Ghidra/IDA/RenderDoc via MCP + oracles) and its application to Route B's bind/skin blocker |
| [01_estructura](01_estructura/ARBOL.md) | The project's complete tree, what each folder is |
| [01_estructura/ESTADO.md](01_estructura/ESTADO.md) | Current state, what works, what fails |
| [01_estructura/HISTORICO_AGENTS.md](01_estructura/HISTORICO_AGENTS.md) | Verbatim session history up to 2026-09-02 (on demand only) |
| [01_estructura/HISTORICO_RELEASES.md](01_estructura/HISTORICO_RELEASES.md) | Verbatim detail extracted from `AGENTS.md` in the 2026-09-26 compaction: §A releases 1.1.3→1.2.9, §B PS2→B3 port research, §C launcher (on demand only) |
| [02_mods](02_mods/COMO_HACER_MODS.md) | Mod pipeline (per-entry override); §7 mods on PS5 |
| [02_mods/MODEL_SWAP.md](02_mods/MODEL_SWAP.md) | Model swap research (what we know/what fails) |
| [02_mods/TEXTURAS_MOD.md](02_mods/TEXTURAS_MOD.md) | **The launcher's Textures tab** (extract/edit/rebuild) |
| [02_mods/PACKS_DE_TEXTURAS.md](02_mods/PACKS_DE_TEXTURAS.md) | **Texture packs (PCSX2 style)**: dev dump, runtime loader and a guide for authors |
| [02_mods/SESION_MODS_LAUNCHER_2026-09-14.md](02_mods/SESION_MODS_LAUNCHER_2026-09-14.md) | Mod sweep + closing/polish of the **HD↔HD Model Swap** + ISO notice + refactor of the Mod centre |
| [02_mods/STUDIO_CAMARAS.md](02_mods/STUDIO_CAMARAS.md) | **Camera Studio**: edit technique cameras, templates, round trip to Blender, save as a mod |
| [03_formatos](03_formatos/AMO_AWO.md) | PS2 (#AMO0) vs HD (#AWO) model format |
| [03_formatos/BIN_LAYOUT.md](03_formatos/BIN_LAYOUT.md) | HD bin layout (headers, buffers, vertex) |
| [03_formatos/AWO_FORMAT.md](03_formatos/AWO_FORMAT.md) | HD #AWO format field by field |
| [03_formatos/ACM_FORMAT.md](03_formatos/ACM_FORMAT.md) | HD moveset format (#AMB→#CSK→#ACM) + ability editing |
| [03_formatos/STAGES_FORMAT.md](03_formatos/STAGES_FORMAT.md) | Stage bins (#AMB→#ZDD/#CAD/#CAS/#SPX) + PS2 container (IW ports) |
| [03_formatos/CAPSULAS_B3.md](03_formatos/CAPSULAS_B3.md) | Capsules: #SKC catalogue, ability sheets, extra places 44-63 and IW ports (hyper mode) |
| [03_formatos/CAMARA_ACC.md](03_formatos/CAMARA_ACC.md) | #ACC/#AMC cameras: 4 tracks (position, aim point, roll, fov) |
| [03_formatos/SB_VS_B3_MOVESET.md](03_formatos/SB_VS_B3_MOVESET.md) | Shin Budokai movesets compared with B3 (AP 20→16, HR 160→128, codes, damage ×0.85) |
| [03_formatos/FORMAS_Y_KI.md](03_formatos/FORMAS_Y_KI.md) | Transformations: required bars, capsule chain, base ki level |
| [03_formatos/TOON_Y_BRILLO_HD.md](03_formatos/TOON_Y_BRILLO_HD.md) | Toon shader (base − ramp, alpha = unshaded) and the HD rim light (c39.x) |
| [04_herramientas](04_herramientas/TOOLS.md) | Inventory of tools and what they do |
| [05_build](05_build/COMO_COMPILAR.md) | How to build the game and the SDK (and where the PS5 build is) |
| [06_limpieza](06_limpieza/PLAN_LIMPIEZA.md) | Cleanup/reorganisation plan |
| [06_limpieza/INVENTARIO_FISICO_2026-09](06_limpieza/INVENTARIO_FISICO_2026-09.md) | Physical inventory and artefacts |
| [06_limpieza/INTEGRACION_MODDING_HD](06_limpieza/INTEGRACION_MODDING_HD.md) | Classification of tools and resources for HD |
| [07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06](07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/README.md) | **Future Gohan at 100 %**: exploration of moveset, techniques, model, forms and Studio |
| [07_ports](07_ports/ESTRUCTURA_DIBUJO_HD.md) | **HD draw structure mapped (A/B descriptors, mesh-refs, arms)** |

---

## 30-SECOND SUMMARY

- **What it is**: a PC recompilation of DBZ Budokai 3 HD Collection (Xbox 360)
  with the ReXGlue SDK, plus an experimental build for **jailbroken PS5**
  consoles (`docs/PS5.md`).
- **Play**: `out\build\win-amd64-release\dbz3.exe`
- **Config**: `out\build\win-amd64-release\dbz3_user.toml` (on PS5:
  `/data/dbz3/dbz3_user.toml`)
- **Mods**: folder `mods\<mod>\` next to the exe (on PS5: `/data/dbz3/mods/`).
  Only those WITHOUT `.disabled`.
- **State**: releases up to **v1.4.2.2** (see `CHANGELOG.md`). v1.2.9 was the
  **self-explanatory diagnostics** release: ALWAYS-ON warnings of sustained fps,
  slow disk and **mixed installation** (the DLLs publish their build stamp in
  `rex/dbz3_build.h`, because they have no VERSIONINFO), `vram=`/`lim=` in the
  `perf` line and a `dbz3: entorno os=... ram=... <versions>` line at
  startup; VRAM guard (no new upscales granted with the local heap at 92 %)
  and `tools/copy_sdk_dlls.ps1`. On top of v1.2.8.2 (the texture upscale stops
  sinking fps: level 0 only on dynamic reloads), v1.2.8.1 (dump of the HUD/UI
  formats + RGBA8 packs, issue #11), v1.2.8 (dump fix: the launcher's cvar did
  not reach the plugin), v1.2.7 (PCSX2-style texture packs, D3D12 and Vulkan),
  v1.2.6 (polished HD texture upscale, clean HUD, scale UX and self-repair of
  `dbz3_user.toml`), v1.2.5 (focus/disk), v1.2.4 EX, v1.2.3 and v1.2.2 EX
  (executable auto-detection + retail ISO mode). The game works (D3D12, 60
  fps, US+EU). Native HD↔HD swap and textures work (Route A approximate). Full
  PS2→HD port **parked** (§3.4.10). The high cost is **supersampling**
  (internal scale), not the HD textures.

---

## KEY POINTS OF THE PROJECT

1. **Runtime**: `rexglue-sdk-0.10\` (source) → installed into `rexglue\` → the
   exe uses `rexruntime.dll`. The PS5 build links the same runtime statically
   (with `ps5/patches/` on top).
2. **Format**: the character bin is `#AWO` (big-endian 360), equivalent to the
   PS2 `#AMO0` (little-endian).
3. **Mods**: the runtime has a hook (`AfsFindModOverride`) that serves files
   per AFS entry without repacking.
4. **Compression**: AFS bins are LZX-compressed with `/N:2048` (NOT `/N:32`).
5. **Slot size**: each AFS entry has a fixed size; the mod's bin must fit
   (padded to the slot) or use the virtual mid-insert.
6. **Operational context**: `AGENTS.md` is the compacted operational
   reference; the historical detail is in `01_estructura/HISTORICO_AGENTS.md`
   (up to 2026-09-02) and `01_estructura/HISTORICO_RELEASES.md` (releases,
   port and launcher).

---

## MAINTAINING THE DOCUMENTATION

**Golden rule**: `AGENTS.md` (what is loaded in every session) is kept
**≤ 60 KB** and only with what is OPERATIONAL (state, offsets, constraints,
commands). All historical or blow-by-blow narrative moves to the historical
files, it is not deleted.

- **Historical files** (not loaded by default):
  `01_estructura/HISTORICO_AGENTS.md` (up to 2026-09-02) and
  `01_estructura/HISTORICO_RELEASES.md` (§A releases, §B port, §C launcher,
  §D verbatim snapshot of AGENTS before the 2026-09-26 compaction).
- **Compaction cycle**: each release that grows `AGENTS.md` beyond ~60 KB →
  move that release's detail to `HISTORICO_RELEASES.md` §A and leave a row in
  table §3.0 + the invariants in §3.0b.
- **Sessions**: each relevant release/session has its `SESION_*_2026-09-*.md`;
  link it from `AGENTS.md` §3.0 ("Session doc" column) and from this index.
- **Check after compacting**: (1) `AGENTS.md` ≤ 60 KB; (2) grep for the
  operational tokens (hashes, offsets, cvars, commands) present; (3) sync with
  `tools/sync_github.ps1` and commit in `github/`.
- **Language**: the documentation is in English (since 2026-10-06).
