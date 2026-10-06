# SESSION: REAL DRAW SEMANTICS (Path B PS2→B3 HD) — 2026-09-11

> Continues `SESION_GPU_DRAW_2026-09-11.md` and
> `SESION_VIA_B_RENDER_2026-09-12.md`. Here it is **proven** how the guest
> draws the AWG0 and why the port explodes. Read BEFORE touching the port.

## 0. 🔴 QUICK RESUME (read this first after a compact)

**WHERE WE ARE:** the PS2→B3 HD port has **CORRECT geometry + draw** (a single
draw `prim=6` strip; the guest uses VB+IB verbatim). The **only remaining
blocker is the SKINNING/RIG** (PS2 skin vs HD animation). None of this is a
delivery. (Later sections refine this: §21-§24.)
- ACTIVE reference mod: `_strip3` (slot **327**/Krillin, `prim=6` 1 draw).
- CLEAN canonical DLLs (no instrumentation) in `out/win-amd64-baseline`, the
  game build and `rexglue/bin`.
- Instrumented backups: `%TEMP%\opencode\draw_evidence\command_processor.cpp.*.bak`.

**REPRODUCE THE PORT** (PS2 Cell F2 → HD template e147 → slot 327):
```powershell
# 1) extract the PS2 model (#AMB or #AMO0) -> json
python "mod center hd\ports\port_ps2_b3_extract.py" <ps2_cell.amb> cell_extract.json
# 2) 44B windows + list IB (bone mapping by label). Generates and grows if needed.
python "mod center hd\ports\port_b3_windows.py" cell_extract.json <tpl_e147.bin> port.amb
# 3) IB -> STRIP (winding preserved) + null arms (+0x3C/+0x44) + desc[0]=B[0,n_ib)
python "mod center hd\ports\port_b3_strip.py" port.amb port_strip.bin
# 4) LZX /N:2048 + pad to multiples of 0x1000:
#    & "mod center\Xbox 360 Compression - Decompression tool .../xbcompress.exe" /N:2048 port_strip.bin port_strip.lzx
# 5) install (ONLY ONE active mod):
#    mods\<mod>\us\data_cmn.afs\327\geom.bin   <- port_strip.lzx (+pad)
# offline check (without opening the game):
python "awo_tools\render_bin_windows.py" port_strip.bin out.png "$PWD\awo_tools" 0 --strip
```
Reference files (in `%TEMP%\opencode\phaseb\`, regenerable): `e147.bin` (Cell
F2 HD AWG0 template, entry 147 of `us/data_cmn.afs`), `cell_extract2.json`
(Cell F2 PS2 extract), `port_cell_grow_fix2.amb` (port without strip),
`port_cell_strip3.bin` (port of the `_strip3` mod).

**NEXT STEP (cheap, 1 test):** isolate hands/face → emit ONLY the body (bones
0-33) and **omit the triangles with vertices of bones 34-47** (which in the HD
live in AWG1-16). If the body renders fine ⇒ the flap comes from the
hands/face (bones 34-47 put into AWG0). If it is still bad ⇒ the problem is
the rig/body. Alternatives in §6.

**GOLDEN RULE:** tests are done with **ONLY ONE active mod** (`.disabled`
marker); the runtime serves the first in alphabetical order.

## 1. METHOD (hard evidence, no speculation)

The following were crossed:
- The `dbz3_draws.log` capture (instrumentation of `command_processor.cpp`,
  a draw log with `dma`, `idx`, `prim`, and each draw's IB).
- The port's bin (`port_cell_grow_fix2.amb`, AWG0 5148 windows / 8724
  indices).
- The 0x60 descriptors of the `e147.bin` template
  (`awo_tools/phase_c_descriptors.py`).
- The canonical tool `awo_tools/awg_vertex_buffer.py` (windows model).

## 2. PROVEN FACTS (the important part of this session)

1. **The guest uses the port's IB VERBATIM.** The **33/33** body draws match
   index by index with `AwgVertexBuffer.load(port).indices()` at
   `(dma - 0x1BD00000)//2`. (This **refutes** the previous note "the guest's IB
   ≠ the file's": it was an **offset error** in the comparison.)
2. **The draws are governed by the 0x60 descriptors.** Each draw's
   `(dma-0x1BD00000)//2` == the corresponding descriptor's `B_start` (exact
   match for the 28 body + hands/face ones).
3. **The vertex buffer is a GLOBAL fetch**, not per part: `VF[95]`
   `addr=0x1BD04000 size=56628` dwords = **226512 B = 5148×44** (the whole
   window pool). The IB lives separately, just before
   (`0x1BD00000..0x1BD031xx`). **They do not overlap.** ⇒ **the `A` ranges do
   not affect the fetch**; only `B` + prim matter.
4. **The prim is PER DESCRIPTOR**: body = `prim=6` (raw Xenos =
   `kTriangleStrip`), hands/face = `prim=4` (= `kTriangleList`). It correlates
   1:1 with:
   - 0x60 descriptor field **`+0x48`**: `0x500` (5) body / `0x400` (4)
     hands-face. The SDK's D3D enum: `kTriangleList=4`, `kTriangleStrip=5`.
   - the arms' part-descriptor field **`+0x30`**: 5 (bone0/body) / 4
     (hands/face).
5. **The port emitted the IB as a LIST** (`port_b3_windows.py` line 14/197:
   `ib = [i for t in tris for i in t]`). The guest draws it as a **strip** ⇒
   wrong triangulation ⇒ "explosion". **This is the root cause of the
   render.**
6. **The port's list IB is 100% valid** (0 degenerate triangles): the problem
   is not the mesh but its *interpretation* (list vs strip).
7. **The port's geometry is correct**: offline render (windows + list IB +
   `world[bone]`) = perfect Cell F2 (see `%TEMP%\opencode\phaseb\view_port.png`).
8. **🔴 THERE ARE TWO DRAW SOURCES (proven 2026-09-11 with a capture of all
   draws)**: the port is drawn with **6 distinct draws**:
   - `off=0 prim=6` (the body, the strip of `desc[0]`).
   - `off=4243/5251/5485/5611/6109 prim=4` (the **hands/face**).
   The offsets 4243+ do **NOT** come from the 0x60 descriptors but from the
   **arms' part-descriptors**, which store:
   ```
   +0x38 vert_start  +0x3C vert_count   (VERTEX range)
   +0x40 idx_start   +0x44 idx_count    (INDEX range)   <- the one that draws
   +0x48 label[]
   ```
   (bone0 body `idx[0,108)`; bone23 LHAND `idx[4243,4333)`; bone30 RHAND
   `idx[4747,4837)`; bone36/38 teeth `idx[5251,5293)/[5485,5527)`; bone40
   FACE `idx[5611,5711)`; bone47 `idx[6109,6173)`).
   ⇒ Nulling only `+0x3C` is **NOT** enough: **`+0x44` must also be nulled**.
   ⇒ **This was the 2nd source** producing the "flap" (hands/face drawing the
   port's IB at the template's offsets).
   Tool: `mod center hd/ports/port_b3_strip.py` (now nulls `+0x3C` and
   `+0x44`).
9. **After removing the 2nd source, 1 single real draw remains** (`prim=6
   idx=8726 off=0`); the VB the guest receives is a **verbatim copy** of the
   file's windows (sample 11/11) and the IB matches ⇒ **VB+IB+draw correct**.
   Even so the model comes out deformed ⇒ **the remaining problem is the
   SKINNING**:
   - PS2 and HD labels **identical and in the same order** (bmap=identity) ⇒
     correct bone indices.
   - But 66% of the port's vertices fall on a bone different from that of the
     nearest HD vertex (the PS2 skin differs from the HD rig in border zones:
     sleeves, torso). The HD animation applied to the mesh with the PS2 skin
     deforms it badly (not visible in bind pose: `inv(bind)·model` cancels the
     bone).
   - ⇒ **The port needs the HD SKIN** (transfer bone+weight by neighbourhood),
     not the PS2 skin. Try `--hd-skin` **now that the IB is right** (the
     previous "makes it worse" note was measured with the exploding list port
     → no longer applies).

## 3. ATTEMPTS AND RESULTS (DO NOT REPEAT)

| Test | What it does | Result |
|---|---|---|
| `_grow327` | port as is (list IB + template descriptors) | explodes |
| `_desc_one` | 1 descriptor `B=[0,n_ib)`, `+0x48=4` (list), the rest at `B_c=0`, arms `+0x3C=0` | **still explodes** ⇒ `+0x48` is **not** enough to change the draw's prim (or the guest does not read it from there) |
| `_strip2` | IB rewritten as **one strip** (winding preserved) + 1 descriptor `B=[0,n_ib)` | **changes** the deformity: head/torso/arm are recognisable, but it **still explodes** with a giant flap |
| `_fit_strip` | **decimated** port (`--fit`) + strip | **invalid**: `cluster_fit` deforms the mesh (useless for isolating) |
| **`_grow_tpl`** | **NATIVE Cell F2 template passed through `grow()`** (5148/8724), nothing else touched | **RENDERS PERFECTLY** ⇒ **`grow()` is FINE**. The port's flap is **NOT** from `grow()` ⇒ **there is a 2nd draw source** (or it comes from the port's data) |
| `_strip3` | strip + `desc[0]` + null arms (`+0x3C` **and `+0x44`**) | **1 SINGLE real draw remains** (`prim=6 idx=8726`); the guest's VB+IB correct; **but still deformed** ⇒ the remaining problem is the **SKIN** |
| `_hdskin_strip` | `_strip3` + **HD skin transferred by neighbourhood** (2587/5148 reassigned) | **MUCH WORSE** ⇒ HD transfer by neighbourhood does **NOT** work (matches the AGENTS note) |

