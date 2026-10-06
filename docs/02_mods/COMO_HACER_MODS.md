# How to make mods for DBZ Budokai 3 HD Collection

> Updated: 2026-10-06 (§5 porting a Shin Budokai character, §6 cameras with the
> Studio, §7 mods on PS5).
> CORRECT validated pipeline (per-entry override + virtual mid-insert).

---

## 1. THE TWO KINDS OF MOD

### 1.1 Whole-file override (replaces an entire AFS)
```
mods/<mod>/us/data_cmn.afs        ← complete AFS file (293 MB)
mods/<mod>/eu/data_cmn.afs
```
- Used by `og_music`.
- Served by the `AfsFindModFileOverride` hook.
- **Drawback**: the whole AFS has to be rebuilt (build_afs.py). It is NO
  longer needed for model/texture swaps.

### 1.2 Per-entry override (replaces ONE bin inside the AFS) — RECOMMENDED
```
mods/<mod>/us/data_cmn.afs/327/geom.bin     ← FOLDER format
mods/<mod>/us/data_cmn.afs/327              ← DIRECT FILE format
```
- Served by the `AfsFindModOverride` hook.
- **No need to rebuild the AFS** — only the bin of one entry (~100 KB).
- **Any bin size**: if it exceeds the slot, the runtime applies the **virtual
  mid-insert** (see §2.4). 2+ simultaneous mods (different entries).

---

## 2. STEPS TO MAKE A MODEL MOD

### Step 0: know the correct entry
The entry = the index in the AFS table (offset 8 of the file, `entry_count` at +4).
- Visible Krillin = **entry 327** (NOT 326). Verified by instrumentation.
- The runtime logs the reads: `AFS327 READ` in `logs/dbz3_*.log`.

### Step 1: extract the original bin
```powershell
# 1. Locate the entry in the AFS (table at offset 8)
# 2. Extract the LZX-compressed bytes
# 3. Decompress with xbdecompress
xbdecompress.exe <entry.lzx> <entry.bin>
```

### Step 2: modify the bin
- To check the B3 HD structure use `awo_tools/awg_to_obj_b3.py`,
  `awo_tools/awg0_export.py` or `awo_tools/awg_cara_export.py`.
- For native swaps use `swap_b3.py` or the launcher's Model Swap tab.

### Step 3: compress with /N:2048 (IMPORTANT)
```powershell
xbcompress.exe /N:2048 <plain_bin> <compressed_bin.lzx>
```
> ⚠️ Do NOT use `/N:32` or `/N:64` — they produce bins bigger than the slot → crash.

### Step 4: pad to to_read
The guest allocates `to_read = ceil(table_size/0x1000)*0x1000`. The compressed
bin is padded with zeros up to that size:
- **If it fits** in the slot (bin ≤ to_read): pad to the slot's to_read.
- **If it is bigger** (e.g. Goten 107006 > Krillin 106496): pad to
  `to_read_virtual = ceil(bin/0x1000)*0x1000` (110592). The runtime allows it
  with the virtual mid-insert: the entry grows in place in the virtual table
  and the later ones shift by +delta. The guest allocates the right buffer and
  receives the complete bin without truncation.

`swap_b3.py` does this padding automatically.

### Step 5: install
```powershell
# Create the mod's folder structure
New-Item -ItemType Directory -Path "mods/<mod>/us/data_cmn.afs/327" -Force
Copy-Item padded.bin "mods/<mod>/us/data_cmn.afs/327/geom.bin"

# Enable (remove .disabled if present)
Remove-Item "mods/<mod>/.disabled"
```

### Step 6: check the logs
```
logs/dbz3_001.log:
  AFS OVERRIDE HIT (folder): ...\mods\<mod>\us\data_cmn.afs\327\geom.bin
  AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=...
```
> `got=to_read` = the guest received the complete bin. If `got < to_read` →
> padding is missing.

---

## 2.4 🔴 VIRTUAL MID-INSERT (2026-08-18)

The guest reads each entry of `data_cmn.afs` with a buffer of
`to_read = ceil(size/0x1000)*0x1000` derived from the AFS table. A mod bin
bigger than that to_read used to be truncated when served by override → crash.

The runtime's solution (patch in `patches/`, files `afs.cpp`/`afs.h`/
`host_path_file.cpp`) presents the guest a **CONSISTENT virtual AFS table**:

- `AfsGetVirtualTable()`: if an override exceeds the slot's `to_read`, the
  entry **grows in place** (slot aligned to 0x800) and **all later entries
  shift** by the accumulated delta — exactly replicating a rebuild with
  mid-insert. The virtual addrs are consistent → the guest finds them
  correctly (unlike the "naive" attempt that inflated sizes while keeping
  addrs: the guest recomputes offsets by accumulating sizes → crash).
