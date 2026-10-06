# Shin Budokai 1 / 2 (PSP) movesets → Budokai 3 HD

Exploration and RE report. First target: Future Gohan (GHF). Date: 2026-10-06.

- The game was not launched and no project file was touched.
- Everything cited was measured with the scripts in this folder. The ISOs are read in place, without extracting them.
- This report was written without reading `AGENTS.md`; the sections it cites were looked up with grep.

---

## 0. Executive summary

1. **SB1 and SB2 use the same engine as B3, but there are differences that break compatibility.**
   - The containers and versions match: `#AMB` v3, `#BSK` v4, `#AMM` v2, `#BCM`, and `#SPX ver 0.01` with the same virtual machine.
   - Inside, several layouts change:
     - the AP lines are **20 B** (16 in B3);
     - the hit-reaction (HR) blocks are **160 B** (128 in B3);
     - the AMM animations are **compressed**, with an 8 B table (16 in B3);
     - the **attack code space is renumbered**;
     - the **indices of the global animation store** are different;
     - the **SPX native functions** are renumbered.
2. **The Future Gohan "community conversion" (`ghf_365/367`) converts nothing.**
   - It is a byte-for-byte repack of the children of SB2's `BCGHF.amb`.
   - The current port `port_gohan_futuro` only decompresses the AMM (with `sb_amm.py`). The `#CSK` is the PSP BSK unchanged: 157,824 B in both.
   - So B3 reads the hits, the impact windows, the damage and the effects with the wrong stride. **It does not hang, but it almost certainly hits wrongly.** It has to be validated in game.
3. **The differences are systematic and can be measured with oracles.** There are 17 characters in both SB and B3 (Goku, Vegeta, Piccolo, Cell, Buu ×3…). Matching their animations by pose gives:
   - 80 % of the own animations are **identical** (0.0°);
   - 78 % of the global store animations are **identical** (206 of 265);
   - a stable table of **SB → B3 engine codes** (96 codes);
   - the **damage scale**: B3 = 0.85 × SB (median of 8,847 hits);
   - which fields match in the BCM, the HR and the effects.
4. **Verdict: a generic `sbport.py`, in the style of `b1port.py`, is VIABLE.**
   - It would come out better than the B1 port, because here the animations, the common effects and the hit fields are preserved.
   - The only thing that cannot be ported directly is SB's own SPX scripts: they call renumbered native functions. They affect few hits: 4 in GHF, which call SPX slots 30/40/50.
   - The B3 donor's SPX would be used, as `b1port` already does.
5. **Estimated effort:** about 5–7 days of work for the full GHF, with the tools and 2–3 rounds of in-game testing. Then about 2–3 days to generalise it to SB2's 24 characters and SB1's 18. Own effects (BSP) and voices are separate work.

---

## 1. Structure of the PSP ISOs

Both ISOs are in `ps2_games/` and are read with `mod center hd/iso.py`. They contain AFS with a **name table** (48 B per entry, the pointer comes after the offset table). The reader is in `sbafs.py`.

| File | SB1 (ULUS_10081) | SB2 (Another Road) | Content |
|---|---|---|---|
| `USRDIR/data_btl_cmn.afs` | 206 entries, 132 MB | 286 entries, 185 MB | Everything battle-related per character (see below) |
| `data_btl_voice_us.afs` (+ `_jp`) | 12.7 MB | 19.1 MB | Battle voices `BC<XXX>SND.amb`, `BC<XXX>M<n>S.amb` (**PPHD** header + PS-ADPCM/VAG) and phrases `ZP1/ZP2<XXX>A0` (RIFF ATRAC3plus) |
| `data_sys_*.afs` | — | — | Menus, images, system voices |
| `PSP_GAME/SYSDIR/BOOT.BIN` | plain ELF | plain ELF (3.1 MB) | Contains no file names: the game uses AFS indices (`BCGHF` was searched; only `MSG_SYS_CHAR_GHF` appears) |

The full listings are in `sb1_btl_cmn.txt` and `sb2_btl_cmn.txt` (index, size, name and header).

**Each character's files in `data_btl_cmn.afs`** (for example, GHF in SB2):

