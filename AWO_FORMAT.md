# FILE FORMAT — DBZ BUDOKAI 3 HD COLLECTION (Xbox 360)

> Reference document for the recomp's modding project (dbz3).
> Consolidates the knowledge acquired through reverse engineering and the study
> of the community's tools (mod center / modding resources).
> **Goal**: make it possible to add new characters/maps/movesets to the native
> port.
> Updated: 2026-08-13. (Later findings: `AGENTS.md` §3.2-§3.4 and
> `docs/03_formatos/`; they correct some points below, e.g. the real vertex
> layouts and the virtual mid-insert that replaced the AFS rebuild of §2.4.)

---

## 1. EXECUTIVE SUMMARY

The recompiled game (yae3_xenon.xex) reads its data from **AFS** files
containing individual bins (models, textures, movesets, audio). Each bin is
**compressed with Xbox 360 LZX** (magic `0F F5 12 EE`) and when decompressed
reveals a **#AMB** container in **big-endian** (PowerPC).

**Critical difference with PS2/PSP**: the PS2 games (Budokai 1/2/3, Infinite
World) use the same #AMB container but in **little-endian** (MIPS), with inner
sections `#AMO0` + `#AMG` ×N + `#AMT`. The Xbox 360 version uses renamed
magics in **big-endian**: `#AWO` (model), `#AWG` (mesh), `#AZT` (texture).

**Conclusion of the study (VERIFIED 2026-08-13)**: the 360 `#AWO` IS the same
PS2 `#AMO0`/`#AMG` model repackaged in big-endian, with the same bones and
mesh groups (NO re-rigging). Direct comparison Krillin GH PS2 (bin 327) vs HD
360 (bin 327, same numbering):
- **51 bones in both**, **18 mesh groups in both**
- **68 identical bone labels** (KLL_*, XKLL_*)
- The endianness, the magics and the layout (offset table vs sequential)
  change

Converting a PS2→360 model requires:
1. Reading the little-endian #AMO0/#AMG (structure documented below)
2. Rewriting each u32/u16 field as big-endian
3. Renaming magics: `#AMO0`→`#AWO`, `#AMG`→`#AWG`, `#AMT`→`#AZT`
4. Converting the inner layout (sequential blocks → offset table)
5. Recompressing with `xbcompress /N:2048`

---

## 2. FILE SYSTEM

### 2.1 AFS container

```
offset 0:  "AFS" magic (3 bytes) + 1 byte padding
offset 4:  entry count (uint32 LE)
offset 8:  entry table: (address uint32, size uint32) — 8 bytes per entry
```

- Entries aligned to 0x800 (2048 bytes); data in [address, address+size).
- In the 360 HD each bin's data is **LZX compressed** (magic `0F F5 12 EE`).
- On PS2 the bins are **uncompressed** and are direct little-endian #AMB.
- The header takes up to 0x8000 (32768); the first entry typically starts
  there.

**The game's AFS files** (active directory):
- `data_cmn.afs` (~280MB, 3990 bins) — models, movesets, maps
- `data_usa.afs` / `data_en.afs` — menus, texts, capsules
- `adx_usa.afs` / `adx_jpn.afs` — audio (ADX)
- `lang_*.afs` — languages

### 2.2 Name list (AFL)

```
offset 0:  "AFL\0" (4 bytes)
offset 4:  version (uint32, =1)
offset 8:  0xFFFFFFFF
offset 12: entry count (uint32)
offset 16: fixed 32-byte records (null-padded name), count × 32
```

- **Important**: the names are NOT consecutive strings but **fixed 32-byte
  records** (verified in the 4 AFLs analysed: `16 + 32×count = size`).
- The **AFL index = the AFS bin number** (direct name→bin mapping).
- The GH/Collector's AFL (DATA_ENG.afl) uses the 360 HD bin numbering for the
  region file (data_usa).
- **Two different numberings depending on the AFS**:
  - `data_cmn.afl` → battle model/moveset/map bins (e.g. Krillin 327-329)
  - `DATA_ENG.afl` (region data_usa) → SCM/select (SCMKLL=35), BT-B00
    (Krillin 420-432)
