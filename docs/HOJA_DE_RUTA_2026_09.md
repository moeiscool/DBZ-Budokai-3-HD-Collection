# ROADMAP 2026-09 — Project maturity (post-1.1.1)

> Updated: 2026-09-26. Base state: **v1.2.9 published** (Latest; diagnostics
> that explain themselves —sustained fps, slow disk and mixed install warnings,
> `vram=`/`lim=`, VRAM guard, `entorno` line—). `AGENTS.md` re-compacted to
> ≤60 KB (from 117 KB) on 2026-09-26, with `01_estructura/HISTORICO_RELEASES.md`.
> On top of v1.2.8.2 (textures without tanking fps) and v1.2.8.1 (HUD/RGBA8
> dump), v1.2.7 (PCSX2-style texture packs), v1.2.6 (polished HD texture
> enhancement —no hitches, native RGBA8 coverage, clean HUD—, anti-abuse UX for
> the internal scale and **TOML self-repair**), on top of **v1.2.5** (I/O
> diagnostics `dbz3_io_logging` + readahead, `fg=`, mute/dim on focus loss),
> **v1.2.4/1.2.4 EX** (FXAA/dither, GPU knobs, portable user data, real volume),
> **v1.2.3** and **v1.2.2 EX** (the launcher finds the executable by itself: the
> retail disc dump and the original ISO boot without renaming anything; TOML fix
> with Windows paths). The game is very functional and validated in battle/menus
> (US+EU, keyboard, presets, override mods).
> Previous documents: `HOJA_DE_RUTA.md` (modding, 2026-08-14) and
> `HOJA_DE_RUTA_COMUNIDAD.md` (community feedback, 2026-08-25, P0-P5 almost all
> DONE). This roadmap **updates and consolidates** them into 3 phases.
>
> **Later addition (2026-10-06)**: an experimental **PS5 build** for jailbroken
> consoles (`ps5/`, `docs/PS5.md`), outside the phases below.

**Guiding principle (inherited from HOJA_DE_RUTA.md)**: *do not guess the
format — read it from the guest*. The recompiled code in `generated/` (and
`generated_eu/`) is the REAL parser; each field is validated by a guest
instruction. Instrument the runtime (log the guest PC) to see what it reads and
validate our bins against that.

---

## PHASE 1 — LIGHT DOCUMENTATION (token spend) — ✅ DONE (2026-09-20)

**Goal**: reduce the context cost of sessions without losing relevant data.
Today `AGENTS.md` = **236 KB / ~3392 lines** (~60k tokens per session). `docs/`
total = 173 KB.

### 1.1 `AGENTS.md` 236 KB → ~60 KB operational + history archive
- **Keep in AGENTS.md (compressed)**: everything OPERATIONAL — consolidated
  state (§0-§3.4), hard constraints (B3 vertex layout, to_read/mid-insert,
  canonical DLLs and the stale-cmake bug §13.6, build commands §6), summarised
  launcher/runtime fixes (§4, §12-§14), mod pipeline (§10), port state (§15 →
  reference to docs), useful commands.
- **Archive the verbatim history**: §8 items 8-65 (the long numbered log),
  §65.1.x (detailed injection sessions), §11.1 (Janemba) → to
  `docs/01_estructura/HISTORICO_AGENTS.md` (new), referenced from AGENTS. Zero
  data deleted: it is moved.
- **Rule**: every engineering constraint (offset, size, root cause, build
  command) is kept; only the historical narrative goes to the archive.
- **Method**: manual rewrite + grep verification that the key tokens (offsets,
  sizes, hashes, commands) survive.

### 1.2 Other .md files
- `HOJA_DE_RUTA_COMUNIDAD.md` (16 KB): **rewrite clean** (it has double-encoded
  mojibake, §14.19) and mark what is complete as historical.
- `HOJA_DE_RUTA.md` (11 KB): mark as historical/superseded by this roadmap.
- `AWO_FORMAT.md` (19 KB): keep (it is the format reference); compress only if
  possible without losing the field-by-field layout.
