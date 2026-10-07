# RE MASTER — DBZ Budokai 3 HD Collection

> Governing document for end-to-end reverse engineering.
> Created: 2026-09-08.

## 1. Goal

Build a reproducible model of the whole path `XEX -> guest -> AFS ->
content -> parser -> GPU -> menus/roster`. An offline result is not considered
validated in game; a crash is not attributed to the bin unless the log proves
the bin was served and consumed.

Questions that must be answered with evidence:

1. Which guest function requests each resource and when.
2. How an AFS index turns into a bin, model, mesh and draw.
3. Which data identify a character, form, stage, ability and slot.
4. Which changes work by override and which need guest data or hooks.
5. Why a change produces a valid render, deformation, a crash or no effect.

## 2. Consolidated state

### Confirmed

- US/EU boot and accept per-AFS-entry overrides.
- The effective AFS table is interpreted from offset 8.
- Models are self-contained `#AMB/#AWO/#AWG/#AZT` bins.
- The guest accepts native HD→HD swaps in existing slots.
- There are several vertex layouts; the bone's offset depends on the layout.
- The select roster does not live in an HD SLXS: there are tables in the guest image.
- `0xFFFF` means an empty cell in the observed selection path.
- Injection that keeps the template's pool is the only PS2→HD route with a
  positive visual result so far.
- Tien with cape is a real PS2 source; its 42 common bones match HD
  Tenshinhan and there are 10 additional cape bones.

### Not confirmed

- General regeneration of mesh-refs, zones, bboxes and descriptors with a new pool.
- Complete stage format and its links with selection.
- Complete table of moves, abilities and parameters.
- Complete identity of a new character: slot, resources, voice and persistence.
- Cause of the `0x85CBD643` crashes in `dbz3_060.log` and `dbz3_062.log`.
  Those logs contain no `AFS OVERRIDE HIT` of entry 327 and are not evidence
  against the Tien bin.

## 3. Architecture to investigate

```text
XEX/decrypted image
  -> guest tables and slot enumeration
  -> identity/character
  -> AFS resource resolution
  -> physical/virtual table and LZX
  -> #AMB -> #AWO/#AWG/#AZT/#ACM
  -> axes, arms, mesh-ref, zones, bboxes, descriptors
  -> vertex/index buffers and transforms
  -> GPU
  -> menu, fight, animation, voice and saving
```

Each link must record guest address, consuming function, AFS entry, offset,
size, endian, structure, preconditions and result.

## 4. Lab protocol

### Frozen baseline

Before each experiment save region, language, backend, cvars, hashes of
`dbz3.exe`, DLLs, `default.xex`, AFS and mods, plus a fresh log. US/EU are not
mixed. An experiment has at most one causal change.

### Classification

- `NO_EFFECT`: there was no request or hit of the override.
- `INFRA_CRASH`: a crash with no evidence the tested resource was read.
- `PARSE_CRASH`: confirmed hit and a crash during deserialisation.
- `DRAW_CRASH`: resource parsed and a crash preparing/drawing.
- `RENDER_BAD`: complete load with wrong geometry/material/rig.
- `RENDER_OK`: visible and stable in the minimal scene.
- `FLOW_OK`: select, fight, victory/rematch and exit stable.

### Mandatory manifest

Each experiment will keep a JSON with:

```text
experiment_id, region, xex_hash, dll_hashes, mod_hashes,
afs_entry, physical_size, virtual_size, compressed_size,
expected_hits, observed_hits, last_guest_pc, result, notes
```

The decompressed bin, compressed bin, intermediate JSON, OBJ, log and captures
will also be kept.

## 5. Phases

### F0 — Infrastructure and traceability

- Record the region and hashes at startup.
- Correlate `AFS LOOKUP`, `OVERRIDE HIT`, `MOD READ`, size requested and served.
- Capture the guest PC and the failure context.
- Test the flow without mods and a control HD→HD swap in entry 327.

