# GPU / DRAW SESSION — Instrumenting the pool consumption (2026-09-11)

> Goal: understand at **draw/GPU** level why reordering the pool inside a
> block deforms (T9) even though the IB is remapped (geometric identity), and
> so unblock **Path B** (PS2→HD port with PS2 topology).
> State: **instrumentation ready + first capture analysed**. The exact layout
> of the vertex buffer and the `vfetch` remain to be identified.

---

## 1. INSTRUMENTATION (SDK 0.10, rexgpu-xenos)

Edited `rexglue-sdk-0.10/src/graphics/command_processor.cpp` (the draw block
`VGT_DRAW_INITIATOR`, ~line 1345):
- `#include <cstdio>` and `<string>`.
- Helper `rexglue_dbz3_path(name)` → path next to the **exe** (robust to the
  CWD).
- Log **to a file** `dbz3_draws.log` (next to dbz3.exe), enabled by:
  - env var `DBZ3_LOG_DRAWS=1`, **or**
  - marker file `dbz3_drawlog.on` (next to dbz3.exe).
- Per **unique draw** (max 1500) it writes:
  - `DRAW prim=.. idx=.. src=.. isz=.. dma=.. nw=..`
  - `IB:` the **first 16 indices** of the index buffer (read from guest
    memory).
  - `VF[i] addr=.. size=.. endian=..` of each **vertex fetch constant** with
    `type=kVertex && address && size` (base of the vertex buffer), + the first
    **16 bytes** of the buffer.

**Build** (baseline):
```
cmake --build "rexglue-sdk-0.10\out\build-win-vulkan-baseline" --target rexgpu-xenos
```
Canonical output: `rexglue-sdk-0.10\out\win-amd64-baseline\rexgpu-xenos.dll`.
Copied to `out\build\win-amd64-release\rexgpu-xenos.dll` and `...-dual\`.

⚠️ **PENDING**: the canonical baseline DLL was left **instrumented** (6168064 B).
When the RE ends, **revert the edit** of `command_processor.cpp` and rebuild to
restore the clean baseline (for releases). The edit is documented here; no git
needed (the SDK is not versioned). (Later: reverted, AGENTS §3.4.5.)

---

## 2. CAPTURE

- Marker `dbz3_drawlog.on` set → game launched → battle **Cell (slot 327 via
  `cell_native`) vs Goku Costume 2** → closed.
- Log: `out\build\win-amd64-release\dbz3_draws.log` (233 KB, 4404 lines,
  **318 draws**). Copy in `%TEMP%\opencode\phaseb\dbz3_draws.log`.

---

## 3. FINDINGS (with evidence from the log)

1. **ALL draws are indexed**: `src=0` (=`SourceSelect::kDMA`), `isz=0`
   (=int16), in 318/318. **There are no auto-draws** (`kAutoIndex`).
   ⇒ The IB rules everything; there is no positional draw without an index.
2. **The IB indices are global indices of a unified space**: max observed
   **8490** (938 of 4960 sampled > 2936, Cell's AWG0 pool).
   ⇒ Indexing spans **several AWGs** (probably the whole AWO / a unified
   buffer), not just AWG0.
3. **315 distinct IB buffers** (`dma` addresses) for 318 draws.
4. **The vertex buffer is NOT the raw `sec34`**: e.g. `VF[95] addr=1BD1A000
   size=32428 endian=2` (32428 words ≈ 129712 B ≈ the size of Cell's pool) but
   its first bytes are `40 33 80 32 3F 63 9E 49 3E AF 7B 46 3F 80 00 00`
   = **vec4 (x, y, z, 1.0)**. The `sec34` starts with `FFFFFFFF` (marker) and
   small u/v ⇒ **the guest builds a derived vertex buffer** (positions), or the
   shader does `vfetch` at offsets (not distinguishable with 16 B).
5. The "large" VFs (`000FE3FC size=4850437`, `00000280 size=5502592`,
   `002CE1DC size=4195584`) are 4–5 M words ⇒ **they are not model buffers**
   (data/constants); the useful ones are those of size 1500–70000.
6. Candidate model buffers (size in words): `1BD1A000 32428`,
   `1D6B8000 32428`, `1D110000 69432`, `1D16E000 100012`, `1BA6F000 27005`,
   `1BA73000 22869`, etc. (two characters: Cell and Goku).

### Interpretation
The guest **transforms/repacks** the geometry into a GPU buffer (vec4 of
positions) and draws with the global IB. If the prepass wrote
`derived[i] = f(pool[i])` it would be consistent with any reordering; **T9
deformed**, so the prepass is NOT a simple per-index one (or the `vfetch` reads
the pool with an offset/stride tied to the order). **This is what remains to be
pinned down** (see §4).

---

## 4. NEXT STEPS (pre-chewed)

> Suggested order; steps 1–2 are offline (SDK code), 3–4 need a capture by the
> user.

1. **Log the shader's `vfetch`** (decisive). Instrument
   `rexglue-sdk-0.10/src/graphics/pipeline/shader/translator.cpp` (or
   `dxbc_translator_fetch.cpp`): when translating, dump per shader every
   `kVertexFetch` instruction with `{fetch_constant_index, offset, stride,
   format}` (position, bone index, weight...). We will know:
   - whether the position comes from a **16 B/vec4** buffer (repack) or from
     the `sec34` (44 B);
   - the exact `stride` and **offsets**;
   - where the **bone index** is read from (`sec34+28` or a separate stream?).
   Look at the access to `register_file_.GetVertexFetch(...)` in
   `interpreter.cpp:927` as a reference.
2. **Log `VGT_INDX_OFFSET`** (base vertex) in the draw: add
   `regs.Get<reg::VGT_INDX_OFFSET>()` to the `command_processor.cpp` log if it
   exists ⇒ rules out a positional base offset.
3. **Identify the guest address of the pool**: (a) dump the load address of the
   `#AMB` (log in `afs.cpp` when serving the override), or (b) scan guest
   memory for the `sec34` signature (`FFFFFFFF` sequence + known u/v of
   `e147.bin`). Compare with the `VF addr`s ⇒ know whether the body is drawn
   from the pool or from a derivative.
