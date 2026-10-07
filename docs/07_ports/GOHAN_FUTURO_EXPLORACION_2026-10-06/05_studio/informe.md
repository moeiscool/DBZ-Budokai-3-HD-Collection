# Animation and cinematics Studio: feasibility and design

Date: 2026-10-06. Exploration and design only: no project file was touched and the game was not opened.
Everything produced is in this folder (`scratchpad/explore/05_studio/`).

## 0. Verdict

**It is feasible, and the camera part is closer than it looked.**

- **Technique cameras.** The #ACC/#AMC format is fully decoded:
  - 4 tracks per clip: eye, target, roll and fov.
  - All 633 clips of the 38 B3 characters match the format.
  - The prototype decodes and re-encodes every clip of a character byte for byte.
  - Round trip through Blender 5.2 (already installed): error ≤ 0.00002 units, animated roll and fov included.
- **Animations.** The #ACM format is decoded:
  - u16 Euler per bone and positions as offsets, already validated in game by `b1port`/`altura`.
  - Round trip through Blender: error ≤ 0.004° after converting back to u16 Euler.
- **Cinematic script (#SPX).** Its structure is understood, but free editing is not safe yet.
  - It is a stack VM.
  - Builtin **0xA7 = "play camera clip"** is identified, as is the pattern "clip → wait N frames".
  - Without the full interpreter, only **in-place** value changes are possible (clip index, wait frames, floats).
  - Adding or removing statements is a later phase.
- **In-game reload without restarting.** Works by the runtime's design:
  - An entry override is read from disk on every load.
  - It is enough to rewrite the file and use "Re-select characters".
  - One condition: the size cannot grow during the session (see §4.3).

**Recommendation:** an in-house Python core with a **glTF bridge** (Blender or any 3D program, no mandatory add-on), plus a **Studio** tkinter window inside the Mod Kit.

- **MVP:** a technique camera editor with a timeline, toon preview and in-game test.
- **Next phases:** retiming and pose editing via Blender, and the SPX event track.

---

## 1. How the data is encoded

### 1.1 Where each thing lives (per character, `roster_db.json`)

| Bin (data_cmn) | HD content (PS2) | Use |
|---|---|---|
| `anm[form]` (Goku 292) | `#AMB[#CSK, #ACM, #ACM, #ACM]` (BSK, AMM×3) | attack properties + 3 animation banks |
| `cam` (Goku 288) | `#AMB[#ACC(type 5), #ACL(6), #CCM(BCM), #SPX(8)]` | **cameras**, stub, combo table, **scripts** |
| `bsp` (Goku 533) | technique effects | beams, technique auras (out of MVP scope) |

- PS2 GH and HD have the same numbering and the same content. HD = big-endian with renamed magics (`ps2hd.MAGIC`).
- #ACC goes from PS2 to HD with a simple 32-bit word swap (`ps2hd.conv_u32`).
- #SPX is copied as is: it is **little-endian in HD too**.
- Goku's animation banks (HD 292):
  - #ACM 1: 142 animations, 53 bones, up to 190 frames.
  - #ACM 2: victim animations in grabs, generic GOK_ skeleton.
  - #ACM 3: 71 animations.

### 1.2 #ACM animation (= PS2 AMM)

```
+0x10 n_anim  +0x14 table(0x20)  +0x18 n_bones  +0x1C name table (32 B/bone)
table: n_anim × [flags, variant, n_frames, off]      flags 9 normal, 0x19 with scale
block (off): n_bones × per pointers  (per 2 = rot+pos, 3 = +scale)
track: [u32 0][u32 type][u32 n_keys] + keys
   rot : [u16 frame][u16 x][u16 y][u16 z]      65536 = 360°
   pos : [u32 frame][f32 x][f32 y][f32 z]      offset ON TOP OF the rest position
```

Pose rules validated in game (`altura.py`, `b1port.py`):
- **Rotation.** `q = qz·qy·qx` (u16 Euler) and it **replaces** the bone's rest rotation.
- **Position.** It is **added** to the rest position.
- **Matching.** The engine matches tracks **by bone name** (suffix), so an animation works on any skeleton with the same suffixes.
- **Interpolation.** Linear per component, shortest path. `b1port.reduce_track` drops keys that interpolation reproduces, and the Zarbon and Dodoria ports look right in game.
- **Track type.** The `type` field is 1 in 5387 tracks and 0 in 185. Type-0 tracks have one key per frame (probably "no interpolation", no practical effect).
- **Time unit.** Game frame, **60 fps**: it is the engine's convention; still to be confirmed by measuring a clip in game.
- **Root motion.**
  - It does not exist as such: the hip (WAIST) moves in the character's local frame.
  - World displacement seems to come from the #CSK AP lines (type 4 = velocity, type 2 = aerial) and from the engine. This is an inference to be verified.

### 1.3 #ACC camera (= PS2 AMC): full format

```
same header as AMM: +0x10 n_clips, +0x14 table, +0x18 n_bones = 1, +0x1C 0
table: n_clips × [0x1D, 0, n_frames, off]
clip block: 4 pointers → tracks  eye | target | roll | fov
  eye, target : [u32 frame][f32 x][f32 y][f32 z]   (vec3)
  roll, fov   : [u32 frame][f32 value]             (scalar, radians)
the last key is always at n_frames-1 (633/633)
```

**Evidence for the semantics** (`cam_stats.py`: 38 CAM bins, 633 clips, 2532 tracks):
- **fov.** Ranges from 0.066 to 1.306 rad (3.8° to 74.8°), median 37.8°.
- **roll.** Between −π and π, median 0.
- **Target, not rotation.** The community guide (`AMC_Guide.zip`, SamuelDBZMA&M) calls the 2nd track "rotation", but it is a **look-at point**:
  - Eye-target distance ranges from 3.5 to 1058 (median 32.7).
  - Goku's target in clip 0 is (0; 10.5; 0), chest height.
  - Rendering with that interpretation frames the character (`render/goku_clip0_f*.png` in Blender and `render/tira_goku_clip0.png` with the kit's toon renderer).
- **Key density.** Usually 1 key per frame (median 0.77 keys/frame). Some clips are sparse: Zarbon (HD) uses 46 keys for 80 frames and holds the last one. Hence linear interpolation is assumed.
- **Clips per character.** From 2 to 69 (Goku 36).
- **Future Gohan:** his #ACC is **empty** (0 clips). His cinematics have no camera of their own, so he is a direct use case for the Studio.

**To verify in game (milestone M0):**
- Reference space: looks local to the attacker, Y up, model units. Still unknown which axis faces the opponent.
- Whether there is left/right mirroring.
- What the 3 extra floats of the 0xA7 call do: (0, 140, 0), (0, 140, −150) and (0, 200, 0) look like a framing offset or rotation.

### 1.4 Cinematic chain (from input to camera)

```
pad ──► #CCM (BCM, combo table) ──► attack code (e.g. 0x259)
          └─► #CSK: list[code] → 48 B sub-blocks [anim u16][bank u16] + params
                 └─► AP lines (per frame): type 1 hits (HR), 2 aerial, 4 velocity, 7 effects (BSP)...
                       └─► HR block with stun_type 3 ("scripted") + stun_code = #SPX SLOT
                             └─► #SPX: slot table → subroutines (stack VM)
                                   ├─ CAMERA_CLIP (builtin 0xA7): clip from the #ACC of the SAME CAM bin
                                   ├─ wait N frames  (push N; call sub 0)
                                   ├─ pushes attack codes (attacker/victim anims)
                                   └─ other builtins (effects, sound, positions...)
```

- **Goku's slots.** HR type 3 only in 0x259/0x359 (slot 0, the hyper mode rush) and 0x257/0x357 (slot 20, the grab). Slot 10 exists in 5 characters.
- **Contradiction in project memory.** The `b1port` docstring says "slot 20 = ultimates", but the data says grab.
- **Pending for M0:** how ultimates (Kamehameha...) start. Perhaps via SCM/capsules or through the common slot-20 path.
- **Slot census** (38 CAM): slot 20 ×38, 0 ×32, 10 ×5, 1/30/31 ×2, 2/32 ×1.

### 1.5 #SPX: what is known about the VM

Safe opcodes:
- `08 10/20/30` push immediate 8/16/32 bits.
- `09 30` push float.
- `01 10/20/30` load accumulator.
- `02 80 02` builtin call.
- `02 73 02` subroutine call (address = base 0x74 + value).
- `12 10 n` pop.
- `0b` end of statement.

There are more 1-byte and jump opcodes (`02 72 00 02`, `76`, `0a`, `5c`...) with no table yet.

**Builtin 0xA7 = play camera clip.**
- Its 2nd integer argument spans 0..n_clips−1: on average it covers 59 % of each character's indices across 30 characters, and only 6 values fall out of range.
- The stages document already suspected `01 20 a7 00`.
- Real example (Goku, `spx_dis.py spx_288.bin 3440 3740`):

```
CAMERA_CLIP(0, g[0x60]+0, 0, 0.5, 0, 0, 0) ; wait 0x2e
CAMERA_CLIP(0, g[0x60]+1, 0, 0.5, 0, 0, 0) ; wait 0x3a ; ...  (clips +0..+7)
```

- `spx_graph.py` groups calls by subroutine. For Goku, slot 0 uses clips 0–19 and slot 10 clips 0–7, with an index relative to a base variable.

---

## 2. Prototypes (in this folder) and results

| File | What it tests | Result |
|---|---|---|
| `anim_cam_decode.py` | decodes and re-encodes #ACC (PS2/HD) and dumps 1 animation and 1 clip to JSON | 36 Goku clips (PS2) and 25 Zarbon clips (HD) **byte-identical**; JSON in `out_ps2/`, `out_hd/` |
| `cam_stats.py` | track semantics over the whole corpus | see §1.3 |
| `spx_calls.py`, `spx_dis.py`, `spx_graph.py` | builtin census, approximate disassembly, clip↔slot graph | 0xA7 = camera; clip + wait pattern |
| `to_gltf.py` | B3 HD → `.glb`: skinned mesh (Goku 264), moveset animation (292) and camera (288) at 60 fps; animated fov with `KHR_animation_pointer` | 46 bones, 2455 vertices, 28 channels; a few seconds (mostly LZX decompression) |
| `blender_check.py` | headless Blender 5.2 imports the .glb and renders from the clip camera | `render/goku_clip0_f000/045/089.png`: Goku animated and framed |
| `blender_roundtrip.py` + `gltf_to_cam.py` | import → export in Blender (with and without edits) → new #ACC inside a **copy** of the CAM bin | eye error 0.0, target 1e‑5, roll 0, fov 0; the "+5 in X" edit arrives exact; other clips and the #ACL/#CCM/#SPX children stay intact (HD and PS2) |
| `gltf_to_anim_check.py` | animation after going through Blender → u16 Euler | 1350 samples, error ≤ 0.0039° after quantizing (the raw 0.056° is float32 rounding in acos) |
| `preview_strip.py` | preview without Blender using the kit's toon renderer (`model_render.py`) | **0.066 s/frame at 320×180** (~15 fps), `render/tira_goku_clip0.png` and `.gif` |

Verification commands (from this folder, with `TMP`/`TEMP` pointing to `cache/` so the `afs_pair` cache does not leave it):
```
python anim_cam_decode.py --cam 288 --clip 0 --anm 292 --anim 0 --out out_ps2
python cam_stats.py
python to_gltf.py --modelo 264 --anm 292 --anim 0 --cam 288 --clip 24 --out goku_clip24.glb
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python blender_roundtrip.py -- <abs>\goku_clip24.glb <abs>\goku_clip24_blender.glb 5
python gltf_to_cam.py goku_clip24_blender.glb --cam 288 --clip 24 --out cam288_rt.bin
python gltf_to_anim_check.py goku_clip24_blender.glb --anm 292 --anim 0
python preview_strip.py --modelo 264 --anm 292 --anim 0 --cam 288 --clip 0 --frames 0 45 89 --out render/tira.png --gif
```

Prototype limits:
- **No textures in the glTF**: the DXT3 decoder already exists in `model_render._textures`.
- **No bone scale** and no victim bank.
- **Baked keys** (1 per frame): key reduction like `reduce_track` is missing.
- **Preview animation loops** (`f % n_frames`). In game it depends on the script.

---

## 3. Architectures compared

| | (a) Blender via glTF | (b) In-house Studio in the Mod Kit | (c) In-game preview |
|---|---|---|---|
| **What it is** | Export to .glb (model + anim + camera), edit in Blender or another program, import | tkinter window: timeline, 2D path editor, toon view with `model_render` | Write the override and watch it in the real game |
| **Status** | Round trip tested (§2); Blender 5.2.1 installed; `KHR_animation_pointer` supported | Render 0.066 s/frame; tkinter + Pillow + numpy (already kit requirements) | The runtime reads the override on every load (§4.3) |
| **Strength** | Real animation tools (curves, IK, target camera); the community already uses Blender (retopology) | Nothing to install; knows which clip belongs to which technique; validates and saves the mod safely | Single source of truth: effects, script timing, real shading |
| **Weakness** | No effects or script; the modder sees "a loose clip"; depends on an external app | Limited 3D editing (2D views + values); no effects | Slow loop (~30–60 s); without debug keys you have to play up to the technique |
| **Effort** | Low-medium (2–3 days: core + textures + docs) | Medium (5–8 days for the MVP) | Low for the manual loop (1–2); high for a hot reload with a key (RE + C++) |
| **Risk** | Low (open format; no add-on needed, which avoids `bpy` GPL obligations) | Low | Medium-high if guest memory is touched |

**Blender add-on or glTF bridge.** The glTF bridge is better.
- It works the same in Blender, Maya, 3ds Max or Cascadeur.
- It does not break with every Blender version.
- It does not require distributing GPL code.
- A thin add-on ("Send to game" = call our CLI) can come later.

---

## 4. Recommendation: layered design

### 4.1 Pieces

1. **`studio_core.py`** (in `awo_tools/`, no UI):
   - Reading and writing #ACC/#ACM and the #CSK AP lines.
   - Validation.
   - Clip catalog per technique.
   - Key reduction.
   - glTF round trip.
   - Builds on what already exists: `altura.py` (FK), `b1port.Amm` (rebuild banks), `ps2hd` (PS2→HD), `afs_pair`, `model_render.Model`.
2. **`studio.py` CLI**, with the same verbs the window uses: `exportar-glb`, `importar-glb`, `vista`, `validar`, `guardar`, `probar` (export-glb, import-glb, preview, validate, save, test).
3. **Studio window.** A separate tkinter window launched from the Mod Kit: a "Studio" button under Tools and on the character sheet. This keeps `modkit_gui.py` (already 5300 lines) from bloating.
4. **In-game test loop.** A reserved `_studio` slot, atomic writes, and a "Re-select characters" guide.

### 4.2 MVP: "Technique camera editor"

1. **Pick character and technique.**
   - The list comes from the catalog: SPX slot/subroutine → clips in order with their wait (`spx_graph`) + a name (curated table in M0).
   - Each clip has thumbnails: first, middle and last frame rendered.
2. **Shot timeline.**
   - Clip blocks with their real duration (the script's wait).
   - Marks for the hit and effect frames from the attack code's AP lines.
3. **Clip editor.**
   - Top and side views (canvas): draggable eye and target curves.
   - Wireframe skeleton of the character at the current frame.
   - Numeric fields.
   - Roll and fov as curves.
4. **Operations.**
   - Move, add and delete keys; smooth.
   - Retime (stretch or shrink without changing the script total).
   - Copy a clip from another character.
   - Templates: orbit, dolly, zoom-in, shake, camera roll.
5. **Preview.**
   - 15 fps toon render while scrubbing.
   - "Play": bakes in the background and saves a shareable GIF.
6. **Blender (optional).** "Open in Blender" exports a .glb (and opens Blender if installed); "Bring from Blender" imports the camera.
7. **Save as mod** with validation and backup, and **"Test in game"** with instructions (§4.3).

Out of the MVP:
- Pose editing.
- Adding animations.
- Script editing (except in-place numbers).
- BSP effects.

### 4.3 Integration with the Mod Kit and roster_build (outputs, validation, safety)

**Outputs:**
- **Native character:**
  - Path: `mods/studio_<character>_<technique>/us/data_cmn.afs/<CAM fid>/geom.bin`.
  - Compressed with LZX `xbcompress /N:2048` and zero-padded.
  - Ships a `manifest.txt` (`type=studio`, `source=CAM 288`) and an **editable project** `studio.json` with the keys and the source. It is the source of truth: the bin can be regenerated.
- **New character or port** (Zarbon, Future Gohan...):
  - The Studio edits the **source mod's** `moveset/camara.bin` (or `anm*.bin`).
  - Then it runs `roster_build.py construir`, as today.
  - `_roster` is never written by hand.
- **Animations (phase 2):**
  - The #ACM is rebuilt with `b1port.Amm.build`.
  - If the duration changes, the `frame` of the code's AP lines is shifted.
  - The override goes to the character's `anm` (or to the source mod).

**Validation before writing** (failure = nothing is written):
- **Round trip.** Decoding what was encoded must give the same result. The other clips or animations and the other #AMB children stay byte-identical (as in `gltf_to_cam.py`).
- **Keys.**
  - Increasing frames; last key at `n_frames−1`.
  - Finite floats; fov between 0.05 and 2.5 rad; roll between −π and π.
  - Eye-target distance > 0.1.
- **Indices.**
  - Clips are never deleted: the script requests them by number.
  - Clips are only appended.
  - If a clip is added, warn that the script will not use it without editing the SPX.
- **Animation.** AP lines must fall within the duration.
- **Size.**
  - Override ≤ reserved size (see reload).
  - If it does not fit, the warning says "restart the game to apply".
  - Nothing is ever truncated.
- **Conflicts.** Another active mod overriding the same entry (first alphabetically wins) raises a warning, as `roster_build estado` does.

**User data safety:**
- `us/*.afs` and the original files are **never touched**: only `mods/` is written.
- **Backups.** Before rewriting a mod file, the previous version is moved to `mods/<mod>/respaldo/<date>/`. It is never deleted (user rule).
- **Atomic writes.** Write to a temp file, then `os.replace`, with retries if the game has the file open.
- The `studio.json` project allows undo and regeneration.

**In-game reload without restarting** (checked by reading the runtime, `afs.cpp` / `host_path_file.cpp`):
- `AfsFindModOverride` opens and reads the override file **on every read**; only the list of mod folders is cached at startup.
- **Consequence 1:** the `mods/_studio` folder (or the mod's folder) must exist **before** the game is opened.
- **Consequence 2:** the virtual AFS table (`GetOrLoadVirtualAfs`, `g_vafs_cache`) is computed **once** with the override's size at that moment. So the Studio reserves size when it creates the override (original + margin, e.g. +25 % or +64 KB) and always writes exactly that size, zero-padded.
- **Loop:** save → in game Pause → "Re-select characters" → same characters → Training → fire the technique. M0 still has to confirm that the entry is re-read when the battle reloads.
- **Automation.** `dbz3_input.req` and `dbz3_shot.req` exist (SDK). They are for development tests (and with the user's permission), not for end users.
- **PS5 build:** the same per-entry override applies (mods live in `/data/dbz3/mods/` on the console), but the Studio and the Mod Kit are PC tools; build the mod on PC and copy it over. Untested on PS5.

### 4.4 Later phases

- **F2 Animation:**
  - Retime attack codes: warp track timing and shift the AP frames.
  - Touch up poses in Blender via glTF: quaternion → u16 Euler (`quat_to_u16`) and key reduction.
  - Add animations to the bank and point the #CSK sub-block at them.
  - Import animations from other games or skeletons: `b1port.retarget`, `sb_amm` and `altura.correccion` already exist.
- **F3 SPX event track:**
  - Full disassembler: opcode table and builtin arity, taken from the interpreter in `generated/` or with a probe in the runtime.
  - First, a read-only timeline.
  - Then in-place edits: clip index, wait, 0xA7 floats.
  - Finally, inserting or deleting statements with relocation of jumps and the slot table.
- **F4 Runtime (C++, optional):**
  - Dev key "replay the last cinematic".
  - Hot reload of the CAM bin in guest memory.
  - Free camera or photo mode: Burst Limit has it in its SDK branch.
  - Requires RE of where the CAM bin is loaded and how an SPX slot is launched. After every build the canonical DLLs must be copied again.
- **F5 BSP effects in the preview:** RE of the BSP format. Long; only if there is demand.

---

## 5. Plan, effort and risks

Effort in agent days, plus the in-game tests done by the user.

| Milestone | Content | Effort | "Done" criterion |
|---|---|---|---|
| **M0 Verification** | 1 capture session: camera frame and mirroring, fps, wait ↔ clip duration, 0xA7 floats; override re-read on character re-select; technique → clips catalog for 2–3 characters (Goku, Vegeta, Cell) | 2–3 | Studio render ≈ game capture (same framing); a clip change visible without restarting |
| **M1 Core** | `studio_core.py` (read/write, validation, key reduction, catalog); test = byte-for-byte round trip of the 633 clips and all #ACM in the corpus | 2–3 | `python studio_core.py --selftest` green |
| **M2 glTF bridge** | export/import with textures, victim bank, opponent in place; buttons in the Mod Kit; "Edit a camera in Blender" guide | 2–3 | Edit in Blender → mod → seen in game |
| **M3 Studio MVP** | §4.2 tkinter window + save as mod with backup and validation + reserved slot | 5–8 | A non-technical user redoes an ultimate's camera without a console |
| **M4 Animation (F2)** | retime + poses via Blender + add animations | 5–10 | A retimed technique with hits on their frame |
| **M5 SPX (F3)** | full disassembler → timeline → in-place edits → insertions | 10–20 | Reading verified on 38 scripts; edits without crashes |

**Risks and mitigations:**
- **Incomplete SPX opcodes → crashes.** Until the interpreter is known, read-only and in-place changes only.
- **Wrong camera frame or mirroring assumption.** M0 settles it with 1–2 captures; the Studio draws with what is verified.
- **Clip longer than the script's wait.** It gets cut.
  - The timeline shows the wait.
  - To lengthen it, the wait must be edited (in-place change, F3).
- **Override grows with the game open → truncated read or crash.** Reserved size and fixed padding; if it does not fit, ask for a restart.
- **Blender versions.** The bridge uses standard glTF. Animated fov depends on `KHR_animation_pointer` (Blender ≥ 4.2; tested on 5.2); as a fallback, fov goes in `extras`.
- **Retimed animations desync hits or effects.** Shift AP frames with the same time function and validate.
- **User data.** Only `mods/` is written, with backups and a regenerable project; never the original AFS.

## 6. Open questions for the user

1. **MVP priority:**
   - redo technique cameras of **native** characters (override of their CAM bin)?
   - or give **ports** their own camera? Future Gohan has none and Zarbon uses his donor's.
2. **Blender:** do we recommend it as an option for the community, with the Studio also working without it? Or must everything work with the kit alone?
3. **Runtime dev tools:** can a "replay cinematic" key or a hot reload be added later? It requires C++ changes, recompiling and re-copying the DLLs.
4. **Scope:** are camera and animation enough, or are **effects** (beams, technique auras) expected too? That is another format (BSP) and much more work.
5. **Studio form:** a tab inside the Mod Kit or its own window launched from it? (Recommended: its own window.)
6. **M0 capture session:** when can it happen? The game is not opened while you are using the PC.

## Annex: files in this folder

- **Community guide:** `amc_guide.txt` (excerpt of `AMC_Guide.zip`).
- **Community editor:** `anim_editor_community.py` (`Animation_Editor.zip`: only swaps animations, no viewer).
- **Working copies:** `amc_288_ps2.bin`, `spx_288.bin`, `zarbon_camara_hd_copia.bin`, `cam288_rt_*.bin`, `zarbon_cam_rt_hd.bin`.
- **glTF exports:** `goku_idle_clip0.glb`, `goku_clip24*.glb`, `zarbon_clip3.glb`.
- **Renders:** `render/`.
- **JSON:** `out_ps2/`, `out_hd/`.
- **afs_pair cache:** `cache/`.
