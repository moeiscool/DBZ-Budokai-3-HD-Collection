# ACCELERATED ROADMAP 2026-09 — Radical time compression

> Updated: 2026-09-08. This roadmap **replaces, as the active execution plan**,
> `HOJA_DE_RUTA_2026_09.md` (post-1.1.1 maturity, Phases 1-3) and
> `RE_MASTER_2026_09.md` (end-to-end RE master plan). It consolidates the
> **architecture assessment (Astra)** whose goal is to reduce Luna's estimates
> (2-5 days → 3-6 months) to **weeks** by inverting the order of work:
> *modding first, understanding as a by-product*.
>
> `RE_MASTER_2026_09.md` remains valid as the lab protocol (baseline, hashes,
> failure classification). `DICTAMEN_GPT6_ASTRA.md` remains the current guide
> for native slots and port. This roadmap adds the accelerated execution layer
> and its automation.

---

## 1. GUIDING PRINCIPLE (why the times compress)

Luna estimated with the classic RE model: *understand the format → then modify
it*. That assumption is inverted in this project because 70% of the
infrastructure already exists. The new guiding principle:

> **Make RE a by-product of modding, not its prerequisite.**

Operational consequences:
1. **Swap first, format later**: to redistribute a resource (model, portrait,
   CAM, LIPS, aura, voice, moveset) there is NO need to understand its format:
   it is moved as a blob with mid-insert. The format is only RE-documented when
   that resource is to be *edited*.
2. **Reader-first RE**: each format is documented by finding the guest function
   that reads it (recompiled code in `generated/`) and tracing the guest PC per
   AFS read. No blind binary dissection.
3. **Corpus-driven parsing**: the "solid" parser is achieved by parsing ALL the
   bins at once and validating against the game's render, not one by one.
4. **Reuse of PS2 knowledge**: the 360 HD is the big-endian twin of the PS2.
   The community already decoded AMO/AMT/AMB/aura/SLES. The BE/LE diff is the
   parser.
5. **Expose what already exists**: the disc contains ~183 characters (Bulma,
   Babidi, Kibito, Giru, Saibaman…). Do not create characters from nothing:
   make playable those that already have resources in `data_cmn.afs` via a
   guest memory patch (Path 2 of the assessment).
6. **LLM over recompiled code**: `generated/` is C++ an LLM can analyse. With
   the traces, mapping tables takes hours, not weeks.

---

## 2. REAL STATE OF THE GROUND (inventory of what is done)

| System | State | Evidence |
|---|---|---|
| Per-entry AFS override + virtual mid-insert | ✅ WORKS | `AfsFindModOverride`, `AfsGetVirtualTable` in `rexglue-sdk-0.10/src/filesystem/afs.cpp` |
| LZX compression `/N:2048` + to_read padding | ✅ WORKS | `swap_b3.py`, `texture_b3.py` |
| Native HD→HD swap | ✅ VALIDATED | `sw_goten_nativo`, `sw_vegeta424`, `swap_96_on_327` |
| PS2→HD injection (Path A) | ✅ VALIDATED | `cell_npm4` (binary threshold 0.8) |
| Character catalogue | ✅ 183 | `mod center hd/catalog_b3.cat` |
| AFS read → entry tracing | ✅ | `HostPathFile::ReadSync` + `HostPathEntry::OpenMapped` → `dbz1_afs_reads.log` (gate `dbz1_diag_logging`) |
| Roster/select tracing (guest) | ✅ | `src/roster_trace.cpp`: `sub_8217F478/F3F0/F520/A920/A8B8/A618/ADE8/80AA0` → `dbz1_roster_trace.log` |
| Select portrait table | ✅ LOCATED | `0x82372818` (39 slots × 2 u32), consumer `sub_8217F3F0` |
| Per-character bin table | ✅ LOCATED | `0x823268C0` (runs of AFS indices, separator 0xFFFFFFFF) |
| `data_cmn.afs` audit | ✅ 3990 entries | `docs/03_formatos/AUDITORIA_DATA_CMN.md` + `mod center hd/data_cmn_map.txt` |
| Stages | ✅ ~20 located | bins 44-69 + 3735/3784…; vertex layout ≠ character (RE pending) |
| Movesets | ◑ at bin level | large `#ACM#AMB` bins per character (Krillin 332/333, Goku 290-292) |
| Guest image dump | ✅ | `out/analysis/guest_image/dbz3_us_image.bin` (0x82000000-0x826D0000) |
| PS2/AWO parser | ✅ partial | `awo_tools/` (65 scripts): `awg_to_obj_b3`, `awg0_export`, `awg_cara_export`, `afs_scan`, `stage_analyze` |
| PS2→HD port pipeline | ✅ | `mod center hd/ports/port_ps2_b3_{extract,geometry,draw,pack,verify,inject}.py` |

