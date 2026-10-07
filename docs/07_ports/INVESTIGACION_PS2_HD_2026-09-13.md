# PS2→B3 HD RESEARCH — 2026-09-13 (subagents: web + RE + mods)

> Consolidation of 4 parallel investigations attempting to close the PS2→HD
> port (Route B). Read together with `SESION_DRAW_SEMANTICS_2026-09-11.md` and
> `AGENTS.md §3.4`.

## 0. EXECUTIVE SUMMARY

- **Nobody in public has done a PS2→HD Collection port of Budokai models.** The
  project is at the state of the art. Those who mod Budokai do it on PS2;
  those who touch HD only do textures/audio/HD→HD swaps.
- The community does have: (a) a **PS2 skinning pipeline** (budokai ps2
  2025.ms, `lean bone tutorial`, `OBJ_to_AMG`), and (b) **~430 `#AMB` models
  already converted from PS2 (IW→B3, B1→B3)** — but in **PS2** format, not HD.
- **Decisive technical finding (web)**: "correct in bind, explodes when
  animated" is the canonical symptom of **wrong bone indices / palette** (in
  bind the skin matrix is the identity for ALL bones ⇒ a wrong index is
  invisible in bind and explosive when animated).
- **New hard data**: `fc=94` = a palette of **128 matrices × 48 B** (3×vec4),
  **per draw**; the bone is read as **1 byte with `endian=2` (k8in32)**, i.e.
  byte **+19** of the window (not +16). The fetch is global (`fc=95`, stride 11).

> **Superseded (2026-10-03):** later RE showed B3 HD does **no GPU skinning**
> (no VS indexes constants; skinning is CPU-side) — see
> `SESION_DRAW_SEMANTICS_2026-09-11.md` §24 and `AGENTS.md` §3.4.10.

## 1. WEB — people/projects that matter

| Who | Where | Why |
|---|---|---|
| **WistfulHopes** | github.com/WistfulHopes/DBZ1 (+RB2) | **Another ReXGlue recompilation of the SAME game**. Same AWO/AWG path. Best potential collaborator. |
| **h3x3r** | ResHax topic/18350 | Author of the only public **#AWG** template (010 Editor). Confirms OUR 44-byte layout (pos/weight/bone/normal/FFFFFFFF/uv) and that hands/face do NOT use strips. |
| **NocturnalRhys** | ResHax | Explicitly working on **OBJ→AWG→AWO** for B3HD (+ A3T reimporter). Not published yet. |
| **killercracker / SleepyZay** | github.com/sleepyzay/Maxscript-Projects | `budokai ps2 2025.ms`: parses bones, AMGs, **weight tables (weightData)** and applies skinning in 3ds Max. |
| Community | B3 modding Discord, ReXGlue Discord | Modder venues. |

**Verdict**: contact WistfulHopes (same stack) and NocturnalRhys (same goal).
There is no public PS2→HD converter.

## 2. WEB — X360/Xenos skinning (why it explodes)

- Xenos **has no palette matrix unit**: the "palette" is a buffer the VS reads
  with an indexed `vfetch` by the vertex's bone. No emulator magic.
- **`fc=N` = fetch constant** (0-95). `fc=95` = vertex stream (44-byte
  stride); `fc=94` = **palette 48 B/matrix** (3×16, a compressed row of a 4×4).
- The shader reads **1 byte** of the bone field (`fmt=6` = 8_8_8_8,
  `used=.x`), swapped by `endian=2` (k8in32) ⇒ it affects byte **+19**.
- SDK format hints: `36=FMT_32_FLOAT, 37=FMT_32_32_FLOAT, 38=FMT_32_32_32_32_FLOAT, 57=FMT_32_32_32_FLOAT, 6=FMT_8_8_8_8`.
- **Ranking of causes of "bind OK / animated explodes"**:
  1. **Palette index space / per-draw base** (local vs global palette).
  2. **Wrong byte** in the bone field (position/endian).
  3. **Bone-local frame computed against ANOTHER skeleton's bind**
     (`local = inv(world_PS2)·model` when the game animates with `world_HD`).
  4. Endianness/format of the whole record.
  5. Assuming 4 influences when there is only 1 weight=1.0.
  6. Index outside the fetch constant's `size`.
- Recommended action: **dump the `fc=94` palette in the draw** and compare it
  slot by slot with the model's bones + a hexdump of the vertex's bone byte.

## 3. GUEST RE (recompiled code) — exact locations