| Entry | Name | Content |
|---|---|---|
| 70 | `BCGHF.amb` | **Moveset**: `#AMB` [AMC (32 B stub), SPX, BCM, BSK, —, own AMM, AMM2, AMM3] |
| 71–74 | `BCGHFB00..B03.amb` | Models (costumes or forms): [`#AMO`, `#AMT`, `#RPT`]. The "LOBI1/AROBI1" `#RPT` is the **belt physics**, and it is the belt strip the port still has pending. |
| 75 | `BCGHFM1.amb` | The same moveset plus a **second small BSK** that overrides individual codes (in GHF only `0x19F`; in GOK `0,18c,18d,190,191,198-19a,19f`). It is tied to a specific B0n model; which one is still to be confirmed. |
| 76 | `BAR_GHF.amb` | Aura: [AMT + AME…, AMO] |
| 77 | `BSP_GHF.amb` | Technique effects: `#AMB` of [AST/ASE, AMT, **`#AME` v0x00020000** with a 0x40 header], **a different format** from B3's `#AME` v2 |
| 164 | `AC_GHF.spx` | A separate SPX with 24 slots; its use is not identified |
| 209 | `EV_ACGHFED.spx` | Event SPX (`EV_AC<XXX>00/01/02/ED`) |
| 0 | `BCCMN.AMB` | Common: [AMT, BSK (0x800 codes, 1 HR), **global AMM** (265 animations, store 0), AMM (5,422)] |

**Characters (code → B3).** The B3 ID is in `corpus.PAIRS`.

| Code | SB1 | SB2 | Character | In B3? |
|---|---|---|---|---|
| GOK | ✓ | ✓ (XGK4 bones) | Goku | ID 0 |
| VGT | ✓ | ✓ | Vegeta | ID 7 |
| PIC | ✓ | ✓ | Piccolo | ID 11 |
| KLL | ✓ | ✓ | Krillin | ID 10 |
| GHM | ✓ | ✓ | Teen Gohan | ID 3 |
| GHL | ✓ | ✓ | Adult Gohan | ID 4 |
| TRX | ✓ | ✓ | Trunks (XTRX skeleton) | ID 8 |
| TRF | | ✓ | Trunks, another variant (XTRX; probably Future with sword) | partial |
| FRZ, CEL, COO, BRL, 18G | ✓ | ✓ | Freeza, Cell, Cooler, Broly, Android 18 | 27, 33, 38, 40, 30 |
| BUS | ✓ | ✓ | Kid Buu (XBUS) | 36 |
| BUL, BUM | | ✓ | Majin Buu (XBUL), Super Buu (XBGX) | 34, 35 |
| BDK, DBR | | ✓ | Bardock, Dabura | 39, 37 |
| **GHF** | | ✓ | **Future Gohan** | **no** |
| **GGT** | ✓ | ✓ | **Gogeta SSJ** (VGT skeleton) | no (B3 only has Gogeta SSJ4 as a form) |
| **VTO** | ✓ | ✓ | Vegito (VGT skeleton) | only as a B3 fusion |
| **GTX** | ✓ | ✓ | Gotenks | only as a Goten form |
| **JNB, PKH** | ✓ | ✓ | Janemba, Pikkon | no (the project already has IW ports) |

---

## 2. The community oracle: the GHF conversion transforms nothing

`oracle_ghf.py` compares each child of `ghf_365.bin` / `ghf_367.bin` (`modding resources/Infinite World to Budokai 3 Moveset Ports/Future Gohan (Shin Budokai)/`) with those of `BCGHF.amb`:

```
ghf_367.bin 0 #BSK 157824  identical to SB2 child [3]
ghf_367.bin 1 #AMM 1737148 identical to SB2 child [5]
ghf_367.bin 2 #AMM 176116  identical to SB2 child [6]
ghf_367.bin 3 #AMM 9756    identical to SB2 child [7]
ghf_365.bin 0 #AMC 32      identical to SB2 child [0]
ghf_365.bin 1 #AML 5       (stub, the same as the 5 B #AML of every B3)
ghf_365.bin 2 #BCM 5996    identical to SB2 child [2]
ghf_365.bin 3 #SPX 4136    identical to SB2 child [1]
```

The community only split the children into the ANM = [BSK, AMM, AMM, AMM] and CAM = [AMC, AML, BCM, SPX] layout.

In the current mod (`out/build/win-amd64-release/mods/port_gohan_futuro/moveset/anm_forma1.bin`):
- the `#CSK` is 157,824 B, the same PSP BSK converted to BE with `ps2hd.conv_bsk`, which assumes 16 B lines;
- the `#ACM` is decompressed: its table is `00000009 00000000 00000018 …`, i.e. it went through `awo_tools/sb_amm.py`.

