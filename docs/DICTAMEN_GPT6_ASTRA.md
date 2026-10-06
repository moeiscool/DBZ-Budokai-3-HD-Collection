# GPT-6 ASTRA ASSESSMENT — Native slots + PS2→B3 HD port

> **Date**: 2026-09-07.
> **Input**: `docs/BRIEFING_GPT6_ASTRA.md` (full project briefing).
> **Author**: GPT-6 Astra (external adviser). Reproduced in full (originally
> in Spanish, translated to English 2026-10-06) + a local analysis appendix
> (§0) with what is new compared to our state.
> **Value**: strategy and experimental method we had not designed; corrects 3
> assumptions and proposes an execution plan 0-7 prioritised by risk.

---

## 0. LOCAL APPENDIX — What it brings and what it corrects (reading summary)

Before the literal assessment, the operational reading for us:

### 0.1 Three corrections to our assumptions
1. **`0xFFFF` = empty cell, NOT a free character.** The proven empty-slot
   mechanism does not imply that there are characters available. Distinguish
   **interface cell / portrait ID / character ID / form ID**.
2. **`bone@+28` is not universal.** It is documented for sec34 (Krillin); in
   format C the bone is at `+40`. **Every test must choose the layout per
   AWG**, never apply a global offset.
3. **The mid-insert enlarges an existing AFS entry; it does NOT prove that new
   indices can be added.** Increasing the AFS count (3990 entries) requires
   validating separately: the count, the virtual table and their consumers.

### 0.2 New findings (we had not got there)
- **The byte at `r30+12` is NOT necessarily the global number of
  characters**: the limit may be per page/row/mode. `sub_82180AA0` must be
  instrumented (log `r30`, `r30+12`, caller, mode, initial/final `r29`) and
  **who writes `r30+12`** must be traced (watchpoint on guest memory).
- **Cheap and safe test**: reduce the observed value by 1 (do NOT try 39→40):
  if exactly one cell disappears without touching other pages, the byte's
  scope is identified.
- **Order of preference of paths**: (1) reuse a real reserved cell if it
  exists → (2) data patch in guest memory → (3) hybrid (tables extended in
  memory + minimal hooks). **It does not recommend re-codegen or touching
  `generated/` as the first step.**
- **The image patch works for DATA, not for already-translated code**: the
  literal limit translated to C++ does not change when PPC instructions are
  patched; and it is not safe to add bytes after the tables (there may be data
  behind them). The portrait address is built DIRECTLY in `sub_8217F3F0` (no
  modifiable indirection) → moving tables requires changing that consumer.
- **Proposed module outside `generated/`**: `src/mods/native_roster`, with a
  manifest per region+hash, verification of original bytes, opt-in, abort on
  mismatch. Without runtime function replacement → a reproducible
  post-processing of the generated code (unique match).
- **First character = duplicate behaviour, not files**: an extra cell that
  **resolves to the ORIGINAL character** (e.g. Android 16), simultaneous
  selection/battle of original+duplicate, an independent record that REUSES
  its resources. Do NOT duplicate CAM/ANM/voice/aura initially. Own
  model/portrait ONLY when independent resolution is proven.
- **Map the 184 B record by behaviour**, not by content: table
  `offset | width | readers | writers | value | hypothesis | test`. **Do not
  assume `r3+64` belongs to the 184 B record** (it may be another UI object).
  Do not clone runtime records with owning pointers: copy the configuration and
  go through the original initialiser.
- **Incomplete playable-character inventory**: missing localised
  name/announcement, voice/audio, stats, forms/fusions/costumes, per-technique
  effects, AI/collision, save indices. The bin map is a base, not a complete
  contract. **Save**: disposable profile + non-persistent slot; do NOT write
  new IDs into normal saves.
- **The reverse test does NOT prove that the whole structure must be
  rebuilt**: it shows that the transformation did not preserve invariants.
  Before regenerating arms/zones: rule out rel/abs indices, vertex base, A
  ranges with another base, non-permuted parallel streams, skinning palettes
  built at load time.