- Update `docs/README.md` (index) with the new map.

**Success criterion**: AGENTS ≤ 60 KB; all constraints verifiable by grep; no
future session needs the history to operate.

---

## PHASE 2 — DEAD-CODE CLEANUP AND DEBUGGING — ✅ 2.1 done; 2.2 as it appears

### 2.1 Dead code (verified in `src/`) — ✅ DONE (2026-09-20)
**Verified**: `dbz3_enabled_mods` (cvar + `JoinList`/`SetModEnabledList`),
`PrepareRegionData` and the `active_region` comments **no longer exist** in
`src/`; `awo_tools/analyze_bin_hd.py` keeps only its OUTDATED warning pointing
to `awg_to_obj_b3.py`/`awg0_export.py`; there is no `out/win-amd64-legacy/` nor
`win-amd64-release-eu`/bootstrap presets. `DBZ3_EU_VARIANT` (CMakeLists L86)
**is used** (historical EU-only variant in `main.cpp`/`hooks.h`/`settings.h`,
and now also by the EU PS5 build), so it is not dead code. The following points
remain as a record:
- **`dbz3_enabled_mods` (cvar + paths)**: dead code since §4.2 (the real
  activation is the `.disabled` marker). Remove: cvar (settings.cpp:62),
  `SetFlagByName("dbz3_enabled_mods", ...)` (launcher_state.cpp:490), the
  `JoinList`/`SetModEnabledList` block of `IsModEnabled`
  (settings.cpp:609-625). Keep `IsModEnabled` (used).
- **`PrepareRegionData`** (settings.cpp:633): no-op stub since §14 (the game
  reads directly without an overlay). Check callers and delete or reduce it to
  its real role (`project_root`). Clean up `active_region` comments.
- **`awo_tools/analyze_bin_hd.py`**: OUTDATED (§13.2, PS3 layout) — delete or
  leave only as a warning; point to `awg_to_obj_b3.py`/`awg0_export.py`.
- **Artefacts of removed variants**: DLLs of `out/win-amd64-legacy/` (legacy
  variant gone since §14.21; the classic one uses avx2 from `out/win-amd64/`).
  Check nothing references them before deleting.
- **Port tool history**: `awo_tools/historial_fallidos/` (Janemba scripts)
  already archived — keep as an archive, do not link.
- **CMakeLists**: review obsolete targets/cache (e.g. bootstrap leftovers,
  `DBZ3_EU_VARIANT`, win-amd64-release-eu already deleted).
- Warning sweep: build dual+release with `-Wall` and close the unintended ones.

### 2.2 Pending debugging (known technical debt)
- **Intermittent `std::terminate` of `LaunchModule`** (§14.14): mitigated with
  try/catch + log, but the exact `throw` has NOT been located. Resolve with the
  stack capture already instrumented if a user hits it.
- **EU core in real battle**: only boot validated (§14.13/§14.16); deep paths
  (battle/events) could reveal unregistered functions → use
  `DBZ3_COLLECT_UNREGISTERED` if a crash appears.
- **`verify_release.ps1` as a gate**: run it on EVERY release (it exists).
- **Mojibake** in `HOJA_DE_RUTA_COMUNIDAD.md` (→ Phase 1.2).
- **Texture packs for 8/16-bit formats** (`k_8`, `k_8_8`, `k_5_6_5`,
  `k_1_5_5_5`, `k_4_4_4_4`...): today they **are dumped** (v1.2.8.1) but their
  pack is ignored because the host resource is not RGBA8 and its swizzle is
  format-specific. Enabling them = RGBA8 resource for the pack + identity
  swizzle in `GetHostFormatSwizzle` (hot path: measure). See
  `docs/SESION_VOLCADO_FORMATOS_2026-09-23.md` §8.