**Conclusion of `_grow_tpl` (2026-09-11)**: `grow()` ruled out. The port
explodes because of a **second draw path** the port does not control, or
because of the port's own data (IB/descriptor). The next step is to **capture
the port's draws** to see how many there are and where they come from.

**Tool bug fixed**: `awo_tools/awg_vertex_buffer.py` `_parse` computed
`n`/`vb0` with the **maximum IB index**; in a file grown with `grow` the IB may
not reference the new stretch → wrong `vb0`. It now uses `g(0x2C)//44` (the
real size of the window buffer, the one the guest uses).

Note: `_strip2`'s strip was validated offline (render identical to the list
IB's, `orient_mal=0`, `faltan=0`). That is, the port's IB **is already a
correct strip**; something **additional** is still drawn badly.

## 4. TOOLS (persisted in the repo)

- `awo_tools/render_bin_windows.py <bin> <png> <awo_tools> [yaw] [--strip]`:
  correct render of the windows model (list or strip). Offline feedback.
- `mod center hd/ports/port_b3_strip.py <in> <out>`: stripifier **preserving
  order and winding** (walks the triangles IN ORDER and joins by edges;
  degenerate connectors with adjusted parity) + rewrites the descriptor to
  `B=[0,n_ib)`.
- `awo_tools/strip_order_winding.py <bin> <awo_tools> <out.txt>`: validates
  the strip (`orient_mal=0`).
- `awo_tools/phase_d_cmp_guest_ib.py <log> <port.bin> <awo_tools>`: checks
  whether the guest uses the file's IB (match per draw).
- `awo_tools/phase_d_descriptor_corr.py <bin>`: correlates descriptor fields
  with the draw's real prim (locates `+0x48`).