4. **Dump 256+ B of the candidate buffers** (not just 16) and **compare
   offline** with `e147.bin`/`e327.bin` to deduce the stride/layout and the
   position→slot mapping. (Increase the log's
   `for (int bi=0; bi<16; ++bi)`.)
5. **Differential capture**: the same scene **normal** vs **T9** and compare
   the derived buffers/IB ⇒ see exactly what changes in the draw.

### Files/tools
- Instrumentation: `rexglue-sdk-0.10/src/graphics/command_processor.cpp`
  (~1345).
- Log: `out\build\win-amd64-release\dbz3_draws.log` (copy in temp).
- Reference bins: `%TEMP%\opencode\phaseb\e147.bin`, `e327.bin`.
- Phase C tools: `awo_tools/phase_c_descriptors.py`, `phase_c_make_t9.py`,
  `awo_tools/awg_invariants.py`.

### Reproducing the capture
```powershell
# create the marker next to dbz3.exe
New-Item -ItemType File -Force "out\build\win-amd64-release\dbz3_drawlog.on"
# launch the game, enter a battle, exit
# read the log
Get-Content "out\build\win-amd64-release\dbz3_draws.log"
```

---

## 5. GLOBAL STATE (for /compact)

- **HD→HD (native swap)**: ✅ DEFINITIVE and validated (Cell F2 → Krillin 327,
  `mod center hd/swap_b3.py`, mod `cell_native` ACTIVE). Documented in
  `docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md`.
- **Path A (PS2→HD injection)**: works with limitations; only useful for
  characters WITHOUT an HD model.
- **Path B (PS2 topology)**: BLOCKED by the positional consumer.
  - Phase C located the map (part ranges / A of 0x60 descriptors + arms;
    `AWG0+0x1F80` = bind-pose matrices):
    `SESION_FASE_C_CONSUMER_2026-09-10.md`.
  - T8 (moving whole parts) = IDENTICAL; T9 (reordering runs inside a block) =
    DEFORMED. No position→bone table ⇒ GPU dependency.
  - **This session**: draw instrumented; all indexed; there is a derived vertex
    buffer; the layout/vfetch remain to be pinned down (§4).
- **Mods**: only `cell_native` active. Test logs removed.
- **WARNING**: the baseline `rexgpu-xenos.dll` is **instrumented** (restore it
  when the RE is closed). The log/marker are disabled without
  `dbz3_drawlog.on`.

