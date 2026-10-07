# HISTORICO_AGENTS — Verbatim history of the original AGENTS.md (2026-09-02)

> Historical file generated on 2026-09-02: a COMPLETE, verbatim copy of the
> previous AGENTS.md (236 KB) BEFORE it was compacted to ~60 KB. It holds the
> detailed account of every session (items 8-65, port experiments,
> launcher fixes, releases 1.0.x-1.1.1, disk cleanup).
> Do NOT load by default: read it only when you need the detail of a specific
> session. The operational reference is the current AGENTS.md.
> For releases 1.1.3→1.2.9, the PS2→B3 port research and the launcher detail,
> see `01_estructura/HISTORICO_RELEASES.md` (2026-09-26 compaction).
>
> **Translation note (2026-10-06):** originally written in Spanish and
> translated to English. Personal absolute paths were generalized. Many
> statements here were later corrected (vertex layout, AFS table offset,
> skinning location); the current facts are in `AGENTS.md`. The experimental
> **PS5 build** (2026-10-06) is documented in `docs/PS5.md` and `AGENTS.md` §14.

---
# DBZ Budokai 3 HD Collection — Project context

> Context document for agents/AI. It consolidates the project's status,
> the decisions made and the work done, so no information is lost
> between sessions.

---

## 0. ✅ MIGRATION TO REXGLUE 0.10.0 — COMPLETED (2026-08-25)

**Read `docs/MIGRACION_REXGLUE_010.md` BEFORE touching the SDK.** It documents the
0.9.0 → 0.10.0 migration (already validated in game).

- **Done**: SDK 0.10.0 cloned into `rexglue-sdk-0.10/` (tag v0.10.0) + submodules;
  build configured (D3D12+Vulkan+FFX, clang 22, x86-64-v3); 2 build bugs
  solved (libmspack wrappers, ffx_api_dll.rc UTF-16); **runtime patch
  ported to 0.10** (afs.h/afs.cpp recreated because 0.10 removed them + host_path_*
  refactored + 3 dbz1 cvars restored); **rexruntime.dll 0.10.0 built
  (10933248 B) with the patch markers**.
- **2026-08-25**: **rexgpu-xenos.dll 0.10.0 built (6207488 B)** + complete
  SDK; **SDK 0.10 installed in `rexglue/`** (0.9 backup → `rexglue_0.9/`,
  PACKAGE_VERSION 0.10.0 verified); **dbz3.exe built against 0.10**
  (17298432 B, Release) with the generated code **regenerated with the 0.10 codegen**
  (`dbz3_codegen`, 44 recomp files; 0.9 used `REX_WEAK_FUNC`, removed in
  0.10); the SDK fixes (CallInUIThreadSynchronous timeout + presenter
  pacing) **are already native in 0.10**; `github/patches/` updated to 0.10
  (9 files + README).
- **✅ VALIDATED IN GAME (2026-08-25, user)**: the mods `swap_96_on_327`
  (Babidi→Krillin, simple override) and `tex_91` (Gero, textures) work, and the
  **virtual mid-insert** works (mod `sw_vegeta424`, armored Vegeta, bin
  126976 > to_read 106496 of slot 327). **0.10.0 migration COMPLETE.**
- **SDK status**: `rexglue/` = 0.10 (active). `rexglue_0.9/` = backup
  (keep just in case, no longer the default). `rexglue-sdk/` = 0.9 source
  (historical, do not touch). (Both 0.9 copies were deleted in the 2026-09-09 cleanup.)
- **⚠️ Building the game**: the `win-amd64-release` preset resolves `clang` to the
  retcomm toolchain (MinGW, does NOT compile `rex/chrono/chrono.h`) — ALWAYS pass
  `-DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe"` and
  `-DCMAKE_PREFIX_PATH=.../rexglue` (see MIGRACION §7.3).
- **⚠️ PENDING (once the general plan is complete)**: update
  release/README + README for SDK 0.10 before uploading to GitHub (the
  `github/` repo is not uploaded yet; patches and docs are already updated locally).

---

## 1. WHAT THIS IS

PC recompiled port of **DBZ Budokai 3 HD Collection (Xbox 360)** using the
**ReXGlue SDK** (derived from Xenia). The project includes the custom launcher
(`src/launcher/`), the region/mod logic, and the runtime (rexglue-sdk).

- **dbz3** (this project): Budokai 3 HD Collection
- **dbz1**: the sibling project *DBZ Budokai HD Collection* (on the
  maintainer's machine; already has the input fixes applied)

## 2. KEY LOCATIONS

| Path | Content |
|------|-----------|
| `src/` | Launcher and game code (main.cpp, launcher/, ingame/) |
| `rexglue-sdk/` | SDK source (runtime, GPU, filesystem) — buildable |
| `rexglue-sdk/out/build-win-vulkan/` | SDK build (D3D12+Vulkan+FFX, clang) |
| `out/build/win-amd64-release/` | **Game build** (dbz3.exe, DLLs, mods/) |
| `out/build/win-amd64-tracy/` | Tracy-instrumented build (profiling) |
| `eu/`, `us/` | Region assets (game AFS) |
| `ps2_games/` | AFS of B1, B2, B2V, B3 GH, IW (PS2 references) |
| `mod center/` | Modding tools (36 programs) |
| `modding resources/` | Documentation + resources (models, lists, art) |
| `modding resources update/` | Drop box for new files from the user |
| `generated/` | Recompiled guest code (dbz3_recomp.*.cpp) |
| `docs/` | **Organized documentation (read FIRST)** — indexes in docs/README.md |

## 2.1 DOCUMENTATION (docs/ — PRIORITY READING)

The project is documented in `docs/`. **READ `docs/README.md` first** and then:

- `docs/01_estructura/ARBOL.md` — what each folder is
- `docs/01_estructura/ESTADO.md` — what works / what fails (current status)
- `docs/02_mods/COMO_HACER_MODS.md` — mod pipeline (per-entry override)
- `docs/02_mods/MODEL_SWAP.md` — model swap research
- `docs/02_mods/TEXTURAS_MOD.md` — the launcher's Textures tab (how it works)
- `docs/03_formatos/AMO_AWO.md` + `BIN_LAYOUT.md` — bin format
- `docs/04_herramientas/TOOLS.md` — tool inventory
- `docs/05_build/COMO_COMPILAR.md` — building the game/SDK
- `docs/06_limpieza/PLAN_LIMPIEZA.md` — pending cleanup plan
- **MODEL PORT → read AGENTS §3.4 (consolidated status) BEFORE anything else**

## 3. CURRENT STATUS (EXECUTIVE SUMMARY)

- **D3D12 = main backend** (prebuilt 2.7 MB, smooth in 3D)
- **Vulkan = experimental** (flagged in the launcher; slow 3D because of the
  Vulkan render path — 6.5x slower than D3D12 in IssueSwap)
- **Controller**: `input_backend = "xinput"` (avoids a hang with RTSS/OBS)
- **Config**: D3D12 + 2x + frame_cap 60 + region us + mod sw_goten_nativo (native swap validated)

### 3.1 CURRENT STATUS (2026-08-17) — VALIDATED WAY FOR SWAPS

- **✅ NATIVE B3→B3 SWAP = WORKS** (mod `sw_goten_nativo`): replacement of the
  character's COMPLETE #AMB bin (AWO+AZT) in the AFS. Validated in game by the
  user (excellent quality, 100 % rig, voice/blinking OK).
- **The correct AFS method is MID-INSERT** (the bin grows in its slot, later
  entries shifted by +delta, delta rounded to 0x800). **--append mode
  is DISCARDED**: it breaks the AFS table order (entry 327 points to the end
  but 328+ go back to the middle) and the guest uses BINARY SEARCH over the table →
  returns wrong entries → host crash (0xC0000005) or hang.
- **CRITICAL CONSTRAINT**: the guest reads entry 327 (Krillin) with a FIXED
  `to_read` = 106496 bytes (the original slot). The mod's compressed bin MUST fit
  in the slot (Goten = 107006 tolerated; B1 port = 271668 → truncated → hang).
- **The B1 HD→B3 HD port requires the bin to fit in 106496 compressed bytes**:
  the B1 AWO (685856 B) is 2.4x larger than the B3 one (290784 B) → the B1
  geometry must be DECIMATED to ~290 KB or the truncated LZX hangs.
- **Janemba (IW→B3) = DOCUMENTED FAILURE**: see §11.1. Removed and archived.
  The geometry ended up corrupt (deformed mass) and caused crashes. Do NOT retry
  until a complete, validated format converter exists.
- **HD MATRICES == PS2 (47/47, verified zone by zone)**: the skeletons are
  the SAME → both models are in the same world space. Matching
  by world coords (v6) gives the SAME result as by locals (v5) because the
  per-bone transform is almost rigid. The problem is not the matching
  but the COVERAGE (660 slots without PS2 + 877 with a bad match).
- **v7 with threshold = THE METHOD**: rewrite only slots with a world match ≤0.3
  (197 of 1296) and leave the rest original HD → removes the deformation.
  Installed as `krillin_ps2` (v6_u03). See SESION_2026-08-17.md §4.
- **IN-GAME FEEDBACK (v7)**: body fine; ear/head/mouth/right shoulder/
  belt fail (HD+PS2 mix) and right knee/left foot (they live in vb2, not
  touchable). v7 is the MAXIMUM of slot injection. See §65.1c.
- **THE REAL WAY = FULL RECONSTRUCTION** (inspired by the B1 docs): sec34 +
  IB + arms + **submesh data zone** regenerated from PS2. The submesh zone
  EXISTS in B3 (labels + `max N m`, 0x2D61-0x3471 AWG0) and its
  layout IS ALREADY MAPPED (see `awo_tools/SUBMESH_DATA_B3.md`): 0x60
  descriptors, contiguous range A at +50/+54, range B at +58/+5C (in B1 it was at
  +60/+64/+68/+6C). See SESION_2026-08-17.md §6.
- **VB2 = FACE/LEGS BLOCKER** (verified): vb2 (226 slots)
  covers 15.4 % of the IB (789/5140 indices = head/faces). Its own layout
  `[x, y, z=1.0, 0, 0, ?, ?, nan@+28, nx, ny, nz]`, positions 0..2 (not
  world). Injection only touches sec34 → it CANNOT fix head/knee/
  foot. Full reconstruction must include vb2 + arms + submesh.
- **REAL NEXT STEP** (optimal way): 1) native swap (done), 2) map
  B3 arms + vb2, 3) adapt B1's amo0_to_awo.py to B3, 4) first real
  port = Pikkon/Pan from IW, 5) automate. See docs/VIABILIDAD_MODELOS_EXTERNOS.md §9.
- **⚠️ TEST CASE DISCARDED (2026-08-17)**: IW Pikkon has a PKH skeleton
  different from KLL (58 bones with a SKIRT, different order) → NOT 1:1.
  Complex pose retargeting is where Janemba failed. For the
  reconstruction a character whose skeleton is 1:1 with a B3 HD one is needed
  (e.g. an alternate costume of an existing character). See §65.1c/§2.7.

### 3.2 🔴🔴 REAL B3 VERTEX LAYOUT (2026-08-17, VERIFIED EMPIRICALLY)

**REAL layout of the B3 sec34 vertex** (stride 44, +2 alignment, verified
by reading the real bin b327_hd.bin + goten_298.bin):

```
+0   0xFFFFFFFF (nan marker)
+4   u (float, 0.1-1.0)
+8   v (float)
+12  z_local (float)
+16  x_local (float)
+20  y_local (float)
+24  weight (float, 0.1-1.0)
+28  BONE (u32, 0-35)
+32  nrm.z (float)
+36  nrm.y negated (float)
+40  nrm.x (float)
```

**Checks** (b327_hd.bin): 36 unique bones 0-35 at +28, normals with
|mag|≈1 in 1000/1000 at +32/+36/+40, weight 0.1-1.0 at +24, `0xFFFFFFFF` at +0.

⚠️ **The (old) item 44 was right and the correction in §11.1 was WRONG**:
the bone is at **+28**, NOT at +0x10. Tools that wrote at +4/+16
(the u/pos zone) produced Janemba's deformed mass.

**Implication**: `mezclar_ps2_hd_v5.py` uses this correct layout. The HD
vertex's bone index is the AWO ZONE index (= the direct PS2 bone, see §3.3).

> (Later: superseded by the window layout `pos@0, w@12, bone@16, nrm@20,
> FFFFFFFF@32, uv@36`; see `AGENTS.md` §3.4.10.)

### 3.3 B3 / B1 BONE MAPPING (2026-08-17)

**B3 Krillin (51 bones, index = label)**:
```
0=XKLL_BODY 1=KLL_WAIST 2=KLL_STMC 3=KLL_OBI 4-7=KLL_ROBI1-4 8-11=KLL_LOBI1-4
12=KLL_CHEST 13=KLL_LCHN 14=KLL_LARMROT 15=KLL_LARM1 16=KLL_LARM2
17=KLL_LHANDROT 18=KLL_L00_LHAND 19=XKLL_NLA 20=KLL_RCHN 21=KLL_RARMROT
22=KLL_RARM1 23=KLL_RARM2 24=KLL_RHANDROT 25=KLL_L00_RHAND 26=XKLL_NRA
27=KLL_NECK 28=KLL_HEAD 29-37=XKLL_M_* (face) 38=KLL_LLEGROT 39=KLL_LLEG1
40=KLL_LLEG2 41=KLL_LFOOT1 42=KLL_LFOOT2 43=XKLL_NLF 44=KLL_RLEGROT
45=KLL_RLEG1 46=KLL_RLEG2 47=KLL_RFOOT1 48=KLL_RFOOT2 49=XKLL_NRF 50=XKLL_NW
```
sec34 uses bones 0-35 (36 bones, no legs/face → those go to vb2).

**B1 Krillin (52 bones, DIFFERENT ORDER from B3)**: same labels but OBI/ROBI/
LOBI moved to the end (29-37) and CHEST=3. The B1→B3 mapping must be BY LABEL
(not by index). Tool: `analyze_awo_b1.py` (B1 AWO structure).

### 3.4 🔴 MODEL PORT PS2→B3 HD — CONSOLIDATED STATUS (read BEFORE touching the port)

> **SINGLE reference for the model port.** The detailed historical info lives in
> §8, §11, §12, §13, §15, §65 and `docs/07_ports/`. This section consolidates the
> REAL STATUS and the PLAN to move forward without repeating mistakes (including
> the test contamination of 2026-08-26).

#### 3.4.1 CURRENT STATUS (2026-08-26, verified in game)

| Way | Status | Best result | Notes |
|---|---|---|---|
| Native B3→B3 swap | ✅ WORKS | sw_goten_nativo, sw_vegeta424 | complete #AMB bin in someone else's slot |
| Injection (template + PS2 positions) | ✅ WORKS (recognizable) | **cell_npm4** (binary threshold 0.8) | PS2 body + HD limbs/head |
| Full port (PS2 topology) | ❌ NO (amorphous) | — | the reordered pool breaks the structure |
| HD→HD head swap | ◑ partial | goku_armadura v3 | z-fighting, paused by decision |

#### 3.4.2 VALIDATED FACTS (how the guest renders)

1. **It draws via the A/B descriptors + IB**: encoding `A<<8|B<<8` (flag 0x01 at +0x5C);
   the IB indices of range B ALWAYS fall in range A. Verified 22/22.
2. **It uses the vertex's bone (+28) for the transform** (`bone0` test: bones→0
   collapses EVERYTHING to the feet; the upper face and one hand survive because they live in vb2).
3. **IT IS TIED to the pool order** (REAL `reverse` test: reversed pool →
   deformities). The mesh-refs/zones reference the pool by its original index.
4. **sec34 layout** (stride 44, align +2): `[FFFF, u, v, z, x, y, weight, BONE@+28,
   nz, -ny, nx]`. The template uses ONLY bones 0-33 in sec34 (34-47 go to
   vb2/other AWGs).
5. **Cell F2's vb2 layout** (layout B, 276 slots): `[1.0, 0, 0, ?, ?, ?,
   nan@+20, U@+24, V@+28, nrm@+32]` — NOT Krillin's "static absolute" one.
6. **Mesh group structure** (AWG0 +0x640): mesh-ref blocks (0x50:
   X=descriptor index, Y=primary bone), axes (80 B: +0x34 arm_ptr, +0x38
   child, +0x3C sibling, +0x40 parent), zone matrix (0x28E0: diagonal of
   bones + pointers to bboxes), bboxes (AABB per zone, 0x40 each), descriptors
   (0x60, from 0x2EA9).
7. **The bin is SELF-CONTAINED** (each character with its own A/B/C format; the
   guest autodetects). The number of AWGs/bones varies per character.
8. **PS2→bone-local conversion**: `local = inv(world[bone])·model`. Verified
   (conv2 world = PS2 model point by point, nearest med 0.000).

#### 3.4.3 THE TWO WAYS (decision pending)

- **Way A — INJECTION (WORKS)**: keep the template's pool ORDER
  and rewrite +12/+16/+20 (and normals `[nz,-ny,nx]`) with the PS2 geometry
  converted to bone-local. Critical parameter: **binary threshold** (0.8 good,
  2.0 bad, blends/soft ALWAYS bad). Limitation: it is not the exact PS2
  topology (the IB/structure remain the template's).
- **Way B — FULL PORT (BLOCKED)**: reorder the pool to the PS2 topology.
  Geometry/conversion/A-B **ARE ALREADY solved** (verified); the blocker
  is that the reordered pool breaks the mesh-refs/zones → the whole draw
  structure (mesh-ref + zones + bboxes + descriptors) must be REBUILT coherently
  with the new pool.

#### 3.4.4 CHRONOLOGY OF ATTEMPTS (so as not to repeat them)

| Date | Attempt | Method | Result | Lesson |
|---|---|---|---|---|
| 14/08 | Janemba IW→B3 (v4-v10) | parse→skin→decimate→build | deformed mass | the PS2 parser did not read the real IB (FaceType) |
| 14/08 | Krillin PS2→HD (v1-v7) | slot injection | silhouette but deformed | HD is a REWORK (0 % match), not a 1:1 conversion |
| 17/08 | Native B3→B3 swap | complete bin in a slot | ✅ WORKS | the guest accepts self-contained bins |
| 17/08 | Injection v5-v7 | +12/+16/+20 with the real layout | recognizable, partly deformed | the bone is at **+28** (u32) |
| 18/08 | Self-contained bins | #AMO0→#AWO re-layout | PS2 rig solved (chunks) | the HD bin is self-contained |
| 19/08 | Vertex formats | awg0_export / awg_cara_export | different A/B/C formats | the guest autodetects each bin |
| 26/08 | NPM injection + normals + threshold | port_ps2_b3_inject.py | **cell_npm4 = BEST** | binary threshold 0.8; blends bad |
| 26/08 | Full port (conv2) | PS2 pool + IB + A/B | amorphous | wrong A descriptor + reordered pool |
| 26/08 | Reverse test (pool reversed) | reordered pool + A/B | **deforms** | **the pool order matters** |
| 26/08 | bone0 test (bones→0) | sec34 bones to 0 | collapses to the feet | **the guest uses the vertex's bone** |

#### 3.4.5 KNOWN BLOCKERS AND ERRORS

1. **mesh-refs/zones tied to the pool by index** → for a reordered pool they
   must be rebuilt (RE pending: decode the exact bone→pool link).
2. **vb2 layout B** of Cell F2: not yet emitted correctly by the port.
3. **Descriptor A**: use `[min(B), max(B)+1)`, NEVER assume the part is
   contiguous (parts share dedup'd vertices).
4. **⚠️ Test contamination**: `AfsFindModOverride` serves the FIRST active
   mod (alphabetical order). A forgotten mod invalidates tests on the same slot.
   → **ONE active mod per test** (`Get-ChildItem mods | Where {-not .disabled}`).
5. **AWG0/sec34 growth**: in excess → crash 0x856AC389 (historical §27).
   For the port use counts ≤ template or solve the growth.
6. Soft/blends (npm6/npm7) and threshold 2.0 ALWAYS make it worse vs npm4.

#### 3.4.6 NEXT STEPS (order of progress)

1. **Re-validate `cell_port_Afix_test` alone** (port with A fixed, without
   the contamination) — confirms whether the port with a correct A renders better.
2. **Decide**: rebuild the complete structure (Way B, long RE session) vs
   accept injection as the practical port (Way A).
3. If Way B: decode the mesh-ref/zones→pool link (how the structure
   references vertices by index) and write the structure regenerator.
4. For a playable state: **re-enable `cell_npm4`** (best injection).

#### 3.4.7 REFERENCES

- `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md` — mesh-refs/descriptors/arms.
- `docs/07_ports/SESION_INYECCION_2026-08-26.md` — Way A (injection).
- `docs/07_ports/SESION_PORT_RE_2026-08-26.md` — port RE + contamination.
- `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md` — roadmap.
- Historical AGENTS: §8 (converter), §11 (Janemba), §12 (self-contained),
  §13 (formats), §15 (pipeline), §65 (injection v1-v7).

## 4. WORK HISTORY

### 4.1 Runtime fixes (applied to dbz3 AND dbz1)
- Launcher hang from `SDL_INIT_GAMEPAD` with RTSS/OBS → `input_backend=xinput`
  (controller via native XInput, SDL only keyboard/mouse) + async gamepad init
- Timeout in `CallInUIThreadSynchronous` (windowed_app_context.cpp)
- Vulkan fence optimization in `CheckSubmissionFenceAndDeviceLoss`
  (wait for only 1 fence — no measurable improvement, documented)

### 4.2 Launcher
- Tabs: Video / Upscaling / Audio / Input / Mods / Model Swap / Dev
- Region selector (us/eu) + `active_region/` overlay
- Mod selector (`dbz3_enabled_mods`, `mods/<mod>/`)
- GPU backend selector (D3D12 / experimental Vulkan)
- Full-file mods (og_music) and per-AFS-entry mods
- **✅ INTERNAL B3→B3 SWAP** (2026-08-17, mimics the sibling dbz1):
  - **Model Swap** tab: B3 catalog (`mod center hd/catalog_b3.cat`,
    183 characters with bins) → select the HD source and the target slot → generates
    the native swap mod and enables it.
  - `mod center hd/swap_b3.py`: extracts the source #AMB bin from `us/data_cmn.afs`,
    compresses LZX /N:2048 and installs it as a **PER-ENTRY OVERRIDE**
    (`mods/<name>/us/data_cmn.afs/<dest>/geom.bin`, ~100 KB) + `manifest.txt`.
    The runtime (`AfsFindModOverride`) serves that file per entry → small
    mods and 2+ simultaneously active mods (each touching different entries).
    **Restriction**: the compressed bin must fit in `to_read = ceil(slot/0x1000)`
    (no mid-insert); if it exceeds it the script aborts with a warning (use another,
    bigger slot or decimate). Mods generated earlier (full AFS ~280 MB,
    mid-insert) are migrated automatically by deleting the old full AFS.
  - `mod center hd/texture_b3.py build`: same (per-entry override from the
    start). `tex_91` migrated 280 MB → 118 KB (2026-08-18).
  - **🔴 PER-ENTRY OVERRIDE = THE METHOD (2026-08-18)**: swap_b3.py and
    texture_b3.py NO longer rebuild the full AFS (~280 MB per mod). They generate
    `mods/<mod>/us/<afs>/<entry>/geom.bin` (~100 KB), which the runtime
    (`AfsFindModOverride`, rexglue-sdk/src/filesystem/afs.cpp) serves per
    entry of the original AFS. Advantages: (a) each mod weighs ~100 KB instead of
    ~280 MB; (b) **2+ model/texture mods active simultaneously** (each one
    touches different entries of the same AFS); (c) `active_region` no longer mounts
    full mod AFSs (it only links the originals from `us/` via hardlink,
    which does NOT duplicate physical space). Restriction: the compressed bin must
    fit in `to_read = ceil(slot/0x1000)*0x1000` (the guest reads a FIXED size, no
    mid-insert). Real examples: tex_91 (bin 91: slot 112458 → to_read
    114688, bin 108312 → padded), tex_ovr (bin 327: slot 105296 → to_read
    106496). Old mods with a full AFS are migrated automatically when
    regenerated (the script deletes the old AFS before creating the override
    tree).
  - **🔴 OFF-BY-ONE FIX IN THE AFS TABLE (2026-08-18)**: the scripts
    (`texture_b3.py`, `swap_b3.py`) read the AFS table at **offset 0x10**
    while the runtime (rexglue-sdk/src/filesystem/afs.cpp) reads it at
    **offset 8** (magic "AFS"(3B)+pad(1B)+count(4B)=8B, then (addr u32,
    size u32) ×8B). That 8 B shift = 1 entry made `bin N` extract
    physical entry N+1. Consequences: (a) tex_91 "bin 91" extracted the
    **alternate costume** Gero bin (runtime 92, 11 textures, 799616 B) instead of
    the base Gero (runtime 91, 10 textures, 733920 B) → a bin with a
    different structure was served in slot 91 → **crash on reaching Dr. Gero**;
    (b) the padding was computed with the wrong slot's to_read.
    **Fix**: `read_afs_index` and `build_afs` corrected to `f.seek(8)` /
    `base = 8`. Verified: script bin 91 = loc 0x122A000 (base Gero),
    bin 327 = loc 0x3AAE000 (Krillin), bin 298 = Goten. tex_91 regenerated
    from the correct bin 91 (10 textures, 733920 B, to_read 114688) with the
    user's edits restored in tex0-9 (the alternate outfit PNGs
    are compatible). `sw_goten_nativo` (full AFS) had the
    table aligned correctly at offset 8 → not affected.
  - **🔴 VIRTUAL AFS TABLE IN THE RUNTIME (2026-08-18) — override of bins > slot**:
    the per-entry override could not serve bins whose LZX exceeded the
    original slot's `to_read` (the guest allocates the buffer from the AFS
    table size → it truncated the LZX → hang). To allow bigger bins
    (e.g. Goten 107006 > Krillin slot 106496) without rebuilding the 293 MB
    AFS, a **virtual table** was added to the runtime:
    - `AfsServeVirtualHeader` (rexglue-sdk/src/filesystem/afs.cpp): builds
      the AFS header+table where each entry with an override reports the
      **real size of the override file** (instead of the slot's original size),
      keeping the addrs intact.
    - `host_path_file.cpp::ReadSync`: when reading `data_cmn.afs`, it intercepts
      reads falling in the header+table region [0, 8+count*8) and serves the
      virtual table → the guest allocates bigger buffers (the override's to_read,
      e.g. 110592) and the override serves the whole bin without truncating.
    - Build: `cmake --build rexglue-sdk/out/build-win-vulkan --target rexruntime`
      and copy `rexglue-sdk/out/win-amd64/rexruntime.dll` →
      `out/build/win-amd64-release/rexruntime.dll`.
    - **Test mod `goten_override_test`**: Goten (bin 298) → Krillin slot
      (327) by override with the whole bin (110592 B = 107006 compressed +
      padding), enabled; `sw_goten_nativo` disabled to isolate the test.
      PENDING an in-game test of whether the geometry is injected correctly.
    - **🔴🔴 NAIVE VIRTUAL AFS TABLE = WRONG, REVERTED (2026-08-18)**: inflating the
      size of the overridden entries while keeping the addrs (`AfsServeVirtualHeader`)
      breaks boot: **the guest recomputes the offsets of the later entries by
      ACCUMULATING the sizes** → high entries (3983/3986) read at the
      wrong offset → CRASH 0xC0000005 (0x7ff65aa2d1fa, same address with
      any mod) or HANG. Fully REVERTED.
    - **🔴✅ VIRTUAL MID-INSERT (2026-08-18) — swaps in any direction**:
      the right way is to present the guest with a **CONSISTENT virtual AFS table**,
      replicating exactly a rebuild with mid-insert:
      - `VirtualAfsLayout` (`AfsGetVirtualTable`): if an override exceeds the
        slot's `to_read = ceil(size/0x1000)*0x1000`, the entry **grows in place**
        to the new slot (aligned to 0x800) and **all later entries are
        shifted** by the accumulated delta (like a rebuilt AFS). The VIRTUAL
        addrs are consistent: the entry grows and the following ones move
        → the guest finds them correctly.
      - `AfsTranslateOffset`: for data reads, translates the virtual
        offset → physical (subtracts the entry's delta) and serves the override
        (whole bin) or reads the physical file at the translated offset.
      - **CORRECT growth criterion**: it only grows if the override >
        `to_read` (what the guest already allocates), NOT if it exceeds the physical slot.
        tex_91 (114688 = to_read 114688) does NOT grow; goten (110592 > 106496)
        grows +4096.
      - Verified result (script): tex_91 delta 0, goten entry 327 grows
        in place (virt=phys), 328+ shifted +4096. The guest allocates to_read
        110592 for 327 → serves Goten's whole bin (before truncated to
        106496 → crash). **Built, DLL copied (11183104 B)**.
        (Later, 2026-09-09: the virtual reads were made 100 % consistent via
        `AfsVirtualRange`; see `AGENTS.md` §6.)
  - **Mods** tab in the sibling's format: `mods/<name>/manifest.txt`
    (key=value: name/description/author/version/type/source/target),
    toggle via a `.disabled` marker, inline manifest editing in the UI
    (Title/Description/Author/Version — Title/name field added 2026-08-17).
  - **60 fps with debug**: Dev tab → "Show FPS counter" (`dbz3_show_fps`) →
    conditional in-game overlay (dbz1 `DebugOverlayDialog` style).
  - **🔴 Diagnostic .bmp files gated by Dev mode (2026-08-19)**: the
    "GPU diagnostic logging" toggle (`dbz3_diag_logging`) propagated `dbz1_diag_logging`
    to the SDK, and the runtime wrote `frontbuf_*.bmp`/`black_*.bmp` (~31.5 MB each)
    every 60 frames even with Dev mode OFF → ~840 MB piled up. Fix in
    `src/launcher/settings.cpp`: the propagation is now `DiagLogging() && DevMode()`
    (in `SetDiagLogging`, `SetDevMode` and `ApplyRuntimeSettingsToSdk`). The dumps
    are ONLY generated with Dev mode + toggle both ON. The 28 .bmp files in the
    build were cleaned up.
  - **Adapted to any monitor Hz + anti-hang** (2026-08-17):
    - `DetectRefreshRate()` (Win32 `EnumDisplaySettingsW`) detects the monitor's
      Hz and shows them in the Video tab (computed ONCE, not per frame).
    - `SafeFrameCap()` validates the cap (0=uncapped, minimum 15, max 1000).
    - **FINAL approach = replicate dbz1 (which works)**: the frame cap is NOT
      forced to 60 nor clamped to a clean divisor. The user's cap is applied
      VERBATIM (`dbz3_frame_cap`, 0=uncapped) both in the launcher and in the
      game. Forcing cap 60 in the launcher and a clean divisor (55/48...) in the
      game caused: (a) the launcher hang at >60 Hz, and (b) lag/judder in
      the game at >60 FPS.
    - **Configurable VRR** (`dbz3_vrr`, checkbox in the Video tab, DEFAULT TRUE
      like the SDK/dbz1 default): enables `d3d12_allow_variable_refresh_rate_
      and_tearing` (swapchain with ALLOW_TEARING → Present(0) does not wait for vblank →
      smooth at any Hz). With VRR OFF and no tearing, Present(0) waits for vblank
      and can lag at high refresh rates → that is why the default is TRUE.
    - **🔴 ROOT CAUSE of the launcher hang at >60 Hz (SDK presenter.cpp)**: the
      ImGuiDrawer requests CONTINUOUS repaint while a dialog (the launcher) is open.
      With a NON-zero frame_cap, the frame_cap skip limited PRESENTATION but
      repaints continued at the monitor's frequency → on a
      120/144/165 Hz panel the UI thread saturated with no time to process messages.
      The right fix was leaving the launcher's frame_cap at 0/uncapped (like
      dbz1) so there is no repaint skip, and also:
    - **Additional FIX (SDK presenter.cpp, 21:43)**: `Presenter::WaitForUITickFromUIThread`
      now paces by TIME (sleep_until at 1/frame_cap) instead of
      relying on the DXGI vblank, in case the user sets a NON-zero frame_cap in
      the launcher. New member `ui_tick_last_paint_time_`. Requires rebuilding
      rexruntime.dll and copying it to the game build (done).
- New code: `src/mods.{h,cpp}` (mod manager with manifest),
  `src/launcher/mod_pipeline.{h,cpp}` (B3 catalog + async swap).
- **Model swap with an AFS selector** (2026-08-17): `swap_b3.py` already accepted
  `--afs <path>`; now the launcher exposes a custom path field for
  `data_cmn.afs` (besides auto-detecting `us/data_cmn.afs`), in case the
  game is in another directory. `ModPipeline::SetAfsPath()` + an input in the
  Model Swap tab.
- **Music mod**: overriding `adx_jpn.afs`, `adx_usa.afs`, `opening.sfd`
  and `Ending00.sfd` ALREADY WORKS — the `og_music` mod (`mods/og_music/<region>/`)
  replaces them per region and is validated end-to-end. Just place the
  files in `mods/<mod>/us/` or `mods/<mod>/eu/`.
- **🔴 MOD SYSTEM UNIFICATION (2026-08-17 21:49)**: there were TWO conflicting
  activation systems. `PrepareRegionData`/`IsModEnabled` (settings.cpp)
  used the `dbz3_enabled_mods` cvar, while the launcher's Mods tab
  (mods.cpp) used the `.disabled` marker. If the user disabled a mod in the
  launcher (marking it `.disabled`), the cvar was not updated and `PrepareRegionData`
  KEPT mounting it → the Krillin experiment mod (`krillin_rec`) stayed
  active even though it appeared disabled → corrupt Krillin "could not be
  selected". **Fix**: `IsModEnabled` (settings.cpp) now uses ONLY the
  `.disabled` marker (like the launcher). The `dbz3_enabled_mods` cvar becomes
  dead code. The launcher's `SetModEnabled` (dbz3::SetModEnabled) is now the
  only path.
- **🔴 KRILLIN AFS RESTORED (2026-08-17 21:49)**: the
  `active_region/us/data_cmn.afs` was MODIFIED (MD5 0094BA98 vs original
  354615B5) by the Krillin PS2/rec geometry injection experiments,
  even though all mods were `.disabled`. Restored by copying the original
  `us/data_cmn.afs` (354615B5) over the active one. Verified: the 15
  files in `active_region/us/` match those in `us/`. When Play is pressed,
  `PrepareRegionData` rebuilds `active_region` from `us/` (clean) + the mods
  really enabled (none). (Later, 2026-08-20: the `active_region` overlay was
  removed; see §14.)

### 4.3 Modding (status)
- **✅ B3 HD→B3 HD TEXTURE MOD WORKS (2026-08-17)**: new
  "Textures" tab in the launcher + `mod center hd/texture_b3.py`:
  - **extract**: extracts the character's bin from data_cmn.afs, locates the
    #AZT block, and writes each texture as an **editable `.png` ONLY** into
    `mods/<mod>/textures/` (or the folder you choose with `--dir`). The original
    DDS header (128 B) of each texture is saved in `textures_meta.json`
    to rebuild the DDS at build time — **the user does NOT need the .dds**.
    Krillin (bin 327) = 13 DXT3 DDS textures (64x64 to 256x256).
  - **build**: re-encodes the edited PNGs to DXT3 (custom BC2 encoder in
    numpy, KEEPS the exact size w*h bytes), rebuilds the complete DDS
    (original header from the meta + new bitmap), replaces it in the #AZT (the bin
    does NOT change size → the AWO stays intact), recompresses LZX /N:2048, pads
    to the slot and generates the AFS mod (mid-insert). Validates the PNG path
    (fallback if the meta is old and does not store the header).
  - **#AZT format**: header (tex_am@+0x10, index_loc@+0x14), offset table
    at index_loc, each texture: idx@+0, type@+4, w@+16, h@+18, data_off@+0x14
    (offset RELATIVE to the AZT of the 128 B DDS header + DXT3 bitmap). The DXT3
    bitmap = w*h bytes (BC2, 16 B per 4x4 block, mipmaps=0).
  - **Pillow reads DXT3 DDS directly** (decodes to RGBA); my DXT3 encoder
    (dxt3 encoder in texture_b3.py) re-encodes to the exact size.
  - **Combinable with a model swap**: the texture mod is applied on the
    target slot (swap) — textures are assigned per mesh part/material, so
    a character swapped with its own bin carries its textures; editing the
    target slot's texture mod changes them.
  - The UI: select a character → "Extract textures to PNG" → "Open folder"
    → edit PNGs → "Rebuild mod with edited textures" → the mod enables itself
    and is listed in the Mods tab.
  - **Editable textures folder (2026-08-17)**: the Textures tab has
    a "Textures folder (PNG)" field that is auto-filled on extract with the
    default path (`mods/<mod>/textures`), and the user can change it to
    any folder they are editing in, with a **"Browse..."** button that opens
    the native Windows dialog (IFileOpenDialog + FOS_PICKFOLDERS, helper
    `PickFolder()` in launcher_state.cpp). The "Rebuild" button is enabled
    ONLY if the configured folder contains `textures_meta.json` (fix for the bug
    where the button stayed disabled if the mod name did not match
    the extract folder). `texture_b3.py` accepts `--dir` in extract and build.
  - **🔴 Argument escaping fix (2026-08-17)**: the error "The filename,
    directory name, or volume label syntax is incorrect" when pressing
    "Extract" was because `RunAsync` (mod_pipeline.cpp)
    concatenated the arguments WITHOUT quotes → the project paths with spaces
    ("DBZ Budokai 3 HD Collection\...") broke into tokens in cmd.exe.
    Fix: `RunAsync` now wraps any argument with spaces in quotes.
    Verified: the script works with quoted paths with spaces (exit 0).
  - **🔴🔴 DEFINITIVE ROOT CAUSE of the error (2026-08-17)**: the message "The
    filename, directory name, or volume label syntax is incorrect. [exit code 1]"
    when pressing "Extract"/"Rebuild"
    came from **MSVC's `_popen` + cmd.exe**, NOT from Python (the script did not
    even start: no `texture_b3_error.log` was generated). `_popen` passes the command
    to `cmd.exe /c`, and cmd.exe **fails to parse quotes when the command
    starts with `"`** (e.g. `"python" "script" ...`). Reproduced with a C++
    `_popen` test (exact error) vs the same command with Python's `subprocess`
    (works, exit 0). **Fix**: `RunAsync` (mod_pipeline.cpp) NO longer uses
    `_popen`; it uses **`CreateProcessW`** directly (launches python without cmd.exe,
    redirects stdout+stderr to a pipe with `CreatePipe`+`ReadFile`). Verified
    with a CreateProcess test: texture extract exit 0.
  - **Also hardened (2026-08-17)**: `texture_b3.py` uses a FIXED project
    workdir (`out/build/win-amd64-release/.tex_work`, independent of the
    environment's `TEMP`) and passes xbcompress/xbdecompress an environment with
    fixed `TEMP`/`TMP` (`_clean_env`) — extra robustness against an invalid TEMP.
    `sanitize_name()` strips invalid characters from the mod name; the launcher
    ignores `--dir` if the path contains invalid characters. `RunAsync` writes
    the exact command to `pipeline_cmd.log` and the script prints a FULL
    TRACEBACK (and dumps it to `texture_b3_error.log`).
  - **Also hardened (2026-08-17)**: `sanitize_name()` in texture_b3.py
    strips Windows-invalid characters from the mod name; the launcher
    ignores `--dir` if the configured path contains invalid characters.
    `RunAsync` writes the exact command to `pipeline_cmd.log` (diagnostics) and
    the script prints a FULL TRACEBACK on any exception.
  - **PNG only (2026-08-17)**: the extract NO longer generates `.dds` — only
    editable PNGs. The original DDS header is saved in the meta and the build
    rebuilds the complete DDS (header + bitmap) from the PNG.
  - **Texture list in the UI (2026-08-17)**: the Textures tab lists the
    PNGs extracted to the active folder (file names in a grid) to
    identify textures without opening the file explorer. The source/
    target combos show each character's bin `[bin N]` to tell apart
    variants of the same character (e.g. Dr. Gero bin 91 vs 92).
  - **Target slot selector (2026-08-17)**: the Textures tab lets you
    choose which character/slot to apply the edited textures to (besides the
    source they are extracted from). `texture_b3.py build --slot <bin>` takes the
    SOURCE bin (with its edited textures) and places it in the TARGET slot of the
    AFS → compatible with model swaps: you extract textures from A, edit them, and
    apply them to B's bin (which may come from a swap).
  - **⚠️ Bins without #AZT (2026-08-17)**: some catalog bins (e.g. Dr. Gero
    bin 92 "alternate costume", 38048 B) are NOT complete models — they have no
    #AZT block with their own textures (they reuse another bin's/variant's).
    The extract now warns with a clear message instead of a traceback with a
    Windows path error. Check with: `texture_b3.py extract --bin <n>`.