- Raw captures: `%TEMP%\opencode\draw_evidence\` (regenerable by
  re-instrumenting).

## 5. PROPOSED NEXT STEP (to resume)

**`grow()` is RULED OUT** (`_grow_tpl` renders perfectly). The port's IB is a
correct strip (validated offline). But the port still has a flap ⇒ **there is
a 2nd draw source**, or it comes from the port's data. Plan:

1. **Re-instrument** `command_processor.cpp` (backup with the instrumentation
   in `%TEMP%\opencode\draw_evidence\command_processor.cpp.dbz3bak`) and
   capture the draws of `_strip2`: **how many** draws the AWG0 does, with which
   `dma`/`idx`/`prim`. If there is more than one, the mesh-refs/arms/AWG1-16 are
   still producing draws.
   ⚠️ Remove the **dedup** by `(idx,dma)` so as not to hide repeated draws.
2. **Candidates for an extra source**: the mesh group's **mesh-refs** (0x50),
   the **arms' part-descriptors** (`+0x30` prim, `+0x38/+0x3C` range), and the
   **AWG1-16** (HD hands/face the port does NOT touch and that are still drawn).
3. Try **nulling completely** arms + mesh-refs + AWG1-16 and leaving ONLY
   desc[0] as a strip, to isolate.

⚠️ **Do NOT again** read `+0x48` as the single switch of the prim (proven that
it does not change the render). ⚠️ **Do NOT** repeat the "positional consumer"
analysis (refuted: it was the tool's index-base bug). ⚠️ **Do NOT** blame
`grow()` (proven OK with `_grow_tpl`). ⚠️ The **fit** (`cluster_fit`) deforms
the mesh → useless for validating the render.

## 6. REAL STATE AND CONCLUSION (2026-09-11)

**What is ALREADY solved in the port (do not touch it again):**
- The **geometry** is correct (perfect offline render).
- The **draw**: a single `prim=6` strip; the guest uses VB+IB verbatim.
- The **2nd draw source** (arms `+0x40/+0x44`) is located and nulled.
- `grow()` OK. The `awg_vertex_buffer` loader fixed.

**REAL remaining blocker = SKINNING/RIG.** The port's mesh carries the **PS2
skin**; the HD animation applied on top deforms it (not visible in bind
because `inv(bind)·model` cancels the bone). The % of bones that differ from
the nearest HD is high (~66%), and **HD transfer by neighbourhood makes it
worse**. This is the known underlying problem: **the HD is a RE-WORK of the
rig**, not 1:1.

**Suggested next experiments (cheap, one per test):**
1. **Restrict the mesh to bones 0-33** (body): remove/omit the faces of
   vertices with bone 34-47 (hands/face, which in the HD live in AWG1-16). If
   the body renders fine ⇒ the flap comes from the hands/face (bones 34-47 in
   AWG0).
2. **Keep the PS2 topology but the HD skin** with a better method than
   "nearest vertex" (e.g. transfer by the bone of the nearest HD vertex with
   per-region smoothing / propagation).
3. **Port by regions**: emit the hands/face in their own AWGs (1 bone) as the
   HD does, instead of putting them in AWG0.

⚠️ **Do NOT again** read `+0x48` as the single switch of the prim (proven that
it does not change the render). ⚠️ **Do NOT** repeat the "positional consumer"
analysis (refuted: it was the tool's index-base bug). ⚠️ **Do NOT** blame
`grow()` (proven OK with `_grow_tpl`). ⚠️ The **fit** (`cluster_fit`) deforms
the mesh → useless for validating the render. ⚠️ **Do NOT** `--hd-skin` by
nearest vertex (makes it worse, proven).

## 7. REFERENCES
- `awo_tools/awg_vertex_buffer.py` (windows model), `phase_c_descriptors.py`,
  `phase_c_meshgroup.py`.
- `mod center hd/ports/port_b3_windows.py` (emission; the `strip` pass still
  **needs** integrating), `mod center hd/ports/port_b3_strip.py` (strip + nulls
  arms).
- `docs/07_ports/SESION_GPU_DRAW_2026-09-11.md`,
  `SESION_VIA_B_RENDER_2026-09-12.md`.
- Raw capture: `%TEMP%\opencode\draw_evidence\`.

## 8. ISOLATION BY BONE (2026-09-13) — IN-GAME TESTS PENDING

**Finding (bone histogram, IB refs)**:
- **Template `e147.bin` (AWG0)**: uses **ONLY bones 0-33**. Bones 34-47 are
  NEVER referenced in AWG0 (their geometry lives in the auxiliary AWGs).
  Labels: 34-41 = mouth/teeth/face (`XCEL_M_*`, `XCEL_L00_FACE`), 42-47 =
  **tail** (`CEL_T_TAIL1-6`).
- **Port `port_cell_grow_fix2.amb` (AWG0)**: puts **1638 refs to bones 34-47**
  (908 vertices) INSIDE AWG0, including the **tail (43-47)** and the face. That
  is **structurally different** from the template ⇒ a direct candidate for the
  flap (the axes of those bones in AWG0 are not used by the template; the tail
  may have "dead" axes).

Detail (refs per bone, port): `32:1466` (vs 68 in the template) and `34-47`
add up to 1638; the template distributes those zones differently (`0:2058`,
`23:837`).

**Tests prepared** (`port_b3_strip.py ... --max-bone=N`, filters triangles
touching a vertex of bone > N, AFTER walking the list IB and BEFORE
stripifying):
- `mods/_body33` (**ACTIVE**): body only (bones ≤33). 2908→2320 triangles. If
  the body renders clean ⇒ the flap comes from mouth/face/tail in AWG0.
- `mods/_nottail` (`.disabled`): body+mouth/face (≤41), without the tail.
  2908→2700. Useful to refine if `_body33` comes out fine.

Verified offline (`render_bin_windows.py --strip`, `strip_order_winding.py`):
`orient_mal=0`, no NaN, healthy bbox in both. ⚠️ The offline render ALWAYS
comes out fine (it uses `world[bone]·pos` = model ⇒ cancels the bone): **the
flap is only visible in game**.

**How it was done**: `python "mod center hd\ports\port_b3_strip.py"
<port.amb> <out.bin> --max-bone=33` → `xbcompress /N:2048` → pad to 0x1000 →
install in `mods/<mod>/us/data_cmn.afs/327/geom.bin` (a single active mod).
Round-trip verified (`xbdecompress` = byte-identical).

**Expected interpretation**:
- `_body33` OK ⇒ re-route mouth/face/tail to their (1-bone) AWGs or exclude
  them.
- `_body33` still deformed ⇒ the problem is the **body/rig** (0-33), not
  34-47.

## 9. NEW REFERENCES
- `mod center hd/ports/port_b3_strip.py` (**NEW** `--max-bone=N`).
- Test mods: `mods/_body33` (active), `mods/_nottail` (disabled); ONE at a
  time.
- Intermediates: `%TEMP%\opencode\port3\` (`port_body33.bin`,
  `port_nottail.bin`, `check_bins.py`, `bonestats.py`, `labels.py`).

## 10. 🔴 DECISIVE GPU EXPERIMENT (2026-09-13) — RESULT

`command_processor.cpp` was instrumented (temporary, ALREADY REVERTED) to dump
per draw the **full `fc=94` palette + `fc=95` VB + IB** to `dbz3_capture.bin`
(format: 32 B header + `nslots`×(20 B + data) + IB). TWO games were captured on
the character select (slot 327):

- **Capture A** = port `_strip3` (explodes).
- **Capture B** = control `_grow_tpl` (grown NATIVE template; renders
  PERFECTLY).

### Findings (hard)

1. **The guest's VB is a VERBATIM COPY of the bin's windows** (captured and
   compared byte for byte). Geometry/IB confirmed.
2. **The `fc=94` palette is IDENTICAL between the port (which explodes) and the
   native (which renders perfectly)** — same values byte for byte (same
   scene/pose). ⇒ **THE PALETTE IS NOT THE PROBLEM.** The GPU receives exactly
   the same skinning.
3. ⇒ **The failure is in the per-vertex `(pos, bone)` data of the port's
   windows** (the PS2 skin applied to the HD rig), NOT in the draw, the IB or
   the palette.

### Palette data (for future sessions)

- `fc=94`: **128 matrices × 48 B** (6144 B) per draw; `endian=2`. The bone is
  read as 1 byte with `k8in32` ⇒ it affects byte **+19** of the window (not
  +16).
- ⚠️ The palette layout is **NOT** the naive "3×vec4 = 3x4 with translation in
  col 3": none of the interpretations tried
  (`%TEMP%\opencode\port3\pal_layout.py`) gives rigid matrices nor rebuilds
  the native. **There is a slot remap/offset that is NOT decoded** (the palette
  is NOT indexed by the raw bone: e.g. record 0 is zero and the native uses
  bone 0). Pending: decode the `bone -> palette slot` mapping (probably a base
  per draw/AWG).
- The port's capture was saved in `%TEMP%\opencode\port3\capture_port\` and
  the native's in `...\capture_native\`.

### Conclusion

Path B's root cause is the **`(pos, bone)` skinning of the windows**, which
comes from the **PS2 skin**. The palette/draw are correct. The real next step
is to fix the per-vertex bone assignment (parsing of the PS2 skin; see
`INVESTIGACION_PS2_HD_2026-09-13.md` §5-6: the PS2 formats use **weight tables
with 2 influences** — the extractor may be reading them wrong). Alternative:
clone the HD skin (different topology → only by region).

⚠️ **Instrumentation REVERTED** (`command_processor.cpp` back to 1616 lines, 0
marks) and the clean DLL (6165504 B) reinstalled in build-release, dual and
`rexglue/bin`. Captures and scripts in `%TEMP%\opencode\port3\`.

## 11. MODS — STATE AT CLOSE
- Active: **`cell_best2`** (Path A: PS2 body + HD hands/face; usable
  delivery).
- `.disabled`: `_strip3`, `_body33`, `_nottail`, `_grow_tpl`, `_bone0port` and
  the rest.

## 12. ITERATION 2026-09-13b — PS2 SKIN AUDIT + BONE0 TEST (RESUME)

### Where we left off (summary to continue)
- **Path B root cause confirmed**: draw + IB + **palette** are correct (the
  port's palette is IDENTICAL to that of the native `_grow_tpl` that renders
  perfectly — see §10). The failure is in the **per-vertex `(pos, bone, w)`
  data** of the port's windows (the PS2 skin applied to the HD rig).

### Skin audit (pipeline `port_ps2_b3_extract.py` → `port_b3_windows.py`)
- `extract_skin()` reads the PS2 rig's weight tables: for each bone there is a
  pointer at `amg + 32 + bi*80 + 52`; 32 B chunks at `rig+16+i*32`:
  `weight(+0), ch_len(+4), ch_loc(+8), sb_len(+12), sb_loc(+16)`. The vertices
  referred to (`amg+ch_loc+k*32+12`) are assigned to `[bi, weight]`
  (**first-wins**).
- **Coverage: 3922/5148 verts.** The rest (hand/face parts: bones
  23/30/36/38/40/47) **have NO skin** and fall to the **PART's bone**
  (`p["bone"]`) with `w=1.0`.
- Weights 0.2–1.0 (mode 1.0). The web confirms that Budokai PS2 uses **2
  influences (bone + parent, w and 1−w)**; the extractor **collapses to 1
  influence**.
- `port_b3_windows.py`: `hb = bmap[ps2_bone]` (label→label; for Cell F2 the PS2
  and HD have the SAME labels and order ⇒ `bmap` = identity). `w` = PS2
  weight.
- **Community reference for fine parsing**: `budokai ps2 2025.ms`
  (killercracker/SleepyZay, `modding resources update 3\3DMax\` or
  `...update 2\lean bone tutorial\budokai_updated.ms`): `weightData` =
  `weight, weightVertCount, weightVertOffset, weightVertCount2,
  weightVertOffset2`.

### Isolation test `_bone0port` → **CRASHES**
- `_bone0port` = the WHOLE port rigid to bone 0 (positions recomputed to
  `inv(world[0])·model`; bone 0 everywhere). **The game crashes** on the
  character select (nothing could be seen).
- ⚠️ **Revealing coincidence**: **record 0 of the captured palette is ALL
  ZEROS** (§10). If all vertices use bone 0 and its palette matrix is zero,
  everything collapses to the origin ⇒ degenerate geometry ⇒ probable crash.
- ⇒ **Strong clue: the palette slot is NOT indexed by the raw bone** (the
  native uses bone 0 and renders fine; record 0 is zero). There is an
  undecoded **`bone → slot` remap**.

### Live hypotheses (in order of probability)
1. **Undecoded `bone→slot` palette remap** (and the layout of the matrix's
   48 B, which is not the naive "3×vec4 = 3x4 with translation in col 3"
   either).
2. PS2 skin bone/weight assignment (2 influences collapsed to 1; 1226 verts
   without skin).
3. Bone-local computation (`inv(world)`) — less likely (the offline render of
   the native is correct, which validates `bind_worlds()` against the game's
   file).

### Next steps (next iteration)
0. **Do NOT try `_bone0port` again** (it crashes).
1. **Decode the layout + `bone→slot` mapping of the `fc=94` palette** using the
   saved captures (`%TEMP%\opencode\port3\capture_native\`). Method: in a
   neutral pose, look in the palette for matrices ≈ identity (the root bone's
   slot) and, for each bone, locate the slot whose matrix is a valid rigid
   transformation; validate by rebuilding the NATIVE (it must come out as Cell
   F2).
2. With `slot()` and the layout: `skinned = palette[slot(bone)]·[pos,1]`
   offline for the port and the native; locate exactly the vertices/slots that
   explode.
3. If the slot/layout is right and it still explodes → fix the **PS2 skin** (2
   influences) with the community reference.

### Reproduction commands (summary)
```powershell
# capture (requires re-instrumenting command_processor.cpp — backup in
# %TEMP%\opencode\draw_evidence\command_processor.cpp.instrumented.bak —
# and rebuilding rexgpu-xenos; do NOT forget to revert + reinstall the clean DLL)
# analyse:
python "%TEMP%\opencode\port3\compare_pal.py"     # palette port vs native
python "%TEMP%\opencode\port3\pal_layout.py"       # try palette layouts
# regenerate the port:
python "mod center hd\ports\port_b3_windows.py" <extract.json> <tpl.bin> out.amb
python "mod center hd\ports\port_b3_strip.py" out.amb out_strip.bin [--max-bone=N]
```

### Key files of this iteration
- Scripts: `%TEMP%\opencode\port3\` (`deep_analyze.py`, `compare_pal.py`,
  `pal_layout.py`, `bonemap.py`, `check_bins.py`, `bonestats.py`,
  `labels.py`).
- Captures: `%TEMP%\opencode\port3\capture_port\` and `capture_native\`.
- Mods: `_bone0port` (crash), `_body33`, `_nottail`, `_strip3`, `_grow_tpl`.
- Game state: CLEAN DLL (6165504 B), `cell_best2` active, 0 markers.

## 13. ITERATION 2026-09-13c — IB BUG SOLVED (the "explosion" was NOT the skin)

### How it was found (analysing the saved captures)
- The PORT's body draw was compared with the NATIVE's from
  `%TEMP%\opencode\port3\capture_port\` and `...\capture_native\`
  (`compare_pal.py`, `deep_analyze.py`, `repro.py`, `ib_stats.py`,
  `cmp_ib.py`).
- **The guest's IB matches the bin's `IB` up to index 6301** and from there on
  it is **GARBAGE** (`0xAAAA`, `0xD69A`, `0xFFFF`, indices up to 63891).
  6301·2 = **12602 B** = the **original template's** IB.
- **Cause**: `awg+0x34` = the **IB SIZE in bytes**. In the template it is
  `2*n_ib` in ALL AWGs (AWG1 816=2·408, AWG2 912=2·456, AWG3 1056=2·528…).
  `grow()` updated `0x2C` (VB), `0x30` (ib_rel) and `0x38` (end) **but NOT
  `0x34`** → the guest sized its copy of the IB with the old value (12602) →
  only 6301 valid indices → the rest produced out-of-range vertex fetches →
  **explosion**.
- **FIX** in `awo_tools/awg_vertex_buffer.py::grow()`:
  `set32(b, self.awg0 + 0x34, new_nib * 2)`.

### In-game result (after the fix)
- **It NO longer explodes**: a **connected Cell** comes out (deformed, but
  recognisable). The pipeline (windows + IB + draw `prim=6` + palette + `grow`)
  is **VALIDATED**.
- **Test `_strip4r1`** (EVERYTHING rigid to bone 1, `pos=inv(world[1])·model`):
  **Cell Form 2 in a PERFECT T-pose with correct textures, silhouette and
  scale.**

### Remaining blocker = SKIN/ANIMATION (reopened)
- `_strip4` (real PS2 skin) → deformed. `_strip4hds` (HD skin by nearest
  neighbour) → deformed. `_strip4w1` (PS2 bones, `w=1.0`) → **better**: leg and
  waist fine, torso/arms wrong.
- Checked: PS2 `world` == HD `world` (48/48) and PS2 `labels` == HD (48/48).
  The `parts`/skin are plausible (bone 32=head with 819 verts is normal: the
  native has the head in a separate auxiliary AWG).
- ⚠️ **All previous skin conclusions (session §12, `_body33`, `--hd-skin`) were
  made with the broken IB → INVALID.** Reopen the skin analysis.
- **Tools**: `awo_tools/awg_vertex_buffer.py` (fix applied).
- **Work mods (one active)**: `_strip4` (PS2 skin), **`_strip4r1` (rigid bone 1
  = PERFECT)**, `_strip4w1`, `_strip4hds`, `_strip4b33`, `_strip4nt`.
- **Scripts**: `%TEMP%\opencode\port3\{ib_stats,cmp_ib,maxidx,repro,
  pal_analysis,dump_pal,checkbone}.py`.

## 14. ITERATION 2026-09-13d — SKIN BY SURFACE (FAILED) + LIMITS

### What was tried
- **Skin transfer by surface** (`port_b3_windows.py --surface-skin[=w]`):
  closest point on the HD template's TRIANGLES in model space (barycentrics;
  the dominant vertex's bone). scipy cKDTree. Reassigns 3867/5148, mean dist
  0.60, max 7.4 (hands/face/tail are not in the HD AWG0).
- **In-game result `_strip4surf` = MORE DEFORMED** than the PS2 skin. ⇒ **the
  bone assignment is NOT the cause** (the PS2 skin, which is the authored one,
  is the best so far). `--hd-skin` (grid with radius ±1.5 u) also failed because
  of a radius bug; the surface one improves it but worsens the render ⇒
  discarded.

### Observed quality order (all with the IB already fixed)
1. `_strip4r1` (EVERYTHING rigid to bone 1) → **PERFECT** (validates
   geometry/pipeline).
2. `_strip4w1` (real PS2 bones, `w=1.0`) → **better**: leg+waist OK,
   torso/arms wrong. ⇒ the PS2 weight `w` gets in the way (blending with a 2nd
   influence that does not fit).
3. `_strip4` (bones + PS2 `w`) → deformed.
4. `_strip4hds` (HD bones by neighbour) / `_strip4surf` (by surface) → worse.

### New hard facts
- PS2 `world` == HD (48/48) and `labels` 48/48. `parts`/skin plausible.
- **The `fc=94` palette is NOT `world`** (bind): searching for the 12 floats of
  each `world[b]` in the palette (row-major / transposed / 4x3) → **0
  matches**. ⇒ the select **is not in bind**, or the 48 B layout is not a
  direct 3x4.
- Reproducing the draw with the captured palette gives huge values (garbage)
  **also for the NATIVE** ⇒ the `fc=94` capture is not an array of 3x4
  matrices readable this way; decoding the palette is **blocked**.
- **Deduction**: slot 0 of the captured palette is ZERO but the native uses
  bone 0 with 772 verts and renders fine ⇒ the shader **does not index the raw
  `palette[bone]`** (there is a remap/slot and/or a 2nd influence). Not
  reproduced yet.

### Conclusion / limit
- The **Path B pipeline is solved** (IB `awg+0x34`). The guest's **skinning**
  (`bone→slot` remap, real palette layout and 2nd influence) **is not
  decoded** and is the remaining blocker. Attempts to transfer the skin
  (neighbour/surface) **make it worse**, which suggests the problem is not
  "which bone" but **how the shader composes the transformation**
  (palette/blend).
- **Recommended next**: RE of the skinning shader (translate the Xenos VS) or
  capture the palette in a known pose to solve `bone→slot` and the 2nd
  influence blend. Delivery alternative: Path A (`cell_best2`).
- New work mods: `_strip4surf`, `_strip4surfw1` (one active at a time).
- New tool: `port_b3_windows.py --surface-skin[=w]` +
  `transfer_skin_surface()` (`_closest_on_tri`).

## 15. ITERATION 2026-09-13e — SKINNING VS DECODED + NaN PALETTE BUG

### How it was obtained
- The cvar **`dump_shaders`** was enabled (an existing REXCVAR in the SDK;
  `flags.cpp`, `translator.cpp:339`, `shader.cpp:122 DumpUcode`) pointing to
  `%TEMP%\opencode\shaderdump`. With `LoadUserSettings`/`rex::cvar::LoadConfig`
  any cvar of `dbz3_user.toml` is applied. One pass on the select dumped **91
  VS + 54 FS** (`shader_<HASH>.ucode.vert`, the Xenos disassembly).
- **Skinning VS** = those that fetch **Stride=11 (VB) and Stride=12
  (palette)**: 6 files (`2DD4268D7EE12280`, `9B2CDBD500DB8645`,
  `B4611D5E3A350359`, `D0D07B299C625324`, `DA9A3E04256563FF`,
  `F3AC1AA2FE3EA253`).
- Decoding (subagent) — **PALETTE LAYOUT (48 B/bone)**:
  `[T.xyz][qA.x][qB.xyz][qA.y][qC.xyz][qA.z]` (3 interleaved vec4). `qA` is the
  main rotation (3 components; `qA.w = sqrt(1-|qA|²)` rebuilt by the VS).
  `qB/qC` are auxiliary rotations for the intra-bone blend.
  - Skinning: `model = R(qA)·pos + T` (with `weight=1.0`; rigid per bone).
  - `pos` (offset 0) = **bone-local**; `bone` (offset 4 dw = byte 16) =
    **DIRECT index into the palette** (`vf1 + bone*48`, no remap); `weight`
    (offset 3) = **intra-bone** blend (not a 2nd bone); `normal` (offset 5)
    bone-local. Then `c0..c3` = world·view·proj.
  - **There is no per-bone scale field**.
- Validated: with the decoded palette, the NATIVE's VB gives a coherent
  humanoid (`dec_native.png`, bbox X[-10,9] Y[-6,17] Z[-8,12]).
  (⚠️ Later refuted, §24: B3 HD does not skin on the GPU.)

### 🔴 REAL BUG found (offline)
- The captured palette has **NaN entries in bones 42-49** (and 85,86): the
  game **does not define them** (the template's AWG0 only animates certain
  bones).
- The **native does NOT use them**; the **port DOES use 43-47 (the tail)** →
  `R·pos+T` = **NaN** → flying vertices/geometry → deformation/explosion.
- Remapping those bones to a valid one ⇒ finite bbox; but the render is still
  **fragmented** ⇒ **there is at least one other cause** besides the NaN.
- **Operational conclusion**: the port's skin **cannot use bones whose palette
  the template does not define** (42-49). They must be remapped (to the HD
  tail chain or to a valid bone) or the HD tail cloned.

### Files / config of this iteration
- `dbz3_user.toml`: added `dump_shaders = "…/opencode/shaderdump"` (REMOVE when
  the RE is done).
- `%TEMP%\opencode\shaderdump\`: 91 `.ucode.vert` + `.d3d12.bin.vert` (DXBC) +
  `.frag`.
- New scripts: `%TEMP%\opencode\port3\decode_pal_repro.py` (decodes the palette
  and renders native/port), `find_world_pal.py`.
- **Next**: (1) remap/clone bones 42-49 of the port; (2) investigate the
  remaining fragmentation with the palette now decoded (compare
  `R(qA)·pos+T` of the port vs the native vertex by vertex).

## 16. ITERATION 2026-09-13f — 🔴 ROOT CAUSE: OUR `world` IS WRONG

### The proof
- With the decoded palette (`decode_pal_repro.py`), the **NATIVE**'s VB gives a
  coherent humanoid; the **PORT**'s gives NaN (bones 43-47 with a NaN palette)
  and, after remapping them, stays **fragmented**.
- But when rebuilding the NATIVE model with **OUR `world`**
  (`world_ours[b]·pos`) the render comes out **WRECKED** (giant spikes), with
  the correct triangulation (list, as `port_b3_strip.py` reads it). It is NOT an
  artefact.
- Comparing the palette's `T` (the bone origin according to the GAME) with the
  translation of **our** `world`:
  - bone 1 (CEL_WAIST): palette `(0.92, 7.23, -0.11)` vs our `world` `(0,0,0)`
    → **diff 7.28**
  - bone 2 (CEL_LLEGROT): palette `(0.19, 7.80, -0.72)` vs ours `(1.32,0.65,0)`
  - differences of 2.8–21.6 units in many bones.

### Conclusion
- **`awo_tools/awg_vertex_buffer.py::bind_worlds()` does NOT give the real
  bind.** The AWG axes (stride 80) have **translations ~0** (quat + scale, but
  pos=0 in almost every bone) → accumulating by parent produces meaningless
  translations.
- **The offline "bind render" is ALWAYS clean** because
  `world·inv(world)·model = model` (self-consistent) → **it does NOT validate
  `world`**. That is why it went unnoticed all this time.
- **The rigid test (`_strip4r1`) looked perfect** because applying ONE bone to
  the whole model = a global transformation → the model stays coherent even if
  the frame is wrong. It did NOT validate the skin.
- 🔴 **Consequence**: `window_from_model` computes `pos = inv(world_ours)·model`
  in a WRONG frame → the guest's shader does `R_anim·pos + T_anim` and each
  piece goes to its place wrongly → **deformation**. This affects **Path B and
  also Path A** (the injection's "recognisable but deformed" was this).
- The PS2 skin (bone assignment) was NOT the problem; the problem is the
  bone-local FRAME (`world`).

### Where the real bind is (pending)
- The palette's `T` ARE the real bone origins (animated pose). In an identity
  animation frame, `(R,T)` = that bone's BIND.
- The AWG axes do NOT contain the translations. Look for the bind in:
  (1) an alternative convention of the axes (pos at another offset / without
  accumulating),
  (2) the table/zones of `AWG0+0x1F80`/`+0x2000` (packed non-clear-4x4 data),
  (3) derive it from the ANIMATION at frame 0,
  (4) capture the palette with the animation forced to identity.
- **Script**: `%TEMP%\opencode\port3\decode_pal_repro.py`. Test files:
  `nat_world_LIST.png` (wrecked) vs `dec_native.png` (coherent).
- **Note**: the captured palette has NaN in bones 42-49; the port uses 43-47
  (tail) → they must be remapped/cloned anyway.

### `world` conventions tried (2026-09-13f) — ALL fail
Render of the NATIVE rebuilding the model with different conventions (all
WRECKED, not a triangulation artefact — the LIST rule was used):
- `bind_worlds()` (accumulated quat + pos) → wrecked (`nat_world_LIST.png`).
- Only accumulated rotation → wrecked (`nat_rot_only.png`).
- Own quat without accumulating (world space) → wrecked (`nat_own_quat.png`).
- Transpose / inverse of the own quat → same.
⇒ **the AWG axes are NOT enough** for the bind (neither rotation nor
translation).
- The ONLY reliable source of the game's frames is the **captured palette**
  (`R_anim, T_anim`), but it is the select pose (NOT bind).
- Candidate pragmatic path (NEXT): **transfer the NATIVE's bone-local `pos`**
  (do not recompute with `inv(world)`): the port would use the HD skin "stuck
  on" (pos of the nearest HD vertex). Requires a reliable model-space
  correspondence (the current model space of `parse_parts` also uses the broken
  `world` → the correspondence must be solved separately, e.g. by UV/part).
- **Really pending**: find the real BIND (identity animation frame, or RE of
  the code that builds the guest's palette).

### §17. BIND INVESTIGATION (session 2026-09-13g) — hard results
The structures and all alternative hypotheses were reviewed in depth.
Conclusions (all verified with scripts):

1. **The window layout is correct** (it is NOT the bug): `pos@+0, w@+12,
   bone@+16 (value at +19), nrm@+20, FFFFFFFF@+32, uv@+36`. First windows of
   `e147`: `bone=21`, `pos=(2.80,0.89,0.34)`, `w=1.0`. Matches §3.4.9.
2. **The template's AWG0 bones are 0-33** (34 unique, 2948 verts), correct
   labels: `0=XCEL_BODY 1=CEL_WAIST 2=CEL_LLEGROT 3=CEL_LLEG1 …` (matches
   `bone_labels()`). The vertex's `bone` indexes the SKELETON.
3. **`bind_worlds()`'s hierarchy is CORRECT**: `+0x40` of the axis's 80 B
   structure is an offset rel. `awg0` → `awg0+poff` = address of the PARENT's
   axis (e.g. bone2 `poff=0xd70` → `0x1a30` = bone1's axis). Confirmed.
   (Careful: `0xd70` seen as a file offset falls in label strings — a
   coincidence, not a pointer to a label.)
4. **No axis convention rebuilds the bind** (exhaustive search: accumulate
   yes/no × quat conjugated/yes × pos rotated/yes × order parent·child /
   child·parent × quat xyzw/wxyz). Metric = length of BORDER edges between
   bones (the "spikes"): all ≥3.0 for a character of ~13 u (a correct bind
   would give ~0.1). Render of the NATIVE with `world` → wrecked
   (`nat_world_view.png`); with `rot` only, own quat, etc. → wrecked
   (`nat_own_quat*.png`).
5. **There is NO bind matrix table** in the file (scan of 4×4/3×4 with an
   orthonormal rotation → 0 candidates). The 0x130 blocks per bone (AWO+0x30 →
   0x4f860+i*0x130) are index tables, not transforms.
6. **The palette (`fc=94`, 6144 B = 128 entries × 48 B) is the ONLY reliable
   source** and is **IDENTICAL port vs native**. Decoded as a skin matrix
   `[T.xyz][qA.x][qB.xyz][qA.y][qC.xyz][qA.z]`, `model = R(qA)·pos + T`.
   `P[0]` = identity. `P·pos` = coherent model (`dec_native.png`).
   ⇒ \(P = M_{anim}·M_{bind}^{-1}\).
7. **The palette is NOT indexed by the skeleton's bone index in axis order**:
   `P·world_axes` (hypothesis "axes = select pose") does NOT give a coherent
   skeleton (`skeleton_anim.png`, bbox ±14). That is,
   `palette[b] ≠ transform of bone b`. **The palette's `bone→slot` mapping is
   still to be decoded** (already noted in §15).
8. `M_bind = palette⁻¹·world` tried → border 10.2 (worse). Discarded.
9. **`pos` is not world/model space**: the render of raw `pos` is also a mass
   (`nat_rawpos.png`), compact but spiky ⇒ it is bone-local, and needs the
   correct bind.

**Conclusion**: the blocker is double and localised:
(a) **decode the palette's `bone→slot` mapping** (why `P[b]` is not the
transform of bone `b` even though the shader indexes `vf1+bone*48`); and
(b) **obtain the real BIND** (`M_bind`). With (a) solved, the palette gives
`M_anim·M_bind⁻¹` and we could **use the (captured) palette itself as a baked
bind**: generate `pos_port = P_ref[b]⁻¹·model_ps2` (palette frame), which at
reference time reproduces the PS2 model exactly and animates by
`P_t·P_ref⁻¹`. It is the shortest path to a port that RENDERS.

**Next experiment (cheap, decisive)**: dump at runtime, PER DRAW, the palette
and the raw `bone` of each vertex, and **correlate** `bone → slot` using the
fact that the native renders: for each palette slot, find which bone (by its
vertices and known `pos`) uses it. Alternative: instrument the PPC function
that builds the palette (fills the `fc=94` buffer) — it is the RE that closes
the topic once and for all.

**Tools of this session** (`%TEMP%\opencode\port3\`): `nat_world_view.png`,
`nat_rawpos.png`, `skeleton_anim.png`, `bind_hyp_PinvAxes.png`,
`nat_own_quat*.png`.
**Current delivery mod**: `cell_best2` (Path A).

### §18. 🔴 BIG FINDING (2026-09-13g, 2nd part): the axes' `world` IS a perfect
### T-POSE skeleton — the problem is the vertex's bone mapping
Rendering ONLY the origins of `bind_worlds()` (bone→parent as lines):

- **`skel_worldT.png` = a PERFECT T-POSE skeleton** (head up, arms
  horizontal, spine, legs down). ⇒ **`bind_worlds()`'s hierarchy and
  translations are CORRECT and `world` IS the bind (T-pose).** We thought it
  was broken before: it was an artefact of the mesh on top blurring the
  reading.
- `skel_paletteT.png` (palette origins) = a standing figure NOT in T-pose ⇒
  **the palette = `M_anim` (select pose), NOT the bind.**

**The contradiction**: if `world`=bind and `pos` is bone-local, `world·pos`
should give the T-pose model. It does NOT (`nat_world_STRIPTRUE.png`, correct
STRIP triangulation `prim=6`, still spiky). Nor with `T+pos`, `R^T·pos+T`, etc.
⇒ **`pos` is NOT `M_bind⁻¹·model` with `world`'s bind.** The missing link is
the **mapping `vertex bone index → skeleton bone`** (σ), or a skin bind
orientation different from the display skeleton's.

**Data in favour of σ ≠ identity**: the metric "distance from the transformed
vertex to the bone origin" does not pick a unique `w` for each `v` (ties due to
left/right symmetry), consistent with a non-trivial remap. The vertex's `bone`
DOES index the palette directly (`decode_pal_repro.py` proved it: `P[B]·pos` =
coherent).

**How to attack it (cheap and decisive)**: since the palette = `M_anim` and
`world` = `M_bind`, the skin matrix is `S[v] = palette[v]·world[?]⁻¹`; solving
which skeleton bone makes `S` consistent (or directly: which `world[w]` makes
`world[w]·pos_v` smooth) gives σ. Implement a per-bone solve with a border-edge
metric (not the distance to the origin, which ties).
**Definitive alternative**: instrument the runtime to dump, per bone, the
**inverse-bind buffer** the guest uses (and/or the real `M_bind` matrix).

### §19. 🔴🔴 INSTRUMENTATION DONE (2026-09-13h): **the palette = `M_anim`**
`rexgpu-xenos` was instrumented (a block in `ExecutePacketType3Draw`, case
`kDMA`, gated by `dbz3_drawlog.on`) to dump the IB, all the vertex fetches and a
**32 KB window of guest memory** around each buffer. Capture on the Select
(many characters and costumes): `out\build\win-amd64-release\dbz3_draws.log` +
`dbz3_bufs.bin`. **Instrumentation REVERTED and clean DLL reinstalled**
(6165504 B, `command_processor.cpp` 1616 lines, 0 `dbz3` refs).

Findings (**big-endian** bytes):
1. The skin buffer (fetch of 6144 B = 128×48) decodes as a known palette:
   `P[1]=(0.922,7.225,-0.112)` (Cell F2's waist!). **The palette's T COLUMN is
   a STANDING skeleton** (head y≈13, pelvis y≈7.2). ⇒ **the palette is NOT the
   skin matrix, it is `M_anim`** (the bone's animated world matrices). The VS
   does `model = M_anim·pos`; therefore **`pos = M_bind⁻¹·model`**
   (bone-local).
2. **`M_bind ≠` our `world` (axes)**: the `M_anim` (palette) and the bind share
   bone lengths (rigid); comparing parent-child distances, the real bind needs
   e.g. bone1 (waist) at **7.28** from the root, but our `world[1]` = `(0,0,0)`
   (no offset). In the leg chain the ratio is ~1.32 (select vs bind, different
   pose), but in the spine it does not fit ⇒ **the axes' bind is wrong (the
   root/waist offset is missing and/or the accumulation differs)**.
3. In the dumped memory **no dense array of 48 T-pose matrices** (bind) appears
   with stride 48/64 and bounded values — the guest probably **computes
   `M_bind` on the fly from the axes** and only persists `M_anim` (palette).

**Conclusion**: `M_bind` must be obtained from the guest (the axes with the
correct convention) or by capturing the palette in the **BIND frame
(T-pose)**.
**Short path to a port that RENDERS**: capture `M_anim` in the T-pose (bind)
state and bake it as `M_bind` ⇒ `pos_port = M_bind⁻¹·model_ps2` (in real time
it animates with `M_anim·M_bind⁻¹`). This is the line to follow.

### §19.b IMPORTANT NUANCE (2026-09-13h): the palette is the SKIN MATRIX, not `M_anim`
Looking at two contiguous palettes (`0x1BA72000` and `0x1BA76000`, both 6144 B =
128×48) their T columns differ per frame: `A[1]=(0.922,7.225,-0.112)` vs
`B[1]=(0.148,6.524,-0.114)` ⇒ they are TWO frames of the SAME character. And the
T column **is not a consistent skeleton** (e.g. head y≈0.05 but chest y≈12.4;
review: `palette[8]=RLEGROT` at y≈10.5 — impossible as a hip). ⇒ the palette is
the **skin matrix** `S = M_anim·M_bind⁻¹` (with bone-local `pos`), NOT `M_anim`.
`A⁻¹·B` = relative pose between frames (small values, not a skeleton).
Confirmed: **the blocker is exactly `M_bind`**, not decodable from these
captures (the guest computes it on the fly; there is no dense bind array in
memory).
**Options**: (1) RE of the PPC function that builds the skin (`S`); (2)
capture `S` in the BIND pose (T-pose) and use it as `M_bind`; (3) accept Path A
as the delivery. The instrumentation was left **REVERTED** and the DLL clean
(6165504 B).

---

## §20. 🔒 CLOSURE (2026-09-13i) — Path B PARKED; HD↔HD = validated delivery

User's decision: **option 3** for Path B (= parked "for now", not impossible),
and **close/polish the native B3 HD ↔ B3 HD swap** (which is validated and is
the real delivery). Path A remains as a documented approximation.

### 20.1 Layout findings (IMPORTANT, they apply to ALL the tools)
Verified on the `e147` template (Cell F2) reading the 17 AWGs:
- **ALL AWGs (0-16) use the SAME WINDOW VERTEX layout**:
  `pos.xyz@+0 | w@+12 | bone@+16 | nrm.xyz@+20 | 0xFFFFFFFF@+32 | uv.xy@+36`
  (stride 44). The `FFFFFFFF` marker is at `+32` in **100% of the slots of the
  17 AWGs**. The region is `[ib − g(0x2C), ib)` with `g(0x2C)/44` = exact
  number of slots (e147 AWG0: 2948; AWG1: 196; …).
- 🔴 **Historical BUG of `port_ps2_b3_inject.py`**: it used `sec_real = AWG0 +
  g(0x34) + 2` with the sec34 layout (`FFFF@+0`, `bone@+28`, `pos@+12`). For
  e147, that region **is NOT 44-aligned** (`(ib−start)/44 = 2938.27`) and is
  **shifted 428 B (=10 slots)** relative to the real window; the count
  `(g(0x2C)−g(0x34)−2)/44 = 2661` is wrong (real 2948). ⇒ the injection wrote
  into shifted slots.
- 🔴 **Historical BUG of `port_ps2_b3_inject_aux.py`**: it used a table of **6
  layout "families"** (different offsets per AWG). It is **wrong**: the 16 aux
  AWGs (hands/face) use the SAME window layout. The host bone (23/30/32) was
  correct.
- Fixes made: `%TEMP%\opencode\phaseb\make_winbody.py` (body with the window
  layout) and `make_winaux.py` (16 aux AWGs with the uniform window layout).
  Mods generated: `cell_winbody`, `cell_win2` (both tested in game).

### 20.2 Path A (approximate) result — PLATEAU
- The injection moves little (median ~0, max ≈0.8 u on a character of ~13).
- `cell_best2`, `cell_winbody` and `cell_win2` look **practically the same** in
  game: the layout fix improves torso/waist, but the visible faults (arms,
  shoulder, head, tail) are in the **body (AWG0)** and are **intrinsic to the
  injection** (it moves HD vertices towards the PS2 surface; it does not
  re-topologise). The aux (hands/face) changed bytes but is visually negligible
  (PS2 ≈ HD).
- ⇒ Path A does NOT beat the native HD. For a model that exists in HD →
  **native swap**; for one that does NOT exist in HD → approximate Path A
  (ceiling = the template).

### 20.3 Path B (real bind) — parked
- Single, localised blocker: **`M_bind`** (the skin's real bind matrix). The
  palette = the transform applied to `pos`; `pos` is bone-local; the axes'
  `world` ≠ `M_bind` (wrong bone lengths). There is no explicit inverse-bind in
  the file; the guest computes it on the fly.
- Community tooling discarded (`budokai_111616.ms`, `pose_matrix.py`, GitHub
  `SamuelDBZMAAM/Budokai-Modding-Tool`): they work at "model part" level, they
  do not rebuild the full rig.
- Paths to resume: (1) RE of the PPC function that builds the skin
  (`sub_82087F58`); (2) capture the palette in the BIND/T-pose frame.
- Evidence/artefacts: `%TEMP%\opencode\port3\` (`nat_*`, `skel_worldT.png` =
  the `world`'s correct T-pose, `skel_paletteT.png` = select pose),
  `%TEMP%\opencode\shaderdump\` (skinning VS), captures in
  `out\build\win-amd64-release\dbz3_bufs.bin`/`dbz3_draws.log`.

### 20.4 Validated delivery: native B3 HD ↔ B3 HD swap
- `mod center hd/swap_b3.py` (`--origen`/`--dest`/`--mod`/`--list`/`--verify`),
  catalogue `catalog_b3.cat` (183 entries). The runtime's virtual mid-insert
  covers bins > `to_read`. Validated in game (`cell_native`, Vegeta 424,
  Goten).
- **Implemented in the launcher** ("Model swap" tab): source/target selector,
  `[NOT PLAYABLE]` warning, mod auto-activation, output log, automatic or
  manual AFS path. Closing polish: removed the temporary log
  `pipeline_cmd.log`; source==target guard (`mod_pipeline.cpp`).

## 21. 🔴 OFFLINE PORT ORACLE (2026-09-30) — CORRECTS THE DIAGNOSIS

> Motivated by `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md` ("oracles"
> method: *reading the code is not the specification; the oracle is*).
> **Offline** comparison of decompressed bins, without opening the game or
> instrumenting anything. New tools: `awo_tools/bind_oracle.py` and
> `awo_tools/bind_oracle_bones.py`.

### Setup
1. Two real bins are decompressed with `xbdecompress` (the mod bins are LZX):
   - **GOOD reference**: `mods/cell_native/.../327/geom.bin` (native swap;
     renders fine in game).
   - **Path B**: `mods/cell_win2/.../327/geom.bin` (the port; deformed in
     game).
2. They are loaded with `AwgVertexBuffer.load(decompressed #AMB bin)` (⚠️ the
   tool expects the **full #AMB**, NOT an isolated #AWO: its parser uses
   `awo=0x40`).
