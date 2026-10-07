# Report 02 — Shin Budokai techniques → Budokai 3 HD (first target: Future Gohan)

Date: 2026-10-06. Exploration / RE only: no project file was touched and the game was not
launched. Everything read is PS2 GH (LE, same content as the HD in BE), the PSP ISOs read in
place (`iso.py`) and the files of the current port. Scripts and outputs in this folder (list at
the end); large extractions in the exploration work folder (`02_tecnicas\`).

---

## 0. Executive summary

1. **The current Future Gohan port has no working techniques, and it is not (only) because of
   `tecnicas.bin`.** Its moveset (`anm_forma1.bin`) and its camera (`camara.bin`) are the
   "community conversion" `ghf_365/367`, which is really **a byte-for-byte copy of the Shin
   Budokai 2 data** (identical BSK, BCM, SPX; see §2.4). SB2's BSK uses **20 B AP lines** (B3:
   16 B) and 160 B hit blocks (B3: 128 B): B3's engine reads all the animation properties (hits,
   effects, voices, speed) misaligned from the second line onwards. In addition its BCM uses SB
   semantics (cond 0x0004 = close-range special in SB, but **transformation** in B3), it has no
   hyper mode entry (without hyper there is no ultimate in B3), its `#ACC` (cameras) is empty
   and its `#SPX` is SB bytecode (another VM).
2. **`tecnicas.bin` (= `scratchpad/ghf/hd_BSP_GHF.amb`, same SHA-1) is SB2's BSP run through
   `ps2hd` as if it were B3's.** SB2's layers are not B3's: `#AME` is another particle system
   (nodes `Line/Sprite/Plane/Model/Gravity/Vortex…` versus B3's `Emitter/Particle/Field`, 0x40
   header versus 0x10), `#ASE` has 0xB0 blocks (B3 0xD0) and SB numbers its beams with codes
   that are **reserved** in B3 (0x15E/0x15F = the look of ki blasts). Commenting it out was
   right; there is no written note of why, but the data explain it (§2.5).
3. **GHF's real technique list (SB2 Another Road data):** 6 specials + 2 ultimates, each gated
   by a "booster" (SB's equivalent of the capsule). Kamehameha (blue beam >E), energy ball
   (>E), close-range special (<E), short-range explosion (>E), projectile (<E), hit + ball (<E);
   ultimates: a giant blue beam (exact twin of Adult Gohan's Super Kamehameha in SB2) and a
   type-12 magenta wave. SB2's names are textures, not text: the exact names are still to be
   confirmed (§2.3).
4. **In B3 a technique = BCM (input/capsule) → BSK (animation + AP1 hit + AP7 effects) → BSP
   (`#AST` energy / `#ASE` visual effect / `#AME` particles / textures) and, only for ultimates
   and grabs, SPX (cinematic) + `#ACC` (camera).** New findings with evidence over the 38
   characters: a **technique's ki cost and forms live in the capsule** (`#SKC` +15 = ki in
   tenths of a bar, 169/191 match; +14 = form mask), not in the BCM; the **beam struggle** is
   marked by bit **0x2000** of the BCM condition + the AP7 line `c0=0x68`, and every character
   with a beam has a **response entry** (cond2 bit 0x4000, `c0=0x69`) (35/38 match); **every B3
   ultimate is P+K+G+E in hyper mode → a hit with HR type 3 → SPX slot 0** (2nd ultimate → slot
   1), with its animations at codes **0x4A0+**; slot 20 is the grab (P+G).
5. **Viable with a hybrid approach**: convert what is compatible (BCM, BSK, `#AST`, `#ASE`,
   textures, animations) and **rebuild on the B3 donor** (Adult Gohan, ID 4) what is not
   (`#AME` particles, the ultimate's SPX cinematic + camera, beam struggle and hyper mode
   entries). Almost everything can be automated; the craft part is choosing/recolouring the
   particles and assembling the ultimate's cinematic. Estimated effort: 6–9 sessions + 3 rounds
   of in-game testing.

---

## 1. How B3 HD defines a technique, end to end

### 1.1 The chain

```
Capsule (#SKC, data_usi 4)  ── ki (+15), forms (+14), required capsule (+16 u16), class (+8)
   │  (id in the BCM block, w8)
BCM (#BCM/#CCM, CAM bin)    ── buttons, direction, condition (w4 on PS2 / w5 in HD), cond2 (w6),
   │                           ground/air attack codes (w12..w15)
BSK (#BSK/#CSK, ANM bin)    ── code → 48 B sub-block: animation (store 3 = own AMM)
   │                           + AP0..AP7 (16 B lines)
   ├─ AP1: hit window → HR code → HR block (8×16 B: damage, type, stun)
   │        HR type 3 → SPX script (slot = code)            → #SPX + #ACC (camera) of the CAM bin
   └─ AP7 [frame u16][id u8][act u8][category u32][value u32]:
        c0 = engine action      (0/1 ki blast, 0x32–0x38 charges, 0x64/0x66 freeze/unfreeze,
                                 0x68/0x69 beam struggle; probable: 0x46/0x47 beam start/end,
                                 0x28 transform — according to the IW community note and the data)
        c1 = sound, c2/c3 = voice (yell bank slot), c5/c6 = hit/ground effects
        c4 = link to the BSP: code of an #AST (energy) or of an #ASE (visual effect)
BSP (data_cmn 504–555; table by ID 0x82333208; `tecnicas =` in personaje.toml)
   ├─ AMB[0] = #AST ("wk" blocks 0xF0: type, code, duration, speed, bone, beam textures,
   │            damage, radius, stun, forms) + small #AMT + #AME
   ├─ AMB[1] = #ASE (0xD0 blocks: start/middle/end codes, bone, link to #AME, forms)
   │            + #AME (+ #AWV)
   └─ rest: large #AMT (effect textures), #AME, #AMO (+#AMM) effect models, #ATR, #AWV
```

### 1.2 Adult Gohan (ID 4: CAM 231, ANM 234, BSP 528) — `gohan_adulto_b3.txt`

| Technique | Capsule (ki, forms) | BCM | Codes | What it does (AP7 / HR) |
|---|---|---|---|---|
| Kamehameha | 26 (10 = 1 bar, 0x0F) | >E, cond **0x2002**, cond2 1 | 0x24B/0x34B (+ 0x24C, 0x24D after combo) | c0 0x64 freezes f8 · c4 0x04/0x05 charge (ASE wk0) · c4 0x10 · **c0 0x68 f34** · c0 0x66 f35 · **c4 0x0 = AST wk0** (beam, 250 damage) f46 · c0 0x46/0x47 |
| Kamehameha (response) | 26 | >E, cond 0x0002, **cond2 0x4003** | 0x26C | same but without 0x64/0x66, **c0 0x69** instead of 0x68, + c0 0x40/0x43 |
| Soaring Dragon Strike | 27 (20 = 2 bars, 0x0F) | <E, cond 0x0002 | 0x24E (+0x24F/0x250) | 5 AP1 hits (80/30/90/100/110, the last type 2 = launches) · c4 0x24, 0x2C–0x30 (ASE) · c4 0x131 |
| Hyper mode | — | P+K+G+E, cond 0x0400 | 0x259 | c7 0x4, c8 0x72 (probable camera), c0 0x64, c4 0x12C, c0 0x2C, c0 0x66 |
| Super Kamehameha (ultimate) | 28 (50 = 5 bars, 0x0E = not in base form, requires 23 SSJ) | P+K+G+E, cond **0x000A**, cond2 0x8001 | 0x25A | rush; AP1 f30 HR 0x68 → **type 3, code 0 = SPX slot 0** |
| Grab | — | P+G | 0x258 | AP1 HR 0xD0 → type 3, code 0x14 = **SPX slot 20** (common routine, BASE 0x480) |

Teen Gohan (ID 3) follows the same pattern (`gohan_teen_b3.txt`): Kamehameha capsule 20 (0x24A,
response 0x250), Soaring Dragon 21, Father-Son Kamehameha 22 (slot 0, anims 0x4A0–0x4B6).

### 1.3 Ki and forms: in the capsule, not in the BCM

In B3 the specials have **w9 (ki) = 0** in the BCM (only the ki blasts have ki there:
350/375/400/425). The cost is in the `#SKC` record:

```
capsule 26 Kamehameha     class 0x21 forms 0x0f ki 10 (1 bar)
capsule 27 Soaring Dragon class 0x21 forms 0x0f ki 20 (2 bars)
capsule 28 Super Kameh.   class 0x21 forms 0x0e ki 50 (5 bars) requires 0x17 (SSJ)
capsule 21/22 (Teen Gohan) forms 0x04 = "SSJ2 only"  ← matches the "Unusable without SSJ2" card
```

`skc_ki_check.py`: in **169 of 191** capsules with the text "Consumes N Ki / N or more Ki", byte
+15 is exactly 10·N (the 22 misses are OCR errors or fusions). It corrects
`docs/03_formatos/CAPSULAS_B3.md` (+15 is not "cost/level" but ki; +16 is u16). The new
`roster_build` capsules copy the template (special = 13 → ki 10; ultimate = 10 → ki 50), which
coincidentally matches SB (1000 / 5000 ki → 10 / 50).

### 1.4 Beam struggle (also answers the Discord request to be able to disable it)

`beam_struggle_censo.txt` over the 38 characters with a BSP:
- The BCM entries with **bit 0x2000** in the condition are exactly the codes whose AP7 carries
  **`c0 = 0x68`** (35/38 characters; exceptions: Teen Gohan in a finisher, Buu M uses 0x2000
  for something else, Omega Shenron has 0x68 without the bit).
- Every character with a beam special has **one** extra "response" entry with **cond2 bit
  0x4000** (0x4003), same capsule and buttons, whose AP7 does not freeze the screen and carries
  **`c0 = 0x69`** (+ 0x40 / 0x43).
- Hypothesis (to validate in game): 0x68 opens the clash window during the freeze; the 0x4000
  entry is the counter-beam that enters the struggle. Removing the cond2 0x4000 entries (or the
  0x68 lines) should disable the clashes.

### 1.5 Ultimates: always an SPX cinematic

`definitivos_b3.txt`: B3's 32 ultimates (29 characters) are **P+K+G+E (0x0F), cond 0x000A**
(0x001A if they depend on the form), their hit has HR **type 3 → SPX slot 0** (Vegeta and Buu
M: 2nd/3rd ultimate in slots 1/2). The cinematic's animations are blocks **without AP** at codes
**0x4A0+** (Adult Gohan 16, Teen Gohan 23, Goku 23): the SPX script pushes them (`08 20 a0 04`,
`08 20 b0 04`) and carries the camera (the CAM bin's `#ACC`, 26 cameras in Adult Gohan), damage
and effects. Slot 20 = grab (BASE 0x480: codes 0x480/0x481/0x488/0x489).
**Correction** of earlier notes (`b1port`, memory): slot 0 is not "the hyper mode rush" but the
ultimate (whose start is the Dragon Rush-like chase), and 0x4A0–0x4BB are not "throws" but the
animations of the ultimate's cinematic.

### 1.6 The BSP and its reserved codes (`bsp_censo_b3.txt`)

- `#AST` types used in B3: 0 beam (57), 1 ball (22), 11 (17), 3 projectile (6), 2 barrier (4),
  12 (Kaio-shin), 4–15 individually. SB's type 12 exists in B3.
- **AST 0x15E / 0x15F = the look of ki blasts** (beam, damage 0, radius 0.7, bones 15/14 =
  hands) in Goku, Kid/Teen Gohan, Goten, Vegeta, Trunks, Piccolo, Ginyu, 17, Buu… The engine
  uses them with `c0 = 0/1` (blast). That is why Zarbon "fired Broly's ki blasts".
- ASE 0x67/0x68/0x69/0xC8 are in 20/38 BSPs (they link to #AME of the main AMB 0x0E–0x10); ASE
  0x64 in 12. They should be **inherited from the donor**.
- AP7 categories: the link to the BSP is **category 4** (confirmed with the community note
  "Special effects breakdown" and with the data). Category 0 is engine actions; `b1port`'s
  `--quitar-efecto 64` removes the freeze (0x64), not a BSP effect.

---

## 2. Shin Budokai: where the techniques are and what the community conversion did

### 2.1 Files (SB2 Another Road, `data_btl_cmn.afs`, with names)

`BCGHF.amb` (= CAM+ANM together: empty `#AMC`, `#SPX`, `#BCM`, `#BSK`, 3 `#AMM`), `BCGHFM1.amb`
(SSJ form, same BCM, extra BSK), `BCGHFB00–03.amb` (models), `BAR_GHF.amb` (aura),
`BSP_GHF.amb` (techniques), `AC_GHF.spx` (arcade mode, not techniques). Battle texts in
`data_btl_us.afs` (`MSG_CMTGHF.ms` = victory quotes; technique names = textures).

### 2.2 Measured format differences (B3 ↔ SB2)

| Layer | B3 | SB2 | Conversion |
|---|---|---|---|
| BCM | 64 B block; codes 0x2xx/0x3xx; specials' ki in the capsule; cond 0x0004 = transform | same block; codes **0x4xx/0x6xx**; w9 = 1000/5000; w8 = **booster**; cond **0x0004 = close-range special**; ultimates **^E** cond 0x0008; no hyper mode | by rules (§3) |
| BSK | 48 B sub-block; **16 B AP lines**; HR 8×16 B | same 48 B sub-block; **20 B AP lines** (1373/1373 gaps measured); HR 8×20 B | drop the 4 B tail; AP1 with s16 hitbox (SB) → s8 (B3) (`bsk_oracle_ghl.txt`) |
| SPX | header `20/74/15`, embedded common library, slots 0/20 | header `20/1B4/65` (101 slots), without the library, another VM; ultimates and specials **without** SPX (only grab = 20 and 0/1 of common mechanics) | cannot be converted: the donor's is used |
| `#AST` | 0xF0 | 0xF0, **same fields** (`ast_b3_vs_sb2_kamehameha.txt`); SB adds a 2nd damage (+0xCA) and +0xEC | copy + renumber the code + relink AME/AMT |
| `#ASE` | 0xD0; bone +0x80; forms +0xAA | **0xB0**; bone +0x48; forms +0x9E; codes +0x6A same | remap by oracle (`ase_oracle_ghl.txt`, 7 GHL pairs) |
| `#AME` | `#AME 02 00 00 00 n 10 00 00 00`, Emitter/Particle/Field nodes | `#AME 00 00 02 00 n 40 00 00 00 … 00 00 80 3f`, Line/Sprite/Plane/Model/Gravity/Vortex/Omni Emitter… nodes (`ame_nodos.txt`) | **not convertible**: replace with the donor's #AME and recolour |
| `#AMT` | PS2 psm 0x13/0x14 | PSP psm 4/5 with swizzle | `psp_amo.convert_amt` (already exists) |
| Damage | — | SB ≈ B3 × 1.33–1.6 (Kamehameha 400 vs 250; jab 40 vs 30) | scale ×0.63 (as for B1) |

Useful curiosity: **Adult Gohan's BSP in SB2** (`BSP_GHL`) descends from B3's (same ASE codes
0x04/0x05, 0x24, 0x2C–0x2F; same AST code 0 Kamehameha): it serves as an **oracle** to map SB→B3
fields, just as the PS2/HD pairs served for `ps2hd`.

### 2.3 Future Gohan's real techniques (SB2) — `ghf_sb2.txt`

| # | Input (booster) | Code | Effect (SB BSP) | Reading |
|---|---|---|---|---|
| S1 | >E (12), ki 1000 | 0x460 (+0x461 finisher) | AST 0x15F **beam** type 0, tex 44/45 **blue**, 400/560 | **Kamehameha** (textures = those of GHL's Kamehameha) |
| S2 | >E (2) | 0x488 (+0x489) | AST 0x160 ball type 1, bone 14, 400/560 | energy ball (Masenko?) |
| S3 | <E (6), **cond 0x0004** | 0x48B (+0x48C) | AP1 hit 35 + c4 0x142 (common) | close-range special / rush |
| S4 | >E (1) | 0x491 (+0x492) | AST 0x162 slow ball, radius 17, lasts 8–14 | short-range explosion |
| S5 | <E (8) | 0x495 (+0x496) | AST 0x161 projectile type 3, 500/600 | blast/projectile |
| S6 | <E (1) | 0x49C (+0x49D) | hit + AST 0x15E ball, 500/650 | hit and ball |
| U1 | ^E (1), ki 5000, cond 0x0008 | 0x499 | AST 0x168 **type 12**, 900, juggle, tex 24/57 **magenta** | ultimate 1 (magenta wave) |
| U2 | ^E (14), ki 5000 | 0x464 | AST 0x169 beam **radius 23, 1000/1600**, tex 44/45 blue | ultimate 2 = exact twin of GHL's **Super Kamehameha** in SB2 (same values) |

Each AST comes in a pair (normal / powered up). No SB2 special or ultimate uses SPX: SB's
"ultimate" is a beam with a freeze (`c0 0x67` … `0x66`), not a cinematic. The official names are
not in the ISO as text (UTF-16/ASCII search in `data_sys_us`, `data_btl_us`, `BOOT.BIN`: no
results); they are menu textures.

### 2.4 The "community conversion" is a copy (`oracle_ghf.py` of explorer 01)

```
ghf_367.bin: #BSK 157824 = SB2 BCGHF child 3 (identical) · 3 #AMM = children 5,6,7 (identical, SB format)
ghf_365.bin: #AMC 32 B, #BCM 5996, #SPX 4136 = children 0, 2, 1 of BCGHF (identical)
```

The project's port converted the AMMs with `sb_amm.py` (correct) but left the BSK as is (`port
BSK == SB2: True`). This is how B3 reads the Kamehameha's AP7 (code 0x460) in the HD `#CSK`:

```
real SB2 (20 B):  01 00 03 02 03 00 00 00 4a 00 00 00 00 00 00 00 00 00 00 00
                  0a 00 04 02 02 00 00 00 1c 08 00 00 …  (voice)   …  2d 00 09 02 04 00 00 00 5f 01 … (beam 0x15F)
B3 reading 16 B:  f1 id3 cat3 val=0x4a | f0 cat33816586 val=0x2 | f0 cat0 val=0x207000b | f10 cat0 val=0 | …
```

### 2.5 Why `tecnicas.bin` is commented out

There is no written note (handbacks, memory, scratchpad), but `personaje_full.toml` (14:22 on
04-10) had it active and the final one comments it out. The data show it could not work:
- The port's `#ACE`: `23 41 43 45 00 02 00 00 00 00 00 14 00 00 00 40 … 3f 80 00 00` versus
  B3's `23 41 43 45 00 00 00 02 00 00 00 08 00 00 00 10`: B3 would read a wrong
  version/count/start in every `#AME`.
- `#CSE` with 18 0xB0 blocks that B3 walks at 0xD0.
- AST with codes 0x15E/0x15F (= ki blasts in B3) with 400–650 damage.
- Moreover the BSK would not reach them (misaligned AP7), so it added nothing but risk.

### 2.6 Other problems of the current port affecting the techniques

- `[[capsula]] reemplaza = 12, 2, 1, 8, 14`: booster 1 is shared by S4, S6 **and** U1 → the
  "Special 3" capsule would also enable ultimate U1; S3 (booster 6) is left out.
- S3 carries cond 0x0004 → B3 treats it as a **transformation** with <E (and `formas = 1`).
- No hyper mode entry (cond 0x0400) → in B3 the ultimates cannot be reached; SB's ultimates are
  pressed with ^E, not P+K+G+E.
- Empty `#ACC` (SB uses no cameras): any script or camera line of the donor would have no data.
- The `#SPX` is SB's: if a grab connected (HR type 3 → slot 20) B3 would execute bytecode of
  another VM (risk of a hang).
- `c0 = 0x7D0` in U2: an SB code unknown to B3 → remove it.

---

## 3. Strategy: "reformulating" SB's techniques on top of B3's system

**Principle**: the character is built **on the B3 donor** (Adult Gohan, ID 4: same skeleton by
suffix `GHL_*` ↔ `GHF_*`, same Kamehameha-family techniques) and SB's own compatible parts are
grafted onto it. What B3 requires and SB does not bring (hyper mode, cinematic, camera, beam
struggle entries, reserved effects) comes from the donor.

### 3.1 By layers

1. **BCM** (automatic, rules):
   - codes 0x4xx/0x6xx → free codes 0x26x–0x27x / 0x36x–0x37x of B3's range (avoids clashing
     with the donor's grab 0x480/0x488/0x489 and the cinematic's 0x4A0+);
   - SB cond 0x0004 → 0x0002; booster → a new capsule (one per technique, not per booster);
   - w9 → 0 and the ki to the capsule (+15 = w9/100: 10 specials, 50 ultimates);
   - finishers (cond2 0x8000/0x8101, window 0x7530) → B3's finisher pattern (combo children
     with the same capsule, like the donor's 0x24C/0x24D);
   - ^E ultimates → P+K+G+E cond 0x000A cond2 0x8001; graft the donor's **hyper mode** entry
     and order it first (`capsulas.hyper_first`).
2. **BSK** (automatic; shared with the moveset explorer): 20 → 16 B lines, HR 160 → 128 B, AP1
   hitbox s16 → s8, damage ×0.63, c2/c3 voices to yell bank slots (`gritos.py`), remove unknown
   c0 codes (0x7D0). Validatable offline against the SB2-GHL / B3-GHL pair (same hits).
3. **Hybrid BSP** (automatic + visual tuning):
   - base = the donor's whole BSP (528) → keeps ASE 0x67–0x69/0xC8/0x64, blast AST
     0x15E/0x15F, `#AWV`, models and their `#AMM`;
   - add SB's ASTs (0xF0 copy) **renumbered** to free codes (0x1–0x9…), with the beam textures
     imported into the donor's large `#AZT` (`psp_amo.convert_amt` + `azt_append`) and the
     BSK's AP7 c4 rewritten to the new code;
   - add SB's ASEs remapped 0xB0 → 0xD0 (GHL oracle table; bones by table);
   - particles: each SB ASE/AST is linked to a **donor `#AME` with the same role** (hand charge
     = the Kamehameha's ASE 0x04/0x05; beam mouth; impact) and recoloured (RGBA float colour
     blocks and textures). U1's magenta and S1/U2's blue come from SB's textures.
4. **Cinematic ultimate (U2 → GHF's "Super Kamehameha")**: graft from the donor the BCM entry,
   block 0x25A (rush + HR type 3 code 0), the **whole SPX** (slots 0 and 20), the **`#ACC` +
   `#ACL`** and animations 0x4A0–0x4AF (`b1port.bsk_graft` + `Amm`); optional: replace the final
   shot's animation with SB's (anim 132) **resampled to the donor's duration**, so as not to
   touch the script's timing. The script's effects point to the donor's BSP, which is in the
   hybrid base.
5. **Second ultimate (U1, type-12 magenta wave)**: two options. (a) A powerful non-cinematic
   special (it is what it is in SB; safe). (b) A 2nd ultimate in slot 1 (precedent: Vegeta
   capsule 44, Buu M) grafting a second cinematic from another donor: more work and risk.
   Recommended (a) in the first version.
6. **Beam struggle for S1 (Kamehameha)**: mark its entries with 0x2000, insert into its AP7
   `c0 0x64` (start), `c0 0x68` and `c0 0x66` anchored to the firing frame (in the donor: 38, 12
   and 11 frames before the beam's c4) and create the response entry cond2 0x4003 with its
   variant (without 0x64/0x66, `c0 0x69`, 0x40, 0x43). All copying the pattern of 0x24B/0x26C.
7. **Capsules**: 6 specials + 1–2 ultimates with provisional names, SB's ki (+15), forms (+14 =
   0x01 with `formas = 1`), without "reemplaza" by booster but by technique.

### 3.2 What is automated and what is craft

| Automatable (tool `sbport.py` or extend `b1port`/`ps2hd`) | By hand / iterative |
|---|---|
| BSK 20→16, HR, AP1 hitbox, damage, code remap | Choosing which donor #AME represents each SB effect |
| BCM: conds, boosters → capsules, ki, hyper, finishers | Recolouring particles until they "look official" |
| AST: copy, renumbering, textures, links | Which GHF animation replaces which in the cinematic |
| ASE: 0xB0→0xD0 remap by oracle | Fine damage/ki balance |
| Grafting hyper, ultimate (SPX, ACC, 0x4A0+), grab | Official technique names |
| Beam struggle pattern anchored to the firing frame | Deciding U1 as a special or as a 2nd ultimate |
| Offline checks (all AP lines with valid categories, c4 codes existing in the BSP, no 0x15E/0x15F with damage, `deep.py` style) | |

---

## 4. Concrete plan, risks, effort and validation

| Phase | Content | Effort | Validation |
|---|---|---|---|
| F0 | SB→B3 BSK/BCM converter (with the moveset explorer) + offline checker | 1–2 sessions | offline vs the GHL pair; in game: GHF's hits and combos |
| F1 | Hybrid BSP (donor + SB AST/ASE + textures) and rewritten AP7 c4 | 1–2 sessions | offline: every c4 exists; in game: S1–S6 fire their energy |
| F2 | Particles: role mapping + recolouring | 1 session + iterations | in-game captures versus SB2 video |
| F3 | Hyper + grafted cinematic ultimate (U2) + the donor's grab | 1–2 sessions | in game: LT/L2, P+K+G+E, full cinematic without broken poses |
| F4 | Beam struggle (S1) + capsules (ki/forms/names) | 0.5 session | in game: Kamehameha against Kamehameha |
| F5 | U1 as a powerful special; technique voices | 0.5 session | in game |

Risks:
- **B3 engine + partial SB data**: any unknown c0 code or broken AME link may close the game →
  clean up with a whitelist of categories/values seen in B3.
- **Cinematic**: the victim's animations come from AMM 2 (3712 generic anims); SB's has the same
  count but other content → use the donor's AMM 2.
- **GHF's extra bones** (`LOBI1-3`, coat tail): they stay at rest during the donor's
  animations; it may be noticeable.
- ASE slots 0x67–0x69/0xC8 and the capsule's byte +20 (0x45 inherited from Goku in the new
  ultimate) have an unconfirmed function.
- Clash with the other explorers' work (moveset, transformations): F0 is shared.

In game it must be validated (the user guides up to the character): normal hits after F0; each
special S1–S6 (effect, damage, ki); hyper mode and ultimate; beam struggle S1 against a B3 beam;
that the ki blast (E) keeps its normal look and damage; Edit Skills with the new capsules.

---

## 5. Open questions

1. Official names of S2–S6 and U1 (Masenko? the magenta wave?): confirm with the user /
   Kanzenshuu, or decode the textures of SB2's command list.
2. U1 as a powerful special (recommended) or as a 2nd cinematic ultimate?
3. Is beam struggle wanted for GHF from the start?
4. What exactly do cond2 0x4000 and c0 0x68/0x69 do (A/B test in game before offering the
   Discord switch)?
5. Meaning of `#SKC` +20 (4 in Gohan's specials, 0x48 in his ultimate) and of AP7 categories
   7/8 (hyper mode camera?).

---

## 6. Evidence and scripts (in this folder)

- `tec_b3.py` — BCM→BSK→BSP→SPX chain of a B3 character (`python tec_b3.py <cam> <anm> <bsp>`).
- `tec_sb.py` — the same for SB2 with its formats (`python tec_sb.py BCxxx.amb BSP_xxx.amb`).
- `tree.py`, `sbafs.py` (copy from explorer 01) — LE/BE #AMB tree; PSP AFS reader.
- `skc_ki_check.py` / `skc_ki_check.txt` — ki and forms in the `#SKC`.
- `gohan_adulto_b3.txt`, `gohan_teen_b3.txt`, `goku_b3.txt`, `nappa_b3.txt` — B3 chains.
- `ghf_sb2.txt`, `ghf_m1_sb2.txt` — GHF's techniques in SB2 (base form and SSJ).
- `beam_struggle_censo.txt`, `definitivos_b3.txt`, `bsp_censo_b3.txt` — censuses of the 38.
- `ast_b3_vs_sb2_kamehameha.txt`, `ase_oracle_ghl.txt`, `bsk_oracle_ghl.txt`, `ame_nodos.txt`
  — B3 ↔ SB2 format comparisons.
- `texturas_rayos_montaje.png` — textures: U1 (magenta 24/57), S1/U2 (44/45), GHL SB2 (34), B3 (42).
- `sb2_btl_us.txt`, `sb2_sys_us.txt` — SB2 AFS listings.
- In the exploration work folder (`02_tecnicas\`): extracted PS2/HD bins (528, 529, 231, 234,
  241, 245…), `BSP_GHL_sb2.amb`, `BCGHL_sb2.amb`, `BSP_CMN_sb2.amb`, `menu_*.amb`, PNG textures;
  `afs_pair` cache in `tmp\` (`TEMP` was set there so as not to write outside).