- Names like `SCMXXX.amb` (selection), `BT-B00_XXXnnn.amt` (battle models),
  `CN-M0X_XXXnnn.amt` (cutscenes), `EN-E00_XXXnnn.amt` (endings),
  `SK-SKL_XXX.amt` (skills).
- Character codes: 16G/17G/18G (androids), GKS (kid Goku), GOK (Goku),
  GHS/GHM/GHL (Gohan), VGT (Vegeta), TRX/TRS (Trunks), KLL (Krillin),
  GNY (Ginyu), PIC (Piccolo), CEL (Cell), FRZ (Frieza), BRL (Broly), etc.

### 2.3 Xbox 360 LZX compression

- Tools: `xbcompress.exe` / `xbdecompress.exe` (XDK 2.0.7645.0) in
  `mod center\Xbox 360 Compression - Decompression tool...\`.
- **The game uses `/N:2048`** (native blocks of 2048) → magic
  `0F F5 12 EE 01 03 00 00`.
- `/Z:32` produces `0F F5 12 ED` (transparent segments) — NOT what the game
  uses.
- Syntax: `xbcompress /N:2048 <src> <dst>` and `xbdecompress <src> <dst>`.
- Round-trip verified: decompress→compress reproduces the exact bin.

### 2.4 The recomp's mod system (runtime)

- A mod replaces an AFS entry or a whole file:
  - **Per entry**: `mods/<mod>/us/<afs_filename>/<entry_index>` (loose bins)
  - **Whole file**: `mods/<mod>/us/<file>` (e.g. a whole `data_cmn.afs`)
- The runtime (afs.cpp + host_path_file.cpp) intercepts the reads and serves
  the mod's bytes when an override exists.
- Enabled mods: `mods/<mod>/` folder without a `.disabled` marker.
- (Historical) The launcher built the `active_region/` overlay from region +
  mods.
- **Per-bin override limit** (historical, 2026-08-13): the guest reads each
  bin with the size it has in the original AFS table. If the mod bin is
  larger, it is truncated (crash). So, for larger bins the **whole AFS had to
  be rebuilt** with the updated table (see script `rebuild_afs2.py`).
  **Superseded** by the runtime's virtual mid-insert (AGENTS §6).
- The rebuild script re-lays the data, updates the header's addr+size,
  preserving the rest byte for byte.

---

## 3. #AMB CONTAINER

```
offset 0x00: magic "#AMB" (23 41 4D 42)
offset 0x04: header/version (0x20 = 32) — BE in HD
offset 0x0C: number of entries (uint32)
offset 0x10: number of models
offset 0x14: 32 (header size)
offset 0x18: 64
offset 0x24: offset of the first data block
offset 0x28: 1
...
Entry table: at offsets 0x20/0x30/0x40... (16 B per entry: loc + size)
```

- Model AMB: entry 1 = AMO/AWO, entry 2 = AMT/AZT (texture).
- Moveset AMB: AMC/AML/BCM/SPX at 32/48/64/80.
- Data aligned to 16 B.
- **PS2 = little-endian, 360 HD = big-endian** (u32 fields read reversed).
- Magic mapping: `#AMO0`→`#AWO`, `#AMG`→`#AWG`, `#AMT `→`#AZT `.

---

## 4. MODEL FORMAT — #AMO0 (PS2) / #AWO (360)

### 4.1 Model file header

```
offset 0x00: magic "#AMO0" (PS2) or "#AWO" (360)
offset 0x10: bone_am  — number of bones/axes
offset 0x14: bone_loc — offset of the bone relation table (32 B/entry)
offset 0x18: amg_am   — total number of AMG blocks/mesh groups
offset 0x1C: padding
offset 0x20: array_am — number of axes-array lines per bone (B3 = 3)
offset 0x24: label_loc — offset of the label list (at the end)
offset 0x28-0x2C: unknown
offset 0x30: amg_loc  — offset of the first AMG (main)
offset 0x34: amg_loc2 — offset of the 2nd AMG; the AMG offset list follows here (4 B each)
```

