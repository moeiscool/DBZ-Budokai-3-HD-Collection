# CONSOLIDATION — #AMO0 → #AWO CONVERTER (complete status)

> Final document consolidating ALL the reverse engineering of the DBZ Budokai 3
> HD Collection (Xbox 360) model format and the converter's path.
> Created: 2026-08-13. Full detail in `awo_tools/RE_PROGRESO.md`.
>
> **Reading note:** chronological log; several conclusions were later refuted
> (the vertex layout, the "re-topology" theory, buffer sizes being fixed). The
> current verified facts live in `AGENTS.md` §3.2–§3.4, §6 and
> `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`. Data files under
> `%TEMP%\opencode\` no longer exist (cleanup 2026-09-02); regenerate them from
> `us/` + `ps2_games/`. Game data is never committed.

---

## 1. SUMMARY OF EVERYTHING LEARNED

### 1.1 The HD (360) format vs PS2

| Aspect | PS2 (Budokai 3 GH / IW) | HD 360 (Budokai 3 HD Collection) |
|---------|------------------------|-----------------------------------|
| Endianness | little-endian | **big-endian** |
| Container | `#AMB` | `#AMB` (2 entries: AWO + AZT) |
| Model | `#AMO0` | `#AWO` |
| Mesh group | `#AMG` (sequential blocks) | `#AWG` (via offset table) |
| Texture | `#AMT ` | `#AZT ` |
| Skeleton | identical (51 bones/68 labels Krillin) | identical |
| Geometry | vertices expanded per triangle | **re-topologized + per-vertex skinning** |

### 1.2 Empirically verified data