- **Permutation matrix T0-T6** (round-trip without changes → swap 2 vertices
  same descriptor/bone/zone → same descriptor between bones → permute inside
  each A range → move contiguous blocks → global inversion). Verify that the
  geometry rebuilt by indices is **equivalent to the original BEFORE opening
  the game** (positions, UV, normals, bones, weights, winding, degenerates).
- **Order of suspicion in the guest**: (1) resolution of ranges/bases/streams
  → (2) arms/skinning tables → (3) mesh-ref part→zone/bone → (4) zone matrix →
  (5) bboxes (only if clipping appears, not displacement).
- **Regenerating a piece without false negatives**: identify the reader + its
  address computation, classify the field (index/offset/count/range/pointer),
  apply the correct transformation, test on the minimal failing case, and
  confirm on another permutation/model. If no single piece fixes it → try
  combinations justified by traces (there may be 2 dependencies).
- **Port verdict**: **Path A is the delivery path**, not a universal
  converter. Invest in: per-bone/zone/material correspondences, seam
  preservation, per-region thresholds (measured against 0.8), rejecting
  doubtful correspondences while keeping the HD vertex. **Path B = bounded
  research with closed deliverables** (round-trip, minimal failing
  permutation, first runtime divergence); if it does not produce a verifiable
  mechanism → pause.
- **Skeletons**: "same number of bones" does NOT validate compatibility.
  Automatic inventory of HD/B3-GH/IW skeletons (labels, hierarchy, bind
  matrices, convention, skinning/face/accessory bones). Classes A-D
  (identity/reindexable/retargetable/incompatible). Hashes filter, they do not
  decide.
- **Lowest-risk retargeting**: keep the donor's HD skeleton+animations, adapt
  the IW mesh to that rig. Rigid accessories→compatible parent; auxiliary
  bones→redistribution with validation; skirt/tail/face without
  equivalent→explicit limit/discard, do NOT collapse silently. **Do not assume
  a single bone field describes all influences** (check the target's skinning
  format and arms). Minimal tests: bind pose, raised arms, elbows/knees, torso,
  root, attack poses.
- **Textures**: separate 4 stages (PS2 swizzle/palette decode → verifiable
  intermediate image → BC2 compression → DDS+`#AZT` conforming to an HD
  reference). **Do NOT impose a global `mipmaps=0`** (absence of a chain ≠ a
  zero field). Keeping the size = an initial simplification, not permanent
  (mid-insert covers growth once the virtual table is validated).
- **Offline validation**: OBJ only validates static geometry. Add a **CPU
  skinning validator in several poses** + checks of offsets/alignment/stride/
  bones/weights/IB/range B inside the IB/flag preservation/bboxes/compression
  round-trip + geometric comparison by attributes.

### 0.3 Execution plan (from the assessment, §5)

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
| Bounded parallel | Path B discriminator | First dependency proven before the general regenerator |

First delivery: **a real additional slot with reused HD behaviour and, later,
its own appearance** (without promising an IW moveset or exact topology).

---

# ASSESSMENT (FULL TEXT)

## Assessment

**I recommend two separate lines: an additional slot that initially reuses a
complete HD fighter, and injection as the visible-content path. The exact port
should progress as bounded research, without blocking either.**

I have read the four documents. The plan below distinguishes documented facts
from what still requires instrumenting the executable; I do not treat the code
or the binary image, which are not attached, as inspected.

### Three important corrections before starting

- **`0xFFFF` demonstrates an empty-cell mechanism, not the existence of a free
  character.** The 39 portrait rows shown are occupied. Interface cell,
  portrait ID, character ID and form ID must be distinguished.
- **`bone@+28` is not universal.** It is documented for Krillin's sec34; in
  format C it is at `+40`. Every test must choose the layout per AWG, never
  apply a global offset.