**Conclusion**: the "Lab/AFS" that Luna estimated at 2-5 days is already built.
What is missing is automation (F0) + the content layers.

---

## 3. THE 7 ARCHITECTURAL ACCELERATORS (A1-A7)

| Id | Accelerator | What it unlocks | Cost |
|---|---|---|---|
| A1 | Swap first, format later | 80% of the intent (models/portraits/CAM/LIPS/aura/voice/movesets) is covered by moving blobs | 1-2 days (swap_matrix.py) |
| A2 | Reader-first RE | Any format is documented by its reader function in `generated/` | hours/format |
| A3 | Corpus-driven parsing | Solid parser validated against ALL bins + Content DB for free | 1-2 days (corpus_scan.py) |
| A4 | Reuse of PS2 knowledge | HD parser by BE/LE diff, no RE from scratch | days |
| A5 | LLM over recompiled code | Guest/table map in hours | — |
| A6 | Memory patch on a new slot | Playable character (expose an NPC) in days, not weeks | 2-4 days |
| A7 | Platform = engineering, not RE | Experiment Runner + Content DB are layers over primitives | 2-4 weeks |

---

## 4. WORK LINES AND HOW TO RUN THEM

### L4.1 — AFS lab (CLOSED, only the F0 automation)

**Goal**: everything touched verifies itself: hashes, region, active mods,
classified logs. **Tool**: `tools/lab_f0.ps1`.

Usage:
```
tools/lab_f0.ps1 -OutDir out\analysis\f0          # manifest + inventory + log summary
tools/lab_f0.ps1 -ClassifyLogs only               # classify logs without touching anything else
tools/lab_f0.ps1 -DryRun                          # review before writing
```
What it produces:
- `manifest.json`: SHA256 of `dbz3.exe`, canonical DLLs, `default.xex`,
  `data_cmn.afs` us/eu; US/EU region detection by the xex MD5.