Then: AMG offset table (amg_am × 4 B, padded to 16), relation table,
axes-array.

### 4.2 Bone relation entry (32 B, at bone_loc)

```
+0:  bone index
+4:  ptr to its first axes-array entry (16 B)
+8:  ptr CHILD
+12: ptr SIBLING
+16: ptr PARENT
+20..31: padding
```

### 4.3 Axes-array entry (16 B; array_am per bone)

```
+0: 0
+4: bone index
+8: ptr to the "axis line" (80 B entry inside the AMG)
+12: 0
```

### 4.4 AMG header (mesh block, 32 B) — magic "#AMG "

```
offset 0x04: 0x20 (base)
offset 0x0C: 0x04 (version/seal)
offset 0x10: bone_am (number of axes)
offset 0x14: axes_loc (offset of the first axis entry, normally 32)
offset 0x18: axis lines per bone (B3 = 3, SB2 = 1)
offset 0x1C: label_loc (offset of the label list, at the end of the AMG)
offset 0x7C: ptr to the mesh-group table (end_loc − 64)
offset 0x80: number of model parts
```

### 4.5 Axis entry (80 B, at axes_loc)

```
+0..47:  transformation data (48 B):
         3×float position (0,0,0) + float rot w=1.0 + 3×float + w=1.0
         + 3×float scale (1.0) + w=1.0 + 0x0F020060
+48:     padding
+52:     ptr to the bone/mesh/rig block
+56:     ptr CHILD (offset to another axis)
+60:     ptr SIBLING
+64:     ptr PARENT
+68..79: padding
```

### 4.6 Bone data block (16 B minimum, at the axis ptr +52)

```
+0:  bone index
+4:  ptr mesh-group header  (or 0 if rig only)
+8:  ptr rig data (weights) (or 0 if mesh only)
+12: ptr "Mesh End" block (64 B) (or 0)
```

Bone types (by the +4/+8/+12 pointers):
- empty:  0,0,0
- norms:  +4=0, +8≠0, +12=0  (rig only)
- model:  +4≠0, +8=0, +12≠0  (mesh only)
- mixed:  all ≠0

### 4.7 Mesh-group header (at the bone ptr +4)

```
+0:  mp_amnt (number of model parts)
+4:  0x10
+8..15: padding (8 B)
+16..: model part offset table (mp_amnt × 4 B, relative to the mesh-group start)
then: the model parts
```

### 4.8 Rig header (at the bone ptr +8)

```
+0..11: padding (12 B)
+12:    wv_am (number of weight groups)
+16..:  weight group table (wv_am × 32 B)
then:   v/vn (rig1) and v (rig2) data
```

Weight group entry (32 B):
```
+0:  weight (float32)
+4:  vvn_am (number of v/vn entries = rig1)
+8:  vvn_loc (ptr to rig1 data)
+12: v_am (number of v-only entries = rig2)
+16: v_loc (ptr to rig2 data)
+20..31: padding
```

Rig entries:
- **rig1 (v/vn): 32 B** = V coords (3×float) + offset to the mesh vertex (u32)
  + VN normal (3×float + 4 pad)
- **rig2 (v only): 16 B** = V coords (3×float) + offset to the mesh vertex
  (u32)

### 4.9 Model part / mesh (vertex format — the most important)

**Model part header (160 B = 0xA0):**
```
+0:  type1: 0x01B5=437 (B5), 0x01B4=436 (B4), 0x0190=400 (90)
+4:  type2: 0x21B5=8629, 0x21B4=8628
+8:  texture index (0xFFFFFFFF = no texture)
+12: shader index (0xFFFFFFFF = no shader)
+16..143: material parameters (mostly 1.0f)
+144: size: 0x60000000 + (mesh_bytes / 16)
+160: mesh data (face blocks)
```

Formulas:
```
mesh_size  = (value_at_+144 − 0x60000000) * 16
long_total = mesh_size + 160
```

**Vertex formats by part type:**
- **B5 (48 B/vertex):** V x,y,z (12) + pad (4) + VN x,y,z (12) + pad (4) + VT
  u,v (8) + pad (8)
