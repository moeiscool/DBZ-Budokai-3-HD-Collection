# Future Gohan's transformations (Shin Budokai: Another Road port) in B3 HD

Date: 2026-10-06. Exploration and RE only. No project file was touched and the game was not opened.
Scripts and dumps: in this folder. Large extractions: the exploration work folder (`04_transformaciones\`).

## 0. Summary

- **The user is right, with a nuance.** In *Another Road*, Future Gohan (code `GHF`) has 4 forms: Normal, Super Saiyan, Super Saiyan 2 and Potential Unleashed. The parameters of those forms are identical to those of Adult Gohan in the same ISO.
  - **The nuance:** in the current port those 4 forms are **4 costumes**, not transformations. The bone names prove it: `traje1` = `NOR_FACE`, `traje2` and `traje3` = `SS_FACE`, `traje4` = `SENZAI_FACE`. In addition the port has `formas = 1`.
  - That is why "SSJ" can be chosen on the select, but in battle he always fights in form 0 and cannot transform.
- **In B3 transforming does not spend ki.** It requires **having at least N bars**: the capsule stores N×10 in byte +15. With less than **1 bar (1000 units)**, if you get hit you go back to the normal form.
  - P+K+G jumps straight to the highest form for which you have ki and capsules.
  - Each form has its own "base ki level".
- **Adult Gohan (ID 4) in B3:**

  | Form | Requirement | Requires | Base ki level |
  |---|---|---|---|
  | Super Saiyan | ≥ 4 bars | — | 3 → 4 |
  | Super Saiyan 2 | ≥ 5 bars | SSJ | 4 |
  | Ultimate («Elder Kai Unlock Ability») | ≥ 6 bars | SSJ2 | 5 (own moveset) |

- **Proposal for Future Gohan:** the same 3 transformations and the same figures (4 / 5 / 6), with his own AR models (B00–B03).
- **What remains to be built:**
  1. The P+K+G input (code 0x2E0/0x3E0) in his BCM.
  2. The two animations of those codes, grafted from the donor.
  3. The ki requirement per capsule: today every new transformation asks for 5 bars and the card says 3.
  4. The model per form, to use his own SSJ2.
  5. The mod configuration: `formas = 4`, 3 capsules and 1 costume with 4 models.

## 1. How B3 HD encodes transformations (RE with evidence)

### 1.1 Command input (BCM / `#CCM` of the camera bin)

The 17 characters with forms have a single start entry to transform:
`w0=0 w1=7 (P+K+G) w5=0x0004 (transform) w6=1 w8=0 (no capsule) w9=0 (no ki) w12..14 = 0x2E0 / 0x3E0 / 0x3E0`.

- Example, Adult Gohan (cam 231): `0000 0007 0000 0000 0000 0004 0001 0000 0000 0000 0000 0000 02e0 03e0 03e0 0000`.
- The entry carries neither a cost nor a target form: the game's code decides (§1.5).
- Script: `bcm_dump.py 4 3 2 0 7 8 9`.

### 1.2 Animation (`#CSK` of the ANM)

- Adult Gohan's block 0x2E0 (data_cmn 234) uses animation 14 of the **global store (pool 0)**, which is common to everyone. It carries 3 AP lines.
- Those lines include the BSP effect `0x64` (transformation flash) and the yell (k3 = slot of the `lang_*` bank). This was already documented in `b1port`: "k0:0x64 + k3:0x29".
- Since the animation is global, grafting 0x2E0/0x3E0 from the donor needs no AMM.

### 1.3 Battle record per form (`char372` 0x82329CF0 + 372·ID, +0xD0 = number of forms, +212 + 20·f)

| Offset | Type | Meaning | Evidence |
|---|---|---|---|
| +0 | u16 | capsule the form requires | `sub_82119108` (lha 0(r29)) |
| +2 | u16 | ID whose `char96` provides the model | `sub_820F9970` |
| +4 | u16 | index into `char96.formas[]` of the +2 ID (and into the ANM: `anm[f]`) | `sub_820F9970`: reads `char96 + 16 + 8·(ID·12 + idx)` |
| +6 | u8 | type: 01 normal (reversible, there are more), 05 irreversible, 06 last (reversible), 07 special/automatic (Majin, ship), 08 another character's form | `sub_82119108` (≠6 to go up; the next 0/7/8 cuts) and `sub_82119258` (when reverting it stops at 3/4/5/7) |
| +7 | u8 | bit 0: "Saiyan" transformation routine (1 in Kaioken/SSJ; 0 in Ultimate, Freeza, Cell…) | `sub_820FB5D0` chooses handler 0x820FA940 or 0x820FA7D8 |
| +8 | u8 | power parameter (0/10/15/30 in Gohan). **Unconfirmed** (damage bonus?) | SB has it the same (BTLPARAM) |
| +9 | u8 | **base ki level in bars** | `sub_82100760`: `+221 × 1000` |
| +10, +12 | u16 | 300/360/420 and 100/150/200, grow with the form. **Unconfirmed** | constant in SB (300/100) |
| +16 | ptr | the character's physics table (floats, the same in all its forms) | `sub_820F9970` → +1380 |

### 1.4 `char96` forms (0x8234ABB8 + 96·ID, +16 + 8·idx)

Each entry is `u16 ID`, `u8 model within the costume`, `u8 mouth`, `u8 ?`, `u8 aura` (3 = form aura, 4 = with SSJ2-style sparks).

- Adult Gohan: `(4, m0, 0)`, `(4, m1, 3)`, `(4, m1, 4)`, `(4, m2, 0)`. That is, **SSJ2 reuses the SSJ model and only adds the sparks**, and the Ultimate uses model 2 (227/230).

### 1.5 Logic in the recompiled code (`generated/`)

**`sub_82119108`: which form do I go up to?**
- If the current form is of type 6, it does not go up.
- Otherwise it walks k = current+1… and checks three things for each form:
  1. that the form is active (byte `fighter+8156+k`: capsule equipped);
  2. that the capsule's +14 mask includes the current form;
  3. that there is **ki ≥ (+15)·100**, asked of `sub_82115518(fighter, ki, 2)`. With flag 2 **it only checks and does not spend**.
- It keeps going up while it can and stays on the last form that qualifies.
- At the end it applies a battle cap (`fighter+7412`, +24 = maximum form).

**`sub_82119258`: reverting.**
- If ki is ≥ **1000.0** (constant 0x8201B3F0 = 1 bar), it does not revert.
- If less, it goes down form by form until the first of type 3/4/5/7, or to form 0. In practice: **SSJ / SSJ2 / Ultimate go back to the normal form at once**.
- There is a minimum cap (+22).

**`sub_82100760`: base ki level.**
- Returns `+9 × 1000` of the current form.
- **`sub_82116458`:** with each hit, the attacker gains `200 + 5·min(combo,5)·(9 − base level)`. Transformed (higher base level), he gains a little less ki per hit.

**Units:** 1 bar = 1000; B3's maximum is 7 bars (SSJ4 asks for "7 Ki Gauges").

### 1.6 Capsule (`#SKC` data_usi 4, 40 B per record)

| Offset | Meaning |
|---|---|
| +8 | class 0x11 |
| +10 | rarity (price 3,000 / 6,000 / 10,000 Z) |
| +14 | **mask of the forms from which it can be used** (SSJ 0x01, SSJ2 0x03, Ultimate 0x07) |
| +15 | **ki requirement ×10** (40 / 50 / 60) |
| +16 and +18 | u16, capsule required to be able to equip it. The game checks both: `sub_821B79F8` and `sub_8214CA30` |

- Byte +15 matches the official text «With N or more Ki Gauges» in 30 of 34 capsules (OCR of `modding resources`).
- The 4 that do not match are Piccolo's (57: data 4 / text 3; 58: 5 / 4), Dabura's (4 / 3) and Cooler's (5 / 4). The data wins: it is what the code uses. The PS2 GH has the same values.

### 1.7 Gohan in B3 (the reference)

Full table of the 17 characters in `evid_tabla_b3.md`. "Requires" = capsule that must be equipped beforehand.

| ID | Form | Capsule | Requirement | From | Requires | Base level | Type | Model (costume 1/2) | Aura | Moveset |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 Adult Gohan | Normal | — | — | — | — | 3 | 01 | 225 / 228 | — | 234 |
| | Super Saiyan | 23 (Rare, 6,000 Z) | **≥4** | 0 | — | 4 | 01 | 226 / 229 | 3 | 234 |
| | Super Saiyan 2 | 24 (Rare) | **≥5** | 0–1 | 23 | 4 | 01 | 226 / 229 (the SSJ's) | 4 (sparks) | 234 |
| | Ultimate «Elder Kai Unlock Ability» | 25 (Special, 10,000 Z, not tradeable) | **≥6** | 0–2 | 24 | 5 | 06 | 227 / 230 | — | **233 own** |
| 3 Teen Gohan | Super Saiyan | 18 | ≥4 | 0 | — | 4 | 01 | m1 | 3 | 245 |
| | Super Saiyan 2 | 19 | ≥5 | 0–1 | 18 | 4 | 06 | m2 (own) | 4 | **244 own** |
| 2 Kid Gohan | Unlock Potential | 16 | ≥3 | 0 | — | 4 | 06 | m0 | — | 251 |
| 0 Goku | Kaioken / SSJ / SSJ2 / SSJ3 / SSJ4 | 1–5 | 2 / 4 / 5 / 6 / 7 | — | chain | 3 / 4 / 4 / 5 / 6 | — | — | — | — |

Other per-form parameters of Adult Gohan (unconfirmed fields): +8 = 0 / 10 / 15 / 30; +10 = 300 / 360 / 420 / 420; +12 = 100 / 100 / 150 / 200.

Official text of Gohan's transformations: «(Does not consume Ki Gauge when transformed)» and «Transformation is reversed if damage is taken with less than 1 full Ki Gauge!».

## 2. What Shin Budokai and Another Road have (ISOs read in place with `iso.py`)

### 2.1 Who transforms in each game

- **Shin Budokai 1** (ULUS-10081, 18 characters): no Future Gohan.
  - Adult Gohan `GHL`: Normal, SSJ, SSJ2 and Potential Unleashed.
  - Teen Gohan `GHM`: Normal, SSJ and SSJ2.
  - Table in the ELF (`SB1_BOOT.elf` 0x142578, 24 B records).
- **Another Road** (24 characters): `BTLPARAM.DAT` (24 × 96 B) and the ELF record (`AR_BOOT.elf` 0x1B55F8 + 0x108·i). Dump in `evid_ar_formas.txt`.

| Character | Forms | (power, base level) per form | Type per form |
|---|---|---|---|
| **GHF Future Gohan (18)** | **4** | (0,3) (10,4) (20,4) (30,5) | 1, 1, 1, 2 |
| GHL Adult Gohan (2) | 4 | (0,3) (10,4) (20,4) (30,5) | 1, 1, 1, 2 |
| GHM Teen Gohan (1) | 3 | (0,3) (10,4) (20,4) | 1, 1, 1 |

GHF is an exact copy of GHL. His base levels (3 / 4 / 4 / 5) are the same as Adult Gohan's in B3. Only the SSJ2's power changes: 20 in SB, 15 in B3.

### 2.2 Files of `data_btl_cmn.afs` (AR)

| File | Content |
|---|---|
| `BCGHF.amb` | base moveset |
| `BCGHFB00`–`B03` | models: `Bnn` = form nn (like `BCGHMB02` = Teen Gohan's `SS2_FACE` face) |
| `BCGHFM1.amb` | the base moveset plus a 2nd `#BSK` that **only redefines code 0x19F**: one animation, no hits. GHL M3 redefines 0, 1 and 0x19F; GHM M2 redefines the stance |
| `BAR_GHF` | aura |
| `BSP_GHF` | techniques |

Detail of each model (`evid_ar_ghf_mallas.txt`, `tex_*.png`, `pelo_formas.png`):

| Model | Form | Face (bone) | Hair | Notes |
|---|---|---|---|---|
| B00 | Normal | `NOR_FACE` | black | |
| B01 | SSJ | `SS_FACE` | golden (255,224,2), green eyes | |
| B02 | SSJ2 | `SS_FACE` | golden, different hair mesh (668 vertices versus 726) | Same tone as the SSJ (Teen Gohan's SSJ2 is darker: 234,189,1) |
| B03 | Potential Unleashed | `SENZAI_FACE` («潜在») | black | Left-hand variant `GHF_L22_LHAND` with the **Z Sword**: 175 vertices, texture 3, the same as Ultimate Gohan's `BCGHLB03`. Only visible if an animation asks for hand 22 |

### 2.3 How one transforms in SB

There is a single entry in its BCM: `w0=0x20` + E, cost **0x0FA0 (4000)**, codes 0x500/0x700. Everyone who transforms has it; Android 18 and Bardock do not.

- That entry **is still inside the port's `camara.bin`** (block `0x172c`).
- B3 never uses `w0=0x10/0x20` in its 38 movesets (`w0` is only 0, 1 or 2). It must be checked in game whether that entry can be triggered. If it is triggered, it would play SB's animation and spend 4 bars without changing form.
- The port's SB ultimates also use `w0=0x10` and the port **has no hyper mode** (`bcm_summary`: `hiper = False`). That is another pending item, not part of this topic.

### 2.4 State of the port (`out/build/win-amd64-release/mods/port_gohan_futuro`)

- 4 costumes, which are the 4 forms (verified by the bone names).
- Moveset = SB's `BCGHF`, via the community port `ghf_365/367`, which is byte for byte SB's BCM.
- `formas = 1`, `capsulas_forma = [0]`, `habilidades_transformaciones = []`.
- The CSK has 0x3E0 (an SB hit the BCM does not use: dead data) and no 0x2E0.

## 3. Proposal of forms and ki

**Recommended: «Another Road + B3's Adult Gohan rules».** His AR data are Adult Gohan's; B3 already has those rules balanced; and his own models exist for the 4 forms.

| Form | Model | New capsule (name) | Requirement (does not spend) | Usable from | Requires | Base level | Aura | Moveset |
|---|---|---|---|---|---|---|---|---|
| 0 Normal | BCGHFB00 (costume1) | — | — | — | — | 3 | — | SB base |
| 1 Super Saiyan | BCGHFB01 (costume2) | «Super Saiyan» (Rare) | **≥4 bars** | form 0 | — | 4 | 3 | same |
| 2 Super Saiyan 2 | BCGHFB02 (costume3) | «Super Saiyan 2» (Rare) | **≥5 bars** | forms 0–1 | SSJ | 4 | 4 (sparks) | same |
| 3 Potential Unleashed | BCGHFB03 (costume4) | «Potential Unleashed» (Special) | **≥6 bars** | forms 0–2 | SSJ2 | 5 | — | same |

- **Reverting:** hit taken with less than 1 bar → back to Normal. Potential Unleashed is of type 06 (last form, reversible), like Adult Gohan's. In SB it is of type 2 (last). It is not known whether it is permanent in SB.
- **Name of Potential Unleashed:** «Elder Kai Unlock Ability» does not fit the character, because in the future there is no Elder Kai. Better «Potential Unleashed» or «Hidden Potential».
- **"Canon" alternative:** only Normal + SSJ (≥4). It is what the anime and manga show: Future Gohan did not reach SSJ2. B02 and B03 are lost.
- **"Without his own SSJ2" variant:** SSJ2 = the SSJ model + sparks, as Adult Gohan does in B3. It needs no runtime changes.
- **If transforming should cost ki** (not how B3 works): the transformation code only checks. `w5 |= 0x0001` + `w9 = 4000` in the P+K+G entry would have to be tried. Not verified and I do not recommend it.

### What each form needs

| Need | Source |
|---|---|
| Model | All 4 already exist converted (costume1–4). Nothing to derive. |
| Moveset | The same for all 4 (SB's M1 only changes 1 animation). `anm = [base]` → forms 1–3 fall back to form 0's, like Adult Gohan's SSJ. |
| Transformation animation | Graft of 0x2E0/0x3E0 from donor 4 (global animation + AP). |
| Effect | `0x64` from the donor's BSP (the port uses Adult Gohan's BSP, because `tecnicas` is commented out). |
| Yell | k3 of the donor's `lang` bank (B3 Adult Gohan's voice) until AR's voices are ported (`ZP2GHF*`, ATRAC3plus). |
| Aura | The donor's aura table (`aura`, 18), with the SSJ2 sparks via `char96` aura 4. |
| Health-bar faces | 4 faces, rendered from B00–B03. |
| Skills card | 3 transformation rows with «With over N Ki gauges». |
| If a form without a model is ever requested | Recolour the hair (like B01 → dark SSJ2 234,189,1) + aura 4. Not needed today. |

## 4. roster_build today and what is missing

**Already works:**
- `formas = N`: the runtime can only **reduce** the donor's forms; donor 4 has 4.
- Copying the donor's `char372` and `char96`. That inherits base levels, types (reversion), aura per form, the physics table and `+7`.
- `[[capsula]] tipo = "transformacion" forma = k`:
  - creates the capsule (ID ≥ 596) with mask `(1 << forma) − 1` and "requires the previous one";
  - generates `capsulas_forma` and the card (SCM) with the donor's `0xFFFFFFFF` rows;
  - does not inherit the donor's 23/24/25 if the moveset is its own.
- `moveset = [...]` per form (`anm[f]`; missing ones = `0xFFFFFFFF` → form 0).
- The health-bar face per form, from the models.

**Missing or wrong:**
1. **Ki requirement per capsule.** Today the template of every transformation is 140 (Broly's LSSJ, +15 = 50), so **every new transformation asks for 5 bars** (Zarbon's Monster Form record, 608, confirms it). In addition the card and the panel say 3, because `capsulas.KI` is empty outside IW.
   - Fix: key `ki = N` → `rec[15] = 10·N` and `KI[id] = N`. Even better: use as the template the donor's native capsule for that form (23/24/25), which brings the correct rarity, mask and +15.
2. **P+K+G entry in the port's BCM**: it does not exist.
   - Fix: a new function in `capsulas.py` that copies the donor's entry (`w1=7`, `w5=4`, 0x2E0/0x3E0/0x3E0) when `formas > 1` and the BCM lacks it, and that nulls SB's (`w0=0x20`, 0x500/0x700, 4000).
3. **Graft in the ANM** of the donor's 0x2E0/0x3E0 blocks: `capsulas.csk_graft` already exists and is used for hyper mode. The port's 0x3E0 is dead data (neither the BCM nor the SPX uses it), so it can be overwritten.
4. **Model per form** (only to use his own SSJ2, B02):
   - New key `modelo_forma = [0,1,2,3]`, with `modelos_por_traje = 4`.
   - In the runtime: write `c96 + 16 + 8·f + 2` after copying the donor's forms (~3 lines in `ApplyCharacter`).
   - In the builder: emit it and use it in `hud_images`. Today it uses `hds[min(f, per−1)]`, which with the donor's map [0,1,1,2] would give the wrong faces.
   - Without this key, the runtime-free variant is `modelos = [B00, B01, B03]` + `modelos_por_traje = 3`, but the builder still needs that map for the faces (or `ui/hud_1..4.png`).
5. `make_record` writes the required capsule as a u32 at +16 (it ends at +18). **It works**, because the game checks +16 and +18, but it is not like the native records.
6. Mod: `formas = 4`, 1 costume with 4 models and 3 transformation `[[capsula]]` with name and `ki`.

### Plan

1. `capsulas.py`:
   - `add_b3_transform(ccm, donor_ccm)`, which copies the P+K+G entry and removes SB's;
   - transformation template = the donor's capsule for that form;
   - `ki` key.
2. `roster_build.py`:
   - apply step 1 if `formas > 1` and the entry is missing;
   - graft 0x2E0/0x3E0 from the donor's ANM (`csk_graft`);
   - `modelo_forma` (roster.toml + health-bar faces).
3. `src/roster_ext.cpp`: read `modelo_forma`. Afterwards, rebuild the exe and **re-copy the canonical DLLs** (the trap in §4 / §7 of AGENTS.md).
4. The port's `personaje.toml`:
   - `modelos = [traje1..4]`, `modelos_por_traje = 4`, `modelo_forma = [0,1,2,3]`, `formas = 4`;
   - 3 `[[capsula]]` with `tipo = "transformacion"`, `forma = 1/2/3` and `ki = 4/5/6`.
5. `roster_build.py construir --force` + `deep.py` / `verify_final.py`. Check in the generated roster:
   - `capsulas_forma = [0, a, b, c]`;
   - byte +15 = 40/50/60 in the records;
   - the P+K+G entry present;
   - 0x2E0/0x3E0 present in the CSK.

**Effort:** ~½–1 day of tools + 1 in-game test session. If his own SSJ2 is dropped, there is no C++ change (Python only).

### Risks

- **SB's "↑E" animation** (0x500/0x700) still in the BCM: it must be removed, or it may spend ki without transforming.
- **Yell and voice** of the transformation: they will be B3 Adult Gohan's until AR's voices are ported (ATRAC3plus).
- **Own BSP:** if in the future the port uses its own SB BSP (`tecnicas.bin`), the AP line of effect `0x64` will launch the wrong effect. Precedent: Zarbon, `--quitar-efecto 64`.
- **Capsule IDs:** they are renumbered (596+, by mod order). The «Custom» lists saved in `mods/capsulas_custom.txt` may end up shifted.
- **Costumes:** going from 4 costumes to 1 changes the select. The runtime pads up to 8 costumes repeating the first, so it should not crash.
- **Z Sword:** it only appears if an SB animation asks for left hand 22.
- **Side bug** (another topic): `ApplyExtraCostume` uses `char372 +4` as the «model within the costume», but that field is the index into `char96.formas[]`. With Adult Gohan the extra costume works by chance (the last write wins); with other characters it may not work.
- **Hyper mode (P+K+G+E):** it does not exist in the port. It does not clash with P+K+G, but it is still pending.

## 5. In-game validation (when the user is not using the PC)

1. Select: 1 Future Gohan costume, with the Normal model.
2. Edit Skills: the 3 capsules appear and it does not allow equipping SSJ2 without SSJ (or Potential without SSJ2).
3. Battle, P+K+G:
   - with 3 bars, nothing happens;
   - with 4, he goes to SSJ (B01 hair, golden aura, face 2, yell);
   - with 5 from Normal, he goes **straight** to SSJ2 (sparks, B02 hair);
   - with 6, he goes to Potential (black hair).
4. Taking a hit with less than 1 bar → back to Normal.
5. Standing still in SSJ, ki tends to 4 bars; in Potential, to 5.
6. Pause → skill list: «With over 4/5/6 Ki gauges», no «3».
7. Combos, blasts, specials and the ultimate work in the 4 forms, and there is no crash when changing model.
8. The CPU with Future Gohan also transforms.
9. SB's "↑+E" no longer exists.
10. The save and the «Custom» list are saved and loaded correctly.

## 6. Open questions

- Faithful to Another Road (4 forms, recommended) or canon (SSJ only)?
- SSJ2 with its own model (B02, needs runtime) or as in B3 (SSJ model + sparks, Python only)?
- Name of the 3rd capsule: «Potential Unleashed» or «Hidden Potential».
- Keep 4 costumes in addition to the forms? (Not recommended: AR has no alternate costumes.)
- Port AR's voices (ATRAC3plus) now for the transformation yell, or wait?
- Fields +8 / +10 / +12 of the per-form record: their exact effect in battle is not confirmed (they are inherited from the donor).

## 7. Evidence (this folder)

| File | Content |
|---|---|
| `evid_tabla_b3.md` | The 17 native transformations: requirement, mask, requires, base level, type, model, aura |
| `evid_char372_formas.txt`, `evid_char96_formas.txt` | Dumps of the US image (`out/analysis/guest_image/dbz3_us_image.bin`) |
| `evid_skc_transformaciones.txt`, `skills_ocr.json`, `b3_caps.json` | Capsule catalogue, official texts (OCR) and PAL sheet |
| `evid_funciones_ppc.txt` | `sub_82119108`, `sub_82119258`, `sub_82100760`, `sub_820FB5D0`, `sub_820F9970` |
| `evid_ar_formas.txt`, `ar_btl_cmn.txt`, `sb1_btl_cmn.txt` | Form tables and SB AFS listings |
| `evid_ar_ghf_mallas.txt`, `tex_BCGH*.png`, `pelo_formas.png` | Meshes, textures and hair of each form |
| `bcm_dump.py`, `forms.py`, `c96.py`, `skc.py`, `tabla_b3.py`, `fn.py`, `scan*.py`, `psp_afs.py`, `sb_bcm.py`, `psp_tex.py`, `psp_mesh.py`, `psp_hair.py`, `ar_formas.py` | Scripts (read-only) |
| `04_transformaciones\ar\` in the exploration work folder, and `AR_BOOT.elf` / `SB1_BOOT.elf` | Large extractions from the ISOs |