- `mods_inventory.txt`: list of mods and their state (active / `.disabled`),
  and which AFS entries they override (critical to avoid "test
  contamination").
- `logs_classified.txt`: automatic classification of each session's last log
  (`dbz3_*.log`): `AFS OVERRIDE HIT`, `AFS MOD READ`, `got < to_read` (broken
  padding), crash (code), stale `rexruntime` (no `AfsGetVirtualTable`).
- `exit_report.txt`: readable summary (all OK / anomalies).

Acceptance criterion: a work session starts with `lab_f0.ps1` and the result
in 2 minutes.

### L4.2 — Solid HD parser + Content Database (CORPUS)

**Goal**: JSON/SQLite of ALL AFS entries (format, size, magics, dependencies,
AWO structure). **Tool**: `awo_tools/corpus_scan.py`.

Procedure:
```
python awo_tools/corpus_scan.py us\data_cmn.afs -o out\analysis\corpus -r 0-3990
python awo_tools/corpus_scan.py eu\data_cmn.afs -o out\analysis\corpus -r 0-3990
python awo_tools/corpus_scan.py us\data_eng.afs -o out\analysis\corpus
```
What it produces (per AFS):
- `corpus_<afs>.json` — per entry: index, physical size, decompressed size,
  magics (#AMB/#AWO/#AWG/#AZT/#ACM/#AWM/#AMO0), number of
  AWG/descriptors/bones, root labels, format cluster, suspicious (NaN/ERR).
- `formats_summary.json` — clusters: how many entries per format, size range,
  character bins vs stages vs portraits.
- `corpus_all.db` (SQLite) — queryable by SQL to cross dependencies.
- `anomalias.txt` — entries that do not parse (ERR) → candidates for new
  formats or tooling errors.

Rule: **the reference corpus is NOT overwritten without a diff**. The corpus is
the seed of the Content DB (platform phase).

Acceptance criterion: >95% of entries classified; 100% of the character bins
identified in the corpus match `MAPA_ROSTER_HD.md`.

### L4.3 — Generic swap matrix (A1)

**Goal**: move ANY resource blob between slots and regions without knowing its
format. **Tool**: `mod center hd/swap_matrix.py` (generalises `swap_b3.py`).

Procedure:
```
python swap_matrix.py --afs us\data_cmn.afs --from 3934 --to 3930 \
    --type portrait --mod nappa_portrait_on_krillin
python swap_matrix.py --afs us\data_cmn.afs --from 333 --to 404 \
    --type moveset --mod krillin_moveset_on_tenshinhan
python swap_matrix.py --region us --from 327 --to 327 --type model \
    --mod tien_ps2  (bins already generated by the port pipeline)
```
> ⚠️ The original roadmap's example (`333→400`) was wrong: **400 is
> Tenshinhan's MODEL** (#AWO+23×#AWG), not a moveset. Tenshinhan's moveset is
> **404** (#ACM×3, 1747360 B ≈ Krillin's). Verified with `--describe`.

✅ **Control mods created and verified 2026-09-08** (LZX validated by
decompression, in `out/build/win-amd64-release/mods/`):
- `nappa_portrait_on_krillin` (3934→3930, virtual mid-insert 122880 ✓)
- `krillin_moveset_on_tenshinhan` (333→404, anm.bin 917504 = to_read ✓)
- `krillin_dmg_test` (Krillin attack 15 → damage 200, geom.bin 900344, damage
  confirmed in the decompressed bin ✓)
> ⚠️ Test ONE at a time (rule 1). The old test mods are `.disabled`.
What it does:
- Extracts the source entry (LZX → bin → checks the magic for `--type`).
- Compresses `/N:2048`, computes `to_read` + `to_read_virtual` (mid-insert).
- Installs as an override `mods/<mod>/<us|eu>/<afs>/<entry>/geom.bin` +
  manifest.
- `--dry-run` reports without installing; `--force` replaces.

Acceptance criterion: the first `portrait` and `moveset` swaps in game have
`AFS OVERRIDE HIT` in the log (control = check the log with L4.1).

### L4.4 — Roster/native slots (A6 + assessment)

✅ **Definitive roster map solved 2026-09-08**: the 39 select slots identified
by name by crossing the guest table with the Pal AFL (US = PAL +45 in the IMG
region): `out/analysis/roster_slots.txt` + `MAPA_ROSTER_HD.md` §7. The roster
is 38 characters + Random (slot 38). This leaves the `0x82372818` table fully
decoded (slot → 2 US portraits).

Execution guide (milestones 0-3 of the assessment, already advanced by
`roster_trace.cpp`):

1. **Milestone 0 (done)**: frozen baseline + effective override + hashes.
2. **Milestone 1**: re-validate `cell_port_Afix_test` on its own (a single
   active mod). Control: a known HD→HD swap before any PS2→HD.
3. **Milestone 2**: ◑ **structure of the 184 B record decoded 2026-09-08**
   (static RE, `MAPA_ROSTER_HD.md` §9.1): u16 fields +12/+14/+18/+68/+114,
   index table `0x8238B670` (≥4 u32), slot object (+28/+48/+60/+62/+64/+68),
   portrait table `0x82372818` indexed by `(s16@+64)*2 + bit0@+62`, `0xFFFF` at
   +64 = empty slot. **The VALUES are runtime**: close the count/cells with
   `dbz1_roster_trace.log` (F478/F3F0/F520/A920/A8B8/A618/ADE8/80AA0).
4. **Milestone 3**: add an alias cell of an existing HD character (candidate
   Android 16), resolving to the ORIGINAL without duplicating
   CAM/ANM/voice/aura.
5. **Milestone 4+**: independent identity → exposed NPC character
   (Bulma/Babidi).
6. Parallel: Path B discriminator (exact port) — bounded research.

> 🔴 **Bin table `0x823268C0`: consumer NOT locatable (2026-09-08)** — the
> address is not referenced in ANY form in `generated/` (neither lis/addi, nor
> ori, nor a pointer in the image). Accessed via a runtime pointer or a struct
> base. Not blocking: the character→bins mapping is already solved
> empirically.

Do not touch `generated/` in this line: the changes go in
`src/mods/native_roster` (hooks + memory patch), manifest per region+hash,
opt-in.

### L4.5 — ACM/movesets (A1 + A2)

Order of progress:
1. **Swap ACM as a blob** (day 1): `swap_matrix.py --type moveset` to
   redistribute movesets between characters. Requires confirming which bin of
   the group is the moveset (ANM column of `MAPA_ROSTER_HD.md`).
2. **ACM format** — ✅ **STATIC RE DONE 2026-09-08** (without entering battle):
   `docs/03_formatos/ACM_FORMAT.md`. The moveset bin is `#AMB → #CSK + 3×#ACM`
   (PS2 BSK/AMM renamed, BE). The editing chain was decoded: attack code →
   animation block → HR list → HR data (damage/stun/pushback). **🔴 PS2↔HD
   identity confirmed**: PS2 BSK/AMM (LE, `ps2_games/B3 GH/USR/data_cmn.afs`,
   SAME indices) = HD #CSK/#ACM (BE) — same sizes and offsets. The LE/BE diff
   IS the parser (A4). HR fields = `[damage u16][code u16]` packed. Tools:
   `awo_tools/acm_parse.py` + `acm_analyze.py`.
3. **Ability editing**: ✅ **TOOL FIXED 2026-09-08** after the
   `krillin_dmg_test` crash. The first `csk_edit.py` patched the FRAMES of the
   AP blocks (misread as damage) → crash in battle (NULL in `sub_820800A8`).
   **Real format decoded** (BSK_breakdown.pdf + PS2 diff): attack code →
   animation block → **AP type 1** (Hit properties) → **HR code** (u16 @bytes
   6-7) → **HR block** (`hr_off + code*128`, 8 lines × 16 B with
   `damage u16`). `csk_chain.py` (analyses) + `csk_edit.py` (edits, verified
   attack 0x21b → HR 28/29/... damage 100). `krillin_dmg_test` mod reinstalled
   with the correct chain.
   🔴 **SECOND CRASH DIAGNOSED AND FIXED 2026-09-09**: the fixed mod still
   crashed on the SELECT (same NULL signature, 3/3). Cause: the virtual
   mid-insert runtime left inconsistent reads (old untranslated offsets) when a
   mod GREW an early entry (333), and the #AMB parser dispatched the garbage
   magic `#ACP` (no handler). Fix: **`AfsRebuildPath`** materialises a rebuilt
   physical AFS when there is growth (all reads consistent). (Later replaced by
   the in-memory `AfsVirtualRange`, AGENTS §6.) Pending: validate in game that
   `krillin_dmg_test` no longer crashes and that damage 100 applies.

Acceptance criterion: a redistributed moveset visible in battle + an edited
ability working.

### L4.6 — Stages

1. ✅ **Stage bin structure RE'd 2026-09-08** (without entering battle):
   `docs/03_formatos/STAGES_FORMAT.md`. Stage = `#AMB` container → `#ZDD` (geo
   1.48 MB) + `#CAD`/`#CAS` (camera tables) + `#SPX` (LE script "ver 0.01") +
   sparse nested `#AMB` (641 slots: `#ACE` collision + `#AWO`/`#AZT`/`#ACM` per
   element). Confirmed stages: even bins 44-68 (odd bins 45-69 = auxiliaries);
   3735-3847 = HD variants.
2. ✅ **Stage names confirmed** (Pal AFL, aligned 1:1): 44=RED_RIBBON BASE_MAP,
   46=WORLD_TOUR, 48=BUU_BODY, 50=CELL_RING, 52=GRANDPA_HOUSE, 54=KAI_WORLD,
   56=ISLAND, 58=TIME_BOLIC_CHAMBER, 60=NAMEK, 62=PLAINS, 64=DESERT, 66=CITY,
   68=DAMAGED_CITY (odd = SE_). Select videos = `*_SELEC.sfd` (~US 3936-3943).
3. RE of the stage vertex layout (FLT_MAX reads ≠ character).
4. RE of the #SPX bytecode (script VM; `+0x18`=count, LE) — PENDING.
5. Duplicate a stage + modify geometry/texture → validate loadable.
6. Reference: the community's PS2 stage mods (Muscle Tower) as a source of
   practice.

### L4.7 — Platform (A7, after L4.1-L4.3)

- Experiment Runner: `tools/run_experiment.ps1` — experiment manifest (region,
  active mods, steps, criterion) + execution + capture + automatic
  classification (reuses the L4.1 classification logic).
- Content DB: fed by the corpus (L4.2) + `MAPA_ROSTER_HD.md`.
- Mod Authoring: layer over `swap_matrix.py` + the `catalog_b3.cat` catalogue.

---

## 5. SPRINTS 0-4 (EXECUTION CALENDAR)

| Sprint | Content | Deliverable |
|---|---|---|
| S0 (today) | Automation: `lab_f0.ps1`, `corpus_scan.py`, `swap_matrix.py` + roadmap | 3 tools + this roadmap |
| S1 | F0 run (manifest) + full us/eu corpus + first portrait/moveset swap | `out/analysis/f0/`, `out/analysis/corpus/`, control mod |
| S2 | Roster/select map closed + expose the 1st NPC (memory patch) | playable NPC character |
| S3 | ACM: swap + format + 1st edited ability | redistributed moveset + new ability |
| S4 | Duplicated stage + Experiment Runner | new stage + runner |

### 5.1 S0 — DONE 2026-09-08 (initial results)

- **`tools/lab_f0.ps1`** working. Its first use revealed that
  `tien_ps2_on_krillin` was ACTIVE (no `.disabled`) → disabled for a clean
  baseline.
- **`awo_tools/corpus_scan.py`** working. `out/analysis/corpus/corpus_all.db`
  (6699 rows): data_cmn us/eu (3990) + data_eng (2709).
- **Format finding via corpus**: `#SPX ver 0.01` = STAGE format (present in
  bins 44-69; 1501 #SPX entries). The large stages (44-69 and 3735-3847) are
  confirmed in the `model` cluster (>1.5 MB, up to 6.2 MB).
- **Character groups mapped by corpus**: each group = models (`#AWO`+18
  `#AWG`, 600-900 KB) + moveset (`#ACM`×3, 1.5-2.4 MB) + auxiliaries
  (`#AMB`+`#SPX`+`#ACC`). E.g. Krillin: models 327-329, movesets 320/324/333.
- **`mod center hd/swap_matrix.py`** working (describe + swap dry-run
  validated: portrait 3934→3930 with virtual mid-insert).
- **Pending diagnosis (crash 0xC0000005 @0x7ff7b6ccd279)**: the last session's
  log shows the crash with Tien active but WITHOUT `AFS OVERRIDE HIT` → the
  override is not served by that path. Hypotheses to investigate: (a) the
  guest reads entry 327 via mmap (`OpenMapped`), which does NOT serve
  overrides, or (b) a region mismatch. The crash is reproducible (2 sessions,
  same addr) and can NOT be attributed to the model until a served override is
  confirmed.

### 5.2 S1 — concrete plan (next)

1. `tools\lab_f0.ps1` before touching anything (green = clean baseline).
2. Enable ONE native control mod (e.g. `sw_goten_nativo` → slot 327) and check
   `AFS OVERRIDE HIT` + `AFS MOD READ` in the log (criterion: got=to_read).
3. Create the portrait control mod with `swap_matrix.py` (3934→3930) and
   validate it on the select.
4. Create the moveset mod with `swap_matrix.py` (333→404 Krillin→Tenshinhan)
   and validate it in battle.
5. Only when an override has been served and verified: reactivate Tien
   (`swap_matrix.py --bin <bins/tien.bin> --to 327`).

## 6. OPERATING RULES (inherited, critical)

1. **ONLY ONE active mod per test** — `AfsFindModOverride` serves the first in
   alphabetical order; a forgotten mod invalidates the tests (contamination).
2. **Check the region in the logs**: the override lives under `us/` or `eu/`
   according to the game's real region (Tien lesson: EU was tested with a US
   override).
3. **Guest's FIXED `to_read`**: the compressed bin must fit unless virtual
   mid-insert is used (grows only if bin > to_read).
4. **LZX compression `/N:2048`** and **exact padding** (if `got < to_read` →
   crash).
5. **Canonical DLLs**: after `cmake --build` copy `rexruntime.dll` again (the
   build overwrites it with a stale version). Verify with a grep for
   `AfsGetVirtualTable`.
6. **Do not touch `generated/`** for slots: hooks + memory in
   `src/mods/native_roster`.
7. **AFS table at offset 8**, not 0x10.

## 7. GLOBAL ACCEPTANCE CRITERIA

- A green `lab_f0.ps1` before and after each change.
- Corpus: >95% classified, consistent with `MAPA_ROSTER_HD.md`.
- At least ONE playable NPC character (select + battle).
- A redistributed moveset + an edited ability working.
- A new loadable stage.
- Everything installable as a mod (per-entry override).

## 8. RISKS (honest)

- **Full port (Path B) is still blocked** — it is not the critical path
  (injection delivers); do not invest until the discriminator.
- **VB2 (face/legs)** is still a specific blocker; work around it with HD→HD
  swap.
- **In-game validation is the real bottleneck** → that is why F0 (automatic
  logs) is sprint 0, not the last.
- **The community's PS2 findings are a reference, not an authority**: every
  ported mod requires HD re-validation.

## 9. REFERENCES

| Topic | Where |
|---|---|
| Slots/port assessment (current guide) | `docs/DICTAMEN_GPT6_ASTRA.md` |
| RE master plan (lab protocol) | `docs/RE_MASTER_2026_09.md` |
| Content audit | `docs/03_formatos/AUDITORIA_DATA_CMN.md`, `mod center hd/data_cmn_map.txt` |
| HD roster | `docs/03_formatos/MAPA_ROSTER_HD.md` |
| Bin/AWO format | `docs/03_formatos/` + `AWO_FORMAT.md` |
| Roster tracing (guest) | `src/roster_trace.cpp` |
| AFS read tracing (runtime) | `rexglue-sdk-0.10/src/filesystem/devices/host_path_file.cpp`, `host_path_entry.cpp` |
| Override/mid-insert (runtime) | `rexglue-sdk-0.10/src/filesystem/afs.cpp` |
