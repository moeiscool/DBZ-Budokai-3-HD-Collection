# HANDOFF — Claude, 2026-10-06 — PS5 build + English documentation

Handback file for the maintainer and opencode, following the protocol in
`MEMORY.md` §0.3. Everything below is already committed on the branch
`claude/sweet-ptolemy-gasuxh`; nothing was pushed to `master`/`main`.

## 1. Summary

Two pieces of work, both requested by the maintainer.

1. **An experimental PS5 build (jailbroken consoles).** It is adapted from
   [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp). That
   project is another ReXGlue-recompiled game that already boots on a PS5.
   - Its PS5 platform layer was rebased onto our SDK overlay
     (`patches/rexglue-sdk/`).
   - A PS5 host program and the build scripts were added.
   - A one-command pipeline goes from the user's own ISO to a PS5 title folder:
     `bash ps5/make_ps5.sh --iso <your.iso> [--console <ip>]`.
   - Why: the maintainer asked to add the PS5 capability that mcla-recomp has.
2. **All repository documents translated to English.** This also adds notes
   about the PS5 build where they matter.
   - File names were kept, because scripts and links refer to them, e.g.
     `LEEME_*.txt` and `README_PRIMER_ARRANQUE.txt`.
   - Where an old document states something that was later refuted, a short
     "(Later: …)" note was added.
   - Personal absolute paths were generalized.

## 2. Files

### 2.1 PS5 build — commit `8a6afb7` (new files, GPL-3.0-or-later inside `ps5/`)

| Path | What it is |
|---|---|
| `ps5/README.md` | Internals: layers, how the patches are stacked, how to refresh the patch if the overlay changes, status. |
| `ps5/LICENSE` | GPL-3.0 text (the code comes from mcla-recomp). |
| `ps5/make_ps5.sh` | One-shot driver: SDK + overlay + PS5 patches → codegen → game build → title folder → optional upload. |
| `ps5/build_game.sh` | Compiles the codegen, the DBZ3 host sources and `main_ps5.cpp`; calls `title_build.sh`. |
| `ps5/title_build.sh` | Links the ELF and lays out the title folder (`PPSA99300`). |
| `ps5/build_ps5_vulkan_driver.sh` | Builds the PS5 Vulkan driver (PS5_Vulkan). |
| `ps5/main_ps5.cpp` | PS5 host: no ImGui launcher; reads `/data/dbz3/dbz3_user.toml`; data in `/data/dbz3/game`, mods in `/data/dbz3/mods`; DualSense via scePad, audio via sceAudioOut; single region (US or EU). |
| `ps5/ps5_pad_input.h`, `ps5/ps5_audio.h`, `ps5/title_log.h`, `ps5/log_fd_sink.h` | Input, audio and logging glue. |
| `ps5/title_support.c`, `ps5/title_stub_system_service.c` | Title runtime support stubs. |
| `ps5/stage_game.py`, `ps5/make_title_art.py`, `ps5/title_log_client.py` | Stage the game files from the ISO, generate title art, read the console log. |
| `ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch` | mcla-recomp's PS5 layer rebased onto `patches/rexglue-sdk/`. Two conflicts merged by hand (vblank clamp + resync; frame_cap + PS5 paint logging). Also `REX_EXECUTABLE_PATH` for `GetExecutablePath()` and a `sha256.cpp` endianness fix. |
| `ps5/patches/rexglue-ffmpeg-ps5-config.patch` | FFmpeg configuration for the PS5 target. |
| `docs/PS5.md` | User guide (requirements, one command, console layout, settings, mods, troubleshooting). |
| `.gitignore` | Ignores `ps5-game/` and the PS5 build outputs. |

The full content of each new file is in commit `8a6afb7`
(`git show 8a6afb7 -- <path>`).

### 2.2 Documentation — commits `edb4f15` … `3ed0034` (113 files modified, none created or deleted)

