# TECHNICAL BRIEFING — DBZ Budokai 3 HD Collection (ReXGlue recompiled)

> **To**: GPT-6 Astra (design and engineering adviser).
> **Author**: the `dbz3` project (recompiled PC port of DBZ Budokai 3 HD
> Collection, Xbox 360).
> **Date**: 2026-09-07.
> **Goals requested**: (1) **add NATIVE CHARACTER SLOTS** to the game's select,
> and (2) **port PS2/3D models in general** to the game's HD format, including
> characters that do NOT exist in an HD version.

---

## 1. WHAT THE PROJECT IS

DBZ Budokai 3 HD Collection is an **Xbox 360 → PC** port made by **static
recompilation** with the **ReXGlue SDK** (derived from Xenia):

- The Xbox 360 executable (`yae3_xenon.xex`, PPC32) was recompiled to x86 C++
  (`generated/dbz3_recomp.*.cpp`, ~44 files). The recompiled code is the
  game's **real parser/executor**: everything the game reads is validated by
  the guest's instructions.
- The host runtime (`src/`, `rexglue-sdk-0.10/`) emulates kernel, guest
  memory, input, audio and graphics (D3D12 primary, Vulkan experimental).
- The game data are in **AFS** files (per-entry containers): `data_cmn.afs`
  (characters + main content, 3990 entries), `data_eng/ger/spn/fra/ita/usi.afs`
  (select/menus per language), `adx_*.afs` (audio).
- The bins inside the AFS are **LZX compressed** (`xbcompress /N:2048`).
- **The decrypted guest image** can be dumped to disk with a mini tool
  (`out/analysis/guest_image/`): `dbz3_us_image.bin` (7 MB, guest memory map
  0x82000000-0x826D0000). **The game's roster lives THERE** (static guest data
  tables), not in the files.

---

## 2. FILE FORMATS (empirically validated facts)

### AFS
- Header: magic `AFS`(3B)+pad(1B)+count u32 → table `(addr u32, size u32)` ×N.
- The table is read at **offset 8** (NOT at 0x10).
- The host runtime supports **per-entry override** without repacking:
  `mods/<mod>/us/data_cmn.afs/<entry_index>/geom.bin` (LZX-compressed bin).
  If the bin grows beyond the slot the guest reads
  (`to_read = ceil(slot/0x1000)*0x1000`), the runtime applies **VIRTUAL
  MID-INSERT** (`AfsGetVirtualTable`): the entry grows in place (align 0x800)
  and later ones shift — a consistent virtual table. This allows serving bins
  LARGER than the original.

### Character bin (#AMB)
- `#AMB` (big-endian) → contains `#AWO` (model), `#AWG*` (mesh groups),
  `#AZT` (DDS DXT3/BC2 texture).
- **The bin is SELF-CONTAINED**: each character brings its own vertex format;
  the guest auto-detects. There are different vertex formats A/B/C.

### Verified vertex layouts (critical!)
- **Format C (most: Goku, Vegeta, Babidi, Goten)** — AWG0, stride 44:
  ```
  +0 x | +4 y | +8 z (bone-local, [-1,1]) | +12 0xFFFFFFFF
  +16 u | +20 v | +24 n.x | +28 n.y | +32 n.z | +36 weight | +40 BONE
  ```
  IB = triangle STRIP (consecutive indices, alternating winding, degenerates as
  jumps, NO 0xFFFF restarts). `+0x2C` = buffer size in bytes.
- **sec34 format (Krillin, stride 44, align +2)**:
  ```
  +0 FFFF | +4 u | +8 v | +12 z_local | +16 x_local | +20 y_local
  +24 weight | +28 BONE (u32 0-35) | +32 n.z | +36 n.y negated | +40 n.x
  ```
- **vb2 (static)**: ABSOLUTE positions, bone=0xFFFFFFFF (no skin).
- **Face AWG** (Goku/Vegeta): buffer at h+0x1F0, stride 44, head bone.
- **Bone mapping**: Krillin's 51 bones with labels; sec34 uses bones 0-35
  (legs/face go to vb2). The skeletons **HD == PS2** (same game, same bin
  numbering as the PS2 Greatest Hits).