---

## 6. PHASE 2 — VERTEX FETCH AND BUFFER LAYOUT (2026-09-11, 2nd capture)

> The **vfetch** (`translator.cpp` → `dbz3_vfetch.log`) and a **full binary
> dump** of the vertex buffers (`dbz3_vf.bin`) were also instrumented.
> Capture: Cell (slot 327 via `cell_native`) vs Goku costume 2.

### 6.1 VFETCH — stream layout (verified)
- **`fc=95`** = the model/character vertex buffer, **stride=11 dwords = 44 B**
  (the same size as the `sec34` record!). Offsets/formats:
  ```
  +0   fmt 57 = 32_32_32_FLOAT   position.xyz
  +12  fmt 36 = 32_FLOAT         w (1.0)
  +16  fmt 6  = 8_8_8_8 (used=1) BONE (u32 value = bone index)
  +20  fmt 57 = 32_32_32_FLOAT   normal.xyz
  +32  fmt 6  = 8_8_8_8          (4 B field; usually FFFFFFFF)
  +36  fmt 37 = 32_32_FLOAT      uv.xy
  ```
- **`fc=94`** = **bone matrix palette**, **stride=12 dwords = 48 B** (3× vec4 =
  3 rows of a 4×4), NOT a vertex buffer.
- Odd "large" VFs (`size` 4–5 M) = data/constants; ignore.

### 6.2 THE GPU BUFFER IS A VERBATIM COPY OF THE POOL, IN ORDER
Dump of Cell's body buffer (`fc=95`, `size=32428` words = **2948 records** of
44 B) against the `sec34` of `e147.bin`:
- **`buffer[i+10] == sec34[i]`** for **i=0..2660**: bones **2661/2661** and
  positions **max diff = 0.00000** (0 records with diff > 0.01).
- ⇒ The guest **repacks the pool keeping the order** (position/normal copied
  exactly, bone in 1 byte, `w=1.0`, marker at +32). **There is NO skinning in
  the buffer** (bind pose copied literally).
- `FFFFFFFF` markers at `+32` of each record (64/64 sampled).

### 6.3 THE GUEST USES THE FILE'S IB (verified)
- The drawn IB (read from guest memory) is a **CONTIGUOUS substring** of the
  correct character's file IB: for Goku (e270) **full match** (444/444,
  459/459, 162/162…). Earlier I compared against `e147` and it did not fit
  because it was **another character** (42 bones, buffer `25916` = e270
  `n_pool=2358`).
- ⇒ The guest **does not regenerate** the IB: it draws sub-ranges of the file's
  IB.

### 6.4 🔴 THE BUG: THE TOOL'S `sec` IS ~9-10 RECORDS LATE
- The file's IB references **0..2947** (max=2947 → **2948 vertices**).
- `buffer[10+i]==sec34[i]` ⇒ in the **IB**'s index space, the `sec34` starts
  at **+10**, not at 0.
- The ~10 records before `sec` **exist in the file** (region 15440..15866 in
  `e147`, next to a `max 0 m…` descriptor tag) and the guest includes them as
  `buffer[0..9]`. The IB **does** reference 0..9 (`e147`: 0→2, 1→5…).
- The tool (`phase_*` and `port_ps2_b3_*`) computes `sec=awg0+g(0x34)` and
  `n_pool=n_sec+n_vb2=2937` — **11 short** and **shifted ~10**. Any IB remapping
  done in that index space touches the wrong records.
- ⇒ **Strong hypothesis**: the T4/T9 deformations ("positional consumer") are
  **a tool index-base bug**, NOT a positional GPU dependency. Consistent with:
  the GPU buffer is order-preserving and the IB is the file's ⇒ **a consistent
  relabelling MUST be identity**.