- **Krillin bin 327 is THE SAME model** in PS2 GH and HD 360 (51 bones, 18 AMG/AWG, 68 identical labels).
- The conversion is generic: Cell 54/19, Goku 64/19 (PS2 = HD).
- Krillin has **3 model bins** (327/328/329 = 3 costumes with 51/47/50 bones).
- The **#AZT texture format is solved** (A3T Analyzer, `mod center`).
- **No tool/documentation of the 360 format exists** anywhere in the ecosystem
  (1007 files with #AMO0, 0 with #AWO).

## 2. RECOMP INFRASTRUCTURE (what was NOT documented)

### 2.1 How the runtime's mod system works (CRITICAL)

The runtime does NOT replace the whole AFS. It uses a **per-entry override**:
```
mods/<mod>/us/<afs_filename>/<entry_index>   <- loose file with the LZX-compressed bin
```
- Code: `rexglue-sdk/src/filesystem/afs.cpp` (`AfsFindModOverride`) +
  `host_path_file.cpp` (`ReadSync`).
- The guest reads the bin with the **original AFS size** (from the header). The
  mod may be shorter (EOF), but not longer (it gets truncated).
- The bin must be **LZX-compressed** (`xbcompress /N:32`, magic `0F F5 12 EE`;
  later corrected to `/N:2048`, see §7).
- **IMPORTANT**: the decompressed bin must have the SAME entries as the
  original (Krillin bin 327 = AWO + AZT). If the texture is missing → crash.

### 2.2 The launcher builds an `active_region/` overlay
- `src/launcher/settings.cpp` `PrepareRegionData`: copies/links the files from
  `mods/<mod>/us/` into the `active_region/us/` overlay (full files).
- The runtime's `game:` drive points at the overlay.
- (Later: `PrepareRegionData` became a stub/dead code; per-entry overrides are
  served directly by the runtime. The PS5 build uses the same mechanism with
  mods under `/data/dbz3/mods/`.)

## 3. AWO STRUCTURE (complete)

### 3.1 AWO layout (offsets relative to the start of the AWO)
```
0x0000: header (0x30)
0x0030: bone relation table (bone × 32 B) → 0x690
0x0690: AMG offset table (amg × 4 B) → 0x6D8
0x06D8: bone labels (bone × 32 B) → 0xD40
0x0D40: AWG0 ... AWG17 (18 blocks)
0x42360: axes-array (51×24=1224 pointers to axes, referenced by +0x34)
0x46FE0: end of the AWO
```
**AWO header pointer +0x34 = offset of the axes-array (at the end).**
If the size of any earlier section changes, +0x34 must be updated.

### 3.2 AWG0 map (offsets relative to the AWG, bin 327)
```
+0x20 (0x6A0):  mesh part headers (880 B)
+0x14 (0xA10):  axes (7408 B, 80 B each, 13 axes)
+0x28 (0x2700): 294 B (small)
+0x34 (0x2826): MAIN VERTICES (86082 B = 1956 verts, stride 44)
+0x2C (0x17868): SECONDARY VERTICES (9984 B = 226 verts, stride 44)
+0x30 (0x19F68): INDEX BUFFER (10280 B = 5140 indices, max 2189)
+0x38 (0x1C790): 144 B (restart)
```
The IB indexes 1956+226 = **2189 vertices** (two vertex buffers).

### 3.3 HD vertex layout (stride 44 = 0x2C, aligned +2)
```
+00: nan (flag/w)
+04: VT.v
+08: VT.u
+12: V.z
+16: pos.x (bone-local / skinning)
+20: pos.y (bone-local)
+24: weight/bone index
+28: 0
+32: VN.z
+36: -VN.y
+40: VN.x
```

## 4. THE FUNDAMENTAL CHALLENGE (why it crashed)

**HD geometry is re-topologized + per-vertex skinning.**

- PS2 stores **absolute** vertices (V+VN+VT in 48 B LE), expanded per triangle.
- HD stores vertices with **bone-local positions** (skinning), reordered
  normals (Y negated), UVs, and weights/bone index.
- There is no 1:1 vertex→vertex correspondence (exhaustive test: 0/5 match).
- HD uses **two vertex buffers** (main + secondary) indexed by a shared IB.

## 5. THE 4 ROOT CAUSES OF THE CRASH (all fixed)

1. **Wrong mod structure**: a full rebuilt AFS was used;
   the runtime expects the loose file `mods/<mod>/us/data_cmn.afs/327`.
2. **+0x34 pointer (axes-array) not updated** when AWG0 grew.
3. **IB indices outside the VB** (read past the buffer).
4. **Missing #AZT texture**: the generated AMB only had the AWO; the guest looks
   for the texture and crashes. The decompressed bin must have AWO + AZT (682528 bytes).

## 6. NEXT STEP: SKINNING TRANSFORM

Converter v4 (`build_awo_v4.py`) already produces a bin with the correct structure
(AWO+AZT, same size, valid indices). The next step for the PS2 model to render is:

1. **Extract each bone's transform matrix** from the PS2 skeleton
   (the 80 B axes contain the transform).
2. **Transform each PS2 vertex (absolute) into its bone's local space**:
   `v_local = inv(bone_bind_matrix) * v_absolute`.
3. **Reorder into the HD layout** (stride 44): VT first, V.z, local pos, VN
   (Y negated), weights.
4. **Set the correct bone index and weights** in the HD vertex.
5. **Rebuild the PS2 index buffer** (triangle list → HD format).

This would make the PS2 model render with correct skinning inside the HD
structure.

### 6.1 PROGRESS: converter v5 (build_awo_v5.py) — skinning extracted

Converter v5 implements the skinning transform:
- **PS2 rig parsed**: 3056 skinning entries (bone, weight, local coords, offset to the vertex).
- **offset→vertex mapping SOLVED**: the rig offset is absolute within the mesh group;
  it lands in a part, and `(offset - vertex_start) % 48 == 0` gives the vertex index.
  Verified: offset 0x1FFD0 → part10, vertex 28 (0x540/48).
- **Vertices converted to the HD layout**: [nan, VT.v, VT.u, V.z, local_pos, weight, 0, VN.z, -VN.y, VN.x].
- Result: 4331 PS2 vertices transformed and ready for injection.

**PENDING (buffer re-layout)**: HD geometry uses 2189 UNIQUE vertices
in 2 buffers (main sec34 1956 + secondary sec2C 226). PS2 has 4331
expanded vertices. To inject:
1. Deduplicate PS2 vertices (by pos+normal+uv) → ~2189 unique
2. Rebuild the IB pointing at the unique ones
3. Re-layout the buffers (+0x34 and +0x2C) in AWG0 + update pointers

### 6.2 HOW THE RUNTIME DRAWS (decoded — key for the re-layout)

- Bone0's mesh group has `count=13` (13 mesh-ref blocks at +0x28).
- Each mesh-ref block has an `arm` = list of consecutive bones (0x17-0x24)
  with **offsets into the IB** (e.g. 0x24E0, 0x1E80).
- The arm offsets point to **u16 indices in the IB** (verified: 0x24E0 →
  [2057,2059,2058...]). The runtime draws those ranges per part.
- The HD IB has 5140 indices without restarts (strips/lists per bone).
- HD has ~1713 triangles vs PS2 1443 → denser geometry (re-topologized).

**The full re-layout (Option A) is the only viable way**: rebuild the
vertex buffers + IB + arms + mesh-ref blocks with the PS2 geometry. The
bones differ between PS2 (1-48) and HD (23-36) in which vertices they cover, so
the PS2 triangles must be grouped by bone and the arms rebuilt.

**Pending validation test**: mod `krillin_texture` (bin 327 with an altered
#AZT texture) to confirm that the mod + texture pipeline works
end-to-end. If Krillin comes out with altered color → the infrastructure is
correct and only the geometry re-layout is missing.

## 7. ROOT CAUSE #5 (THE DEFINITIVE ONE): THE LZX COMPRESSION PARAMETER

**ALL the crashes (including the texture-only one) were caused by LZX compression.**

- The original bin 327 in the AFS is **105296 bytes** compressed.
- `xbcompress /N:32` (the parameter we had been using) produces **128236 bytes**
  → LARGER than the original.
- The guest reads the bin with the **original AFS table size (105296)**.
  Since the mod is larger, it is **truncated** → incomplete LZX → crash.
- This explains ALL the crashes of ALL versions (v1-v5 and the texture one).

**Solution**: `xbcompress /N:2048` (2 MB blocks) produces **exactly
105296 bytes** (same as the original), with a perfect round trip.
- `/N:2048` → 105296 ✓
- `/N:1024` → 105296 ✓
- `/N:512` → 105650 ✗
- `/N:32` → 128204 ✗ (the wrong parameter we were using)

**Correct command**:
```
xbcompress /N:2048 <decompressed_src> <compressed_dst>
```

## 8. ROOT CAUSE #6: THE GUEST READS THE WHOLE SLOT (106496 bytes)

**Runtime instrumentation revealed the final problem**:
```
AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=121968
```
- The guest reads **106496 bytes** (the SLOT size from bin 327 to 328, not the
  bin size 105296).
- Slot 327 goes from 0x3AAE000 to 0x3AC8000 = 0x1A000 = **106496 bytes**.
- The real compressed bin 327 is 105296 (+1200 of padding in the slot).

**Fix**: the mod must be **at least 106496 bytes** (the slot). The compressed
LZX is padded at the end up to 106496 bytes. The round trip is
perfect (the decompressor ignores the padding).

**Command**:
```
xbcompress /N:2048 bin.bin bin.lzx   # gives 105296
# pad bin.lzx to 106496 bytes (slot) with 0x00 bytes
```

Verified: LZX padded to 106496 bytes → decompresses to exactly 682528. Game
boots stably.

## 9. ROOT CAUSE #7 (THE ONE THAT BLOCKED EVERYTHING): MULTIPLE ACTIVE MODS

**Even with a correct bin, the game crashed** because there were MULTIPLE mods
enabled at once (krillin_test, krillin_control, krillin_1byte, etc.).
The runtime (`afs.cpp` `ScanModDirs` + `std::sort`) looks up the override in
**alphabetical** order, and the first one that has the file wins. `krillin_test`
(with a BAD 121968-byte bin) won over `krillin_texture` (good bin).

**Solution**: disable every mod except the one under test
(`.disabled` marker in the mod folder).

## 10. ✅ VALIDATED END-TO-END (2026-08-13, afternoon)

**The per-entry override works perfectly.** Krillin loads without a crash
with the original bin recompressed:
- `mod_size=106496` (bin padded to the slot)
- `to_read=106496, got=106496` (the guest gets all the bytes)
- 4 reads of bin 327 (costume previews + battle)
- No errors in the log

**Mod bin REQUIREMENTS (CRITICAL)**:
1. Decompressed content: AWO + AZT (682528 bytes for bin 327)
2. Compress with `xbcompress /N:2048` (not /N:32)
3. **Pad to 106496 bytes** (the SLOT size the guest reads)
4. Only ONE mod enabled per bin (alphabetical order)

**NEXT STEP**: converter v6 with the converted PS2 geometry (skinning),
using the same bin requirements (AWO+AZT, /N:2048, padded to the slot).

## 11. ✅✅ MILESTONE CONFIRMED: TEXTURE MOD WORKS END-TO-END

**VISUALLY CONFIRMED** (2026-08-13): Krillin shows **red pixels on the
outer gi/outfit** (neck area) with the texture mod.

### #AZT texture format (360) — DDS DXT3

- Texture 1 of bin 327 is a **DDS DXT3** (256×256).
- Structure: DDS header (128 bytes) + DXT3 bitmap.
- A3T Analyzer: `data_offset` points to the DDS header, `data_offset+128` to the bitmap.
- DXT3: 4×4 blocks = 16 bytes (8 B alpha + 2 B color0 RGB565 + 2 B color1 RGB565 + 4 B indices).
- **To change the color**: modify the RGB565 colors of the DXT blocks
  (not "random" bitmap bytes — that produces no visible change).
  `color0 = (R<<11)|(G<<5)|B`, little-endian.

### Validated texture mod pipeline
1. Decompress bin 327 → #AMB (AWO + AZT).
2. Edit the AZT's DXT3 blocks (RGB565 colors).
3. Recompress with `xbcompress /N:2048`.
4. Pad to 106496 bytes (slot).
5. Place at `mods/<mod>/us/data_cmn.afs/327` (only active mod).

**This milestone proves the mod system works end-to-end** — the foundation
of hard modding (textures, and soon geometry/characters).

## 12. ✅ FINDING: GEOMETRY IS MODIFIABLE (deformation experiment)

**Visually confirmed** (2026-08-13): shifting the vertices of the main buffer
(sec34) of bin 327 in X (+3.0), **Krillin appeared deformed**
(very tall, deformed body), keeping the shape of the head and the shoes.

**Implications**:
- The runtime **renders geometry changes** (the position floats of the
  main buffer control the shape).
- No re-layout is needed to modify geometry — it can be altered in place.
- The head and shoes were preserved → they probably use other buffers
  (secondary sec2C) or other AWGs.
- The game did not crash; it was playable (though the camera aimed at the
  original height, and the intro was temporarily buggy).

**HD vertex layout (stride 44, main buffer sec34, aligned +2)**:
```
+00: nan (flag)
+04: VT.v
+08: VT.u
+12: V.z
+16: pos.x (bone-LOCAL — modifying here deforms the model)
+20: pos.y (bone-local)
+24: weight/bone
+28: 0
+32: VN.z
+36: -VN.y
+40: VN.x
```
**NOTE**: positions are bone-LOCAL (skinning). Shifting X uniformly is not a
translation of the model — it deforms because each vertex is in its bone's
space.

### 12.1 SECONDARY BUFFER = HEAD AND SHOES (experiment 2)

Shifting ONLY the main buffer (sec34), the head and shoes were preserved
→ **head/shoes use the secondary buffer (sec2C/vb)**, not sec34.

**Data**:
- IB: 5140 indices, 234 unique (1956-2189) point into sec2C.
- sec34 (main): 1956 vertices stride 44, `nan` at +0. Layout:
  `[nan, VT.v, VT.u, V.z, pos.x_local, pos.y_local, weight, 0, VN.z, -VN.y, VN.x]`
- sec2C (secondary): stride 44 but `nan` at +28 — DIFFERENT layout.
  vert0: `[-0.1370, 0.0434, 1.0000, 0,0,0,0, nan, 0.1683, 0.0473, -0.1428]`

### 12.2 EXPERIMENT 3: PS2 SKIN IN THE MAIN BUFFER (skinning feasibility)

**Result** (2026-08-13): replacing the 1956 sec34 vertices with the
first 1956 skinned PS2 vertices (rig 3056 entries, local coords):
- **Does NOT crash** → the runtime renders the skinned PS2 data.
- Krillin ends up CORRUPTED (only the front + one fist recognizable, with
  textures intact). The rest deformed. The red texture from experiment 1 is
  visible on the face → confirms textures are assigned per mesh part/material.

**Diagnosis**: the vertex order does NOT match. The HD buffer is
re-topologized (Krillin HD's specific order, 1713 triangles) and the PS2
vertices come in PS2 mesh part order (4331 expanded, 1443 triangles). Putting
them in slot by slot assigns each PS2 position to a different HD bone → corruption.

**Implication**: the PS2 skinning is VALID (data accepted by the runtime).
The problem is the TOPOLOGY (how the IB indexes). A correct conversion
needs a full re-layout: dedup PS2 vertices → ~2190 unique (they would fit in
sec34+sec2C = 2190 slots), rebuild the IB with PS2 triangles, and re-map
arms/mesh-ref. This is Option A of the plan (re-layout), now unblocked by
full-file mode (bins of any size).

**Useful data**: PS2 Krillin = 19 mesh parts, 4331 expanded vertices, 3792
unique (by pos+nrm+uv), 2492 unique position-only. HD = 2190 slots (1956+234).

## 13.5 BUFFER RE-LAYOUT (2026-08-14): STATUS AND BLOCKERS

**GOAL**: the PS2 geometry (2492 unique position-only vertices / 3792 by
pos+nrm+uv) does NOT fit in the 2190 HD slots (1956 sec34 + 234 sec2C). To
convert characters the **buffers must grow** (re-layout).

### 13.5.1 REAL AWO STRUCTURE (critical RE corrections)

- **AWO header** @0x40: `+0x18` amg_am(18), `+0x1C` AMG table (rel AWO),
  `+0x34` axes-base.
- The **AMG table** points to the **#AWG magic** (NOT +0x40). The AWG internal
  offsets (+0x2C vb2, +0x30 ib, +0x34 sec34, +0x38 restart) are **relative to the magic**.
  - BEFORE we thought `AWG = awg0_off + 0x40` (a mistake that broke everything).
  - CORRECT: `AWG = awg0_off` (the AMG table value points to the magic).
- The AWO header has **51 entries of 0x20** (one per bone) with pointers into
  the axes zone (0x42360+): `+0x34, +0x54, +0x74, ...` every +0x20.

### 13.5.2 "FULL FILE" MODE (rebuilt AFS) VALIDATED ✅

- The launcher copies `mods/<mod>/us/<file>.afs` to the `active_region` overlay.
- The **rebuilt full AFS** (with the original bin 327, recomputed table)
  **works perfectly** — Krillin loads and fights without a crash.
- This allows bins **larger than the slot** (the per-entry override is
  limited to the slot size 106496).
- (Later superseded by the virtual mid-insert of 2026-09-09: no full AFS copies,
  per-entry overrides may grow; see `AGENTS.md` §6.)

### 13.5.3 SCRIPT `build_big_amb.py` (buffer re-layout)

Usage: `python build_big_amb.py <bin_amb> <sec34|vb2> <n_verts> <output>`
- `sec34`: grows the main buffer (vertices 0-1955).
- `vb2`: grows the secondary buffer (head/shoes).
- Recomputes: AWG header offsets, AMG table (AWG1-17), 51 axes-zone pointers.

### 13.5.4 BUGS FOUND AND FIXED (causes of the crash)

1. **`AWG = awg0_off + 0x40`** (read the AWG offsets at the wrong
   position) → fixed to `AWG = awg0_off`.
2. **Double delta in the AMG table**: the "axes-zone pointers" loop
   (`for j in 0x34..0x700`) ALSO swept the AMG table (0x690-0x6D8). The
   AWG16/17 offsets (≥ axes_base) received a 2× delta → corrupt positions
   → guest null deref. **FIX**: exclude the AMG table from the loop.
3. **Duplicated AMB header** in the repack (corrupted the AWO pointers).

### 13.5.5 RE-LAYOUT RESULT (vb2 +536 slots, bin 1097792 bytes)

- **The model LOADS** (no longer crashes on selection) — big step forward.
- **PROBLEM**: the character's **right hand** is missing.
- **PROBLEM**: **crash when entering battle** (after loading).
- Filling the vb2 padding with **valid vertices** (cyclic copies) instead
  of zeros did **NOT fix** the hand or the crash.

### 13.5.6 OPEN HYPOTHESES (unresolved)

- The right hand uses IB indices (1956-2189 → vb2). The IB uses **234 slots**
  of vb2 but the real vb2 only has **226** (9984/44). With the re-layout vb2 grows
  to 762 slots; the runtime may misalign the hand's indices.
- The battle crash: the guest processes the secondary buffer vertices with
  the new size; it may expect a fixed vertex count per buffer.
- The mesh-ref blocks (0x1ED8, 13×0x50) and arms (offsets relative to the IB)
  stayed valid according to the RE, but the runtime may use the buffer size
  (ib - vb2) for something we have not mapped.

### 13.5.7 NEXT STEPS

1. **DECISIVE EXPERIMENT (2026-08-14)**: grow sec34 by only **1957 vertices
   (+1)** with a remapped IB → **CRASHES in battle**. The runtime expects
   `sec34_count`/`vb2_count` to be EXACTLY the originals (derived from the
   AWG header offsets). ANY size change breaks rendering.
2. **CONCLUSION**: buffer re-layout is INCOMPATIBLE with the runtime.
   The guest uses the counts derived from the AWG offsets to validate the
   indices drawn by the arms. When the sizes change, the counts do not
   match → null-deref crash in battle.
3. **VIABLE ALTERNATIVE**: keep the HD buffers at the SAME size and **decimate
   the PS2 geometry to ≤2190 vertices** (from 2493 unique), rebuilding the IB
   (the 4329 PS2 indices fit in the 5140 of the HD IB) and re-mapping the arms.
   The PS2 skin experiment (replacing sec34 data without changing the size)
   did NOT crash → validated that the runtime accepts in-place data changes.

> (Later correction: `grow()` in `awg_vertex_buffer.py` was validated on
> 2026-09-11 — a grown native template renders perfectly when `awg+0x2C` and
> `awg+0x34` are updated. See `AGENTS.md` §3.4.9.)

### 13.5.8 KEY FINDING: sec34 SENSITIVE, vb2 TOLERANT (2026-08-14)

**Decisive control experiment**:
- **vb2 +1 vertex** (sec34 intact at 1956): **ENTERS BATTLE**. There is lag,
  Krillin's textures flicker, the right hand (sometimes the left) is missing,
  but you can fight/interact/fire techniques. **Does NOT crash**.
- **sec34 +1 vertex** (vb2 intact, IB remapped): **CRASHES in battle**.

**Implication**: the runtime is sensitive to the sec34 size (main buffer)
but tolerant to vb2 changes (secondary buffer). This isolates the
behaviour:
- sec34_count is used critically (possibly validation/allocation in battle).
- vb2_count can vary without a crash (only misalignment of the hand indices).

**Pending data point RESOLVED**: sec34+1 WITHOUT remapping the IB also
**CRASHES** (this time in the preview on selection, Addr=0x7ff7f59c295c — the
same parsing point). With remapping it reached the preview but crashed in battle.

**FINAL CONCLUSION**: `sec34_count`/`vb2_count` are FIXED parameters the
guest uses to deserialize THE WHOLE model structure. Changing them (even
+1) breaks parsing → null deref. The guest derives these counts from the
AWG header offsets and uses them to locate later structures.

**Definitive implication**: NO buffer of an existing HD model can be grown.
To add an IW character (Janemba 4415 verts, Pikkon 3643, Pan 4517, Super 17
4604, Super Baby 4967 — all more than double Krillin's 2190 slots), the
**complete HD AWO must be built from scratch** with the character's correct
counts (not reusing Krillin's structure).

### 13.5.9 RUNTIME INSTRUMENTATION (completed 2026-08-14)

- The SDK was recompiled with ninja + clang (`rexglue-sdk/out/build-win-vulkan`):
  `ninja -C <build> rexruntime`
- Logging was added in `host_path_file.cpp` ReadSync:
  `AFS327 READ: off=... to_read=... entry_start=... entry_size=...`
- **DATA CAPTURED** (grown bin 327):
  ```
  AFS327 READ: off=0x3AAE000 to_read=131072 entry_start=0x3AAE000 entry_size=130752
  ```
  The guest reads the whole slot (131072), the LZX bin (130752) is served whole.
  The bin is read correctly; the crash happens WHILE PROCESSING the model, not while reading.
- **Restart buffer** (0x38, 144 bytes): contains u32 indices (FFFFFFFF, 1, 2, 3,
  ... 48) — sec34 indices, it does NOT need remapping (they point to 0-1955).
- The instrumented rexruntime.dll was copied to `out/build/win-amd64-release/` and
  `rexglue/bin/`. (That instrumentation was later reverted; the canonical DLLs
  carry none.)

### 13.5.8 WORKING FILES (re-layout)

| File | Purpose |
|---------|-----------|
| `awo_tools/build_big_amb.py` | Buffer re-layout (sec34/vb2) + AMB repack |
| `awo_tools/relayout_awg.py` | AWG0 re-layout (simple version) |
| `%TEMP%\opencode\b327_vb2fix4.bin` | vb2 +536 slots with the fixed AMG table |
| `%TEMP%\opencode\data_cmn_vb2fix4.afs` | AFS with the grown vb2 bin |
| `%TEMP%\opencode\data_cmn_original_rebuilt.afs` | Control AFS (original bin, works) |

### 13.5.10 ✅ MILESTONE: JANEMBA LOADS WITHOUT A CRASH (2026-08-14)

**First IW character injected into the recomp** — bin 327 with Janemba's
geometry (decimated to sec34=2386, IB=8484 indices) **LOADS without a crash**.

**What was validated**:
- The runtime accepts an AWO with sec34=2386 (larger than bin 329's 2277).
  Confirms variable counts work if the structure is coherent.
- The whole pipeline works: extract PS2 → skinning → HD layout →
  decimation (voxel cell=0.10) → rebuild IB → pack AMB → AFS.

**The problem (no crash)**: the model looks like a **"uniform mass"** — Janemba
is not visible. Cause: Janemba's vertices are in **coords local to Janemba's
bones (JNB_*, 48 bones)**, but Krillin's slot applies **Krillin's bone matrices
(KLL_*, 51 bones)** via the mesh group's arms. Different skeletons → each
vertex is transformed wrongly → mass.

**This is the re-rigging challenge** (documented in AGENTS.md): the
Krillin→Krillin skin experiment worked (identical skeletons); Janemba→Krillin
did not (skeletons differ in bone count and orientation).

**Tools produced**: `awo_tools/convert_personaje.py` (skinning + HD layout),
`awo_tools/decimar.py` (voxel grid), `awo_tools/build_janemba2.py`
(AMB construction with its own counts).

### 13.5.11 NEXT BLOCKER: MESH-REF BLOCKS + ARMS (2026-08-14)

**Janemba's model loads without a crash but looks like a deformed mass.** The
cause is that **Krillin's mesh-ref blocks + arms** define HOW the runtime draws
each part (which IB range, which bones, which material). With Janemba's
geometry and a different IB, those arms point at IB ranges that no longer
correspond → each part draws Janemba triangles in the wrong ranges.

**Mapped structure**:
- Mesh group @AWG+0x1F80: count=13, mesh-ref table @+0x28.
- Each mesh-ref block (0x50): +0x18 stamp (0x9000020C mesh / 0x8000020C rig /
  0x00000204), +0x1C arm ptr, +0x20 idx ptr (dat/material), +0x28 tr ptr.
- Arm: list of bones `[bone, 0, 0, 0]` (16 B) + interleaved IB offsets
  (0x24E0=4720, 0x2550=4776, 0x2620=4880, 0x2690=4936 — IB indices).
- The runtime draws each part as `[previous_offset, bone_offset)`. The arm
  offsets are IB indices (byte offsets ÷ 2).
- Dat (material): floats + stamp 0x8000020C at +0x30 + ptr to the next one
  (recursive chain): +0x34 next arm, +0x38 next dat.

**For Janemba to show up**: rebuild the complete mesh group (mesh-ref
blocks + arms + dat chain) with Janemba's geometry, grouping its triangles by
material and assigning Krillin's bones (JNB→KLL mapping).
Requires: (1) transforming Janemba's positions into the local space of Krillin's
bones (re-rigging by labels JNB_HEAD→KLL_HEAD, etc.), (2) building the IB
grouped by material, (3) re-mapping the arms with the new IB offsets.

**Status**: blocked on fine re-rigging + arms reconstruction. It is a
complete conversion job requiring more RE sessions.

### 13.5.12 COMMUNITY FINDING (2026-08-14) — THE LOGICAL HANDOFF

**IW → B3 PS2 models ALREADY EXIST** (made by the community):
- `modding resources\All Character Models from IW into AMB format\`
  → **241 .amb models** (#AMB PS2 LE: #AMO0 + #AMT). Janemba, Pikkon, Pan,
    Super 17, Super Baby, Gogeta, Vegito, all the Freezas/Buus, etc.
- `Janemba.amb` = identical to IW bin 541 (48 bones, 17 AMGs, 4415 unique).
- IW→B3 moveset ports already exist (AGENTS.md).

**Community tools** (`mod center\`):
- `AMO Decompiler.py` / `AMO Compiler.py` (Model Compiling Tools): PS2 #AMO0
  pipeline. Basis of the parsing we use.
- `B3_IW Model Converter` (amb_model.py): packs/unpacks #AMB.
- `Model Rig Toolset V0.6`, `Model Merger Tool`, `Bone Addition Tool`,
  `OBJ to AMG / Bin to OBJ`, `EMD to AMG` (Xenoverse ecosystem).

**Key handoff data**:
- PS2 Krillin: 3216 triangles, 4252 unique positions.
- HD Krillin: 1713 triangles, 2182 slots (~50 % reduction).
- **HD 360 halves the PS2 geometry.** The converter must replicate
  this (reduce Janemba 4415 → ~2200 positions, 3141 → ~1700 triangles).

**The technical blocker** (why Janemba's model comes out deformed):
- Krillin's mesh-ref blocks + arms define how the runtime draws each
  part (IB offsets, bones, materials).
- Injecting Janemba geometry with a different IB, the arms point at
  wrong ranges → deformed mass.
- **build_janemba3.py** tries to rebuild the arms, but has a relative-offset
  bug: the arm_ptr (rel magic) does not match the position in the rebuilt
  AWG0 (the mesh group is relocated).

**Correct next technical step**: fix the arm_ptr offset bug in
build_janemba3 (the rebuilt AWG0's mesh group is not at the same relative
position as in Krillin; arm_abs must be recomputed relative to the new bin's
mesh group, not the original's).

### 13.5.13 ARM_PTR BUG SOLVED (2026-08-14) — ARMS ZONE DECODED

**The bug was not about relative offsets but two conceptual errors**:

1. **The arm offsets are in IB BYTES, not indices.** Krillin:
   `0x24E0` = 9440 bytes = 4720 indices (×2). v3 wrote indices.
2. **The arms zone is a contiguous list of 20-byte blocks**, each
   `[bone_idx, offset_A_bytes, 0, offset_B_bytes, 0]`. Each mesh-ref
   block points (arm_ptr rel magic) to the START of ITS block. v3 swept
   96 bytes from each arm_ptr, stomping on neighbouring blocks of other MRs
   (which is why MR[1] overwrote MR[0]'s offset with 9423).

**Krillin's arms zone (14 blocks of 20 bytes, @0x1BCC-0x1CD0)**:
```
0x1BCC: [0x17, 0,0,0,0]        <- MR[0] mesh
0x1BE0: [0x18, 0,0,0,0]        <- MR[1] rig
0x1BF4: [0x19, 0x24E0,0,0x1E80,0]  <- MR[2] shadow  [3904,4720) idx
0x1C08: [0x1A, 0,0,0,0]        <- MR[3] rig
...      (mesh blocks without offsets)
0x1C80: [0x20, 0x2550,0,0x1EC0,0]  <- MR[9] shadow  [3936,4776)
0x1CBC: [0x23, 0x2620,0,0x1F00,0]  <- MR[12] shadow [3968,4880)
0x1CD0: [0x24, 0x2690,0,0x1F40,0]  <- extra (no MR) [4000,4936)
```
Only blocks with stamp 0x204 (shadow) define IB limits (in bytes).
The runtime draws each part as `[previous_offset, bone_offset)`.

**Fix applied in build_janemba3.py (v3.1)**:
- Write ONLY to the shadow blocks (stamp 0x204), at +4 (end_byte) and +0xC
  (start_byte), with values = index × 2.
- The extra block (bone 0x24 @0x1CD0) is updated to the end of the IB.
- Janemba regions: [0,3468), [3468,6396), [6396,9423) (3 shadows) +
  extra at the end. sec34=2128, vb2=226, IB=9423 indices.

**Generated**: `%TEMP%\opencode\janemba_v3.bin` (1090304-byte AMB) →
`janemba_v3.lzx` (149860, /N:2048) → `data_cmn_janemba_v3.afs` (full-file
mode, entry 327 = Janemba, the other 3989 intact).
Installed in `mods\krillin_afs\us\data_cmn.afs`.
**Test**: select mod krillin_afs and load Krillin. If Janemba's shape shows
(not a deformed mass), the arms mapping is correct.

### 13.5.14 SESSION 3 (2026-08-14): PIPELINE VALIDATED + v6 WORKS (2026-08-14)

**FINAL SESSION RESULT**: **Janemba enters battle without a crash** (v6).
The model looks like a deformed mass (re-rigging pending). This is the first
IW character that boots and enters battle in the recomp.

**Key lessons of the session**:

1. **The bin the guest reads is AFS e326** (682528 = `b327_hd.bin`),
   NOT e327 (624000 = `test327.bin`). The "327-329" numbering in AGENTS.md
   was off by one (table A index vs real index). `b327_hd.bin` = e326.
   (Later: this off-by-one came from reading the AFS table at 0x10 instead of
   offset 8; with the correct table, Krillin's visible entry is 327. See
   `AGENTS.md` §5–§6.)

2. **AFS method VALIDATED** (`build_afs.py`): e326 loc INTACT, the bin grows in
   its place, e327+ shifted by `delta rounded to 0x100`, empty entries
   (loc=0) preserved. Reproduces `data_cmn_janemba.afs` byte for byte.
   WRONG method (re-align to 0x80) → boot hang.

3. **CORRECT vertex pipeline**: `convert_personaje.py` (PS2 skinning →
   HD local positions) → `decimar.py` (voxel cell=0.10 → 2386 verts)
   → `build_janemba2.py` (pack AMB). **Do NOT use absolute positions**
   (huge values like -8.7 → boot hang).

4. **Runtime constraints** (critical):
   - v4 (sec34=2386, IB=8484, AWG0 grows to 142320): reaches select but
     **CRASHES in battle** (crash 0x7ff6180e6cc5).
   - v5 (sec34=1313, IB=5100, AWG0 shrinks to 88352): **does NOT boot**
     (the guest deserializes by the AWG header offsets; if it shrinks,
     the AMG1+ offsets point at overlapping data).
   - **v6 (sec34=1956, IB=5140, AWG0 keeps 116720): WORKS.** Padding
     sec34/IB to Krillin's EXACT counts with empty slots is the key.
   - AWG0 can NOT shrink (hangs) nor grow too much (battle crash).

5. **Re-mapping the arms CRASHES**: changing the shadow offsets to new
   ranges [0,1275,2550,3825,5100] → crash while processing the model
   (0x7ff6180cf202). **FINDING: the arm offsets are NOT IB ranges
   to draw.** In ORIGINAL Krillin all 5140 indices are in
   [0,3904); the shadows' [3904,4936) ranges are EMPTY. The IB is drawn
   whole; the arm offsets define other information (bone skinning, not which
   triangles to draw).

6. **v6's deformed mass is RE-RIGGING**: Janemba's vertices have per-bone
   local positions (y=0.358, y=-8.706, y=-8.374...) skinned with
   JANEMBA'S BONES (JNB). The guest interprets them with KRILLIN'S BONES (KLL)
   from the mesh group's arm → misinterpreted positions → deformed mass.
   **Fix: map JNB→KLL bones by labels (JNB_HEAD→KLL_HEAD,
   JNB_WAIST→KLL_WAIST, JNB_LLEGROT→KLL_LLEGROT...) and transform Janemba's
   local positions into Krillin's local space.**

**Generated files** (in `%TEMP%\opencode\`):
- v4 = `janemba_v4.bin` (1099760, = `janemba_amb10.bin`) — reaches select,
  battle crash
- v5 = `janemba_v5.bin` (1045792, sec34=1313) — does not boot
- v6 = `janemba_v6.bin` (1074160, sec34=1956/IB=5140) — **WORKS**,
  `janemba_v6.lzx` (123520), `data_cmn_janemba_v6.afs`
- v6r = arms re-mapped — boot crash (discarded)

**New tool**: `awo_tools/decimar_tri.py` (triangle decimation to fit within
Krillin's limits) and `build_afs.py` rewritten with the validated AFS
rebuild method.

### 13.5.15 JNB→KLL RE-RIGGING: ANALYSIS (2026-08-14, session 3 — final)

**Current blocker**: Janemba v6 enters battle but looks like a deformed mass.
Cause: Janemba's vertices have local positions skinned with JNB bones, but the
guest interprets them with the KLL bones of Krillin's mesh group arm.

**Analysis completed**:
1. **Bone labels**: Krillin HD has 51 bones (KLL_*, labels at AWO +0x24,
   102 strings = 2 duplicated blocks of 51). IW Janemba has 64
   labels (JNB_*, 48 bones + tail T_TAIL1-6 + multiple fingers).
2. **Mapping by labels**: 46/64 map 1:1 (JNB_HEAD→KLL_HEAD,
   JNB_LARM1→KLL_LARM1, XJNB_BODY→XKLL_BODY, etc). Those that do NOT map:
   fingers L01-L41 (Krillin only has L00), faces L01-L18 (Krillin only
   L00), and the tail T_TAIL1-6 (Krillin has none).
3. **Poses by index do NOT match**: KLL bone 2=(0,0,0) vs
   JNB=(-0.71,-0.71,0). The bone order differs between skeletons — mapping is
   only possible by labels.
4. **The 80-byte axis does NOT contain the pose matrix**: floats 0x00-0x2F
   are identity (0,0,0,1.0 ×2 + 1.0×5). The axis has: +0x30 stamp
   (0x6000020F root / 0x9000020C bone), +0x34 armature ptr (16 B block),
   +0x38 child, +0x3C sibling, +0x40 parent. The hierarchy is walked through
   these pointers.
5. **PS2 AMG header**: +0x10 bone_am, +0x14 axes_loc (0x20), +0x18
   mesh_groups (17), +0x1C labels_off. Labels are in a table with
   offsets (not sequential).

**Re-rigging requires**:
1. Parsing the JNB (48) and KLL (51) bone hierarchies via child/sibling/parent.
2. Extracting each bone's bind pose matrices (NOT in the 80 B axis —
   look in the armature or mesh part headers).
3. Mapping JNB→KLL by labels (46 direct; resolve fingers L01+→L00,
   faces→L00_FACE, tail→WAIST or ignore).
4. For each skinned vertex (bone_jnb, weight, pos_local):
   world = M_jnb_bind · pos_local; pos_local_kll = M_kll_bind⁻¹ · world.
5. Rebuilding the bin with the transformed positions.

**Unexplored alternative**: copy Janemba's axes into the v6 bin (so the
guest skins with Janemba's poses). Requires the guest to use the bin's axes
(not the arm's). Worth trying BEFORE full re-rigging since it is a
cheap change.

**DISCARDED (verified)**: copying the axes does NOT work. The 80 B axes of
both skeletons are the IDENTITY matrix (bind pose). The guest does NOT use the
axes for the pose — the vertices' local positions are used
directly (multiplied by identity = unchanged). The deformed mass comes from
Janemba's local positions (y=-8.7, in the JNB bone's space) being interpreted
in the space of the equivalent KLL bone of the arm.
**Correct re-rigging**: transform each Janemba vertex from the JNB bone's
space into the equivalent KLL bone's space, using the relation between both
skeletons' bind poses. For equivalent bones in the same base pose (standing
figure), the transform is a translation:
`v_kll_local = v_jnb_local + (kll_origin - jnb_origin)`, where origin is the
bone's position in model space.

> (Later: the HD and PS2 matrices turned out to be identical 47/47 and the
> pose lives in the `world` matrices of the axes; see `SESION_2026-08-17.md`
> §4 and `AGENTS.md` §3.4.2.)

### 13.5.16 ✅ THE HD VERTEX CARRIES THE BONE INDEX AT +28 (KEY DISCOVERY)

**Inspired by the B3→B1 port** (docs/INVESTIGACION_FORMATO_B1_HD.md §9 of the
sibling project): the HD vertex format is `[pos.xyz, w, bone, normal,
FFFF, uv]` stride 44. **In B3 the layout is**:
```
+00: nan (flag)   +04: u   +08: v
+12: pos.z_local  +16: pos.x_local  +20: pos.y_local
+24: weight (float)
+28: BONE INDEX (u32)      <-- the guest skins with this bone's matrix
+32: normal.z  +36: normal.y  +40: normal.x
```

**v6 ROOT BUG**: `build_vertex_hd` wrote `f32(0.0)` at +28 (bone index),
so ALL of Janemba's vertices pointed at bone 0 (BODY) → deformed
mass. Fixed: write `bone_idx` as u32 at +28.

> (Later: the "window" layout — `bone@16` — supersedes this reading; see the
> note at the top.)

**Label mapping**:
- Krillin HD: AWO +0x24 → table of 102 blocks of 16 B; bone N's label
  is in block `N*2` (even indices 0..100). bone 0=XKLL_BODY,
  1=KLL_WAIST, 2=KLL_STMC... 12=CHEST, 15=LARM1, 28=HEAD, 38=LLEGROT...
- PS2 Janemba: AMG +0x1C (labels_off) → 16 B blocks per bone (`bone_idx*16`).
  AMG0 has 24 even labels (0=XJNB_BODY, 2=JNB_WAIST, 4=JNB_LLEGROT...).
  Fingers/faces are in separate AMGs (AMG1-10 fingers, AMG11-16 faces).

**JNB→KLL mapping** (rig_mapeo.py): bone_jnb→label→label_kll→bone_kll. 24
direct + manual (odd fingers→L00_LHAND/RHAND, faces→L00_FACE).

**Results**:
- v7 (24 direct mappings, unmapped→bone 0): **WORKS, Janemba's body
  recognizable** but with corrupt triangles and flicker (fingers/faces at bone 0).
- v8 (full mapping incl. fingers→18/25, faces→36): **CRASH** — JNB finger
  local positions interpreted with Krillin's L00_LHAND give extreme values
  that break the render.
- **Current status**: v7 installed (recognizable body, corrupt). Next
  step: refine the mapping (try faces→36 without fingers→18, or keep fingers on
  fallback).

**Tools**: `rig_mapeo.py` (mapping + bone index remap), pipeline:
`convert_personaje.py` → `rig_mapeo.py` → `decimar_tri.py` → `build_janemba2.py`.

### 13.5.17 ✅ VALIDATION EXPERIMENT: KRILLIN B3 PS2 → B3 HD (CONVERTER)

**Goal**: validate the #AMO0→#AWO converter with Krillin (same skeleton,
no re-rigging) to learn the process of bringing models from the original B3
(PS2) — applicable to Shin Budokai, Budokai 2, etc.

**Result**: **the converter WORKS** — B3 PS2 Krillin renders in HD
with a **recognizable silhouette** (not a deformed mass). The validated pipeline:
```
convert_personaje.py (PS2 skinning→HD local positions + bone index)
  → build_ib_from_ps2.py (voxel dedup + IB from PS2 triangles)
  → build_janemba2.py (pack into the b327_hd template)
  → build_afs.py (rebuilt AFS, e326)
```

**Lessons**:
1. The HD vertex layout (fixed in build_vertex_hd): `[nan, u, v,
   pos.z, pos.x, pos.y, weight, BONE_INDEX(u32), normal.z, normal.y, normal.x]`.
2. PS2 and HD Krillin share the skeleton (51 bones, identical KLL labels) —
   the PS2 bone indices are directly valid in HD. **No re-rigging.**
3. v2 (1443 verts, bin 134044 LZX): **HANGS** the initial load (bin much larger
   than the slot + more vertices).
4. v3 (1109 verts, bin 125764): **BOOTS and Krillin is recognizable by
   silhouette** but corrupt (loose triangles).
5. The corruption comes from the converter only filling sec34 (body); the
   original HD uses **vb2 (226 verts) for the head/face** and the IB references
   BOTH buffers (max HD index=2189 > sec34=1956). The HD IB is not a
   sequential triangle list — it is optimized (nearby vertices).

**Next step**: replicate the complete HD structure — fill vb2 with the
head/face and build an IB that references both buffers in HD order.
This improves detail (the head would stop being corrupted).

**New tool**: `build_ib_from_ps2.py` (verts + IB from PS2 triangles).

### 13.5.18 REVIEW 2026-08-14 (afternoon): KRILLIN'S HD MODEL DIFFERS FROM THE PS2 ONE

**The user reported that the converter is NOT working** (deformed mass). After
a deep investigation, a **finding that changes the approach** was made:

**Krillin's original HD (e326 = b327_hd.bin)**:
- sec34 (1956 verts): **ONLY bones 0-35** (body, arms, head) skinned.
- vb2 (226 verts): bone=0xFFFFFFFF (no skin), ABSOLUTE positions — the
  head/face/faces.
- **Bones 36-50 are not used by any skinned vertex.** The HD model's
  legs/face are NOT skinned with leg bones.

**Krillin's PS2 (b327_ps2.bin)**:
- The skin uses bones 1-48, including skinned legs (38-48).
- The geometry is 9700 expanded verts, 4331 unique (not decimated).

**The #AMO0→#AWO converter is NOT a simple format conversion** — HD is a
rework: skinned body (0-35) + unskinned head/faces in vb2.
The guest validates the bone indices; putting bones 36-50 (PS2 legs) in sec34
**hangs** the load (the guest has no such matrices set up for the
bin).

**Lessons from the Krillin experiment**:
1. The IB fixes (index mismatch, triangles were lost) and UV (u,v order)
   are correct and necessary.
2. But Krillin's PS2→HD bone index is NOT direct: HD uses a simplified
   rig (0-35) + unskinned vb2.
3. **Janemba v7 worked** (recognizable body) because IW uses a full
   rig that matches the bin's 51 bones better.

**For a working converter** the HD structure must be replicated:
- Map PS2 legs/head → bones 0-35 or into vb2 (no skin).
- Build the IB referencing sec34 + vb2.
This is a geometry rework, not a mechanical conversion.

### 13.5.19 🔴 FUNDAMENTAL TRUTH: THE PS2 PARSER DOES NOT READ THE TRIANGLE IB

**Final review (2026-08-14)**: the conversion pipeline **was NEVER
correct**. `extract_geometry.py::_parse_part` reads each part's vertices
as **unique** (`n_verts = len(mesh_data[32:]) // stride`), but it does **NOT
read the part's triangle index buffer (IB)**.

**Consequences**:
1. `build_ib_from_ps2.py` generates triangles as `global_off + t*3`
   assuming expanded verts (3 per triangle), but the verts are unique →
   the resulting IB is wrong.
2. The `janemba_ib.bin` that made "Janemba v7" work is an artifact
   (`[0,256,512,...]` jumps of 256, max 65294) — **it is not a real triangle
   list**. Janemba v7 "worked" by accident (the guest drew a
   pseudo-random pattern that looked like a body).
3. The PS2 mesh part format (header 0xA0 + mesh_data) has the IB in a
   layout not yet mapped (the area after the verts contains non-IB data).

**The REAL next step**: RE the PS2 mesh part format to
locate the triangle IB (indices referencing the part's unique verts),
and rebuild the converter with correct triangles. Without this, the
converter produces corrupt geometry.

### 13.5.20 ✅ SOLVED: THE PS2 IB FORMAT (MaxScript budokai_updated.ms)

**The finding in `modding resources update 2`** (full report in
`modding resources update 2\INFORME_modding_resources_update_2.md`) revealed
the PS2 triangle IB format:

**The PS2 mesh part does NOT have an explicit index buffer.** Each mesh part is
made of **chained submeshes**, each with a 0x20-byte header:
```
mesh_data:
  +0x00..0x0F: header (12 B) + ukw
  +0x10: FaceType (long)   <- 1 = triangle strip, 0 = triplets
  +0x14: VertCount (long)
  +0x18: Null (8 B)
  +0x20: [VertCount vertices of 48 B]
  [next submesh in the chain]
```
- **FaceType == 1**: triangle strip (alternating zig-zag winding): f1=0, f2=1,
  and for x=2..: f3=x, alternating direction, append [f1,f2,f3] or [f1,f3,f2].
- **FaceType == 0**: consecutive triangles (every 3 vertices a triangle).

**PS2 vertex format** (first byte of meshType, stride):
- 0xB5/0xB6/0xF5 = 48 B (standard character): pos(3)+null+normal(3)+null+uv(2)+null+skip4
- 0xBD/0xFD/0x3D = 48 B (with normals+UV)
- 0x199 = 32 B (pos+normal, no UV)
- 0xB4/0xA4/0x99/0x92/0x19 = 32 B (facial: pos+uv, no normal)
- 0x90 = 16 B (shadows)

**New tool**: `awo_tools/parse_ps2_mesh.py` — PS2 mesh part parser
based on the MaxScript. Results for PS2 Krillin (b327_ps2):
- AMG0: 3990 verts, 2392 tris (19 parts)
- All 18 AMGs: 9144 verts, 5182 tris
- This IS the real geometry with correct triangles.

**Tool**: `awo_tools/build_hd_pipeline.py` — full pipeline:
parse → skin (SkinData) → HD verts (bone index layout) → decimate → IB.
The resulting v7 (1018 verts, 1700 tris) **hangs the boot** — the
unskinned vertices (30 %) use absolute positions with bone 0, which hangs
the guest. **Pending**: map/discard the unskinned vertices.

**NOTE on the real geometry**: AMG0's vertex count varies with the
`end` used: `md+mesh_size` (flag +0x90) gives 3990 verts AMG0 / 9144 total
(authoritative source, the MaxScript); `next part` gives 354 / 5005. The
flag's `mesh_size` is the real extent of the part.

**Main pending item**: the skin→mesh mapping. convert_personaje's SkinData
gives voffs that do NOT exactly match the mesh vertex offsets
(only 20/52 in part 0). The skin voffs point into the rig's v/vn list
with a mapping that needs more RE (relation between the v/vn list and the
submesh vertices). Until solved, unskinned vertices use absolute
positions → hang.

**Key new documentation**: `modding resources update 2\` contains the
community tutorials and tools (B3/IW bin list, AMG format,
re-rigging with Tutorial12, SLXS for adding characters, 512 KB LZX
compression, AZT/DDS textures). See the full report.

> (Outcome: the Janemba IW→B3 port was abandoned as a documented failure; the
> deliverable is the native HD↔HD swap. See `AGENTS.md` §3.1 and §3.4.10.)

## 13. MAINTENANCE: .bmp/.dmp FILES

The runtime writes GPU debug captures (`.bmp`, ~30 MB each) and crash dumps
(`.dmp`) into the build directory. 906 MB were cleaned up. The `.bmp` files
are debug captures (probably a cvar) and can be deleted.

## 7. WORKING FILES

| File | Purpose |
|---------|-----------|
| `awo_tools/parse_model.py` | #AMB → #AMO0/#AMG or #AWO/#AWG parser |
| `awo_tools/analyze_awg.py` | Analysis of an #AWG |
| `awo_tools/analyze_mesh.py` | Mesh parts inside an AWG |
| `awo_tools/trace_bone.py` | Hierarchical bone tracing |
| `awo_tools/extract_geometry.py` | Extract PS2 geometry (B5 vertices) |
| `awo_tools/build_awo.py` | Converter v1 (simplified structure, crashed) |
| `awo_tools/build_awo_v2.py` | Converter v2 (geometry replacement, broke +0x34) |
| `awo_tools/build_awo_v3.py` | Converter v3 (indices outside the VB) |
| `awo_tools/build_awo_v4.py` | **Converter v4 (correct structure: AWO+AZT, fixed size)** |
| `awo_tools/RE_PROGRESO.md` | Complete RE document |

Data in `%TEMP%\opencode\` (no longer exists): b327_ps2.bin, b327_hd.bin,
b327_hd.lzx, b328_hd.bin, b329_hd.bin, b146_ps2.bin, b146_hd.bin, b352_hd.bin,
and the generated .lzx/.bin files.
