# Tools — inventory

> Updated: 2026-10-06 (§0 camera Studio and Shin Budokai / Heroes port; §7 PS5
> build). Inventory of the available tools and what they do.

---

## 0. MOD KIT: NEW CHARACTERS AND STUDIO (2026-10-06)

All of this is used without a console from the Mod Kit
(`mod center hd/modkit_gui.py`) and the launcher; the console is for modders.
Every tool with logic has its own self-test.

### Camera Studio (`mod center hd/studio/`)
| Tool | Function | Check |
|---|---|---|
| `studio_gui.py` | The Studio window: character + technique, script timeline, 2D views, templates (orbit, dolly, shake, roll), toon preview, GIF, Blender, save as mod | `--selftest` (no window), `--captura out.png` |
| `studio_core.py` | Core: `#ACC/#AMC` (camera clips), `#SPX` script (clip ↔ technique, waits), `#CSK` hit marks, validation, templates, glTF round trip, saving with LZX + reservation + backup | `selftest` (633 HD + 633 PS2 clips byte for byte), `info ID`, `exportar-glb`, `importar-glb` |
| `blender_puente.py` | Script that Blender runs (no add-on): `abrir` (imports the shot and saves a .blend) and `exportar` (in the background, `.blend` → `.glb`) | round trip with `blender -b` |

Guide: `docs/02_mods/STUDIO_CAMARAS.md`. Format: `docs/03_formatos/CAMARA_ACC.md`.

### Shin Budokai (PSP) and Super Dragon Ball Heroes (PC) characters
| Tool | Function | Check |
|---|---|---|
| `mod center hd/importar.py` | The importer of the launcher and the Mod Kit. Sources `b1`, `b2`, `b3`, `iw`, **`sb1`, `sb2`, `sdbh`** | `fuentes`, `lista FUENTE`, `importar …` |
| `awo_tools/sbport.py` | SB1/SB2 moveset → B3 (AP 20→16 B, HR 160→128 B, damage × 0.85, codes, global store, grafts from the donor) | `--prueba`, `--oraculo` |
| `awo_tools/sb_tablas.py` | Measured SB → B3 tables (global store, AP7 effects) | (module) |
| `awo_tools/sb_amm.py` | SB animation decompressor | (module) |
| `awo_tools/sb_tecnicas.py` | SB techniques: hybrid BSP, official names (`bsp`, `aplicar`, `nombres`) | `prueba` |
| `awo_tools/psp_amo.py` | PSP model → HD bin | byte for byte with the costumes of the Future Gohan port |
| `awo_tools/sdbh_model.py` | Heroes model (EMD/ESK/EMB) → HD bin with mouth, 7 faces and native ramps | `--selftest` |
| `mod center hd/roster_build.py` | Mounts the new characters; keys `formas`, `ki_base`, `modelo_forma`, `fisica`, `transformacion`; `capsulas --ki` | `construir --mods <copy>` |

Formats: `docs/03_formatos/SB_VS_B3_MOVESET.md`, `FORMAS_Y_KI.md`, `TOON_Y_BRILLO_HD.md`.
Complete recipe: `docs/02_mods/COMO_HACER_MODS.md` §5.

---

## 1. OUR TOOLS (awo_tools/ + mod center hd/)

### awo_tools/ — RE and conversion scripts
| Tool | Function | State |
|---|---|---|
| `analyze_bin_hd.py` | Historical parser based on the PS3 template | ⚠️ Obsolete; reference only |
| `awg_to_obj_b3.py` | OBJ exporter for complete B3 bins | ✅ Recommended |
| `awg0_export.py` | AWG0 exporter with A/C auto-detection | ✅ Recommended |
| `awg_cara_export.py` | Face AWG exporter | ✅ Recommended |
| `parse_ps2_mesh.py` | PS2 mesh parser (verts+IB) | ✅ |
| `pose_matrix.py` | World matrices of PS2 bones | ✅ |
| `rig_mapeo.py` | JNB→KLL remapping by labels | ✅ |
| `build_awo_desde_cero.py` | Parse Janemba.amb → AMGs | ✅ (extraction) |
| `build_janemba_final.py` | Inject Janemba's geometry into Krillin | 🔸 under research |
| `swap_cuerpo_hd.py` | Inject Goten's body into Krillin | 🔸 under research |
| `build_janemba2.py`, `build_afs.py`, `mezclar_ps2_hd.py` | Earlier experiments | 🔸 archivable |