- **B4 (32 B):** V (12) + pad (4) + VT (8) + pad (8)
- **90 (16 B):** V (12) + pad (4)

**Face block / triangle (176 B = header 32 + 3 vertices × 48):**
```
+0..11:  08 00 00 14 | 00 00 00 00 | 00 00 00 00  (tag)
+12..15: 00 C0 0A 6C → magic 0xC06C (block detection)
+16:     01 00 00 00  (marker 01)
+20:     03 00 00 00  (block vertex count: 3)
+24..31: padding
+32, +80, +128: the 3 vertices (48 B each in B5)
```

Mesh-group footer: `triangle_end_bottom.bin` (16 B `08 00 00 14 ...`).
"Mesh End" block: 64 B (dummy floats + `00 00 80 3F`).
Labels: `bone_am × 32 B` at the end of each AMG (name in the first 16 B).

---

## 5. OBSERVED PS2 vs 360 DIFFERENCES (Krillin, verified bin by bin)

Direct comparison of the SAME bin (327 = Krillin) in GH PS2 and HD 360:

| Property | PS2 GH (bin 327) | HD 360 (bin 327) |
|-----------|------------------|-------------------|
| Compression | none | LZX `/N:2048` |
| Endianness | little-endian | big-endian |
| Model magic | `#AMO0` | `#AWO` |
| Mesh magic | `#AMG` (18, sequential) | `#AWG` (18, via offset table) |
| Texture magic | `#AMT ` | `#AZT ` |
| Decompressed size | 812KB | 682KB |
| **Bones** | **51** | **51** |
| **Mesh groups** | **18** | **18** |
| **Bone labels** | **68 (identical)** | **68 (identical)** |
| AMG layout | consecutive blocks with magic | table of 18 offsets at 0x690 |

**Conclusion (corrects previous analyses)**: there is NO re-rigging. It is the
same skeleton and the same meshes, just repackaged in big-endian with renamed
magics and a different mesh-group layout. This greatly simplifies the
converter: no need to adapt bones, only endianness + magic renaming +
rebuilding the AMG offset table.