| Concern | Location |
|---|---|
| AWO tag handler (relocates arms/mesh-group pointer trees + registers) | `generated\dbz3_recomp.11.cpp:3` (`sub_82080A40`) |
| Tag dispatcher (AWO/AMG/AZT/ACM/ACC/ACL/ACP) | `generated\dbz3_recomp.3.cpp:3` (`sub_820800A8`); registry at guest `0x82310110` |
| Skeleton walker (80 B, quat+pos+children) | `generated\dbz3_recomp.16.cpp:248` (`sub_82087F58`) |
| GPU command builders (PM4 packets, `stwu`) | `generated\dbz3_recomp.41.cpp:23855` (`sub_82241848`), `...23.cpp:23639`, `...36.cpp:8571` |
| Draw decode in the runtime | `rexglue-sdk-0.10\src\graphics\command_processor.cpp:1301-1397`; `packet_disassembler.cpp:213-251` |
| vfetch/formats in the runtime | `...\pipeline\shader\translator.cpp:379-453`, `translator_disasm.cpp:253-318` |

**RE conclusion**: **rigid single-bone-per-vertex** skinning (`+16`, 44 B)
against a **48-byte palette** built on the CPU from the 80-byte axes
(`sub_82087F58`). There is no code (nor hidden path) that compensates for a
bad index.

## 4. RESOURCE INVENTORY (mods + community)

### 4.1 Most valuable community resources (in `modding resources*`)
- `All Character Models from IW into AMB format\` — ~200 IW→B3 `.amb` (**PS2 format**).
- `Budokai 1 Models Converted to AMB\` — ~230 B1→B3 `.bin` (**PS2**).
- `Budokai Models\` (Son Swag) — `.amo/.amt/.amb` per slot + B3GHC exclusives.
- `update 2\MOD EJEMPLO\` — example mods in both formats (Ginyu Force, etc.).
- `update 2\lean bone tutorial\` — complete **RE-RIG workflow** (`budokai_updated.ms`, `Rig Data Tool`, `Goku_Skeleton.FBX`).
- `discord\research\00000002-00000002-b3.AMO.json` — the most complete **B3 AMO** breakdown (aerithdevs).
- `discord\research\B3_AMB_PS3.bt` — 010 template of the **HD AWO/AWG**.
- `discord\tools\` — `Model-Rig_Extractor`, `AMG_to_OBJ_V2`, `OBJ_to_AMG_v0.92`, `Bone_Addition_Tool`, `B3_IW_Model_Converter`, `Budokai_B3_IW_B1_AMO_Converter`, `axis_data.py`.
- `update 2\INFORME_modding_resources_update_2.md` — **best single reference** for PS2 formats (AMB/AMO0/AMG/AMT, FaceType, bone/axis 0x20).

### 4.2 State of the project's mods
- **Only `_body33` active**; 77 `.disabled` mods (all first-party; `NovaPowers` = the author).
- Route B: `_strip3` = best (1 strip draw, correct VB+IB, still deformed). `_grow_tpl` rules out `grow()`. `_body33`/`_nottail` = per-bone isolation.
- Route A: `cell_npm4_test` (best injection) / `cell_best2` / `cell_npm_fix` = **validated usable deliverable**.
- Diagnosis: `cell_bone0_test` (proves the guest uses the vertex's bone), `cell_clamp33_test`, `cell_boneclamp_test`.

## 5. NEW HARD FACTS (capture `%TEMP%\opencode\draw_evidence\`)

- `VF[94]` (palette) **always `size=1536`** dwords = **6144 B = 128 matrices**
  of 48 B. `endian=2`. **Per draw** (the address changes between draws).
- `VF[95] size=56628` (= **5148×44**, the port's AWG0) appears **33 times** ⇒
  the capture IS of the port (not of the native swap).
- `dbz3_vf.bin` = [VF95 of 6776 B (=154 verts×44)][**6144-byte palette** from
  offset 6776]. The palette has **slot 0 (bone 0) = ZERO matrix** and the rest
  affine matrices.
- The bone register is read from byte **+19** (due to `k8in32`), not +16.

## 6. MAIN HYPOTHESIS

The symptom (bind OK / animated explodes) + per-draw palette + PS2 skin
translated by label point to: **the port's per-vertex bone indices do not
select the same matrix the original HD mesh selected**. Candidates, in order:
1. The AWG0 draw's palette is built for the HD mesh and the port keeps the PS2
   bone index (by label) — it may not be the same "slot" HD uses for that zone
   (e.g. HD sends the torso to bone 0/23; the port to 1/16/32).
2. Some vertex with a bone whose axis in AWG0 is a placeholder (34-47) — but
   `_body33` rules out that this is the only cause.
3. `local` computed against a bind that does not exactly match the animated one.

## 7. PROPOSED PLAN (2 routes)

**Route B (research, decisive):** re-instrument the runtime to dump, per AWG0
draw, the **complete palette (6144 B)** + the VB + the IB. With that:
reproduce the skinning **offline** (`skinned = P[bone]·[pos,1]`), locate the
vertices that explode and which palette slot is the culprit; compare with the
NATIVE template (which renders fine) to find the exact difference.
Cost: rebuild `rexgpu-xenos` + 1 play session by the user.

**Route A (product, closing):** keep the injection (`cell_npm4`/`cell_best2`)
as the deliverable; document Route B as open research with this report.