3. `world[bone]·pos` (model space) is applied and they are compared.

### Results (hard, reproducible)

| Metric | native | win2 (Path B) |
|---|---|---|
| Windows / IB | 2948 / 6302 | **2948 / 6302 (identical)** |
| Bones / labels / used | 48 / id. / 34 | **identical** |
| **`world[bone]` (axes bind)** | — | **diff = 0.0 (IDENTICAL)** |
| **`bone` u32 @+16** | — | **0/2948 windows differ (IDENTICAL)** |
| **`uv` @+40** | — | **0/2948 differ (IDENTICAL)** |
| Model-space bounds | x[-10.229,12.771] y[-15.486,10.440] z[-3.139,5.019] | **almost identical** (Δx_min=0.045) |
| Position per bone (radii) | — | similar (same spread) |
| Selftest forward/inverse | OK | OK |
| Axis permutation | — | **xyz/+++ is the best** (no permutation) |
| **Connectivity (edge length)** | med 0.574 p95 7.17 max 26.6 | **med 0.593 p95 7.14 max 26.5 (≈identical, 1.00×)** |
| Fields `+0x2C`/`+0x34` (VB/IB size) | 129712 / 12602 | **identical** |
| Only differ | — | `pos` (+0) and `nrm` (+20), max 0.78 u (50 % of vertices) |