- **The runtime's mod system WORKS**: AFS rebuild + LZX `/N:2048`
  + overlay. Validated end-to-end (og_music, sw_goten_nativo).
- **✅ NATIVE B3→B3 SWAP WORKS** (sw_goten_nativo): Goten's complete #AMB bin
  (AWO+AZT) in Krillin's slot. See §3.1.
- **Janemba (IW→B3) = FAILURE, REMOVED** (see §11.1). The PS2 IW format
  (#AMO0/#AMG LE) is NOT directly compatible with HD 360 (#AWO BE);
  it requires a complete, validated format converter, which does not exist yet.
- **Verified by instrumentation**: Krillin loads bins 327-329 (HD uses
  the PS2 GH bin numbering).
- **AWO_FORMAT.md** documents the complete format (see section 5).

## 5. FILE FORMAT — SEE `AWO_FORMAT.md`

**Summary**: AFS (LZX `/N:32`-compressed bins with magic `0F F5 12 EE`;
later corrected to `/N:2048`) → big-endian #AMB → #AWO (360 model) vs
#AMO0/#AMG (PS2 LE model). HD 360 uses the bin numbering of the **PS2 Greatest
Hits data_cmn** (Krillin 327-329, verified by instrumentation). The #AWO IS the
same PS2 model **(51 bones, 18 mesh groups, 68 identical labels — there is NO
re-rigging)**, only big-endian with renamed magics (#AMO0→#AWO, #AMG→#AWG,
#AMT→#AZT) and a different mesh-group layout (offset table at 0x690 vs
sequential blocks). Conversion = endianness + renaming + re-layout.
See the full document for the field-by-field layout.

### 5.1 Findings of the deep scan (modding resources + update)
- AFL = fixed **32-byte** records (not strings), AFL index = AFS bin.
- Two numberings: data_cmn (models, GH=HD) vs region DATA_ENG (select/menus).
- **IW-exclusive characters with real bins** (verified in
  `ps2_games\Infinite World (USA)\USR\DATA_CMN.AFS`): Janemba 541-544,
  Pikkon 583-586, Pan 566-569, Super 17 606-609, Super Baby Vegeta 678-681.
- **IW→B3 moveset ports already exist** (8): Janemba→Krillin, Pikkon→Raditz,
  Pan→Nappa, Super 17→A17, Super Baby→Kid Trunks, GT Goku→Teen Gohan,
  Saiyawoman→Kid Gohan, Future Gohan (Shin Budokai).
- SDBH WM = a mine of Xenoverse models (EMD/ESK/EAN/EMB): Janemba (bcbjn),
  Pikkon (bcbjk/bcpkk), Super 17 (bcs17), Pan (bcpan), Super Baby (bcvby).
  Chibi style — to be evaluated. EMD↔FBX ecosystem available (EmdFbx/FbxEmd).
- HD texture = `#AZT ` (not #AMT). DDS_PNG.exe converts DDS↔PNG.
- `Tail AMO`: custom tail model — **do NOT merge WAIST (crash)**.

### 5.2 Binary verification (phase 3 — converter RE)
- **Krillin bin 327 is THE SAME model in PS2 GH and HD 360**: 51 bones, 18
  AMG/AWG, 68 identical bone labels (KLL_*, XKLL_*). Verified by reading
  both bins directly (`ps2_games\Budokai 3 Greatest Hits (USA)\USR\data_cmn.afs`
  uncompressed vs LZX-decompressed `us\data_cmn.afs`).
- HD layout: table of 18 AMG offsets at `+0x1C` (0x690) of the #AWO header →
  points to `#AWG` blocks (header 0x40). PS2: sequential `#AMG` blocks.
- Identical vertex formats: B5 (`01 B5` LE / `00 00 01 B5` BE), B4, 90.
- The #AWG header is longer than the #AMG one (base 0x40 vs 0x20) with more
  offset fields — mapped field by field in phase 3.
- Temporary working files in `%TEMP%\opencode\`: b327_ps2.bin (812 KB
  LE #AMO0), b327_hd.bin (682 KB decompressed BE #AWO), b327_hd.lzx.

## 6. USEFUL COMMANDS

```powershell
# Build the game (release)
cmake --build "out\build\win-amd64-release"

# Build the SDK (D3D12+Vulkan+FFX, clang, ninja)
cmake -G Ninja -S rexglue-sdk -B rexglue-sdk\out\build-win-vulkan `
  -DCMAKE_C_COMPILER="C:/Program Files/LLVM/bin/clang.exe" `
  -DCMAKE_CXX_COMPILER="C:/Program Files/LLVM/bin/clang++.exe" `
  -DCMAKE_RC_COMPILER="C:/Program Files/LLVM/bin/llvm-rc.exe" `
  -DREXGLUE_ENABLE_FIDELITYFX=ON -DREXGLUE_USE_VULKAN=ON `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-march=x86-64-v3"

# LZX compression of 360 bins (the game's format)
xbcompress /N:32 <src> <dst>   # compress (later: use /N:2048)
xbdecompress <src> <dst>       # decompress

# Extract/decompress bins from the AFS (working scripts)
#   %TEMP%\opencode\ contains b327_ps2.bin, b327_hd.bin, b327_hd.lzx
```

**XDK tools**: `mod center\Xbox 360 Compression - Decompression tool...\`

## 8. PHASE 3 (IN PROGRESS) — #AMO0 → #AWO CONVERTER

Goal: write the PS2→360 converter and add IW characters to the recomp.
**See `awo_tools/CONSOLIDADO.md` for the complete summary of everything learned.**

Validated plan (see AWO_FORMAT.md section 8 and awo_tools/RE_PROGRESO.md):

1. [x] Verify that PS2 GH and HD share the numbering (Krillin = bin 327)
2. [x] Confirm the same skeleton (51 bones / 18 AMG / 68 identical labels)
3. [x] Map #AMO0/#AMG (PS2) vs #AWO/#AWG (HD) field by field
4. [x] Deterministic AWO layout: header + relations + AMG table + labels + AWGs + axes-array (+0x34)
5. [x] Map the AWG internal structure (80 B axes, mesh groups, mesh-ref blocks, VB/IB)
6. [x] HD vertex layout (stride 0x2C, aligned +2): VT + V.z + bone-local pos + VN (Y negated)
7. [x] #AZT texture format SOLVED (A3T Analyzer, 14 Krillin textures)
8. [x] The 4 root causes of the crash fixed (mod structure, +0x34, indices, AZT texture)
9. [x] Converter v4 (build_awo_v4.py): AWO+AZT, same size, correct structure
10. [x] **SKINNING TRANSFORM (build_awo_v5.py)**: PS2 rig parsed (3056
        entries), offset→vertex mapping solved, vertices converted to the HD layout
        [nan, VT.v, VT.u, V.z, pos_local, weight, 0, VN.z, -VN.y, VN.x]
11. [ ] **Buffer re-layout**: deduplicate PS2 vertices (4331→~2189 unique),
        rebuild the IB, re-layout the 2 AWG0 buffers (+0x34 and +0x2C)
12. [ ] Validate: convert GH Krillin → load in HD and compare render/bytes
13. [ ] Apply to IW characters (Janemba 541-544, Pikkon 583-586, Pan, Super 17...)
14. [ ] Add a new character: slot + model + moveset (existing ports) + voice
15. [x] Explore the empty data_cmn bins for new character slots
16. [x] **ROOT CAUSES #5-7 solved**: compression /N:2048 (not /N:32), bin padded
        to the slot (106496), and only ONE active mod per bin (alphabetical order).
17. [x] **✅ MILESTONE: TEXTURE MOD WORKS** — Krillin shows red pixels on the
        gi with the texture mod (DXT3 DDS, RGB565 colors). Validated end-to-end:
        per-entry override + LZX /N:2048 + padding to the slot + #AZT texture.
18. [x] **✅ FINDING: GEOMETRY IS MODIFIABLE** — shifting the vertices
        of the main buffer (sec34) in X, Krillin appears deformed (very tall),
        keeping head and shoes. The runtime renders geometry changes
        without a re-layout. HD vertex layout: [nan, VT.v, VT.u, V.z, pos.x_local,
        pos.y_local, weight, 0, VN.z, -VN.y, VN.x] (stride 44, +16/+20 = local pos).
19. [ ] Complete geometry conversion (skinning) to add characters
20. [ ] Apply to IW characters (Janemba 541-544, Pikkon 583-586...)
21. [x] **FULL-FILE MODE VALIDATED**: rebuilt AFS (original bin 327,
        recomputed table) works perfectly. Allows bins > slot (per-entry
        override limited to 106496). Script: `awo_tools/build_big_amb.py`.
22. [x] **BUFFER RE-LAYOUT (structure mapped + bugs fixed)**:
        - The AMG table points to the #AWG magic (NOT +0x40) — the AWG internal
          offsets (+0x2C vb2, +0x30 ib, +0x38 restart) are relative to the magic.
        - 51 axes-zone pointers in the AWO header (+0x34,+0x54,... every +0x20).
        - **BUG #1**: `AWG = awg0_off + 0x40` (wrong position) → crash.
        - **BUG #2**: the axes-zone pointer loop swept the AMG table (0x690)
          and applied a double delta to AWG16/17 (≥ axes_base) → guest null deref.
        - **BUG #3**: duplicated AMB header in the repack.
23. [ ] **BUFFER RE-LAYOUT DISCARDED (2026-08-14)**: the runtime expects
        sec34_count/vb2_count (derived from the AWG header offsets) to be
        EXACTLY the originals. Growing sec34 by just 1957 (+1) already CRASHES
        in battle. The guest uses the counts to validate the indices drawn
        by the arms. **Buffer re-layout is incompatible with the runtime.**
        Instrumentation done (AFS327 READ): the bin is read correctly
        (130752 bytes), the crash happens while processing the model.
        **VIABLE**: keep the HD buffers at the same size + decimate the PS2 geometry
        to ≤2190 vertices + rebuild the IB (4329 PS2 indices fit in 5140 HD) +
        re-map the arms. The in-place PS2 skin (without changing size) does NOT crash.
        (Later refuted: `grow()` works once `awg+0x2C`/`awg+0x34` are updated;
        see `AGENTS.md` §3.4.9.)
24. [x] **FINDING (2026-08-14)**: the runtime is SENSITIVE to changes in sec34
        (main buffer) but TOLERANT to changes in vb2 (secondary buffer).
        - vb2 +1 vertex: ENTERS BATTLE (lag, flickering textures, right
          hand sometimes missing, but does NOT crash).
        - sec34 +1 vertex: CRASHES in battle.
        SOLVED: sec34+1 without remapping the IB ALSO crashes (in the preview,
        same parsing Addr). The sec34/vb2 counts are FIXED — the guest
        uses them to deserialize the whole structure. Buffers of an existing HD model
        CANNOT be grown. To add IW characters (all with
        3600-5000 vertices, >2x Krillin's 2190) the HD AWO must be built
        from scratch with the character's counts.
25. [x] **✅ MILESTONE (2026-08-14): JANEMBA LOADS WITHOUT A CRASH** — bin 327 with
        Janemba's geometry (decimated sec34=2386, IB=8484) LOADS without a crash.
        The runtime accepts variable counts (sec34 up to 2277 validated in bin
        329). BUT the model looks like a **deformed mass**: Krillin's mesh-ref
        blocks/arms draw Janemba's triangles with wrong IB
        ranges. Blocked on fine re-rigging (map JNB→KLL bones
        + transform positions into Krillin's local space) and the
        mesh group reconstruction (arms with new IB offsets).
        Tools: convert_personaje.py, decimar.py, build_janemba2.py.
27. [x] **✅ MILESTONE 2 (2026-08-14): JANEMBA BOOTS AND ENTERS BATTLE** —
        v6 with counts IDENTICAL to Krillin (sec34=1956, IB=5140) boots and
        enters battle. Lessons:
        - v4 (sec34=2386, IB=8484, AWG0 grows to 142320): reaches select but
          CRASHES in battle.
        - v5 (sec34=1313, IB=5100, AWG0 shrinks to 88352): does NOT boot.
        - **v6 (sec34=1956, IB=5140, AWG0 keeps its 116720 size): WORKS.**
        The guest deserializes the structure by the AWG header offsets;
        AWG0 can NOT shrink (hangs) nor grow too much (battle
        crash). Padding sec34/IB to Krillin's EXACT counts is the
        key.
        - **Re-mapping the arms (v6r) CRASHES**: changing the shadow
          offsets to new ranges [0,1275,2550,3825,5100] breaks boot
          (crash 0x7ff6180cf202 while processing the model).
        - **FINDING: the arm offsets are NOT IB ranges to
          draw**. In ORIGINAL Krillin all 5140 indices are in
          [0,3904); the shadows' [3904,4936) ranges are EMPTY. The
          IB is drawn whole; the arm offsets define other info
          (bone skinning, not which triangles to draw).
        - **v6's deformed mass comes from RE-RIGGING**: Janemba's
          vertices have per-bone local positions (y=0.358, y=-8.706,
          y=-8.374...) skinned with JANEMBA'S BONES (JNB). The guest
          interprets them with KRILLIN'S BONES (KLL) from the arm → misinterpreted
          positions → deformed mass. Fix: map JNB→KLL bones +
          transform positions into Krillin's local space.
28. [x] **COMMUNITY FINDING (2026-08-14)**: the IW→B3 PS2 models ALREADY EXIST in
        `modding resources\All Character Models from IW into AMB format\`
        (241 .amb: Janemba, Pikkon, Pan, Super 17...). Community tools
        in `mod center\` (AMO Decompiler/Compiler, B3_IW Model
        Converter, Model Rig Toolset, OBJ to AMG, EMD to AMG). Key data:
        HD Krillin has ~50 % of the PS2 geometry (3216→1713 tri, 4252→2182
        pos) → HD halves it. The blocker: Krillin's mesh-ref blocks +
        arms draw Janemba's geometry with wrong IB ranges (deformed mass).
        build_janemba3.py tries to re-map the arms
        but has a relative-offset bug in arm_ptr (the rebuilt AWG0's mesh group
        is relocated). See HALLAZGO_COMUNIDAD.md.
29. [x] **✅ INJECTION PIPELINE VALIDATED (2026-08-14, session 3)**:
        - **The Krillin bin the guest reads is AFS e326** (682528
          bytes, = `b327_hd.bin`), NOT e327 (624000). The AGENTS.md
          numbering "bins 327-329" was off by one because of the table A index.
          (Later: the off-by-one came from reading the AFS table at 0x10
          instead of 8; with the right table the visible Krillin entry is 327.)
        - **Rebuilt AFS (build_afs.py)**: VALIDATED method = e326 loc
          intact, the bin grows in place, e327+ shifted by a delta
          rounded to 0x100, empty entries (loc=0) preserved. Reproduces
          byte for byte the working `data_cmn_janemba.afs`.
        - **CORRECT vertex pipeline**: `convert_personaje.py` (PS2
          skinning→local positions) → `decimar.py` (voxel) → `build_janemba2.py`
          (pack AMB). Do NOT use absolute positions (huge values
          hang the boot).
        - **v6 = WORKS**: counts identical to Krillin (sec34=1956, IB=5140),
          AWG0 keeps its 116720 size. Enters battle. Deformed mass due to
          re-rigging (JNB vertices interpreted with KLL bones).
        - **Next step**: rig_mapeo.py — map JNB→KLL bones by labels
          and transform Janemba's local positions into Krillin's space.
30. [ ] **JNB→KLL RE-RIGGING (analyzed, final session 3)**: Janemba v6 enters
        battle but as a deformed mass. Analysis: 46/64 bones map 1:1 by
        labels; poses by index do NOT match (different order); the 80 B axis
        does NOT have the pose matrix (only identity + child/sibling/parent +
        stamp); PS2 AMG header: +0x10 bone_am, +0x14 axes, +0x18 mesh_groups,
        +0x1C labels_off. **2 paths**: (a) copy Janemba's axes into the v6 bin
        (cheap, try first — if the guest skins with the bin's axes);
        (b) full re-rigging (bind matrices of both skeletons +
        vertex transform). See CONSOLIDADO.md §13.5.15.
31. [x] **✅ KEY DISCOVERY: THE HD VERTEX CARRIES THE BONE INDEX AT +28**.
        Inspired by the B3→B1 port (INVESTIGACION_FORMATO_B1_HD.md §9 of the
        sibling project): the HD vertex layout is `[flag(nan), u, v,
        pos.z_local, pos.x_local, pos.y_local, weight, BONE_INDEX(u32),
        normal.xyz]`. **build_vertex_hd wrote f32(0.0) at +28 → all the
        vertices pointed at bone 0 → deformed mass.** Fix: write bone_idx
        as u32 at +28.
32. [x] **✅ v7: JNB→KLL RE-RIGGING BY BONE INDEX WORKS** — Janemba's body
        RECOGNIZABLE in battle (before a shapeless mass). Mapping:
        bone_jnb→label (AMG0, bone_idx*16) → label_kll (AWO+0x24, bone*2*16)
        → bone_kll. 24 direct + manual. v7 (unmapped→bone 0): WORKS
        but corrupt (fingers/faces on BODY). v8 (fingers→18/25, faces→36):
        CRASH. Status: v7 installed. Next: refine the finger/face mapping.
        Tool: rig_mapeo.py. See CONSOLIDADO.md §13.5.16.
33. [x] **✅ VALIDATION EXPERIMENT: KRILLIN B3 PS2 → B3 HD (2026-08-14)**:
        the #AMO0→#AWO converter WORKS. B3 PS2 Krillin renders in HD
        with a recognizable silhouette (not a deformed mass). Pipeline: convert_personaje
        → build_ib_from_ps2 (dedup+IB) → build_janemba2 → build_afs. v2
        (1443 verts) HANGS; v3 (1109 verts) boots and Krillin can be made out
        but corrupt. **Finding: HD uses sec34 (1956, skinned with a bone
        index) + vb2 (226, WITHOUT skinning, bone=0xFFFFFFFF, absolute
        positions) for the head/face. The HD IB references both (max
        index 2189). Our converter only fills sec34 → corrupt head.**
        Next step: fill vb2 with the head/face. New tool:
        build_ib_from_ps2.py. See CONSOLIDADO.md §13.5.17.
34. [ ] **🔴 KRILLIN'S HD MODEL DIFFERS FROM THE PS2 ONE (review 2026-08-14)**:
        the converter is NOT working (deformed mass). Finding: the original HD
        (e326) has sec34 with ONLY bones 0-35 (skinned) + vb2 (226) with
        bone=0xFFFFFFFF (no skin, absolute positions) for head/faces.
        **It does NOT use skinned bones 36-50.** PS2 skins the legs (38-48) →
        putting them in sec34 HANGS the guest (it has no such matrices). The
        converter is NOT mechanical — HD is a rework (skinned body
        0-35 + unskinned vb2 head). Valid fixes: IB (index mismatch) and UV
        (u,v order). For a working converter: map legs/head to
        bones 0-35 or vb2. Janemba v7 worked because IW uses a full rig.
        See CONSOLIDADO.md §13.5.18.
35. [x] **🔴 FUNDAMENTAL TRUTH: THE PS2 PARSER DOES NOT READ THE TRIANGLE IB**:
        the conversion pipeline was NEVER correct. extract_geometry.py
        reads UNIQUE verts per part but NOT the triangle index buffer.
        build_ib_from_ps2 generates triangles assuming 3 verts per triangle
        (wrong). The janemba_ib.bin of the "working v7" is an artifact
        ([0,256,512,...], max 65294) — NOT a real triangle list; v7 worked
        by accident (the guest drew a pseudo-random pattern that looked like a
        body). See CONSOLIDADO.md §13.5.19.
36. [x] **✅ SOLVED: PS2 IB FORMAT (MaxScript budokai_updated.ms)** —
        found in `modding resources update 2\`. The PS2 mesh part has NO
        explicit IB: they are submeshes with a 0x20 header (FaceType at +0x10,
        VertCount at +0x14) + N 48 B vertices. FaceType 1 = triangle strip
        (alternating winding), FaceType 0 = triplets. PS2 vertex: 48 B
        (pos+null+normal+null+uv+skip). Tool: `parse_ps2_mesh.py`
        (Krillin AMG0: 3990 verts, 2392 tris; total 9144 verts, 5182 tris).
        `build_hd_pipeline.py`: parse→skin→HD→decimate→IB. v7 (1018 verts,
        1700 tris) HANGS — unskinned vertices (30 %) use absolute pos + bone 0.
        Pending: map the unskinned vertices. See CONSOLIDADO.md §13.5.20 and
        `modding resources update 2\INFORME_modding_resources_update_2.md`.
37. [x] **🔴 PS2 MESH PART STRUCTURE CONFIRMED (B1 docs/mod center session)**:
        the PS2 part = 0xA0 header (MeshType[8] + Ukw3 + Ukw4 + 0x30 matrix +
        0x50 unknown) + size flag 0x600000XX at +0x90 (mesh_size = XX*16) +
        submeshes at +0xA0. **The vertex stride comes from MeshType[1]** (the part's
        first byte): 0xB5/0xB6/0xF5 = 48 B, 0xB4/0xA4 = 32 B facial,
        0x199 = 32 B without UV, 0x90 = 16 B shadows. The submesh header's
        `VertBufferLength` (byte at +0x0E * 0x10) is the buffer SIZE used to
        jump to the next submesh, NOT the stride. Verified in Krillin AMG0:
        15 B5 parts + 4 B4 parts, correct flag in all of them.
38. [x] **🔴 THE HD VB2 (SECONDARY BUFFER) USES A DIFFERENT LAYOUT (verified)**:
        vb2 = `[pos.x_abs, pos.y, pos.z, 0,0,0, weight=0, 0xFFFFFFFF, nx, ny, nz]`
        (stride 44, ABSOLUTE positions, bone=0xFFFFFFFF = no skin). sec34
        uses `[nan, u, v, z_local, x_local, y_local, weight, BONE_u32, nz, -ny, nx]`
        (skinned LOCAL positions). **HD splits the vertices into 2 buffers
        by design**: sec34 = skinned (bones 0-35), vb2 = static (head/
        faces/hands, absolute model positions). The B1 doc
        (INVESTIGACION_FORMATO_B1_HD.md §9) says B1 uses
        `[pos,w,bone,normal,FFFF,uv]` "same as B3" but that is NOT true — the
        empirically verified B3 uses the layout above. Do NOT copy the B1 layout.
        (Later: the window layout — the "B1-like" one — turned out to be the
        right reading for B3 too; see `AGENTS.md` §3.4.10.)
39. [x] **🔴 PS2→HD KRILLIN: WHAT GOES INTO EACH BUFFER (skin mapping per part)**:
        AMG0 parts 0-12 (body: torso/arms/legs) have 100 % skin →
        sec34 (with bones>35 such as legs 38-48 → HD does NOT skin them, they go to
        vb2). AMG0 parts 13-18 (0x335C0+: face XKLL_L00_FACE=36, static hands
        KLL_L00_LHAND=18) + AMG1-17 = 0 % skin → **vb2**. The AMG0 skin voffs
        cover ONLY AMG0 (max 0x26C70 < AMG1@0x527D0).
        AMG0 skin = 3056 entries, 100 % match in parts 0-12 (voffs = real
        vertex offsets rel AMG, NOT a contiguous formula — the 0x20 submesh
        headers break contiguity).
40. [ ] **PENDING: TRANSFORM OF STATIC PS2 PARTS → HD ABSOLUTE**:
        the static PS2 parts (hands part13 bone=18, face part18 bone=36)
        have positions in BONE-LOCAL SPACE (mags 0.27-1.35), but the
        HD vb2 expects ABSOLUTE model positions (PS2 body mags
        ~5, HD ~1). Requires transforming the local coords by the bone's pose
        matrix (same re-rigging problem as Janemba). The AMG's 80 B axis
        does NOT have the matrix (only identity+hierarchy+stamp). Tried
        alternative: sec34 + the bone's index (but HD does not skin bones 36-50).
41. [ ] **PENDING: VB2 DECIMATION**: with the sec34/vb2 split, the PS2 vb2
        (parts 13-18 + AMG1-17) ends up at ~3000-7000 verts vs HD's 226. The
        runtime tolerates vb2 +1 (item 24) but not thousands. Decimate vb2 hard
        (voxel) and/or use full-file mode (item 21, build_big_amb.py).
        v12 status: sec34=265 (padded to 1956) + vb2=3116 (truncated to 226,
        loses the head) + AWG0 shrinks -0x30 → likely hang.
42. [x] **COMMUNITY TOOLS REVIEWED (mod center)**:
        - `B3_IW Model Converter/amb_model.py` = ONLY packs/unpacks AMB
          (not a geometry converter). `Files/functions.py` reads #AMB: +0x20 table
          loc+size, AMO at +0x20.
        - `Model-Rig Extractor.py` (Model Rig Toolset V0.6) = documents the PS2
          rig: AMG +0x10 bone_am, +0x14 axes_loc; 80 B axes with +0x34 arm ptr;
          arm +8 rig_ptr; rig +12 chunk_amnt; 32 B chunks [weight, vvn_am, vvn_loc,
          v_am, v_loc]; 32 B vvn entries (coords + voff at +12), 16 B v entries.
          **The rig voffs = ABSOLUTE vertex offsets** (compared
          against mp_points). Confirms our SkinData.
        - `B3-IW AMO Converter + Shadows` = B3/IW→B1 converter (exe, @Scoops999).
        - `Model-Rig Remover.py`, `Bone Addition Tool`, `AMBStudio`, `AMO
          Decompiler/Compiler` = community rig/AMB editors.
43. [x] **B1 INSTRUCTIONAL DOCS REVIEWED (dbz1, sibling)**:
        - `docs/INVESTIGACION_FORMATO_B1_HD.md`: B1 uses separate bins per type
          (#ACM rig + #AWO + #AZT, no #AMB). B1 vertex layout ≠ B3 (see item
          38). **§10.8/10.9**: B3 mesh parts (AWG version 4, fixed 0x50)
          are NOT compatible with B1 (version 2, variable size) and the BONE
          ORDER differs between games → skinning glitches. Proposed fix:
          reorder bones by label + re-map the vertices' bone indices
          (exactly our JNB→KLL rig_mapeo).
        - `docs/TUTORIALES_MODDING.md`: OBJ editing pipeline (Nelson's AMG to OBJ V2
          + Blender), AZT/A3T textures (Paint.NET + NVIDIA DDS plugin,
          BC2/DXT3), X360 LZX compression, SLXS (MDB 0x60/CDB 0x174) for adding
          characters, SLXS IDs.
44. [x] **🔴🔴 MILESTONES OF THE PS2→HD SESSION (2026-08-14, deep analysis)**:
        - **The visible Krillin bin in the game is e326** of data_cmn.afs
          (682528 bytes uncompressed, = `b327_hd.bin`, md5 b04b0741c4, n_sec=1956,
          n_vb2=226, n_ib=5140). e327 (624000, 1791/208/5004) is ANOTHER Krillin
          bin (another costume/select). The runtime logging (host_path_file.cpp
          `entry_index == 327`) points to a bin other than the visible one.
        - **The earlier working AFS files (`data_cmn_original_rebuilt.afs`, md5
          f7e53b99) are NOT the game's real AFS** (md5 354615b5). Rebuild
          from the REAL AFS in `us\data_cmn.afs`.
        - **Layouts of the 2 buffers of the real bin e326 (b327_hd.bin)**:
          sec34 = `[nan, u, v, z_local, x_local, y_local, weight, BONE@+28, nz,
          -ny, nx]` (stride 44, align +2, u32 bone at +28, ALL with nan at +0).
          vb2 = `[pos.x_abs, pos.y, pos.z, 0,0,0, 0, 0xFFFFFFFF@+28, nx, ny,
          nz]` (ABSOLUTE positions, bone=0xFFFFFFFF, stride 44).
          ⚠️ The B1 doc §9 claims "B3 uses [pos,w,bone@+16,normal,FFFF,uv]"
          but it is WRONG for B3's sec34 (verified: bone@+16 gives
          absurd values; bone@+28 gives coherent 0-35). B1 uses that layout,
          B3 does NOT. Do NOT copy the B1 layout to B3.
          (Later reversed: the window layout with bone@16 is the correct one; the
          +2-aligned "sec34" grid was misaligned by 428 B. See `AGENTS.md` §3.4.10.)
        - **⚠️ Bin e327 (real_e327.bin, 624000) has ANOTHER vb2 layout**:
          `[pos.x=1.0, pos.y, pos.z, w@+12, bone@+16, normal@+20, float@+32,
          uv@+36]` (B1-type layout, bone=0). Do NOT confuse it with e326.
        - **HD→PS2 bone mapping: HD bone = PS2 bone × 2** (labels at even indices
          of the AWO: 0=XKLL_BODY, 2=KLL_WAIST, 4=KLL_STMC... 50=KLL_L00_RHAND;
          odd = structural slots without a label). HD sec34 uses bones 0-32.
        - **HD Krillin IS a REWORKED model, NOT a 1:1 conversion**
          of the PS2 one: 0 % match of local coordinates, different per-bone counts
          (HD bone 20 needs 420 verts, PS2 only gives 4). There is no
          vertex-to-vertex nor per-bone correspondence.
        - **🔴 THE RUNTIME DRAWS BY MESH-REF BLOCKS + ARMS (NATIVE IB)**:
          rebuilding the IB breaks the render. Tests v16-v20 (rebuilt IB)
          hung. Janemba v7 worked because it kept the native IB+arms and only
          filled the sec34 slots with data (mostly bone 0). See B1 §10.13.
        - **The viable way**: keep the COMPLETE e326 bin (native IB/arms/vb2/AZT)
          and ONLY rewrite the sec34 vertex positions in their
          slots, keeping the bone indices. `mezclar_ps2_hd.py` implements this
          (1254 slots rewritten). BUT the PS2/HD coords do not share a scale
          (ratios 0.12-7.7 per bone) → direct mixing deforms. Requires per-bone
          scale or a pose transform.
        - **The HD sec34 is interleaved by bones (412 runs)**, not grouped.
          The IB defines the order; do not reorder.
45. [x] **✅✅ MILESTONE (2026-08-14): PS2→HD KRILLIN ENTERS BATTLE AND SHOWS A
        SILHOUETTE** — validated way: keep the COMPLETE e326 bin (native IB/arms/vb2/
        AZT) and ONLY inject PS2 positions into the sec34 slots
        keeping the bone indices (`mezclar_ps2_hd.py`, 1254 of 1956 slots).
        Visual result (user): recognizable Krillin silhouette; GOOD right
        foot, right hand, left arm, forehead+upper face, part
        of the torso; DEFORMED in the rest; eyes with a normal texture; smooth battle.
        **Lessons**:
        - Do NOT rebuild the IB (it breaks labels→arms→IB, hangs). The runtime requires
          a coherent bin (PLAN_RELAYOUT B3→B1 §91-99: use the AWO as a
          complete template, inject only geometry).
        - The earlier hangs (v16-v24) were caused by: a corrupt AFS from earlier
          sessions (5.4M entries vs 3990 real), rebuilding the IB/arms, padding
          with the wrong bone. With the real AFS + intact bin + positions only → OK.
        - PS2 and HD local coords do NOT share a scale (ratios 0.01-177 per
          bone). The remaining deformation comes from mixing coords of different
          systems. The parts that look fine are the ones that match.
        - `pose_matrix.py` transforms PS2 local coords → absolute model world
          (coherent mags ~5). Pending: transform world→HD local
          (HD does not store the pose → requires more RE).
46. [x] **MIXING EXPERIMENTS (mix1/mix2/mix3, 2026-08-14) — result**:
        - **mix1** (nearest by position, no scale): BEST state. Recognizable
          silhouette, right foot/right hand/left arm/forehead+face fine; the rest
          deformed but structured.
        - **mix2** (per-bone scale = HD mag/PS2 mag): the good parts stay
          fine but the bad ones get MORE COMPRESSED (spaghettified). Per-bone
          scale makes it worse: HD is a rework with different proportions.
        - **mix3** (sequential skin order, no scale): good parts stay fine,
          bad ones more corrupt with dysfunctional vertices.
        - **CONCLUSION**: Krillin's HD is a REWORK (0 % coord match,
          different per-bone counts). No mechanical PS2→HD mapping is possible
          for a model that already exists. The parts that match are the ones that
          share structure.
        - **The Krillin case served its purpose**: it validated the end-to-end
          install pipeline (real AFS + e326 + position injection into
          slots + keeping native IB/arms/vb2/AZT). The game enters
          battle without a crash with the mod active.
        - **For NEW characters (IW)**: use the same technique (bin as a
          template + injection), or build the AWO from scratch with the
          character's counts (Janemba v6 worked). The HD rework only
          affects characters that already exist in HD.
        - Final installed state: mix1 (best). Tools: `mezclar_ps2_hd.py`
          (v1 nearest), `mezclar_ps2_hd_v2.py` (scale), `mezclar_ps2_hd_v3.py`
          (sequential).
        - B1 documentation: `docs/PLAN_RELAYOUT_B3_B1.md` (§91-99: AWO as a
          complete template, inject only geometry), `INVESTIGACION_FORMATO_
          B1_HD.md` §10.14-10.16 (interconnected labels+axes+arms+IB system).
47. [x] **🔴 FINAL VERDICT PS2→HD KRILLIN (mathematical RE)**: it is NOT feasible to
        reproduce the PS2 model in HD. Verified by least squares: there is NO
        rigid transform (R,t) that maps HD local coords to the PS2 world
        coords of the same bone (RMS error 1.7, unacceptable). Krillin's HD is a
        DIFFERENT model (reworked with 0 % vertex correspondence). It is not
        a skinning matrix problem — they are simply not the same model.
        **What WAS learned (valid for IW characters)**:
        (1) install pipeline validated (real AFS with 3990 entries + bin e326
        + position injection into slots + native IB/arms/vb2/AZT → no crash);
        (2) layouts of B3's 2 buffers confirmed; (3) the 241 IW→B3 PS2
        models (`modding resources\All Character Models from IW into AMB
        format\`) have the B3 skeleton (Janemba.amb = 48 JNB bones) and are the
        clean source for characters that do NOT exist in HD.
        **Real next step**: build the HD AWO from scratch with the IW
        character's counts (Janemba v6 made it work). There is no HD rework to
        interfere for absent characters.
48. [x] **🔴🔴 CRITICAL CORRECTION: HD POSE MATRICES = PS2 (51/51)**:
        item 47's conclusion ("HD is a rework, not convertible") was
        PARTLY WRONG because of a mapping error. Verified:
        - The HD AWO structure: the table at header +0x34 has 51
          entries pointing to bone ZONES, each zone with `+4 = the bone's real
          index` and `+8 = ptr to the local matrix (12 floats: quat+pos)`.
        - Bone 0 (BODY) is at 0x42360 (outside the table).
        - **The HD local matrices (read by zone index) are IDENTICAL to
          the PS2 ones (51/51, exact quat+pos).** The skeleton is the SAME.
        - With the same hierarchy (pose_matrix), the WORLD matrices are also
          identical (51/51). Both models are in the SAME pose and scale.
        - HD and PS2 world vertices have VERY similar magnitude ranges
          per bone (e.g. bone1: HD=[1.08..1.87] PS2=[1.08..1.87]) but they do NOT
          match vertex to vertex (0 % exact match).
        - **REVISED CONCLUSION**: Krillin's HD shares pose/scale/skeleton
          with the PS2 one, but the geometry is reworked/decimated (fewer vertices
          per bone). The PS2 local coords are in the right space.
        - **Implication for the converter**: the injection technique (mix1) was
          essentially correct. Pending refinement: map the PS2 vertices
          to the HD slots of the SAME bone with the right pose (I already have the
          world matrices per bone in both). `pose_matrix.py` needs the correct
          reading of the HD AWO zones (AGENTS said "the axis has no matrix"
          — FALSE, it is at +8 of the zone).
49. [x] **CRITICAL FINDING: HD BONE MAPPING = PS2 DIRECT (not ×2)**:
        HD sec34 uses bones 0-35 that point DIRECTLY to the AWO zones
        (index +4 of each zone), and the HD[zone] == PS2[idx] matrices. The
        correct mapping is `bone_HD = bone_PS2` (NOT ×2). `mezclar_ps2_hd.py`
        fixed to the direct mapping. The PS2 local coords of bone B are
        injected into the HD slots of bone B and produce the right world.
50. [x] **EXHAUSTIVE ANALYSIS OF THE 4 MODDING FOLDERS (2026-08-14)**:
        - **MOD EJEMPLO** (`modding resources update 2\MOD EJEMPLO`): the
          community converts IW→B3 PS2 and publishes BOTH formats per character
          (`B3\XXX.AMB` = #AMO0 LE PS2 + `IW\XXX.AMO/.AMT`). Complete Ginyu Force
          (Android 19, Burter, Chiaotzu, Cui, Dodoria, Guldo, Jeice,
          Zarbon). The .AMBs are the SAME PS2 format we know how to parse.
        - **EMD to AMG v0.90** (mod center): converts Xenoverse EMD→PS2 AMG.
        - **Bin to OBJ V3** (Nelson) + AMO_S: the community's mesh editing
          pipeline (exports AMG→OBJ, edit, re-import).
        - **DBZ B3 (X360) Lesson 1/2**: confirms X360 LZX 512 KB compression
          (/N:2048), and that the community edits HD bins with 010 Editor + the
          B3_AMB template (it does not convert PS2→HD).
        - **CONCLUSION**: the community has NO PS2→HD converter. They work the
          HD format directly (010 Editor) or convert IW→B3 PS2. The PS2→HD jump
          is our problem. MOD EJEMPLO + the 241 IW→B3 PS2 models are the
          source for new characters.
        - **Discord**: the "Dragon Ball Z Budokai Modding Community"
          (Nexus's discord.gg/qUcDxNj) has #modding-ressources, #tool-uploads
          and the B3_AMB template for 010 Editor. Access could give the
          definitive template of the HD structure.
51. [x] **✅ SCAN OF THE COMMUNITY DISCORD (2026-08-14, with the user's
        token)**: accessed "Dragon Ball Z Budokai Modding Community" (id
        349593493791965194). Findings:
        - **`.aerithdevs`** (an RE user) is developing a **converter for external
          models to Budokai** (Java, Windows/Linux/Android) that is adding
          "Porto BT3p to Budokai" with "creation of a compatible bone list"
          — EXACTLY our problem. Documents the AWG header:
          `Offset subs, size subs, flag, Offset name, offset materials, size
          materials, offset vertices, size vertices, offset faces, size faces,
          offset bones, size bones` + "the AWO contains more offsets and counters".
          Shared `port_test.zip` and skeleton JSONs (0001-0001.AMO._skel).
          Their tool has no public link (in development).
        - **`samueldoesstuff`** documents the HD RIG: bone ID, rig start,
          chunks, weight, points, sub-points, vertex location —
          confirms our SkinData. And the model port: the model
          part header (`B5 01 00 00 BD 29 00 00`), texture, shader, normals.
        - **Universal `Zero Devs' Tool`** (mega.nz/folder/wZlAiCBQ) — the
          community tool for model conversion (BT3p/PS2).
        - **`Goku_B3_PS3.zip`** — Goku models from B3 PS3 (A3T, close to 360).
        - **KEY CONFIRMATION**: samueldoesstuff: "all file types
          seem to be the same as B3, just with slight alterations like AWO
          instead of AMO" + .aerithdevs: "the AWO contains more offsets and
          counters". **The 360 format (AWO) is almost the same as PS2 (AMO)** —
          validates our pipeline (re-layout, not a different format).
        - The community does NOT publicly document PS2→360 (the 360 one is obscure);
          they work PS2→PS2 (BT3p/B2/B1→B3) or the 360 with 010 Editor. The
          user's token was stored in a local temp file for future sessions
          (never committed).
52. [x] **✅ DISCORD DOWNLOADS (2026-08-14) → `modding resources discord\`**:
        ~250 resources downloaded (tutorials, tools, research). The key ones:
        - **`B3_AMB_PS3.bt`** = 010 Editor template of the AWO/AWG (VALIDATES our
          RE): AWO header (+0x10 bones, +0x14 ptrConnections, +0x18 numAWGs,
          +0x1C ptrAWGoffsets, +0x24 ptrBoneNames); AWG header (+0x10 numBones,
          +0x14 rigging_data_ptr, +0x24 unk_Count, +0x2C ptrVertexBlock=vb2,
          +0x30 VertexBlockSize, +0x34 ptrFaceData=sec34, +0x38 FaceDataSize);
          riggingData = quaternion+pos+scale; BoneNames[32]. The template calls
          vb2 "vertexBlock" and sec34 "faceData".
        - **`00000002-00000002-b3.AMO.json`** = .aerithdevs's INTERMEDIATE format:
          breaks the B3 AMO down into text ($AMO→$AMG→$grp→$sub) with vertices
          `$v:F[pos] $u:F[uv] $n:F[normal] $c:B[color]` + weight, mesh part header
          `I&[000001B5 000029BD tex shader 00050401]`, matrix `$mtx:F[quat+pos]`,
          axis stamp `&6000020F`. 10 AMGs, 8256 verts. IT IS THE MOST COMPLETE
          STRUCTURAL REFERENCE OF THE B3 AMO.
        - **`0001-0001.AMO._skel-1.json`** = skeleton exported by .aerithdevs.
        - **`ZERODEV_tool_tutorial_edit_rig_data_animations_etc.zip`** and
          **`Zero_Devs_Tool_Axis_Data_Editing.rar`** = Zero Tool tutorials.
        - **`AMO_Model_Separator_v1.01.zip`**, **`Model-Rig_Extractor.py`** (v0.9),
          **`AMG_to_OBJ_V2.zip`**, **`Model_Part_Addition_Tool.zip`**.
        - **`Goku_B3_PS3.zip`** (not downloaded, a duplicate of what we already
          had). The rest: textures, bin lists, audio, shaders.
53. [x] **🔴 RB2 (Raging Blast 2) = REFERENCE FOR SPIKE CHUNSOFT SKINNING**
        (the sibling *Raging Blast 2* project on the maintainer's machine):
        - PC recompile of RB2 (2010) with the SAME ReXGlue/xenia/D3D12 SDK.
        - The modloader accepts PS3 ZPAK (STPZ→0LCS blocks): _i.zpak=IORAM (mesh+
          skeleton), _s.zpak=SPR (sprites), _v.zpak=VRAM (textures).
        - **RB2.exe contains the STPK/IORAM/VRAM/SPR3/TX2D parser** (strings
          verified): "could not read PS3 IORAM asset size", "SPRP contains
          no TX2D descriptors". It is the reference implementation of Spike
          Chunsoft's character format (same company/SDK as Budokai).
        - A format different from AWO (RB2 uses STPK/IORAM), but the skinning
          CONCEPT (IORAM = mesh+skeleton with a per-bone rig) is the reference
          for understanding Budokai's HD skinning.
        - Modloader: mods in `Modloader/Characters/<id>/` with `mod.toml`
          (kind=costume, base_character_id, form_id). IORAM/VRAM adapter
          "not enabled yet" (current phase).
        - **IORAM structure verified**: STPZ → 0LCS blocks + an STPK sub-block,
          named `XXX_PS3.ioram`/`XXX_X360.ioram`. Each character
          has an X360 variant (same Spike format). IORAM (mesh+skeleton)
          is Spike's skinning concept, a reference for understanding AWO.
        - Copied to `modding resources discord\rb2_reference\` (exe + goku ZPAK
          + modloader README).
54. [x] **FOLDER `modding resources discord\` (2026-08-14)**: 381 files in
        research/ (245), tools/ (58), tutorials/ (78), rb2_reference/. They do not
        duplicate mod center/modding resources (the download script filters
        duplicates and loose images). Key files:
        B3_AMB_PS3.bt (010 AWO/AWG template), 00000002-00000002-b3.AMO.json
        (.aerithdevs intermediate format, complete B3 AMO structure as text),
        0001-0001.AMO._skel-1.json (skeleton), Model-Rig_Extractor.py (v0.9),
        AMO_Model_Separator, AMG_to_OBJ_V2, Model_Part_Addition_Tool,
        ZERODEV tutorials, Zero_Devs_Tool_Axis_Data_Editing, Goku_B3_PS3.zip.
        `LEEME_PARA_SESION_B1.md` was created in the sibling dbz1 project to
        hand these findings over to the Budokai 1 session.
55. [x] **.AERITHDEVS INTERMEDIATE FORMAT (analysis of the JSONs)**:
        the files `00000002-00000002-b3.AMO.json` and `0001-0001.AMO._skel-1.json`
        are the breakdown of the B3 AMO into text:
        `$AMO/$model` → `$AMG000` → `$data000` (bones/labels) → `$grp00` →
        `$data00` (mesh part header) → `$sub00` (submeshes).
        Vertex: `<$dataNNN, weight, $v:F[pos] $u:F[uv] $n:F[normal] $c:B[color]>`.
        Mesh part header: `I&[000001B5 000029BD tex shader 00050401]`.
        Matrix: `$mtx:F[quat+pos]`, axis stamp `&6000020F`.
        `00000002` is the B3 PS2 format (18 AMGs in the skel, 10 AMGs in the other),
        weights per bone (1.0 mostly). **Validates our B3 PS2
        vertex structure (pos+normal+uv+weight+bone)** and the mesh part header.
        .aerithdevs did not publish their tool (in development, Java).
56. [x] **✅ JANEMBA v10 PIPELINE (2026-08-14, session 4)**: built from
        `Janemba.amb` (IW→B3 PS2, `modding resources\All Character Models
        from IW into AMB format\`). The AMO0 = 48 JNB bones, 17 AMGs,
        AMG0@0x8480 (21 parts), total 8943 verts / 4905 tris (parse_ps2_mesh).
        Skin: AMG0 parts 0-13 = 3788 skinned (100 %), parts 14-20 + AMG1-16 =
        5155 static (0 % skin). JNB→KLL mapping = 24 direct by label
        (0→0, 2→1, 4→38, 6→39, ... legs 38-49, 28→2, 30→12, 44→18, 46→27).
        - Pipeline v8/v9 (TEMP): parse_ps2_mesh → SkinData (local coords +
          bone) → split sec34 (skinned)/vb2 (static absolute via world_mats) →
          exact dedup by (bone, local coords 4dp) → JNB→KLL remap →
          prune tris to ≤1713 → vb2 decimated to ≤226 → build_janemba2 →
          build_afs (entry 326 = Krillin's visible bin).
        - v10 result: sec34=1956 (484 real + 1472 pad bone 0), vb2=226,
          IB=5140 (5139 + FFFF), **AWG delta=0x0** (AWG0 keeps its size),
          AMB 1074208 B. AFS: e326 loc intact + bin grows (delta +8192
          rounded). **IMPORTANT: the AFS expects the LZX-COMPRESSED bin**
          (magic 0F F5 12 EE) — use `xbcompress /N:2048` BEFORE build_afs
          (raw AMB 1074208 B → LZX 113484 B). Uncompressed, the game
          fails to read.
        - Installed as mod `janemba_v10` (mods/janemba_v10/us/data_cmn.afs,
          active in dbz3_user.toml `dbz3_enabled_mods = "janemba_v10"`).
        - **PENDING IN-GAME TEST**: boot + enter battle.
        Tools (TEMP): build_janemba_v8/v9/v10.py, analyze_skeleton.py,
        janemba_axes.py, janemba_skin.py, janemba_ranges.py, janemba_bone_map.py.
57. [x] **REFERENCES FOR THE B1 SESSION**: `modding resources
        discord\LEEME_PARA_SESION_B1.md` was created in the sibling dbz1 project with
        the Discord findings (B3_AMB_PS3 template, .aerithdevs intermediate
        format, RB2, resources, how to use the Discord API with the token).
58. [x] **RETARGETING RESEARCH (2026-08-14, web)**: to port geometry
        between HD games with skeletons of different pose/rotation:
        - World-space retargeting algorithm (retargeting-threejs/sketchpunk):
          `trgLocal = invBindTrgWorldParent * bindSrcWorldParent * srcLocal *
          invBindSrcWorld * bindTrgWorld`. Transfers ROTATION RELATIVE TO THE PARENT,
          works across different axis conventions.
        - For vertices (not animation): `local_trg = inv(mat_trg_bone) *
          mat_src_bone * local_src` (rotation R only, no translation).
        - Keys: homogeneous positive scale, quaternions for rotation,
          bone mapping by label or by bind-pose POSITION (Unigine
          SkeletonRetargeterTranslations pairs by bind pose translations).
        - **B1→B3 diagnosis (verified)**: bone directions differ by
          90-180° (STMC/CHEST 90°, LARM 180°...). It is NOT just scale/position,
          it is a different axis convention → direct injection (v17) or naive
          transform (v16) produce shear/stretching.
        - **v18**: rotation retargeting `local_trg = inv(R3)·R1·local_src`
          applied to the Krillin B1→B3 port. Installed for testing.
59. [x] **FINAL DIAGNOSIS OF THE B1→B3 PORT (2026-08-14, research)**: the
        "coord injection into slots" approach can NEVER import the B1 model
        because **the IB (topology) is B3's** — changing coords = deforming B3.
        B1 DID achieve a port (PS2 Goku→B1 HD) because **it rebuilt the IB**
        (build_ib_from_ps2, doc ESTADO_PORT_GOKU_SS2 §1: "no longer uses Gero's
        topology"). In B3, rebuilding the IB crashed (v6r) because B3's arms/mesh-refs
        are stricter than B1's.
        **THE REAL BLOCKER (common to B1 and B3)**: the PS2 skin→mesh mapping
        only covers 11-49 % of the vertices (our SkinData uses a contiguous
        formula but the 0x20 headers between submeshes break contiguity).
        **Solution in Model-Rig_Extractor v0.9** (lines 314-460): each
        bone's rig has ch_loc/sb_loc (rel AMG) → 32 B/16 B blocks with the mesh
        vertex OFFSET at +12. Comparing against the real vertex offsets
        (mp_extract: `160 + 32*cur_block + i*type_amnt`) yields
        (bone, weight, coords) per vertex → 100 % of the body.
        **Web research**: Bing/DDG/zenhax/Noesis have no public Budokai
        plugins; the practical documentation is LOCAL (Discord). Real retargeting uses
        world space with an auxiliary pose (retargeting-threejs/sketchpunk) and
        bind-pose position mapping (Unigine SkeletonRetargeterTranslations).
        **Community tools for the manual port**: AMO Decompiler/
        Compiler, OBJ to AMG v0.92, AMG to OBJ V2 (Nelson), Model Rig Toolset,
        EMD to AMG, Model Merger (all in mod center/).
60. [x] **FINAL VERDICT KRILLIN B1→B3 PORT (2026-08-14)**: NOT feasible as a
        binary conversion. Summary of experiments:
        - **v16** (B1 PS2 + naive local→world→local transform): shear
          (elongated) because bone ROTATIONS differ 90-180° between
          games (verified: STMC/CHEST 90°, LARM 180°).
        - **v17** (B1 HD direct coord injection): 90 % of slots but stretched/
          deformed — the bones' local spaces differ (bone 0: B1
          x[-0.97..2.37] vs B3 x[-0.38..0.55]).
        - **v18** (rotation retargeting inv(R3)·R1·local): improves arms/hands/
          forehead but still B3 (only 49 % of slots).
        - **v19** (world matching 100 % of slots): DEFORMED + giant triangles +
          black gaps (B1 world ≠ B3 slot space).
        - **ROOT CAUSE of "it always looks like B3"**: the IB (topology) is B3's —
          changing local coords without changing the IB deforms B3, it does not import B1.
          Rebuilding the IB in B3 crashes (v6r); B1 does tolerate it (Goku port).
        - **WHAT DID WORK HISTORICALLY**: mix1 (Krillin B3 PS2→B3 HD,
          recognizable silhouette) = coord injection into slots with the SAME pose
          (same game). The B1→B3 port fails because of a different pose/scale.
        - **Conclusion**: porting between games with different poses requires
          manual 3D retopology (OBJ→AMG + Blender + Model Rig Toolset), the
          path the community uses. Pure binary conversion is NOT feasible.
61. [x] **🔴 FEASIBILITY REVIEW (2026-08-14) — THE PORT IS FEASIBLE**:
        item 60's conclusion was wrong because of a wrong approach:
        - **The community successfully ports SDBH WM/B1/B2/IW→B3 PS2**. The SDBH WM
          EMD format uses the SAME skeleton as Budokai (verified:
          Android 18's `bc18gb00.esk` → labels waist/llegrot/stmc/chest/neck/
          head → direct mapping to KLL bones, 28 bones).
        - **The mistake was "slot injection"** (v15-v19): the IB (topology) is
          B3's → changing coords deforms B3. **The community builds the bin
          FROM SCRATCH** with its own rebuilt IB (EMD to AMG / OBJ to AMG:
          mesh part templates + face index + expanded 48 B vertices).
        - **The PS2→360 jump is a RE-LAYOUT** (endianness + renamed magics
          + mesh group re-layout), not a different format (AWO_FORMAT.md).
        - **EmdFbx (LibXenoverse) WORKS**: `emdfbx.exe` converts SDBH WM EMD
          → binary FBX (3.1 MB, mesh+skeleton). In `modding
          resources\EmdFbx-and-FbxEmd-LibXenoverse`. It is the universal bridge
          (Blender edits FBX → exports OBJ/FBX).
        - **Primitive community tools**: EMD to AMG (15 KB py),
          OBJ to AMG (10 KB py) — tkinter Python scripts hardcoded to PS2.
          Refactorable for HD → folder **`mod center hd\`** created with
          README.md + `emd_to_awo_hd.py` (v1: ESK parsing + KLL bone mapping).
        - **Real next step**: complete the EMD→FBX→OBJ→AWO HD pipeline
          (re-layout of the PS2 AMG into the 360 AWG) using Krillin's structural
          template (header+zones+mesh group+arms) with rebuilt geometry.
62. [x] **✅ EMD→FBX→JSON PIPELINE WORKS (2026-08-14, SDBH session)**:
        - `emdfbx.exe -ExportAscii` (LibXenoverse) converts SDBH WM EMD →
          binary FBX + ASCII FBX (4.3 MB). Verified with Android 18
          (`bc18gb00_x18g_body.emd` + `.esk`).
        - **`mod center hd\fbx_ascii.py`**: complete ASCII FBX parser.
          Extracts: meshes (verts/tris/nrm/uv), 69 skinning clusters
          (Indexes+Weights per bone), 90 bones with poses, connections.
          Android 18: 14 meshes, 1682 verts, 1851 tris.
        - **`mod center hd\emd_to_awo_hd.py`**: v1 — ESK parsing + SDBH→KLL
          label mapping (28 bones: waist→1, llegrot→38, stmc→2, chest→12,
          neck→27, head→28, rhand→25).
        - `%TEMP%\opencode\sdbh_test\SDBH_body.json` = intermediate data
          (meshes + clusters + bones) for building the HD AWO.
        - **Next**: build_awo from the JSON (AMG→360 AWG re-layout).
63. [x] **✅ HD AWO BUILT FROM JSON (2026-08-14, SDBH session)**: complete
        EMD→FBX→JSON→AWO HD→mod pipeline working:
        - **`fbx_ascii.py` v2**: stores mesh/cluster/object ids +
          connections. The cluster→mesh mapping is resolved via the OO
          connections (cluster→Skin→mesh). Cluster indices are LOCAL to the mesh.
        - **`build_awo_from_json.py`**: for each mesh, skin per local vertex
          (the cluster's bone+weight), transforms world→KLL local (PS2
          Krillin matrices), generates HD verts (stride 44) + IB.
        - **SDBH WM Android 18**: 14 meshes, 1682 verts, 1851 tris,
          **100 % skinned** (with skinning) to KLL space.
        - Packed with build_janemba2 (sec34=1956, IB=5140, delta=0),
          AFS with delta +23296 (128 KB bin > 105 KB slot).
        - **Installed as a mod in Krillin's slot** (e326).
        - **PENDING TEST**: boot + enter battle.
        - Tools in `mod center hd\`: emd_to_awo_hd.py, fbx_ascii.py,
          build_awo_from_json.py, README.md.
64. [x] **FINAL VERDICT ON THE SDBH→HD PIPELINE (2026-08-14)**: the
        EMD→FBX→JSON→AWO extraction works perfectly, but the port to B3 HD is
        blocked by pose retargeting:
        - **Slot injection (v3/v21)**: shows the HOST's topology
          (Krillin), never the new character. V21 filled 100 % of the slots but
          is still a deformed Krillin.
        - **Full re-layout (v20)**: rebuilt IB + different counts
          (sec34=1296≠1956, IB=5144≠5140) → CRASH. The B3 guest requires fixed
          counts (sec34=1956, vb2=226, IB=5140).
        - **Root cause**: the skeletons differ in ROTATION (SDBH vs KLL:
          Android 18's cluster transforms have different orientations).
          World→local retargeting requires the SDBH skeleton's complete world
          matrices, which EmdFbx's FBX does not export as an accumulated
          hierarchy (only 4x4 cluster transforms with translations of the
          ~1.75-tall chibi model).
        - **The community solves this with manual 3D retopology** (OBJ→AMG +
          Blender + Model Rig Toolset), NOT binary conversion. Confirmed
          repeatedly.
        - **SDBH extraction tools: WORKING** (fbx_ascii.py,
          emd_to_awo_hd.py). **HD packing tools: need pose
          retargeting** (not feasible in binary between skeletons with
          different axis conventions).
65. [x] **3D RETOPOLOGY + COMMUNITY TOOLS (2026-08-14)**: the viable
        way is manual retopology (Blender). Validated pipeline:
        - `emdfbx.exe -ExportAscii` (LibXenoverse): EMD→FBX. Blender 2.78
          plugin in `modding resources\EmdFbx-and-FbxEmd-LibXenoverse\
          FBXImporterExporterFromBlender2.78`.
        - `OBJ to AMG v0.92` (Nexus-sama, source code.zip): reads OBJ (V/VN/VT),
          expands vertices per triangle (48 B V+VN+VT), builds PS2 mesh parts
          with binary templates. It is THE retopology pipeline.
        - `Model Rig Toolset V0.6` (Source/): Model-Rig Extractor/Remover.
          Documents the PS2 rig (ch_loc/sb_loc → vertex offsets) → 100 %
          skin→mesh mapping.
        - `Bone Addition Tool v1.02` (.py): adds bones to the AMO.
        - `Budokai Modding Tool V1.5` (discord tools): AMO_LGBT (model
          merge), AMG_C (create AMG), Axis Editor. `b3_amg_*.bin` templates.
        - **Documented**: `mod center hd\RETOPOLOGIA_3D.md` (complete
          EMD→FBX→Blender→OBJ→AMG→AMB→HD pipeline).
        - **Reverse engineering of the 3D format** (consolidated summary):
          HD AWO = 0x30 header + AWG0 (sec34 stride 44 + vb2 + IB) + mesh
          group (13×0x50 mesh-ref blocks + arms). B3 vertex = `[nan,u,v,z,x,
          y,weight,bone@28,nz,-ny,nx]`. FIXED counts (sec34=1956, vb2=226,
          IB=5140) — changing them breaks parsing. The shadow arms (stamp 0x204)
          define IB limits in bytes.
        - `docs/INVESTIGACION_MODDING_BUDOKAI.md`: AFS/AMO/AMT/AMB ecosystem,
          abbreviation→character mapping.
        - `docs/PERSONAJES_BINS.md`: complete map of B1 bins→characters.

**Reference data** (in `%TEMP%\opencode\`, since deleted):
- Krillin: b327_ps2.bin (812 KB LE #AMO0), b327_hd.bin (682 KB BE #AWO)
- Cell: b146_ps2.bin, b146_hd.bin | Goku: b352_hd.bin
- IW Janemba: bin 541 = #AMO0 (48 bones/17 AMG), bin 542 = #AMT

**Key HD structure** (offsets rel AWO):
- +0x1C = AMG offset table | +0x24 = bone labels
- Each #AWG: labels at 0x40, axes at +0x14 (rel AWG), +0x30 = index buffer,
  +0x38 = FFFF restart | mesh group +0x28 = mesh-ref block table (0x50 B each)
- **CORRECT (2026-08-14)**: the AMG table points to the **#AWG magic** (0xD40 rel
  AWO), and the AWG internal offsets (+0x2C vb2, +0x30 ib, +0x34 sec34,
  +0x38 restart) are relative to the magic. The AWO header has 51 entries of 0x20
  (one per bone) with pointers into the axes zone (0x42360+) at +0x34,+0x54,...

**Tools**: `awo_tools/` (parse_model.py, analyze_awg.py, analyze_mesh.py,
trace_bone.py, RE_PROGRESO.md, build_big_amb.py, relayout_awg.py,
pose_matrix.py, mezclar_ps2_hd.py).

### 65.1 ✅ B3 PS2→B3 HD PORT — INJECTION PIPELINE WORKS (2026-08-17)

**In-game result** (mod `krillin_ps2`, user): Krillin loads and fights,
recognizable silhouette, but **DEFORMED**: only the hands, the
right arm and the upper face are preserved well. The rest is deformed but the
silhouette does not go into horrible territory (better than the Janemba mass).

**What was done**:
1. **REAL B3 vertex layout discovered** (see §3.2): the bone is at **+28**
   (u32), not +0x10 as the old tools said. Verified on
   b327_hd.bin + goten_298.bin: 36 unique bones 0-35, normals mag≈1, weight
   0.1-1.0, marker 0xFFFFFFFF at +0.
2. **AFS --append DISCARDED**: it breaks the table order → the guest uses
   binary search → host crash (0xC0000005, minidump analyzed: RIP in
   dbz3.exe RVA 0xA0967A, `movzbl (%r9,%rax)` = invalid guest memory
   read). The correct method is MID-INSERT with the delta rounded to 0x800.
3. **`mezclar_ps2_hd_v5.py`** (correct layout): injects PS2→HD coords per
   bone into the sec34 slots (1296/1956 slots rewritten; 660 uncovered =
   bones >35 that HD does not skin). Keeps the native IB/arms/vb2/AZT → the bin
   keeps its size (682528) → LZX 101052 < slot 106496 → mid-insert delta=0.
4. **B1→B3 analyzed**: the B1 and B3 skeletons share KLL labels but in a
   DIFFERENT ORDER (B1: 52 bones with OBI/ROBI/LOBI at the end; B3: 51 interleaved).
   The B1 AWO (685856 B) is 2.4x the B3 one (290784 B) → it does NOT fit compressed in the
   slot without decimation.

**Why it deforms (analysis)**:
- The "nearest by local coords" injection pairs PS2 vertices with HD slots
  of the same bone by minimum Euclidean distance. The parts that match
  (hands, right arm, upper face) are those with scale correspondence.
- The rest deforms because Krillin's HD is a decimated REWORK (0 % coord match,
  different per-bone counts, items 46-47). There is no mechanical PS2→HD
  mapping for a model that already exists in HD.
- The 660 uncovered slots (bones 36-50: legs/face vb2) keep the original HD
  positions → mix of two coordinate systems → deformed.

**Real next step (next session)**: instead of "nearest by coords",
transform PS2 local coords→PS2 world→HD local using the pose matrices
(identical 51/51) and look for the HD slot of the SAME bone whose world matches.
Or accept the partial deformation and use characters that do NOT exist in HD (IW),
where there is no HD rework to interfere (build the AWO from scratch with the
character's counts).

### 65.1b 🔴 SESSION 2 RESULT (2026-08-17 afternoon) — THRESHOLD + CONCLUSIONS

**v6/v7 with threshold installed as `krillin_ps2`** (world matching + only
good matches): see awo_tools/SESION_2026-08-17.md §4.

Key findings:
1. **World == Local within the same bone** (47/47 identical matrices, the
   per-bone transform is almost rigid). v6 == v5 byte for byte. Matching
   was never the problem.
2. **The problem is COVERAGE**: 660 slots (34 %) without PS2 coords (bones
   36-50, HD does not skin them in sec34) + 877 slots with a world match >0.5.
   Only ~197 slots (10 %) have a real world correspondence between PS2 and HD.
3. **Feasibility conclusion**: injecting PS2 into an existing HD model can NOT
   improve much (HD is a rework, 0 % vertex correspondence). The optimal
   result = the original HD with ~200 spot touch-ups.
   The REAL way to bring in external models = characters that do NOT exist in HD
   (IW, Pikkon, Pan, Super 17), building the AWO from scratch with the
   character's counts (no HD rework to interfere).

**For the user**: test the `krillin_ps2` mod (active). It should look like the
original Krillin HD (no deformation) with small PS2 improvements in the zones
with good correspondence (hands, right arm, upper face). If it looks fine, the
install pipeline is complete and the next way is a new character (IW) with its
own bin from scratch.

### 65.1d ✅ B3 FULL RECONSTRUCTION PIPELINE (2026-08-17 night) — TO BE TESTED

**New tool**: `awo_tools/port_ps2_to_b3.py` — PS2→B3 HD port with a REAL
IB (FaceType), adapted from B1's `amo0_to_awo.py` to the B3 layout:

- **parse_ps2_full**: parses ALL AMGs with chained submeshes →
  REAL verts + triangles + skin (rig → local coords). Krillin: 43 parts,
  9304 verts, 5294 tris.
- **build_buffers**: sec34 (44 B B3 layout) + IB from the real triangles.
  Without decimation: 5890 unique / 15882 indices.
- **decimate**: voxel per (bone, cell) — merges vertices of the SAME bone.
  → 734 verts / 4908 indices ≤ Krillin's counts (1956/5140).
- **FIXED-SIZE repacking (delta=0)**: keeps the template bin's structure
  (b327_hd.bin) and fills IN PLACE sec34, IB, descriptors
  (uniform A/B ranges, anchors at +0x18) and arms. The bin keeps 682528 B
  → LZX 90850 < slot 105296 → AFS mid-insert without shifting.
- **Installed as mod `krillin_rec`** (replaces krillin_ps2):
  `out\build\win-amd64-release\mods\krillin_rec\us\data_cmn.afs`,
  config `dbz3_enabled_mods = "krillin_rec"`.
- **⚠️ PENDING IN-GAME TEST**: if it works, it validates full
  reconstruction (the real way for IW characters). If it crashes, the regenerated
  descriptors/arms point to ranges the guest does not expect.
- Differences vs Janemba (failure): REAL IB + correct B3 layout (bone@+28)
  + fixed size (delta=0) + regenerated descriptors.

### 65.1e 🔴 VERIFICATION OF THE REAL B3 VERTEX LAYOUT (empirical, 2026-08-17)

Verified by reading b327_hd.bin: the sec34 vertex starts with
`0xFFFFFFFF` at +0, u at +4, v at +8, z_local at +12, x_local at +16,
y_local at +20, weight at +24, BONE at +28, nz at +32, -ny at +36, nx at +40.
Real v0 normal: (-0.99, 0.146, -0.0077) |n|≈1, bone 29 (facial). The HD
normal is [nz, -ny, nx] (y negated). B3 submesh descriptors: labels at +00,
"max N m" at +18 (NOT +30 as in B1), A ranges at +50/+54 and B at +58/+5C,
all with <<8 and contiguous.

### 65.1f 🔴 TEST CASE ANALYSIS (IW Pikkon) — DISCARDED

**Result of the tested v7 (user)**: the body looks SURPRISINGLY
GOOD, but 7 zones fail: ear, back of the head, mouth, right shoulder, belt,
right knee, left foot. Analysis (see SESION_2026-08-17.md §2.5):
- **Right knee (bones 44-46) and left foot (41-42) = 0 slots in sec34** → they live
  in **vb2** (absolute positions, bone=0xFFFFFFFF). The PS2 injection only
  touches sec34 → those zones stay 100 % HD ALWAYS. Inherent to injection.
- **Ear/mouth/head** = face in bones 29-37 + vb2 → almost nothing is rewritten
  with threshold 0.3 → they stay original HD → visible mix with the PS2 body.
- **v7 (threshold 0.3) is the MAXIMUM of slot injection** for an existing HD
  model. Fixing face/legs requires rebuilding the complete bin.

**Key insight from the sibling project (B1 docs, read tonight)**:
- B1 validated that the runtime draws the complete #AWO bin as is (native
  swap). Injection deforms because HD is re-topologized.
- **The right way for a PS2→HD port = REBUILD the complete bin**: sec34
  (44 B) + IB + arms + **submesh data zone** regenerated from PS2.
- **The submesh data zone ALSO EXISTS in B3** (verified: labels
  XKLL_BODY/L00_LHAND/L00_RHAND/M_DTEETH/L00_FACE + `max N m` strings at
  0x2D61-0x3471 of AWG0). **LAYOUT MAPPED**: 0x60-byte descriptor, contiguous
  range A at +50/+54, range B at +58/+5C (in B1 it was at +60/+64/+68/+6C).
  See `awo_tools/SUBMESH_DATA_B3.md`.
- Real pipeline for adding characters to B3: native swap (done) + PS2→HD
  port only for characters WITHOUT an HD version (IW: Pikkon, Pan, Super 17),
  using the HD bin of the same skeleton as a structural template + rebuilt
  geometry + regenerated submesh data.
- Reusable B1 resources: `amo0_to_awo.py`, `obj_to_awg_hd.py`,
  `port_b3_to_b1_v2.py` (in the sibling project's `mod center hd\conversores\`).
- See the full document: `awo_tools/SESION_2026-08-17.md` §6.

### 65.2 ⚠️ AFS --append DISCARDED (2026-08-17) — CRASH DETAIL

- **Symptom**: with `build_afs.py --append`, the game CRASHES (Goten) or
  HANGS (B1 port) on the loading screen. The control (original Krillin in
  append) loaded by chance (identical content).
- **Root cause (minidump)**: the guest uses **binary search** over the AFS
  entry table (it assumes increasing offsets). Append puts entry 327 at
  the end (0x117D4800) but 328+ go back to the middle (0x3AC8000) → unordered
  table → the search returns wrong entries → the guest reads a
  byte of invalid guest memory (`movzbl (%r9,%rax)` in dbz3.exe RVA
  0xA0967A, exception 0xC0000005).
- **Verified**: in the original AFS the table has 0 out-of-order entries; with append
  there is 1 (entry 328). Mid-insert preserves the order.
- **Decision**: mid-insert is THE method. The bin must fit in the slot
  (compressed ≤106496) or the LZX gets truncated. For big bins, decimate the
  geometry (not append). (Later the virtual mid-insert removed the size limit.)

## 9. IMPORTANT NOTES

- The game build uses the SDK installed in `rexglue/` (local install).
- The Tracy build (`win-amd64-tracy`) uses instrumented DLLs (`rexruntimerd.dll`,
  `rexgpu-xenosrd.dll`, `TracyClientrd.dll`).
- To profile: `tracy-capture.exe -o out.tracy` while playing, then
  `tracy-csvexport.exe` for zone analysis.
- The user speaks Spanish. Long play sessions.

### 9.1 🔴 FOLDER `github/` — UPLOAD REPO (manual sync)

`github/` is the project's **versionable** copy for uploading to GitHub (it is NOT a
local git repo; it is uploaded manually). The SDK (`rexglue-sdk/`) is NOT uploaded: the
`.gitignore` excludes it. **Runtime changes are distributed as patches**
in `github/patches/`.

**How to sync after a change** (replicate from the root respecting
`.gitignore`):

```powershell
# Copy the versionable folders (git ignores bins/lzx/afs/pyc/etc.)
# 1) src/  2) mod center hd/  3) awo_tools/  4) docs/  5) tools/  6) mods/
# 7) root files: AGENTS.md, AWO_FORMAT.md, CMakeLists.txt, CMakePresets.json,
#    dbz3_config.toml, dbz3_manifest.toml
# 8) SDK patches: github/patches/rexglue-sdk/{include,src}/... (the 3 files)
```

Key rules:
- **Do not upload** game files: `*.xex`, `*.afs`, `*.bin`, `*.awo`, `*.amb`,
  `*.amo`, `*.amg`, `*.azt`, `*.dds`, `*.iso`, `*.png`, `*.bmp`, `*.log`.
- **`generated/`**: only `README.md` (code derived from the .xex is not uploaded).
- **`mods/`**: distributed empty with `README.md` (real mods are not uploaded;
  they contain character binaries).
- **`tools/`**: `xbcompress.exe`/`xbdecompress.exe` ARE uploaded (exception in
  `.gitignore` `!tools/*.exe`).
- The **runtime patch** (virtual mid-insert) lives in `patches/` with its
  `README.md` on how to apply it. If the SDK is touched, UPDATE the 3 files
  in `patches/` and rebuild + copy `rexruntime.dll` to the build.

## 10. 🔴🔴 CORRECT MOD PIPELINE (2026-08-14) — per-entry override

**A finding that changes the cornerstone of mods** (inspired by
B1's `docs/PLAN_AFS_OUT_RE_COMPARATIVA.md`):

The runtime has an `AfsFindModOverride` hook (rexglue-sdk/src/filesystem/afs.cpp)
that serves files per AFS ENTRY **without repacking the whole AFS**:

```
mods/<mod>/us/<afs>/<entry_index>            ← direct file
mods/<mod>/us/<afs>/<entry_index>/<file>     ← folder with a file inside
```

### The 3 fixes found (cause of the historical hangs)
1. **B3's hook only supported a direct file**, not a folder. B1 already
   supported it (which is why B1's Gero/Piccolo worked and here they never did).
   → Fix: port the folder handling (iterate and use the first regular file).
   → Verified log: `AFS OVERRIDE HIT (folder)`.
2. **Compression**: the game uses LZX `/N:2048` (NOT `/N:32`). With `/N:32` the bin
   exceeds the slot → the guest truncates the LZX → crash.
3. **Padding**: the mod's bin must be **padded to the exact slot size** the
   guest reads (`to_read=106496` for entry 327). If it is shorter, the
   guest receives fewer bytes than expected → crash.

### Verification in logs
```
AFS OVERRIDE HIT (folder): ...\mods\<mod>\us\data_cmn.afs\327\geom.bin
AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=...
```
> `got=106496` = whole bin served. If `got < to_read` → padding is missing.

### The correct entry
- The runtime reads the AFS table at **offset 8** (NOT 0x10).
- Visible Krillin = **entry 327** (105296 bytes → padded 106496).
- Historical mistake: we were editing 326 (table@0x10), which is another bin.
- **🔴 2026-08-18**: the scripts (`texture_b3.py`, `swap_b3.py`) also
  read the table at 0x10 → a 1-entry shift (bin N = physical N+1). Fixed
  to offset 8 (see §4.2 "OFF-BY-ONE FIX"). This was the cause of the
  tex_91 crash (it served bin 92 in slot 91).

### Model swap status
- The override WORKS (the bin is served intact).
- The guest **crashes when processing another character's bin** (Goten→Krillin,
  Goten's body injected). The bin's content/structure is not accepted yet.
  (Later: native swaps work; see §3.1.)
- The community (LGBT Method, Add AMG tutorial) NEVER replaces the whole
  bin — it swaps axes/parts selectively.
- Next step: RE of the guest parser in `generated/dbz3_recomp.*.cpp`
  (crash addr `0x7ff7...`), instrument which offsets it reads from the bin.

### New tool
`awo_tools/analyze_bin_hd.py` — HD bin parser with the B3_AMB_PS3.bt template
(official offsets). Usage: `python analyze_bin_hd.py <bin> --dump`.
(Later marked OUTDATED — PS3 layout; do not use.)

### Documentation
Everything documented in `docs/` (index: `docs/README.md`). Start there.
- `modding resources update` is the drop box: the user puts new files there
  for us to integrate into `mod center`/`modding resources`.

## 11. 🔴 DOCUMENTED FAILURES

### 11.1 JANEMBA (IW→B3) — FAILURE, REMOVED AND ARCHIVED (2026-08-17)

**User decision**: remove all the Janemba work. The geometry
ended up corrupt (deformed mass) and caused crashes. Do NOT retry.

**What was attempted** (2026-08-14 sessions): port of IW Janemba's model
(bins 541-544, PS2 LE #AMO0/#AMG, 48 JNB bones) into Krillin's slot (360 BE
#AWO HD bin). Pipeline: parse_ps2_mesh → PS2 skin→local coords →
decimate (voxel) → build_janemba2 (Krillin's counts: sec34=1956, IB=5140) →
build_afs (mid-insert).

**Partial milestones** (documented in CONSOLIDADO.md §13.5): v6 entered
battle (deformed mass), v7 with the bone index at +28 showed a recognizable body,
but the rebuilt IB was an artifact ([0,256,512,...] — NOT a real triangle
list) and the PS2 parser does not read the triangle IB → the "working v7" drew
a pseudo-random pattern that looked like a body. The geometry was never valid.

**Lessons learned (they validate the real ports' path)**:
1. The runtime requires a COMPLETE, coherent #AMB bin (native IB/arms/vb2/AZT).
   Rebuilding the IB breaks the render → hang. Injecting only positions into
   sec34 slots while keeping the native IB/arms DOES work (Krillin PS2→HD
   showed a silhouette, smooth battle).
2. The HD vertex's bone index is at **+28** (u32) — REAL layout verified in
   §3.2: `[0xFFFFFFFF, u, v, z_local, x_local, y_local, weight, BONE@+28, nrm.z,
   -nrm.y, nrm.x]` (stride 44, align +2). The old tools that
   wrote at +4/+16 (the u/pos zone) produced the deformed mass. See
   `mezclar_ps2_hd_v5.py` (current user of the correct layout).
3. The sec34/vb2/IB counts are FIXED in the runtime — buffers of an existing HD
   model CANNOT be grown. For NEW characters the AWO must be built
   from scratch with the character's counts (Janemba v6 worked in this
   respect: sec34=1956, IB=5140 with padding).
4. Decimation (voxel, decimar.py) works to reduce geometry, but the
   result depends on a real IB (parse the PS2 IB with FaceType from the
   budokai_updated.ms MaxScript, do NOT assume triplets).

**Archived**: Janemba scripts in `awo_tools/historial_fallidos/`. Mod
`janemba_v10` removed from the build. Historical documentation in
`awo_tools/CONSOLIDADO.md` §13.5 (session 3) — keep as a learning
reference, do not retry.

## 12. 🔴🔴 SESSION 2026-08-18 — THE RIGHT WAY: SELF-CONTAINED HD BINS (RE)

**User decision**: ABANDON injecting PS2 geometry into Krillin's HD
template (it ALWAYS fails, documented in 65.1 and 11.1). The new
way: understand how **native swaps** work and build **SELF-CONTAINED** HD bins
(like Bulma/Babidi) by re-laying out the PS2 #AMO0 into the HD #AWO.
The Krillin test mods were disabled (clean Krillin; only
`tex_91` active).

### 12.1 KEY FINDING: THE HD BIN IS SELF-CONTAINED

**The native HD→HD swap works** (the user managed to put Bulma and Babidi in
Krillin's slot). The HD bin carries the WHOLE character (skeleton, geometry,
textures, draw structure) → the runtime accepts it in any slot.

Comparative analysis of 3 HD bins (decompressed from `us/data_cmn.afs`):

| Character | bin | bones | AWGs | structure |
|---|---|---|---|---|
| Krillin | 327 | 51 | 18 | AWG0 body + 17 hand/face AWGs |
| Bulma | 110 | 43 | 2 | AWG0 + 1 separate AWG |
| Babidi | 96 | 41 | 1 | a single AWG0 |

→ **The number of AWGs and bones VARIES per character.** There is no fixed structure.
Each HD bin is independent. (Krillin is the MOST complex case: 18 AWGs.
Bulma and Babidi are much simpler.)

### 12.2 PS2 (#AMO0) and HD (#AWO) SHARE STRUCTURE (RE-LAYOUT)

Verified by comparing `Janemba.amb` (IW→B3 PS2) with `b327_hd.bin`:
- **The 80 B axes are IDENTICAL** in both formats (same stamps):
  axis 0 (body) = `0x6000020F`, sub-bones = `0x9000020C` / `0x9800020C` /
  `0x9800020E`. The skeleton is the SAME.
- PS2 AMG0 header: `+0x10 n_bones, +0x14 axes, +0x18 mesh_groups, +0x1C
  labels_off` (labels at the END of the AMG).
- HD AWG0 header: `+0x10 n_bones, +0x14 axes, +0x18 groups, +0x1C 0x40,
  +0x20 mg_off, +0x24, +0x28 mg_size, +0x2C vb2, +0x30 ib, +0x34 sec34,
  +0x38 end, +0x3C` (labels AFTER the header, buffers in the header).

### 12.3 DEFINITIVE DIAGNOSIS OF THE JANEMBA/KRILLIN FAILURE

Both were attempted by **INJECTING** PS2 geometry into **Krillin's
template** (fixed counts sec34=1956/IB=5140, Krillin's descriptors/arms).
This ALWAYS fails with deformed polygons (polygons stretched towards the floor)
because the HD draw structure (mesh parts + descriptors + arms) does not
match the injected geometry. Krillin's body descriptors (0-11)
point at sec34 vertices up to 4440, but the rebuilt PS2 geometry
has fewer → OOB → deformation. Regenerating only the body descriptors
(leaving the hands intact) did NOT fix it.

**The B3 vertex layout IS CORRECT** (verified: 1956/1956 markers
0xFFFFFFFF, bones 0-35, weights 0-1, normals |mag|≈1). The script
`mod center hd/awg_to_obj.py` uses the **B1** layout (wrong for B3):
`[pos@+0, weight@+12, BONE@+16, nrm@+20, uv@+40]`. **Do NOT copy the B1 layout
to B3.** The real B3 layout: `[0xFFFFFFFF, u@+4, v@+8, z@+0xC, x@+0x10,
y@+0x14, weight@+0x18, BONE@+0x1C, nz@+0x20, -ny@+0x24, nx@+0x28]` (sec34 at
`sec_rel+2` because of the align).
(Later reversed: the window layout — pos@0, w@12, bone@16 — is the right one;
see `AGENTS.md` §3.4.10.)

### 12.4 THE PS2 RIG (bone→vertex mapping) — KEY PIECE OF THE CONVERTER

From `Model-Rig Extractor.py` v0.6 (SamuelDBZMAAM), the PS2 rig structure
for assigning the right bone to each vertex:
- Each bone (axis) points to its arm: `bone_loc = AMG0 + 32 + i*80 + 52`.
- `rig_start` = `read(bone_loc + 8)`.
- In the rig: `rig + 12` = `chunk_amnt`.
- Each 32 B chunk: `[weight, ch_len, ch_loc, sb_len, sb_loc]`.
- The **chunks (ch_loc)** are 32 B blocks with the vertex OFFSET at
  `+12`; the **sub-chunks (sb_loc)** are 16 B blocks with the offset at `+12`.
- The mapping: for each PS2 vertex (with its absolute offset), find which
  chunk of which bone it appears in → that bone + weight. (Algorithm in
  `Model-Rig Extractor.py` lines 314-460.)

**🔴 RIG OFFSET SOLVED (2026-08-18)**: the vertex offsets pointed to by the
rig chunks are **RELATIVE to AMG0**, NOT absolute. The AMG0 offset
(`amg_abs`) must be added to the offset read from the chunk
(`off = le32(bin, amg_abs + ch_loc + k*32 + 12) + amg_abs`). Without the shift
only 1059/4651 vertices match; with `delta = amg_abs`, **3788/4651** match
(the maximum, matches §56 "parts 0-13 = 3788 skinned"). Implemented in
`awo_tools/ps2_rig_skin.py`. Janemba AMG0: 4651 verts, 34 skinned bones
(bones 1-46), 863 static (vb2).

### 12.5 THE RIGHT WAY AND THE UNIVERSAL CONVERTER

**Build Janemba's HD bin as a SELF-CONTAINED bin** (re-layout of the
PS2 #AMO0 into the HD #AWO), NOT injecting into Krillin's template.

Universal converter pipeline (analogous to SamuelDBZMAAM's `amg_c.py`,
which builds PS2 AMGs from scratch with templates):
1. Parse the source model (PS2 #AMO0, OBJ, or any format→OBJ).
2. Build the HD AWGs: header + labels + axes (reuse the PS2 ones, same
   stamps) + mesh parts + descriptors + arms + buffers (sec34/vb2/IB).
3. Convert PS2 geometry (48 B, rig→bone) → HD (skinned 44 B sec34 + static 44 B
   vb2 + IB).
4. Convert textures #AMT→#AZT.
5. Pack the #AMB + LZX /N:2048 compression + per-entry override
   (the virtual mid-insert allows bins of any size).

**Community tools studied**: SamuelDBZMAAM's `Budokai-Modding-Tool`
(downloaded to a local temp folder):
`amg_c.py` (PS2 AMG Creator: header + axes + mp chunks + parts + end, LE),
`amo_a.py`, `amb_c.py`, templates `Files/AMG/b3_amg_*.bin`. The PS2
construction pattern is the guide for HD.

**CONVERTER PROGRESS (2026-08-18)**:
- `awo_tools/ps2_rig_skin.py`: **PS2 rig solved**. Parses the PS2 geometry
  (mesh parts + chained submeshes with the right stride per vtype) and assigns
  (bone, weight) via the rig (chunks/sub-chunks with offsets **relative to the AMG**;
  `amg_abs` must be added). Janemba AMG0: 4651 verts, 34 skinned bones
  (bones 1-46), 863 static (vb2).
- `awo_tools/ps2_to_hd_geometry.py`: **PS2→HD geometry**. Converts the
  PS2 vertices (local coords + bone) into the HD buffers: sec34 (skinned 44 B,
  correct layout `[FFFF,u,v,z,x,y,weight,BONE,nz,-ny,nx]`), vb2 (static 44 B)
  and IB (u16 BE). Janemba: 3832 skinned → sec34, 950 static → vb2, 4782
  indices. PS2 and HD local coords are the same (same skeleton/pose).
- **PENDING**: build the HD draw structure (mesh parts +
  descriptors + arms) to generate the self-contained `#AMB` bin, and the
  #AMT→#AZT texture conversion.

**RE documentation**: `awo_tools/RE_AWO_HD_CONVERSOR.md` (complete HD
structure, findings, converter pipeline).

### 12.6 NEXT STEP (in progress)

Build the PS2/OBJ→self-contained HD bin converter for Janemba:
1. Parse the PS2 rig → bone per vertex.
2. Convert PS2 geometry (48 B) → HD sec34/vb2/IB (44 B).
3. Rebuild a coherent HD draw structure (mesh parts + descriptors + arms)
   — the `amg_c.py` pattern in HD.
4. Install as an override (swap) in slot 327 and test.

## 13. 🔴🔴 SESSION 2026-08-19 — FRESH EYES + FINDING: MULTIPLE VERTEX FORMATS

**External review of the project (new perspective) + a quick-feedback tool
+ a finding that changes the diagnosis of the PS2→B3 port.**

### 13.1 🔴 KEY FINDING: B3 HD HAS SEVERAL VERTEX FORMATS, NOT ONE

**The RE was done almost entirely on the game's ODDEST bin (Krillin b327, 18 AWGs).
Other native bins use DIFFERENT vertex formats.** Verified empirically
by reading fresh bins from the same `us/data_cmn.afs`:
| Character | bin | AWGs | bones | main buffer marker | layout |
|---|---|---|---|---|---|
| Krillin | 327 | 18 | 51 | `0xFFFFFFFF` at +0 | **Format A**: skinned sec34 `[FFFF,u,v,z,x,y,weight,BONE@28,nz,-ny,nx]` + static vb2 (absolute pos, bone=FFFF) |
| Bulma | 110 | 2 | 43 | no FFFF | format B (positions at +0, another field at +24/+28) |
| Babidi | 96 | 1 | 41 | `0x00090000` | format C: positions at +0, no FFFF marker, garbage bones at +28 |
| Goten | 298 | 21 | 56 | `0x20353320` | format C/B: mixed, NaN in some fields |
| Cell F2 | 147 | 17 | 48 | FFFF at +0 | format A (same as Krillin) |

- Bin e327 (another Krillin, 624000 B) already documented a different "B1-type" layout
  (item 44). → **The guest autodetects each bin's format. Each bin is
  self-contained (confirms the thesis of §12).**
- **Implication**: the native swaps that work (Bulma/Babidi/Goten → Krillin
  slot) carry formats DIFFERENT from Krillin's → the guest accepts any
  coherent format. **The port of a new character does NOT have to force
  Krillin's format A: it can be emitted in the format of a simple template
  tested in game (Babidi/Bulma).**
- "Injection into Krillin's template" failed because it forced PS2 geometry onto
  Krillin's specific topology/mesh-refs (format A). Root cause now clear.
- (Later: all the bins turned out to share the window layout, read at the right
  base; the "formats" were artifacts of misaligned readings. See `AGENTS.md` §3.4.10.)

### 13.2 NEW TOOL: `awo_tools/awg_to_obj_b3.py` (self-contained OBJ exporter)

Exports an HD bin (#AMB/#AWO) to OBJ **without needing the PS2 reference**:
- World matrices rebuilt from the bin's own axes: local quat+pos in
  the first 12 floats of the axis (80 B), **parent pointer at +0x40 (rel AWG0)**.
  Verified: HD-from-axes world == PS2 world **51/51 exact match** on
  Krillin. (Corrects the belief of items 30/40 that "the axis has no matrix".)
- AWG0 layout verified empirically (settles the discrepancy with the Discord's
  010 "PS3" template, which uses offsets+size and gives absurd counts):
  `+0x2C vb2_rel | +0x30 ib_rel | +0x34 sec34_rel | +0x38 end_rel` (offsets, not
  off+size pairs). Counts come out exact (Krillin 1956/226/5140).
- **`analyze_bin_hd.py` is OUTDATED**: it uses the 010 template layout
  (offsets+size at +28/+2C/+30/+34), which is WRONG for X360 → gives absurd
  n_sec (233 on Krillin). Fix or mark as PS3-only.
- Usage: `python awo_tools\awg_to_obj_b3.py <bin> [out.obj] [--no-skin]`.

**This exporter is the missing feedback loop**: it lets you see the geometry
of any built bin in 2 seconds without opening the game (it instantly detected
the format difference of Babidi/Goten).

### 13.3 QUICK DIAGNOSIS OF A BIN (bounds/finiteness)

Analysis script for the exported OBJs: checks NaN/inf and the bounding box.
Valid native characters (Krillin, Cell F2) give plausible human bounds
(~7-25 units) and 0 NaN. The built Janemba bins
(`janemba_from_cell.amb`, `janemba_v2.amb`) export cleanly: **4782 verts, 2100
tris, 0 NaN, plausible bounds** → the port's geometry is WELL FORMED; what is
pending is whether the guest accepts it.

### 13.4 TEST MOD INSTALLED: `janemba_from_cell` (slot 327)

- Bin: `awo_tools/bins_trabajo/janemba_from_cell.amb` (796996 B, #AMB with a 340 KB AWO
  + 375 KB AZT, 48 JNB bones, sec34=3832 + vb2=950 + ib=6302).
- Built with `build_from_template.py` using **Cell Form 2 (bin 147, 48 bones)
  as the structural template** (same bone count as Janemba) + Janemba's real
  geometry (ps2_to_hd_geometry) + descriptors regenerated to cover all the geometry.
- Installed as a per-entry override (LZX /N:2048 = 122472 B, pad to 122880):
  `mods/janemba_from_cell/us/data_cmn.afs/327/geom.bin` + `manifest.txt`.
- **ACTIVE** (no `.disabled`). Only other active mod: `tex_91` (entry 91, no
  conflict). The toml's `dbz3_enabled_mods` is still dead code (real activation
  is by the absence of `.disabled`).
- **⚠️ PENDING IN-GAME TEST**: boot → character select → Krillin
  (slot 327) → if it shows Janemba's silhouette, the self-contained reconstruction
  is VALIDATED and the PS2→B3 pipeline is open. If it crashes/hangs, the guest
  rejects Cell's descriptors/arms with Janemba's geometry.
- The bin exceeds the slot's to_read (122472 > 106496) → it also exercises the
  runtime's **virtual mid-insert** (pending in-game validation since
  08/18 with goten_override_test).

### 13.5 FEASIBILITY VERDICT (fresh perspective)

- **The PS2→B3 port is FEASIBLE and CLOSER than the history suggests.** Each
  earlier failure (Janemba, PS2 Krillin) was a concrete bug identified and solved
  separately: fake IB (→ FaceType), bone at +28 (→ layout A), incoherent structure
  (→ template with the same bone count + regenerated descriptors), formats (→ finding
  13.1). The sibling B1 ALREADY completed a full PS2→HD port (Goku) by rebuilding the IB.
- **The real blocker is not research but feedback**: each test meant
  opening the game. `awg_to_obj_b3.py` + the bounds check bring it down to seconds.
- **Strategy conclusion**: do not force Krillin's format. Emit the new
  character in the format of a simple tested template (Babidi/Bulma) or validate the
  Cell F2 template (48 bones) with Janemba. Next step = test `janemba_from_cell`.

### 13.6 🔴🔴 ROOT CAUSE OF "KRILLIN UNCHANGED" (2026-08-19): STALE RUNTIME DLL

**The `janemba_from_cell` mod was tested in game (13:37, log dbz3_056) and Krillin came
out 100 % normal.** After analyzing the runtime (not the bin — the LZX decompresses exactly
to the source .amb), the cause was NOT the mod but the **outdated runtime DLL**:

- The `out/build/win-amd64-release/rexruntime.dll` was the **old** version (11155968 B,
  from 08/14): it contains `AfsFindModOverride` + the `AFS327 READ`/`AFS MOD READ` debug
  but **NOT** the virtual mid-insert (`AfsGetVirtualTable`/`AfsTranslateOffset` and the
  `AFS OVERRIDE LOOKUP/HIT/MISS` logs ABSENT from the DLL).
- The **correct** DLL (11183104 B, 08/18 12:29, with virtual mid-insert) existed in
  `rexglue-sdk/out/win-amd64/rexruntime.dll` but **had not been copied** to the build:
  the build had the old copy from `rexglue/bin`.
- **Consequence**: the slot 327 override (geom.bin 122880 B > to_read 106496)
  was silently rejected → the guest read the original Krillin → "0 changes".
  The simple override system (bins ≤ to_read, e.g. tex_91 114688 ≤ 114688) did
  work, which is why tex_91 was still OK.
- **This also explains why `goten_override_test` (110592 > 106496) was never
  validated**: the virtual mid-insert had NEVER run in game (AGENTS marked it
  "PENDING in-game test").
- **Fix applied**: `Copy-Item rexglue-sdk/out/win-amd64/rexruntime.dll →
  out/build/win-amd64-release/rexruntime.dll`. Verified: the build's DLL now
  has the virtual mid-insert strings and size 11183104.
- **⚠️ LESSON**: any SDK change (afs.cpp/host_path_file.cpp) requires
  rebuilding `rexruntime` AND copying the DLL to the build — if the copy is skipped, the build
  uses the version installed in `rexglue/bin` (stale) and big overrides fail
  SILENTLY (the original character shows, no crash or warning). Always check:
  `Select-String rexruntime.dll -Pattern "AfsGetVirtualTable"` must give PRESENT.
  (This became `tools/copy_sdk_dlls.ps1`.)
- **STATUS**: `janemba_from_cell` still active and the correct DLL is in the build.
  PENDING an in-game re-test (it should show Janemba with Cell's colors).

### 13.7 🔴✅ AWG0 FORMAT C SOLVED (Goku 264 / Vegeta 424) — 2026-08-19

**Session goal**: "Goku with Saiyan armor" (armored Vegeta 424 body +
Goku's head). Locating the head required exporting both bins → the
FORMAT C (that of most bins: Goku, Vegeta, Babidi, Goten, armored
Krillin 329) was decoded, distinct from format A (Krillin 327, Cell F2 147).

**AWG0 FORMAT C layout (stride 44, NO +2 align)** — verified on Goku and Vegeta:
```
+0  x | +4  y | +8  z  (position IN BONE-LOCAL SPACE, bounds [-1,1])
+12 0xFFFFFFFF (u32 marker)
+16 u | +20 v  (UV, 0-1)
+24 n.x | +28 n.y | +32 n.z  (local normal)
+36 weight | +40 BONE (u32)
```
`+0x2C` is NOT a vb2 offset: it is the buffer SIZE in bytes (2455×44 on Goku).
The IB is a **triangle STRIP** (consecutive indices, alternating winding,
degenerate triangles as jumps), NOT a list, and there are NO 0xFFFF restarts (unlike format A).

**⚠️ KEY: the location of the AWG0 sec34 buffer VARIES per bin** (not always at
`sec_rel`). The exporter `awg0_export.py` TRIES 3 locations (sec_rel, sec_rel+2,
end of the mesh group = mg+mg_size) × 7 marker offsets (0,2,12,16,24,38,40) and picks the
one that gives ≥50 % FFFF markers:
- **Goku 264**: sec34 at `sec_rel` (0x37B4), marker at +12, n_sec=2418
- **Vegeta 424**: sec34 at `end_mg` (0x44E0), marker at +38/+40, n_sec=2656
- **Krillin 327** (format A): sec34 at `sec_rel+2`, marker at +0, n_sec=2183
Bounds verified: Goku [-1,1] 0 NaN, Vegeta [-1,1] 0 NaN, Krillin [-1.76,2.49] 0 NaN.

**New tool**: `awo_tools/awg0_export.py` — exports any bin's AWG0
to OBJ autodetecting the format (A/C) and buffer location. `awg_parts2.py` — per AWG.

**AWG map (identified by the mesh group labels)**:
- **Goku** (23 AWG): AWG0 body+XGOK_L00_S00_FACE+teeth; AWG1-8 GOK_L*_LHAND (left
  fingers); AWG9-15 GOK_R*_RHAND (right fingers); **AWG16-22 XGOK_Lxx_S00_FACE (face/hair)**
- **Vegeta** (26 AWG): AWG0 body+XVGT_HAIR+XVGT_L00_S00_FACE+teeth+armor(RWPAT/
  RSPAT/SCOUT/TAIL); AWG1-18 fingers; **AWG19-25 XVGT_Lxx_S00_FACE (face/hair)**

**Goku↔Vegeta face correspondence** (by numeric label): Goku L01,L18,L04,L05,L06,
L42 ↔ Vegeta L01,L18,L04,L05,L06,L44 (Goku L09/L00 ↔ Vegeta L00/L00_S09).

**Shifted skeletons** (same base order, Vegeta's armor inserts bones):
Goku HEAD=36, JAW=38, RMOUTH=40, LMOUTH=42, DTEETH=44 | Vegeta HEAD=44, JAW=50,
RMOUTH=52, LMOUTH=54 (+ RWPAT=16/18, RSPAT=26/28, HAIR=48, FAC=46). Mapping BY LABEL.

**Head swap status**: the face AWGs (nb=1) use an offset layout not yet
solved (different from AWG0 and from the finger AWGs). Each AWG type has its own
offsets. PENDING: fine RE of the face AWG layout to complete the swap.

**Thesis 13.1 confirmed**: each bin is self-contained with ITS OWN
format (Goku marker+12, Vegeta marker+38/+40, Babidi+16, Goten+10, armored Krillin+24).
The guest autodetects each bin's format. Krillin 329 (armor) uses format C,
Krillin 327 format A — the same character has bins in both formats.

### 13.8 TEST MOD: `sw_vegeta424` (validate format C in the runtime) — 2026-08-19

- Goal: confirm the runtime accepts a bin in **format C** (armored Vegeta
  424) via a whole-bin swap, before investing in fine head mixing.
- Bin: `awo_tools/bins_trabajo/vegeta_424.bin` (#AMB, 894528 B, format C, 26 AWG,
  55 bones, sec34=2656). Compressed LZX /N:2048 = 126030 B, pad to 126976 (0x1F000).
- Installed: `mods/sw_vegeta424/us/data_cmn.afs/327/geom.bin` + manifest. **ACTIVE**
  (no `.disabled`). `janemba_from_cell` **disabled** (it also touched 327, it was
  isolated for this test). Only other active mod: `tex_91` (entry 91, no conflict).
- The bin exceeds the slot's to_read (126976 > 106496) → exercises the virtual mid-insert.
- **⚠️ PENDING IN-GAME TEST**: select → Krillin (slot 327) → does Vegeta appear
  with Saiyan armor? If YES, format C is validated in the runtime and the base for
  head mixing is confirmed. If it crashes, the runtime does not accept this complete C bin
  and it needs review.
- Correct DLL (11183104 B, with virtual mid-insert) VERIFIED present in the build
  after the 13.6 fix.
- **✅ VALIDATED IN GAME (user)**: `sw_vegeta424` shows **Vegeta with Saiyan
  armor in Krillin's slot**. Format C + the virtual mid-insert work in
  the runtime. Base confirmed for head mixing.

### 13.9 🔴✅ LAYOUT OF THE FACE/HAND AWGs (nb=1) SOLVED — 2026-08-19

**The head swap requires exporting the face AWGs. The layout of the
AWGs with n_bones=1 (face/hair/hands) was decoded**, distinct from AWG0 (format C) and format A.

**Face AWG vertex layout (44 B, marker 0xFFFFFFFF at +0)**:
```
+0  u32 0xFFFFFFFF (marker)
+4  f32 u | +8  f32 v        (UV, 0-1)
+12 f32 x | +16 f32 y | +20 f32 z  (position in the head bone's LOCAL space)
+24 f32 weight (=1.0) | +28 f32 0.0 (pad)
+32 f32 nx | +36 f32 ny | +40 f32 nz  (unit normal)
```
Verified: dot product normal·(pos−centroid) positive in 100 % → this is the
only interpretation (positions +12/+16/+20, normal +32/+36/+40).

**Face AWG structure (offsets rel the #AWG header, h)** — the fields mean
SOMETHING ELSE than in AWG0:
```
+0x10 n_bones (=1) | +0x2C = vertex buffer SIZE (n*44)
+0x30 ib_rel = IB offset | +0x34 sec_rel = IB SIZE in bytes
+0x38 end_rel | Descriptor at h+0x180: +0x1C = n_verts, +0x24 = n_tris
The vertex buffer is ALWAYS at h+0x1F0.
```
⚠️ In the face AWGs, `sec_rel` (+0x34) is NOT an offset: it is the index buffer SIZE.
The vertex buffer is NOT at sec_rel but at a fixed **h+0x1F0**.
The IB is a **triangle list** (every 3 indices = 1 triangle, quad strip), not a strip
with alternating winding. The "IB max > n_sec" mystery was a meaningless computation
(it used sec_rel as an offset).

**New tool**: `awo_tools/awg_cara_export.py` — exports a face AWG to OBJ.
Usage: `python awg_cara_export.py <bin> <awg_index> [out.obj]`. Verified: Goku AWG16
101 verts/148 tris, Vegeta AWG25 120 verts/150 tris, all 0 NaN, plausible bounds.

**KEY FOR THE HEAD SWAP**: Goku's and Vegeta's face pieces share the
head bone's local space (almost identical bounds: Goku y[0..1.52] z[0..1.25],
Vegeta y[0..1.62] z[0..1.23]) → the geometry is copied 1:1 between bins without
transformation.

**Face AWG map confirmed**: Goku AWG16-22 = XGOK_L01/L18/L09/L04/L05/L06/L42
_S00_FACE ↔ Vegeta AWG19-25 = XVGT_L01/L18/L00_S09/L04/L05/L06/L44_S00_FACE.
Correspondence by numeric label (L01↔L01, L04, L05, L06, L18, L42↔L44).

**NEXT STEP (head swap)**: a script that takes the armored Vegeta bin (base,
works) and replaces the geometry of its face AWGs (19-25 + face/teeth/HAIR of the
AWG0) with Goku's face AWGs (16-22 + face/teeth of AWG0), by
label correspondence, keeping Vegeta's bones/offsets.

### 13.10 🔴✅ GOKU→VEGETA HEAD SWAP WORKS (block reconstruction) — 2026-08-19

**New script**: `awo_tools/swap_cabeza.py`. Takes the armored Vegeta bin (424) and
replaces its block of face AWGs (AWG19-25, XVGT_Lxx_S00_FACE) with Goku's
(AWG16-22, XGOK_Lxx_S00_FACE), by numeric label correspondence. Keeps Vegeta's
body/armor.

**AWG correspondence** (Goku → Vegeta): L01(16→19), L18(17→20), L09(18→21),
L04(19→22), L05(20→23), L06(21→24), L42(22→25). L09→L00_S09 mapped explicitly.

**Strategy = BLOCK RECONSTRUCTION** (not per-AWG mid-insert, which was fragile because of the
buffer/IB overlap): Goku's 7 face AWGs are read, repacked as Vegeta AWGs
(layout with the buffer at h+0x1F0 + an IB overlapping the last 32 B), and Vegeta's
whole face block is replaced at once, recomputing the offsets of later AWGs,
the AZT and the AWO size.

**KEY of the buffer/IB overlap in face AWGs**: the buffer (n*44 bytes) and the IB (n*2
bytes) overlap by 32 bytes — the IB starts at `ib_rel = 0x1F0 + n*44 - 32`, and the
total AWG size is `end_rel = ib_rel + n*2`. When rebuilding, the data block from
0x1F0 is `buffer[0 : n*44-32] + whole IB`. (Initial bug: trimming 32 B from the end
corrupted the IB → OOB indices → many skipped.)

**Verified by OBJ export** (awg_cara_export.py): the generated bin's 7 face AWGs
export 148/148 or 156/156 tris, 0 skipped, 0 NaN, bounds y[0..1.52] z[0..1.25]
(= Goku's head/hair). AWG0 (armored Vegeta's body) stays intact.

**Mod installed**: `mods/goku_armadura` (slot 327, ACTIVE). `sw_vegeta424` disabled.
Bin: `awo_tools/bins_trabajo/goku_armadura.bin` (892216 B, LZX 123788 B, pad 126976).
**⚠️ PENDING IN-GAME TEST**: select → Krillin (slot 327) → Goku with Saiyan
armor (Goku's head + Vegeta's body)? If it works, the HD→HD head swap is
VALIDATED. If the head looks odd/crashes, review AWG0's face/teeth
(not swapped yet).

**🔴 CRASH OF THE BLOCK-RECONSTRUCTION SWAP (2026-08-19)**: the `goku_armadura` bin
(block reconstruction with mid-insert) is STRUCTURALLY VALID (contiguous face AWGs,
Vegeta's mesh group kept, Goku's geometry with 0 skipped/0 NaN,
AWG0 intact) but the guest CRASHES with 0xC0000005 while parsing the model (GPU thread,
no AFS327 READ = early crash). Probable cause: AWG0 references the face AWGs
by offsets that break when the face block moves.

**✅ ALTERNATIVE WAY: IN-PLACE INJECTION (do not move offsets)** — `swap_cabeza_inplace.py`:
starts from the armored Vegeta bin and copies the geometry of Goku's face AWGs into the
EXISTING buffers of Vegeta's face AWGs, KEEPING each AWG's size (no
mid-insert, no offset moves, AWG0 untouched). If Goku's buffer is smaller it is
padded with 0xFF; if larger it is truncated (L04 106->102, L06 120->106). The bin keeps
the original size (894528 B) and AWG0's references stay valid. Verified by
OBJ export (0 NaN, 148-156 tris, few skipped due to truncation). Installed as
`mods/goku_armadura` v2.0. **PENDING IN-GAME TEST**.

**✅ WORKS IN GAME (v2.0 in-place, user)**: the in-place injection bin LOADS and
enters battle — Vegeta with Saiyan armor with Goku's injected head/hair.
**BUT there is localized Z-FIGHTING on the forehead/eyes**: when blinking, the geometry
and texture of Goku's face are seen alternating. Cause: VEGETA's face/hair is still in
AWG0 (descriptors XVGT_L00_S00_FACE, XVGT_HAIR A=[1992+87], XVGT_M_DTEETH/UTEETH) and
overlaps the Goku geometry injected into the independent face AWGs (19-25).

**FIX (v3.0)**: neutralize Vegeta's face/hair/teeth descriptors in AWG0
by setting their A_size/B_size to 0 (XVGT_HAIR x2, XVGT_M_DTEETH x2, XVGT_M_UTEETH x1). The
AWG0 descriptors have the label at +0x00 of the block, 'max N m' at +0x18, A/B ranges
at +0x50/+0x54/+0x58/+0x5C. Verified: 20 descriptors still draw (XVGT_
BODY body intact), 5 neutralized. Installed as `mods/goku_armadura` v3.0.
**IN-GAME RESULT (v3.0)**: parts of the hair disappear, but it is STILL not Goku's
face (not Goku's complete head). The forehead/eye z-fighting was reduced but
not solved: Goku's base face injected into the face AWGs (19-25) does not match
what the runtime draws, and neutralizing Vegeta's hair left holes.

**🔴 FINAL STATUS OF THE HEAD SWAP (2026-08-19) — PAUSED BY USER DECISION**:
the Goku→Vegeta swap (armored Vegeta 424 body + Goku 264 head) stays
**documented but UNSOLVED** and is set aside to devote the session to other tasks.
What was learned is archived in case it is resumed:
- The **in-place injection** way (copy face AWG buffers into the target's face AWGs
  without moving offsets) DOES load and enter battle (unlike the
  block reconstruction, which crashes).
- The real blocker: the runtime draws AWG0's face (descriptors XVGT_L00_S00_FACE/
  HAIR/DTEETH/UTEETH), which is NOT replaced just by injecting the separate face AWGs →
  z-fighting and incomplete mixing. A complete face would ALSO require replacing
  the face/hair geometry in AWG0's sec34 (not just neutralizing it, which leaves
  holes), which requires re-mapping vertices between formats A/C. Not trivial, paused.
- Mod `goku_armadura` v3.0 is still active (slot 327) but the result is not the one sought.
- Tools: `swap_cabeza.py` (reconstruction, crashes), `swap_cabeza_inplace.py`
  (in-place way), `awg_cara_export.py`, `awg0_export.py`, `awg_to_obj_b3.py`.

## 14. 🔴✅ ASSET REFACTOR: NO `active_region` OVERLAY (2026-08-20)

**Problem**: the launcher built an `active_region/` overlay next to the exe
(`PrepareRegionData`) by hardlinking/copying the chosen region's assets +
the mods, and deleted the whole folder at every boot. This duplicated space
and forced the end user to have the assets in awkward places. The sibling dbz1 already
uses the clean model (read assets directly, without duplicating), replicated here.

**Solution (dbz1 model, no duplicates)**:
1. **`OnConfigurePaths`** (`src/main.cpp`): `paths.game_data_root = game_dir`
   directly (the folder containing `us/`/`eu/`). `active_region` is NO longer built.
   `game_dir` detection supports TWO layouts:
   (a) `us/` next to the exe, and (b) `assets/{default.xex,us,eu}` next to the exe
   (`FindGameRoot` looks for `base/us` or `base/assets/us`, falling back to the
   development project root 3 levels up and to the exe's parent).
2. **`ApplyRegionMount()`** (`src/region.h`/`src/region.cpp`, new): mounts a
   `HostPathDevice` at `\Device\Harddisk0\Partition1\us` → `game_dir/<region>`
   (us/eu), reading the assets directly without copying anything. Called in the
   Play handler and in `OnPreLaunchModule` (also covers skip-launcher).
3. **`PrepareRegionData`** (`src/launcher/settings.cpp`): now returns
   `project_root` without building an overlay (the signature is kept for compat).
4. **SDK — whole-file override** (`rexglue-sdk`):
   - `AfsFindModFileOverride()` (`afs.cpp`/`afs.h`): looks for a replacement of a
     whole file at `mods/<mod>/<filename>` or `mods/<mod>/us|eu/<filename>`.
   - `HostPathEntry::Open()` (`host_path_entry.cpp`): if a whole replacement
     exists, it opens the mod's file (so og_music and audio/sfd packs
     work without an overlay).

**Result**: the game reads `game:\us\...` directly from the assets folder (or from
the mounted region), and mods (per AFS entry and per whole file) are
served by the runtime from `mods/`. Zero duplication, zero staging. `active_region/`
removed from the build.

**⚠️ LESSON (AGENTS §13.6)**: when rebuilding the game (`cmake --build
out/build/win-amd64-release`), cmake OVERWRITES `rexruntime.dll` with the
version installed in `rexglue/bin` (stale, 11155968 B). After building the
game the correct SDK DLL must be copied again
(`rexglue-sdk/out/win-amd64/rexruntime.dll`, 11188224 B, with
`AfsFindModFileOverride`) into the build. Verified present in the build.

**SDK patches updated** in `github/patches/` (now 4 files:
`afs.cpp`, `afs.h`, `host_path_file.cpp`, `host_path_entry.cpp`). README
updated. Release **v1.0.2**.

### 14.1 🔴✅ FIX: DETECTING `assets/` IN THE STANDALONE PACKAGE (2026-08-20)

**Reported problem**: with the standalone package deployed as
`<folder>/dbz3.exe` + `<folder>/assets/{default.xex, us/, eu/}`, the launcher
looked for `default.xex` at the disk root (`D:\default.xex`) instead of
`assets/default.xex`. In the log: `Game directory: D:\` and
`Entrypoint XEX not found: D:\default.xex`.

**Root cause**: `OnConfigurePaths` (src/main.cpp) only detected `us/` next to the
exe or in the project root 3 levels up; with the assets in `assets/` neither
existed and the final fallback was `exe_dir.parent_path()` (= the disk root if the
exe is at the root of a drive).

**Fix applied** (src/main.cpp): helper `FindGameRoot(base)` that returns `base`
if `base/us` exists, or `base/assets` if `base/assets/us` exists. Priority:
1) next to the exe (exe_dir or exe_dir/assets), 2) dev project root (3 levels
up, or its assets/), 3) the exe's parent (or its assets/), 4) fallback exe_dir.

**Verified in game** (`D:\Budokai 3`, `assets/` layout): the log shows
`Game directory: D:\Budokai 3\assets`, `Mounted D:\Budokai 3\assets at
\Device\Harddisk0\Partition1`, `Loading XEX image: game:\default.xex` without error,
and the launcher shows (`launcher shown, waiting for Play`).

**Sync applied**: `src/main.cpp` → `github/`, `dbz3.exe`/`rexruntime.dll`
updated in `github/release-stage/`, `RELEASE_README.md` + `README.md`
document both layouts (us/ next to the exe or inside `assets/`).
The correct DLL (11188224 B, with `AfsFindModFileOverride`) was restored in the
build after rebuilding (cmake overwrites it with the stale version from
`rexglue/bin`).

### 14.2 🔴✅ MODDING TOOLKIT INTEGRATED INTO THE RELEASE PACKAGE (2026-08-20)

**Reported problem (test on the standalone package)**: running the release zip
(exe + DLLs only, without `mod center hd`), the **Model Swap** and
**Textures** tabs showed "Expected at: mod center hd/catalog_b3.cat" (the catalog
did not exist next to the exe), and the **Mods** tab said "no mods found...". The
user asked: (a) for the toolkit to work natively in the package,
(b) to be able to install a downloaded mod natively (the exe creating the
folder), and (c) an explanation of what is needed if the toolkit is missing.

**Solution — toolkit integrated into the release zip**:
- The release package now includes `mod center hd/` next to the exe with the
  RUNTIME subset: `swap_b3.py`, `texture_b3.py`, `catalog_b3.cat` and
  `tools/` (`xbcompress.exe`/`xbdecompress.exe` + their DLLs `MSVCR71.dll`,
  `MSVCP71.dll`, `xbdm.dll`). Added `MODDING_README.md` at the package root
  (how to install mods and use the toolkit) and a section in `RELEASE_README.md`.
- **⚠️ XDK DLLs**: `xbcompress/xbdecompress` are old XDK binaries
  that depend on `MSVCR71.dll`/`MSVCP71.dll` **and also on `xbdm.dll`**
  (without xbdm they give error 0xC0000135 = DLL not found). All three must be copied
  NEXT TO the .exe files (Windows looks for them in the exe's directory). The sibling
  B1 project already had them in its `tools/`.

**Code changes**:
1. **`mod_pipeline.cpp::ProjectRoot()`**: now also detects `probe/assets/us`
   and `probe/assets/eu`, so that in the standalone package (assets in `assets/`)
   the catalog and the scripts are found next to the exe.
2. **`launcher_state.cpp`**: the missing-catalog message is now clear and
   actionable (explains that `mod center hd/` must be next to the exe and the expected
   path); the **Mods** tab with 0 mods shows an **"Open mods
   folder"** button that creates `mods/` if it does not exist and opens it in Explorer (so
   the user can drop their downloaded mod there; the launcher lists and enables it by itself).
3. **`swap_b3.py` and `texture_b3.py`**: PORTABLE paths (work in dev and in the
   package):
   - `TOOLS_DIR` looks first at `HERE/tools` (package), then at the repo's XDK.
   - `DEFAULT_AFS` looks at `ROOT/assets/us` and `ROOT/us` (in the package `ROOT` = the
     exe's directory, because `mod center hd/` lives inside it).
   - Default `workdir` and `mods_root`: in the package they use the fixed TEMP and
     `exe_dir/mods` (the runtime serves mods from `exe_dir/mods`); in dev
     they use `out/build/...`.

**Verified end-to-end (`D:\Budokai 3`, assets/ layout)**: `swap_b3.py --origen
298 --dest 327` extracts Goten (XGTN_BODY), compresses (107006 B), applies the virtual
mid-insert (pad 110592) and generates the mod in `exe_dir/mods/...` without errors. The
launcher boots and loads (game dir, mount, XEX, "launcher shown"). The catalog
(183 characters) resolves at `exe_dir/mod center hd/catalog_b3.cat`.

**Sync applied**: `mod center hd/{swap_b3.py,texture_b3.py}` and
`src/launcher/{mod_pipeline.cpp,launcher_state.cpp}` → `github/`;
`dbz3.exe`/`rexruntime.dll` and the `mod center hd/` toolkit → `github/release-stage/`;
new `MODDING_README.md`; `RELEASE_README.md` updated. The correct DLL
(11188224 B) restored in the build after rebuilding. Release v1.0.2 updated
with the regenerated zip (includes the toolkit).

### 14.3 🔴✅ CRITICAL: `dbz1_diag_logging` could not be disabled → .bmp files in normal play (2026-08-20)

**Reported problem (critical)**: the game kept generating `black_*.bmp` and
`frontbuf_*.bmp` (30 files, ~7.5 MB each) **with nothing checked in Dev**.
This cluttered the folder and was unacceptable.

**Root cause (double)**:
1. **Propagating the flag by name did NOT work**: `src/launcher/settings.cpp`
   used `rex::cvar::SetFlagByName("dbz1_diag_logging", ...)` to turn the
   diagnostics off. BUT `dbz1_diag_logging` is defined ONLY in `rexruntime.dll`
   (`src/system/dbz1_diag_flags.cpp`), not in the exe. `SetFlagByName` resolves in
   the **exe's cvar registry**, where that flag does NOT exist → it returns `false`
   and **did nothing**. The runtime's flag stayed in its state (true if a
   session had left it on), and the GPU (rexgpu-xenos.dll, `command_processor.cpp`
   lines 2284/2372/2934/2986) wrote the .bmp files gated by
   `REXCVAR_GET(dbz1_diag_logging)`.
2. **The installed link lib was stale**: the exe links against
   `rexglue/lib/rexruntime.lib` (installed, 5471988 B, 09/08) which did **NOT export**
   `FLAGS_dbz1_diag_logging_storage_`. The correct SDK lib
   (`rexglue-sdk/out/win-amd64/rexruntime.lib`, 5978500 B) did. Using
   `REXCVAR_SET(dbz1_diag_logging, ...)` failed to link until the lib was copied.

**Fix applied** (`src/launcher/settings.cpp`):
- Added `REXCVAR_DECLARE(bool, dbz1_diag_logging)` (the symbol is exported
  by the runtime's `WINDOWS_EXPORT_ALL_SYMBOLS`). Now the exe links the accessor
  `FLAGS_dbz1_diag_logging_storage_()` and writes the **same storage** the
  GPU reads.
- Replaced `SetFlagByName("dbz1_diag_logging", ...)` with
  `REXCVAR_SET(dbz1_diag_logging, ...)` in the 3 places: `SetDevMode`,
  `SetDiagLogging` and `ApplyRuntimeSettingsToSdk`. With Dev and Diag off (default),
  `false && false` = **false** → the GPU generates no .bmp.
- Copied `rexglue-sdk/out/win-amd64/rexruntime.lib` → `rexglue/lib/rexruntime.lib`
  (so the link finds the symbol) and
  `rexglue-sdk/out/win-amd64/rexruntime.dll` → `rexglue/bin/rexruntime.dll`
  (so future builds use the correct DLL, see §13.6).

**Verified**: the exe compiles (links the symbol), and in the standalone package
`D:\Budokai 3` the game boots **without generating any .bmp** (0 files) with Dev
and Diag off. .bmp generation is gated exclusively by
`REXCVAR_GET(dbz1_diag_logging)` in `command_processor.cpp`.

**Sync applied**: `src/launcher/settings.cpp` → `github/`; `dbz3.exe` +
`rexruntime.dll` (11188224 B) → `github/release-stage/`. New **Release v1.0.3**
with the fix (zip regenerated).

### 14.6 🔴✅ P2.1 COMPATIBILITY: ISA BOOTSTRAP + AVX2/LEGACY VARIANTS (2026-08-25)

**Goal (HOJA_DE_RUTA_COMUNIDAD 2.1)**: CPUs without AVX2 (Intel pre-Haswell,
AMD pre-Excavator) crashed with `0xc0000142`/`0xc000001d` at boot because
the runtime was built with `-march=x86-64-v3`.

**Key finding that simplifies the design**: the game exe (`dbz3.exe`) is
built **without** `-march` (empty CMAKE_CXX_FLAGS = baseline x86-64). AVX2
lives ONLY in the SDK DLLs (rexruntime.dll, rexgpu-xenos.dll and FFX).
Verified in the build cache. So the core is ONE binary and only
the DLLs change per variant.

**Architecture (industry standard, UE5-like)**:
```
<release>/
  dbz3.exe               <- bootstrap (baseline x86-64, 44544 B, NO SDK)
  dbz3_avx2/dbz3_core.exe + rexruntime.dll(10934272 v3) + rexgpu-xenos.dll(6207488) + ffx dx12(5420544)
  dbz3_legacy/dbz3_core.exe + rexruntime.dll(10836480 v2) + rexgpu-xenos.dll(6162944) + ffx dx12(5414912)
  assets/ (or us/eu + default.xex), mods/, mod center hd/, docs
```
- **`src/bootstrap.cpp`** (`dbz3_bootstrap` target in CMakeLists): WinMain,
  `HasCpuX86V3()` = `__cpuid` leaf 7 EBX {AVX2 bit5, BMI1 bit3, BMI2 bit8} +
  leaf 1 ECX {FMA bit12, OSXSAVE bit27} + `_xgetbv(0)`&6 (gated by OSXSAVE).
  Launches `dbz3_avx2\dbz3_core.exe` or `dbz3_legacy\dbz3_core.exe`, passes the
  user's args, propagates the exit code, and shows a clear error window if the
  child is not found or fails with an exception code (>=0x80000000).
- **dbz3_core.exe = the current dbz3.exe** (baseline, SAME binary in both
  folders). In dev it is still launched directly (`out/build/.../dbz3.exe`).
- **SDK v2 build**: a second build dir `rexglue-sdk-0.10/out/build-win-vulkan-legacy`
  with `-march=x86-64-v2` and `-DREXGLUE_OUTPUT_DIR=.../out/win-amd64-legacy`
  (new cache var in the SDK's CMakeLists so as not to overwrite `out/win-amd64`).
  Produced rexruntime.dll v2 (10836480), rexgpu-xenos v2 (6162944),
  amd_fidelityfx_dx12 v2 (5414912). FFX is built from the SDK's FFX
  source (not just the signed prebuilt) → it needs its variant.
- **amd_fidelityfx_vk.dll** = the inherited 0.9 one, the same in both variants (the
  Vulkan backend is experimental; acceptable).

**Required path changes (in release the core lives in a subfolder)**:
- **Mods walk-up** (patch in `afs.cpp::AfsModsRoot` + `settings.cpp::ModsRoot`
  + `mod_pipeline.cpp::ModsOutDir`): they look for `mods/` from the exe going up to
  3 levels (release: `dbz3_avx2\` → `<root>\mods`). Unchanged in dev.
- `ProjectRoot()` already walked up (covers `mod center hd/` and `assets/`).
- `FindGameRoot` (main.cpp) already had the "exe's parent" fallback (§14.1) →
  resolves `<root>\assets` from `dbz3_avx2\` without changes.
- logs/toml/user_data stay in the variant folder (acceptable; the
  crash dialog shows the log path).

**⚠️ bootstrap without AVX2 in its own .text**: the target's explicit
`-march=x86-64` guarantees it (verified: the `-S` of bootstrap.cpp emits no AVX2). The
only AVX2/AVX instructions in the final exe belong to the **MSVC CRT's wmemcpy,
protected by dispatch** (`testb $0x20, [__isa_available]` + a `je` SSE2 fallback
at 0x1400050ac) — safe on legacy CPUs. The dynamic DLL is linked (imports
MSVCP140/VCRUNTIME140/api-ms-win-crt).

**Release script**: `tools/make_release.ps1` — assembles `github/release-stage`
(dbz3.exe bootstrap + dbz3_avx2/ + dbz3_legacy/ + mod center hd/ + mods/ +
docs) and generates the zip. Canonical source of the CRT DLLs = `github/` (msvcp140,
msvcp140_atomic_wait, vcruntime140, vcruntime140_1 from the VC redist; rexruntime
imports msvcp140_atomic_wait). New `README_PRIMER_ARRANQUE.txt` (layouts
+ ISA variants).

**Validated (local test, AVX2 CPU)**: bootstrap → spawns `dbz3_avx2\dbz3_core.exe`
(confirmed by process + log in `dbz3_avx2\logs`), the launcher shows
"launcher shown, waiting for Play"; the **legacy** variant also boots
directly (v2 DLLs OK). Pending: validate on a real non-AVX2 CPU (or force the
legacy path) and visual confirmation that the mods are listed from the root.
(Later superseded by v1.1.0: a single universal SSSE3 executable; see §14.21.)

**Sync**: `src/{bootstrap.cpp, launcher/{settings.cpp, mod_pipeline.cpp}}`,
`CMakeLists.txt`, `tools/make_release.ps1`, `patches/.../afs.cpp` (walk-up),
`RELEASE_README.md`, `README_PRIMER_ARRANQUE.txt`, `MODDING_README.md` →
`github/`. Release **v1.0.5** in `github/release-stage/` + zip (33112680 B).

### 14.7 🔴✅ P3.1 CONTROLS: KEYBOARD BY DEFAULT + CONFIGURABLE MAPPING + REAL DEADZONE/RUMBLE (2026-08-25)

**Goal (HOJA_DE_RUTA_COMUNIDAD 3.1)**: "keyboard/buttons do not respond in
game". Diagnosis: the SDK's MnK driver (keyboard→controller) already existed in full,
but `mnk_mode` was **false** by default and **nobody in dbz3 enabled it**
→ the keyboard did nothing. Also, the launcher's deadzone/rumble sliders
were a **placebo** (saved in the toml but they never reached the runtime: SDK
0.10 removed those cvars).

**What was done**:
1. **SDK patch `input_system.cpp`** (new file in `github/patches/`):
   - `REXCVAR_DEFINE_DOUBLE(deadzone, 0.1)` — applied in `InputSystem::GetState`
     to the merged state: the 4 stick axes are zeroed if their magnitude
     < `deadzone * INT16_MAX`. Covers XInput+SDL+MnK at the single exit point.
   - `REXCVAR_DEFINE_BOOL(rumble, true)` — in `InputSystem::SetState` accepts
     vibration without reaching any pad when OFF.
   - Both are exported by name; the exe writes them via `SetFlagByName` (the
     cvar registry lives in rexruntime.dll and is shared with the exe —
     verified: rexruntime.dll exports `SetFlagByName`/`RegisterFlag`/`Query`).
2. **Launcher `settings.{h,cpp}`** — new cvars persisted in dbz3_user.toml:
   - `dbz3_mnk_mode` (**default TRUE** → the keyboard works out of the box on PC),
     `dbz3_mnk_mouse` (mouse → right stick), `dbz3_input_backend`
     ("xinput"/"sdl", default xinput).
   - `dbz3_keybind_*` (24 wrappers: a,b,x,y,lt,rt,lb,rb,ls 4d+press, rs 4d+press,
     dpad 4, back, start, guide) with defaults = SDK 0.10's (start fixed
     to "Return" so the X key does not duplicate pause).
   - `ApplyUserSettingsToSdk` now propagates: `input_backend`, `deadzone`,
     `rumble`, `mnk_mode`, `mnk_mouse` and the 24 `keybind_*` to the runtime.
3. **Launcher `launcher_state.cpp`** — expanded Input tab:
   - "Controller backend" selector (XInput/SDL) with a warning that SDL can
     hang with RTSS/OBS (which is why xinput is the default).
   - Deadzone slider + rumble checkbox (now with a real effect).
   - "Enable keyboard/mouse emulation" + "Use mouse for right stick" checkboxes.
   - "Keyboard (MnK) mapping" section: 24 text fields (helper `DrawKeybind`,
     format `Key`, commas = alternatives, `Shift+/Ctrl+/Alt+` = modifiers).
   - Reset to defaults restores the new cvars.
4. **Detail verified**: the exe links `rex::runtime` (the DLL) → its calls
   to `rex::cvar::SetFlagByName` resolve to rexruntime.dll's export
   → shared registry. The §14.3 warning about `SetFlagByName` was from
   the 0.9/prebuilt era; in 0.10 the by-name path is the right one (documented
   in `cvar.h`: "Cross-DLL access path").

**Built and smoke test OK**: rexruntime.dll 10940928 B (deadzone/rumble patch),
dbz3.exe 17461248 B, "launcher shown, waiting for Play" without errors. FFX v3
restored to 5420544 (the v1.0.5 release one; an SDK rebuild regenerated it as
5418496 and it was preferred not to change a binary the task did not touch).

**⚠️ PENDING IN-GAME TEST (user)**: (a) the keyboard emulates the controller
by default (menus + battle), (b) remap keys in the Input tab and check they
apply, (c) an XInput controller still works (deadzone/rumble). In the release
package `dbz3_avx2/` and `dbz3_legacy/` must be regenerated with the new
dbz3_core.exe and rexruntime.dll.

**Sync**: `src/launcher/{settings.{h,cpp}, launcher_state.cpp}` and
`patches/.../src/input/input_system.cpp` (new) + `patches/README.md` (10
files) → `github/`.

### 14.8 🔴✅ P2.3/P2.2 PERFORMANCE: REAL FRAME PACING + PER-GPU QUALITY PRESETS (2026-08-25)

**Goal (HOJA_DE_RUTA_COMUNIDAD 2.3 and 2.2)**: "the game runs sped up" and
making integrated GPUs playable (automatic presets).

**Key finding of 2.3 — guest pacing in 0.10 is done by `vsync`, not
`frame_cap`**:
- SDK 0.10 **removed 0.9's `frame_cap` cvar**. Verified: it does not exist anywhere
  in the SDK source → the launcher's `SetSdkInt("frame_cap", cap)` failed
  silently (placebo).
- The guest's real pacing is `GraphicsSystem`'s `vsync` worker
  (`graphics_system.cpp`): with `vsync` ON the guest's vblank runs at
  `1/video_mode_refresh_rate` (60 Hz) → the game at its correct speed. With
  `vsync` OFF the vblank runs at ~1000 Hz (1 ms interval) → **the game logic
  runs ~16x faster = the "sped-up game"** of the reports.
- `video_mode_refresh_rate` only *reports* the mode (xboxkrnl_video.cpp); it does not pace.
- **Fixes**:
  1. **vsync forced to true in the game** (`ApplyRuntimeSettingsToSdk`): the guest
     MUST run at 60 Hz; if the user had it off it is forced with a warning.
     The **"VSync" checkbox was removed** from the launcher and the Dev menu (it was a
     placebo/counterproductive) → it now shows "Game speed: fixed 60 FPS".
  2. **REAL `frame_cap` restored** (patch `d3d12_presenter.cpp`): cvar
     `frame_cap` (0=no limit) + presentation throttle in
     `PaintAndPresentImpl` (sleep until the frame_cap FPS slot with
     `std::chrono::steady_clock` + `rex::thread::Sleep`; serialized painting →
     safe file-scope timestamp). It only limits the host presentation rate
     (30 = half load on integrated GPUs); it does NOT touch the guest's vblank.
  3. **`dbz3_frame_cap` default 0 → 60** (fresh installs get correct
     pacing; ResetToDefaults already set 60 — now coherent).
  4. The `SetSdkInt("frame_cap", ...)` propagation now ONLY in game mode
     (`for_game`); the launcher keeps its ImGui repaints uncapped.

**2.2 — Quality presets + GPU detection (the practical option; OpenGL/D3D11 NOT
viable, see HOJA_DE_RUTA §2.2)**:
- **DXGI detection** (`settings.cpp`): `DetectGpuName()`/`DetectGpuTier()`
  enumerate the first non-software adapter (`CreateDXGIFactory1` +
  `EnumAdapters1`, description + `DedicatedVideoMemory`), linked with
  `#pragma comment(lib, "dxgi.lib")`. Tier: 0=low, 1=medium, 2=high. Intel
  iGPU (without "Arc") never auto above medium. RTX 4070 SUPER → tier 2.
- **Preset `dbz3_quality_preset`** (auto/low/medium/high/ultra/manual):
  - `auto` → detects the GPU and applies the recommended profile at every boot.
  - Profiles: **low** (1x, no MSAA, aniso off, bilinear), **medium** (1x, no
    MSAA, 4x aniso, FSR), **high** (1x, MSAA on, 16x aniso, FSR),
    **ultra** (2x, MSAA on, 16x aniso, FSR — manual only, never auto).
  - **Migration**: an existing toml WITHOUT `dbz3_quality_preset` is migrated to
    "manual" (LoadUserSettings is called twice: first in OnConfigurePaths
    BEFORE logging is active — the migration runs there — and then in
    OnPreSetup). So a user with a hand-made config never sees it changed.
  - Fresh install (no toml) → "auto" → the launcher applies detection.
- **UI (Video tab)**: line "GPU: <name> - detected tier: <X>", combo
  "Quality preset" (Auto/Low/Medium/High/Ultra/Manual), "Frame cap" slider
  now REAL with a 30 FPS hint for integrated GPUs, text "Game speed: fixed 60".
  ResetToDefaults adds `dbz3_quality_preset=auto`.
  (Later, v1.2.6: presets renamed auto/performance/balanced/quality/manual and
  none of them raises the internal scale.)

**Verified**: rexruntime.dll 10944000 B (`frame_cap` cvar present), dbz3.exe
17479168 B, smoke test OK. With the user's toml: `preset=manual` (2x, no
changes). Without toml: `preset=auto` → tier 2 → `1x + fsr` (High). FFX v3
restored (5420544).

**⚠️ PENDING**: (a) test the frame cap (60 and 30) in game and the auto preset on
a machine with an integrated GPU; (b) Tracy profiling of the D3D12 path (build
win-amd64-tracy) stays as an optional fine-optimization task — it needs a
play session for real data.

**Sync**: `src/launcher/{settings.{h,cpp}, launcher_state.cpp}`,
`src/ingame/menu.cpp`, `patches/.../src/ui/d3d12/d3d12_presenter.cpp` (new) +
`patches/README.md` (11 files) → `github/`.

### 14.9 🔴✅ CLOSE/BOOT BUGS + LAUNCHER I18N (2026-08-25 night)

**User reports**: (a) Alt+F4 in game → "Not responding" until the process is
killed; (b) the launcher sometimes opened black + "Not responding" and appeared
"after a while"; (c) presets "not visible"; (d) the Language selector should
translate the WHOLE launcher (it was "Spanglish"). **ROOT CAUSE OF (b) FOUND AND
REPRODUCED (log markers)**: boot hung in
`InputSystem::AttachWindow` → `SDLInputDriver::OnWindowAvailable` →
`CallInUIThreadSynchronous` → **`SDL_InitSubSystem(SDL_INIT_GAMEPAD)`** (the
classic hang with RTSS/OBS). The user has `dbz3_input_backend = "sdl"` in
their toml. **Fix**: ASYNC SDL init (a `std::thread` does the SDL init in the
background; atomic flags; detached thread). The launcher goes from hanging to
"launcher shown" in **1.6 s**. 0.9's `CallInUIThreadSynchronous` timeout fix
was NOT ported to 0.10 (fence.Wait without a timeout) — with the async init it no longer
blocks boot; noted as a follow-up.

**Fix (a) Alt+F4**: the user's log (dbz3_003) confirmed that Alt+F4 DID reach
`Dbz3App::OnWindowCloseRequested` ("Window close requested") but hung
afterwards (it never reached `OnClosing`). **Fix in `src/main.cpp`**:
`OnWindowCloseRequested` now does `rex::FlushLogging()` + `std::_Exit(0)`
immediately (same hard exit as OnClosing; TerminateTitle/PerformClose/
focus loss could block with lagging guest threads). Closing the game (X or
Alt+F4) always exits instantly.

**Fix (c) visible presets**: the Video tab now shows "Active: <preset> →
<scale>x, MSAA, aniso, effect" under the preset combo → "auto" is no longer a
black box (it applies in memory and re-evaluates at every boot).

**Fix (d) launcher i18n** (ES/EN, the rest → EN):
- New `src/launcher/i18n.{h,cpp}`: `dbz3::i18n::SetLanguage(id)` +
  `T(es, en)` returning the string according to `dbz3_language` (5=ES, rest=EN).
- `launcher_state.cpp`: **172 strings** wrapped with `T(es,en)` (banner, tabs,
  Video/Upscaling/Audio/Input/Mods/Model Swap/Textures/Dev, tooltips, dialogs).
  `OnDraw` calls `SetLanguage(Language())` every frame → a language change
  applies instantly. The localized combo arrays were made non-static
  (with `static` they would capture the language only once).
- `CMakeLists.txt`: added `src/launcher/i18n.cpp`.
- The Video tab renames the combo to "Launcher and game language" and the
  help explains that it translates the whole launcher.

**SDK patched (rexruntime, avx2+legacy)**: `src/ui/presenter.cpp`
(`WaitForUITickFromUIThread` with `wait_for(50ms)` → the UI thread NEVER blocks
waiting for vblank → no more black window + it always processes messages) and
`src/input/sdl/sdl_input_driver.{h,cpp}` (async SDL init). New patches in
`github/patches/` (README → 14 files). **Binaries**: dbz3.exe 17488896 B,
rexruntime.dll 10945536 B (avx2) / 10847232 B (legacy). FFX validated intact
(identical hashes).

**Verified**: launcher "shown" in 1.6 s (it used to hang 25 s+), the 3 input
drivers pass AttachWindow instantly, the game compiles and links, FFX intact.
Alt+F4 validated by static analysis (the automated test cannot simulate a real
Alt+F4: SDL intercepts the key, not a posted SC_CLOSE; the user will
validate in game). **Release v1.0.7** pending packaging with these
binaries.

**Sync**: `src/{main.cpp, launcher/{launcher_state.cpp, i18n.{h,cpp}}}`,
`CMakeLists.txt`, `patches/.../{presenter.cpp, sdl_input_driver.{h,cpp}}` +
`patches/README.md` (14 files), `RELEASE_README.md` → `github/`. NOT uploaded to
GitHub (general plan still in progress).

### 14.10 🔴✅ IT/DE/FR I18N + COMPACT UI WITHOUT SCROLLBARS + BOOT MARKER (2026-08-26)

**User reports**: (a) the language selector only translated ES/EN (IT/DE/FR
fell back to English "for some reason"); (b) the launcher still takes a while to go from
black screen to launcher; (c) the UI does not fit in the window (scroll bars);
(d) Alt+F4 now works ✅.

**Fix (a) complete EN/ES/IT/DE/FR i18n** (`src/launcher/i18n.{h,cpp}`):
- TABLE design, not per call site: `T(es,en)` keeps its signature; internally
  it looks up in `kTable[]` (161 entries) the translation for `dbz3_language`
  (3=DE, 4=FR, 5=ES, 6=IT; rest→EN, including 2=Japanese). The ES key is the
  **EXACT runtime string** (multi-line concatenated literals count
  as a single key; generated with a Python script that parses the 172 call
  sites of `launcher_state.cpp`, `extract_i18n.py`/`gen_i18n.py` in %TEMP%).
- Translations: 483 strings (161×3) written by hand (IT from ES, DE/FR from
  ES/EN), UTF-8 (clang compiles it fine). Strings with `\n`/`\\` are emitted
  verbatim in the key and escaped in the translations.
- The language combo still lists the game's 6 languages; the launcher only
  has EN/ES/IT/DE/FR (Japanese→EN).

**Fix (b) compact UI without scrollbars** (`launcher_state.cpp`):
- Tight global style: WindowPadding (16,16)→(12,8), FramePadding
  (10,6)→(7,4), ItemSpacing (10,8)→(7,4), smaller CellPadding/ScrollbarSize.
- Banner: font scale 1.5→1.3, separators reduced.
- **Video tab in 2 columns** (BeginChild left/right): left =
  Image quality + Language; right = Display + Engine + Gamma. The long help texts
  (preset, scale, MSAA, frame cap, VRR, monitor, Vulkan) move to
  `SetTooltip` on hover (always `SetTooltip("%s", i18n::T(...))`
  to avoid triggering -Wformat-security).
- **Input tab: the 24 keybinds in a 3-column grid** (vertical before).
  Backend/MnK/mouse help moved to tooltips.
- Dev tab: 4 help texts to tooltips. Mods/ModelSwap/Textures keep their internal
  scroll (naturally long lists).
- Result: all the settings tabs fit in the 1280x720 window without bars.

**Fix (c) slow boot diagnosis** (`patches/.../d3d12_presenter.cpp`):
- Log of the D3D12 presenter's first `Present`: `dbz3: first present OK
  (device/swapchain init + first paint took X ms)` → with the log timestamps
  (which already have the time), the user's log shows how long the black screen
  lasts (window created→first frame) on THEIR machine. On mine it is ~7 ms.
  PENDING: read the value on the user's machine to know whether the
  bottleneck is the D3D12/swapchain init of the first paint (then: early init
  or a hidden window until the first frame) or something earlier.

**Binaries**: dbz3.exe 17517568 B, rexruntime.dll 10947584 B (avx2) /
10849792 B (legacy) with the marker. The avx2 DLL copied to the build and to
`rexglue/bin` (avoid the §13.6 stale one). FFX intact.

**Sync**: `src/launcher/{i18n.{h,cpp}, launcher_state.cpp}` +
`patches/.../d3d12_presenter.cpp` + `patches/README.md` → `github/`. NOT uploaded
to GitHub. **Release v1.0.8** pending packaging.

### 14.11 🔴✅ LANGUAGE THAT DRIVES THE GAME + FOOTER WITH PLAY ALWAYS VISIBLE (2026-08-26)

**User reports**: (a) the language selector only affected the launcher
(they expected it to also drive the game's text); (b) the right scroll bar
was still there in Video/Audio/Dev and "PLAY" was not visible up front; (c) make the
launcher more user-friendly (research good practices).

**Fix (a) REAL language → game** (`patches/.../xam_info.cpp`, new patch #10):
- The guest picks its language via `XGetLanguage`. `XGetLanguage_entry` returned
  a fixed English (based on region). It now returns `REXCVAR_GET(user_language)`,
  the cvar the launcher ALREADY propagated from `dbz3_language`
  (`ApplyUserSettingsToSdk`: `REXCVAR_SET(user_language, Language())`).
- ⚠️ Scope: `user_language` is defined in `xam_user.cpp` BEFORE the namespaces
  open → its accessor is GLOBAL. The `REXCVAR_DECLARE` in `xam_info.cpp`
  must also go outside `namespace rex::kernel::xam` (otherwise: link error
  `undefined symbol: rex::kernel::xam::FLAGS_user_language_storage_`).
- **Verified by disassembly**: the new DLL has `XGetLanguage_entry` =
  `sub rsp,28; call FLAGS_user_language_storage_; mov eax,[rax]; add rsp,28; ret`.
  The launcher's selector now controls the game's text.

**Fix (b) scrollbars + invisible PLAY** (`launcher_state.cpp`):
- **ROOT CAUSE**: the settings tabs used `BeginChild(..., ImVec2(0,0))`
  (they fill ALL the remaining height) → the footer was drawn OUTSIDE the window →
  the window gained a scroll bar and PLAY ended up below the fold.
- **Fix**: ALL tabs reserve the footer's height with
  `ImVec2(0, -kFooterHeight)` (kFooterHeight = 76) → the footer is always visible.
- **Verified by geometry logging** (temporary debug, later removed):
  `win_scroll_y=0`, `video_left/right scroll_y=0`, and **PLAY rect y=[670,712]
  in a 720 window** → no bars and PLAY in view.

**Fix (c) user-friendly** (applying launcher good practices researched
online: PLAY = primary action always visible and high-contrast; grouping by
intent; feedback on what is about to launch; discreet secondary utilities):
- **Redesigned footer**: summary line "Start: <region> - <backend> - <N>x -
  <effect> - <language>" + region combo (moved from the Mods tab, now
  always visible with a tooltip) + secondary buttons [Reset][Save] +
  **big GREEN PLAY (300x42, primary style)** on the right.
- The region selector was removed from the Mods tab (no duplicate any more).
- The language combo tooltip clarifies it affects the launcher AND the game.
- Fixed a double-mojibake string (`pequeÃƒÂ±a` → `pequena`, byte-level).
- New strings in the i18n table: "Start: ..." and the language tooltip
  (added by hand in i18n.cpp, which is GENERATED — regenerate with the script if
  more strings are touched).

**Binaries**: dbz3.exe 17519104 B, rexruntime.dll 10947584 B (avx2) /
10849792 B (legacy) with the XGetLanguage patch. FFX intact (avx2 5420544 A20438,
legacy 5414912 5FE146). avx2 DLL copied to the build + `rexglue/bin`.

**⚠️ LESSON**: when rebuilding the avx2 SDK, the FFX in `rexglue-sdk-0.10/bin/`
is regenerated (5415424, different from the validated one). Do NOT copy it to the build: the build
and the release use the validated FFX (5420544). The FFX in the SDK's `out/win-amd64`
is still the validated one (the regeneration goes to `bin/`, not to `out/`).

**Sync**: `src/launcher/{i18n.{h,cpp}, launcher_state.cpp}` +
`patches/.../{xam_info.cpp}` + `patches/README.md` (15 files) → `github/`.
NOT uploaded to GitHub. **Release v1.0.9** pending packaging.

### 14.12 🔴✅ THE EU/PAL XEX IS NOT COMPATIBLE + DETECTION AND BLOCKING (2026-08-26)

**User report**: "a lot of people reported problems with the `.xex` when
using the EU one; in previous conversations it was said to be the same as the USA one".
Request: verify that this is 100 % fixed.

**EMPIRICAL VERIFICATION (real guest boot, not just hashes)**:
- `yae3_xenon.xex` (US/NA) vs `yae3_xenon_eu.xex` (EU/PAL): same size
  (4890624 B), same title id (0x82) and media id (0xFF030000), SAME XEX2
  headers, same image layout reported by the runtime (code=82080000-
  8230EC00, image=82000000-826D0000) — but **different MD5** (A53E... vs
  C37E...). The raw bytes are encrypted with each region's key → do not
  compare them raw.
- **The EU xex can NOT boot in this port**: with `dbz3_skip_launcher`,
  `OnPostLaunchModule` is reached but the guest dies instantly with
  `XThread::Execute - No function registered at 8221C570` (the same address both
  with EU assets and with US assets → the failure is 100 % the EU executable's).
  Cause: the **codegen (recompiler, 44 recomp files) was generated ONLY from the US
  xex**; the decrypted EU code differs (different call graph) and calls
  addresses the recompiler's function table does not cover.
- **The US xex boots the guest without error** (control), with the EU region and any
  language via the launcher (us/eu mount + `user_language`). → An EU user does
  not lose anything by using the US xex: the PAL region (`eu/` assets) and the language are
  handled by the launcher.

**Fixes applied**:
1. **`FindGameRoot` accepts `eu/`** (`src/main.cpp`): before it only accepted `us/`
   → a layout with ONLY `eu/` (EU user without a us folder) failed
   auto-detection and fell into "Entrypoint XEX not found" at Play. Now it accepts
   `base/eu` and `base/assets/eu` (consistent with `IsValidGameDataDir` and the banner).
   (This was the secondary bug that EXPLAINED part of the "EU" reports.)
2. **EU xex detection in the launcher** (`settings.{h,cpp}` +
   `launcher_state.cpp`): new `XexStatus` (kMissing/kUs/kEu/kUnknown) +
   `CheckDefaultXex(root)` = MD5 of `default.xex` (CryptoAPI, cache by
   path+size+mtime so as not to re-hash the ~4.9 MB every frame; fast reject by
   size). Known hashes: US `A53E324B5D2A65EBCBF648E4F85A7271`, EU
   `C37EB979B762DA0AB5B8C9BA8037CE4E` (the disc ones are fixed per region).
   - Banner: EU xex → **clear red message and Play BLOCKED** (instead of the
     cryptic crash); unknown xex (modified/other region) → informative **amber note**
     without blocking; US → normal green.
   - Guard also in `LaunchModule` with `skip_launcher` (dev path): if the xex
     is EU, error + clear MessageBox, the guest does not boot.
3. **Docs**: RELEASE_README + README_PRIMER_ARRANQUE explain "ALWAYS use the
   US/NA `default.xex` (`yae3_xenon.xex`); the EU/PAL one does not boot; region and
   language are chosen in the launcher".

**Verified**: with the EU xex + skip_launcher → log `skip_launcher with EU/PAL
default.xex - the recompiled port only supports the US/NA executable` and it does NOT
create the guest; with the US xex → `OnPostLaunchModule - guest thread created and resumed`
(no error); the launcher with the EU xex shows without a crash (banner active).
`dbz3.exe` 17528320 B.

**IMPORTANT NOTE (the truth of the matter)**: "the EU xex is the same as the USA one" is
**FALSE** at the binary and code level — the port is only recompiled from
US. What IS correct: **an EU xex is not needed** because region and
language are handled by the launcher on top of the US xex. With the US xex + eu region +
chosen language, the EU user plays 100 % (PAL assets + text in their language).
(Superseded by §14.13: a second recompilation made the EU xex work.)

**Sync**: `src/{main.cpp, launcher/{settings.{h,cpp}, launcher_state.cpp,
i18n.cpp}}` + `RELEASE_README.md` + `README_PRIMER_ARRANQUE.txt` → `github/`.
NOT uploaded to GitHub. **Release v1.0.10** pending packaging.

### 14.13 🔴✅ THE EU/PAL PORT NOW WORKS — SECOND RECOMPILATION (2026-08-26)

**User report (after §14.12)**: "the EU xex should be 100 % compatible, we
cannot promise US or EU and not deliver it". **Decision: build
the EU xex port as a second recompilation** (not just block it). Result:
**both executables work** — the launcher picks the right core by itself.

**KEY FINDING: the EU xex is a different build at the code level** (not just
bytes): the codegen analyzes the EU one but with **DIFFERENT function addresses**
(partition JSON: US partition 3 @0x820800A8 vs EU @0x82080158). The title id is the
SAME (4E4D0856) in both → the discriminator is the **MD5** (US `A53E...`, EU
`C37E...`; the raw bytes are encrypted per region).

**EU port pipeline (all validated)**:
1. **EU codegen converges** (`dbz3_manifest_eu.toml` + `dbz3_config_eu.toml`):
   `rexglue codegen` on `yae3_xenon_eu.xex` → `generated_eu/` (prefix
   `dbz3_eu_*`). 95 functions (same count as US). `dbz3_config_eu.toml` =
   the US one + EU adjustments:
   - `0x82097F08` without `size 0x10` (EU branches beyond it);
   - 4 name-only entries (`0x821ECA98, 0x82097EA0, 0x8213EB00, 0x821ED5C8`) for the
     5 unresolved calls;
   - ⚠️ additional entries must go INSIDE `[functions]` (appending them
     after `[[switch_tables]]` puts them in the switch table → no effect);
   - unresolved conditional branches → **declare with the partition range's
     size** (`0x8213E834 size 0x1CC`, `0x82296500 size 0x288` + remove
     `0x82296528` from the US config); the **bulk name-only of 298 candidates does NOT
     work** (chaotic gap-fill → new unresolved ones at 0x82303xxx);
   - functions via data pointers (dispatch) → declare them one by one (0x822A5AE0
     size 8, 0x82290F18 size 0xF8, cluster 0x8228B8D8/E0/F0/B948,
     handler table 0x822922B8..0x82292300, 0x821F9D40 size 0x18).
2. **CMake variant** (`CMakeLists.txt`): `DBZ3_GENERATED_DIR` (cache,
   default `generated`). EU build: `cmake -B out/build/win-amd64-release-eu
   -DDBZ3_GENERATED_DIR=generated_eu` (same compilers/prefix path as
   US). `main.cpp` includes `generated_eu/dbz3_eu_init.h` if `DBZ3_EU_VARIANT`
   (a define set by CMake); `hooks.cpp` is excluded from the EU build (its US
   hooks sub_820F2280/sub_820BB938 do not exist in EU) and `hooks.h` is guarded with
   `#ifndef DBZ3_EU_VARIANT`.
3. **EU boot validated**: the EU core with the EU xex boots the guest and **runs
   the real game** (reads `data_eng.afs`, `data_cmn.afs` 3983-3985, `data_yah.afs`;
   60 s stable without FATAL). Iterating over unregistered functions resolved until
   the guest was stable. **The SDK runtime is game-agnostic** (same DLLs
   for both cores).
4. **Variant-aware detection** (`settings.h XexIsExpected()` +
   `launcher_state.cpp` banner + `main.cpp` skip_launcher guard): each core only
   boots ITS xex; with the other one it blocks it with a clear message (red banner /
   MessageBox). i18n messages added for both cases.
5. **Bootstrap dispatch** (`src/bootstrap.cpp`): now also detects the xex
   (`DetectXex` MD5 CryptoAPI, looks for `default.xex` in exe_dir, exe_dir/assets,
   parent, parent/assets) → launches `dbz3_eu_avx2|legacy` if EU, `dbz3_avx2|
   legacy` if US. **Validated end-to-end**: EU xex → dbz3_eu_avx2 → EU guest
   boots; US xex → dbz3_avx2 → US guest boots.
6. **FindGameRoot priority fix** (`main.cpp`): the "3 levels up" fallback
   found the dev project root (with `us/` and the US `default.xex`) BEFORE the
   release's `assets/` when the core runs from `github/release-stage/
   dbz3_eu_avx2` → the EU core classified the EU xex as US. Reordered: exe →
   **parent → 3-up (dev)**. Works for dev AND release.
7. **Packaging** (`tools/make_release.ps1`): 4 variants (dbz3_avx2/legacy =
   US core, dbz3_eu_avx2/legacy = EU core; same SDK DLLs). Zip v1.0.10
   (66.4 MB). (Later merged into a single dual-region exe; see §14.16.)

**Useful diagnostics**: `InvalidFunctionTrap` (rexglue-sdk-0.10/src/system/
function_dispatcher.cpp) with the env var `DBZ3_COLLECT_UNREGISTERED` → logs each
unregistered function to `dbz3_unregistered.txt` and continues (mass collection,
although the guest corrupts quickly → one per boot). EU image dump:
env `DBZ3_DUMP_IMAGE` (main.cpp) writes the decrypted image so function
pointers (u32 BE → code) can be scanned — it served to find the dispatch targets.

**Binaries**: US core 17529344 B, EU core 17508864 B, rexruntime 10951168 B
(avx2) / 10849792 B (legacy), bootstrap 46592 B. FFX validated intact
(avx2 5420544 A20438, legacy 5414912 5FE146).

**⚠️ PENDING (user)**: validate the EU core **in game** (menus + battle).
Boot is stable, but deeper paths (battle/events) could reveal
more unregistered functions (use `DBZ3_COLLECT_UNREGISTERED` to
collect them) and the US hooks (miscompiled dispatches) could have
EU equivalents to discover. If something crashes, iterate `dbz3_config_eu.toml`
and re-codegen.

**Sync**: `src/{bootstrap.cpp, main.cpp, hooks.h, launcher/{settings.{h,cpp},
launcher_state.cpp, i18n.cpp}}`, `CMakeLists.txt`, `dbz3_manifest_eu.toml`,
`dbz3_config_eu.toml`, `tools/make_release.ps1`, `RELEASE_README.md`,
`README_PRIMER_ARRANQUE.txt`, `patches/.../function_dispatcher.cpp` (collection
of unregistered functions) + `patches/README.md` → `github/`. NOT uploaded to
GitHub. `generated_eu/` is NOT uploaded (derived code). **Release v1.0.10**
packaged and verified (EU dispatch end-to-end OK).

### 14.14 🔴✅ v1.0.6 — FIX FOR THE CLOSE AT THE INTRO (0xC0000409 / 0x82292A58) (2026-08-26)

**User reports (pattern):** "they reach the game's intro and then it
closes". Errors: **0xC0000409** (several) and *"Call to invalid or unregistered
function at guest address **0x82292A58**"*. One more user reported that
disabling V-Sync makes the game run super fast (derived task, see below).

**ROOT CAUSE (1) — unregistered function in the EU intro**: `0x82292A58` is a
**vtable dispatch thunk** (family `lwz r11,0x48(r3); addi r3,r11,0x40;
lwz r11,0x40(r11); lwz r11,N(r11); mtctr r11; bctr`, size 0x18). The EU guest
calls it INDIRECTLY (via a vtable data pointer) during the
intro, and since it is not compiled → `InvalidFunctionTrap` → `REX_FATAL` →
`std::abort()` → **0xC0000409** (in UCRT, abort = fastfail = 0xC0000409). It is the
SAME crash for both reports (the trap message + the exception code).

**REPRODUCTION (without depending on the user)**: the intro plays without input
(the guest advances by itself to the title/intro after ~90 s). With the EU core in a
test folder (EU core + `assets/{default.xex EU, eu/}` + `dbz3_user.toml` with
`dbz3_skip_launcher=true`) the log gives exactly the FATAL:
`[FATAL] Call to invalid or unregistered function at guest address 0x82292A58`.

**⚠️ Diagnosis**: the collector path (`DBZ3_COLLECT_UNREGISTERED=1`) does NOT
work: with the env var set the boot dies with `std::terminate` before the
intro (boot quirk, see below). The productive path is static: **scanning
vtable thunks** in the decrypted image (`dbz3_eu_image.bin` via
`DBZ3_DUMP_IMAGE=1`; capstone PPC BE) and registering them with the exact size.

**FIX (1)**: `dbz3_config_eu.toml` + `0x82292A58 = { name = "rex_sub_82292A58",
size = 0x18 }` (the sibling `0x82292A40` with offset +8 WAS registered; so were the
3 thunks of the 0x44 family at 0x82292500/528/550). EU re-codegen
("5 written, 90 unchanged") + rebuild. **VALIDATED**: the EU core passes the intro
(210 s without FATAL; before it crashed at ~90 s). The US core also passes (210 s).

**ROOT CAUSE (2) — intermittent `std::terminate` at boot (another
0xC0000409)**: sometimes, right after `OnPostLaunchModule`, the UI thread dies with
`std::terminate called!`. Diagnosed with a stack (`RtlCaptureStackBackTrace`
in the terminate handler): the exception escapes the deferred lambda of
`LaunchModule` (`ExecutePendingFunctionsFromUIThread` invokes the function, and it
throws there). Intermittent (~1/3 under load, 0/6+ cold).
**The exact `throw` could not be located** (it did not reproduce with the try/catch in place).
**Measures applied**: (a) `rex_app.cpp` (compiled into the EXE from
`rexglue/share/rexglue/rex_app.cpp`, NOT into rexruntime.dll — check with the
string "Failed to launch module" in the exe) — the `LaunchModule` lambda is
wrapped in a try/catch that logs `e.what()` and rethrows; (b) the
`std::terminate` handler in main.cpp logs the thread's stack. So, if a user
hits it, the log will have the exact message.

**V-SYNC (task for the future 1.0.6 EX, NOT fixed in 1.0.6)**: report that
disabling V-Sync speeds the game up. In 1.0.6 the correct sync is forced
at boot (vsync=true, see §14.8), but the open task is to
find WHICH setting/option lets it be disabled (an internal guest menu? a
residual cvar?) and harden it. Documented in RELEASE_README "Known bugs".
(Fixed in v1.0.9, see §14.17.)

**1.0.6 binaries**: US core 17532416 B, EU core 17511936 B, rexruntime
10951168 B (avx2, with trap+collect, no functional changes) / 10849792 B
(legacy), FFX validated intact (avx2 5420544 A20438, legacy 5414912 5FE146).
Bootstrap unchanged.

**⚠️ Build constraint (repeated)**: when rebuilding the game, cmake
overwrites `rexruntime.dll` with the stale version from `rexglue/bin` → copy
`rexglue-sdk-0.10/out/win-amd64/rexruntime.dll` to the build again after building.

**Sync**: `src/main.cpp`, `src/launcher/…` (no changes), `dbz3_config_eu.toml`,
`AGENTS.md`, `RELEASE_README.md` → `github/`. The edited `rex_app.cpp` (try/
catch in LaunchModule) is synced to `rexglue/share/rexglue/rex_app.cpp` and,
if distributed as a patch, to `github/patches/rexglue-sdk/src/ui/rex_app.cpp`.
NOT uploaded to GitHub. **Release v1.0.6** packaged and uploaded (see §14.15).

### 14.15 🔴✅ RELEASE v1.0.6 — UPLOADED TO GITHUB (2026-08-26)

**Sync**: `src/main.cpp`, `dbz3_config_eu.toml`, `AGENTS.md`, `RELEASE_README.md`,
`patches/rexglue-sdk/src/ui/rex_app.cpp` (new, #12 in patches/README → 17
files) → `github/`. Commit `cd4a368`, push to origin/master, **tag v1.0.6**.

**Release v1.0.6** created on GitHub (Latest):
https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/releases/tag/v1.0.6
Zip `DBZ-Budokai-3-HD-Collection-v1.0.6.zip` (66428050 B) with the 4 variants
(US/EU × avx2/legacy). Cores: US 17532416 B, EU 17511936 B. FFX validated
(avx2 5420544 A20438, legacy 5414912 5FE146). rexruntime avx2 10951168 (trap +
collect), legacy 10849792.

**Final package smoke test**: the packaged EU core boots and runs 100 s without
FATAL (the full intro validated with 210 s). Changelog in the release: fix for the
close at the intro + stronger diagnostics + V-Sync noted for 1.0.6 EX.

**PENDING (user)**: validate 1.0.6 in game (that the EU intro passes). If any
user reports 0xC0000409 again, the log now carries "LaunchModule deferred
threw std::exception: <msg>" + "terminate stack[...]" → solve the throw.

### 14.5 🔴✅ P1 FIRST USE: VALIDATION BANNER + FOLDER SELECTION + CRASH WINDOW (2026-08-25)

**Goal (HOJA_DE_RUTA_COMUNIDAD P1.1/P1.2)**: a user with misplaced assets
should NOT fall into the "Entrypoint XEX not found" crash, and any
crash should show a window with the log path instead of closing silently.

**Validation banner in the launcher** (`launcher_state.cpp` OnDraw, after the
header): every frame it checks `default.xex` + `us/`/`eu/` (current region) on
the **effective root**:
- Green `[OK] Game data at: <path>` when present; red with the detail of
  what is missing (default.xex / us / eu) when not.
- **"Select data folder..." button**: `PickFolder` (IFileOpenDialog),
  validates with `IsValidGameDataDir` (contains `us/`/`eu/` or `default.xex`),
  persists it in the `dbz3_game_dir` cvar (dbz3_user.toml) and **remounts the game
  live** without restarting.
- **PLAY is blocked** (`BeginDisabled`) while assets are missing.

**Live remount of the game data** (`src/region.{h,cpp}`):
- `dbz3::EffectiveGameRoot()`/`SetEffectiveGameRoot()`: effective root (the one
  containing `us/`/`eu/`). Registered in `OnConfigurePaths` and used by
  `ApplyRegionMount` (before it used `rt->game_data_root()`, which is FIXED at Setup and
  goes stale after a remount).
- `dbz3::RemountGameDrive(root)`: unregisters and re-registers the
  `\Device\Harddisk0\Partition1` device at the new root + re-creates the `game:`/`d:`
  symlinks (same pattern as `Runtime::SetupVfs`). `RelocateGameData` =
  remount + re-apply region. Safe because the guest has not launched yet.
- `OnConfigurePaths` priority: CLI arg > `dbz3_game_dir` (override) >
  auto-detection (exe / assets / project / parent). If the override is not valid
  it is ignored with a warning.

**Crash window** (`src/main.cpp` SetupCrashHandler):
- On an unhandled exception: minidump (if Dev "Write crash minidump"),
  crash log, `rex::FlushLogging()`, and a **MessageBox "DBZ Budokai 3 - Error"**
  with the exception code, address, **log path** (`LatestLogPath()`, the most
  recent `logs/dbz3_*.log`) and minidump path. With a debugger attached it
  defers to the debugger (`EXCEPTION_CONTINUE_SEARCH`).
- `std::terminate` also shows the window.

**Built and smoke test OK**: dbz3.exe 17322496 B (25/08 18:23), the launcher
boots ("launcher shown, waiting for Play"), 0.10 DLLs intact in the build.
Pending: visual validation of the banner (green/red + picker) and of the crash
dialog in the standalone package.

**Sync**: `src/{main.cpp, region.{h,cpp}, launcher/{settings.{h,cpp},
launcher_state.{h,cpp}}}` → `github/`. NOT uploaded to GitHub (general plan still
in progress). When a release is made: add `README_PRIMER_ARRANQUE.txt` to the zip and
strengthen RELEASE_README.

### 14.4 🔴✅ LAUNCHER: AUTOSAVE OF SETTINGS WHEN CHANGED (2026-08-20)

**Reported problem**: the user selects the **internal scale** (e.g. 2x)
or the **upscaling effect** (CAS) in the launcher, but **does not always press
"Save settings"** → when launching or closing the launcher, the change is lost and the
game boots with the previous configuration (it was perceived "at 720p"). Persistence
only happened on the "Save settings" and "PLAY" buttons
(`launcher_state.cpp` lines 227-236).

**Root cause**: the launcher's combos only called the cvar setter
(`SetResolutionScale`/`SetPresentEffect`) in memory, without persisting. Saving
depended on pressing "Save settings" or "PLAY", which the user does not always do.

**Fix** (`src/launcher/launcher_state.{h,cpp}`):
1. **Immediate autosave when changing the internal scale** (DrawVideoTab):
   after `SetResolutionScale`, `SaveUserSettings()` is called → the
   `dbz3_user.toml` is written instantly and `draw_resolution_scale_x/y`
   are persisted. Applied at the next boot.
2. **Immediate autosave when changing the effect** (DrawUpscaleTab): same with
   `SetPresentEffect`.
3. **Autosave in `OnClose()`** (new override): a safety net that
   persists ALL settings when closing the launcher (X button or PLAY), covering
   any other option the user marked without pressing "Save".

**Result**: the selected scale/effect are saved "on change", 100 %
guaranteed without depending on "Save settings". Confirmed that the toml persists
`draw_resolution_scale_x/y` (propagation to the GPU plugin works via the
shared registry + pending values, and the hash of the `dbz3_user.toml` on D:
shows the correct values).

**Verified**: compiles (launcher_state.cpp/h) and the new `dbz3.exe` (17285120 B)
deployed to `D:\Budokai 3` and `github/release-stage/`. `rexruntime.dll`
(11188224 B) correct in build/release-stage/D: (hash 0A18EFAA, with
`AfsGetVirtualTable` + `AfsFindModFileOverride`).

**Sync applied**: `src/launcher/launcher_state.{h,cpp}` → `github/` (commit
`de40780`), push to origin/master, tag `v1.0.4`. **Release v1.0.4** created
(Latest, zip `DBZ-Budokai-3-HD-Collection-v1.0.4.zip` 17222532 B).
⚠️ git note: the https push required `git config --global credential.helper
"!gh auth git-credential"` (before it hung without a helper).

### 14.16 ✅ FIX FOR THE EU DEMO BATTLE CRASH + DUAL CORE + RELEASE v1.0.7 (2026-08-26)

**Context**: the EU core crashed in the DEMO battle ("Press start" menu
idle, ~40-50 s) with 0xC000001D (UD2) or, after advancing, with
`[FATAL] Call to invalid or unregistered function`. The DEMO is the game's
attract mode: leaving "Press start" without input kicks off a 3D AI
battle. The user was AFK → the tests had to be automatic (skip_launcher,
no input). It was ruled out (with evidence) that the prefix/integration caused
the crash: the EU-only core WITHOUT the prefix also crashed → a pre-existing bug in the
EU codegen.

**ROOT CAUSES (4, all found and fixed)**:
1. **UD2 in sub_820F2370 (bctr 0x820F2390)**: the guest does a real indirect
   tail call reading function pointers from table 0x8201E348
   (`lwzx r11,r10,r11; mtctr r11; bctr`). The codegen auto-detected it as a
   **single-case jump table** (`switch(r11){case 0: goto loc; default:
   __builtin_trap();}`) → any real pointer (e.g. 0x820F24D8,
   registered) → UD2 → 0xC000001D.
2. **UD2 in sub_820BB8C8 (virtual call)**: vtable at 0x82122B08, index
   `*(r3+82)<<2` → `lwzx; mtctr; bctr`. Same wrong classification
   (single-case switch → trap). Real crash target: 0x820BB178.
3. **Clobber of r31 (callee-saved) by a codegen mis-split in
   sub_8213E7D0**: the `dbz3_config_eu.toml` config had
   `0x8213E834 = { name="rex_sub_8213E834", size=0x1CC }` and
   `0x8213EA00 = { name="rex_sub_8213EA00" }` (added in the EU iteration
   §14.13 to resolve "unresolved" branches). They are MID-FUNCTION blocks of
   sub_8213E7D0 (loop header 0x8213E834 and block 0x8213EA00), NOT functions.
   The codegen turned sub_8213E7D0's `blt 0x8213e834` into a tail call to
   rex_sub_8213E834 **without an epilogue** (it does not restore r31/f30/f31/lr) → after the
   call, the callback-table loop of sub_820FCF90 (0x8201ED74)
   read a corrupt r31 (0x8201ED94→0x823EE502) → garbage target (0xB8DC45D7,
   0xDC0845A9...) → FATAL. **Fix**: declare `0x8213E7D0 = { size = 0x304 }`
   (real extent 0x8213E7D0-0x8213EAD4, epilogue `addi r1,r1,0xa0; lfd
   f30/f31; b __restgprlr_28`) and REMOVE the 2 split entries → sub_8213E7D0
   is generated as ONE function with its correct loop and epilogue.
4. **Unregistered function 0x820BB178 (vtable method)**: the function
   table at 0x8201D300 (virtual methods, NO RTTI) is not scanned by the
   vtable_scanner (only C++ vtables with typeinfo). 0x820BB178 was called via
   bctrl from sub_820BB418 (`*(0x8201D314)`) and was the only unregistered
   method → `UNREGISTERED indirect call: target=0x820BB178`. **Fix**:
   `0x820BB178 = { size = 0x24 }` in the config.

**Instrumentation that solved it**:
- main.cpp's crash handler logs the fault ctx + guest registers (r3/r4/r11)
  on every unhandled exception (KEPT in release, it only logs on a
  crash).
- `InvalidFunctionTrap` (function_dispatcher.cpp) logs caller_lr + r3/r4/r11
  of the unregistered call (KEPT).
- `tools/fix_eu_bctr.py` GENERALIZED: a regex that replaces any single-case bctr
  (`switch(r11){case 0: ...; default: __builtin_trap();}`) with
  `REX_CALL_INDIRECT_FUNC(ctx.ctr.u32); return;` — covers sub_820F2370 and
  sub_820BB8C8 (and future ones). ALWAYS re-apply after a re-codegen.
- `DBZ3_DUMP_IMAGE` (main.cpp) to dump the decrypted image and analyze
  tables/vtables offline; `%TEMP%\opencode\disppc.py` to disassemble PPC.

**Pointer table scan**: an ad-hoc script that walks the image
looking for runs of 3+ consecutive code pointers → 186 tables with
unregistered members, but most are jump table case blocks (false
positives). The real unregistered vtable methods are solved one at a time
(with the crash log) or by registering the UNREGISTERED target.

**VALIDATED IN GAME (user, several runs)**: the full EU DEMO battle
passes without a crash (both the EU-only core and the dual core). The user closed
manually ("the demo worked perfectly").

**DUAL CORE v1.0.7 (rebuilt)**:
- `win-amd64-dual` (DBZ3_DUAL_REGION=ON): US codegen (generated) + EU codegen
  (generated_eu PREFIXED with `tools/prefix_eu_codegen.py`) → **dbz3.exe
  33881088 B**. main.cpp: `ResolveImageInfo` picks PPCImageConfigEU/US by the
  MD5 of default.xex. The bootstrap only picks dbz3_avx2/legacy by CPU.
- Verified automatically (skip_launcher, forced D3D12, 180 s): US and EU
  ALIVE without a crash; log "dual-region core detected US/NA|EU/PAL".
- **⚠️ When rebuilding the SDK, the rexruntime/FFX in `rexglue-sdk-0.10/bin/` are
  regenerated differently — ALWAYS use the canonical ones from `rexglue-sdk-0.10/out/
  win-amd64` (rexruntime 10951168, rexgpu 6207488, ffx 5420544) and `out/
  win-amd64-legacy` (rexruntime 10849792, rexgpu 6162944, ffx 5414912).**

**RELEASE v1.0.7**:
- `tools/make_release.ps1` rewritten: **2 variants** (dbz3_avx2/dbz3_legacy,
  the SAME 33.8 MB dual core; v3/v2 DLLs from the SDK outs; shared DLLs from
  `out\build\win-amd64-release`), new bootstrap (44544 B, 2-variant), optional UPX
  `-UpxPath`.
- **UPX -9 of the dual core: 33881088 → 6960640 B (20.5 %)**. Scanned with
  Windows Defender (MpCmdRun): **no threats**. Zip 36778594 B.
  (Later, v1.0.10/v1.1.0: UPX dropped because of antivirus false positives.)
- **⚠️ Stale bootstrap**: the release-stage had the OLD bootstrap (46592 B,
  4-variant, dispatched EU to dbz3_eu_avx2, which no longer exists) → the EU package
  failed without logs. Rebuilt `dbz3_bootstrap.exe` (44544 B) from the
  current `src/bootstrap.cpp` and copied it to the stage. **LESSON: when the
  variant design changes the bootstrap must be rebuilt**.
- Verified the real PACKAGE (bootstrap → dbz3_avx2\dbz3.exe UPX):
  US and EU boot, "first present OK", no crash (US 70 s, EU 120 s).
- PENDING (user): upload to GitHub (tag/release) and validate on real
  machines (AV, legacy variants). The PE VERSIONINFO is still pending
  (cosmetic).
- **⚠️ RENAME (v1.0.8)**: the package core went from `dbz3_core.exe` to
  **`dbz3.exe`** (inside `dbz3_avx2\` and `dbz3_legacy\`), the same as the
  root bootstrap, to unify the name (consistent docs/launcher).
  Touch `src/bootstrap.cpp` (child path) + `tools/make_release.ps1`
  (name when copying) and REBUILD the bootstrap + regenerate the release.
- **⚠️ VERSION NOTE (corrected after the session)**: the release packaged in
  this section was initially called v1.0.11, but the real version we are
  on is **v1.0.7** (GitHub's Latest is v1.0.6; the local zips
  1.0.7-1.0.10 were consolidated into the "1.0.5 EX" tag, commit d629f8c). The
  package and the zip were renamed to v1.0.7 and make_release.ps1 has the default
  `$Version = "v1.0.7"`. Also verified that the package, untouched,
  shows the launcher and waits for Play (it does not boot the guest directly).

**Sync**: `src/main.cpp`, `tools/{make_release.ps1, fix_eu_bctr.py}`,
`dbz3_config_eu.toml`, `AGENTS.md` → `github/`. `generated_eu/` is NOT uploaded
(derived code). The SDK change (logging in function_dispatcher.cpp) is
documented in `github/patches/` if distributed.

### 14.17 🔴✅ BUG CLOSED: V-SYNC/VRR — HARDENING THE GUEST PACING TO 60 Hz (2026-08-26)

**Reported bug**: "disabling V-Sync makes the game run super fast" (the game
runs ~16x). It is the last open gameplay issue.

**Root cause (multi-vector)**:
1. `GraphicsSystem`'s "GPU VSync" worker (`rexglue-sdk-0.10/src/graphics/
   graphics_system.cpp`) marks the guest's vblank with:
   `interval_ticks = REXCVAR_GET(vsync) ? (freq/refresh_rate=60Hz) : (freq/1000=1ms)`.
   With the `vsync` cvar OFF the vblank runs at ~1000 Hz → the game logic
   runs ~16x faster.
2. The launcher already forced `vsync=true` in `ApplyRuntimeSettingsToSdk`
   (settings.cpp:949), but that only covers boot: any path that
   turned the cvar off at runtime (command-line args via `cvar::Init(argc,
   argv)` — the SDK stashes and parses `--cvar=value` in cvar.cpp:610 — or a residual
   toml/config) sped the game up again.

**Fix — hardening in the SDK (patch #13, `graphics_system.cpp`)**:
the worker now **clamps the interval** so that the guest's vblank is never
shorter than one 60 Hz frame, whatever the cvar state:
```cpp
uint64_t interval_ticks = std::max(
    REXCVAR_GET(vsync) ? vsync_interval_ticks : no_vsync_interval_ticks,
    vsync_interval_ticks);
```
→ `vsync=false` becomes a no-op. The game always runs at 60 Hz.
It lives in **rexgpu-xenos.dll** (NOT in rexruntime.dll): `src/graphics/CMakeLists.txt`
puts graphics_system.cpp and command_processor.cpp in `rexgpu-xenos`.

**⚠️ When rebuilding `rexgpu-xenos` with the build, the FFX in `rexglue-sdk-0.10/bin/`
is regenerated differently — do NOT copy it. And the rexruntime in `out/win-amd64-legacy`
may relink to a different size (10853376 vs canonical 10849792): if that happens,
**restore the canonical one** from the release-stage (this patch's change does not
touch rexruntime). Canonical: rexruntime avx2 10951168 / legacy 10849792;
rexgpu-xenos avx2 6207488 / legacy 6162944 (new); FFX 5420544 / 5414912.**

**Distributed DLLs**: new `rexgpu-xenos.dll` (avx2+legacy) copied to
`out/win-amd64`, `out/win-amd64-legacy`, `out/build/win-amd64-release`,
`github/release-stage/{dbz3_avx2,dbz3_legacy}`. **The stale `rexglue/bin` one
fixed along the way**: it had rexruntime 10947584 (old, §14.11) → now the
canonical 10951168 + the new rexgpu (avoids the §13.6 bug in future cmake runs).

**Verified**: package smoke test with the new DLLs — US core detected,
`applied runtime settings -> vsync=true`, `first present OK`, guest thread
created, 45 s without FATAL/UNHANDLED (the guest runs its normal loading sequence).
With `--vsync=0` the launcher keeps `vsync=true`; and even if something turned it off, the
clamp prevents the speed-up. **The bug is closed on every path.**

**Sync**: patch `patches/rexglue-sdk/src/graphics/graphics_system.cpp` (new,
#13 → patches/README 18 files) + new DLLs. Pending: regenerate the release zip
when convenient (bundle with the mod center / housekeeping).

### 14.18 ✅ MOD CENTER (P4.1): INSTALL FROM .ZIP + PROFILES (2026-08-26)

**Goal (HOJA_DE_RUTA_COMUNIDAD 4.1)**: let the community manage optional mods
easily. Closes the "install a mod from a .zip" + "profiles" requests. Keeps the
vanilla core by default (it already was: without mods, the original game).

**Changes** (launcher/project only, no SDK):
1. **Install a mod from a .zip** (Mods tab → "Install mod (.zip)..."):
   - New `PickFile` (`launcher_state.cpp`, IFileOpenDialog + FOS_FORCEFILESYSTEM
     with a `*.zip` filter, returns the path in **UTF-8** — WideToUtf8, unlike
     the old `PickFolder`, which truncates to char).
   - `dbz3::InstallModFromZip(zip_utf8, name, err)` (`mods.cpp`): unzips with
     **PowerShell `Expand-Archive` via `-EncodedCommand`** (base64 UTF-16LE, immune
     to spaces/quotes/unicode; `CreateProcessW` with CREATE_NO_WINDOW, waits and
     checks exit 0). Normalizes the layout (if the zip wraps everything in ONE folder
     with no loose files, it unwraps that folder) and moves it to `mods/<name>`
     (sanitized; suffix `_2`/`_3` if it already exists).
   - ⚠️ **Do NOT use PS's `N'...'` prefix in the script**: Expand-Archive passes it
     to its internal New-Item and breaks the path (`drive 'NC:'`). Use normal
     single quotes with `''` escaping for paths with a quote.
   - Button also in the empty state ("no mods").
2. **Mod profiles** (a set enabled/disabled at once):
   - File `mods/profiles.txt` (`[name]` + list of mods; "vanilla" = built-in
     all disabled, not saved). `ListProfiles/ProfileEnabledMods/SaveProfile/
     DeleteProfile/ApplyProfile` in `mods.cpp`.
   - Cvar `dbz3_mod_profile` (default "vanilla", persisted in the toml) + a combo in
     the Mods tab: selecting applies instantly; "Save as..." saves the
     current state with a name; "Delete profile". "Reset to defaults" goes back to
     vanilla and applies.
   - The real state is persisted via the `.disabled` markers (as always) → the
     applied profile survives restarts.
3. **Open folder** per mod (button in the row) + a transient status line (click
   to dismiss).

**i18n**: 16 new strings added MANUALLY to `kTable[]` in `i18n.cpp`
(ES/IT/DE/FR; the file is generated — if regenerated with the script, re-include them).

**Verified**: compiles (dbz3.exe 17624064 B); launcher "shown" without a crash;
the PowerShell `-EncodedCommand` invocation tested in isolation (exit 0, correct
extracted layout, including nested wrappers). PENDING an in-game UI test
(install a real zip + save/apply a profile).

**Sync**: `src/{mods.{h,cpp}, launcher/{settings.{h,cpp}, launcher_state.{h,cpp},
i18n.cpp}}` → `github/`. Bundle release v1.0.9 with the V-Sync fix (§14.17) when
convenient.

### 14.19 ✅ HOUSEKEEPING + RELEASE v1.0.9 (2026-08-26)

- **PE VERSIONINFO** (cosmetic, pending before): new `src/version.rc`
  (VS_VERSION_INFO, version 1.0.9.0, product "DBZ Budokai 3 HD Collection",
  author NovaPowers, MIT) added to the `dbz3` and `dbz3_bootstrap` targets in
  `CMakeLists.txt`. Compiles with llvm-rc (the build's RC compiler was already
  configured). **Version bump**: edit `VERSION_MAJOR/MINOR/PATCH` in
  `version.rc` + `make_release.ps1` + `RELEASE_README.md` + `AGENTS.md`.
- **Stale zips deleted** from `github/`: `v1.0.5`, `v1.0.9` (old) and `v1.0.10`
  (leftovers of the §14.16 version confusion). The ones uploaded to GitHub stay
  (1.0.6/1.0.7/1.0.8).
- **⚠️ Mojibake in `docs/HOJA_DE_RUTA_COMUNIDAD.md`** (155 sequences): MIXED
  corruption (CP1252 double encodings + invalid bytes + legitimate accents) → NOT
  safely reversible with a CP1252 round trip. It is an internal doc; it stays
  as a known cosmetic issue (the public-facing docs — README, RELEASE_README,
  first boot — are clean). If it is to be fixed, rewrite the doc.
- **Release v1.0.9 packaged** (`make_release.ps1 -Version v1.0.9 -UpxPath`):
  bundle of the V-Sync fix (§14.17, new rexgpu) + mod center (§14.18) +
  VERSIONINFO. Dual core 33,959,936 B → UPX 6,984,704 B (20.6 %); zip
  `DBZ-Budokai-3-HD-Collection-v1.0.9.zip` (36,827,718 B). `make_release.ps1`
  default `$Version = "v1.0.9"`.
- **Package verified**: VERSIONINFO 1.0.9.0 in bootstrap and core, rexgpu
  `60B613B2` (clamp present), launcher "shown" without a crash.
- **✅ UPLOADED TO GITHUB (2026-08-26)**: tag `v1.0.9`, release with zip + changelog,
  now Latest → https://github.com/novapowers0/DBZ-Budokai-3-HD-Collection/releases/tag/v1.0.9.
  (It is the package equivalent to the release build; the user validated that it "looks
  fine".)

**Sync**: `CMakeLists.txt`, `src/version.rc` (new), `tools/make_release.ps1`,
`AGENTS.md` → `github/`.

### 14.20 🔴✅ USER FEEDBACK → RELEASE v1.0.10 (2026-08-28)

**Feedback received (video/comments)** and the fixes applied:

1. **"dbz3_legacy variant → 0xC000001D, no logs appear"** (bootstrap):
   - Diagnosis: the AVX (ymm) in the legacy DLLs is ONLY in the CRT/context-switch
     dispatch, **protected by `__isa_available`** (verified:
     rexruntime → 1 function `HostToGuestFunction`, rexgpu → `rex_gpu_create`,
     both with `testb $0x20; je fallback`) → the crash comes from a CPU **older
     than SSE4.2** (pre-2009) running unguarded `-march=x86-64-v2` code.
   - Fix: bootstrap message corrected (real path `dbz3_<variant>\logs` +
     explains the cause of the 0xC000001D and which variant to try).
2. **Antivirus false positive in v1.0.6 (UPX)**: the core was packed with
   UPX -9 → AVs flag it as a virus (malware pattern). **Fix**: it is NO longer
   packed by default (`make_release.ps1` documents NOT to use `-UpxPath` in
   releases; 40.7 MB zip without UPX).
3. **0xC000001D crash when choosing a Stage in Duel / Start button in battle**:
   - 🔴 **ROOT CAUSE (US codegen)**: `sub_820BB938` is a **vtable dispatch**
     (index `*(r3+82)<<2` → `lwzx; mtctr; bctr`) that the codegen classified as a
     **1-case jump table** → `default: __builtin_trap()` → UD2 → 0xC000001D
     when entering battle. SAME family as EU `sub_820BB8C8` (§14.16, already
     fixed) but in the US codegen.
   - Fix: `tools/fix_eu_bctr.py` GENERALIZED (processes US `dbz3_recomp.*` and
     EU `dbz3_eu_recomp.*`) → applied to US (`dbz3_recomp.0.cpp` → 1 site) →
     `REX_CALL_INDIRECT_FUNC(ctx.ctr.u32)`. ALWAYS re-apply after a re-codegen.
     **Dual core rebuilt** (33961472 B) + dev build.
4. **PLAY button does not respond to the mouse (only Enter), Windows and Steam Deck**:
   - 🔴 **ROOT CAUSE**: `assets_ready` blocks PLAY with `xex_blocked`, and a
     `kUnknown` xex (modified/compatible dump) or **EU on the dual core** made
     `xex_expected=false` → PLAY disabled → the mouse did not click, but
     **Enter did NOT go through `BeginDisabled`** → it launched anyway.
   - Fixes: (a) `XexIsExpected` accepts US AND EU on the dual core (`DBZ3_DUAL_REGION`)
     → fixes "it does not recognize my EU version"; (b) `xex_blocked` only blocks an
     xex of a **known wrong variant** (an unknown one warns but does not
     block); (c) Enter respects the same `assets_ready` gate.
5. **The launcher does not detect the dedicated GPU on Optimus laptops**: `GetPrimaryGpu`
   picked the first non-software adapter (integrated). Fix: pick the one with **the most
   dedicated VRAM** (the dGPU always wins).

**v1.0.10 binaries**: dual core 33961472 B (VERSIONINFO 1.0.10.0), bootstrap
50176 B (new message), release-stage updated, zip regenerated
(`DBZ-Budokai-3-HD-Collection-v1.0.10.zip`, 40.7 MB, NO UPX). Canonical DLLs
intact (rexruntime 10951168, rexgpu 6207488 with the V-Sync clamp, FFX 5420544).
Smoke test: launcher shown + first present OK without FATAL. `make_release.ps1`
default `$Version = "v1.0.10"`.

**Sync**: `src/{bootstrap.cpp, version.rc, launcher/{settings.{h,cpp},
launcher_state.cpp}}`, `tools/{fix_eu_bctr.py, make_release.ps1}`,
`RELEASE_README.md`, `AGENTS.md` → `github/`. NOT uploaded to GitHub.

> ⚠️ **The SDK out DLLs changed**: `rexglue-sdk-0.10/out/win-amd64/
> rexgpu-xenos.dll` is now 6210048 B (regenerated 08/27), different from the canonical
> 6207488 (§14.17). Do NOT re-run the full `make_release.ps1` (it would copy DLLs from the
> out) — the release-stage keeps the canonical ones; the zip is generated from the stage.

### 14.21 🔴✅ A SINGLE UNIVERSAL EXECUTABLE (BASELINE SSSE3) + GITHUB CLEANUP (2026-08-28)

**User request**: (a) there can only be ONE universal `.exe`, everything very
simple and user-friendly; (b) leave out of GitHub (delete) the releases/tags that
went wrong.

**🔴🔴 ARCHITECTURE DECISION — the ISA bootstrap and the avx2/legacy variants are
REMOVED**: instead of dispatching by CPUID to `dbz3_avx2\`/`dbz3_legacy\`, the
whole SDK is compiled for the **universal baseline ISA `-march=x86-64 -mssse3`**
(SSSE3 = Core 2 from 2006 onwards → works on ANY x64 CPU; it even covers
the pre-SSE4.2 ones that gave 0xC000001D in the legacy variant). Result:
**a single `dbz3.exe` + a single set of DLLs, no folders or variant
choice**. `src/bootstrap.cpp` and the `dbz3_bootstrap` target are removed.

**SDK baseline build** (`rexglue-sdk-0.10/out/build-win-vulkan-baseline` →
`out/win-amd64-baseline`):
- Flags: `-march=x86-64 -mssse3` (C and CXX). The SDK requires SSSE3
  (`memory.cpp` uses always_inline `_mm_shuffle_epi8`) → pure baseline is
  NOT possible. SSSE3 covers everything real (2006+).
- **Known build bug §0**: `ffx_api_dll.rc` UTF-16 → copy the FIXED `.rc`
  (2831 B, ASCII `// Micro...`) from `out/build-win-vulkan/_deps/
  fidelityfx-src/...` into the baseline build BEFORE compiling.
- **The dx12 FFX is compiled into `bin/`** (not into the out): copy
  `bin/amd_fidelityfx_dx12.dll` (5413888 B) into the out. The vk one = the inherited prebuilt
  (9332432). Resulting baseline DLLs: rexruntime 10856960, rexgpu 6164992,
  FFX dx12 5413888.
- **Verified by disassembly** (llvm-objdump): the AVX/ymm in the baseline DLLs
  is ONLY in 2 functions with dispatch guarded by `__isa_available`
  (rexruntime → `HostToGuestFunction` context switch, rexgpu → `rex_gpu_create`)
  → safe on any CPU. (Same finding as §14.20.1 but now the floor
  is SSSE3, below SSE4.2.)
- **Installed in `rexglue/`** (`cmake --install --prefix rexglue`): future game
  builds use baseline DLLs by default (avoids the §13.6 stale problem).

**Core**: dual-region `dbz3.exe` (US+EU) rebuilt against the baseline SDK
(33961472 B, VERSIONINFO **1.1.0.0**). Smoke test OK: "dual-region core detected
US/NA" + "launcher shown, waiting for Play" + "first present OK" (with real assets
next to the exe). The package WITHOUT assets fails in ConstructRuntime before the
launcher (pre-existing behaviour, not a regression; later fixed in 1.1.1 §14.23).

**Packaging** (`tools/make_release.ps1` rewritten, single folder):
```
<stage>/
  dbz3.exe                  <- ONE single exe (dual, baseline)
  rexruntime.dll, rexgpu-xenos.dll, amd_fidelityfx_dx12.dll, amd_fidelityfx_vk.dll,
  TracyClient.dll, SPIRV-Tools-shared.dll, MSVC CRT DLLs
  mod center hd/            <- toolkit + tools/ (xbcompress/xbdecompress + MSVCR71/MSVCP71/xbdm)
  mods/ (README), README_PRIMER_ARRANQUE.txt, RELEASE_README.md, MODDING_README.md, baserom.md
```
- The `tools/` toolkit (XDK) is copied from `github/tools/` + the repo's
  "Xbox 360 Compression - Decompression tool from the XBOX Development Kit" folder
  (MSVCR71.dll/MSVCP71.dll/xbdm.dll) — before it depended on `mod center hd/
  tools/`, which did NOT exist (an undetected §14.2 bug).
- NO UPX (AV, §14.20.2). Zip **v1.1.0 = 21.9 MB** (40.7 before, with the bootstrap).
- `version.rc` bumped to 1.1.0; `make_release.ps1` default `$Version = "v1.1.0"`.

**Docs**: RELEASE_README + README_PRIMER_ARRANQUE rewritten for the
single-folder layout (no variants or "two dbz3.exe"); Known bugs without V-Sync
(closed §14.17).

**GitHub cleanup (decision §14.21)**: ALL previous releases and tags are deleted
(v1.0.0-v1.0.9, v1.0.5-EX) — all of them had known bugs (Duel/
Start crash, PLAY, UPX virus, version confusion) — and ONLY the universal v1.1.0
is published as Latest. Obsolete releases out of public reach.
(Partly reverted in §14.22: tags recreated as a code archive.)

**⚠️ dev NOTE**: the dual build `out/build/win-amd64-dual` has the baseline DLLs
copied by hand; any `cmake --build` overwrites them with those from
`rexglue/bin` (now baseline, so it is fine).

**Sync**: `CMakeLists.txt`, `src/{main.cpp, version.rc, launcher/{settings.cpp,
mod_pipeline.cpp}}` (bootstrap.cpp REMOVED), `tools/make_release.ps1`,
`RELEASE_README.md`, `README_PRIMER_ARRANQUE.txt`, `AGENTS.md` → `github/`.
**Release v1.1.0** packaged and ready to upload.

### 14.22 ✅ v1.1.0-CLASICO FALLBACK + VERSION ARCHIVE ON GITHUB (2026-08-28)

**User request (after §14.21)**: "don't delete them all — leave them archived
(is there a way on GitHub?) and keep one of the most functional ones around
in case 1.1.0 gives someone problems".

**Answer to "is there a way to archive on GitHub?"**: GitHub has **NO
native "archived" state for releases**. The standard mechanism is:
(a) **tags** (GitHub automatically serves "Source code (zip/tar.gz)" for each
tag → each version's code stays downloadable forever from the Tags
tab), and (b) **non-Latest** releases clearly marked as deprecated in the
text. Only ONE release can be "Latest".

**What was done**:
1. **Playable fallback `v1.1.0-clasico`** (non-Latest release): the SAME current
   dual core (dbz3.exe 1.1.0, same code/fixes as 1.1.0) but with the **classic
   avx2 runtime** that had been tested for months in v1.0.x. The avx2 DLLs that
   STILL EXIST in `rexglue-sdk-0.10/out/win-amd64` are reused (rexruntime 10951168,
   rexgpu 6210048, ffx dx12 5420544, TracyClient 246784) — nothing rebuilt.
   Smoke test OK (current core + classic DLLs → "launcher shown"). Single-folder
   package = `github/release-stage-classic/`, zip
   `DBZ-Budokai-3-HD-Collection-v1.1.0-clasico.zip` (21952645 B). Clear note in the
   release: use it ONLY if universal 1.1.0 gives problems on a modern CPU; the
   1.1.0 remains the recommended one and the only one for old CPUs.
2. **`gh release edit v1.1.0 --latest`**: when v1.1.0-clasico was created GitHub marked it
   automatically as Latest → v1.1.0 was marked Latest again. ⚠️ LESSON:
   any new release created afterwards automatically becomes Latest; if it is not
   the main one, the main one must be re-marked with `gh release edit <tag> --latest`.
3. **Tags of all the old versions recreated** (code archived, nothing
   lost): v1.0.0=8fbd58d, v1.0.1=7218da8, v1.0.2=9e6eae3, v1.0.3=bc7ae61,
   v1.0.4=de40780, v1.0.5-EX=d629f8c, v1.0.6=cd4a368, v1.0.7=3f8b2a8,
   v1.0.8=583b947, v1.0.9=0ee3d5c (pushed to origin). The git history of
   v1.0.10 lives in commit d629f8c (1.0.5→1.0.10 compaction) + later ones.
   **⚠️ The old binary zips (v1.0.0-v1.0.10) NO longer exist** (deleted
   from GitHub and locally) — the archive stays as CODE (tags + GitHub's automatic
   source zips), not as a playable binary. The playable fallback binary
   is v1.1.0-clasico.
4. **`.gitignore`**: `release-stage/` → `release-stage*/` (covers `release-stage-classic/`).

**GitHub status (2026-08-28)**: releases = v1.1.0 (Latest, universal) +
v1.1.0-clasico (fallback, classic runtime). Tags = v1.0.0..v1.0.9, v1.0.5-EX,
v1.1.0 (code archive). No code was lost; only the old binary zips.

### 14.23 🔴✅ PHASE 1.1.1 — DEBUGGING + INTERNAL IMPROVEMENT + LINUX GROUNDWORK (2026-08-28)

**Goal**: close the feedback leftovers, tidy up the internal process and
lay the groundwork for a Linux port. Full design in
`docs/PLAN_1.1.1.md`; port strategy in `docs/PLAN_LINUX.md`.

**Phase A — Debugging**:
1. **🔴 FIX: 0xC0000005 crash without assets** (`src/main.cpp`): with the data
   folder empty, `Runtime::Setup` failed (no xex) and the teardown died with
   0xC0000005. **Fix**: pre-flight in `OnPreSetup` — if there is no `default.xex` in
   `EffectiveGameRoot()`, a clear MessageBox (how to place the assets) + a clean
   `_Exit(1)`. Validated: exit 1 without a crash; the happy path reaches the launcher
   at ~880 ms.
2. **Boot timing markers** (`src/main.cpp`): `PhaseLog()` records
   ms since start in each override (OnPreSetup/OnPostSetup/OnCreateDialogs/
   OnPreLaunchModule/OnPostLaunchModule) → "slow black screen" reports
   (§14.10) are diagnosed from the log (gap until `first present OK`).
3. **Pending (documented)**: intermittent `std::terminate` from `LaunchModule`
   (mitigated §14.14, not reproduced), EU core in real battle (§14.13), JP
   language for the launcher.

**Phase B — Internal improvement**:
1. **`tools/sync_github.ps1` (NEW)**: automates the §9.1 sync into
   `github/` (src/docs/awo_tools/mod center hd/tools + root files), respects
   the .gitignore (keeps the canonical `tools/xbcompress.exe`/`xbdecompress.exe`
   that live only in github/, does not touch `mods/`), with `-DryRun`. Reminds that
   `patches/` is manual.
2. **Single-source version**: `make_release.ps1` reads `VERSION_MAJOR/MINOR/
   PATCH` from `src/version.rc` by default (override `-Version` for suffixes such as
   `-clasico`).
3. **Pending**: `tools/verify_release.ps1` (canonical hashes + VERSIONINFO +
   V-Sync clamp + zip without assets), clean up the outdated `analyze_bin_hd.py`
   (§13.2), rewrite HOJA_DE_RUTA_COMUNIDAD (mojibake §14.19).

**Phase C — Linux groundwork** (detail in `docs/PLAN_LINUX.md`):
- **Audit**: the SDK is already portable (`REX_PLATFORM_*`, `*_win/*_posix` pairs,
  Vulkan ON by default on Linux, SDL, abstracted filesystem). The
  bottleneck was `src/`.
- **DONE (platform guards in `src/`)**:
  - `settings.cpp`: **portable MD5 (RFC 1321)** written for `CheckDefaultXex`
    → removes CryptoAPI (compiles on Linux); DXGI GPU detection guarded with a
    fallback (tier medium); per-platform defaults for `dbz3_gpu_backend`
    (d3d12/vulkan) and `dbz3_input_backend` (xinput/sdl).
  - `launcher_state.cpp`: COM dialogs (PickFolder/PickFile) + UTF-16 guarded
    with a "cancelled" fallback.
  - `mod_pipeline.cpp`: `CreateProcessW` guarded with a clear error fallback.
  - `main.cpp`: `OutputDebugStringA` → no-op outside Windows; portable
    pre-flight (MessageBox/stderr).
- **Pending for a real Linux build**: Linux CMake preset, portable dialogs
  (zenity/kdialog/SDL), portable spawn (posix_spawn), portable zips (libzip),
  **validate smooth Vulkan** (today 6.5x slower than D3D12 — that is the challenge), LZX
  toolkit on Linux (mspack/Wine). (Later: a Linux CI build ships a tarball; and
  on 2026-10-06 an experimental PS5 build was added, see `docs/PS5.md`.)

**Verified**: the dual + release builds compile (no new warnings); smoke test
of the pre-flight (no assets → exit 1 + a clear log, no crash) and of the happy path
(launcher shown + first present OK). `sync_github.ps1` syncs and shows the
git status of github/.

**Sync**: `tools/sync_github.ps1` (root + github/), `docs/{PLAN_1.1.1.md,
PLAN_LINUX.md}` (new), `src/{main.cpp, launcher/{settings.cpp,
launcher_state.cpp, mod_pipeline.cpp}}`, `tools/make_release.ps1`, `AGENTS.md` →
`github/`. Pending: commit + push; release 1.1.1 once the pending Phase B is
complete and validated in game.

### 14.23.1 ✅ RELEASE v1.1.1 (2026-08-28) + ANALYSIS OF "A BIT SLOW"

**User report**: tested `win-amd64-release\dbz3.exe` in battle and menus
(EU region) — everything works, but they found the game "a bit slow". **Analysis**:
- The session log (dbz3_041, 78 s) is **clean** (0 errors/FATAL, normal
  close). GPU = RTX 4070 SUPER, 2x scale + FSR, EU region mounted OK.
- **Benchmark clang -mssse3 vs -march=x86-64-v3** on hot host kernels
  (ARGB swizzle, FMA blend, popcnt, memcpy): the difference is only **~5-11 %**
  (memcpy the same, the CRT dispatches it via __isa_available). The universal
  baseline runtime does NOT explain a dramatic slowdown; it is the accepted cost of "a
  single exe".
- The build was left **vanilla** (disabled `cell_reverse_test`, the only active
  diagnostic mod, which deformed Krillin).
- **Conclusion**: no bug; the baseline ISA cost is documented in
  RELEASE_README ("Known bugs" + "Contents") with the alternative
  `v1.1.0-clasico` (AVX2 runtime) if it is noticeable on a specific machine.
  (Later analysis showed the real cost driver is supersampling; see
  `AGENTS.md` §3.0b.)

**Phase B completed in 1.1.1**: `tools/verify_release.ps1` (DLL hashes vs the baseline
SDK, VERSIONINFO, vsync cvar in rexgpu, empty mods/, zip without game
assets) + `analyze_bin_hd.py` marked OUTDATED (§13.2). HOJA_DE_RUTA_
COMUNIDAD (mojibake) still pending (cosmetic).

**Release v1.1.1 PUBLISHED** (Latest): zip 21898908 B, dual core 1.1.1.0,
baseline DLLs verified identical to the SDK. `make_release.ps1` read the version
from `version.rc` (single source). **v1.1.0-clasico** (avx2 fallback) intact.
Commit `3e3c74f` → github/.

### 14.24 ✅ DISK CLEANUP (2026-09-02) — 44 GB → 31.4 GB (+15.5 GB in TEMP)

**Cleanup approved by the user** (only regenerable/accidental content).
The project folder went from **44 GB → 31.4 GB** and opencode's scratch
(`%TEMP%\opencode`) from **16 GB → 0.5 GB** (~28 GB freed in total).

**DELETED (all regenerable — do NOT recover by hand, regenerate with the
documented commands)**:
- `out/build/win-amd64-tracy/` (10.2 GB) — profiling build; regenerate with the
  CMake Tracy preset (see §9). It contained us/eu/mods/active_region copies and
  frontbuf_*.bmp files.
- `rexglue-sdk-0.10/out/build-win-vulkan-legacy/` (1.05 GB) — legacy variant
  removed (§14.21). The legacy DLLs are in `out/win-amd64-legacy/` (intact).
- `--append/` (560 MB) — accidental test AFS from the §65.2 experiment.
- `afs_out/` (259 MB) — AFS extraction scratch.
- `out/build/win-amd64-release-eu/` (58 MB) — obsolete (the dual core handles EU).
- `awo_tools/bins_trabajo/` (308 MB) + `github/awo_tools/bins_trabajo/` — intermediate
  port bins (regenerable from `us/data_cmn.afs` + `ps2_games/` with
  the scripts in `mod center hd/ports/`).
- `github/release-stage/` + `github/release-stage-classic/` (135 MB) — regenerate
  with `tools/make_release.ps1`.
- Release zips in `github/` (v1.1.0, v1.1.0-clasico, v1.1.1) — already published
  on GitHub (downloadable).
- Loose build garbage: `dbz3.exe.bak`, `.diag_91/`, `.tex_work/`,
  `.swap_work/`, `run_diag.bat`.
- **`%TEMP%\opencode`**: ONLY the DBZ part (test sandboxes with asset
  copies: dbz3_*, eu_boot/eu_*, us_*, dual*, launcher_test*, rel_*, mods_ui_test,
  vsync_test, upx, codegen_test, check106, isabench, obj_to_amg_src,
  generated_*_backup, __pycache__; intermediate bins/objs cell_*, babidi_*,
  goku_264, selfport, world_*, eu.map, find_*.ps1, march_test*, etc.).

**KEPT (by user decision)**: `ps2_games/` (10.8 GB, PS2 AFS for
reference), `modding resources*` (~4.1 GB, community docs/tools),
the whole mod archive (`out/build/win-amd64-release/mods/` 2.4 GB with
og_music + `out/build/_archivo_mods` + `_archivo_builds`/`_archivo_dlls`),
`rexglue_0.9/` (SDK 0.9 backup) and `rexglue-sdk/out/` (historical 0.9 build).
(Several of these were removed in the later 2026-09-09 and 2026-09-14 cleanups;
see `AGENTS.md` §13.)

**⚠️ Notes**:
- The reference data that AGENTS places in `%TEMP%\opencode\` (b327_*.bin,
  cell_*.bin, etc.) NO longer exists: regenerate it from `us/` and `ps2_games/` with the
  `awo_tools/` tools if needed.
- The SDK's `out/win-amd64-baseline/`, `out/win-amd64/` and `out/win-amd64-legacy/`
  (canonical DLLs), `rexglue/` (installed), `out/build/win-amd64-dual` and
  `out/build/win-amd64-release` (active builds + mods) stay INTACT.

---

## 15. 🔴✅ PS2→B3 HD PORT PIPELINE (`port_ps2_b3_*`) — 2026-08-26

> ⚠️ **This §15 is the pipeline's HISTORY. For the consolidated STATUS and the
> PLAN, read AGENTS §3.4 FIRST.**

**Complete ecosystem study**: `docs/07_ports/ESTUDIO_ECOSISTEMA_MODS.md`
(inventory of ~60 community tools — ALL PS2 LE; **none
converts PS2→HD 360**; the community works PS2→PS2 or edits HD with 010 Editor).
**Roadmap**: `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md`.

### 15.1 HD DRAW STRUCTURE MAPPED (descriptors/mesh-refs/axes/arms)

`docs/07_ports/ESTRUCTURA_DIBUJO_HD.md` (based on Babidi bin 96, format C):
- Mesh group = header + **mesh-ref blocks** (0x50: type B5/B4 + texture 0x29BD)
  + **axes** (80 B: quat+pos + stamp + arm_ptr) + **arms** (per-bone skinning
  data) + **descriptors** (0x60).
- **Descriptor CONFIRMED by direct correlation**: `A = vertex range`
  (pool), `B = IB index range` (triangle strip). The IB of range B
  [237,251) = `125,126,119,121,120...` falls exactly in range A [119,128). ✓
- **Arms = per-bone skinning** (NOT draw ranges — the descriptors do that;
  solves the mystery of Krillin's "empty shadows").
- **The structure is REGENERABLE**: descriptors = computed from the IB grouped by
  part; mesh-refs = from the PS2 parts; axes/arms = copied 1:1 from the template.

### 15.2 NAMED PIPELINE (`mod center hd/ports/`, format A by default)

```
port_ps2_b3_extract.py  <ps2.amb|amo0> <extract.json>      # mesh+rig+skeleton
port_ps2_b3_geometry.py <extract.json> <geometry.json>     # HD buffers + groups
port_ps2_b3_draw.py     <geometry.json> <template.bin> <draw.json>  # A/B descriptors per part
port_ps2_b3_pack.py     <template.bin> <geometry.json> <draw.json> <output.amb>
port_ps2_b3_verify.py   <bin.amb> [out.obj]                # OBJ + bounds/NaN
```

- `draw` reads the template's count of REAL descriptors (stride 0x2C00,
  buffer offset != 0; discards false anchors) and merges adjacent IB groups
  (same tex/vtype) if they exceed that count. **Fixes the uniform split of
  `build_from_template.py`** (which divided the buffers equally without respecting the
  mesh parts → misaligned ranges).
- `pack` clones the template: internal mid-insert (buffers grow in place,
  AWG/AWO table/AZT offsets shifted, like the runtime), fills geometry,
  descriptors and the rest of the IB with 0xFFFF. Keeps the template's axes/arms
  (requires a 1:1 skeleton = same bone count and order).
- **FIRST PORT GENERATED (2026-08-26)**: PS2 Cell F2 (GH bin 147, 48 bones) →
  HD Cell F2 template (48 bones, format A, 29 real descriptors). Complete
  pipeline OK: 36 parts → 29 descriptors (merged), sec34=4938 vb2=210
  ib=5148, internal mid-insert +100164 B, 0 NaN, 0 OOB, OBJ exports. Installed as mod
  **`cell_ps2_port`** (slot 327, ACTIVE). LZX 123536 → pad 126976 (exercises the
  virtual mid-insert). Correct DLL verified (10951168, `AfsGetVirtualTable`).
- **⚠️ PENDING**: (a) validate `cell_ps2_port` IN GAME (slot 327 → PS2 Cell F2
  with the template's structure?); (b) the static parts (no rig)
  go to vb2 with PS2 coords (ABSOLUTE ones missing → transform by the bone's world
  matrix, item §40) — may produce big coords; (c) mesh-ref blocks are still
  kept from the template (not regenerated); (d) the number of descriptors is
  limited to the template's (merge); (e) the big PS2 coords (Cell up to
  ±13) belong to the real PS2 model (not the HD one) — they are rendered with the
  skeleton's matrices (the same), not necessarily a bug.
- **🔴 CRASH IN THE SELECT (2026-08-26, log dbz3_008) — ATTRIBUTION PENDING**:
  when trying to enter Krillin's slot, the guest crashed reading guest
  address `0x856AC389` (out-of-range pointer, host RIP in a DLL). **ANALYSIS**:
  (1) in the build's 8 logs, `data_cmn.afs` was NEVER read (0 HITs of
  327) → **our port bin was not served in any session** → the crash comes
  from the select/attract flow (data_spn + adx_jpn), probably PRE-EXISTING;
  (2) the axes (bind matrices + stamps) are **byte-identical PS2=HD** (41/41
  on Babidi) → the conversion IS a real re-layout, not an endianness mystery;
  (3) the A/B descriptor model confirmed 10/10 on HD Cell F2 (each B range's
  IB indices fall in the A vertex range). **STATUS**: `cell_ps2_port`
  disabled (only `tex_91` active) for the attribution test: if the select
  crashes WITHOUT the mod → a pre-existing select bug to fix (like §14.16); if
  it does not crash → re-enable the mod to isolate our bin.
- **🔴 ATTRIBUTION COMPLETE (2026-08-26)**: with `cell_ps2_port` OFF it does **NOT crash**
  (normal battle, data_cmn=211 reads in dbz3_009); with the mod active it **CRASHES**
  (dbz3_008/010: data_cmn=0, crash reading guest heap 0x85xxxxxx in the select).
  `sw_vegeta424` (native HD bin, same 126976 > to_read override) **WORKS
  PERFECTLY** → the mod system/virtual mid-insert is OK; the crash comes from the
  CONTENT of our port bin.
- **🔴🔴 ROOT CAUSE OF THE CRASH (2026-08-26) — BONES 36-47 IN SEC34**: structural
  diff + sec34 bone analysis:
  - HD Cell F2 template (works): sec34 uses bones **0-33** (0 in 36-47).
    Format A: sec34 skins ONLY bones 0-35; bones 36+ go to **vb2**
    (second stream, NOT static: layout B `[1.0,0,0, 0,0,FFFFFFFF@+20, weight,
    float2, nx,ny,nz]` — descriptor 26 crosses the sec34→vb2 boundary, see below).
  - Our port (crashes): **669 vertices with bones 36-47 in sec34** (40=276,
    47=165, 45/46=56, 37/39=35...) → the bone matrix lookup goes OOB → heap
    read 0x8598xxxx. The geometry's classification by `vtype` (BODY_VTYPES→sec)
    is the bug: it must be BY BONE.
  - The HD sec34 IB is a **triangle STRIP with degenerates** (repeated pairs
    as restarts; NOT 0xFFFF, NOT a list). Our port emits a LIST → incompatible
    format. The descriptor's B range = the strip's INDEX count (not
    3×triangles); `draw` computes it wrong (3×tris). A/B go `<<8` with a low flag
    of 1 at +0x5C (our pack already does it right).
  - Cell F2's vb2 is NOT Krillin's "static absolute" one: it is a second
    stream with its own layout, and parts can cross sec34→vb2 (desc26
    A=(2655,25) uses 6 sec34 verts + 20 vb2). RE of this layout pending to
    emit it correctly.
  - **TEST IN PROGRESS**: mod `cell_boneclamp_test` (same ported bin + 669 bones
    clamped to 35, LZX 123502→pad 126976) active ALONE. If it does not crash → bones
    confirmed as the cause; if it crashes → structure (mid-insert/descriptors).
- **🔴🔴 TEST 1 (bones) FAILED (2026-08-26)**: `cell_boneclamp_test` (669 bones
  clamped to ≤35 in sec34) **CRASHES IDENTICALLY** (same 0x856AC389, same
  registers, same thread) → **bones 36-47 were NOT the cause** (or the bin is never
  parsed). Key data from log dbz3_012: **`data_cmn=0` again** — but the
  virtual path (`AfsTranslateOffset`) does NOT log per-entry reads, so
  data_cmn IS read without logs → the crash IS from the content. The bin never
  showed up as served in the logs because the virtual path does not log.
- **🔴🔴 HYPOTHESIS 2 (2026-08-26) — SEC34 GROWTH (internal mid-insert)**:
  the original port grew sec34 2661→4938 (+100188 B) with an internal mid-insert
  inside the bin. History §27: "AWG0 can NOT grow too much (battle
  crash); padding sec34/IB to the template's EXACT counts is the key"
  (v6 delta=0 WORKED, v4 with growth crashed). **New script
  `port_ps2_b3_decimate.py`**: voxel merge per part + consecutive strip; discards
  the vb2 parts (face, hypothesis test). **TEST IN PROGRESS**: mod `cell_delta0_test`
  = port decimated to exact counts (sec1880≤2661, vb2 210≤276, ib6302; bin
  **715872 B = exact template size, delta=0**) active ALONE. If it does not
  crash → growth confirmed as the cause → the pipeline MUST always decimate
  (delta=0). If it crashes → instrument with a minidump (exact guest function).
  (Later: `grow()` was validated once `awg+0x2C`/`awg+0x34` were updated; see
  `AGENTS.md` §3.4.9.)
- **Babidi case discarded as a template**: its HD bin (format C) has the
  vertex buffer at an odd position (sec_abs detected with garbage at the
  start) and layout C differs from A. The pipeline emits format A (validated in
  game with sw_goten_nativo) → use format A templates (Krillin 327, Cell F2 147).

**Sync**: `mod center hd/ports/` (5 scripts) + `docs/07_ports/` (3 docs) →
`github/`. NOT uploaded to GitHub.

### 15.3 ✅ THE INJECTION WAY (2026-08-26) — HD TEMPLATE + CONVERTED PS2 POSITIONS = RECOGNIZABLE

**See the full doc**: `docs/07_ports/SESION_INYECCION_2026-08-26.md`.

**Finding that changed the diagnosis**: the full port (rebuilt pool/IB/descriptors)
ALWAYS comes out amorphous, and the draw instrumentation (`DBZ3_DRAW`
in rexgpu-xenos.dll, env `DBZ3_LOG_DRAWS=1`, dedup by dma+idx) **PROVED that the
guest draws our strips correctly** (23 strips at the exact `B_start×2`
with `B_count+2`). The bug is NOT the IB/descriptors → it is the template's **draw
structure** (arms/mesh-refs/interleaved pool) that breaks when the pool is
reordered. Negative tests that changed nothing: bone clamping to 35/33, +0x10=9 body,
0xFFFF→0 in the IB, flipped winding.

**The way that WORKS = INJECTION**: the COMPLETE HD template intact (pool, IB,
descriptors, arms, axes, vb2, other AWGs) and ONLY rewrite +12/+16/+20 of the
sec34 slots with the converted PS2 geometry. Validated in game: PS2 Cell F2 looks
recognizable (hands, torso, part of the head, one leg, silhouette).

**🔴🔴 AXIS PARENT = OFFSET, NOT INDEX (corrects EVERYTHING before)**:
`axis+0x40` = pointer to the parent axis as an OFFSET relative to AWG0.
`parent_idx = (AWG0 + poff - axes_base) // 80`. Verified: bone 1 parent=3360
(0xD20) → AWG0+0xD20 = 0x19E0 = bone 0's axis. With the corrected parent, the
template's world traces a coherent body (feet y≈-12.6, head y≈8.7) that matches
the PS2 model space (feet -11.5, head 9.6) → both are in the SAME
world. **All earlier world matrices (and the `cell_conv` conversion) were
garbage.**

**HD sec34 stores bone-LOCAL** (mag 1.7); PS2 delivers model space (coherent
body). The correct conversion: `local = inv(world[bone]) · model`. With it
the injection pairs in the same space → it works. Injection v1 failed by
pairing model space against bone-local.

**Current limitation ("decimated" look)**: PS2 has 1880 unique vertices
(4938 expanded from the strip, voxel dedup 0.05) vs 2661 HD slots → a complete
fill reuses ~781 vertices → collapsed triangles. Match distances (slot world
↔ PS2 vert): med 0.62, p90 2.02, max 8.91. Threshold 2.0 → 276 slots (10 %) keep
the original HD position.

**New tool**: `mod center hd/ports/port_ps2_b3_inject.py` (world matching
+ per-slot conversion + threshold). Usage: `python port_ps2_b3_inject.py <template>
<geometry.json> <threshold> <output> [--npm]`. Current mod: `cell_inject4_test` (2385
injected + 276 HD).

**✅ IN-GAME PROGRESS (2026-08-26 afternoon) — see `docs/07_ports/
SESION_INYECCION_2026-08-26.md` §5**:
1. **NPM** (projection onto the PS2 surface, not onto the vertex): removes the collapse
   (568→1394 unique world positions ≈ the template's 1501) but visually "practically
   the same" → the collapse was NOT the visible problem.
2. **🔴 NORMALS**: the injection only touched positions; the HD normals remained
   → broken specular → "deformed polygons". Writing the PS2 surface normals
   (`[nz,-ny,nx]` at +32/+36/+40): the B3HD shine works. Interpolated vertex
   normal (smoothed) > geometric (faceted). Verified 100 % unit length.
3. **🔴🔴 STRICT THRESHOLD = THE KEY**: the PS2/HD mismatch is NOT uniform. Match
   distances per bone: core (BODY/WAIST/CHEST/legs) 0.33-0.8 ✅ aligns; the
   limbs (LHAND/RARM/RHAND, OBI, LLEGROT, bones 13/14) 1.5-8.9 ❌ mismatch.
   Threshold 2.0 injected the limbs with badly paired positions →
   stretched → amorphous (mouth/tail/hands/arms). **Threshold 0.8** (1821+840) only
   touches the well-aligned body, correct HD limbs → **SIGNIFICANT
   IMPROVEMENT** (torso, upper head, lower waist, legs, feet, arms,
   hands; slight mouth). Current mod: `cell_npm4_test`.
4. **Pending**: **BINARY YES, BLEND NO** (the soft blends npm6/npm7 were
   worse than binary npm4: partial weights produce halfway positions →
   amorphous). Tune the binary threshold VALUE, head/mouth (medium mismatch
   1.0-1.25), and the full port (PS2 topology + arms) as the final goal.

**How to keep the quality (next step)**: nearest-point-on-surface (project
each HD slot to the closest point of the PS2 SURFACE over the triangles, not to the
vertex) → 2661 distinct positions without collapse. Alternatives: subdividing the
PS2 mesh, rebuilding the arms (real port), or tuning threshold/matching (incremental).

**Sync**: `mod center hd/ports/port_ps2_b3_inject.py` (new) +
`docs/07_ports/SESION_INYECCION_2026-08-26.md` (new) → `github/`. NOT uploaded to
GitHub.

### 15.4 🔴🔴 RE OF THE FULL PORT (2026-08-26) — see `docs/07_ports/SESION_PORT_RE_2026-08-26.md`

**User decision: commit to the full port** (PS2 topology). The
injection stays as an intermediate result. Findings:

1. **AWG0 draw structure MAPPED** (Cell F2): mesh-ref blocks (0x50,
   X=descriptor index, Y=primary bone), axes (80 B, +0x34 arm_ptr, +0x38
   child, +0x3C sibling, +0x40 parent), zone matrix (diagonal of bones +
   pointers to bboxes), bboxes (AABB per zone), descriptors (0x60).
2. **A/B descriptor CONFIRMED**: `A_start<<8 | A_count<<8 | B_start<<8 |
   B_count<<8 | 0x01`. Verified: the IB indices in B ALWAYS fall in A.
3. **🔴🔴 THE POOL ORDER DOES NOT MATTER** (test `cell_reverse_test`): sec34 pool
   REVERSED + IB remapped + A/B recomputed + mesh-refs/zones/bboxes
   intact → **RENDERS CORRECTLY in game**. The guest reads the pool via
   A/B+IB, NOT via the mesh-refs/zones/bboxes by index. (Invalidated by item 8:
   contaminated test.)
4. **🔴 PORT BUG: descriptor A**. `port_ps2_b3_geometry.py` computed
   `A=[first_vertex, n_vertices]` assuming contiguity, but parts
   share vertices → the strip references much wider indices → 22/23
   wrong A descriptors. Fix: `A=[min(B), max(B)+1)`. `cell_conv2_fixA` → 22/22
   OK. **BUT in game nothing changes** → A was not the visual bug.
5. **The port's geometry IS correct point by point**: conv2 transformed by
   the world matrices = the exact PS2 model (nearest med 0.000, max 1.518).
6. **DIFFERENCES conv2 vs template** (candidates for the amorphous shape):
   (a) new IB (PS2 topology, 4298 0xFFFF padding);
   (b) **293 slots with bones 34-47 in sec34** (the template uses ONLY 0-33);
   (c) **vb2 with a DIFFERENT layout** (template: `[1.0,0,0,?,?,?,nan@+20,U,V,normal]`
   Cell F2's layout B; port: `[x,y,z,0,0,0,0,FFFF,nx,ny,nz]`);
   (d) decimation (1880 verts → stretched triangles, "badly polygonized").
7. **DISCRIMINATOR IN PROGRESS** `cell_bone0_test`: template with all sec34
   bones=0 (positions intact). If it deforms → the guest USES the vertex's
   bone → bones 34-47 are the cause (map/clamp). If the same → vb2/
   topology.
8. **🔴🔴🔴 TEST CONTAMINATION DISCOVERED (2026-08-26)**: `cell_npm8_test`
   (injection, from the previous session) **stayed active** throughout the RE session.
   The runtime (`AfsFindModOverride`) serves the **first active mod in
   alphabetical order** for each entry → npm8 (sorts first) was served instead of the
   tests. INVALID results: cell_reverse_test ("practically the same") and
   cell_port_Afix_test ("exactly the same") — the user saw the injection, not
   the test bins. VALID: cell_bone0_test (sorts before npm8) →
   "collapsed to the feet" = the guest uses the vertex's bone. **LESSON**: check
   that ONLY the test mod is active before each test
   (`Get-ChildItem mods | Where {-not (Test-Path "$_.FullName\.disabled")}`).
9. **🔴🔴🔴 REAL RESULT OF THE REVERSE — THE POOL ORDER DOES MATTER
   (2026-08-26)**: re-tested alone (npm8 disabled): sec34 pool
   REVERSED → **DEFORMITIES**. The §15.4.3 conclusion ("the pool order does NOT
   matter") was FALSE (contaminated test). **The guest is tied to the pool
   order through the mesh-refs/zones** (they reference the pool by original index). The
   port with a reordered pool requires rebuilding the WHOLE draw structure
   (mesh-refs + zones + bboxes + descriptors). Injection works because it
   keeps the template's pool order. Reconciliation: bone0 (valid)
   proved the transform uses the vertex's bone (+28), and the reverse proved that
   the pool is also tied to the structure — both are true.
   (Later refuted on 2026-09-11: the reverse's deformation was an index-base bug
   in the tool; a consistent relabeling is an identity. See `HISTORICO_RELEASES.md` §B.)
10. **SESSION CLOSE STATUS (2026-08-26, user decision: no new versions,
    hand-over to another session)**: active mod = cell_reverse_test
    (diagnostic, DEFORMED — not playable). cell_npm8_test disabled. The best
    playable result is still cell_npm4 (binary 0.8 injection). Pending:
    re-validate cell_port_Afix_test alone; decide full port (rebuild
    the structure) vs accept injection as the practical port. See
    `docs/07_ports/SESION_PORT_RE_2026-08-26.md`.

**New tool**: `mod center hd/ports/pool_reorder_test.py` (pool reordering
test). Mods: cell_reverse_test (OK), cell_port_Afix_test
(no change), cell_bone0_test (ACTIVE).

> ⚠️ For the consolidated status and the plan forward, use **AGENTS §3.4**.

---

## 16. 🔴❌ SESSION 2026-09-07 — MILESTONE 3 NATIVE SLOTS: DATA PATCH = FAILURE

> **Summary**: an attempt to turn the select screen's reserved "?" cell (slot 38)
> into a fixed **Android 16** cell (tag 28, AFS bin 70) via **way 2 of the
> DICTAMEN (guest memory data patch)**. Result: **3 identical `0xC0000005`
> crashes**, root cause identified and **code reverted**. Do NOT retry
> this way as is (see blocker §16.4).

### 16.1 FACTS ESTABLISHED BEFORE THE ATTEMPT (earlier sessions, milestone 2 closed)

- Select capacity = 39 slots (0-38); **slot→tag u16 table at `0x82020618`**
  read DIRECTLY by the guest (no runtime copy; `r25 = 0x82020000+1560`).
- `slot 38 → tag 65535` = the "?" cell; `slot 23 → tag 28` = **Android 16**.
- Portrait table `0x82372818` (stride 8, 2 u32/slot): `slot 23 → entry 3884`
  (Android 16), `slot 38 → 3936` ("?").
- The "?" picks randomly among **unlocked** characters via an LFSR
  (`sub_82084A78`) → Android 16 (not unlocked) never came up naturally.
- Pick trace: ADE8 → if tag==65535 → list from bitmap `obj+16` → LFSR →
  `stb r11,4(r31)`. User tests: it resolved to slot 11 (Piccolo) and 10
  (Krillin) without a crash (battle not confirmed).

### 16.2 CHRONOLOGY OF ATTEMPTS (all with the SAME crash)

| # | Change | Result |
|---|--------|-----------|
| 1 | `REX_STORE_U16(0x82020618+38*2, 28)` + `REX_STORE_U32(portraits+38*8, 3884)` in the ADE8 hook (only with diag) | crash `write of guest 0x82020664` |
| 2 | the same but via a temporary `heap->Protect` + `TranslateVirtual` + byte_swap (restores read-only) | identical crash (same fault ctx) |
| 3 | `MakeWritableGuest` (unprotects and LEAVES it writable) + write, applied ALWAYS (not depending on diag) | identical crash (same fault ctx) |

Logs: `out/build/win-amd64-release/logs/dbz3_056/057/058.log`.
Fault ctx (all 3 identical):
```
Unhandled guest access violation: write of guest 0x82020664 (host 0x...282020664)
RAX=0x82020664 RSI=0x200000000  guest: lr=0x8217D408 (caller of sub_8217A920)
```

### 16.3 🔴 ROOT CAUSE (diagnosed)

1. The fault is **a WRITE by the guest itself** (recompiled codegen: pattern
   `RSI=base`, `RAX=guest_addr`), NOT by the hook. It happens when **CONFIRMING the "?"
   cell**: the guest **persists the chosen tag by writing it into the table
   `0x82020618 + slot*2`** (slot 38).
2. That page is in the guest image as **`XEX_SECTION_READONLY_DATA`**
   (`xex_module.cpp` → `heap->Protect(..., kMemoryProtectRead)`). The guest's write
   to a read-only image page triggers the runtime fault.
3. That is why the 3 attempts failed the same way: the crash is **not from writing
   in the hook**, it is the guest writing to a page the port keeps
   read-only. Attempts 2/3 unprotected the hook's host page, but the
   reported fault (RAX/RSI) is from the guest codegen running its own store.
4. **Conclusion**: turning the "?" into Android 16 via a data patch requires
   the `0x82020618` page to be writable FOR THE GUEST. Unprotecting in the hook
   was not enough; the clean way would be to make the section writable in the
   LOADER (`xex_module.cpp`), which touches the SDK (patch + rebuild DLLs) and was not
   done. **Way discarded for now.**
5. Extra data point: confirming the "?" crashes **even with no mod/patch at all**
   (it is a latent bug of the port in the "?" flow): confirming the "?" cell
   will always write into the read-only table. In the earlier tests only the
   visual RESOLUTION (ADE8→obj+4) was observed, never the CONFIRM with loading.

### 16.4 BLOCKERS / LESSONS

- **The slot→tag table `0x82020618` is read-only in the port** (image). Any
  guest write there (persisting the "?" pick on confirm) crashes with
  `0xC0000005` (`write of guest 0x82020664`).
- A data patch meant to change that table must come with making
  the section writable at the **loader/SDK** level (not the hook).
- The patch applied "unconditionally" and "only with diag" gives the SAME crash →
  the fault does not depend on the hook. ALWAYS check the fault ctx's `RAX/RSI` to
  tell a hook write from a guest write (codegen uses RSI=base, RAX=addr).
- **Final status (reverted)**: `src/roster_trace.cpp` keeps ONLY tracing
  (milestone 2, 8 hooks), with no data patches. Compiled OK (`dbz3.exe`).
  Pending in the game flow: confirming the "?" crashes by itself.

### 16.5 REFERENCES

- `src/roster_trace.cpp` (tracing hooks, no patches — comment in ADE8
  with this session's note).
- `docs/DICTAMEN_GPT6_ASTRA.md` (native slots guide, ways 0-7).
- SDK: `rexglue-sdk-0.10/src/system/xex_module.cpp` (section protection,
  lines ~1014-1030) and `xmemory.cpp` (`AccessViolationCallback`, lines
  ~534-550).
- Crash logs: `out/build/win-amd64-release/logs/dbz3_056..058.log`.