### 6.5 WHY T2 (swapping 2 verts) CAME OUT IDENTICAL
`phase_b_make_t2.py` picks i,j from the **IB values** and touches the records
at `sec+i*44` (the tool's base). The ~10 mismatch may not show if i,j fall in
the same "bucket" or the pair is barely used. It does not invalidate the
hypothesis; an in-game confirmation is missing.

### 6.6 PENDING DECISIVE EXPERIMENT (T10)
1. Define the **real pool in the IB's space**: start at the first record of
   the marker run ending at `sec+2` (in `e147` = offset 15472; 9-10 extra
   records) and `n_pool = (vb2 - pool_start)//44 + n_vb2` (≈2948).
2. Apply a permutation (e.g. **reverse runs inside an A block**) in THAT space
   and remap the IB with the SAME index base.
3. **If IDENTICAL** ⇒ tool bug confirmed ⇒ **Path B unblocked** (the rebuilder
   only has to emit a pool consistent with the IB).
   **If it DEFORMS** ⇒ there is a real positional consumer (back to GPU).
- A simpler alternative for the 1st confirmation: **swap 2 whole records +
  remap the IB in the correct base** (must be trivial identity).

### 6.7 OTHER DATA
- Per-character buffers identified in the capture: Cell=`32428` (2948 recs, 34
  bones), Goku alt=`25916` (2356, 42), other=`22869` (2079, 28); `1536` (fc=94)
  = matrix palette.
- Instrumentation added: `translator.cpp` (`rexglue_dbz3_vfetch_path` /
  `rexglue_dbz3_vfetch_enabled`, uses
  `rex::filesystem::GetExecutableFolder()`); `command_processor.cpp` binary
  dump `dbz3_vf.bin` + `indxoff` in the DRAW line.

---

## 7. ✅ EXPERIMENT T10 — PATH B UNBLOCKED (GEOMETRY) (2026-09-11)

### 7.1 What was done
- New tool `awo_tools/phase_c_make_t10.py`: **full REVERSE of the `sec34`**
  (maximal permutation) + IB remap **in the guest's index base**
  (`IB'[k] = perm[IB[k]-10] + 10`; the historical one used base 0 = bug).
- Mod `_t10` (the only active one) with the bin compressed LZX/2048 + padded to
  118784. Offline validation of the tool: 5418 IB entries remapped, **OK**
  (each vertex resolves to the same record).

### 7.2 Result IN GAME
- **The model's geometry is EXACTLY THE SAME** as the normal Cell (confirmed by
  the user). ⇒ **A consistent relabelling IS identity** ⇒ the "positional
  consumer" of T4/T9 was the **tool's index-base bug**. **Path B unblocked for
  geometry** (position/normal/bone).
- **BUT the textures deform** (UV only; the model is fine).

### 7.3 Cause of the texture issue: UV SKEW (+1 record)
Verified offline on the normal buffer (`dbz3_vf_fase2.bin`, body buffer
`1B77F000`):
```
buf[i].uv == file_sec34[pos_index + 1].uv     1190/1190   (pos_index = i-10)
buf[i].uv == file_sec34[pos_index + 0].uv       63/1190
```
⇒ The guest **reads the UV of the NEXT record** (`pos_index+1`), not its own.
The file stores the UV **one row ahead** of the position (or the guest applies
a skew of 1). That is why moving whole records (T10) breaks the position↔UV
association even though the geometry is identical.

**Implication for the Path B rebuilder**: the 44 B records cannot be treated as
closed units; the UV of "logical row" k lives in record k+1. Options:
1. When permuting, **carry the UV with the skew** (the UV of row k goes to
   record `dest(k)+1`, or permute the UV field separately with the ±1 offset).
2. Or emit the PS2 topology respecting that shift of the UV table.
3. (Path A, injection, does NOT touch the order → immune to this.)

### 7.4 Conclusion
- **Geometry**: relabelling = identity ⇒ Path B's historical blocker was a
  **tool index bug**, not a GPU dependency. The pool can be reordered (taking
  the +10 base into account).
- **Textures**: the **UV skew (+1)** remains to be solved in the rebuilder.
  Before tackling it, it is worth confirming the skew with a minimal T11 (move
  a row and its UV+1 together → must be total identity, geometry + texture).

### 7.5 Files
- Tool: `awo_tools/phase_c_make_t10.py`.
- Test mod: `out/build/win-amd64-release/mods/_t10` (⚠️ now `.disabled`;
  `cell_native` restored as the only active one).
- Data: `%TEMP%\opencode\phaseb\e327_t10.bin`, `dbz3_vf_fase2.bin`,
  `dbz3_draws_fase2.log`.

