# CONTENT AUDIT — data_cmn.afs (full map)

> Date: 2026-09-02. Result of Phase 3.1 of `docs/HOJA_DE_RUTA_2026_09.md`.
> Method: every AFS entry >100 KB was decompressed (XDK xbdecompress) and
> classified by its internal magics (#AWO/#AWG/#AZT/#ACM/#AMB). Raw map:
> `mod center hd/data_cmn_map.txt` (3990 lines: `entry | compressed | class`).

## SUMMARY

| Entry range | Content | Typical signature |
|---|---|---|
| 44-69 | **STAGES (candidates)** — multi-model environments | `#AMB2 #AWO5-16 #AWG7-24 #AZT2-8 #ACM1-7` (1.8-4.3 MB decomp.) |
| 70-505 | **Characters** — models + texture (1 #AWO each) | `#AMB1 #AWO1 #AWG15-26 #AZT1` (~0.7-1 MB) |
| 504-555 | **Effects** (Kamehameha, Final Shine, etc.) | `#AMB3 #AWO1-4 #AWG1-7 #AZT4-9 #ACM1-2` |
| 127, 358, 435, 444, 2208, 2209, 3881 | **Animations/movesets** (#ACM) | `#ACM` (1-3 blocks) |
| 481, 3877, 3884-3899 | **Loose textures** | `#AZT1` (~1 MB) |
| 3735-3847 | **STAGES (candidates)** — 1 giant #AWO | `#AWO1 #AWG1` (0.9-6.2 MB) |
| 3979-3982 | **Videos** (intro/ending) | MPEG (`00 00 01 BA`) |
| 3983-3989 | DRM audio (IECS/XMA) + "dummy" | `IECS...` / `xma` |

## 1. STAGES — location VALIDATED (2026-09-02)

Validation with `awo_tools/stage_analyze.py` (reuses the
`awg_to_obj_b3.py` parser): the #AWO blocks per bin and the
vertices/triangles of each were counted. **No character exceeds ~2-3K
vertices; stages have 7K-102K.** Conclusion: B3's stages live in TWO zones:

### Zone A (44-69) — multi-piece environments (13 stages)
Each bin = an `#AMB` container with **5-16 #AWO blocks** (platforms, props,
animated elements) + #AZT textures + #ACM animation:

| entry | #AWO | verts | tris | decomp. |
|---|---|---|---|---|
| 44 | 6 | 16.5K | 8.9K | 1.9 MB |
| 46 | 6 | 16.6K | 8.9K | 1.8 MB |
| 48 | 6 | 13.4K | 12.3K | 1.9 MB |
| 50 | 8 | 26.5K | 20.4K | 3.1 MB |
| 52 | 11 | 27.1K | 20.2K | 3.5 MB |
| 54 | 5 | 14.2K | 12.5K | 2.1 MB |
| 56 | 16 | 34.4K | 27.8K | 4.0 MB |
| 58 | 3 | 7.4K | 6.5K | 1.1 MB |
| 60 | 14 | 33.9K | 28.4K | 4.2 MB |
| 62 | 14 | 28.2K | 19.1K | 3.9 MB |
| 64 | 10 | 26.0K | 20.8K | 3.6 MB |
| 66 | 5 | 21.2K | 14.5K | 2.1 MB |
| 68 | 12 | 29.3K | 20.5K | 4.2 MB |

The small interleaved bins **53/57/59/61/63/65/69** (~260 KB, #AMB WITHOUT
#AWO) = each stage's **collision/physics** (pattern: 1 model bin + 1 collision
bin per stage).

### Zone B (3735-3847) — single giant mesh (7 stages)
Each bin = **raw #AWO of a single mesh** (no #AMB wrapper):

| entry | verts | tris | decomp. |
|---|---|---|---|
| 3735 | — (different parse layout) | — | 0.9 MB |
| 3786 | 102.2K | 138.2K | 6.0 MB |
| 3788 | 16.3K | 11.9K | 0.9 MB |
| 3821 | 102.2K | 138.7K | 6.0 MB |
| 3823 | 16.3K | 11.9K | 0.9 MB |
| 3845 | 51.8K | 37.9K | 2.7 MB |
| 3847 | 19.2K | 15.1K | 1.0 MB |

Total: **~20 stages** (matches the B3 roster).

### ⚠️ Technical note
The stage vertex layout **differs from the characters'** (several reads give
FLT_MAX/0 positions): stages mostly use vb2 (static) and a different axis
scheme. To EDIT stages (F3.4) the stage vertex layout needs RE (see
`docs/07_ports/`).

### Pending
- Match each bin with the stage name (the select screen lives in
  `data_eng/ger/spn/fra/ita/usi.afs`).
- Locate the **loose #AZT 3877/3884-3899** (shared stage textures?) and 481.

## 2. CHARACTERS (70-505)

- **Definitive character→bins map**: `docs/03_formatos/MAPA_ROSTER_HD.md`
  (2026-09-07) consolidates the HD catalogue + real probe + AFL names. Each
  character has: models (`#AMB1 #AWO1 #AWG* #AZT1`) + CAM + LIPS + ANM (large
  `#ACM`) + optional SCOUT + AURA (0-43).
- The numbering matches the **PS2 Greatest Hits data_cmn**. The name list
  `data_cmn.afl` (Pal) matches the HD up to 286 and with an offset of **+6**
  from ~287 (GH added 6 angelic Goku models 281-287). The offset drifts
  locally (Recoome/Raditz/Saibaman, Trunks): the HD catalogue
  (`catalog_b3.cat`) is the authority for models.
- **A character slot = 1 #AMB bin** with `#AWO1 #AWG15-26 #AZT1`. The native
  swap (AGENTS §3.4) already takes advantage of this: a full #AMB bin in
  another's slot.
- **Each character's moveset/animation IS already located** (ANM column of
  the map, e.g. Krillin = 332/333, Goku = 290-292, Vegeta = 433-435/437): they
  are the large `#ACM#AMB` bins interleaved after each model group, identified
  by AFL name (CAM/LIPS/ANM) and size (1.2-2.4 MB). ⚠️ The #ACM signature alone
  does not distinguish a moveset from a stage animation; the name + the
  position in the character group does.