---

## 3. Format differences, with evidence

### 3.1 AMM (animations): **already solved by `awo_tools/sb_amm.py`**

- **SB:** 8 B table `[u16 frames][u16 options][u32 bones]`. The tracks are compressed: keys in u8 and values s16/f32.
- **B3:** 16 B table `[flags 9/0x19][0][frames][ptr]`.
- Example (`BCGHF` AMM, entry 0): SB `18000000 98040000` versus the mod's ACM `00000009 00000000 00000018 00000910`.
- `sb_amm.convert` was used to compare. With it, the animations match by pose at 0.0° (see 3.6). The decompressor is validated.

### 3.2 BSK: **20 B AP lines** (B3: 16 B)

Same hit, Adult Gohan's first combo, SB2 `GHL 0x400` versus B3 `ID 4 0x200` (`apdump.py`):

```
SB2  AP type 1 (hit), 20 B per line:
     0900 0001 0000 0000 0100 0f16 0000 0000 0000 0000   <- frame 9, HR 0, props 1, part 0x0f, radius 0x16
     0d00 0000 ffff ffff 0000 0f00 0000 0000 0000 0000   <- close (HR 0xFFFF)
B3   AP type 1, 16 B per line:
     0800 0001 0000 0000 0100 0e00 0000 0000
     0b00 0000 ffff ffff 0000 0e00 0000 0000
```

- Read 16 at a time, SB's line 2 comes out as `0000 0000 0d00 0000 ffff ffff …`: frame 0, HR 0x0d, props 0xFFFF. That is garbage, and it is what the game reads today in the GHF port.
- With a 20 B stride, SB2's distributions match B3's: the same AP types 0–7 and the same effect classes.
- The 4 tail bytes are 0 in every line, except in type 1 lines (`apstats.py`).

**Hit line (type 1), fields by byte** (`t1hit.py`, checked with matched hits in `pairhits.py`):

| Field | SB (20 B) | B3 (16 B) |
|---|---|---|
| frame, idx, 0x01 | +0..+3 | +0..+3 |
| HR code (u16; SB goes up to >255 blocks) | +4 | +4 |
| props | +8 | +8 |
| body part | +10 | +10 |
| radius | **+11** | **+12** (+11 = 0) |
| position x, y, z | **3 × s16 at +12, +14, +16** | **3 × i8 at +13, +14, +15** |

Matched example (Krillin, SB `0x18c` ↔ B3 `0xfc`):

```
SB 1200 0001 0601 0000 6000 0496 0000 0000 0000 0000
B3 1200 0001 5d00 0000 6000 0400 9600 0000
```

### 3.3 BSK: **160 B HR blocks** (8 lines of 20 B; B3: 8 of 16 B)

- SB's HR section is `n_hr × 160` in the 42 characters of SB1 and SB2.
- The lines have the same fields as B3: `[damage u16][grunt u8][visual u8][type u16][code u16][push f32][specific u32]`, plus a 4 B tail that is 0 in all 53,296 lines.
- Example of the same hit:

```
HR SB 7800 c800 0200 0200 0000 8c42 0000 0000 0000 0000
HR B3 7800 40e7 0200 0200 0000 8c42 0000 0000
```

- Field agreement over 70,872 matched lines (`hrcols.py`): type 84 %, code 79 %, push 73 %, grunt/visual 70 %, damage 21 %. The damage differs because it is rebalanced.
- **Converting an HR line means truncating it to 16 B.**
- **Damage scale (`dmgscale.py`):** B3/SB = **0.846** median, with quartiles 0.67 / 0.85 / 0.92 over 8,847 hits. Per character it ranges from 0.71 (Android 18) to 1.0 (Majin Buu). Recommendation: multiply by 0.85.

### 3.4 BSK: animation sub-block (48 B), almost identical

Comparison of 18,468 matched sub-blocks (`subblk.py`):

- +6, +0xC, +0xE, +0x12–0x16 and +0x24: 100 % equal.
- **+0x10:** SB carries the **0x80** bit where B3 has 0 (5,452 cases). It is an SB-only flag and must be removed.
- **+0x1C–+0x22:** link or next-code fields (`0x1a7`, `0x130`, `0x1a0`, `0xffff`). They are **codes** and must go through the remap table.
- +0x28 / +0x2C: number and offset of the APs. Recomputed.