### Conclusion (CORRECTS §10 and §3.4.10)

- The **bind (`world`) is identical** to the valid native's → **the bind is
  NOT broken**.
- The **per-vertex bone assignment (+16) is identical** → **the PS2 skin is
  NOT being parsed wrongly**; the hypothesis "root cause = `(pos,bone)` skin"
  **is refuted** by offline evidence.
- The **IB, bones, UV** are identical; **there is no axis permutation**.
- The **connectivity is identical**: the port's edge lengths match the native's
  (med/p95/max ≈ 1.00×) → **there are NO crossed triangles**; the HD IB applied
  to the PS2 positions produces a mesh as coherent as the native one.
- The **sizing fields** `+0x2C` (VB size) and `+0x34` (IB size) are identical
  and correct (129712 and 12602).
- The only thing that changes is **`pos`/`nrm`** (the PS2 shape), inside the
  same volume.

⇒ **The port is structurally correct.** With ALL the offline checks exhausted
(bind, bones, UV, axes, connectivity, size fields, bounds, radii), the cause is
NOT in the bin. It must be at **runtime**: the **VB/palette served to the GPU
are not the port's** (copy taken from the native, or different fetch
`n`/`n_ib`) or the shader's **interpretation of `pos`/`nrm`**. New priority:
verify **in game** that the VB copied to the GPU matches byte for byte
`[vb0, ib)` of the **port**'s bin (not the native's).