- `AfsTranslateOffset()`: for data reads, translates virtual → physical
  (subtracts the entry's delta) and serves the override (complete bin) or reads
  from the physical file at the translated offset.

**Growth criterion**: it only grows if the override > `to_read` (what the
guest already allocates), NOT if it exceeds the physical slot. A mod that fits
(e.g. Gero's textures, 114688 = to_read) shifts nothing.

**Result**: native B3→B3 swaps weighing ~100 KB, in **any direction** (the bin
can be bigger or smaller than the slot), and 2+ model/texture mods active at
the same time.

---

## 3. SLOT SIZES OF KEY ENTRIES

| Entry | Character | Compressed slot | to_read |
|---|---|---|---|
| 327 | Krillin (visible) | 105296 | 106496 |
| 328 | Krillin Buu Saga | 104404 | 106496 |
| 329 | Krillin Namek | 101268 | 102400 |
| 298 | Goten | 107006 | 110592 |
| 270 | Goku | 128062 | 130048 |

> With the virtual mid-insert the bin NO longer has to fit in the target
> entry's slot: if it exceeds it, the virtual table grows the entry and shifts
> the later ones automatically.

---

## 4. HOW TO ENABLE/DISABLE MODS

- **Active**: folder `mods/<mod>/` WITHOUT a `.disabled` file.
- **Disabled**: with `.disabled`.
- **Order**: mods are sorted alphabetically; the first match wins.
- Real activation uses only the `.disabled` marker; `dbz3_enabled_mods` is
  obsolete and does not control the current mods. The per-entry override is
  independent of the profile the launcher displays.

---

## 5. PORTING A SHIN BUDOKAI CHARACTER (from start to finish)

Sources: the PSP ISOs in `ps2_games/` (Shin Budokai = `sb1`, Another Road =
`sb2`) and, for better HD models, the Super Dragon Ball Heroes World Mission
folder in `modding resources/` (`sdbh`). Formats and differences:
`docs/03_formatos/SB_VS_B3_MOVESET.md`.

### 5.1 The quick way (no console)
Launcher → **New characters** → "Import character" → *Shin Budokai: Another
Road* → the character → name → **Import** → PLAY. In the Mod Kit it is the
"Import character" card.

What the importer does (`mod center hd/importar.py importar sb2 GHF --mod … --nombre …`):
1. **Models:** each `BC<XXX>B0n.amb` → HD bin (`awo_tools/psp_amo.py`); with
   `sdbh`, each `bc<xxx>bNN` → HD bin with mouth, 7 faces and ramps
   (`awo_tools/sdbh_model.py`, template = the donor's model). They go in as the
   **forms** of one costume (`modelos_por_traje`).
2. **Moveset and camera:** `awo_tools/sbport.py` (AP 20 → 16 B, HR 160 → 128 B,
   damage × 0.85, codes remapped, global store by table, hyper / throw /
   Dragon Rush / ultimate from the donor). It leaves `moveset/anm_forma1.bin`
   and `moveset/camara.bin`.
3. **Techniques:** `awo_tools/sb_tecnicas.py` (hybrid BSP, official names)
   when ready → `moveset/tecnicas.bin`.
4. **Forms:** `formas = n`, `transformacion = "donante"` (the donor's P+K+G,
   removes SB's down+E), `fisica = "donante"` and one transformation capsule
   per form named after the donor's (its ki bars). See
   `docs/03_formatos/FORMAS_Y_KI.md`.
5. **Voices:** the donor's until the voice module understands `sb2:XXX`.

If `sbport.py` fails or is missing, the character is still imported with
**the donor's hits** (and as many forms as the donor has) and the log says so.

### 5.2 Adjust afterwards (Mod Kit → Characters)
- **Forms, physics and appearance:** forms, base ki per form, model per form,
  hair and belt physics, the donor's transformation.
- **Capsules:** official names, order, **"Set ki"** of each transformation
  (bars you must have; they are not spent).
- **Cameras (Studio):** SB's ultimates bring no camera of their own: make it
  with the Studio (§6).
- **Images:** icon, name label and portraits are generated from the model;
  "Regenerate preview".

### 5.3 By hand (console)
```powershell
python awo_tools/sbport.py --lista --juego sb2                       # 3-letter codes
python "mod center hd/importar.py" lista sb2                          # what the launcher sees
python "mod center hd/importar.py" importar sb2 GHF --mod imp_sb2_future_gohan --nombre "Future Gohan" --mods <mods folder>
python "mod center hd/roster_build.py" construir --mods <mods folder>    # or press PLAY
```
To test without touching your mods, use a separate folder with `--mods`
(`construir` rewrites the `_roster` of the folder you pass it).

### 5.4 What to check in game
Normal hits and damage; P+K+G with 3/4/5/6 bars; back to normal with less
than 1 bar; the pause sheet ("With over N Ki gauges"); specials and the
ultimate; the belt at rest and when walking; the toon shading and the HD rim
light at 0 % and 100 %.

---

## 6. TECHNIQUE CAMERAS (Studio)

User guide: `docs/02_mods/STUDIO_CAMARAS.md`. Format: `docs/03_formatos/CAMARA_ACC.md`.

- **Game character:** the Studio writes
  `mods/studio_<character>/us/data_cmn.afs/<CAM fid>/geom.bin` (LZX `/N:2048`,
  padded to a **reserved** size so it can reload without restarting) and a
  `studio.json` with the edited clips.
- **New character:** rewrites its `moveset/camara.bin` (mounted when PLAY is
  pressed).
- Backups in `mods/<mod>/respaldo/<date>/` (never inside `us/`: the runtime
  serves the first file in the entry's folder).
- Test cycle: save → Pause → "Re-select characters" → use the technique. The
  first time, restart the game.
- Console: `python "mod center hd/studio/studio_core.py" info 0` (Goku's clips
  and scripts), `exportar-glb`, `importar-glb`, `selftest`.

---

## 7. MODS ON PS5

The PS5 build (`docs/PS5.md`) uses the same runtime mod code. Copy ready-made
mod folders to `/data/dbz3/mods/` on the console (FTP), with the same layout
(`<mod>/us/data_cmn.afs/<entry>/geom.bin`, `.disabled` to turn one off), or
pass `--with-mods` to `ps5/make_ps5.sh` to upload this repository's `mods/`.
There is no launcher on PS5, so mods are built on a PC. For new characters,
let the PC launcher build the generated `_roster` mod (press PLAY once, or run
`roster_build.py construir`) and copy the whole `mods/` folder; the PS5 host
applies it at launch on the **US** build only (like the PC single-EU core,
the EU build has no roster extensions).