- **Formats not dumped**: `k_DXN` (BC5), `k_DXT5A` (BC4), `k_DXT3A`, `k_24_8`,
  `k_16_16_16_16` (they warn once in the log).

---

## PHASE 3 — RE: NEW CONTENT THROUGH DUPLICATES (abilities, characters, stages)

**User hypothesis (valid)**: duplicating an existing entry and modifying it is
the way — it is already PROVEN that the runtime accepts self-contained bins in
any slot (native swap §3.4.1) and that the guest auto-detects each bin's format
(§13.1). What is missing is **mapping the content tables** (roster, stages,
moves) to duplicate the correct ENTRY.

### 3.1 Content audit (the base of everything) — 🔴 IN PROGRESS (2026-09-02)
1. **✅ Full map of `data_cmn.afs`** (3990 entries): done and documented in
   `docs/03_formatos/AUDITORIA_DATA_CMN.md` + raw map in
   `mod center hd/data_cmn_map.txt`. Classification by internal magics
   (#AWO/#AWG/#AZT/#ACM/#AMB) with `awo_tools/afs_scan.py`.
2. **✅ Locate the STAGES: VALIDATED** (2026-09-02) — two zones confirmed with
   `awo_tools/stage_analyze.py` (#AWO/vertex count): bins 44-69 (multi-piece
   environments, 13 stages + collision bins 53-69) and 3735/3786/3788/3821/
   3823/3845/3847 (giant #AWO of 16K-102K vertices, 7 stages) = **~20 total**
   (matches the game; no character exceeds ~3K verts). Detail in
   `docs/03_formatos/AUDITORIA_DATA_CMN.md` + `mod center hd/stages_b3.txt`.
   ⚠️ **Stage vertex layout ≠ character** (FLT_MAX reads): editing stages
   (F3.4) needs RE of the layout. Pending: match each bin with the real stage
   name (select in data_eng.afs).
3. **Locate the MOVESETS/abilities — SOLVED at bin level (2026-09-07)**: each
   character's moveset/animation is the large `#ACM#AMB` bin of its group (ANM
   column in `MAPA_ROSTER_HD.md`, e.g. Krillin 332/333, Goku 290-292, Vegeta
   433-435/437). Identified by AFL name (CAM/LIPS/ANM) + size (1.2-2.4 MB), not
   just by the `#ACM` signature. Pending: internal structure of the move table
   in `generated/` (F3.2).
4. **🔴 Map the HD SLXS/roster: ✅ SOLVED (2026-09-07)** — there is no SLXS
   file in the HD; the roster lives in the **decrypted guest image**, not in
   `data_eng.afs`. `out/analysis/guest_image/dbz3_us_image.bin` was dumped with
   a mini tool (`out/analysis/guest_image/`, CMake+source; loads the xex in
   tool_mode with the installed SDK and dumps membase 0x82000000-0x826D0000)
   and the following were located:
   - **Select portrait/slot table** `0x82372818`: 78 u32 = 39 slots × 2
     entries; slot 10 = Krillin (3930), slot 19 = Nappa (3934) —
     **CONFIRMED with the substitution experiment** (§3.3.2). Full order in
     `MAPA_ROSTER_HD.md` §7.
   - **Per-character bin table** `0x823268C0`: runs of AFS indices with
     0xFFFFFFFF separator (models→CAM→LIPS/ANM).
   - **Consumer function** `sub_8217F3F0` (recomp `.15.cpp:13877`,
     `lis -32201; addi r9,r9,10264` → index slot*8+flag*4 over 0x82372818).
   The previous AFS read trace (`dbz1_afs_reads.log`) and the substitution
   experiment turned the temporal associations into a confirmed mapping; the 17
   exported 288x352 `#AZT1` are documented in `AUDITORIA_DATA_CMN.md` §3.2.1.

### 3.2 Additional ability (by duplicate)
1. RE of the ability format in `generated/` (move table).
2. Duplicate an existing ability (e.g. a Ki Blast) + modify parameters
   (damage/animation/name/texture).
3. Install as a mod (per-entry override) + validate in battle.

### 3.3 Additional character slot (by duplicate) — the closest one
1. **Character dependency inventory — CLOSED (2026-09-07)**: `#AMB` model,
   auxiliaries (CAM/LIPS/SCOUT), moveset/animation (large `#ACM` bin) and aura
   (0-43) mapped per character in `docs/03_formatos/MAPA_ROSTER_HD.md` (HD
   catalogue + probe + Pal AFL, +6 offset validated). The portraits are `#AZT1`
   candidates 3884-3960 with medium-confidence temporal association
   (`AUDITORIA_DATA_CMN.md` §3.2.1).
2. **✅ Lowest-risk experiment — DONE (2026-09-07)**: substitution on an
   existing slot. The `portrait_swap_test` mod (serving entry 3934 in slot 3930
   via per-entry override) made **Nappa's portrait appear on Krillin** in the
   select → confirms the pairs 3930=Krillin and 3934=Nappa and validates the
   portrait override. In addition, the guest image was dumped and the **select
   portrait table** (`0x82372818`, 39 slots) and the bin table (`0x823268C0`)
   were located — the roster lives in guest data, with consumer
   `sub_8217F3F0` (§7 of MAPA_ROSTER_HD). 🟢 The next step is to study how the
   guest enumerates the 39 slots (loop/count) and try ONE native slot.
3. Confirm where the slot index lives in the recompiled guest: find the
   consumer of the select entry table and validate whether the bin is an
   immediate, a static table or a descriptor loaded from `data_eng`.
   **→ Advanced 2026-09-07**: consumer located (`sub_8217F3F0`), the table is
   static in the guest image (`0x82372818`), not a `data_eng` descriptor.
   Pending: the 39-slot loop/count and deciding host hook vs re-codegen (§9 of
   MAPA_ROSTER_HD).
4. Only then implement the real duplication: extend/replace the slot
   descriptor, associate the `data_cmn` model, associate the portrait of the
   `#AZT1`/composite and keep the target's voice/animation auxiliaries.
5. Validate by layers: model in battle, selection/portrait, transformations,
   voice and save. Each layer must have an isolated override to locate the
   missing dependency.

### 3.4 Additional stage (by duplicate)
1. Locate stage bins (3.1.2) + where it is listed in the select.
2. Duplicate an existing stage (bins + select entry) + modify
   geometry/texture.
3. Validate: stage selectable and loadable.

### 3.5 Common tool: "duplicate entry"
A generic script/pipeline that duplicates an entry (AFS + SLXS/select) and
points to a new bin — reusable for characters, stages and abilities.

### 3.6 🔴 GPT-6 ASTRA PLAN — native slots + port (assessment 2026-09-07)

> **Full document**: `docs/DICTAMEN_GPT6_ASTRA.md` (verbatim + appendix with
> new findings). The external assessment corrects 3 assumptions and proposes
> the execution plan 0-7 that replaces "step 4/5" of 3.3 for native slots.

**Corrections that apply now (verified against our state):**
1. **`0xFFFF` = empty cell, NOT a free character**: distinguish interface
   cell / portrait ID / character ID / form ID. Do not assume free slots.
2. **`bone@+28` is only valid for sec34 (Krillin)**: format C uses `+40`.
   Choose the layout per AWG, never a global offset.
3. **The mid-insert enlarges an existing AFS entry; it does NOT add new AFS
   indices**: increasing the count of `data_cmn.afs` requires validating the
   count, the virtual table and the consumers separately.

**Execution plan (0-7 + bounded parallel track):**

| Order | Work | Acceptance criterion |
|---|---|---|
| 0 | Freeze baseline, DLL and effective override | Repeatable results and recorded hashes |
| 1 | Restore known injection and run Afix in isolation | Stable visible model; diagnosis without contamination |
| 2 | Trace count, cells and the 184 B record | Distinguish capacity, identity and enumeration |
| 3 | Add an alias cell of an existing HD character | Original and duplicate selectable, without substitution |
| 4 | Create independent identity and resource resolution | Both fight at the same time without improperly sharing state |
| 5 | Scan rigs and produce a first compatible IW | Acceptable silhouette and animation on an HD rig |
| 6 | Integrate that model into the independent slot | Select→battle→victory→rematch stable |
| 7 | Complete voice, texts, forms and persistence | Save tested with a disposable profile; roster regression |
| Parallel | Path B discriminator (exact port) | First dependency proven before the general regenerator |

**Assessment decisions we adopt as criteria:**
- **Native slots**: order of paths = (1) reuse a real reserved cell →
  (2) data patch in guest memory → (3) hybrid tables + minimal hooks. **NO
  re-codegen nor touching `generated/` as the first step.** Module
  `src/mods/native_roster` outside `generated/`, manifest per region+hash,
  opt-in, abort on mismatch.
- **First character = duplicate behaviour, not files**: an alias cell that
  resolves to the ORIGINAL (candidate: Android 16), initially without
  duplicating CAM/ANM/voice/aura; own model/portrait only once independent
  resolution is proven.
- **Port**: Path A (injection) = DELIVERY path; Path B = bounded research with
  closed deliverables (round-trip, minimal failing permutation, first runtime
  divergence). Investment in Path A: per-bone/zone/material correspondences,
  seam preservation, per-region thresholds, rejecting doubtful
  correspondences while keeping the HD vertex.
- **Save**: disposable profile + NON-persistent experimental slot; do not
  write new IDs into normal saves.

**Recommended execution order** (by feasibility): 3.3 (characters, swap
already validated) → 3.4 (stages, requires locating bins) → 3.2 (abilities,
the deepest RE). The user's order (abilities → characters → stages) is valid as
a priority of interest; technical execution follows feasibility.
**⚠️ The assessment's plan (§3.6) is the current guide for native slots and
port**: milestones 0-3 first, rig scanner, then IW.

---

## SUGGESTED EXECUTION ORDER

1. **Phase 1** (light docs) — immediate benefit in tokens per session.
2. **Phase 2.1** (dead code) — low risk, quick cleanup + minor release.
3. **Phase 2.2** (debugging) — only what comes up; not blocking.
4. **Phase 3.1** (audit) — the content map enables all the RE.
5. **Phase 3.3 → 3.4 → 3.2** (new content by duplicates), following the
   **assessment's plan (§3.6)** for native slots and port.

## ACCEPTANCE CRITERIA
- F1: AGENTS ≤ 60 KB without losing constraints; coherent indexes.
- F2: dual+release build without new warnings; no traceable dead cvars/code.
- F3: at least ONE new playable character (select + battle), ONE new loadable
  stage and ONE new working ability, all installable as a mod.

## REFERENCES
| Topic | Where |
|---|---|
| Consolidated port state | `AGENTS.md` §3.4 |
| Native swap / override mods | `AGENTS.md` §6, §10; `docs/02_mods/` |
| Roster/SLXS (historical) | `docs/HOJA_DE_RUTA.md` (phases 2-3) |
| Community feedback (P0-P5) | `docs/HOJA_DE_RUTA_COMUNIDAD.md` |
| Bin format | `docs/03_formatos/` + `AWO_FORMAT.md` |
| Plan 1.1.1 (debugging/Linux) | `docs/PLAN_1.1.1.md`, `docs/PLAN_LINUX.md` |
| PS5 build | `docs/PS5.md`, `ps5/README.md`, `AGENTS.md` §14 |
| Guest code (real parser) | `generated/`, `generated_eu/` |
| **GPT-6 Astra assessment (slots + port plan)** | `docs/DICTAMEN_GPT6_ASTRA.md` |
| Briefing that produced the assessment | `docs/BRIEFING_GPT6_ASTRA.md` |