## 3. SLXS / ROSTER — next RE step

- **PS2**: roster→costumes→bins is edited via SLXS (MDB 0x60 / CDB 0x174
  blocks) with `SLXS Editor v0.50` (mod center/) and tutorials in `modding
  resources update 2/SLXS Edit Tutorial - Lesson *` (1-1, 1-2 adding models to
  costumes, 2-1 character blocks, 2-2 transformations, 3-1 auras, 4-1 select
  screen).
- **HD 360 — 🔴 there is NO SLXS file**: the equivalent is NOT in data_cmn
  (3983-3989 = IECS DRM audio) nor as a loose file in the AFS. The HD roster
  lives in the **guest code** (generated/) + the `data_eng` composites.

### 3.1 Audit of `data_eng.afs` (2709 entries, select/menus) — 2026-09-02
- **Entry 0** = **character select** composite (`#AMB` 28 MB: 5 `#ACA`
  sections + 5 `#AZT` textures + 1 `#AWO` model with 3 `#AWG`). The 5 #ACA
  sections = menu pages (characters / stages / modes).
- **1976, 2043** = giant `#AZT` textures (29-34 MB: select portraits/
  backgrounds).
- **`#SKC`** (small entries, e.g. 4) = UI config/screen rects (not roster).
- `#AMB+#ACA` composites (1-3, 5-7...) = other screens (VS, results...).
- ~2600 small entries (2-16 KB) = UI/texts.
- **Conclusion for F3.3**: "adding a character slot" in HD = duplicating the
  guest entry (the one referencing the bin in data_cmn) + duplicating its
  portrait in the select composite (entry 0). The exact mapping (slot→bin)
  requires **instrumenting the guest at runtime** (logging which data_cmn bins
  it loads when opening the select with each character).

