# Inventory of modding resources (4 folders)

> Updated: 2026-08-14. What is in each folder, so work is not duplicated.
> Paths relative to `C:\Users\javie\Desktop\PROYECTOS IA\DBZ Budokai 3 HD Collection\`.

---

## 1. `modding resources/` — BASE (31,629 files, 2.4 GB)

The main resources folder.

| Contents | Use |
|---|---|
| `All Character Models from IW into AMB format/` (241) | **IW→B3 PS2 models** (Janemba, Pikkon, Pan, Super 17...) |
| `Budokai Models/` (569) | Budokai PS2 models |
| `Super Dragon Ball Heroes World Mission/` (30,402) | SDBH WM models (EMD/ESK, a Xenoverse goldmine) |
| `Infinite World to Budokai 3 Moveset Ports/` (70) | IW→B3 moveset ports |
| `EmdFbx-and-FbxEmd-LibXenoverse/` (20) | EMD↔FBX converter (works) |
| `Tail AMO/` (4) | Custom tail models |
| `map swap in b1/` (97) | B1 maps |
| `Budokai 3 Story Art/` (190) | Game art |
| Bin lists (DBZ_B3_Character_Bin_List.txt, etc.) | bin→character mapping |

## 2. `modding resources update/` — INBOX (432 files, 292 MB)

Inbox for new files from the user. Contains DUPLICATES of the base
(All_Character_Slots, Budokai_3_Capsules_IDs, etc.) + `Budokai 1 Models
Converted to AMB/` (230, unique).

## 3. `modding resources update 2/` — TUTORIALS (5,198 files, 694 MB)

The most valuable folder for model swaps (community tutorials):

| Contents | Use |
|---|---|
| `lean bone tutorial/` (4,681) | Rig tools + docs (Budokai Toolset, amo_lgbt.exe) |
| `Tutorial #1 Añadir AMG manualmente/` | **How to add an AMG by hex** (JaromSc) |
| `SLXS Edit Tutorial/` (several) | Adding characters/transformations (SLXS) |
| `MOD EJEMPLO/` (115) | **IW→B3 conversion examples** (complete Ginyu Force) |
| `- Budokai OBJ Editing Tutorial` / `- Tutorial de Edición de OBJ` | Retopology with OBJ |
| `DBZ B3 (X360) - Lesson 1/` | **X360 LZX 512 KB compression (/N:2048)** |
| `DBZ B3HD - Lesson 2 (Texture Edition)/` | HD texture editing (AZT) |
| `Tutorial remove parts of the model whit LGBT` | LGBT method (bodyswap) |
| `SB2 Breakdowns/` | Breakdown of the SB2 format |
| `goku_all_animations_b3_and_iw.txt` | Animation list |
| `INFORME_modding_resources_update_2.md` | Earlier report on this folder |

## 4. `modding resources discord/` — DISCORD DOWNLOADS (384 files, 924 MB)

Resources downloaded from the community:

| Folder | Contents |
|---|---|
| `research/` (245) | **B3_AMB_PS3.bt template** (AWO/AWG format), aerithdevs intermediate format, rig docs |
| `tools/` (58) | **Budokai Modding Tool V1.5** (amo_lgbt, amg_c, axis_e), Zero Devs tutorials |
| `tutorials/` (78) | **LGBT Method**, How_to_combine_model_parts, CREATE_AMG_WITH_2_MODEL |
| `rb2_reference/` (3) | RB2 reference (Raging Blast 2, same Spike SDK) |
| `models/` (0) | Empty |

---

## DUPLICATES FOUND

- `modding resources/` and `modding resources update/` share: bin lists,
  story art, capsule IDs, voice list.
- `modding resources discord/` and `modding resources update 2/` share:
  Zero Devs tutorials, LGBT.

> Nothing has been deleted from modding resources (risk of breaking script
> paths). A future cleanup may consolidate the bin-list txt files into `docs/`
> as a reference, and deduplicate the tutorials.