**Detail of the HD inner layout (#AWO):**
```
#AWO  (header 0x30, big-endian):
  +0x10: bone_am (51)
  +0x14: bone_loc (0x30)
  +0x18: amg_am (18)
  +0x1C: offset of the AMG offset table (0x690)
  +0x20: array_am (24)
  +0x24: offset of the labels (0x6D8)
  +0x34: 0x42360 (end of the data area)

AMG offset table (at +0x1C): 18 × uint32 BE → absolute offset of each #AWG
Each #AWG (header 0x40, big-endian):
  +0x04: 0x40 (base)
  +0x0C: 0x04 (version)
  +0x10: bone_am (51)
  +0x14: axes_loc
  +0x18: number of axes
  +0x1C: label_loc
  +0x20: offset of the content
  ...bone labels at the end of the AWG (XKLL_BODY, etc.)
```

**To convert an IW (PS2) → HD (360) model:**
1. Read the little-endian #AMO0 + N×#AMG + #AMT
2. Convert each u32/u16 field to big-endian
3. Rename magics (#AMO0→#AWO, #AMG→#AWG, #AMT→#AZT)
4. Rebuild the layout: AMG offset table + adjust relative pointers
5. Recompress with `xbcompress /N:2048` and pack into the AFS
6. Validate by comparing the render of the converted base character vs the
   original

---

## 6. CHARACTER BINS (real mapping, from the data_cmn GH = HD)

**IMPORTANT**: there are TWO different numberings. The one that matters for
the recomp is that of **data_cmn.afs** (battle models, movesets, maps), which
the HD shares with the **PS2 Greatest Hits/Collector's** (verified by runtime
instrumentation: Krillin reads bins 327-329 of data_cmn).

### 6.1 data_cmn.afs (GH = HD) — battle models

The source of truth is `DBZ_B3_GH_Character_Bin_List.txt` (verified against
the GH AFL and the instrumentation). Bins vary per region:
- **Krillin = 327-329** (GH) — VERIFIED by instrumentation in the recomp
  (PAL is 321-323, +6)
- Cell = 146-151 (does not change between PAL and GH)
- Auras = 0-43 | Effects = 504-555 | HUD = 452-503

### 6.2 data_usa/data_en.afs (region) — select/menus

From the GH `DATA_ENG.afl` (2705 entries, index = bin):
- `SCMKLL.amb` = bin 35 (Krillin's select model)
- `BT-B00_KLL000-012` = bins 420-432 (region battle variants)
- `BT-B00_CEL000-027` = bins 157-184
- `CN-M0X` cutscenes, `EN-E00` endings, `SK-SKL_XXX.amt` skills

### 6.3 IW characters that do NOT exist in the HD (real IW bins)

Bins verified by reading `ps2_games\Infinite World (USA)\USR\DATA_CMN.AFS`
(1136 entries, uncompressed, LE #AMO0):

| Character | IW bins |
|-----------|---------|
| **Janemba** | 541-544 (541 amo + 542 amt + 543/544 recolour) |
| **Pikkon** | 583-586 |
| **Pan** | 566-569 |
| **Super 17** | 606-609 |
| **Super Baby Vegeta 2** | 678-681 |
| Syn Shenron | 97-98 (default) + 101-102 (recolour) |
| Omega Shenron | 99-100 + 103-104 |
| Bubbles | 118-119 (NPC) |
| Giru | 338-339 (cutscene) |
| Goku GT | 341-358 + 383-396 + 419-432 |
| Vegeta GT | 685-696 + 705-722 |
| Great Saiyaman 2 (Saiyawoman) | 482-489 |
| Shenron | 970-971 (NPC) |

To add them: convert their IW models (LE #AMO0) → BE #AWO (see section 5) and
the movesets from the ports (see section 7). (Since v1.4.0 the launcher's
character importer does this; see `README.md`.)

---

## 7. AVAILABLE RESOURCES (paths)

### Tools (mod center)
- `Model Compiling Tools\` — AMO Compiler.py / Decompiler.py (**source code of
  the structure**)
- `OBJ to AMG v0.92\source code.zip` — LE AMG writer (binary templates)
- `EMD to AMG v0.90\source code.zip` — EMD→AMG converter (from Xenoverse)
- `B3_IW Model Converter\amb_model.py` — AMB↔AMO/AMT repacking
- `Axis Line Tool\`, `Bone Addition Tool v1.02\` — axis/bone structures
- `BoneAxis Display\axis_data.py`, `Delete_AXIS.py` — AMO reading
- `Model Rig Toolset V0.6\`, `Model-Rig Extractor Tool V1.0\` — rig extraction
- `Model Merger Tool (32-Bit)\` — model merging
- `B3-to-SB2.py` — B3→SB2 AMG conversion (u16 vertices)
- `Xbox 360 Compression...\` — xbcompress/xbdecompress (LZX)
- `basic_functions.py` (in several tools) — **hex_to_int_be/int_to_hex_be
  helpers**
- `A3T Analyzer.py` — big-endian A3T textures (BE reference)

### Data resources (modding resources)
- `ps2_games\` — full AFS of B1, B2, B2V, **B3 GH**, **IW** (PS2 references)
  - B3 GH: `USR\data_cmn.afs` (3990 bins) = **same numbering as the HD** →
    compare bin by bin
  - IW: `USR\DATA_CMN.AFS` (1136 bins) = exclusive characters, uncompressed
- `Budokai Models\` — 279 .amo/.amt pairs (IW models) + B3GHC/B2V exclusives
- `All Character Models from IW into AMB format\` — 241 IW models in .amb
  (Janemba.amb 934KB: 48 bones/17 AMG; Pikkon.amb 805KB: 58 bones/16 AMG)
- `Infinite World to Budokai 3 Moveset Ports\` — 8 moveset ports:
  - **Janemba** → Krillin (B3: 330-333, 539 = LE #AMB: #AMC moveset,
    #AMO0+#AMG, #AMT+#AMO0+#AMG×3)
  - Goku GT → Teen Gohan | Great Saiyawoman → Kid Gohan | Pan → Nappa
  - Pikkon → Raditz | Super 17 → Android 17 | Super Baby Vegeta → Kid Trunks
  - Future Gohan (Shin Budokai) → ghf_365/367
- `map swap in b1\Stages\` — 13 extracted B1 stages (BBKAM, BBTEN, BBHAKB...)
  formats: .BD collision, .HD, .MAD, .MAS, .MDD geometry, .SPX, .SQ
- `Complete AFL ... DATA_ENG.afl` — GH region AFL (2705 entries, 32B/rec)
- `Data_CMN file name list (Budokai 3 Pal)\data_cmn.afl` — PAL data_cmn AFL
  (3945 entries)
- `ADX AFL v4 for Budokai 3\` — audio AFL (adx_jpn/usa), ADX bins per
  character
- `DBZ_B3_Character_Bin_List.txt` (PAL) / `DBZ_B3_GH_Character_Bin_List.txt`
  (GH)
- `All_Character_Slots Infinite World.txt` — IW slots (Janemba (1)(2), Pikkon
  (1)(2)...)
- `Voice list for Infinite World.txt` — IW voice bin ranges
- `Budokai_3_Capsules_IDs.txt`, `Budokai 1 and 2 Capsule Data\` — capsules
- `OCR scanned...\SkillList.dson` — 579 skills SK-SKL_### (DSON)
- `Budokai 3 GH's menus relevant stuff...\B3_GH_-_Data_USA_breakdown.txt` —
  menu map
- `Story Mode lists for Budokai 3 GH\` — GH story BPL/LST bins
- `Story_Mode_B3_Pal_Tool_V0.4.rar\` — PAL story mode editor (.NET, patches the
  exe)
- `Tail AMO\` — custom tail AMO (7 bones) + warning: **do NOT merge WAIST
  (crash)**
- `EmbPack-v2-LibXenoverse\` + `EmdFbx-and-FbxEmd-LibXenoverse\` — Xenoverse
  ecosystem (EMD/ESK/EAN/EMB ↔ FBX): a link to import/export models
- `Super Dragon Ball Heroes World Mission\` — **30402 EMD/ESK/EAN/EMB files**
  (Xenoverse): 392 characters, including Janemba (bcbjn), Pikkon
  (bcbjk/bcpkk), Super 17 (bcs17), Pan (bcpan), Super Baby (bcvby). "Chibi"
  style — evaluate whether it is worth it.
- `DDS_PNG\` — DDS↔PNG converter (textures)

### Textures
- PS2: `#AMT ` (206KB for Krillin); HD: `#AZT ` (391KB for Krillin).
- `A3T Analyzer.py` (mod center) handles big-endian A3T textures (reference).
- `DDS_PNG\DDS_PNG.exe` to convert extracted textures to PNG.

---

## 8. PENDING / NEXT STEPS

The plan was **simplified** after verifying that PS2 and HD share the same
skeleton (51 bones, 68 identical labels). There is no longer any need to adapt
rigs, only to convert endianness + magics + layout. Steps:

1. [x] Verify that PS2 GH and HD share the bin numbering (Krillin = 327)
2. [x] Confirm the same skeleton (51 bones / 18 AMG / 68 identical labels)
3. [ ] **Map field by field** #AMO0 vs #AWO (relative vs absolute pointers)
4. [ ] **Map the #AWG structure** (header 0x40, axes, mesh parts, B5/B4
   vertices)
5. [ ] **Map the #AZT texture format** (vs #AMT/A3T)
6. [ ] Write the #AMO0→#AWO converter (BE helpers + re-layout)
7. [ ] Validate: convert Krillin IW/GH → load in HD and compare the render
8. [ ] Apply to IW characters (Janemba 541-544, Pikkon 583-586, Pan, Super
   17...)
9. [ ] Add a new character: slot + model + moveset (existing ports) + voice
10. [ ] Explore empty data_cmn bins for new character slots
11. [ ] Integrate the converter into the launcher (mod center UI)
