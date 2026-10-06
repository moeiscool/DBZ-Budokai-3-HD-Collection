# DBZ Budokai 3 HD Collection — Project context (operational)

> Context document for agents/AI. **Compacted 2026-09-26** (117 KB → ~60 KB)
> when **v1.2.9** was published; **updated 2026-09-30** for **v1.3.0**,
> **2026-10-03** (Path B skinning RE + handoff to Claude) and **2026-10-06**
> (experimental **PS5 build**, §14; documentation translated to English). The
> detailed verbatim narrative lives in
> `docs/01_estructura/HISTORICO_AGENTS.md` (up to 2026-09-02) and
> `docs/01_estructura/HISTORICO_RELEASES.md` (releases 1.1.3→1.2.9, PS2→B3 port
> research and launcher detail). This document is the OPERATIONAL reference:
> current state, engineering constraints and commands. The **live state and the
> protocol with Claude** are in `MEMORY.md` (root) + `docs/MIGRACION_CLAUDE.md`.

---

## 1. WHAT THIS IS

A PC port, recompiled, of **DBZ Budokai 3 HD Collection (Xbox 360)** using the
**ReXGlue SDK** (derived from Xenia). It includes a custom launcher
(`src/launcher/`), region/mod logic and runtime. An **experimental PS5 build**
for jailbroken consoles is made from the user's own copy with
`ps5/make_ps5.sh` (§14, `docs/PS5.md`).

- **dbz3** (this project): Budokai 3 HD Collection
- **dbz1** (sister project): DBZ Budokai HD Collection (separate repository)

## 2. KEY LOCATIONS