### Environment maintenance (development only, not distributed)
- `tools/cleanup.ps1` — manual cleanup of the project's weight: `-DryRun`
  (preview), `-Yes` (L0 without asking), `-Full -Yes` (+ L1 archived). It
  never touches docs/src/assets/mods/SDK/ps2_games. Reports the top-12
  consumers. See the script's header.
- `awo_tools/corpus_scan.py` — since 2026-09-09 it **cleans its temporaries**
  after each decompression (before, it left ~16 GB in
  `out/analysis/corpus/.work`). Only `--keep-bin` keeps copies in `.work/bins/`.
- `tools/make_test_iso.py <out.iso> <folder> [--quiet]` — generates a **test
  XDVDFS** (what the runtime reads as "GDFX") packing a folder with the retail
  layout: it is used to validate **disc (ISO) mode** without a real ISO (v1.2.2
  EX, see `docs/SESION_AUTODETECCION_XEX_2026-09-17.md` §4.bis). It only packs
  what you give it: it contains no game data. (Also used to test
  `ps5/stage_game.py`'s ISO reader.)
- `tools/perf_report.ps1 [-Count N]` (+ double-click `perf_report.cmd`) -
  **performance report** of the last N logs: applied config, 5 s windows, fps
  min/med/max, worst `max_frame_ms`, windows <58 fps, errors and verdict.
  Saves the text in `%TEMP%\opencode\perf_report.txt`.
- `tools/perf_test_config.ps1 -Scale 1..4 -Msaa on|off [-Show]` - sets the
  internal scale + native MSAA in `dbz3_user.toml` for A/B performance tests
  (leaves `dbz3_texture_upscale=1` and `dbz3_perf_logging=true`).
- `tools/hidden_run.ps1 -Label <txt> -Seconds <n> [-HideMode 0|1] -Overrides
  "cvar=value;cvar=value"` — **offscreen test harness** (2026-09-18): launches
  `dbz3.exe` with the window moved off-screen, applies overrides to
  `dbz3_user.toml` (automatic backup/restore), kills the process and
  summarises the log (`AFS OVERRIDE`, `perf fps=`, `upscale pipeline ready`
  lines, errors). Use `dbz3_skip_launcher=true` to boot straight into the
  game. Text values in the toml go **in quotes** (`"manual"`, `"fsr"`);
  without quotes the parser discards the whole file. See
  `docs/ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md` §6.

### mod center hd/ — adapted HD tools
| Tool | Function |
|---|---|
| `fbx_ascii.py` | ASCII FBX parser (SDBH→FBX→data) |
| `emd_to_awo_hd.py` | ESK parsing + SDBH→KLL mapping |
| `build_awo_from_json.py` | JSON→HD AWO |
| `awg_to_obj.py` | Export HD AWG→OBJ |
| `obj_to_awg.py` | Import OBJ→HD AWG |
| `json_to_obj.py` | SDBH JSON→OBJ |
| `RETOPOLOGIA_3D.md` | Document of the retopology pipeline |

---

## 2. COMMUNITY TOOLS (mod center/) — 36 programs

### Model conversion
| Tool | Function | Format |
|---|---|---|
| `OBJ to AMG v0.92` | OBJ→PS2 mesh parts (with templates) | PS2 |
| `EMD to AMG v0.90` | Xenoverse EMD→PS2 AMG | PS2 |
| `B3-IW AMO Converter + Shadows` | B3/IW→B1 (exe) | PS2 |
| `Bin to OBJ (English) V3` | Bins→OBJ | PS2 |
| `AMG to OBJ V2` | AMG→OBJ | PS2 |
| `Model Merger Tool` | Merge 2 models (AMO_LGBT) | PS2 |

### Rig/model editing
| Tool | Function |
|---|---|
| `Model Rig Toolset V0.6` | Rig extractor/remover (documents the format) |
| `Model-Rig Extractor Tool V1.0` | Same, standalone |
| `Bone Addition Tool v1.02` | Add bones to the AMO |
| `Model Part Editor` | Convert parts B3↔B1 |
| `Axis Line Tool` | Generate the AMO's axis lines |
| `BoneAxis Display` | View bone positions |

### AMB / AFS
| Tool | Function |
|---|---|
| `AFS Toolset v0.90` | Pack/unpack AFS |
| `AMB Tool` / `AMBStudio` | AMB editor |
| `Budokai AMB Packer-Unpacker` | AMB packer/unpacker |
| `AMB_AMT Manipulator 1.5` | Manipulate AMB/AMT |
| `B3_IW Model Converter` | Pack AMB (not a converter) |

### Compression (CRITICAL)
| Tool | Function |
|---|---|
| `Xbox 360 Compression tool` | **`xbcompress.exe /N:2048`** and `xbdecompress.exe` |

> ⚠️ ALWAYS USE `/N:2048` (the game uses that block size). `/N:32` produces
> bins that exceed the slot → crash.

### Others
| Tool | Function |
|---|---|
| `A3T Analyzer` | Analyse A3T/AZT textures |
| `CRI Middleware ADX Tools` | ADX audio |
| `PSound` | Audio editor |
| `SLXS Editor v0.50` | Add characters (SLXS) |
| `Budokai3_SLUS_Editor` | Edit SLUS (select) |
| `Set Unlimited Fusion` | Unlimited fusions |
| `Transformation Input Stuff` | Transformations |
| `Zero Devs' Tool` | The community's universal tool (BT3p→Budokai) |

---

## 3. DISCORD TOOLS (modding resources discord/tools/)

| Tool | Function |
|---|---|
| `Budokai Modding Tool V1.5` | AMO_LGBT, AMG_C, AXIS_E, SLXS... |
| `AMO Model Separator v1.01` | Separate the AMO's parts |
| `Model Part Addition Tool` | Add parts |
| `AMG to OBJ V2` | Export OBJ |

---

## 4. SDK TOOLS (rexglue-sdk-0.10/)

- `rexruntime.dll` — runtime (mod hook, filesystem, logging)
- `rexgpu-xenos.dll` — GPU backend
- Tracy — profiling (build win-amd64-tracy)

---

## 5. RECOMMENDED FLOW TO STUDY A MODEL

```powershell
# 1. Decompress the bin from the AFS
xbdecompress.exe entry.lzx entry.bin

# 2. Export/check the structure with the current B3 tools
python awo_tools/awg_to_obj_b3.py entry.bin output.obj

# 3. If it is PS2, extract the mesh
python awo_tools/parse_ps2_mesh.py entry.amb 0 output
```

---

## 6. TEST HARNESS FOR THE RUNNING GAME (tools/, 2026-09-19)

| Tool | Function |
|---|---|
| `tools/long_run.ps1` | Starts/stops/queries decoupled **long** tests; mutes the game (`audio_mute=true`), applies overrides to `dbz3_user.toml` and restores it. State in `%TEMP%\opencode\long_run_state.json`. |
| `tools/press_key.ps1` | Injects keys via `PostMessage` (`-TargetPid`; map W/A/S/D/Backspace/Tab/Space/Return). |
| `tools/grab_window.ps1` | PNG capture of the window (`PrintWindow` PW_RENDERFULLCONTENT). Needs the window **on-screen** (off-screen the presentation freezes and the captures come out identical). |
| `tools/click_window.ps1` | Click by the window's **client** coordinates (ImGui launcher). |
| `tools/hidden_run.ps1` | Like long_run but moving the window off-screen (only to measure the guest's swap rate, not for captures). |

**Recipe to reach the 3D fight**: boot with `dbz3_skip_launcher=true` →
opening (~90-100 s) → press `Return` (Start) → title/menu → idle ~2-2.5 min →
the 3D attract demo battle kicks in.

---

## 7. PS5 BUILD (ps5/, 2026-10-06)

| Tool | Function |
|---|---|
| `ps5/make_ps5.sh` | One command (Arch Linux, root): driver + toolchain, patched SDK, recompiler, staging + codegen, PS5 runtime, title art, game build, FTP upload. Resumable. |
| `ps5/stage_game.py` | Finds the Budokai 3 xex by checksum (US/EU) in an ISO or folder; stages `default.xex` + `us/` `eu/` and the recompiler input. |
| `ps5/build_game.sh` | Compiles the codegen + DBZ3 host sources + `main_ps5.cpp` with the PS5 toolchain and links the title. |
| `ps5/title_log_client.py` | PC side of a test build's log connection. |
| `ps5/make_title_art.py` | Tile/background from the disc's `nxeart`. |

Guide: `docs/PS5.md`; internals: `ps5/README.md`.