Acceptance: distinguish `NO_EFFECT`, `INFRA_CRASH` and `PARSE_CRASH` without
relying on the game's picture.

### F1 — Guest image and tables

- Dump US/EU with hashes and ranges.
- Label the tables of slots, portraits, 184-byte records, availability,
  forms and AFS runs.
- Follow readers and writers in `generated/`.
- Find counts, limits and validations.

Acceptance: describe `cursor -> slot -> record -> model -> portrait` with
concrete functions and offsets in both regions.

### F2 — AFS and resources

- Map guest request to AFS, entry, offset and size.
- Compare physical read, virtual table and mid-insert.
- Confirm bins larger than `to_read`, including mappings.
- Determine whether resolution uses entry, offset, AFL, group or descriptor.

Acceptance: follow a control override from the guest call to the
decompressed bytes consumed.

### F3 — Parser and render

- Separate layouts A, B, C, face, vb2 and stages.
- Model containers, relative pointers and endianness.
- Decode pool → mesh-ref → zones → bboxes → descriptors.
- Round-trip original bins without semantic changes.
- Run unit permutations, one structure per experiment.
- Capture the first divergent guest read.

Acceptance: a stable round-trip and a minimal permutation that explains the
first deformation or crash.

### F4 — PS2 → HD

- Route A: injection per zone/material over a kept HD pool, falling back to
  the HD vertex if the matching is not safe.
- Route B: a full port with a new pool only after closing F3.
- First validate the common rig without the cape; Tien with cape will be
  another experiment.
- Use the template's resources and textures until the draw is validated.

Acceptance: `RENDER_OK` offline, `RENDER_OK` in the minimal scene and then
`FLOW_OK`.

> **F4 update (2026-09-30) — the offline oracle refutes "cause = skin".**
> Comparing `cell_native` (good) vs `cell_win2` (port) decompressed: `world`
> (bind) IDENTICAL, `bone`@+16 IDENTICAL, `uv`@+40 IDENTICAL, IB/bones equal,
> no axis permutation, model-space bounds almost identical; only `pos`/`nrm`
> change. ⇒ The port is structurally correct. The cause of the deformed
> render is NOT the bind/skin: look at **how the renderer interprets
> `pos`/`nrm`** or the **VB served to the GPU**. Tools:
> `awo_tools/bind_oracle.py`/`bind_oracle_bones.py`; detail in
> `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` §21 and
> `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md` (oracle method).

### F5 — Roster and new content

- A slot alias reusing the original resources.
- Independent model and portrait.
- Record, forms and moveset.
- Voice, texts, aura and persistence.
- An experimental profile separate from normal saves.

Each dependency is enabled in a separate test.

### F6 — Stages, abilities and tools

Investigate the stage layout, collision/animation, `#ACM`, fight parameters
and a generic duplication pipeline with a manifest and rollback.

## 6. First battery

1. Baseline without mods, US, menu and a fight with Krillin.
2. A known HD→HD swap in entry 327 with a confirmed hit.
3. A temporary Tien bin, US only and with hit/read logs.
4. Tien over Tenshinhan, not Krillin, to remove the rig change.
5. Tien without the cape, only the 42 common bones.
6. Tien with the cape, adding the 10 extra bones.
7. Only afterwards, rebuild the pool and the draw structure.

The test that crashed when placed over Krillin is provisionally classified as
`INFRA_CRASH` until it is shown that entry 327 was served.

## 7. References

- Format: `docs/03_formatos/AWO_FORMAT.md`, `BIN_LAYOUT.md` and
  `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md`.
- Roster: `MAPA_ROSTER_HD.md` and `AUDITORIA_DATA_CMN.md`.
- Port: `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md` and dated sessions.
- Historical RE: `awo_tools/RE_PROGRESO.md` and `awo_tools/CONSOLIDADO.md`.
- Operation: `AGENTS.md` and `docs/05_build/COMO_COMPILAR.md`.

If an old document contradicts a later reproducible test, the later test
prevails and the correction is marked with a date; history is not deleted.