### 3.2 Guest read trace — partial capture 2026-09-07

`out/build/win-amd64-release/dbz1_afs_reads.log` was captured with the
`HostPathFile::ReadSync` trace while going through the characters and stages
available in the save. The log has 663 total reads, of which 417 are of
`data_cmn.afs`.

#### Models confirmed by the `#AWO1#AWG*#AZT1#AMB1` signature

| Entry | Identification | Note |
|---:|---|---|
| 91 | Dr. Gero | model, not playable per the catalogue |
| 141 | Kid Buu | model |
| 181 | Freeza form 1 | model |
| 258 | Ginyu | model |
| 264 | Goku normal | model |
| 270 | Goku normal alternate | model |
| 327 | Krillin | model; known reference entry |
| 345 | Nappa | model |
| 350 | Piccolo normal | model |
| 360 | Raditz | model |
| 366 | model with no name in the current catalogue | needs an internal label |
| 400 | Tenshinhan | model |
| 416 | Vegeta without armour | model |
| 445 | Yamcha short hair | model |

In addition, small entries appear interleaved immediately after several
models: `91→94`, `141→144`, `181→195`, `258→261`, `264/270→289`, `327→331`,
`345→348`, `350→355`, `360→359/363`, `366→365/369`, `400→403`, `416→431` and
`445→449`. The trace shows that they are resources read in the same load
sequence, but **does not yet allow stating** that each small bin is
exclusively that character's moveset or voice; some may be shared
tables/configuration.

#### Content unrelated to the roster

- `3881` is `#ACM1` and is read three times: a common animation/moveset
  resource, still without an unambiguous assignment to a character.
- `3971`, `3973`, `3976-3981` produce large repeated reads; they belong to the
  late video/cinematic block of the AFS, not to character models.
- `3983-3988` are the DRM/audio entries already identified.
- `data_spn.afs`, `adx_jpn.afs` and `adx_usa.afs` appear for localisation and
  audio; they must not be mixed with the model map.

#### 3.2.1 Re-reading the load order and portrait candidates

The capture does contain the useful information for F3.3, although no
`mapped entry=` lines appear. The information is in the per-page `ReadSync`
calls: the guest first loads groups of entries `3884-3951`, which the map
classifies as loose `#AZT1` of a uniform decompressed size (~1,048,800 bytes),
and then reads the character model from `70-505`. So those groups must not be
classified as video. The paged video reads are entries `3971-3981`,
classified as `ERR` by the content scanner.

The following table is a **candidate** map derived from the capture order, not
an explicit internal reference. Confidence rises when a `39xx` group precedes a
known model and repeats with the same variant:

| Candidate #AZT group | Model read after | Identification | Confidence |
|---:|---:|---|---|
| 3924-3925 | 264, then 270 | Goku normal and variant | medium |
| 3918 | 246 | Kid Gohan | medium |
| 3958 | 416 | Vegeta without armour | medium |
| 3930 | 327 | Krillin | medium |
| 3938 | 350 | Piccolo normal | medium |
| 3952 | 400 | Tenshinhan | medium |
| 3960 | 445 | Yamcha short hair | medium |
| 3940 | 360 | Raditz | medium |
| 3934 | 345 | Nappa | medium |
| 3922 | 258 | Ginyu | medium |
| 3942 | 366 | model without a label yet | medium |
| 3912 | 181 | Freeza form 1 | medium |
| 3892 | 91 | Dr. Gero | medium |
| 3898 | 128 | Fat Majin Buu | medium |
| 3900 | 133 | Super Buu | medium |
| 3902 | 141 | Kid Buu | medium |

The observed association is broader than the initial list of 14 models: the
capture also loads `246` (Kid Gohan), `128` (Fat Majin Buu) and `133` (Super
Buu). In cases with two variants, such as `264→270`, the same 1 MB texture
group may be shared by several appearances; a new portrait should not be
created for each bin until the visual content is checked.