### Draw structure (AWG0 mesh group)
- **Mesh-ref blocks** (0x50 each): vertex type (B5 body / B4 face) +
  texture/shader + `X,Y` = part index and primary bone.
- **Axes** (80B each): quat+pos (bind pose) + seal + arm_ptr +
  child/sibling/parent.
- **Zone matrix** (0x28E0): diagonal of bones + pointers to bboxes.
- **Bboxes** (AABB per zone, 0x40).
- **Descriptors** (0x60 each): label + `max N m` + **range A** (vertices of
  the sec34 pool) + **range B** (IB indices). Verified: the IB indices in range
  B ALWAYS fall in range A.
- The guest draws the strips by **A/B descriptors + IB**; the transform uses
  the **vertex's bone (+28)**. **The sec34 pool order matters**: the structure
  references the pool by index (mesh-ref/zones/bboxes).

---

## 3. GOAL 1 — NATIVE CHARACTER SLOTS

### Current state (what we know)

**The select's roster lives in the guest IMAGE** (not in the AFS files). Two
static tables were located:

1. **Select portrait/slot table** at `0x82372818` (image offset `0x372818`):
   **78 u32 = 39 slots × 2 entries** (a pair per slot; the second value is
   usually `first+1`). Slot 10 = `[3930, 3931]` = Krillin and slot 19 =
   `[3934, 3935]` = Nappa (both **CONFIRMED by a substitution experiment**:
   override 3934→slot 3930 showed Nappa's portrait on Krillin). The 39 rows
   correspond to the select's selectable characters.
2. **Per-character bin table** at `0x823268C0` (offset `0x3268C0`): runs of
   AFS indices separated by `0xFFFFFFFF` (models → CAM → LIPS/ANM). The run
   `[323..329]` contains Krillin's group (327/328/329).

**Guest functions identified** (in the recompiled code):
- `sub_8217F3F0` (`.15.cpp:13877`): consumer of the portrait table. It does
  `lis -32201; addi r9,r9,10264` → `0x82372818`; index `slot*8 + flag*4`
  (slot id read as u16 at `r3+64`; a flag bit at `r3+62`).
- `sub_8217F478` (`.14.cpp:14437`): reads the slot id u16 at `r3+64`; **if it
  is `0xFFFF` = empty slot** (returns without acting); otherwise calls
  `sub_8217F3F0` to resolve the portrait. **This is the "empty slot"
  mechanism — a natural hook for native slots.**
- `sub_82180AA0` (`.15.cpp:13916`): indexes a **character base with
  `mulli r10,r10,184`** → a 184-byte struct per character, reading offsets
  `+14/+18/+114` (u16). Slots are enumerated with a counter (`r29`) compared
  against a byte at `r30+12`.

**How a swap is done today (validated)**: extract the `#AMB` bin of a
character (source), compress it LZX `/N:2048`, install it as a per-entry
override in the target slot (`mods/<mod>/us/data_cmn.afs/<dest>/geom.bin`). It
works because the guest accepts self-contained bins. **But this REPLACES an
existing slot; it does not ADD a new slot.**

### Design questions for you (Goal 1)

1. **How is the slot count (39) decided in the guest?** The counter in
   `sub_82180AA0` compares against a byte at `r30+12`. Is it a fixed limit in
   the code, or a value living in a guest-image table we can patch? How do we
   confirm it cheaply?
2. **"Native slot" strategy: runtime host hook vs re-codegen?** The host
   controls the decrypted image in memory before launching the guest. Options:
   - **(a) Patch the image in memory** at startup: modify the `0x82372818`
     table (add portrait rows) and the `0x823268C0` bin table, without touching
     code. Is it viable if the count is hardcoded?
   - **(b) Patch the recompiled code**: modify the recompiled functions (e.g.
     the loop limit) in `src/` and rebuild. More invasive but deterministic.
   - **(c) Reuse the empty-slot mechanism**: `0xFFFF` = empty. Are there empty
     slots among the 39? Can we "wake" one by pointing it at a new character
     (model + portrait + auxiliaries) via override?
3. **What else does a slot need besides portrait and model?** For a character
   to be PLAYABLE it needs: model (`#AMB` bin), portrait (select table +
   texture in `data_eng.afs`), CAM/LIPS/SCOUT, moveset/animation (large `#ACM`
   bin), voice, aura (0-43) and the entry in the 184 B/slot struct. How do we
   fully map the 184 B struct and which fields distinguish a "playable" slot
   from an "empty" one?
4. **Full character→bins mapping**: we have the definitive map
   (`docs/03_formatos/MAPA_ROSTER_HD.md`): models + CAM + LIPS + ANM + aura per
   character, validated with the catalogue + real probe + AFL names (+6 offset
   from the Pal). Is it enough as a dependency inventory for a new slot, or is
   more needed (voice, stats, colour palette)?
5. **Is there a lower-risk intermediate path?** For example: first add a slot
   that reuses an EXISTING character (double slot = duplicated alternate
   costume) and then a NEW (ported) character. What layered validation do you
   recommend (model in battle → portrait → transformations → voice → save)?

---

## 4. GOAL 2 — PORT PS2/3D MODELS IN GENERAL TO B3 HD

### Context
The 360 B3 HD **IS the same PS2 model** (51 bones, 18 mesh groups, identical
labels) only big-endian with renamed magics (`#AMO0→#AWO`, `#AMG→#AWG`,
`#AMT→#AZT`) and a different mesh-group layout. HD bin numbering = the
**PS2 Greatest Hits** `data_cmn`. We have access to the PS2 AFS (`ps2_games/`):
B1, B2, B2V, **B3 GH**, IW (Infinite World).

### Paths investigated (all documented, verified in game)

| Path | State | Result |
|---|---|---|
| Native B3→B3 swap (HD→HD) | ✅ WORKS | full `#AMB` bin in another's slot |
| PS2→HD injection (Path A) | ✅ WORKS (recognisable) | PS2 body + HD limbs/head; parameter **binary threshold 0.8** |
| Full port (PS2 topology, Path B) | ❌ NO (amorphous) | a reordered pool breaks the draw structure |
| HD→HD head swap | ◑ partial | z-fighting, paused |
| Janemba IW→B3 | ❌ documented FAILURE | deformed mass; do NOT retry without a full converter |

### PS2→HD port pipeline (exists, `mod center hd/ports/`)
`port_ps2_b3_extract → geometry → draw → pack → verify`. Already solved:
- **extract**: parses the PS2 mesh + real IB (FaceType) + rig (bone+weight) +
  skeleton (labels + hierarchy + world matrices). Geometry verified point by
  point = exact PS2.
- **geometry**: local coords + bone → HD buffers (44B skinned sec34 + 44B
  static vb2 + u16 BE IB). **Conversion**: `local = inv(world[bone])·model`;
  normals `[nz,-ny,nx]`.
- **pack + verify**: packs a self-contained `#AMB` + LZX + override + OBJ
  export for feedback without opening the game.

**The REAL blocker of the full port (Path B)**:
> The **sec34 pool order is tied to the draw structure by index** (mesh-ref
> blocks, zone matrix, bboxes, A/B descriptors). When the pool is reordered to
> PS2 topology, that structure becomes inconsistent → deformation in game.
> **Injection works because it keeps the template's pool order.** (Verified:
> the reverse test with an inverted pool DEFORMS; bone0 test: the guest uses
> the vertex's bone +28.)

**Injection (Path A) = the PRACTICAL port today**: HD template (keep the pool
order) + PS2 positions/normals converted to bone-local. Limitation: it is not
the exact PS2 topology (imperfect face meshes/blends; critical binary threshold
parameter: 0.8 good, 2.0 bad; soft/blends ALWAYS make it worse).

### Design questions for you (Goal 2)

1. **How do we unblock the full port (Path B)?** The pending discriminator: do
   reverse + regenerate **ONE piece at a time** (arms / mesh-ref X,Y / zone
   matrix + bboxes / descriptors) to find which one stops deforming when fixed.
   How would you design that experiment to isolate the structure→pool link?
   Which structure do you suspect (arms with vertex offsets, zone matrix,
   mesh-ref)?
2. **Is Path B worth it, or is injection the right destination?** Path B's
   return is the exact PS2 topology (correct face/legs). The cost is rebuilding
   the whole draw structure. Do you recommend investing in Path B or in
   improving Path A's quality (per-zone threshold for the head, seams,
   blending)?
