# ROADMAP — PS2 → B3 HD port (named pipeline)

> Date: 2026-08-26. Part of ESTUDIO_ECOSISTEMA_MODS.md. Defines the pipeline of
> tools specialised in **PS2 (#AMO0/#AMG LE) → B3 HD (#AWO/#AWG/#AZT BE)
> ports**, with names that state their purpose. The stable Launcher tools
> (`swap_b3.py`, `texture_b3.py`, `catalog_b3.cat`) are NOT touched; the new
> pipeline reuses them for LZX/padding/installation.

---

## 1. NAMING CONVENTION

Every tool in the port pipeline has the prefix **`port_ps2_b3_`** and lives in
`mod center hd\ports\` (a new folder, separate from the stable Launcher toolkit).
Each is a **single, self-contained script** (not dependent on the
`awo_tools/` experiments), with a documented CLI and internal validation.

```
port_ps2_b3_extract.py    → extracts and parses the PS2 model (mesh+rig+skeleton)
port_ps2_b3_geometry.py   → local coords + bone → HD buffers (sec34/vb2/IB)
port_ps2_b3_draw.py       → [KEY PIECE] HD draw structure from scratch
port_ps2_b3_pack.py       → packs a self-contained #AMB bin (AWO+AZT) + LZX
port_ps2_b3_verify.py     → feedback loop: OBJ export + bounds/NaN check
port_ps2_b3_textures.py   → #AMT (PS2) → #AZT (HD) (optional for now)
```

End-to-end pipeline: `extract → geometry → draw → pack → verify → install
(override)`. Each script outputs intermediate JSON (model structure, counts)
that the next one consumes, so each stage is validated in isolation.

---

## 2. PHASES

### Phase 0 — Validate the converter's premise (cheap)

**Re-test `janemba_from_cell` in game with the correct DLL** (it was never
validated because of the stale runtime of §13.6, now fixed). It is the HD bin
built by `build_from_template.py` (Cell F2 template, 48 bones = Janemba) with
Janemba's real geometry, structurally valid (0 NaN, plausible bounds). If it
renders → the draw structure of a template with the same bone count accepts
foreign geometry → the converter only needs to emit into a proven template.
If it crashes → the draw-structure generator (`port_ps2_b3_draw`) is the real
blocker and the focus goes there.

### Phase 1 — Consolidate the PS2 pipeline (already solved, renamed)

- **`port_ps2_b3_extract.py`**: clone/consolidate `parse_ps2_mesh.py` (mesh +
  real IB by FaceType) + `ps2_rig_skin.py` (rig: bone+weight per vertex, with
  the `amg_abs` offset resolved) + `pose_matrix.py` (world mats). Output: JSON
  with vertices (local pos, normal, uv), real IB, skin (bone+weight per
  vertex), skeleton (labels + hierarchy + matrices).
- **`port_ps2_b3_geometry.py`**: clone `ps2_to_hd_geometry.py` (local coords +
  bone → 44 B skinned sec34 format A + 44 B static vb2 + u16 BE IB). Output:
  JSON of HD buffers ready to pack.

### Phase 2 — The key piece: HD draw structure from scratch

**`port_ps2_b3_draw.py`** generates the structure the guest needs to
deserialize and draw, consistent with the new geometry:

- **AWG header** (nb=1 or n_bones per AWG, correct sec34/vb2/IB offsets for
  the emitted format).
- **Mesh-ref blocks + arms** (IB limits in bytes, 0x204 seals).
- **Submesh descriptors** (0x60 bytes; label at +00, `max N m` at +18, A ranges
  at +50/+54, B at +58/+5C — layout from SUBMESH_DATA_B3.md) and the AWG0
  submesh data area.
- **Axes/skeleton**: reuse the PS2 ones (same seals, §12.2) or copy the axes
  area of the HD template.

Study base: `analyze_meshgroup.py`, `analyze_mesh.py`, `awg0_export.py`,
`awg_cara_export.py` (parsing) + the community's `amg_c.py` pattern
(`b3_amg_*.bin` templates) translated to HD/BE. **This is the pending fine RE**
and the real milestone of the port.

### Phase 3 — Packing and installation (reuse the stable tools)

- **`port_ps2_b3_pack.py`**: packs the self-contained #AMB (header + AWO +
  AZT), compresses with LZX `/N:2048`, pads to to_read and generates the
  override `mods/<mod>/us/data_cmn.afs/<entry>/geom.bin` + manifest. Reuses
  the `swap_b3.py` utilities (compression/padding/installation).
- **`port_ps2_b3_verify.py`**: exports the built bin to OBJ with
  `awg_to_obj_b3.py`/`awg0_export.py` and checks 0 NaN + plausible bounds +
  triangle count (feedback in seconds without opening the game).

### Phase 4 — In-game testing with a real character

See §3. Criteria and candidates.

### Phase 5 — Automation and Launcher integration

- Once a character is validated in battle, expose it in the Model Swap tab
  ("PS2→B3 port") as an asynchronous pipeline (`ModPipeline::RunAsync`
  pattern).
- Extend `catalog_b3.cat` with the ported characters.
- (Long term) Automatic #AMT→#AZT textures with `port_ps2_b3_textures.py`.

---

## 3. TESTING PHASE — CHOOSING THE CHARACTER

### 3.1 Criteria (from the lessons in §5 of the study)

1. **Skeleton 1:1 with the target HD bin** (same game = no retargeting;
   rotation retargeting is where Janemba failed).
2. **Simple HD template** to validate the converter in isolation (not Krillin
   with 18 AWGs; prefer Babidi with 1 AWG or Bulma with 2).
3. **Available in B3 PS2 GH or IW** (unlimited access to the AFS).
4. Long-term goal: **add characters without an HD version** (IW).

### 3.2 Recommendation — two stages

**Stage A — CONVERTER VALIDATOR: Babidi (B3 PS2 GH → HD).**
- Why: Babidi's HD bin (entry 96) is the SIMPLEST template in the game (1 AWG,
  41 bones, simple format). Babidi exists in B3 PS2 GH with the SAME numbering
  (GH=HD, §5) → we have the PS2 source. 1:1 skeleton (same game). It lets us
  isolate each pipeline stage without the noise of Krillin's complex
  structure.
- **Important**: Babidi is not a playable character in the select screen. He
  is our technical guinea pig and is installed temporarily over Krillin (slot
  327) to check render, rig and structure.
- Validation: port Babidi PS2 → self-contained bin → install over Krillin as a
  test override → a correct Babidi must render in battle.
- If Babidi's PS2 GH skeleton differs in bones from the HD one (check with
  `scan_bones.py`), pick another simple template of the same character.

**Stage B — REAL PORT (adding content): an IW character with a 1:1 skeleton
to an HD one.**
- Search `ps2_games\Infinite World` and the 241 .amb files for a character
  whose skeleton maps 1:1 (same labels/order) to an existing HD bin.
- First candidate to rule out: an alternate costume of an existing character
  (AGENTS §3.1), or Pikkon/Pan if a compatible skeleton is confirmed (PKH with
  SKIRT → NOT 1:1 per §3.1; verify before committing).
- Validation: the new character appears in battle with the correct silhouette.

### 3.3 Testing-phase plan (steps)

```
1. Check Babidi PS2 in ps2_games\Budokai 3 Greatest Hits (USA)\USR\data_cmn.afs
   (same entry as HD = 96; decompress with xbdecompress).
2. `port_ps2_b3_extract` on the PS2 bin → JSON (verts/tris/skin/skeleton).
3. `port_ps2_b3_geometry` → HD buffers.
4. `port_ps2_b3_draw` → draw structure (fine RE, phase 2).
5. `port_ps2_b3_pack` → self-contained bin + override in a test slot.
6. `port_ps2_b3_verify` → OBJ + bounds (quick feedback).
7. Test in game on slot 327 (Krillin); do not use entry 96 as if it were an
   independent playable slot.
```

---

## 4. WHAT NOT TO DO (past mistakes, §5 of the study)

- Do NOT inject PS2 geometry into HD templates of another character.
- Do NOT rebuild the IB/arms of an existing HD bin (fixed counts).
- Do NOT use the B1 vertex layout (bone@+16) in B3 (bone@+28).
- Do NOT assume triplets in the PS2 IB (use FaceType).
- Do NOT compress with /N:32 or forget the padding to to_read.
- Do NOT trust the build's DLL without checking the virtual mid-insert
  (`Select-String rexruntime.dll -Pattern "AfsGetVirtualTable"`).
- Do NOT force Krillin's format A: each bin is self-contained (formats A/C).

---

## 5. STATUS AND NEXT STEPS

> **Update 2026-09-08**: the next PS2→HD test will not be another visually
> similar model over Krillin. The candidate matrix in
> `MATRIZ_CANDIDATOS_PS2_HD.md` will be used, starting with Babidi B3 GH if the
> scan confirms a 1:1 rig. The skeleton is validated first, then the
> geometry/packing.
>
> **Current blocker**: entry 96, expected to be Babidi PS2, returns a
> big-endian HD `#AMB/#AWO`; the extractor correctly rejects it. The AFS files
> locally labelled as PS2 must be verified before continuing. No port will be
> generated until a real LE `#AMO0/#AMG` source is available.
>
> **Progress made**: a real PS2 source of Tien with a cape was found
> (`Tien (With Cape).amo`) and the base rig passes 1:1 against Tenshinhan HD
> entry 400: 42 common labels in the same order; 10 extra cape bones. This is
> the active candidate for the next offline phase.

> ⚠️ **UPDATED at the close of the 2026-08-26 session (see SESION_PORT_RE §7.1).**
> The table below is the post-session reality; the original Phase 0 is
> SUPERSEDED and the real blocker is the structure→pool link (§5.2).

| Phase | Status |
|---|---|
| 0. Re-test `janemba_from_cell` (premise: does the template accept foreign geometry?) | **⚠️ SUPERSEDED by injection** (npm4): the template DOES accept foreign geometry, BUT only if the pool order is preserved. `build_from_template`/port reorder the pool → crash/deformation (cell_ps2_port CRASH 0x856AC389; reverse DEFORMS). |
| 1. `extract` + `geometry` (consolidate what is solved) | **✅ DONE 2026-08-26**: `port_ps2_b3_extract.py` (PS2→JSON) + `port_ps2_b3_geometry.py` (format-A HD buffers + groups per part). Geometry verified point by point = exact PS2 (nearest med 0.000). |
| 2. `draw` (RE of the HD draw structure) | **✅ LAYOUT MAPPED** (ESTRUCTURA_DIBUJO_HD: mesh-ref/axes/zone matrix/bboxes/A/B descriptors confirmed). **⚠️ The REGENERATOR for a reordered pool does NOT exist** — that is the real blocker (see §5.1). |
| 3. `pack` + `verify` (reuse the stable tools) | **✅ DONE**: `port_ps2_b3_pack.py` + `port_ps2_b3_verify.py` (OBJ + bounds/NaN). |
| 4. In-game testing | **🔴 SESSION RESULT**: first port (cell_ps2_port) CRASH. Full port (conv2) AMORPHOUS. **npm4 injection = WORKS** (best result). Reverse (inverted pool) DEFORMS → the pool order DOES matter. |
| 5. Launcher (Model Swap tab + catalogue) | PENDING (requires a path validated in game). |

### 5.1 🔴 THE REAL BLOCKER: THE STRUCTURE REFERENCES THE POOL BY ORDER

The reverse test (sec34 pool INVERTED + IB remapped + A/B recomputed,
mesh-ref/zones/bboxes intact) **deforms** in game. Since the draw log already
proved that the guest draws the strips via A/B descriptors + IB correctly, and
bone0 proved the transform uses the vertex's bone (+28), the deformation
implies that **SOMETHING ELSE in the structure references the pool by index**
(arms with vertex offsets, the zone matrix, or mesh-ref). Mechanism not yet
decoded.

**Implication**: a port with exact PS2 topology requires rebuilding the WHOLE
structure consistently with the new pool. Injection works because it keeps the
template's pool order → the structure stays valid.

### 5.2 LOGICAL NEXT STEP (order of work)

1. **Re-validate `cell_port_Afix_test` ON ITS OWN** (port with A fixed, without
   the npm8 contamination) — the cleanest full-port attempt. Prediction: it
   deforms (consistent with reverse). If it renders → the port is solved.
2. **Discriminating RE of the structure→pool link** (the unblocker): reverse +
   regenerate **ONE piece at a time** (arms / mesh-ref X/Y / zone matrix +
   bboxes) to find which one stops the deformation when fixed. That is the
   pending "mesh-ref/zones→pool link" of AGENTS §3.4.5.1.
3. **Decision** (informative): if the piece can be regenerated → the full port
   (Path B) is viable → write the structure regenerator (multi-session RE
   project). If it can NOT be regenerated (deep binding) → accept injection
   (Path A) as the practical port and invest in its quality (per-zone
   threshold for the head, seams).
4. **In parallel**: reactivate `cell_npm4` (best injection result) for a
   playable state.

**Key fact for the discriminator (2)**: the reverse test is done OFFLINE with
`pool_reorder_test.py` + OBJ verification (`awg_to_obj_b3.py`), and needs only
ONE in-game round trip per hypothesis.