- **Mid-insert allows enlarging an existing AFS entry; it does not show that
  new indices can be added.** Increasing the 3990 entries requires validating
  the count, the virtual table and their consumers separately.

---

## 1. Native slot: strategy and initial experiment

### 1.1 Locating the count without introducing out-of-range accesses

The comparison against the byte at `r30+12` indicates that **that loop gets the
limit from memory**. It does not show that it is the global number of
characters: it could be the number of cells of a page, row or mode.

I would instrument `sub_82180AA0` to log:

- Address of `r30`, value of `r30+12`, caller and game mode.
- Initial/final values of `r29`.
- Base indexed with stride 184 and the indices actually used.
- Correspondence between character record, created cell and the ID written
  to `r3+64`.

Then I would trace **who writes `r30+12`** via a watchpoint on guest memory or
instrumentation of the writer in the recompiled C++.

**Cheap and safe test:** temporarily reduce the observed value by one, after
it is initialised and before enumeration. If exactly one cell disappears,
without changing other pages, we will have identified its scope. **Do not
start with 39→40:** it may read beyond the tables or write outside the widget
array.

Possible outcomes:

| Origin of the byte | Intervention |
|---|---|
| Static table copied into the object | Patch the source before the copy |
| Value computed from a list | Extend the list and check capacity |
| Immediate in a recompiled function | Hook or reproducible modification of that function |
| Per-page/row count | Also extend navigation and layout |

### 1.2 Choosing between the three paths

**Order of preference:**

1. **Reuse a really reserved cell**, if it exists and supports navigation and
   confirmation.
2. **Data patch in guest memory**, if there is enough capacity and enough
   references.
3. **Hybrid solution: tables extended in guest memory + minimal hooks of the
   recompiled code.**

I do not recommend a general modification of the generated code or re-codegen
as the first step.

#### A. Reusing empty cells: an opportunity, not an assumption

I would dump all the select cells in several unlock states and modes. For each
`0xFFFF`, I would check:

- Is it grid padding, a locked character or a reserved space?
- Can the cursor reach it?
- Do confirmation and loading accept a valid ID?
- Does activating it shift or remove another character?

**Unlocking an existing character does not count as adding one.** An extra
cell that aliases a character does work as a first milestone, but it does not
yet show a new fighter ID.

#### B. Image patch: valid for data, not for already-translated code

> **⚠️ STATE 2026-09-07**: **path 2 (guest-memory data patch)** was tried on
> the "?" cell (slot 38 → Android 16, tag 28) and **FAILED with 3 identical
> crashes** `0xC0000005` (`write of guest 0x82020664`). Root cause: the slot→tag
> table `0x82020618` is in an `XEX_SECTION_READONLY_DATA` section of the image,
> and the guest **persists the chosen tag by writing there when confirming**
> the "?" — it is not a write from the hook. Unprotecting the page from a hook
> is not enough (the crash comes from the guest codegen). For this path to work
> the section would have to be made writable in the **loader/SDK**
> (`xex_module.cpp`), not in the hook. **Full detail: HISTORICO §16.**

It is viable to change values inside the current tables. **It is not safe to
add bytes after them:** there may be other data immediately behind.

If growth is needed:

- Reserve **guest** memory with a long enough lifetime.
- Copy and extend the necessary tables.
- Redirect their consumers.
- Keep offsets, pointers and integers in the corresponding guest format.

The portrait address is built directly in `sub_8217F3F0`. If there is no
modifiable indirection, **moving the table requires changing that consumer**.

Besides, patching PPC instructions in the image does not automatically change
the already-recompiled C++ instructions. A translated literal limit requires a
hook, a transformation of the generated code or re-codegen.

#### C. The implementation I would choose

A module maintained outside `generated/`, for example
`src/mods/native_roster`, with:

- A manifest per region and executable hash.
- Verification of original bytes/values before applying changes.
- Tables extended in guest memory.
- Small hooks for bases, limits or ID resolution that really need them.
- Opt-in activation; on mismatch, do not apply the mod.