⚠️ This requires **re-creating** the `command_processor.cpp` instrumentation
(the VB capture is **not** in the canonical DLL; only `dbz3_drawlog` remains,
which captures the vertex-fetch *layout*, not the bytes). The previous backup
(`%TEMP%\opencode\draw_evidence\`) **no longer exists** (cleanup).

### ADDITIONAL offline checks (2026-09-30, all negative)

More probes were added and run; **none** explains the deformed render,
reinforcing that the cause is at runtime:
- **Space of `pos`** (`space_probe.py`): the port is in **bone-local**
  correctly (`world·pos` err 0.71 = PS2 shape; raw `pos` err 6.02). It is not a
  space error.
- **Connectivity** (`topology_check.py`): identical edges → no crossed
  triangles.
- **Size fields** (`awg_fields.py`): `+0x2C`/`+0x34` identical.
- **`dbz3_vfetch.log`** (cvar `dbz3_drawlog`, present in the DLL): captures
  the shader's vertex-fetch **layout**, NOT the VB bytes → it does **not**
  distinguish port from native (same shader). It is useful for shader RE, not
  for this purpose.

⇒ **FINAL CONCLUSION (offline exhausted)**: the port's bind, bones, UV, axes,
connectivity, fields and space are **correct and identical** to the native's.
The failure is **exclusively at runtime**. The only step left: **re-instrument
`command_processor.cpp`** to dump the **bytes of the VB served to the GPU** in
the port's run and compare them with `[vb0, ib)` of the port's bin. If they
match, the problem is in the shader's `pos`/`nrm` interpretation; if not, the
runtime serves the wrong VB.

### Notes
- The offline analysis does NOT replace in-game verification (the oracle rule:
  "works in the fake host ≠ works in the game").
- Reproduce: see the header of `awo_tools/bind_oracle.py`.

## 22. 🔴 RUNTIME VERIFICATION OF THE VB SERVED TO THE GPU (2026-10-01) — RESULT

> Closes Block A of the oracles method. It required **re-creating** a temporary
> instrumentation in `rexgpu-xenos` (`command_processor.cpp`, d3d12): in the
> vertex-fetch residency loop, dump to `dbz3_vbdump.bin` the **REAL bytes**
> served to the GPU (copy from shared memory), gated by the marker
> `dbz3_vbdump.on` next to the exe. **ALREADY REVERTED** (code and canonical
> DLL restored; the clean code does not contain `dbz3_vbdump`).

### Setup
1. Instrumentation: dump by `dbz3_vbdump_one()` of the VBs with
   `size >= 16384 && size % 44 == 0` (only the model geometry).
2. **A single active mod**: `cell_win2` (the port). Cell F2 body (AWG0).
3. Real run (`tools/long_run.ps1` + `press_key.ps1`) up to the menu/select,
   where the model is drawn. ~60 fps, 0 errors.

### Result (hard)

The captured VB (`addr=0x1D23A000`, `vfetch=95`, `size=129712` = 2948×44):

| Comparison | sha1 | matching dwords |
|---|---|---|
| GPU VB vs the **PORT**'s bin (`cell_win2`) | `91fa3a12…` **==** | **32428/32428 (100 %)** |
| GPU VB vs the **NATIVE** bin (`cell_native`) | `91fa3a12…` ≠ | 21214/32428 |

⇒ **The GPU receives EXACTLY the port's geometry, byte for byte** (verbatim
copy of `[vb0, ib)` of the port's bin). It is **not** truncated, nor served from
the native, nor corrupted.

### DEFINITIVE conclusion (Block A closed)

Together with §21 (correct bind/bones/UV/IB/axes/connectivity/fields/space),
the **bin → shared memory → GPU** chain is **correct end to end**. The render's
deformity is **NOT in the data**. The cause is **exclusively in the skinning
shader** (how it interprets `pos`/`nrm` + the palette) or in the applied
**palette** — NOT in the bin, the IB, the binding or the transfer. (⚠️ Refined
by §24: there is no GPU skinning.)

⇒ Real next step (if Path B is resumed): RE of the **skinning shader** (what it
does with `pos`/`nrm` and the palette) — the `dbz3_vfetch.log` (fetch layout)
and the `dbz3_drawlog` help. The data port is already proven correct.

### Artefacts
- Evidence: `%TEMP%\opencode\vbdump\dbz3_vbdump_win2.bin` (37 MB, 200 VBs).
- Analysers: `awo_tools/vbdump_info.py`, `awo_tools/vbdump_vs_bin.py`.
- Cost: 2 builds of `rexgpu-xenos` (instrumented + reverted).



---

## §23 — Locating Path A's visual defect (`cell_win2`) — 2026-10-03

Context: during the Block A session it was observed that `cell_win2` (Path A:
NPM injection into the body + 16 auxiliary AWGs) renders a **coherent** Cell
but with **localised defects**: the **right arm** appears with grey faceted
planes (a disconnected "metallic" shell) and the **head** (crest) has an
intruding **grey wedge**. The `cell_native` (native swap) renders perfectly.

### Methodology (offline oracle, numpy+PIL)
Each AWG was rendered separately in model space (`render_aux.py`), applying to
each auxiliary AWG the **bind matrix of the body bone** that corresponds to it
by label:

| AWG | label (native) | body bone | socket |
|---|---|---|---|
| 1-5 | `CEL_L01/L02/L04/L05/L10_LHAND` | 23 (`CEL_L00_LHAND`) | left hand |
| 6-10 | `CEL_L01/L02/L04/L05/L10_RHAND` | 30 (`CEL_L00_RHAND`) | right hand |
| 11-16 | `XCEL_L01/L18/L09/L04/L05/L06_FACE` | 40 (`XCEL_L00_FACE`) | face |

Result: the port's auxiliary AWGs fall **in the correct sockets** and the
geometry **overlaps the native almost exactly** (green/red overlay). They do
**NOT reproduce** the defect's "shell" in bind pose. The defect does not
reproduce offline in a static pose.

### Field-by-field comparison (native.bin vs win2.bin, both 715872 B)

| Field | AWG0 (body) | aux hand AWGs (1-10) | aux face AWGs (11-16) |
|---|---|---|---|
| `pos` | differs (mean 0.149, max 0.797) | differs (RMS 0.13-0.21) | identical (0.000) |
| `nrm` | differs (dot 0.686, 307 verts opposite) | differs (dot 0.70-0.81) | differs (dot 0.87-0.95) |
| `uv` | identical | identical | identical |
| `weight`/`bone`/`marker` | identical | identical | identical |
| `IB` | identical | identical | identical |
| header/axes/bind | identical | identical | identical |

**There is no normal-rotation bug**: it was checked that port and native use
**the same convention** (applying `inv(R)` to the port's normals moves them
away from the native, not closer). The normal difference is a **legitimate
consequence** of the geometry (`pos`) differing.

### Conclusion
The arm/head defect in `cell_win2` is **inherent to Path A** (approximate
injection: the HD mesh's `pos` is projected onto the PS2 surface, whose
shape/silhouette does not match 100 %). In **bind pose** the geometry is almost
identical; the grey artefact appears because of **shading** (approximate
normals and silhouette) and is accentuated in **animation**. **It is not a
one-off bug in a field** of the bin.

⇒ To improve the arm/head there are two real paths: (a) **refine the Path A
injection** (thresholds / `--bone-aware` / `--normal-only` per zone), or (b)
**unblock Path B** (RE of the skinning shader, §22). The "grey shell" is NOT
fixed by touching up normals by hand.

### New tools (in `%TEMP%\opencode\viab\`, not versioned)
`render_mesh.py` (body with skinning), `render_aux.py` (all AWGs with the
correct bone's bind), `render_hand_overlay.py` (native/port overlay of one
AWG), `awg_fielddiff.py` (per-field diff), `awg_nrm.py`/`awg_nrm_geo.py`
(normals), `nrm_convention2.py`/`nrm_rotation_bug.py` (normal convention),
`awg0_region_diff.py` (AWG0 diff per bone).

### §23.1 — Runtime test: `cell_nfix` (2026-10-03)

Hypothesis derived from §23: if the grey artefact on the arm/head is
**shading** due to approximate normals, replacing the `nrm` field of ALL the
port's AWGs with the **native HD** normals (leaving the port's `pos`/`uv`/`IB`)
should remove the grey shell.

**Build** (`mk_nfix.py`): copies `nrm` (offset +20..+32, window layout) from
the native into `cell_win2` → `cell_nfix`. Verified offline: `nrm_dot` vs
native = 1.000 in the 16 aux AWGs and 0.960 in AWG0 (identical bytes; the 0.96
is an artefact of degenerate vertices in the metric). `pos`/`uv`/`IB`
unchanged.

**Setup**: mod `cell_nfix` as the only active one (slot 327), LZX `/N:2048`,
virtual mid-insert (123104 B > `to_read`). Real run (`tools/long_run.ps1`) at
60.0 fps, 0 errors.

**Result**: in the **3D attract demo** (battle), the mod's **Cell renders whole
and clean** — mottled green body, orange bands, head crest, extended arm with a
ki charge — **WITHOUT the grey faceted shell** that `cell_win2` showed on the
select (`shots\n_12.png`). Capture: `shots\nfix_08.png`.

**Honest caveat**: the clean capture is of the **battle demo** (a different
pose); it was not possible to capture the static select again for a 1:1
comparison (keyboard navigation with `press_key.ps1` / Return is unreliable: it
cycles title↔opening↔demo without entering the menu). So the test is
**qualitative** (a clean animated Cell is incompatible with the "exploded
geometry defect" hypothesis) but **not** a quantitative A/B in the same frame.

**Operational conclusion**: injecting the native HD normals on top of the PS2
`pos` **is a real, low-cost improvement** for Path A (without touching
geometry/IB/uv or the shader). It fits §23 (the defect was shading). It remains
a line of work to refine Path A, not a delivery (the delivery is still the
native swap).

**Artefacts**: `%TEMP%\opencode\viab\mk_nfix.py`, `win2_nfix.bin`,
`diff2.py`; captures `%TEMP%\opencode\shots\nfix_0*.png` (notably
`nfix_08.png`).

---

## §24 — RE OF THE SKINNING SHADER (Path B) — 2026-10-03

### DECISIVE finding: B3 HD does NOT skin on the GPU (neither VS nor memexport)

`rexgpu-xenos` (d3d12, `command_processor.cpp`) was instrumented with a
per-draw capture gated by the marker `dbz3_paldump.on` (writes
`dbz3_paldump.log`): `shader hash + indx_offset + count + c0..c63` of the VS
float constants.

1. **Ucode dump** (`dump_shaders`): 30 `.ucode.vert` + 54 `.ucode.frag`.
   - **NO vertex shader uses dynamic constant indexing** (no
     `a0`/`arl`/`c[a0+..]`/`lc` appear in any disasm). No indexed palette.
   - **NO shader (vert or frag) uses `memexport`/`alloc export`.**
   - The VSs are **rigid transformations**: `vfetch_full` of `vf0` (pos, nrm,
     uv) and `mad/mul` against **a single 4×4 matrix** in `c0..c3`.
2. **Per-draw capture** (656 MB, 3D scene reached with real focus):
   - **ALL body draws (count 360..1995, e.g. 1995) use
     `shader=FDF960B5D7869030`**, `indx_offset=0`.
   - Their constants: `c0..c3` = **a single world/view matrix** (4 rows),
     identical for the 1995 vertices; `c8..c11` = object identity/translation.
     **There is no per-bone matrix nor bone index anywhere.**

### Consequence (rewrites the hypothesis of §22)

- B3 HD's skinning is **CPU-side (Xenon)**: the guest reads the vertices in
  bind pose, applies the bone matrices and **writes a VB in world space**; the
  VS only applies the final rigid transform (c0..c3). It is the Xenon's
  "procedural synthesis / real-time skinning" model (MS patent 20050099417),
  consistent with Ars Technica.
- Therefore the port's deformation **cannot be "the shader"** by itself: the
  shader is generic and knows nothing about bones. The defect is born at the
  **input of the CPU skinning** (local bind pose + the guest's bone matrix) or
  in the **reconstruction of the world-space VB**.
- This **refines** §22: although bin→GPU is verbatim, the GPU does **not** see
  local bind pose as we assumed, but **pre-skinned world space**. The critical
  chain is `[bin's bind-pose vertices] → [guest's skinning routine] → [world
  VB]`.

### Implication for Path B / Path A

- The right question becomes: **in which space/order does the guest expect the
  bin's vertices for its skinning routine?** If it expects per-bone local bind
  pose (and we put something else in), the result deforms even if "the bind is
  identical".
- Viable Path B = make the port's vertices be in the **same per-bone bind-pose
  space** as the native, not just with the same scale/silhouette.
- Tools: not `rex/cvar`; the capture lives in `command_processor.cpp`
  (`dbz3_paldump_enabled`/`dbz3_paldump_draw`, marker `dbz3_paldump.on`, env
  `DBZ3_LOG_PAL=1`). **REVERT after the RE** (AGENTS §7: the canonical DLL has
  no instrumentation).

### Confirmation (2nd run, 730 MB): the matrix does NOT change per draw

25 consecutive body draws captured (`FDF960B5`, counts 3..1212):
`c0=1.44853 0 -0.00012 -0.00012` and `c3=0.0145 -33.4771 49.0088 50.008`
**identical in ALL**. That is, the body's "33 chunks" are drawn with **a single
rigid matrix**. ⇒ each chunk's vertices arrive **already in world space**: the
skinning happens **before** the VS (CPU Xenon), and the VS applies only the
view/projection.

### RE conclusion (Path B) — what to do with this

1. **The shader is not the culprit.** There is no palette on the GPU: looking to
   "fix the skinning shader" is a dead end (refutes §3.4.6/§10 Path B "shader
   RE").
2. The real blocker is **the guest's CPU-side skinning**: how it transforms the
   bin's bind-pose vertices into world space using the bone matrices.
3. **Correct Path B** = reproduce the **exact per-bone bind-pose space** the
   guest consumes ("identical world bind" at file level is not enough). The
   routine in the recompiled code that reads the bin's vertices and applies the
   bone matrices must be located, and the space/order it expects them in
   verified.
4. Measurement alternative: capture the **final world-space VB** in the body's
   draw (not the bin) to compare port vs native in the same frame/pose. The
   current instrumentation (`dbz3_paldump_draw` with `VF0`) does not hook that
   fetch (the body does not use `GetVertexFetch(0)`); the real fetch would have
   to be hooked (the VS's `vf0` ⇒ fetch constant index) to dump the served
   buffer.

### Artefacts

- `%TEMP%\opencode\shaderdump\shader_FDF960B5D7869030.ucode.vert` (the body's
  VS).
- `out\build\win-amd64-release\dbz3_paldump.log` (656 MB, delete).
