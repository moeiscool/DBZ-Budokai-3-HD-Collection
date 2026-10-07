# ROADMAP — Model swaps, costumes and roster (HISTORICAL)

> **SUPERSEDED by `docs/HOJA_DE_RUTA_2026_09.md`** (2026-09-02). Kept as a
> record of the original modding plan (2026-08-14, 3 phases: models →
> costumes → roster). Phase 1 (model swap) was **completed and validated**
> (native swap + injection, see `AGENTS.md` §3.4). Phase 3 (roster) is today
> the axis of content RE in the current roadmap.

---

## PHASE 1 — WORKING MODEL SWAP (understand the models in depth)

### Goal
Get a working HD→HD model swap (e.g. Goten in Krillin's slot) to understand
EXACTLY how the guest parses and validates the bins.

### Current state
- ✅ The per-entry override works (the bin is served whole).
- ✅ The pipeline's 3 fixes are applied and documented.
- ✅ We have `analyze_bin_hd.py` (parser with the official template).
- 🔴 The guest crashes when processing another character's bin (content, not mechanism).

### Findings that guide phase 1
1. **The guest does NOT validate the magics** (#AWO/#AWG do not appear as
   constants in the guest code) — it trusts the AFS index and reads the header
   by offsets.
2. **The vertex stride of 44 is confirmed** in the guest (`mulli r11,r11,44`).
3. **The community has no PS2→360 converter** — our jump is unique. The HD
   method they document: decompress → 010 Editor + B3_AMB template → recompress.
4. **The crash is about CONTENT**: the bin is served whole (got=106496) and
   still crashes → the guest rejects the structure of Goten's bin.

### Phase 1 plan (in order)
1. **[IN PROGRESS] Instrument the runtime** to log the **guest PC** where bin
   327 is processed. Compare the flow of the original bin (works) vs Goten
   (crashes) → see the exact address where they diverge.
2. **Identify the real guest parser**: with the guest PC, locate the function
   in `generated/dbz3_recomp.*.cpp` and read ITS parsing logic.
3. **Isolate the field that crashes**: with the parser identified, compare
   Krillin's bin vs Goten's field by field → learn what it validates.
4. **Try a swap with bins of the SAME skeleton**: some B3 HD characters have a
   structure almost identical to Krillin (same pose). If a swap works, the
   format is validated.
5. **Convert PS2→HD correctly**: with the format understood, apply the
   AMO0→AWO re-layout (AWO_FORMAT.md) to Janemba.amb.

### Tools for phase 1
- `rexglue-sdk/src/filesystem/devices/host_path_file.cpp` — instrument here
- `generated/dbz3_recomp.*.cpp` — the real guest parser
- `awo_tools/analyze_bin_hd.py` — analyse bins
- Tracy (build win-amd64-tracy) — profiling

---

## PHASE 2 — EXTRA COSTUMES (costumes without losing slots)

### Goal
Add extra costumes to characters without losing slots or breaking the game.

### Key data
- **Each character already has alternative outfit slots**: Krillin has
  327 (normal), 328 (Buu Saga), 329 (Namek). They are separate bins.
- The community adds costumes **by replacing alternative outfit slots** or
  with SLXS (Lesson 1-2 "Adding models to costumes").
- B3 HD's SLXS is the file that maps character→costumes.

### Phase 2 plan
1. Map the costume slots of every character (from the AFS).
2. Check how SLXS assigns costumes to characters.
3. Try: duplicate a Krillin costume into an empty slot → see whether it
   appears as a selectable costume.
4. If it works: the pipeline for new costumes = free slot + edited bin.

### Resources
- `modding resources discord\tutorials\SLXS...` (lessons 1-2, 2-2)
- `mod center\SLXS Editor v0.50`
- `All_Character_Slots.txt`

---

## PHASE 3 — ADD CHARACTERS TO THE ROSTER

### Goal
Add new characters to the roster (duplicating an existing one) without losing anyone.

### Key data
- On PS2, the roster is edited via SLXS (character blocks + select screen,
  Lesson 4-1) or cheats for hidden ones.
- **In the HD Collection there is no public example** — we will be the first.
- The user's plan: **duplicate an existing character right below another**
  (use an empty AFS slot) and change its model/face.

### Phase 3 plan
1. Identify empty AFS slots (or how to duplicate an entry).
2. Understand B3 HD's SLXS (how it maps roster → characters → bins).
3. Duplicate a character (e.g. Krillin) into the new slot with its own bin.
4. Add a new face (select texture) to the duplicated character.

### Resources
- `mod center\SLXS Editor v0.50`
- `modding resources discord\tutorials\SLXS Edit Tutorial - Lesson 4-1`
- `DBZ_B3_Character_Bin_List.txt`

---

## GUIDING PRINCIPLE

> **Do not guess the format — read it from the guest.** The recompiled code in
> `generated/` is the REAL parser. Every field of the bin is validated by a
> guest instruction. By instrumenting the runtime (logging the guest PC) we can
> see exactly what the parser reads and validates, and adapt our bins to it.
> The community's documentation is a guide, not the ultimate truth — they work
> on PS2, we on the only HD with a recomp.

---

## QUICK REFERENCES

| Topic | Where |
|---|---|
| Mod pipeline (override) | `docs/02_mods/COMO_HACER_MODS.md` |
| Model swap research | `docs/02_mods/MODEL_SWAP.md` |
| Bin format | `docs/03_formatos/` + `AWO_FORMAT.md` |
| Tools | `docs/04_herramientas/TOOLS.md` |
| Building | `docs/05_build/COMO_COMPILAR.md` |
| PS5 build | `docs/PS5.md` |