Every change is a translation of the existing content. Extra edits on top of the
translation:

- `README.md`
  - Now the English README.
  - Adds a "PS5 (jailbroken, experimental)" section, a status row, `ps5/` in the
    layout, and credits plus a GPL note.
- `README_EN.md`: now a pointer to `README.md`. It is kept because the Linux CI
  copies it.
- `CHANGELOG.md`: "Unreleased" entry for the PS5 build and the translation.
- `AGENTS.md`: new §14 "PS5 BUILD", plus PS5 notes in §2, §3, §6, §7, §8, §9
  and §13.
  - ⚠️ The protocol says not to rewrite `AGENTS.md`/`MEMORY.md`. The maintainer
    explicitly asked for *all* documents in English, so they were translated.
    Review the PS5 additions in §14.
- `MEMORY.md`: translated; §1.0 points to this handoff.
- `patches/README.md`: PS5 note plus a "2026-10-06 - PS5 build" section.
- `docs/01_estructura/HISTORICO_RELEASES.md`
  - §D, the verbatim Spanish snapshot of the v1.2.9 AGENTS.md (≈1,700 lines),
    is **not reproduced**. It duplicated §A–§C and the current `AGENTS.md`.
  - The section now tells readers how to get the Spanish original from git:
    `git show 1dbccb17a243713cf98cfca850cbc21c3fb843be:docs/01_estructura/HISTORICO_RELEASES.md`.
- `docs/01_estructura/HISTORICO_AGENTS.md`: full translation (same 90 headings
  as the original), with "(Later: …)" correction notes.
- `awo_tools/SESION_2026-08-17.md`: a verbatim duplicated block (the Pikkon
  evaluation, repeated in §2.8) was dropped, with a note.
- `docs/03_formatos/MAPA_ROSTER_HD.md`: a duplicated "## 8" heading renumbered
  to "## 10. SOURCES".

Exact list of documentation files touched (diff: `git diff 8a6afb7 3ed0034`):