If the runtime does not offer function replacement, I would use a
**reproducible post-processing of the generated code**, with unique-match
checks. I would avoid hand-editing files that get overwritten.

### 1.3 First character: duplicate behaviour, not all the files

I would choose a simple, fully playable HD fighter without complex
transformations —for example, Android 16— and do:

1. An additional cell that resolves to the original character.
2. Simultaneous selection and battle of the original and its duplicate.
3. An independent character record that reuses its resources.
4. Own model and portrait, once independent resolution is proven.

**I would not duplicate CAM, ANM, voice and aura initially:** sharing
references reduces variables.

For exclusive resources there are two later options:

- Reuse AFS entries whose lack of use is proven.
- Implement a real extension of the virtual AFS directory, including new
  indices and count.

A global override of the original model would change both characters; **it
does not prove the new slot's independence**.

### 1.4 Mapping the 184-byte record by behaviour

It is not necessary to understand the 184 bytes before the first alias. It is
necessary to identify the fields consumed by selection and battle.

I would build a table:

`offset | width | readers | writers | value per character/form | hypothesis | test`

Priority:

1. Origin and lifetime of the base; initialisation and copies.
2. Fields `+14`, `+18`, `+114`, without attributing semantics in advance.
3. Identity, forms/costumes, resource references and selection conditions.
4. Dependencies used during loading, battle and exit.

I would compare records of different characters and different forms of the
same character; then change **one field at a time**, with valid values from a
donor.

I would not assume that `r3+64` belongs to the 184-byte record: it may be
another interface object. Nor would I blindly clone a runtime record with
owning pointers; I would rather copy its configuration and go through the
original initialiser.

### 1.5 Inventory still missing

The bin map is an excellent base, but **it is not a complete contract for a
playable character**. Accesses must be captured during selection, intro,
battle, techniques and victory to locate:

- Localised name and selection announcement.
- Voice banks and audio events.
- Stats, abilities/equipment and unlock rules.
- Forms, fusions, transformations and costumes.
- Effects and accessories referenced by techniques.
- AI tables and any character-specific collision configuration.
- Persisted indices, bitsets and save limits.

Portraits already work via `data_cmn.afs`; I would not touch `data_eng.afs` to
replace them. Localised texts are another investigation.

**Save:** first a disposable profile and a non-persistent experimental slot.
Do not write a new ID into normal saves until readers, sizes and validation are
known.

---

## 2. Exact port: discriminating experiment

### 2.1 What the reverse test really shows

It shows that **the transformation done did not preserve all the runtime's
invariants**. It does not yet identify the hidden link nor prove that the whole
structure must be rebuilt.

Before regenerating arms or zones, I would rule out:

- Relative versus absolute indices.
- Vertex base and effective buffer offset.
- A ranges numerically correct but interpreted with another base.
- Parallel streams that were not permuted.
- Palettes or skinning buffers built at load time.

The draw log can confirm correct indices and counts while the draw consumes
**another buffer or a wrong base**.

### 2.2 Preparation: a single reproducible case

First I would run `cell_port_Afix_test` on its own, as the updated roadmap
asks. I would not reactivate the old Janemba experiment.

For the discriminator I would use a **native HD** model, with no PS2
conversion or skeleton change:

- Preferably the same Cell and AWG where the failure already reproduces.
- Babidi as a second simple case of a different format, **only as a technical
  guinea pig over Krillin**; he is not a playable character nor a slot
  candidate.

Freeze:

- Hash of the original bin, modified bin and loaded DLL.
- A single active mod.
- Log of the override actually served.
- Pose, camera and animation sequence.
- Full restart for each variant that changes data processed at load.

### 2.3 Permutations that isolate the problem

Explicitly define a permutation **old index→new index**. Move complete vertex
records and remap each IB value, keeping its sequence.