3. **Porting characters that do NOT exist in HD (IW)**: the final goal is to
   bring characters from Infinite World / PS2 3D in general. Identified
   requirement: a **1:1** skeleton (same labels/order) with a target HD bin —
   otherwise retargeting is needed (where Janemba failed). How do we
   find/validate 1:1 skeletons cheaply and what retargeting strategy do you
   recommend for the non-1:1 case?
4. **Texture requirements**: `#AMT` (PS2 LE) → `#AZT` (HD DXT3/BC2, 128B DDS
   header + bitmap). Recommendations for the automatic texture converter
   (mipmaps=0, keep the size so as not to break to_read)?
5. **Validation chain without opening the game**: OBJ export already exists
   (`awg_to_obj_b3.py`, `awg0_export.py`, `awg_cara_export.py`). What additional
   checks (bounds, NaN, triangle count, A/B consistency) do you recommend to
   iterate faster?

---

## 5. HARD ENGINEERING CONSTRAINTS (not guessable)

- The B3 vertex layout is **NOT** B1's: the **bone is at +28**, not at
  +0x10/+16. Old tools using the B1 layout produce a deformed mass.
- The game's LZX compression: **`/N:2048`** (NOT `/N:32`; with /N:32 the bin
  exceeds the slot and the guest truncates → crash).