---

## 8. ✅✅ PATH B READY — "WINDOWS" MODEL + T11 (2026-09-11)

### 8.1 The GPU buffer is a VERBATIM copy of a contiguous region
Checked byte for byte (`%TEMP%\...\basecmp.py`):
```
GPU buffer (fc=95, size 2948 windows) == file[15440 : 15440+129712]
                                         match 32307/32307 dwords
15440 = ib_abs - 2948*44 = vb0      (ib_abs = awg0 + g(0x30))
```
⇒ The guest **does not repack**: it copies (or binds) the region `[vb0, ib)` of
the AWO to the GPU buffer. The tool's `sec+2` grid is **misaligned by +428 B**
relative to the window grid; hence the "UV skew" of §6-7.

### 8.2 Each 44 B WINDOW is self-contained for the shader
```
+0   position.xyz  (3f)   fmt 57 = 32_32_32_FLOAT
+12  w             (f)    fmt 36 = 32_FLOAT
+16  bone          (u32)  fmt 6  = 8_8_8_8 (1 byte)
+20  normal.xyz    (3f)   fmt 57
+32  0xFFFFFFFF    (4B)   fmt 6  (unused)
+36  uv.xy         (2f)   fmt 37 = 32_32_FLOAT
```
The IB (`g(0x30)`, int16 BE) references window indices **directly**
(0..N-1). The guest **uses the file's IB** (§6.3).

### 8.3 T11 = permute WINDOWS + remap IB ⇒ TOTAL IDENTITY
- `awo_tools/phase_c_make_t11.py`: reverse of the 2948 windows +
  `IB'=perm[IB]`. Offline validation OK.
- **In game: PERFECT, geometry AND textures** (confirmed by the user).
- ⇒ **Path B fully unblocked.** Any consistent relabelling on the window grid
  is identity (position, normal, bone, UV, texture).

### 8.4 Canonical tool
`awo_tools/awg_vertex_buffer.py` — the real vertex buffer model:
```
python awg_vertex_buffer.py info <bin>
python awg_vertex_buffer.py permute <in> <out> [--reverse | --swap I J]
python awg_vertex_buffer.py roundtrip <in> <out>
# API: AwgVertexBuffer.load(path).vertices / .indices / .emit(out, vertices, indices)
```
- `permute --reverse` == T11 byte for byte (validated in game).
- `roundtrip` reproduces the original bin exactly.

### 8.5 PATH B RECIPE (PS2 → B3 HD port) — no more RE blockers
1. Choose an **HD template with the SAME skeleton** (bone count/order) and the
   same texture; axes, arms, mesh-ref and descriptors are kept.
2. Write the **N windows** (pos/normal/bone/uv) of the new geometry (converted
   to bone-local as in Path A).
3. Write the **new IB** (window indices) = PS2 topology.
4. Keep descriptors/arms (they do not affect the drawing — T6), or readjust
   them.
- **v1 limit**: N fixed = the template's capacity. Fewer vertices ⇒ pad the
  windows. More vertices ⇒ grow the region (internal mid-insert) = pending v2.

### 8.6 Old pipeline (SUPERSEDED)
`mod center hd/ports/port_ps2_b3_{geometry,draw,pack}.py` worked with the
**A/B descriptors + separate sec34/vb2 buffers** model, which is NOT how the
GPU draws. They must be rebuilt on top of `awg_vertex_buffer.py` (windows +
IB). Kept as historical reference.

---

## 9. ✅ FIXED SEMANTICS + PATH B v2 IMPLEMENTED (2026-09-12)

### 9.1 Field order: NATURAL (x,y,z), NOT (z,x,y)
The shader (vfetch) confirms `pos@0, w@12, bone@16, nrm@20, marker@32, uv@36`.
Comparing the HD `e147` with its PS2 equivalent (`cell_extract2.json`, same
model):

| | c0 | c1 | c2 |
|---|---|---|---|
| PS2 bone-local (inv(world)·model) | [-3.31, 6.21] | [-2.97, 5.03] | [-3.37, 2.33] |
| HD window pos | [-3.31, 6.21] | [-2.97, 10.44] | [-3.37, 2.33] |
| PS2 local normal | (0.48,0.48,0.55)… | | |
| HD window nrm | (0.47,0.50,0.53)… | | |