| Test | Modification | What it isolates |
|---|---|---|
| T0 | Original | Reference |
| T1 | Round-trip without semantic changes | Serialiser errors |
| T2 | Swap two vertices of the same descriptor, bone and zone | Strict index dependency |
| T3 | Swap within the same descriptor, between bones | Skinning or grouping by bone |
| T4 | Permute within each A range | Internal dependency without moving limits |
| T5 | Move whole blocks, keeping each range contiguous | Bases and ranges between parts |
| T6 | Global inversion | Reproduce the known broad failure |

In T2–T4 I would choose vertices with **the same descriptor membership**, if
there are overlapping ranges.

Before opening the game, verify that the geometry rebuilt by indices is
equivalent to the original: positions, UV, normals, bones, weights, winding
and degenerates. It is not enough for the OBJ to "look like it".

**Advantage:** an equivalent permutation does not change the geometric bboxes.
If recomputing them alters the result, their interpretation or references
should be investigated, not simply attributed to new bounds.

### 2.4 Locating the first divergence in the guest

I would capture three points:

1. Pool and structures just decompressed.
2. Buffers/palettes produced during initialisation and skinning.
3. Buffer, offset, stride, vertex base, IB and constants sent to the draw.

I would compare the data taking the inverse permutation into account. The
first divergence indicates where to instrument additional reads.

**Order of suspicion:**

1. Effective resolution of ranges, bases and streams.
2. Arms or auxiliary tables used to build skinning/palettes.
3. Mesh-ref and the part→zone/bone association.
4. Zone matrix.
5. Bboxes, mainly if disappearances or clipping appear, not anatomical
   displacement.

It is a prioritisation, not a conclusion about their semantics.

### 2.5 Regenerating a piece: avoiding false negatives

I would not do "reverse + modify suspicious fields" without knowing what they
represent. For each candidate:

1. Identify the reader and its address computation.
2. Classify the field: index, offset, count, range or pointer.
3. Apply the corresponding transformation.
4. Test it on the **minimal failing case**, not first on the global inversion.
5. Confirm on another permutation and another model.

If no isolated correction works, try combinations justified by the traces:
there may be two simultaneous dependencies. **That no single piece fixes the
model does not prove that none takes part.**

### 2.6 Verdict: injection now, exactness as the next capability

**Path A is the current delivery path, but not a universal converter.** It
keeps the HD topology; it cannot exactly reproduce silhouettes, accessories
and surfaces absent from the template.

I would invest first in:

- Correspondences restricted by bone, zone and material.
- Seam preservation and separation between nearby surfaces.
- Hard thresholds per region, measured against the known 0.8 result.
- Rejecting doubtful correspondences and keeping the original HD vertex.

I would not go back to soft blends by default: they already made the tested
cases worse.

**Path B is still necessary for arbitrary characters with high fidelity.** I
would assign it a first investigation with closed deliverables: round-trip,
minimal failing permutation and first runtime divergence. If it does not
produce a verifiable mechanism, it is paused; `draw` is not rewritten blindly.

---

## 3. 1:1 skeletons and Infinite World characters

### 3.1 "Same number of bones" does not validate compatibility

I would generate an automatic inventory of all HD, B3 GH and IW skeletons:

- Original labels and indices.
- Parent, children, roots and hierarchy.
- Local and global bind matrices.
- Coordinate convention, scale and orientation.
- Bones used by skinning, face and accessories.
- Animation channel correspondence, when it can be extracted.

Classification:

| Class | Condition | Action |
|---|---|---|
| A: identity | Same bones, order, hierarchy and compatible bind | Direct reuse |
| B: reindexable | Same rig, different order | Remap all references |
| C: retargetable | Different hierarchy/proportions, clear equivalences | Adapt to the HD rig |
| D: incompatible | Essential bones or deformations without equivalent | Postpone or extend capabilities |

I would use documented tolerances to compare matrices, with a visual check of
axes and joints. Hashes serve to filter, not to decide approximate
equivalence.