- Padding to the **exact size** the guest reads
  (`to_read = ceil(slot/0x1000)*0x1000`), or use the virtual mid-insert if the
  bin grows larger.
- A mod is active if it does NOT have the `.disabled` marker; **only one active
  mod per test** (the override serves the first mod in alphabetical order).
- After rebuilding the SDK, copy the canonical DLLs to the build (the build
  overwrites `rexruntime.dll` with a stale version). Always check
  `Select-String rexruntime.dll -Pattern "AfsGetVirtualTable"`.
- Do not touch `github/` (manual upload copy, no automatic commits).
- Recompiled code: `generated/` (US) + `generated_eu/` (EU); the executable is
  dual-region (detects the xex by MD5).

---

## 6. WHAT WE NEED FROM YOU (executive summary)

1. **Native slots**: strategy to add ONE new character slot to the select
   without breaking the guest: in-memory image patch (host hook) vs recompiled
   code patch vs reusing empty slots (`0xFFFF`)? How do we locate the slot
   limit/count and the full 184 B/slot struct?
2. **Full port**: design of the discriminating experiment to locate the
   structure→pool link (which piece must be regenerated when the pool is
   reordered) and verdict: Path B (exact topology) or Path A (injection) as the
   destination?
3. **Porting new characters (IW)**: how to validate 1:1 skeletons cheaply and
   the retargeting strategy for the non-1:1 case.
4. **Prioritisation**: given the current state, what order of work do you
   recommend (native slots vs character port vs both in parallel) and what
   layered validation milestones do you propose for each?

---

## 7. KEY FILES TO DIG DEEPER (if they can be attached)

| Topic | Path |
|---|---|
| Definitive HD roster map (slot→character→bins) | `docs/03_formatos/MAPA_ROSTER_HD.md` |
| Full content audit | `docs/03_formatos/AUDITORIA_DATA_CMN.md` |
| HD draw structure (mapped) | `docs/07_ports/ESTRUCTURA_DIBUJO_HD.md` |
| PS2→B3 port roadmap | `docs/07_ports/HOJA_DE_RUTA_PORT_PS2_B3.md` |
| Injection session (Path A, threshold 0.8) | `docs/07_ports/SESION_INYECCION_2026-08-26.md` |
| Port RE (conv2, amorphous) | `docs/07_ports/SESION_PORT_RE_2026-08-26.md` |
| Decrypted guest image (roster tables) | `out/analysis/guest_image/dbz3_us_image.bin` |
| Recompiled code (real parser) | `generated/` (tables in `recomp.14/15.cpp`) |
| Full operational context | `AGENTS.md` |
| 2026-09 roadmap | `docs/HOJA_DE_RUTA_2026_09.md` |
| Port pipeline (scripts) | `mod center hd/ports/` |
| Bin format | `docs/03_formatos/AWO_FORMAT.md`, `BIN_LAYOUT.md` |