| Path | Content |
|------|-----------|
| `src/` | Launcher and game code (main.cpp, launcher/, ingame/) |
| `rexglue-sdk-0.10/` | **SDK source 0.10 (active)** — builds in `out/` |
| `rexglue/` | **Installed** SDK 0.10 (used by the game build); the 0.9 backup was removed (cleanup 2026-09-09) |
| `out/build/win-amd64-release/` | **Game build** (dbz3.exe, DLLs, mods/) |
| `out/build/win-amd64-dual/` | Dual build (US+EU) — **the release exe comes from here** |
| `eu/`, `us/` | Region assets (the game's AFS) |
| `ps2_games/` | B3 GH and IW AFS (PS2 references; B1/B2/B2V/Shin Budokai removed 2026-09-14) |
| `mod center/` | PS2 modding tools (36 programs) |
| `mod center hd/` | Own HD tools (swap_b3.py, texture_b3.py, texture_pack.py, ports/) |
| `modding resources/`, `modding resources discord/` | Community docs + resources (cleanup pending a decision) |
| `generated/` | Recompiled code of the US guest (`dbz3_recomp.*.cpp`) |
| `generated_eu/` | Recompiled code of the EU guest (`dbz3_eu_recomp.*.cpp`) |
| `awo_tools/` | Format RE tools (parse/export/port) |
| `ps5/` | **PS5 build** (scripts, host `main_ps5.cpp`, SDK patches; GPL-3.0-or-later) — §14 |
| `docs/` | **Documentation (read `docs/README.md` FIRST)** |
| `github/` | Versionable copy for GitHub (manual sync, §9.3) |

## 2.1 DOCUMENTATION (docs/ — READ FIRST)

**Full index: `docs/README.md`.** Shortcuts by topic:

- **State / structure**: `01_estructura/ESTADO.md` (what works/fails),
  `01_estructura/ARBOL.md`, `01_estructura/HISTORICO_AGENTS.md` and
  `01_estructura/HISTORICO_RELEASES.md` (history, on demand only).
- **Formats**: `03_formatos/AMO_AWO.md`, `BIN_LAYOUT.md`, `AWO_FORMAT.md`
  (bin format), `ACM_FORMAT.md` (moveset), `STAGES_FORMAT.md` (stages/SPX/PS2),
  `MAPA_ROSTER_HD.md`.
- **Mods**: `02_mods/COMO_HACER_MODS.md`, `MODEL_SWAP.md`, `TEXTURAS_MOD.md`,
  `PACKS_DE_TEXTURAS.md`.
- **PS2→B3 port**: `07_ports/` (ESTRUCTURA_DIBUJO_HD + sessions + roadmap);
  operational summary in §3.4 of this document.
- **Tools / build / cleanup**: `04_herramientas/TOOLS.md`,
  `05_build/COMO_COMPILAR.md`, `06_limpieza/`.
- **PS5**: `PS5.md` (user guide) + `ps5/README.md` (architecture, patch layers).
- **Performance / HD textures**: `07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md`,
  `ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md`.
- **Recent sessions** (one per release): `SESION_*_2026-09-*.md` — see the
  table in §3.0.
- **Master plan / assessments**: `HOJA_DE_RUTA_2026_09.md` (active),
  `HOJA_DE_RUTA_ACELERADA.md`, `RE_MASTER_2026_09.md`, `DICTAMEN_GPT6_ASTRA.md`.
- **External tools / method**: `07_ports/UNIVERSAL_MODDER_2026-09-30.md`
  (evaluation of `rehan-remade/universal-modder`: RE with Ghidra/IDA/RenderDoc
  via MCP + oracles; applicable to Path B's bind/skin).
- **Live memory / handoff to Claude**: `MEMORY.md` (root; live state + traps +
  protocol) and `docs/MIGRACION_CLAUDE.md` (temporary migration to Claude:
  Claude returns the changes as **a single handback `.md`**, never a push to
  main; see §0 of MEMORY.md).

## 3. CURRENT STATE (EXECUTIVE SUMMARY)

**Game working**: D3D12 primary, 60.0 fps, **dual US+EU core** in a single exe,
XInput controller, keyboard by default (`mnk_mode=true`). Vulkan experimental
(part of the Linux CI). Native HD↔HD swap and textures work. Full PS2→HD port
**parked** (§3.4.10). v1.2.9 diagnostics explain themselves; **v1.3.0** adds
"Repair installation", button labels (Xbox/PS/Switch), DRED by default,
`gamecontrollerdb.txt`, the texture-extractor fix (#13) and launcher
polish/optimisation. **PS5 build** (2026-10-06): compiles for the PS5 target,
not yet run on a console (§14).

> Release-by-release detail (diagnostics, causes, measurements, DLL sizes) is
> in `docs/01_estructura/HISTORICO_RELEASES.md` §A and in the session docs.
> Here only the table and the invariants to remember.

### 3.0 RELEASE TABLE

| Release | Date | Key content | FileVersion | Session doc |
|---|---|---|---|---|
| **v1.3.0** (Latest) | 2026-09-30 | "Repair installation", button labels (Xbox/PS/Switch), DRED by default, `gamecontrollerdb.txt`, texture-extractor fix (#13), launcher polish and optimisation | 1.3.0 | SESION_LAUNCHER_V130_2026-09-30 |
| v1.2.9 | 2026-09-26 | Self-explaining diagnostics: ALWAYS-ON warnings (sustained fps, slow disk, mixed install), `vram=`/`lim=` in `perf`, VRAM guard, `entorno` line, `copy_sdk_dlls.ps1` | 1.2.9 | SESION_DIAGNOSTICO_2026-09-26 |
| v1.2.8.2 | 2026-09-24 | Texture enhancement no longer tanks FPS (dynamic-texture throttle: level 0 only) + `cfg=`/`upx_dyn=`/`texload=` | 1.2.8.2 | SESION_PERF_TEXTURAS_2026-09-24 |
| v1.2.8.1 | 2026-09-23 | Uncompressed HUD/UI dump + RGBA8 packs + cap of 4 versions/identity (issue #11) | 1.2.8.1 | SESION_VOLCADO_FORMATOS_2026-09-23 |
| v1.2.8 | 2026-09-21 | Dump fix: shared cvar registry → `REXCVAR_QUERY` (issue #11) | 1.2.8.0 | SESION_FIX_VOLCADO_2026-09-21 |
| v1.2.7 | 2026-09-21 | PCSX2-style texture packs (D3D12 + Vulkan) + tool and guide | 1.2.7.0 | SESION_TEXTURAS_PACK_2026-09-20 |
| v1.2.6 | 2026-09-20 | Polished HD texture enhancement (RGBA8, anti-ringing min-size) + TOML self-repair + anti-abuse UX for scale | 1.2.6.0 | SESION_TOML_Y_UX_2026-09-20 |
| v1.2.5 | 2026-09-19 | I/O (`dbz3_io_logging`, readahead) + focus (`fg=`, mute/dim) + diag OFF by default + log pruning | 1.2.5.0 | SESION_IO_FOCO_2026-09-19 |
| v1.2.4 EX | 2026-09-19 | FXAA/dither, mouse sensitivity, GPU knobs, portable data; polished update check | 1.2.4.1 | SESION_LAUNCHER_AUDIT_2026-09-19 |
| v1.2.4 | 2026-09-19 | Launcher audit: real `audio_gain` volume, update check, dead controls removed (superseded by EX) | 1.2.4 | same |
| v1.2.3 | 2026-09-18 | `dbz3_perf_logging` counter, AFS log silenced, HD Textures WIP/OFF | 1.2.3 | ANALISIS_RENDIMIENTO_LOGS_2026-09-18 |
| v1.2.2 EX | 2026-09-17 | Executable auto-detection + ISO-mode fixes (`NormalizeGuestPath`, folder→ISO fallback) + TOML fix | 1.2.2.1 | SESION_AUTODETECCION_XEX_2026-09-17 |
| v1.2.1 | 2026-09-14 | Launcher hotfix: pipeline join, FSR sharpness label, mod list refresh | 1.2.1 | — |
| v1.2.0 | 2026-09-14 | Renewed mod center + polished HD↔HD Model Swap + FSR/CAS sharpness | 1.2.0 | SESION_MODS_LAUNCHER_2026-09-14 |
| v1.1.4 EX | 2026-09-10 | EU crash when fighting (`fix_eu_bctr.py`), xex detection by entry point, ISO xex cache | 1.1.4.1 | — |
| v1.1.3 | 2026-09-09 | Source selector always visible, DBZ1 xex blocked, audited i18n | 1.1.3 | — |
| v1.1.2 | 2026-09-09 | Real Vulkan (`gpu_backend`), `ResolveRegion()`, **disc (ISO) mode** | 1.1.2 | — |
| v1.0.x / v1.1.0-clasico | 2026-09 | Archived (not Latest). The old binary zips do NOT exist | — | HISTORICO_AGENTS |

> Later releases (v1.4.0 → v1.4.2.2) are in `CHANGELOG.md` and `MEMORY.md`.

### 3.0b INVARIANTS (do not rediscover)

- **Real cost = supersampling**, not HD textures: `draw_resolution_scale` makes
  the guest really render at Nx. At 3x internal without HD textures ≈ 51 % GPU;
  at 1x+FSR ≈ 22 %. That is why `1x` is the default and recommended, and the
  presets **never** raise the scale. Scale>1x + texture enhancement = the most
  common source of the "it runs at 30" report (frame > 16.7 ms ⇒ vsync at half
  rate).
- **HD textures** (`dbz3_hd_textures` = Off/x2/x3): Nx host resource + mips,
  without touching guest files or memory. Scales **native DXT and RGBA8**; costs
  VRAM; `dbz3_upscale_min_size`=16 avoids the HUD; anti-ringing clamp.
- **An out-of-range cvar does NOT break the toml**: only that cvar is rejected
  (`warning Config: invalid value for cvar`). (An old `dbz3_texture_upscale=4`
  did break the whole file; that cvar no longer exists.)
- **Runtime build stamp**: `rex/dbz3_build.h` (`DBZ3_RUNTIME_BUILD`) is
  published via `dbz3_runtime_build` / `dbz3_gpu_build` (the DLLs have **no**
  VERSIONINFO). Bump it together with `src/version.rc`; `verify_release.ps1`
  requires it.
- **Controller**: `input_backend = "xinput"` (avoids a hang with RTSS/OBS); SDL
  as alternative selector.
- **Mods**: per-AFS-entry override + virtual mid-insert (§6).
- **PS2→HD port**: Path A (injection) = approximate delivery; Path B (full
  port) = parked on the bind/skin (§3.4.10). Janemba IW→B3 discarded.
- **PS5**: single-region build (US or EU from the user's executable), no
  launcher, settings from `/data/dbz3/dbz3_user.toml`; the PS5 SDK patch must
  stay in sync with `patches/rexglue-sdk/` (§14).

### 3.1 SWAPS AND PORT — VALIDATED PATHS (2026-08-17..08-26)

- **✅ NATIVE B3→B3 SWAP = WORKS**: the character's full #AMB bin (AWO+AZT) in
  another's slot. Validated (sw_goten_nativo, sw_vegeta424, swap_96_on_327).
- **The correct AFS method is MID-INSERT** (the bin grows in its slot, later
  entries +delta, delta rounded to 0x800). **`--append` DISCARDED** (breaks the
  table order → the guest uses binary search → crash 0xC0000005).
- **CRITICAL CONSTRAINT (simple override)**: the guest reads the entry with a
  FIXED `to_read = ceil(slot/0x1000)*0x1000`. The mod's compressed bin MUST fit,
  unless the **virtual mid-insert** (§6) is used.
- **HD MATRICES == PS2 (47/47, zone by zone)**: same skeleton, same world.
  Bone B's PS2 local coords are injected into bone B's HD slots.
- **Injection (HD template + PS2 positions) = RECOGNISABLE** (best: cell_npm4,
  binary threshold 0.8): PS2 body + HD limbs/head. See §3.4.
- **Full port (PS2 topology) = ❌ DOES NOT RENDER (2026-09-11)**: the GPU draws
  with **self-contained 44 B windows** in the `[vb0,ib)` region of the AWO + IB.
  The port's geometry is **exact** and **reaches the GPU**; the **draw is also
  correct** (1 strip draw, VB+IB verbatim) and the **remaining blocker is the
  skinning/bind**. ⚠️ The "previous validation" was the native swap
  (`cell_native`), NOT the port. See §3.4 +
  `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`.
  Tool: `awo_tools/awg_vertex_buffer.py`, `mod center hd/ports/port_b3_strip.py`.
- **VB2 = part of the window region**: "injection only touches sec34" belonged
  to the old model; with windows+IB the whole body is rebuilt at once.
- **Janemba (IW→B3) = DOCUMENTED FAILURE**: deformed mass, removed/archived
  (detail in HISTORICO and `awo_tools/CONSOLIDADO.md` §13.5). Do NOT retry
  without a validated full converter.
- **Discarded test case**: Pikkon IW (PKH skeleton different from KLL, 58 bones
  with skirt) → NOT 1:1. For a full port look for a 1:1 skeleton.

### 3.2 🔴 REAL B3 VERTEX LAYOUT (EMPIRICALLY VERIFIED)

**sec34 (stride 44, align +2)** — b327_hd.bin + goten_298.bin:
```
+0   0xFFFFFFFF (nan marker)
+4   u | +8   v | +12  z_local | +16  x_local | +20  y_local
+24  weight (0.1-1.0) | +28  BONE (u32, 0-35)
+32  nrm.z | +36  nrm.y negated | +40  nrm.x
```
Verified: 36 unique bones 0-35, normals |mag|≈1, weight 0.1-1.0, FFFF at +0.
⚠️ **The bone is at +28, NOT at +0x10** (the old tools wrote at +4/+16 →
deformed mass). Tools using the B1 layout
(`[pos@+0, weight@+12, BONE@+16, nrm@+20, uv@+40]`) are NOT valid for B3.

**vb2 (Krillin, "static" layout)**: `[pos.x_abs, y, z, 0,0,0, weight=0,
0xFFFFFFFF@+28, nx, ny, nz]` (ABSOLUTE positions, bone=FFFF = no skin).
**vb2 of Cell F2 (layout B, 276 slots)**: `[1.0, 0, 0, ?, ?, ?, nan@+20,
U@+24, V@+28, nrm@+32]`.

**Format C (most bins: Goku 264, Vegeta 424, Babidi, Goten)** — AWG0,
stride 44 WITHOUT align:
```
+0 x | +4 y | +8 z (bone-local, [-1,1]) | +12 0xFFFFFFFF
+16 u | +20 v | +24 n.x | +28 n.y | +32 n.z | +36 weight | +40 BONE
```
IB = triangle STRIP (consecutive, alternating winding, degenerates as jumps),
WITHOUT 0xFFFF restarts. `+0x2C` is the buffer SIZE in bytes (not an offset).

**Face AWG (nb=1, Goku/Vegeta)** — buffer ALWAYS at h+0x1F0:
```
+0 FFFF | +4 u | +8 v | +12 x | +16 y | +20 z (head-bone local)
+24 weight=1.0 | +28 pad 0.0 | +32 nx | +36 ny | +40 nz
```
`+0x2C` = buffer size (n*44), `+0x30` ib_rel, `+0x34` = IB SIZE in bytes (not
an offset!), `+0x38` end. Descriptor at h+0x180 (+0x1C n_verts, +0x24 n_tris).
IB = triangle list. Buffer and IB overlap by 32 B
(`ib_rel = 0x1F0 + n*44 - 32`).

**Mesh group structure (AWG0 +0x640)**: mesh-ref blocks (0x50: X=descriptor
index, Y=primary bone), axes (80B: +0x34 arm_ptr, +0x38 child, +0x3C sibling,
+0x40 parent — **parent is an OFFSET rel AWG0, not an index**), zone matrix
(0x28E0: diagonal of bones + pointers to bboxes), bboxes (AABB per zone, 0x40),
descriptors (0x60). **Descriptor** (§3.4.8): `A_start<<8 | A_count<<8 |
B_start<<8 | B_count<<8 | 0x01` (flag at +0x5C). **A = VERTEX range of the
pool `[A_start, A_start+A_count)`** (NOT `[min(B),max(B)+1]`; the A ranges
**tile the pool without overlap**). B = INDEX range of the IB; IB indices are
**global** (they cover all of A). The "max N m" descriptors (found at `+0x18`)
are at stride 0x60.

### 3.3 B3 BONE MAPPING (Krillin, 51 bones, index = label)

```
0=XKLL_BODY 1=KLL_WAIST 2=KLL_STMC 3=KLL_OBI 4-7=KLL_ROBI1-4 8-11=KLL_LOBI1-4
12=KLL_CHEST 13=KLL_LCHN 14=KLL_LARMROT 15=KLL_LARM1 16=KLL_LARM2
17=KLL_LHANDROT 18=KLL_L00_LHAND 19=XKLL_NLA 20=KLL_RCHN 21=KLL_RARMROT
22=KLL_RARM1 23=KLL_RARM2 24=KLL_RHANDROT 25=KLL_L00_RHAND 26=XKLL_NRA
27=KLL_NECK 28=KLL_HEAD 29-37=XKLL_M_* (face) 38=KLL_LLEGROT 39=KLL_LLEG1
40=KLL_LLEG2 41=KLL_LFOOT1 42=KLL_LFOOT2 43=XKLL_NLF 44=KLL_RLEGROT
45=KLL_RLEG1 46=KLL_RLEG2 47=KLL_RFOOT1 48=KLL_RFOOT2 49=XKLL_NRF 50=XKLL_NW
```
sec34 uses bones 0-35 (no legs/face → they go to vb2). **B1** (52 bones)
shares labels but in a DIFFERENT ORDER → map BY LABEL, not by index.
Tool: `analyze_awo_b1.py` (B1 AWO structure, in dbz1).

### 3.4 🔴 MODEL PORT PS2→B3 HD — CONSOLIDATED STATE

> The ONLY reference for the port. Verbatim detail (table of attempts T2-T11,
> chronology, GPU experiments) in `HISTORICO_RELEASES.md` §B; session documents
> in `docs/07_ports/`.

### 3.4.1 STATE OF THE PATHS

| Path | State | Best result | Notes |
|---|---|---|---|
| Native B3→B3 swap | ✅ WORKS | sw_goten_nativo, sw_vegeta424 | full #AMB bin in another's slot |
| Injection (template + PS2 positions) | ✅ WORKS (recognisable) | **cell_npm4** (binary threshold 0.8) | PS2 body + HD limbs/head |
| Full port (PS2 topology) | ❌ DOES NOT RENDER | geometry + draw CORRECT (1 strip draw, VB+IB verbatim); bind/skin/bones/IB/UV **verified identical** to native (2026-09-30) → the cause is NOT the skin | See 3.4.5 and 3.4.10 |
| HD→HD head swap | ◑ partial | goku_armadura v3 | z-fighting, paused |

### 3.4.2 VALIDATED FACTS (how the guest renders)

1. **Draws = 0x60 descriptors + prim PER DESCRIPTOR** (proven 2026-09-11):
   `(dma-0x1BD00000)//2 == B_start`; the IB is used **verbatim** (33/33 body
   draws). Body = `prim=6` (strip), hands/face = `prim=4` (list); the prim is
   at **`+0x48`** of the descriptor (`0x500` strip / `0x400` list) and at
   `+0x30` of the arms' part-descriptors (5/4). D3D enum: `kTriangleList=4`,
   `kTriangleStrip=5`.
   ⇒ **🔴 ROOT CAUSE of the port**: `port_b3_windows.py` emitted the IB as a
   **LIST** but the guest draws the body as a **STRIP** ⇒ "explosion". Fix: IB
   as **strip** (`port_b3_strip.py`).
2. **GLOBAL vertex fetch** (`VF[95] 0x1BD04000 size=5148×44`); **the A ranges
   are NOT used for the fetch**; only `B` + prim matter.
3. **The guest uses the vertex's bone (+28) for the transform** (bone0 test:
   bones→0 collapses EVERYTHING to the feet; upper face and one hand survive →
   they live in vb2).
4. ~~Positional consumption of the pool~~ ⇒ **REFUTED**: the GPU buffer is a
   verbatim copy of the pool and the guest uses the file's IB; the deformation
   of T3/T4/T9 was a **tool index-base bug** (`awg_vertex_buffer._parse` used
   the max IB index; it now uses `g(0x2C)//44`).
5. **vb2/bones**: the sec34 template uses ONLY bones 0-33; the number of
   AWGs/bones varies per character (Krillin 18 AWG/51; Bulma 2/43; Babidi
   1/41). The bin is **SELF-CONTAINED** (formats A/B/C; the guest
   auto-detects). ⚠️ **Format C** (Babidi): marker ≠ FFFFFFFF, no +2 align and
   bone at **+40**. The pipeline must auto-detect A vs C.
6. **PS2→bone-local conversion**: `local = inv(world[bone])·model` (verified).

### 3.4.3 THE TWO PATHS (operational)

- **Path A — INJECTION (delivery)**: keep the template's pool ORDER and
  rewrite pos/normals (`[nz,-ny,nx]`) with PS2 geometry converted to
  bone-local. Critical parameter: **binary threshold** (0.8 good; 2.0 and the
  blends/soft ALWAYS bad). Does not re-topologise.
- **Path B — FULL PORT (parked)**: pipeline `port_b3_windows.py` →
  `port_b3_strip.py` (IB as **strip** + nulls arms `+0x3C` **and `+0x44`** +
  `desc[0]=B[0,n_ib)`). After that only **1 draw** remains with correct
  verbatim VB+IB, **but it is still deformed**. `grow()` is FINE (validated
  with native `_grow_tpl`). ⚠️ Do NOT use as a delivery.

### 3.4.4 CHRONOLOGY OF ATTEMPTS (summary)

Full table of attempts T2-T11 (Phases B/C/GPU) in `HISTORICO_RELEASES.md` §B.
Summary: T2/T8/T10/T11 = **IDENTICAL** (consistent relabelling = geometric
identity); T3/T4/T9 = **DEFORMED** (it was the tool's index-base bug);
T5 = worse; T6 = normal (**A is not used for drawing**); T7 = massive (**the
IB rules**). See §3.4.9.

### 3.4.5 BLOCKERS / THINGS NOT TO REPEAT

1. **Pool partition by part ranges** (Phase C): vertices are in `(start,count)`
   ranges per part, declared in **A of the 0x60 descriptors** and in the
   **arms' part-descriptors** (`+0x38/+0x3C`); their union **tiles
   `[0,n_pool)` without overlaps or gaps** (Cell F2: 29 desc. + 7 parts =
   2937/2937). IB indices (B) are **global**. The "2nd table @AWG0+0x1F80"
   was the **bind-pose matrix table** (the arms' `p2`).
2. **T8**: permuting **whole parts** + remapping the IB → **IDENTICAL** (the
   GLOBAL order of parts is free). **T9**: reordering single-bone runs
   **inside** a block → **DEFORMED** (the intra-block order matters and there is
   no position→bone table in the bin). ⇒ moving only whole parts is safe.
3. **`_bone0port` (everything rigid to bone 0) CRASHES**: record 0 of the
   captured palette is all zeros ⇒ the palette slot is NOT indexed by the raw
   bone. ⚠️ Do NOT retry.
4. **`--hd-skin` (nearest neighbour) MAKES IT WORSE**; `--fit`/`cluster_fit`
   decimates and deforms the mesh (invalid for render validation).
5. **⚠️ Test contamination**: `AfsFindModOverride` serves the FIRST active mod
   (alphabetical order) → **ONLY ONE active mod per test**.
6. **AWG0/sec34 growth**: in excess → crash 0x856AC389. For the port use counts
   ≤ template or solve the growth.
7. **PS2 source**: the `ps2_games/*/data_cmn.afs` ARE authentic LE #AMO0/#AMG
   (B3 GH 558 #AMO0 / 0 #AWO).
8. ⚠️ Draw/palette instrumentation already **REVERTED**; the canonical DLL has
   NO instrumentation. `dump_shaders` must be removed from `dbz3_user.toml`
   when done.

### 3.4.6 NEXT STEPS (if resumed)

1. Practical Path A: reactivate/refine `cell_npm4`; extend to the 16 auxiliary
   AWGs (`port_ps2_b3_inject_aux.py`, see §10).
2. Path B: **CORRECTED 2026-10-03 (§24)** — the blocker is **NOT the shader**:
   B3 HD **does not skin on the GPU** (no VS indexes constants; no
   `memexport`; the body VS = rigid transform with a `c0..c3` matrix identical
   across the ~33 chunks). Skinning is **CPU-side (Xenon)**. The data are fine
   (identical bind §21 and verbatim VB §22). **Next step = RE of the CPU
   skinning routine** in the recompiled code (`generated/`/`generated_eu/`):
   which vertex space/order the guest expects. See
   `SESION_DRAW_SEMANTICS_2026-09-11.md` §21-§22 and **§24**.
3. `vb2` (layout B) for face/legs.

### 3.4.7 REFERENCES

- `docs/07_ports/SESION_FASE_B_ARMS_2026-09-10.md`,
  `SESION_FASE_C_CONSUMER_2026-09-10.md`,
  `SESION_GPU_DRAW_2026-09-11.md`,
  `SESION_DRAW_SEMANTICS_2026-09-11.md` (definitive + RESUME §0),
  `SESION_VIA_B_RENDER_2026-09-12.md`, `INVESTIGACION_PS2_HD_2026-09-13.md`,
  `ESTRUCTURA_DIBUJO_HD.md`, `HOJA_DE_RUTA_PORT_PS2_B3.md`, `PLAN_PS2_B3/`.
- Canonical Path B instrument: `awo_tools/awg_vertex_buffer.py` (`info`/
  `permute`/`roundtrip`/`grow`/`selftest`; `bind_worlds()`/`bone_labels()`/
  `window_from_model()`; API `load().vertices/.indices/.emit()`).
- Port oracle (2026-09-30): `awo_tools/bind_oracle.py` (compares structure,
  `world`, bounds and model-space positions of two bins) +
  `bind_oracle_bones.py` (per-bone error). They expect the **full decompressed
  #AMB** (`xbdecompress`), not an isolated #AWO.
- Phase tools: `phase_c_descriptors.py`, `phase_c_arms_targets.py`,
  `phase_c_meshgroup.py`, `phase_b_*.py`, `afs_extract_hd.py`.
- Pipeline in `mod center hd/ports/` (`port_ps2_b3_extract/geometry/draw/pack/
  verify.py` + `port_ps2_b3_inject.py` + `port_b3_windows/strip.py`).

### 3.4.8 0x60 DESCRIPTORS AND POOL PARTITION (Phase C, 2026-09-10)

**0x60 descriptor** (ASCII tag `"max N m"` at `+0x18`):
```
+0x00 label[]     +0x18 "max N m"   +0x44 type==0x2C00   +0x48 prim (0x500 strip / 0x400 list)
+0x50 A_start<<8  +0x54 A_count<<8     A = VERTEX range of the pool
+0x58 B_start<<8  +0x5C B_count<<8     B = INDEX range of the IB
```
- **A tiles the pool** `[0, n_pool)` **without overlaps**; IB indices (B) are
  **global** (`min==A_start`, `max==A_start+A_count-1`).
- Part descriptors (arms) have the range at `+0x38/+0x3C` + label at `+0x48`;
  **they fill the gaps**.
- **Total partition (Cell F2)**: `[0,2937)` = 29 descriptors + 7 parts, 0
  overlaps, 0 gaps (`awo_tools/phase_c_descriptors.py`).
- 4×4 bind-pose matrix (64 B) of each arm in the `AWG0+0x1F80` table (the
  `p2`).

### 3.4.9 DRAW SEMANTICS (definitive, 2026-09-11)

- **The guest uses the port's IB VERBATIM** (33/33 draws match
  `AwgVertexBuffer.load(port).indices()`).
- **44 B window** (VERBATIM copy of `[vb0, ib)` of the AWO; `ib = awg0+g(0x30)`,
  `vb0 = ib - g(0x2C)`; `g(0x2C)` = buffer SIZE in bytes):
  ```
  +0 pos.xyz(3f) | +12 w | +16 bone(u32,1B) | +20 nrm.xyz(3f) | +32 FFFFFFFF | +36 uv.xy(2f)
  ```
  The IB (`g(0x30)`, int16 BE) references window indices. `pos` = bone-local;
  semantics `pos = inv(world[bone])·model`.
- **2nd draw source = the arms' part-descriptors** (`+0x40 idx_start`,
  `+0x44 idx_count`); nulling only `+0x3C` is NOT enough: **`+0x44` must also
  be nulled** (`port_b3_strip.py` already does it).
- **Discarded attempts** (do NOT repeat): `_desc_one` (`+0x48` is not enough
  to change the prim), `_strip2` (deformity changes but it still explodes),
  `_body33`, `_nottail`, `_bone0port` (crash), `_strip4*`, `_hdskin_strip`.
- ✅ **`grow()` is correct** (with `awg+0x2C` and `awg+0x34` updated);
  `_grow_tpl` (grown native template) renders PERFECTLY.
- **Remaining blocker = bind/skin** (see §3.4.6). PS2==HD `world` (48/48) and
  labels 48/48 ⇒ skeleton and mapping correct.

### 3.4.10 CLOSURE — Path B PARKED; HD↔HD = delivery

**Decision** (2026-09-13): Path B (real bind) **parked** (not impossible).
Path A documented as approximate. The delivery is the **native B3 HD↔HD swap**
(already in the launcher). Detail:
`docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` §20.
- **🔴 REAL LAYOUT (all 17 AWGs)**: ALL use the **window layout** (`pos@0`,
  `w@12`, `bone@16`, `nrm@20`, `FFFFFFFF@32`, `uv@36`, stride 44); region
  `[ib−g(0x2C), ib)` with exactly `g(0x2C)/44` slots (FFFF@32 in 100 %).
  ⚠️ **The "sec34" layout (`FFFF@0`,`bone@28`) is wrong** for these bins;
  `port_ps2_b3_inject.py` wrote with a 428 B (10 slot) offset. Fixes in
  `%TEMP%\opencode\phaseb\make_winbody.py` + `make_winaux.py`.
- **Path B — blocker = `M_bind`**: `world` (axes) gives a correct T-pose but is
  not the skin's exact bind; the palette = transform applied to `pos`
  (bone-local). To resume: RE of `sub_82087F58` or capture the palette in
  BIND/T-pose.
- **🔴 CORRECTION 2026-09-30 (offline oracle)**: comparing `cell_native`
  (renders fine) vs `cell_win2` (port) **decompressed**, the **bind (`world`) is
  IDENTICAL** (diff 0.0), the **`bone` @+16 IDENTICAL** (0/2948), the **`uv`
  @+40 IDENTICAL**, IB/bones equal, **no axis permutation**, and the model-space
  bounds almost identical. Only `pos`/`nrm` change (max 0.78 u). ⇒ **the port
  is structurally correct; the bind/skin/bones are NOT the cause.** If it
  explodes in game, the cause is in how the renderer interprets `pos`/`nrm` or
  in the **VB served to the GPU** (check that the GPU copy == `[vb0, ib)` of the
  PORT's bin and that `n`/`n_ib` are the port's). Refutes the hypothesis "root
  cause = skin `(pos,bone)`" of §10. Tools: `awo_tools/bind_oracle.py` +
  `bind_oracle_bones.py`; detail in `SESION_DRAW_SEMANTICS_2026-09-11.md` §21.
- **🔴 RESOLVED 2026-10-01 (runtime verification)**: `rexgpu-xenos`
  (`command_processor.cpp` d3d12, **ALREADY REVERTED**) was temporarily
  instrumented to dump the **real VB served to the GPU**. Result: the body VB
  (129712 B, `vfetch=95`) is a **VERBATIM copy of the PORT's bin** (sha1
  `91fa3a12…`, **32428/32428 dwords**), NOT of the native one (21214). ⇒ the
  bin→GPU chain is **correct end to end**. The cause of the deformed render is
  **exclusively in the skinning shader** (`pos`/`nrm`+palette), not in the data.
  Tools: `awo_tools/vbdump_info.py` + `vbdump_vs_bin.py`; detail in §22.
- **🔴 PATH A `cell_win2` — arm/head defect = INHERENT (2026-10-03)**: on the
  select screen the Path A port renders a **coherent** Cell but with **localised
  grey faceted planes** on the right arm and a grey wedge on the head crest
  (`cell_native` = perfect). Offline oracle (render of EACH AWG with the bind
  matrix of the correct bone: hands `world[23]/[30]`, face `world[40]`): the 16
  aux AWGs fall **in the correct sockets** and overlap the native **almost
  exactly** in bind pose → **the defect does NOT reproduce statically**.
  Field-by-field diff: `pos`/`nrm` differ (Path A projects the HD mesh onto the
  PS2 surface; shape/silhouette do not match 100 %), `uv`/`weight`/`bone`/
  `marker`/`IB`/header/axes/bind **identical**. **There is NO normal-rotation
  bug** (applying `inv(R)` to the port's normals moves them AWAY from the
  native). ⇒ The grey artefact is a consequence of **shading approximate
  geometry**, it is accentuated in animation; it is **not** fixed by touching
  normals. Real paths: (a) refine injection (thresholds/`--bone-aware`/
  `--normal-only` per zone) or (b) unblock Path B (§22). Detail:
  `SESION_DRAW_SEMANTICS_2026-09-11.md` §23.
- **HD↔HD SWAP (delivery)**: `mod center hd/swap_b3.py` + `catalog_b3.cat`
  (183), virtual mid-insert. In the launcher: "Model swap" tab. Source==target
  guard in `src/launcher/mod_pipeline.cpp`.
- **🔴🔴 SKINNING RE — B3 HD DOES NOT SKIN ON THE GPU (2026-10-03)**:
  `rexgpu-xenos` (`command_processor.cpp`, **ALREADY REVERTED**) was
  instrumented with per-draw capture (marker `dbz3_paldump.on`, log
  `dbz3_paldump.log`: shader hash + `c0..c63` + vf0). **Hard** results:
  1. **No vertex shader indexes constants dynamically** (no `a0`/`arl`/`lc`)
     and **no shader uses `memexport`/`alloc export`** ⇒ there is no palette on
     the GPU.
  2. The body VS is **a rigid transformation**: `vfetch` of `vf0` (pos/nrm/uv)
     and `mad/mul` against **a single 4×4 matrix in `c0..c3`**.
  3. **ALL** body draws in a scene use the same shader `FDF960B5D7869030`,
     `indx_offset=0`, and **IDENTICAL `c0..c3`** across the ~33 chunks (counts
     3..1995) ⇒ the vertices arrive **already in world space**.
  ⇒ **Skinning is CPU-side (Xenon)**: the guest reads the bind pose, applies
  bone matrices and writes world space; the VS only projects. **This REFUTES the
  hypothesis "cause = skinning shader"** (§3.4.6/§10 and §22). The real blocker
  is **which space/order the guest expects the bin's vertices in for its
  skinning routine**. Next step: RE of the CPU skinning routine in the
  recompiled code (not the shader). Detail:
  `SESION_DRAW_SEMANTICS_2026-09-11.md` §24. RE artefacts deleted; canonical DLL
  restored (6360064 B).

## 4. USEFUL COMMANDS

```powershell
# Build the game (release, uses the SDK installed in rexglue/)
cmake --build "out\build\win-amd64-release"
# 🔴 AFTER every game build: re-copy the canonical DLLs (the build overwrites
# them with the stale/avx2 ones from rexglue/bin -> a test would measure another runtime)
powershell -ExecutionPolicy Bypass -File tools\copy_sdk_dlls.ps1
# Dual build (US+EU): cmake -B out/build/win-amd64-dual -DDBZ3_DUAL_REGION=ON ...
# EU build (historical, no longer used): -DDBZ3_GENERATED_DIR=generated_eu

# Build SDK 0.10 (universal SSSE3 baseline — the ONLY one in use)
cmake -G Ninja -S rexglue-sdk-0.10 -B rexglue-sdk-0.10\out\build-win-vulkan-baseline `
  -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe" `
  -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe" `
  -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" `
  -DREXGLUE_ENABLE_FIDELITYFX=ON -DREXGLUE_USE_VULKAN=ON `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=x86-64 -mssse3"
# ⚠️ build bug: copy the FIXED (ASCII) ffx_api_dll.rc from another build BEFORE building
# The dx12 FFX is generated in bin/ → copy it to the out (it is not installed by itself)
cmake --build rexglue-sdk-0.10\out\build-win-vulkan-baseline --target rexruntime rexgpu-xenos

# LZX compression of 360 bins (the game's format) — /N:2048, NOT /N:32
xbcompress /N:2048 <src> <dst>   # compress
xbdecompress <src> <dst>         # decompress
# XDK tools: "mod center\Xbox 360 Compression - Decompression tool..."

# ACCELERATED roadmap (S0-S4) and its automations
#  docs/HOJA_DE_RUTA_ACELERADA.md            <- active execution plan
#  tools/lab_f0.ps1                          <- baseline: hashes+region+mods+classified logs
#  awo_tools/corpus_scan.py                  <- parse-all AFS -> JSON+SQLite (Content DB)
#  mod center hd/swap_matrix.py              <- move ANY blob between slots/regions
#  tools/make_test_iso.py <out.iso> <folder> <- test XDVDFS (validate disc/ISO mode)
```

```bash
# PS5 build (Arch Linux as root; see §14 and docs/PS5.md)
bash ps5/make_ps5.sh --iso /path/to/your.iso --console <PS5 IP>
```

**⚠️ Building the game**: ALWAYS pass
`-DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe"` and
`-DCMAKE_PREFIX_PATH=.../rexglue` (the win-amd64-release preset resolves clang
to the retcomm/MinGW toolchain, which does NOT compile `rex/chrono/chrono.h`).

## 5. FILE FORMAT — SEE `AWO_FORMAT.md` (+ docs/03_formatos/)

**Summary**: AFS (LZX-compressed bins with magic `0F F5 12 EE`) → big-endian
#AMB → #AWO (360 model) vs #AMO0/#AMG (LE PS2 model). The 360 HD uses the bin
numbering of the **PS2 Greatest Hits data_cmn** (Krillin 327-329). The #AWO IS
the same PS2 model (51 bones, 18 mesh groups, 68 identical labels, **NO
re-rigging**) only big-endian with renamed magics (#AMO0→#AWO, #AMG→#AWG,
#AMT→#AZT) and a different mesh-group layout.

**Key HD format data** (offsets rel AWO):
- `+0x1C` AMG offset table | `+0x24` bone labels | header with 51 entries of
  0x20 (pointers to axis zones at +0x34,+0x54,...).
- Each #AWG: labels at 0x40, axes at +0x14 (rel AWG), `+0x2C` vb2, `+0x30` ib,
  `+0x34` sec34, `+0x38` restart. **The AMG table points to the #AWG magic**.
- Texture = #AZT block (header tex_am@+0x10, index_loc@+0x14; texture: idx@+0,
  type@+4, w@+16, h@+18, data_off@+0x14 rel AZT of the 128B DDS header + DXT3/BC2
  bitmap w*h bytes, mipmaps=0).
- **The runtime's AFS table is read at offset 8** (magic "AFS"(3B)+pad(1B)+
  count(4B)=8B, then (addr u32, size u32)×8B). **NOT at 0x10** (the scripts with
  the off-by-one served bin N+1 → crash).

**The game's AFS**: `adx_jpn/usa.afs` (audio), `data_cmn.afs` (characters +
main content, 286 MB), `data_eng/ger/spn/fra/ita/usi.afs` (select/menus per
language), `lang_jpn/usa.afs`, `data_yah.afs` (small, not located yet).

## 6. CORRECT MOD PIPELINE (per-entry override)

The runtime has `AfsFindModOverride` (rexglue-sdk-0.10/src/filesystem/afs.cpp)
which serves files per AFS ENTRY without repacking:

```
mods/<mod>/us/<afs>/<entry_index>            ← direct file
mods/<mod>/us/<afs>/<entry_index>/<file>     ← folder with a file inside
```

The same layout works on the PS5 under `/data/dbz3/mods/` (§14).

### The 3 fixes (cause of historical hangs)
1. The hook supports folders (iterate and use the first regular file) → log
   `AFS OVERRIDE HIT (folder)`.
2. **LZX compression `/N:2048`** (NOT /N:32): with /N:32 the bin exceeds the
   slot → the guest truncates → crash.
3. **Padding to the exact size** of the slot the guest reads (`to_read`). If
   it is shorter → crash.

### 🔴 VIRTUAL MID-INSERT (swaps in any direction) — 100% LIGHTWEIGHT (2026-09-09)
- `AfsGetVirtualTable`: if an override exceeds `to_read`, the entry grows in
  place (0x800-aligned) and later ones shift by the accumulated delta
  (CONSISTENT virtual table, replicates a mid-insert rebuild).
- 🔴 **NO giant files**: NO rebuilt AFS is materialised on disk. All
  consistency is resolved in memory via `AfsVirtualRange` (ReadSync): each byte
  of the requested range is translated to the physical file or the override,
  and gaps/pads/EOF are served as ZEROS. A physical read with an untranslated
  offset is never done.
- **History (crash 2026-09-09)**: the first virtual version served only the
  starting entry of each read and fell back to a physical read with the virtual
  offset for the rest → garbage → the #AMB parser dispatched a non-existent
  magic (`#ACP`) → crash `UNREGISTERED indirect call` target=0 in
  `sub_820800A8`. The PHYSICAL rebuild (`AfsRebuildPath`, 286 MB in %TEMP%)
  worked but VIOLATED the low-footprint promise → discarded.
- **Growth criterion**: it only grows if override > `to_read` (what the guest
  already allocates), NOT if it exceeds the physical slot.
- `AfsFindModFileOverride`: WHOLE-FILE replacement in `mods/<mod>/<filename>`
  or `mods/<mod>/us|eu/<filename>` (og_music, sfd, etc.), served via
  `HostPathEntry::Open`.

### Verification in logs
```
AFS OVERRIDE HIT (folder): ...\mods\<mod>\us\data_cmn.afs\327\geom.bin
AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=...
```
> `got=106496` = full bin served. If `got < to_read` → padding missing.

### Correct entry
- AFS table at **offset 8**. Visible Krillin = **entry 327** (105296 B →
  padded 106496). History: we used to edit 326 (table@0x10) = another bin.

### Mod activation rules
- **ONE SINGLE system**: a mod is active if it does NOT have the `.disabled`
  marker (`IsModEnabled` uses ONLY the marker). The cvar `dbz3_enabled_mods` is
  **DEAD CODE**. Full AFS files of old mods are migrated automatically on
  regeneration (per-entry override).

## 7. RUNTIME / SDK — CANONICAL DLLs AND BUILD TRAPS

- **Canonical SDK 0.10 DLLs** (do NOT replace with the ones regenerated by the
  build):
  - **Baseline (the only one in use)**: `rexglue-sdk-0.10/out/win-amd64-baseline/`
    → `rexruntime.dll` **10920448 B** and `rexgpu-xenos.dll` **6360064 B**
    (2026-09-29); `amd_fidelityfx_dx12.dll` 5413888.
    - rexruntime has: `audio_gain`, `dbz3_perf_logging`, `dbz3_io_logging`/
      `dbz3_io_readahead`, log pruning, `dbz3_mute_unfocused`, `frame_cap`
      (defined in `src/ui/presenter.cpp`), `d3d12_dred` (DRED ON by default,
      without the debug layer), **slow-disk warning** and the
      `dbz3_runtime_build` stamp.
    - rexgpu-xenos has: `fg=` and `cfg=`/`upx`/`upx_dyn=`/`texload=`/`vram=`/
      `lim=` in the `perf` line, mips fix of the `texture_upscale_cs` shader +
      anti-ringing clamp, extension to native RGBA8, `dbz3_upscale_min_size`,
      the `UpscaleBudgetAllows` video guard, dynamic-texture throttle
      (v1.2.8.2), VRAM guard and sustained-fps warning (v1.2.9), the dev dump
      `dbz3_texture_dump`/`dbz3_texture_dump_max`, the `dbz3_texture_packs`
      loader and the `dbz3_gpu_build` stamp; **no** draw instrumentation.
  - avx2 (classic fallback): `out/win-amd64/` → rexruntime 10951168,
    rexgpu-xenos 6207488 (or 6210048), ffx 5420544, TracyClient 246784.
  - legacy: `out/win-amd64-legacy/` (variant removed; can be cleaned up).
- ⚠️ **The SHA256 varies per build** (embeds a timestamp) → compare by **size**
  or rebuild and copy. The sizes of BOTH DLLs change when the SDK is rebuilt;
  the reference value is that of `out/win-amd64-baseline/` (what
  `verify_release.ps1` uses). Sizes of previous releases: 10910720/6346240
  (v1.2.8.2), 10910208/6227456 (v1.2.6), 6346752 (v1.2.7), 6340096 (v1.2.8),
  6342656 (v1.2.8.1), 10910208/6355456 (v1.2.9); **10920448/6360064**
  (v1.3.0, 2026-09-30; same size as v1.2.9 but stamp `1.3.0`).
- ⚠️ **Build stamp**: `rex/dbz3_build.h` (`DBZ3_RUNTIME_BUILD`) is published
  by the cvars `dbz3_runtime_build` / `dbz3_gpu_build`; **bump it together with
  `src/version.rc`** (`verify_release.ps1` checks it). The launcher uses it to
  warn about mixed installs. **When bumping the version, rebuild `rexruntime`
  and `rexgpu-xenos`** (SDK baseline targets) so the embedded stamp matches;
  otherwise the warning fires on ALL new installs.
- **🔴 The game build OVERWRITES `rexruntime.dll`** with the stale version from
  `rexglue/bin`: after `cmake --build`, copy the canonical ones with
  `powershell -ExecutionPolicy Bypass -File tools\copy_sdk_dlls.ps1` (it warns
  if the stamp is missing; close dbz3.exe or the file is locked). Verify:
  `Select-String rexruntime.dll -Pattern "AfsGetVirtualTable"` must say PRESENT
  and the `dbz3_perf_logging` marker must exist (if missing it is the stale
  10,863,616 B one and the `perf fps` lines do not appear).
- **🔴 When the SDK is rebuilt, the FFX in `rexglue-sdk-0.10/bin/` is
  regenerated differently** — do NOT copy it. Use the ones from the canonical
  `out/` folders.
- **SDK patches** in `github/patches/` (afs.cpp/h, host_path_file.cpp,
  host_path_entry.cpp, input_system.cpp, d3d12_presenter.cpp, presenter.cpp,
  d3d12_provider.cpp (DRED), command_processor.cpp (DRED report),
  texture_cache.*, sdl_input_driver.{h,cpp}, xam_info.cpp,
  graphics_system.cpp, function_dispatcher.cpp, rex_app.cpp). **If the SDK is
  touched: update patches/ + rebuild + copy the DLLs — and check that the PS5
  patch still applies (§14).**
- **Measuring performance**: cvar `dbz3_perf_logging` (default false; enable in
  Dev) → line `dbz3: perf fps=... frames=... max_frame_ms=...` every 5 s on the
  **guest swap** (`IssueSwap`, rexgpu-xenos). (v1.2.9) adds
  `vram=used/budget` MB and `lim=` (0 none / 1 reload streak / 2 VRAM guard),
  plus `cfg=` and `upx_dyn=`/`texload=` (v1.2.8.2). To test without a window:
  `tools/hidden_run.ps1` (applies overrides to `dbz3_user.toml` and restores;
  `dbz3_skip_launcher=true` boots directly; strings go in quotes or the parser
  discards the whole file).
- **ALWAYS-ON warnings** (v1.2.9, independent of the logging cvars; the normal
  log stays clean and the line only appears if there is something actionable,
  max 3/session): **sustained low fps** (with scale/MSAA/enhancement → vsync at
  half rate) and **slow disk** (5+ physical reads ≥ 50 ms). See
  `docs/SESION_DIAGNOSTICO_2026-09-26.md`.
- **Harness to reach the 3D DEMO** (2026-09-19): `tools/long_run.ps1`
  (Start/Status/Stop, muted and restores the toml), `tools/press_key.ps1`
  (PostMessage; W/A/S/D/Backspace/Tab map), `tools/grab_window.ps1` (PNG
  capture; requires the window **on-screen**) and `tools/click_window.ps1`.
  Recipe: boot with `dbz3_skip_launcher=true` → opening (~90-100 s) → **Start
  (Return)** → menu → idle ~2-2.5 min → 3D attract demo battle. Measured: 2x and
  3x + MSAA = 60.0 FPS, 0 errors, 6 min without a crash.
- **Runtime cvars**: `deadzone`, `rumble`, `frame_cap`, `vsync` (hardened: the
  guest ALWAYS runs at 60 Hz), `user_language` (XGetLanguage), `audio_gain`/
  `audio_mute`.
- **AFS read trace**: `dbz1_afs_reads.log` (`HostPathFile::ReadSync` +
  `HostPathEntry::OpenMapped`) and the override log `AFS OVERRIDE
  LOOKUP/HIT/MISS` are gated by `dbz1_diag_logging` (dev).

## 8. LAUNCHER — FUNCTIONALITY

> Full verbatim detail in `HISTORICO_RELEASES.md` §C. Operational summary
> (Windows/Linux; **the PS5 build has no launcher**, §14):

- **Tabs**: Video / Upscaling / Audio / Input / Mods / Native mods / Model Swap /
  Textures / Dev. Footer with an **always-visible green PLAY** + summary
  "Start: region-backend-scale-effect-language" + region selector + Reset /
  Save / **Repair installation** buttons. **Language** (`dbz3_language`):
  ES/EN/IT/DE/FR + JP (launcher via i18n.cpp `kTable[]`; the table is
  maintained by hand —add the entry with the exact ES key—: the
  `extract_i18n.py`/`gen_i18n.py` scripts are not versioned; game via
  `XGetLanguage`).
- **Executable resolution (v1.2.2)**: `ResolveBootSource()` = `CheckDefaultXex`
  of the canonical path and, if not, `FindGameExecutable()` (by **size+MD5**;
  scan of the root depth ≤3 + `root`/`DBZ3`/`assets`/`assets/DBZ3`) →
  `EnsureXexCache()` copies to `user_data/dbz3/xex_cache/default.xex` and sets
  the data root. `GameDataHostDevice` (folder) and `RegionDiscDevice` (ISO)
  serve `game:\default.xex` and prefix `DBZ3\`. ⚠️ The `OnConfigurePaths` logs
  are lost (logging starts later): the diagnosis appears on Play
  (`RelocateGameData`). **Banner**: "Executable detected: … (nothing needs
  renaming)", PLAY blocked if `!assets_ready`.
- **XexStatus** (`ClassifyXexFile`: MD5 RFC 1321 + entry point + size): US
  `A53E324B5D2A65EBCBF648E4F85A7271`, EU `C37EB979B762DA0AB5B8C9BA8037CE4E`,
  DBZ1 `5A6AB28A4911851FCA955B5925CDFEBB` (4464640 B) → blocks PLAY, HD menu
  3317760 B → `kHdMenu` blocks. `kUnknown` warns in amber but does not block.
  (`ps5/stage_game.py` uses the same checksums.)
- **Disc (ISO) mode**: cvar `dbz3_iso_path` + an always-visible "ISO (.iso)"
  selector. Plays from the `.iso` (GDFX = raw XDVDFS; magic
  `MICROSOFT*XBOX*MEDIA`) without extracting; `ExtractGameXexFromIso` extracts
  only the xex to `user_data/dbz3/iso_cache/` (`source.stamp`) and
  `RemountGameDrive` mounts a `DiscImageDevice`. `RegionDiscDevice` remaps
  `us\`→`eu\` INSIDE the device; ⚠️ **`ResolvePath` normalises the path**
  (`NormalizeGuestPath`, the VFS gives it as `\us\...`) or neither the remap nor
  the `DBZ3\` prefix is applied (0xc000000f). **Folder→ISO fallback** if the
  folder is not bootable and there is an `.iso` next to it. ⚠️ **Mods are NOT
  applied in ISO mode** (amber warning; swap disabled).
- **TOML fix (v1.2.2 + self-repair v1.2.6)**: `SaveUserSettings` passes the
  file through `EscapeTomlStrings` (escapes `\`/`"`; **idempotent**).
  `LoadUserSettings` **SELF-REPAIRS**: validates with toml++ (`TomlParses`,
  reading TEXT), and if it fails applies `EscapeTomlStrings` and reloads; state
  `ConfigLoadState` (kOk/kRepaired/kInvalid) → green/red warning at the top. If
  still invalid it does not load and saves `dbz3_user.toml.bak`. ⚠️ It runs
  TWICE per start → preserve the state. Requires `<toml++/toml.hpp>`.
- **Video**: presets (`dbz3_quality_preset` auto/performance/balanced/quality/
  manual; `auto` detects the GPU via DXGI; **no preset raises the scale**, cap
  1x; old aliases low/medium/high/ultra), internal scale
  (draw_resolution_scale_x/y), MSAA, aniso, FSR/CAS, REAL frame_cap
  (0/15-1000), VRR (`dbz3_vrr`), "Game speed: fixed 60". **Texture enhancement
  (experimental)**: `dbz3_hd_textures` (Off/**Sharp x2**/**Very sharp x3**) +
  VRAM setting (`dbz3_hd_texture_max_texels`, Low/Medium/High) in Dev. In
  **Upscaling**: **FXAA** (`dbz3_fxaa` → `swap_post_effect`; runs BEFORE the
  upscaler) and **dither** (`dbz3_present_dither`).
- **Audio (real since 2026-09-19)**: `dbz3_master_volume` → `audio_gain` (SDL
  callback gain) + Mute checkbox → `audio_mute` (live). The music/SFX/voice and
  Gamma sliders were **removed** (dead).
- **Model Swap (HD↔HD)**: catalogue `mod center hd/catalog_b3.cat` (183) →
  combos with search, preview, source==target warning; `swap_b3.py` extracts
  the #AMB bin, compresses LZX /N:2048 and installs it (virtual mid-insert if it
  exceeds `to_read`). `texture_b3.py` extract/build (DXT3/BC2, keeps size) +
  `--slot`/`--dir`.
- **Mod center**: cached list, search, enable/disable all, refresh, type
  badges, alternating rows. Install from `.zip`, profiles
  (`mods/profiles.txt`, `dbz3_mod_profile`).
- **Update check** (`src/launcher/update_check.{h,cpp}`): a background thread
  queries `api.github.com/.../releases/latest` (WinHTTP) and compares with the
  VERSIONINFO (`VersionNewer`; `1.2.4-EX` > `1.2.4` but < `1.2.5`; a local
  build > 0 counts as a repack). Shows installed version + state + "Check for
  updates"/"Retry" button; never blocks PLAY. Toggle `dbz3_update_check`.
  Requires linking `winhttp` + `version`.
- **Mixed install / stamp (v1.2.9)**: the DLLs publish their build by cvar; the
  launcher compares major.minor.patch with the exe. If it does not match (or no
  stamp) → orange banner + `[warning]` + a line in Dev; plus a line `dbz3:
  entorno os=... ram=... dbz3.exe=... rexgpu-xenos=... rexruntime=...
  amd_fidelityfx_dx12.dll=...` (real system via `RtlGetVersion`).
- **Input**: `dbz3_input_backend` (xinput/sdl), `dbz3_mnk_mode` (default TRUE),
  `dbz3_mnk_mouse`, `dbz3_mnk_sensitivity` (0.1-5.0 → `mnk_sensitivity`),
  deadzone/rumble, 24 keybinds (`dbz3_keybind_*`). **Button labels**
  (`dbz3_input_glyphs` = Xbox/PlayStation/Switch, 2026-09-30): the Controls
  tab shows readable names next to each keybind (`ButtonGlyph()` in
  `launcher_state.cpp`); **cosmetic only**, does not touch the runtime mapping.
  **Controller (SDL)**: `gamecontrollerdb.txt` (608 KB, zlib) ships next to the
  exe; the runtime loads it with the cvar `hid_mappings_file` (SDL backend).
- **Repair installation (2026-09-30)**: footer button + one-shot cvar
  `dbz3_repair` (CLI `--dbz3_repair=true` / `REX_DBZ3_REPAIR=1`) which reopens
  the launcher and shows the report in a popup.
  `dbz3::settings::RepairInstallation()` quarantines an unreadable
  `dbz3_user.toml` (`*.invalid`) and rewrites clean settings, checks
  `rexruntime.dll`/`rexgpu-xenos.dll`/`amd_fidelityfx_dx12.dll`/
  `gamecontrollerdb.txt` and ensures `user_data`. Does not touch `us/eu/`,
  `mods/` or the caches.
- **Dev**: FPS counter, diag logging gated by `DevMode() && DiagLogging()`,
  minidump on crash, GPU knobs `dbz3_async_shaders` →
  `async_shader_compilation` and `dbz3_occlusion_queries` →
  `occlusion_query_enable`, file versions.
- **User data**: `UserDataRoot()`/`UserSettingsPath()` use
  `<exe_dir>/user_data/dbz3` and `<exe_dir>/dbz3_user.toml` if writable;
  otherwise they fall back to `Documents/dbz3` (real cached probe; path visible
  in Dev). On PS5 `<exe_dir>` is `/data/dbz3` via `REX_EXECUTABLE_PATH` (§14).
- **QoL on focus loss (v1.2.5)**: `dbz3_mute_unfocused` (ON) and
  `dbz3_dim_unfocused` (ON, "Game in background" overlay). **There is NO real
  pause** (no safe mechanism).
- **I/O diagnostics (v1.2.5)**: `dbz3_io_logging` (OFF by default) → summary
  every 5 s (`reads/phys/cache/mb/pre_avg_us/read_avg_us/p95/p99/max/slow/
  opens`) + a line per read > `dbz3_io_slow_ms` (25). `dbz3_io_readahead` (ON,
  `_kb`=2048; only without mods). The `perf` line has `fg=` (focus; DWM limits a
  visible unfocused window to HALF). `logging.cpp` **prunes** the
  `dbz3_NNN.log` files (`log_max_files`=20).
- **Auto-save**: changes are persisted when marked + OnClose.

## 9. UNIVERSAL EXECUTABLE + RELEASES + GITHUB

### 9.1 A single dbz3.exe (SSSE3 baseline)
- SDK built with `-march=x86-64 -mssse3` → works on ANY x64 CPU (Core 2
  2006+). NO ISA bootstrap or variants. The remaining AVX is in 2 functions with
  dispatch by `__isa_available` (safe).
- **Dual-region** core (US+EU): `ResolveImageInfo` picks the PPCImageConfig by
  the MD5 of default.xex. Codegen: `generated/` (US) + `generated_eu/` (EU).
  ALWAYS re-apply `tools/fix_eu_bctr.py` after a re-codegen. EU config:
  `dbz3_config_eu.toml` (entries ALWAYS inside `[functions]`, before the first
  `[[switch_tables]]`; use `DBZ3_COLLECT_UNREGISTERED` / `DBZ3_DUMP_IMAGE`).
- The **PS5** build is single-region instead (US or EU, from the user's
  executable; §14).

### 9.2 Releases and GitHub state
- **v1.3.0 = Latest** (2026-09-30): Repair installation, button labels, DRED by
  default, `gamecontrollerdb.txt`, fix #13, polish/optimisation. (Later
  releases: see `CHANGELOG.md`.)
- **v1.2.9 / 1.2.8.2 / 1.2.8.1 / 1.2.8 / 1.2.7 / 1.2.6 / 1.2.5 / 1.2.4 EX /
  1.2.4 / 1.2.3 / 1.2.2 EX / 1.2.1 / 1.2.0 / 1.1.4 EX / 1.1.3 / 1.1.2 /
  1.1.1** = not Latest (content in §3.0); **v1.1.0-clasico** = fallback (avx2
  runtime); tags v1.0.0..v1.0.9 + v1.0.5-EX kept (the old binary zips do NOT
  exist). ⚠️ The **plain v1.2.2 was withdrawn** (it lacked the ISO fixes).
- **PortForge**: `defaultVersion` = 1.3.0; visible 1.3.0 / 1.2.9 / 1.2.8.2;
  the rest archived (`portforge/archive/`).
- ⚠️ **The release exe is built from `out\build\win-amd64-dual`** (dual core);
  `make_release.ps1` takes `dbz3.exe` from there + the DLLs from
  `rexglue-sdk-0.10\out\win-amd64-baseline\`.
- Packaging: `tools/make_release.ps1` (reads the version from
  `src/version.rc`, NO UPX). Verification: `tools/verify_release.ps1` (DLL
  hashes vs SDK, VERSIONINFO, stamp vs `version.rc`, vsync cvar in rexgpu,
  empty mods/, zip without assets). `make_release.ps1` assembles: dbz3.exe +
  DLLs + `mod center hd/` + `mods/` + docs. **There is no PS5 release
  artefact**: a PS5 build contains the user's recompiled game and is never
  distributed.
- **Issues (triage 2026-09-29)**: closed #7 (crash at title = HD menu, v1.2.2
  EX), #11 (dump: v1.2.8 + HUD/RGBA8 v1.2.8.1), #9 (import saves: recipe per
  folder; no converter), #12 (FPS at 4K: answered — internal scale 1x + FSR),
  #13 (extract textures to PNG: `python` = Microsoft Store alias → exit 9009;
  interpreter fix in `mod_pipeline.cpp` + **reporter follow-up**: the chosen
  folder was ignored because validation rejected absolute paths for the drive
  `:` and fell back to `mods/<mod>/textures`; fixed in `launcher_state.cpp` and
  `mod center hd/texture_b3.py`), #3 (CrossOver Mac; the splash without a red
  channel is from D3DMetal). **Open**: #8 (FPS drops: waiting for the `perf`
  log), #1 (volume spike when flying; the reporter's last reply = livestream
  with timestamps 17:37 / 2:08:46, answered accepting the clip as a repro;
  Kaioken deduction CORRECTED: Kaioken IS part of Goku's cycle, the capsule is
  a requirement for SSJ). #10/#6/#5/#4/#2 closed earlier. **Review
  2026-09-30**: no new pending replies (the last message on #11 is a success
  confirmation from the reporter).
- **DRED + gamecontrollerdb (2026-09-29, from reblue/LostOdysseyRecomp)**: DRED
  (`d3d12_dred`, ON) no longer depends on `d3d12_debug` → the *device lost*
  report names the queue/list and the allocation nodes; `gamecontrollerdb.txt`
  ships next to the exe (SDK cvar `hid_mappings_file`). See §7 and
  `docs/VIABILIDAD_UPSCALING_TEMPORAL_2026-09-29.md`. ⚠️ The DLLs were
  rebuilt: baseline `rexruntime` **10920448**, `rexgpu-xenos` **6360064**.
- **Linux CI** (`.github/workflows/linux.yml`, 2026-09-30): the version is read
  from `src/version.rc` (`DBZ3_VERSION_STR`) → the tar.gz is named
  `DBZ-Budokai-3-HD-Collection-v<ver>-linux-amd64.tar.gz` (nothing hardcoded).
  The job attaches the tar.gz to release `v<ver>` with `gh release upload
  --clobber` **only if the release already exists** (it never creates it);
  otherwise it leaves the *artifact*. `permissions: contents: write`.
  Publication order Windows→Linux: create the Windows release first, then the
  Linux CI uploads its asset.

### 9.3 🔴 `github/` FOLDER — UPLOAD REPO (manual sync)
`github/` is the versionable copy (NOT a local git repo; uploaded manually). The
SDK is NOT uploaded (`.gitignore`); runtime changes go as patches in
`github/patches/`. **Sync with `tools/sync_github.ps1`** (`-DryRun` to preview;
patches/ is manual). The `ps5/` folder is uploaded as is (no game data in it).
- **Do not upload**: `*.xex *.afs *.bin *.awo *.amb *.amo *.amg *.azt *.dds
  *.iso *.png *.bmp *.log`, nor `ps5-game/` or `out/` (PS5 staging/output).
- `generated/` and `generated_eu/`: README.md only. `mods/`: empty with
  README.md. `tools/xbcompress.exe`/`xbdecompress.exe` YES (exception
  `!tools/*.exe`).
- Manual commit + push. If the https push hangs: `git config --global
  credential.helper "!gh auth git-credential"`.
- **🔴 Pre-upload lint**: `tools/publish_check.ps1` (`-Repo github`, or an
  absolute path to any git repo) — adapted reimplementation of `um publish
  check` (universal-modder). It walks the **tracked** files and gives **FAIL**
  for verbatim game files (`.bin/.afs/.awo/.iso/.xex/...`), build artefacts
  (`.exe/.dll/.zip`) or **secrets** (API keys, `.env`), and **WARN** for
  decompiler fingerprints (`FUN_xxxx`/`sub_XXXX`), absolute personal paths or a
  missing README. `sync_github.ps1` runs it at the end; exit 1 = failure.
  Adopted from Block C of `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md`.

## 10. MODEL PORT — PIPELINE

- **Native HD→HD swap** (✅ **main delivery**, validated 2026-09-10 with Cell
  Form 2 (147) → Krillin's slot (327), 100 % functional incl. mouth):
  `python "mod center hd\swap_b3.py" --origen 147 --dest 327 --mod cell_native`
  (`--list` lists the catalogue). `bin == AFS entry index`; catalogue
  `mod center hd/catalog_b3.cat`. LZX /N:2048 + per-entry override. **Rule**:
  if the character exists in HD → native swap; the PS2→HD port only helps for
  models that are NOT in HD.
- **PS2→HD injection (Path A)**: `port_ps2_b3_inject.py <template>
  <geometry.json> <threshold> <output> [--npm] [--bone-aware]`
  (world-matching + bone-local conversion + normals `[nz,-ny,nx]`; best binary
  threshold 0.8). `port_ps2_b3_extract.py` reads the PARENT of the PS2 axis
  (`+0x40`, rel AMG; `axes_rel=0x20`) and transforms the "L00" parts
  (hands/face) from local to model space. The inject's `axes_base` uses
  AWG+0x14 (not hardcoded).
- **🔴 STRUCTURAL LIMIT (Cell F2)**: the HD bin has **17 AWGs**: AWG0 (48
  bones, 2661 verts, body) + **16 single-bone AWGs = bones 48-63** (**10 hands +
  6 face**). The PS2 has only **48 bones (0-47)** → the 16 extra AWGs have NO
  PS2 equivalent and stay HD. Injection only touches the AWG0 `sec34`.
- **✅ PHASE 1 DONE**: `port_ps2_b3_inject_aux.py` extends Path A to the 16
  auxiliary AWGs (10 hands `world[23]/[30]`; 6 face `world[32]`) with the 6
  layout families of `PLAN_PS2_B3/04_FORMATO_RE.md` (3079/3085 verts). Mods:
  `cell_best2` (16 AWGs), `cell_face_only` (6 face). Flags
  `--only all|face|hands`, `--face-thr`, `--hand-thr`.
- **Full port (Path B)**: pipeline `port_b3_windows.py` → `port_b3_strip.py`;
  geometry + draw correct, blocker = bind/skin (§3.4). Test mods: `_strip3`
  (best), `_grow327`, `_hdskin_strip` (worst) — **ONE active** (slot 327).
  `cell_native` (327) = native swap (renders, it is NOT the port). Old pipeline
  `port_ps2_b3_geometry/draw/pack` (A/B descriptors) SUPERSEDED.
  **RESUME + commands**: `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` §0.
- **OBJ exporters** (feedback without opening the game):
  `awo_tools/awg_to_obj_b3.py` (full bins), `awg0_export.py` (AWG0 with A/C
  auto-detection), `awg_cara_export.py`. Check bounds/NaN.
- **🔧 Path A NORMAL FIX (2026-10-03)**: `awo_tools/awg_normal_fix.py`
  (`<port.bin> <native.bin> <out.bin>`) copies the `nrm` field of ALL AWGs from
  the native HD into the port's bin (keeps the port's `pos`/`uv`/`IB`). Removes
  the grey faceted shading of the arm/head (§23). Test mod `cell_nfix` (slot
  327). Comparator: `awo_tools/awg_diff.py` (field-by-field diff of two bins).
- `awo_tools/analyze_bin_hd.py` is **OUTDATED** (PS3 layout) — do not use it.

## 11. HISTORY

- `docs/01_estructura/HISTORICO_AGENTS.md` — verbatim history up to 2026-09-02
  (items 8-65, Janemba §11.1, injection §65.1.x, head swaps, releases
  1.0.x-1.1.1, disk cleanup §14.24).
- `docs/01_estructura/HISTORICO_RELEASES.md` — verbatim detail of: §A
  narrative of releases 1.1.3→1.2.9 and runtime; §B PS2→B3 port research
  (Phases B/C, GPU, attempts T2-T11); §C full launcher.
- Other references: `awo_tools/CONSOLIDADO.md`, `awo_tools/RE_PROGRESO.md`,
  `docs/07_ports/`, `docs/PLAN_1.1.1.md`, `docs/PLAN_LINUX.md`.

## 12. CURRENT ROADMAP

See **`docs/HOJA_DE_RUTA_2026_09.md`** — 3 phases:
1. **Light documentation** (compaction 2026-09-26: AGENTS ≤ 60 KB; detail to
   HISTORICO_RELEASES.md).
2. **Dead-code cleanup** (`dbz3_enabled_mods`, `PrepareRegionData` stub,
   `analyze_bin_hd.py`, legacy artefacts) + pending debugging.
3. **Content RE through duplicates** (abilities, slots, stages): audit the bins
   of `data_cmn.afs`, locate stages/movesets, map SLXS/roster + select, and
   duplicate+modify entries.

> **⚠️ Current guide for native slots and port**: `docs/DICTAMEN_GPT6_ASTRA.md`
> (plan 0-7 + 3 corrections: `0xFFFF`=empty cell, not a free character; bone
> `+28` only sec34, format C uses `+40`; mid-insert does not add AFS indices).
> Native slot paths: (1) reserved cell → (2) guest-memory data patch →
> (3) hybrid tables+hooks; **no re-codegen first**. Port: Path A (injection) =
> delivery, Path B = bounded research.

## 13. OPERATING NOTES

- **Issue replies = PARTIAL "AI" (declared in #1, 2026-09-29)**: the
  maintainer is an advanced user (not an expert) and uses AI to
  analyse/accelerate; the decisions and tests are theirs. Be explicit if asked;
  do not hide it.
- The reference data that lived in `%TEMP%\opencode\` (b327_*.bin, cell_*.bin,
  etc.) **NO longer exist** (cleanup 2026-09-02): regenerate from `us/` +
  `ps2_games/` with the `awo_tools/` tools.
- **Cleanup 2026-09-09 (~46 GB → ~28.4 GB)**: deleted
  `out/analysis/corpus/.work/` (regenerable with `corpus_scan.py`),
  `rexglue-sdk/` (0.9) and `rexglue_0.9/`, `out/build/_archivo_builds/` +
  `_archivo_dlls/`, duplicate docs in `modding resources discord/tutorials/`.
  Detail: `docs/06_limpieza/INVENTARIO_FISICO_2026-09.md`.
- **Cleanup 2026-09-14 (~10.6 GB; 29.4 → 18.8 GB)**: deleted
  `out/build/_archivo_mods/`, `out/build/win-amd64-release/mods_archivo/` (83
  tests), `github/release-stage/` + `release-stage/`, `rexglue_backup/`, the
  avx2 SDK build `out/build-win-vulkan/` (`out/win-amd64/` with the avx2 DLLs is
  kept), the B1/B2/B2V/Shin Budokai PSP AFS **and their ISOs** (**B3 Greatest
  Hits** and **Infinite World** are kept), and dedup of `modding resources
  update*`. `mods/og_music` **is kept**. Sweep of `__pycache__`/`*.pyc`/
  `.tmp`/`.bak`. **Pending decision**: `modding resources` (2.2 GB) and
  `modding resources discord` (0.86 GB).
- `out/build/win-amd64-tracy` (profiling) was deleted: regenerate it with the
  CMake Tracy preset if needed.
- The maintainer speaks Spanish; the documentation is in English
  (2026-10-06). Long play sessions.

## 14. PS5 BUILD (experimental, 2026-10-06)

> User guide: `docs/PS5.md`. Architecture and patch layers: `ps5/README.md`.
> Licence: everything in `ps5/` is **GPL-3.0-or-later** (adapted from
> [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp), and
> the title links the GPL-3 PS5 Vulkan driver); the rest of the repo stays MIT.

- **What it is**: `ps5/make_ps5.sh` (Arch Linux, root; on Windows Arch under
  WSL2) turns the user's own copy (ISO or folder, US or EU) into a homebrew
  title for a **jailbroken PS5**, in 9 resumable steps: host packages → PS5
  toolchain + RADV driver ([mihawk-99/PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan),
  `/root/ps5vk`) → SDK v0.10.0 checkout in `/root/dbz3/rexglue-sdk` + DBZ3
  overlay + PS5 patches → host recompiler → `stage_game.py` + codegen →
  runtime for PS5 → tile/backgrounds → `build_game.sh` (title in
  `out/ps5-title/<TITLEID>`) → FTP upload (only with `--console`). Logs in
  `/root/dbz3/logs/<step>.log`. Options: `--iso`, `--game-dir`, `--console`,
  `--ftp-port` (2121), `--title-id` (`PPSA99300`), `--tile`, `--theme`,
  `--art-dir`, `--with-mods`, `--test-build`, `--jobs`.
- **Three SDK patch layers, in order**: (1) `patches/rexglue-sdk/` overlay
  (DBZ3's runtime, same as Windows/Linux); (2)
  `ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch` = mcla-recomp's
  `rexglue-v0.10.0-mcla.patch` **rebased onto layer 1** (two conflicts merged
  by hand: `graphics_system.cpp` keeps DBZ3's 60 Hz vblank clamp + adds
  mcla's backwards-tick resync; `vulkan_presenter.cpp` keeps DBZ3's
  `frame_cap` pacing + the PS5 paint logging) plus two DBZ3 additions:
  `GetExecutablePath()` honours `REX_EXECUTABLE_PATH` on PS5
  (`filesystem_posix.cpp`), and `thirdparty/crypto/sha256.cpp` gets a
  `__PROSPERO__` byte-order branch; (3) `ps5/patches/rexglue-ffmpeg-ps5-config.patch`
  (unchanged from mcla-recomp).
- **🔴 Invariant**: **any change to `patches/rexglue-sdk/` must keep layer 2
  applying.** Check with `git apply --check` on a clean v0.10.0 checkout with
  layer 1 copied in; if it fails, regenerate it (apply mcla's patch with
  `git apply --3way`, resolve, `git diff` against the layer-1 commit).
- **Host** (`ps5/main_ps5.cpp`): no ImGui launcher, no in-game ImGui menu.
  Sets `REX_EXECUTABLE_PATH=/data/dbz3/dbz3`, so everything DBZ3 keeps "next to
  the exe" lives in `/data/dbz3` (`dbz3_user.toml`, `mods/`, `mods_nativos/`,
  `user_data/`, log `dbz3-play.log`). Loads settings
  (`settings::LoadUserSettings` / `ApplyUserSettingsToSdk`), then forces
  `gpu_backend=vulkan`, `video_driver=offscreen`, `hid_mappings_file=""` and
  the shared-memory tuning cvars; creates the runtime with `Ps5AudioSystem`
  (sceAudioOut, stereo) and `Ps5PadInputDriver` (DualSense as an Xbox 360
  pad); order: Setup → `RelocateGameData` → `LoadXexImage` → `InitHeap` →
  `ApplyRuntimeSettingsToSdk` → (US only) `roster::GuardGeneratedMod` /
  `ApplyAtLaunch` → launch; relaunches the module on guest thread exit (max 8).
- **Region**: single-region. US = `generated/` + `hooks`/`roster_trace`/
  `roster_ext`/`select_ext`; EU = `generated_eu/` + `-DDBZ3_EU_VARIANT`
  (after `fix_eu_bctr.py`, as on PC). `stage_game.py` classifies the xex by
  SHA-256/MD5 (same values as `baserom.md` and the launcher).
- **Console layout**: title `/data/homebrew/<TITLEID>`; game data
  `/data/dbz3/game` (`default.xex`, `us/`/`eu/`); settings
  `/data/dbz3/dbz3_user.toml`; mods `/data/dbz3/mods/`; saves + shader cache
  `/data/dbz3/user_data/dbz3/`.
- **Left out on PS5**: launcher, Model Swap/mod tools (Python + XDK), D3D12-only
  features (HD texture upscale, texture dump, DLSS/FSR 3, FidelityFX). Texture
  packs and ready-made mods work.
- **Status**: the merged SDK patch applies cleanly; `rexruntime` +
  `rexgpu-xenos` and the DBZ3 host sources + `main_ps5.cpp` (US and EU) compile
  for the PS5 target with clang 21 (clang 18 fails on a va_list in
  `xma_decoder.cpp`). **Not yet run on a console** and no full game build in CI
  (needs the user's xex). First boots will likely need missing indirect-call
  targets in `dbz3_config*.toml`, as on PC.
- **Never commit or share** `ps5-game/`, `generated*/`, `out/`, `*.xex` or
  anything built from them.