Normalising name prefixes only helps to find candidates: **it does not show
that two bones have the same function**.

### 3.2 Lowest-risk retargeting

For the first non-1:1 IW, I would keep the **donor's HD skeleton and
animations**. I would adapt the IW mesh to that rig; I would not also try to
port its moveset.

Process:

1. Choose the donor by hierarchy, proportions and joints, not just looks.
2. Align scale, orientation and rest pose.
3. Define explicit semantic correspondences.
4. Adapt the mesh to the target bind pose.
5. Transfer weights and convert positions to target local space.
6. Transform normals correctly and verify deformations.

Extra bones:

- Rigid accessories: assignment to the compatible parent, accepting the loss
  of movement.
- Auxiliary bones: redistribution of influences with validation.
- Skirt, tail or face without equivalent: explicit limitation or a discarded
  candidate; do not collapse them silently.

Nor would I assume that a single `bone` field describes all the influences
supported: the target's skinning format and arms must be checked.

**Minimal tests:** bind pose, raised arms, elbow/knee flexion, torso twist,
root displacement and attack poses. A model correct at rest can be completely
wrong when animated.

Janemba comes after passing these tests with a simple case. Pikkon/Pan are
candidates to scan, not prior commitments.

---

## 4. Textures and offline validation

### Textures

The converter must separate:

1. PS2 decoding: swizzle, palette, format and alpha.
2. Verifiable intermediate image.
3. BC2/DXT3 compression.
4. DDS and `#AZT` wrapper conforming to an HD reference.

For the first case I would keep the template's dimensions and mipmap policy.
**I would not impose `mipmaps=0` on all DDS files:** I would check flags,
count and payload; the absence of an extra chain and a numeric zero field are
not equivalent for every reader.

The BC2 bitmap uses 4×4 blocks and 16 bytes per block, including dimensions
rounded up to blocks. I would validate each level, alpha and the
material→texture correspondence.

Keeping the size is an initial simplification, not a permanent constraint:
growth can use mid-insert once the virtual table and the full read are
checked.

### Additional checks

I would add to the verifier:

- Offsets and pointers inside their section, with the correct relative base.
- Alignment and no disallowed overlaps.
- Stride, size and vertex count consistent per format.
- Valid bone IDs and a cycle-free hierarchy.
- Valid weights and bind inverses.
- Finite values and plausible normals.
- Valid IB, correct interpretation of strips and degenerates.
- Range B inside the IB; effective indices compatible with A and its base.
- Preservation of flags in packed A/B fields.
- Bboxes in the correct space.
- Valid references to materials and textures.
- Compression/decompression round-trip and read sizes.
- Geometric comparison by attributes, not just triangle count.

I would add a **CPU skinning validator for several poses**. OBJ only validates
static geometry and can hide precisely the failure of interest.

---

## 5. Priority and order of execution

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
| Bounded parallel | Path B discriminator | First dependency proven before the general regenerator |

With a single person, I would do milestones 0–3 first and then choose the IW
from the scanner's results. With two, I would separate roster/runtime from
geometry/rigging; **I would not change both systems in the same experiment**.

The first delivery should be **a real additional slot with reused HD
behaviour and, later, its own appearance**, without yet promising an IW
moveset or exact topology. That way visible value is obtained without making
the most uncertain RE a requirement of the whole project.

---

## CROSS-REFERENCES

| Topic | Where |
|---|---|
| Briefing that produced the assessment | `docs/BRIEFING_GPT6_ASTRA.md` |
| Roster tables in the guest image | `docs/03_formatos/MAPA_ROSTER_HD.md` §7 |
| HD draw structure | `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md` |
| Port pipeline (injection/port) | `docs/07_ports/` + `mod center hd/ports/` |
| Integrated execution plan | `docs/HOJA_DE_RUTA_2026_09.md` |
| Operational context | `AGENTS.md` |