- `AGENTS.md`
- `AWO_FORMAT.md`
- `CHANGELOG.md`
- `MEMORY.md`
- `MODDING_README.md`
- `README.md`
- `README_EN.md`
- `README_PRIMER_ARRANQUE.txt`
- `RELEASE_README.md`
- `awo_tools/CONSOLIDADO.md`
- `awo_tools/HALLAZGO_COMUNIDAD.md`
- `awo_tools/PLAN_AWO_DESDE_CERO.md`
- `awo_tools/RE_AWO_HD_CONVERSOR.md`
- `awo_tools/RE_PROGRESO.md`
- `awo_tools/SESION_2026-08-17.md`
- `awo_tools/SUBMESH_DATA_B3.md`
- `docs/01_estructura/ARBOL.md`
- `docs/01_estructura/ESTADO.md`
- `docs/01_estructura/HISTORICO_AGENTS.md`
- `docs/01_estructura/HISTORICO_RELEASES.md`
- `docs/02_mods/COMO_HACER_MODS.md`
- `docs/02_mods/MODEL_SWAP.md`
- `docs/02_mods/PACKS_DE_TEXTURAS.md`
- `docs/02_mods/SESION_MODS_LAUNCHER_2026-09-14.md`
- `docs/02_mods/STUDIO_CAMARAS.md`
- `docs/02_mods/TEXTURAS_MOD.md`
- `docs/03_formatos/ACM_FORMAT.md`
- `docs/03_formatos/AMO_AWO.md`
- `docs/03_formatos/AUDITORIA_DATA_CMN.md`
- `docs/03_formatos/BIN_LAYOUT.md`
- `docs/03_formatos/CAMARA_ACC.md`
- `docs/03_formatos/CAPSULAS_B3.md`
- `docs/03_formatos/FORMAS_Y_KI.md`
- `docs/03_formatos/MAPA_ROSTER_HD.md`
- `docs/03_formatos/SB_VS_B3_MOVESET.md`
- `docs/03_formatos/STAGES_FORMAT.md`
- `docs/03_formatos/TOON_Y_BRILLO_HD.md`
- `docs/04_herramientas/TOOLS.md`
- `docs/05_build/COMO_COMPILAR.md`
- `docs/06_limpieza/INTEGRACION_MODDING_HD.md`
- `docs/06_limpieza/INVENTARIO_FISICO_2026-09.md`
- `docs/06_limpieza/INVENTARIO_MODDING.md`
- `docs/06_limpieza/PLAN_LIMPIEZA.md`
- `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md`
- `docs/07_ports/ESTUDIO_ECOSISTEMA_MODS.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/01_moveset/informe.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/02_tecnicas/informe.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/03_modelo/informe.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/04_transformaciones/informe.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/05_studio/informe.md`
- `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/README.md`
- `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md`
- `docs/07_ports/INVESTIGACION_PS2_HD_2026-09-13.md`
- `docs/07_ports/MATRIZ_CANDIDATOS_PS2_HD.md`
- `docs/07_ports/PLAN_PS2_B3/01_WEB.md`
- `docs/07_ports/PLAN_PS2_B3/02_MODS_INVENTARIO.md`
- `docs/07_ports/PLAN_PS2_B3/03_DOCS.md`
- `docs/07_ports/PLAN_PS2_B3/04_FORMATO_RE.md`
- `docs/07_ports/PLAN_PS2_B3/PLAN.md`
- `docs/07_ports/SESION_BABIDI_VALIDACION_2026-09-08.md`
- `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`
- `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md`
- `docs/07_ports/SESION_FASE_C_CONSUMER_2026-09-10.md`
- `docs/07_ports/SESION_GPU_DRAW_2026-09-11.md`
- `docs/07_ports/SESION_INYECCION_2026-08-26.md`
- `docs/07_ports/SESION_PORT_RE_2026-08-26.md`
- `docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md`
- `docs/07_ports/SESION_TIEN_RIG_2026-09-08.md`
- `docs/07_ports/SESION_VIA_B_RENDER_2026-09-12.md`
- `docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md`
- `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md`
- `docs/09_mods_nativos.md`
- `docs/ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14.md`
- `docs/ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md`
- `docs/BRIEFING_GPT6_ASTRA.md`
- `docs/DICTAMEN_GPT6_ASTRA.md`
- `docs/EVALUACION_2026_09_PLAN_DEPURACION.md`
- `docs/HOJA_DE_RUTA.md`
- `docs/HOJA_DE_RUTA_2026_09.md`
- `docs/HOJA_DE_RUTA_ACELERADA.md`
- `docs/HOJA_DE_RUTA_COMUNIDAD.md`
- `docs/LINUX.md`
- `docs/MIGRACION_CLAUDE.md`
- `docs/MIGRACION_REXGLUE_010.md`
- `docs/PLAN_1.1.1.md`
- `docs/PLAN_1.4.2_DLSS_FSR3.md`
- `docs/PLAN_LINUX.md`
- `docs/README.md`
- `docs/RE_MASTER_2026_09.md`
- `docs/SESION_AUTODETECCION_XEX_2026-09-17.md`
- `docs/SESION_DIAGNOSTICO_2026-09-26.md`
- `docs/SESION_FIX_VOLCADO_2026-09-21.md`
- `docs/SESION_IO_FOCO_2026-09-19.md`
- `docs/SESION_LAUNCHER_AUDIT_2026-09-19.md`
- `docs/SESION_PACING_WINDOWS_2026-09-20.md`
- `docs/SESION_PERF_TEXTURAS_2026-09-24.md`
- `docs/SESION_TEXTURAS_PACK_2026-09-20.md`
- `docs/SESION_TOML_Y_UX_2026-09-20.md`
- `docs/SESION_VOLCADO_FORMATOS_2026-09-23.md`
- `docs/VIABILIDAD_MODELOS_EXTERNOS.md`
- `docs/VIABILIDAD_UPSCALING_TEMPORAL_2026-09-29.md`
- `docs/consejos_desde_b1_ps2_port.md`
- `mod center hd/GUIA_SWAPS_Y_PORTS.md`
- `mod center hd/README.md`
- `mod center hd/RETOPOLOGIA_3D.md`
- `mod center hd/fonts/LEEME_FUENTE.txt`
- `mod center hd/stages_b3.txt`
- `mods/README.md`
- `patches/README.md`
- `portforge/archive/README.md`
- `tools/modpacks/LEEME_KIT.txt`
- `tools/modpacks/LEEME_PERSONAJES.txt`
- `tools/modpacks/LEEME_PS2_GAMES.txt`