⇒ `window.pos = inv(world[bone])·model` and
`window.nrm = inv(world[bone]).R·model_nrm`, **both in natural order
(x,y,z)**. The HD and PS2 `world`s are **identical** (max diff 5e-7).
Format "C" was the `sec+2` grid misaligned by +428 B; **the window model is
universal** (Goku 264 also gives an integer bone at +16).
⚠️ **The Path A injection permuted** `(lc[2],lc[0],lc[1])` into
`(+12,+16,+20)` → that is why it was only "recognisable". The correct order is
`lc` directly.

### 9.2 Canonical tool (extended)
`awo_tools/awg_vertex_buffer.py`:
- `info` / `permute` / `roundtrip` / `grow` / `selftest`.
- `bind_worlds()` (80B axes: quat+pos, parent +0x40), `bone_labels()`
  (AWG0+0x40, stride 32), `window_from_model(pos,nrm,bone,w,uv,invw)`.
- `grow(new_n, new_nib)`: enlarges windows **and IB**, shifts the tail and
  readjusts AMB (0x24/0x30/0x34), the AWG table (rel. to awo) and the AWO
  header **[awo,awg0) (absolute pointers, per-bone table at +0x34/stride
  0x20)**. vb0 constant. Tail identical +delta verified. **EXPERIMENTAL** (2
  doubtful pointers of the old sec34 model remain in `[awg0,vb0)`; validate in
  game).
- `selftest <bin>`: forward(window→model)∘inverse = original (≤1e-7).

### 9.3 Path B converter
`mod center hd/ports/port_b3_windows.py <ps2_extract.json> <template.bin> <out>`
`[--fit | --no-grow]`: maps PS2→HD bones by label, emits windows + IB (triangle
list, prim=4) on the template. `--fit` = cluster-decimate to fit without grow.
Validated: rebuilding model space from the port == original PS2 (dist 0.0000).

### 9.4 In-game test
- `cell_extract2.json` (PS2 Cell) → template `e147.bin` (Cell F2 HD):
  - **fit**: 1907 verts / 2033 tris → mod **`cell_viab`** (entry **147**), no
    growth. **← main test.**
  - **grow**: 5148 verts / 8724 IB → mod `cell_viab_grow` (disabled).
- LZX `/N:2048` compression, pad to ceil(comp/0x1000)*0x1000, round-trip
  verified. `cell_native` (327) stays active (no collision: another entry).

### 9.5 ❌ IN-GAME RESULT (2026-09-12) — Path B does NOT render
**Important correction**: what looked like a "perfect Cell" was the **native
swap `cell_native`** (native HD bin in slot 327), **not** the port. In no logged
session was there an `AFS OVERRIDE HIT` for `cell_native`/`cell_viab` (AFS
logging does not capture `data_cmn` through a different path/cache, so the
absence of a log proves nothing; but the render is visible).

The port (`cell_viab`/`_grow327`, PS2 Cell → e147) **explodes on screen**:
- **Exact** geometry: the 5148 windows rebuild the PS2 model (dist 0.0000).
- **It reaches the GPU**: windows `win0..win3000` found contiguous in
  `dbz3_vf.bin`.
- After the `AWG0+0x2C` fix, the fetch covers the 5148 windows (56628 dwords),
  and the guest draws the body with `prim=4` (list) in ~11 chopped draws.
- Even so the model comes out **in pieces** (see §10).

**Cause**: the guest **splits the IB by the TEMPLATE's A/B descriptors/part
ranges**; since the port changes the topology, those ranges do not match →
wrong connectivity. Transferring the **HD skin** (`--hd-skin`) **makes it
worse** (rigging is not the main problem). ⇒ The **A/B ranges and mesh-refs
must be rebuilt**. Full detail: `SESION_VIA_B_RENDER_2026-09-12.md`.

> `grow` **is** mechanically fixed (2 bugs, see §10), but Path B remains
> **unvalidated**. The *definitive* test (porting a model absent from HD) stays
> blocked until the render is solved. (Later findings: the body is drawn as a
> strip, see `SESION_DRAW_SEMANTICS_2026-09-11.md`; and B3 HD skins on the CPU,
> AGENTS §3.4.10.)