The sequence does not yet show whether a `39xx` group is a unique portrait, a
normal/alternate pair, or a block shared by several select entries. To confirm
it, each `#AZT1` must be decompressed/exported and the image compared, not
inferred only from temporal proximity. `3881` is still an `#ACM1` and appears
between the two Goku variants; it may be a common table or animation, but must
not yet be assigned as Goku's moveset.

The capture contains no reads of the known stages (`44-69` or `3735-3847`), so
this session was a capture of the character flow, not a valid capture for
mapping stage→bin.

#### 3.2.2 Exporting `#AZT1` candidates (2026-09-07)

The candidate entries were tested directly, without going through
`texture_b3.py`: that tool is designed for character bins starting with
`#AMB`, while these entries are standalone `#AZT` blocks. The analysis utility
`awo_tools/extract_azt_afs.py` decompresses and exports each entry to PNG.

Result for the 17 candidate entries `3892, 3898, 3900, 3902, 3912, 3918, 3922,
3924, 3925, 3930, 3934, 3938, 3940, 3942, 3952, 3958, 3960`:

- Each entry contains exactly one texture.
- All textures are `288x352`.
- The 17 PNGs have distinct SHA-256 hashes; they are not binary copies of the
  same portrait.
- The analysis PNGs are in `out/analysis/azt_exports/` and are not part of any
  active mod.

This confirms that the `#AZT1` are independent graphic resources, but does not
allow assigning character names without visual inspection. So the
`#AZT1 → model` pairs in the previous table remain medium-confidence temporal
associations, not a confirmed slot mapping.

#### Limitation of the first trace

Entry 0 of `data_eng.afs` (select composite) does not appear as a normal read.
The guest may access it via `HostPathEntry::OpenMapped`, which does not go
through `HostPathFile::ReadSync`. The runtime was already updated to also log
the creation of the mapping (`mapped entry=...`), but this only identifies the
initial range being mapped; it does not guarantee an event for each page the
guest touches afterwards. So this capture solves part of the
**character→model bin** map, but not the select's slot→portrait layout nor all
the locked stages. The next fine trace would have to instrument the
faults/reads of the `MappedMemory` wrapper, if the chosen backend exposes them.

## 4. AUDIT TOOLS (awo_tools/)

- `afs_list.py <afs>` — full table (entry, addr, size, magic).
- `afs_probe.py <e1 e2 ...>` — extracts and decompresses entries; lists magics
  in the first 128 KB.
- `afs_scan.py <range>` — decompresses and classifies (magic count over the
  whole buffer) all bins >100 KB of a range; appends to
  `%TEMP%\opencode\afs_classified.txt`.
- `extract_azt_afs.py <afs> --tool <xbdecompress> --entries ... --out ...`
  — exports standalone `#AZT` entries to PNG to compare portraits/textures.

## 5. REFERENCES

| Topic | Where |
|---|---|
| **Definitive HD roster map** | `docs/03_formatos/MAPA_ROSTER_HD.md` |
| Raw map (3990 lines) | `mod center hd/data_cmn_map.txt` |
| Model Swap catalogue (183 characters) | `mod center hd/catalog_b3.cat` |
| Pal AFL names (parsed) | `out/analysis/data_cmn_pal_afl.txt` (source: `modding resources/Data_CMN file name list (Budokai 3 Pal)/data_cmn.afl`) |
| Annotated table (probe + AFL + catalogue) | `out/analysis/data_cmn_annotated.txt` |
| PS2 community list | `modding resources/DBZ_B3_Character_Bin_List.txt` |
| Bin format | `docs/03_formatos/AWO_FORMAT.md`, `BIN_LAYOUT.md` |
| Native swap / port | `AGENTS.md` §3.4, `docs/07_ports/` |
| Roadmap | `docs/HOJA_DE_RUTA_2026_09.md` (Phase 3) |