## 3. Commands run and results

Run in a Linux cloud container. There was no Windows toolchain, no game
executable and no console.

| Command / check | Result |
|---|---|
| Apply `patches/rexglue-sdk/` onto a clean ReXGlue v0.10.0, then `ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch` (`git apply --check` then `git apply`) | Applies cleanly. |
| Configure + build `rexruntime` and `rexgpu-xenos` for the PS5 target (pinned payload SDK, clang 21) | Build OK. |
| Compile the DBZ3 host sources + `ps5/main_ps5.cpp` for PS5, US and EU variants | Compile OK. No unresolved symbols other than the codegen's (the codegen needs the user's executable, which is not available here). |
| Documentation sweep: grep of all tracked `*.md`/`*.txt` for common Spanish words | No Spanish documents left. |
| `HISTORICO_AGENTS.md` heading count, original vs translation | 90 / 90. |
| `git push -u origin claude/sweet-ptolemy-gasuxh` | Returned **403** earlier in the session (no GitHub access for this repository from the session). See §4. |

## 4. Not done / risks / assumptions

- **The PS5 build has never run on a console.** The game itself was never
  built, because the codegen needs the user's executable. Expect the first boot
  to need iteration:
  - Missing indirect-call targets go into `dbz3_config*.toml`, as on PC.
  - `/data/dbz3/dbz3-play.log` holds the warnings and the crash report.
- **Linking against `patches/rexglue-sdk/`**: if the overlay changes, the PS5
  patch may stop applying. The refresh procedure is in `ps5/README.md`.
- **Features missing on PS5**: D3D12-only features are absent, because the
  console has Vulkan only. That covers the HD texture upscale, texture dump,
  DLSS/FSR 3 and FidelityFX. Texture packs do have a Vulkan path.
- **Dual region**: the PS5 build is single-region, made from the executable the
  user supplies.
- **License**: `ps5/` is GPL-3.0-or-later; the rest of the repository stays
  MIT. Distributing a PS5 build means distributing GPL code. The built title
  also contains code recompiled from the user's game, so it must never be
  shared.
- **Translation scope**: Markdown and text documents only. Code comments, TOML
  comments, launcher UI strings (`src/launcher/i18n.cpp`) and historical git
  commit messages remain in Spanish.
- **Push**: if the 403 persists, the commits exist only on the session's local
  branch. Reconnect GitHub at https://claude.ai/connect-github and push the
  branch again.

## 5. Recommended next step

1. Push `claude/sweet-ptolemy-gasuxh` once access works, then open a PR into
   `master` if the maintainer wants it.
2. On a jailbroken PS5:
   - Run `bash ps5/make_ps5.sh --iso <your.iso> --console <ip>` from an Arch
     Linux host.
   - Boot the title and send back `/data/dbz3/dbz3-play.log`.
3. Opencode side (MEMORY.md §0.4):
   - Merge §1.0 of `MEMORY.md` and §14 of `AGENTS.md` into the next compaction.
   - Run `tools/sync_github.ps1` so `publish_check.ps1` vets the new `ps5/`
     folder.