### 3.5 BSK: **the code space is renumbered**

Average codes defined per character and per 0x100 range (`apstats` / corpus):

```
SB1/SB2: 0x0:12  0x100:53  0x200:7  0x300:8  0x400:81  0x500:17  0x600:81  0x700:17  0x800:6-9
B3     : 0x0:23  0x100:6   0x200:161 0x300:117 0x400:22
```

Deduced layout:

| SB | B3 | What it is |
|---|---|---|
| 0x000–0x1FF (ground), 0x200–0x3FF (air, **+0x200**) | 0x000–0x0FF / 0x100–0x1FF (air, **+0x100**) | Stances and basic moves triggered by the engine |
| 0x400–0x5FF ground, 0x600–0x7FF air | 0x200–0x2FF ground, 0x300–0x3FF air | Attacks launched by the BCM (each character's own numbering) |
| 0x500+i / 0x508+i / 0x510+i | 0x2E0+i / 0x2E8+i / 0x2F0+i | Transformation families (global store 6/7/8 ↔ 14/15/16) |
| 0x700+i / 0x708+i | 0x3E0+i / 0x3E8+i | The same, in the air |
| 0x800, 0x801, 0x808, 0x809 | 0x480, 0x481, 0x488, 0x489 | **Grab BASE**: SPX 20 does `push16 BASE` in both games |

**Stable table of engine codes** (`enginemap.py` → `engine_map.json`). Matched by animation in the 17 pairs and accepted with 60 % agreement or more:

```
0->0  1->2  3->4  6->7  7->8  8->9  9->a  a->b  15->10  16->11
40->3c 41->38 42->39 43->3a 44->13b
194..197->f4..f7  198->f8 199->f9 18c->f8 18d->f9 191->f9 19f->f6
241->138 242->139 244->13b  3e0..3e7->3c8..3cf
453->257 (grab hit) 653->357  500..517->2e0..2f7  700..70f->3e0..3ef  800->480 801->481
```

The full votes, including each character's attacks, are in `code_votes.json`.

**Codes B3's engine triggers that SB does not provide.** They are grafted from the donor, as in `b1port`:

```
3b ea ec-ed fa-ff 13a 13c 1ec-1ed 233 23e 256 259 280-293 2a0-2b1 2c0-2d9 333 33e 356 359
3d0-3d7 433-437 46e-471 482-48d 490-4bb 4c0-4c1
```

This list is computed from `b1port.ENGINE` minus the codes covered by the table. It includes hyper mode (0x259), Dragon Rush (the 0x280 family), throws and grabs. SB codes 0x1C0–0x1E7 resemble 0x280/0x2A0/0x2C8, but the agreement is low (13–20 votes out of 65–100), so they are grafted too.

### 3.6 Global animation store (store 0): **the same data with another index**

- `globalmap2.py` compares SB's `BCCMN.AMB` child 2, decompressed, with B3's `data_cmn` 165 child 0 (359 animations; it is the common pack `[AMM, AMM, AMC, AML, BSK(2172), SPX]`).
- **206 of 265 animations are identical by pose (0.0°)**, but at another index. Examples: `2->4, 6->14, 7->15, 8->16, 25->35, 26->36, 196->201, 197->202` (the last two are the grab animation).
- The full table is in `global_map_sb2.json`; SB1 gives the same result (`global_map_sb1.json`).
- There are 59 SB animations without a pair (e.g. 222, 241, 243). The proposal is to copy them into the character's own AMM, as store 3, so as not to lose them.
- Today the GHF port uses SB's indices as is. In game, SB's 6 asks for B3's animation 6, which is a different one.

### 3.7 Own AMM, AMM2 and AMM3

- **Own AMM.** Matched by pose (`posematch.py`, with the body bones' rotations at t = 0, 0.5 and 1), between **74 and 90 %** of SB's animations are exactly B3's for the same character (`animmatch.log`).
  - SB's animations use the SB model's skeleton, e.g. XGHF_* in GHF. `psp_amo.py` keeps those names, so nothing needs retargeting.
  - The donor's do need retargeting, with `b1port.retarget` and `altura.py`.
- **AMM2** (victim animations, a sparse table of 3,712 entries): SB has 1,322 non-null entries and B3 49, at different indices. **The donor's is used**, which brings the grabs.
- **AMM3** (257 entries): B3 only uses 256; SB uses 129 onwards. The donor's is used.

### 3.8 BCM (combos and inputs): the same 64 B block, but with other flags

`bcmstats.py` gives the distributions and `bcmpairs.py` matches the fields by animation. On PS2, `w4` is the condition and `w5` the type; in HD they are the other way round (see `capsulas.py`).

| Field | SB | B3 | Conversion rule |
|---|---|---|---|
| w0 direction | 0, 1, 2, **0x10 (↑), 0x20 (↓)** | 0, 1, 2 | ↑/↓ do not exist in B3 inputs. Ultimates ↑+E → P+K+G+E in hyper mode (like `adapt_iw_bcm`); ↓+E with w4 0x20 → transformation P+K+G. Normal attacks with ↑ matched B3's `w1=3` (5 votes): **validate**. |
| w1 buttons | 1, 2, 5, 8 | 1, 2, 3, 5, 6, 7, 8, 0xF | Transformation goes to w1=7 and hyper to 0xF (from the donor) |
| w3 | **0x7530** in 104 entries | always 0 | Set 0 |
| w4 condition | 1 (costs ki), 2 (special with capsule), **4, 8, 0x10, 0x20, 0x40, 0x80** | 1, 2, 4, 0x400, 0x2002, 0x12… | SB 4 → B3 special (2). SB 8 → ultimate. SB 0x20 → transformation (4). SB 0x80 + w6 0x100 → ultimate in hyper (B3 `w1=f w4=1a w6=8001`). |
| w5 | 2 in 88 entries ("alternative" variant) | 0 | Set 0 |
| w6 | 1 ground, 0x40 air, **0x100, 0x101, 0x8000, 0x8101** | 1, 0x40, 0x8001, 0x4003 | Remove 0x100. Duplicated entries with w6 0x8000 (+ w3 0x7530) are the "after-combo variant": move them to the B3 pair `w4 0x2002 / w6 0x4003`, or discard them. |
| w9 ki | Blasts 0x12c–0x177 (**same as B3**); specials 1000; ultimates 5000; transformation 4000 | Blasts the same; specials 0 | Blasts: copy. Specials and ultimates: 0, and move the cost in bars ((w9+500)//1000) to the capsule, as `capsulas.KI` does |
| w12–w15 codes | 0x4xx / 0x6xx | 0x2xx / 0x3xx | Remap: engine table + relocation |
| header (0x50 B) | 19 of 24 equal to B3's; 3 (GHF included) carry a copied block | 36 of 38 equal | Use the standard B3 header |

Example of a special entry in GHF and its pair in B3:

```
SB2 GHF: 0001 0008 0000 0000 0002 0000 0101 0000 000c 03e8 0000 0000 0460 0660 0660 0000   (→+E, capsule 12, ki 1000)
SB2 GHF: 0001 0008 0000 7530 0002 0002 8000 0000 000c 03e8 0000 0000 0461 0661 0661 0000   (variant)
B3 GohL: 0001 0008 0000 0000 2002 0000 0001 0000 001a 0000 0000 0000 024b 034b 034b 0000
B3 GohL: 0001 0008 0000 0000 0002 0000 4003 0000 001a 0000 0000 0000 026c 036c 036c 0000
```

SB has no hyper mode; its equivalent is the state with w6 0x100. The hyper entry (P+K+G+E, 0x400) and the grab (P+G) must be grafted from the donor, just like in `b1port.convert_bcm`. SB's grab, `w1=5 → 0x453`, goes to B3's 0x257.

### 3.9 SPX: **the same virtual machine, with the native functions renumbered**

Slot 20 (the grab) is the same program in both games. Only the BASE and the address of the common routine change:

```
SB2 GHF/KLL: 08 20 00 08  01 30 70 05 00 00  02 73 02  12 10 04  0b 76    push16 0x800; call 0x570; pop 4; ret
B3 GohanL : 08 20 80 04  01 30 20 25 00 00  02 73 02  12 10 04  0b 76    push16 0x480; call 0x2520; ...
```

**The natives** (`01 10 id 02 80 02 12 10 nn`) are renumbered:
- `spxbuiltins.py` → `spx_builtins.txt`: of 69 common IDs, 56 have a different argument size.
- Aligning the grab routine gives the SB→B3 pairs `8→8, 64→64, 17→33, 18→34, 22→38, 26→42`. In that stretch B3 adds 16, but it is not a single offset.
- A global alignment by argument size (`spxalign.py`, `spxmap.py`) is not enough. It would require aligning call graphs, which are the common library every SPX carries before the 1st slot (SB 0x7B4 B, B3 0x2784 B).

**Slots** (`spxslots.py`):
- SB2 GHF uses slots 0, 1, 20, 30, 40, 50 and 100. B3 uses 0 (Dragon Rush in hyper) and 20 (grab).
- SB calls its slots from **class 10** type-7 AP lines. In GHF: slot 30 at `0x528/0x728`, slot 40 at `0x529-52a/0x729-72a` and slot 50 at `0x52b/0x72b`.
- In B3 class 10 exists but is hardly used.
- There are SB type-3 HR hits that call a script: 18G and CEL at `0x453` (grab, slot 10/100), and PIC and TRX at `0x18c-19f`.

→ **Decision: use the donor's SPX.** The codes it pushes are relocated (`b1port.spx_code_refs`) and SB's class 10 lines and the type 3 hits pointing to SB slots are removed, turning them into type 2 as in `b1port.bsk_fix_b1_hits`. Later, optional: an SB→B3 natives translator.

### 3.10 Camera (AMC)

- Each character's AMC in SB is a stub with 0 animations (32 B). In B3 it carries about 26 cameras (14–127 KB).
- SB's ultimate cameras come from somewhere else: the SPX or the common data.
- Class 5 lines, which contain camera or slow-motion values, **match 100 %** (e.g. `0x4b0/0x44e` in the grab BASE of both games).
- → **Use the donor's AMC.** SB's ultimates would have no cinematic camera of their own: validate.

### 3.11 Effects, sounds and voices (AP type 7)

Format `[frame][0x02 idx][class u32][value u32]` (+4 B tail in SB). Result of matching lines by frame and class in matched hits (`t7pairs.py` → `t7_maps.json`):

| Class | What it is | Equal | Action |
|---|---|---|---|
| 0 | Effect (BSP index; < 0x64 are common) | **97 %** | Copy. Those ≥ 0x64 point to the own BSP: remove them (`--quitar-efecto`) or convert the BSP. |
| 1 | Sound | 0 % | Majority table (e.g. `3d→51` 507/507, `f→17` 398/414, `10→18`) |
| 2 | Spark or impact | 0 % | Majority table (`7f7→32`, `be0→2b`, `39→35`) |
| 3 | Yell slot of the language bank | 5 % | Remap by ranges (SB 0x0b–0x12 → B3 0x13–0x1a, which are random variants; `1a→27`, `1b→28`) |
| 4 | — | 76 % | Copy plus table |
| 5, 6, 8, 9 | — | 99–100 % | Copy |
| 0xA (10) | SPX slot call | — | Remove (donor's SPX) |
| 0xB… | SB-only | — | Remove |

**Own BSP:** SB's `#AME` is another version (`00000200`, 0x40 header; B3 `02000000`, 0x10 header). For now, the donor's BSP; converting it is separate work.

**Voices:** `BC<XXX>SND.amb` is PPHD + PS-ADPCM, an easy format already decoded in B1 (`gritos.scei_bank`) that enters through the RXADPC gateway. The ZP phrases are ATRAC3plus. An ffmpeg build that decodes them is already on the machine (`-decoders` shows `atrac3plus`). Nothing needs installing.

---

## 4. What probably happens today to `port_gohan_futuro` (validate in game)

1. **Hits.** The AP lines are read every 16 B over 20 B data. The hit windows, HRs, effects, sounds, speed and turn come out shifted. Damage and reaction random or null; some hits may not connect.
2. **HR.** Block h is read at `128·h` when it is really at `160·h`, with garbage stun types (the `0xcccd`, `0x999a` that come out when reading 16 B).
3. **Global store with another index.** The transformation (0x500), the grab (196/197) and pose 0x2 ask for other animations.
4. **The engine triggers B3 codes that are not in the moveset.** The grab (BASE 0x480), hyper (0x259) and Dragon Rush (0x280…) are missing. In their place are SB's attacks at 0x480–0x4BB.
5. **BCM.** The ↑+E (ultimate) and ↓+E (transformation) inputs use directions B3 does not have in inputs. The duplicated entries with w6 0x8000 / w3 0x7530 have an unknown effect. The specials cost ki through the BCM and also through the capsule.
6. **SB's SPX.** If its slots are ever executed, they would call the wrong natives. Today they are probably never called, because class 10 is read misaligned.

---

## 5. Design of `sbport.py` (generic SB1/SB2 → B3 PS2 → `ps2hd`)

What exists is reused: `b1port` (AMM, BSK, BCM, grafts, retarget, SPX), `sb_amm`, `psp_amo`, `ps2hd`, `capsulas` (adaptation, hyper first), `gritos`, `altura` and `roster_build`.

```
sbport.py --juego sb2 --personaje GHF --donante-anm 234 --donante-cam 231 [--forma-m 75]
          --modelos traje1..4.amb --salida DIR [--quitar-efecto 64..]
```

1. **Reading.** `sbafs.Afs` reads `BC<XXX>.amb` (and `M<n>`) from the ISO; `sb_amm.convert` decompresses the AMMs.
2. **Normalise the BSK** (new, about 150 lines):
   - AP 20 → 16 B: copy `[0:16]`. Only in type 1 lines is the hit box reordered (radius to +12, s16 → i8 at +13..+15).
   - HR 160 → 128 B (truncate each line). Damage × 0.85.
   - Remove the 0x80 bit at +0x10 of the sub-block.
3. **Remap codes.**
   - **Engine:** `engine_map.json`, plus the 0x500/0x700/0x800 families by offset.
   - **BCM attacks:** relocate 0x4xx/0x6xx into free gaps of 0x2xx/0x3xx, not in `ENGINE`, keeping the ground/air pair (+0x100).
   - The same map is applied in the BCM (w12–15), in the sub-block links (+0x1C..+0x22) and in the donor's SPX (`spx_code_refs`).
4. **Store 0.** Use `global_map_sb*.json`. Unpaired animations are copied into the own AMM (store 3).
5. **Donor grafts** (`b1port.bsk_graft`). Everything listed in §3.5 is grafted: hyper, Dragon Rush, grab and throws (the donor's BASE).
   - By default, the donor's whole grab, because of the victim in AMM2.
   - Optional: SB's grab animation (0x800…) with the donor's victim, if the frames fit.
6. **Effects.**
   - Classes 1, 2, 3 and 4 through `t7_maps.json`.
   - Remove classes 10 and 11+.
   - Remove class 0 ≥ 0x64 (or keep them if the BSP is converted).
   - HR type 3 hits to SB slots → type 2.
7. **BCM.** Apply the rules of §3.8 and then those of `capsulas` (own capsules, KI in bars, `hyper_first`).
8. **Forms.**
   - SB's 0x500 family (↓+E) is the transformation. In B3 it would be P+K+G → 0x2E0 with form 2.
   - Form 2 uses the same moveset plus the `M<n>` override (e.g. 0x19F → 0x0F6).
   - `B0n` models with `psp_amo`.
9. **Camera and SPX:** from the donor. **AMM2 and AMM3:** from the donor.
10. **Checking:** a `deep.py`/`verify_final.py` for SB:
    - the code table covers all of `ENGINE`;
    - no 20 B lines remain;
    - the store indices are valid;
    - the donor's SPX only changes in the relocated bytes.

---

## 6. Step-by-step plan and effort

| # | Step | Effort | Validation |
|---|---|---|---|
| 1 | `sbport.py` step 2: normalise the BSK (20 → 16, HR, flags) and check against the corpus with a field round-trip | 0.5–1 d | No game: the distributions of 3.2/3.3 must equal B3's |
| 2 | Code remap and store 0 (tables already computed) | 1 d | No game: every BCM code exists in the BSK and every engine code is covered |
| 3 | Donor grafts and BCM | 1–1.5 d | **Game:** combos, hits, damage, grab, hyper, Dragon Rush |
| 4 | Effects and sounds by table; yells (PPHD → gateway) | 1 d | **Game:** correct sounds and voices when hitting |
| 5 | GHF's SSJ transformation (form 2, models B01/B03, `M1`) | 1 d | **Game:** transform and back |
| 6 | Generalise and test 2–3 more characters (SB Janemba, Gogeta SSJ, Pikkon) | 2–3 d | **Game** |
| 7 | (Optional) Own BSP: converter for SB's `#AME` | 2–4 d | **Game:** techniques with their effects |
| 8 | (Optional) SPX natives translator SB → B3 to recover SB's scripts | 3+ d, uncertain | **Game** |

Core total (steps 1–5): about 5–7 days. With generalisation: about 8–10.

---

## 7. Risks

- **BCM ↑/↓ inputs.** It is not known whether B3's input reader accepts w0 0x10/0x20, because no B3 character uses them. They are converted to B3 buttons, although the mapping of normal attacks with ↑ has little evidence.
- **Variants with w6 0x8000 / w3 0x7530.** The semantics are probable but not confirmed ("after combo" or "aura").
- **Damage scale.** It varies per character (0.71–1.0). SB's maximum health has not been compared.
- **Ultimates without their own camera or script.** The same happened with B1. They will look like hits with their animation, but without SB's cinematic.
- **Grab.** Mixing SB's animation with the donor's victim may desync; by default it comes wholly from the donor.
- **Select pose.** GHF's closed the game with `pose_select=false`. Still open; it may get fixed by the normalisation.
- **Retargeting the donor's animations** onto SB skeletons (XGHF with 44 bones): hip height; see the memory [[b3hd-port-height]].
- **`#RPT` (belt physics):** B3 does not have it; the belt strip will stay static.

## 8. What to validate in game (when the user can)

1. The current port unchanged (as a reference): do GHF's hits connect, deal normal damage and have their effects?
2. After step 3: P/K combos, ki blasts, the 4 specials and the ultimate, the grab (P+G), hyper mode with its Dragon Rush, and the damage versus Adult Gohan.
3. Impact sounds and yells.
4. The SSJ transformation.
5. The select pose with its own animation.

## 9. Open questions

- Which costume or form goes with `BCGHFM1.amb`? SB2's ELF character table is not located; the candidate tables are at `0x1a3ef8` and `0x1b9d54` of `sb2_boot.elf`.
- What do `AC_<XXX>.spx` (24 slots, about 7 KB) and `EV_AC<XXX>*.spx` do? Probably events or cameras of SB's ultimates.
- Exact semantics of w4 0x10/0x40 and w6 0x100 in SB ("aura" state?).
- Is the SPX natives translator worth it? It would recover SB's scripts, including the cinematic ultimates.
- Super Dragon Ball Heroes World Mission includes `BCGHF.bsk`, `BCGHFM1.bsk` and `BCGHFM3.bsk` (same `#BSK` v4 family). It could serve as an extra oracle (not analysed).

---

## Appendix: scripts and data (in this folder)

None of them write into the project.

| File | Use |
|---|---|
| `sbafs.py` | Reader of the PSP AFS (with names) inside the ISO. `python sbafs.py sb2 data_btl_cmn.afs [dump i out]` |
| `ambtree.py` | Tree of an LE `#AMB` |
| `src.py` | Loads the SB movesets (`sb_char`) and the B3 GH ones (`b3_char`, data_cmn + `roster_db.json`) |
| `corpus.py` | Cache of all movesets (SB AMMs already decompressed) in `corpus2.pkl` in the exploration work folder. `corpus.pkl` in that same folder is an old undecompressed cache, no longer used. |
| `oracle_ghf.py` | Proof that `ghf_365/367` are the byte-for-byte repack of `BCGHF.amb` |
| `posematch.py`, `animmatch.py` (+ `animmatch.log`, `code_votes.json`) | Pose matching of animations and SB → B3 code votes |
| `globalmap2.py` (+ `global_map_sb1/2.json`) | Global store SB → B3 |
| `enginemap.py` (+ `engine_map.json`) | Stable table of engine codes |
| `apstats.py`, `apdump.py`, `t1hit.py`, `subblk.py`, `hrcols.py` | Format of AP lines, HR and sub-blocks (20 / 16 B) |
| `pairhits.py`, `dmgscale.py` | Matched hits and damage scale |
| `bcmstats.py`, `bcmpairs.py` | BCM fields SB versus B3 |
| `spxslots.py`, `spxbuiltins.py` (+ `spx_builtins.txt`), `spxalign.py`, `spxmap.py` | SPX slots and native renumbering |
| `t7pairs.py` (+ `t7_maps.json`) | Effects, sounds and yells tables SB → B3 |
| `*.amb`, `*.spx`, `b3_bsp_*.bin`, `sb2_boot.elf` | Working copies extracted for inspection (12 MB) |
