# Shin Budokai 1/2 (PSP) movesets compared with Budokai 3

RE from 2026-10-06 (exploration `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/01_moveset`,
oracle adult Gohan: SB2's `BCGHL` against B3's ID 4). Converter: `awo_tools/sbport.py`
(tables in `awo_tools/sb_tablas.py`); the importer calls it (`importar.py importar sb2 GHF …`).

Same engine as B3 (`#AMB` v3, `#BSK` v4, `#AMM` v2, `#BCM`, `#SPX 0.01`) with
different layouts inside. Copying SB's children as they are (as the community
port `ghf_365/367` does) **does not work**: B3 reads hits, damage and effects
misaligned from the 2nd line on.

## Where the data is (PSP ISO, `USRDIR/data_btl_cmn.afs`, with 48-byte names)

| File | Contents |
|---|---|
| `BC<XXX>.amb` | moveset: `#AMB` [empty AMC, SPX, BCM, BSK, —, own AMM, AMM 2 (victim), AMM 3] |
| `BC<XXX>B0n.amb` | models (forms or costumes): [`#AMO`, `#AMT`, `#RPT` (belt physics)] |
| `BC<XXX>M<n>.amb` | the same moveset + a 2nd `#BSK` that redefines individual codes for one form |
| `BSP_<XXX>.amb` | technique effects (`#AME` of another version: 0x00020000, header 0x40) |
| `BCCMN.AMB` | common: global AMM (265 animations) |

Three-letter codes: GOK, VGT, PIC, KLL, GHM, GHL, **GHF**, TRX, TRF, FRZ, CEL,
COO, BRL, 18G, BUS, BUL, BUM, BDK, DBR, GGT, VTO, GTX, JNB, PKH (SB2 has 24;
SB1, 18). Super Dragon Ball Heroes World Mission uses the same ones
(`model/bc<xxx>/bc<xxx>bNN`).

## Differences and how they are converted

| Part | Shin Budokai | Budokai 3 | Conversion |
|---|---|---|---|
| AP lines (`#BSK`) | **20 B** | **16 B** | copy `[0:16]`; in hit lines (type 1) the box changes: radius +11 → +12, position 3 × s16 at +12/14/16 → 3 × s8 at +13/14/15 |
| HR blocks | **160 B** (8 × 20) | **128 B** (8 × 16) | truncate each line to 16 B |
| Damage | — | **0.85 × SB** (median of 8,847 hits; 0.71–1.0 depending on the character) | multiply by 0.85 (`--dano`) |
| 48-byte sub-block | bits 0x80/0x100/0x200 at +0x10 | never above 0x7F | remove the bits |
| Engine codes | ground 0x000–0x1FF, air **+0x200** | ground 0x000–0x0FF, air **+0x100** | per-animation matched table (`ENGINE_SB`) |
| BCM attacks | **0x4xx** ground / **0x6xx** air | **0x2xx** / **0x3xx** | keep the offset; whatever collides goes to a free gap (pair +0x100) |
| Transformation | 0x500 / 0x700 (down+E, costs 4000 ki) | **0x2E0 / 0x3E0** (P+K+G) | SB's is removed; the donor's P+K+G (`transformacion = "donante"`) |
| Throw | BASE **0x800** | BASE **0x480** | the donor's (with its victim in AMM 2) |
| Hyper mode, Dragon Rush, cinematic ultimate | do not exist | 0x259, 0x280…, SPX slot 0 | grafted from the donor |
| Global store (common anims) | 265, different index | 359 | 206 match by pose at 0.0° (`sb_tablas.GLOBAL`); the rest are copied into the own AMM |
| Own AMM | compressed, 8-byte table | 16-byte table | `sb_amm.py`; 74–90 % of the animations are identical to B3's |
| AP type 7 (effects) | classes 0–11+ | classes 0–9 | class 0 equal in 97 %; 1 sound, 2 spark, 3 shout: majority tables; 4 = link to the BSP; 10 (SB's SPX slot) and 11+: removed |
| BCM: directions | 0x10 (↑) and 0x20 (↓) | do not exist | ↑+E ultimate → P+K+G+E in hyper; normal ↑ → P+K; ↓ → K+G |
| BCM: ki | specials 1000, ultimates 5000 | 0 (the cost is in the capsule) | set 0 and move the cost to the capsule |
| BCM: aura variants | w6 0x8000 / w3 0x7530 / w6 0x100 | do not exist | removed |
| BCM: cond 4 | melee special | **transform** | 4 → 2 (special) |
| `#SPX` | native functions **renumbered** | — | the donor's SPX is used (and its `#AMC`: SB's ultimates have no camera of their own; they are made with the Studio) |
| `#AMC` cameras | empty (32 B) | ~26 clips | the donor's |
| Belt physics | `#RPT` in the model | per-model table in the XEX | `fisica = "donante"` (see `FORMAS_Y_KI.md`) |

## Checks (without the game)

- `python awo_tools/sbport.py --oraculo --juego sb2`: converts SB2's GHL and
  compares it with B3's adult Gohan.
- `python awo_tools/sbport.py --prueba`: self-test without an ISO.
- Every conversion ends with `comprobacion: OK` (every engine code covered, no
  20-byte lines, valid store indices). If not, the importer uses the donor's
  hits and says so.

## Still to confirm in game

Hits and damage against adult Gohan, throw, hyper and Dragon Rush; converted
↑/↓ inputs; which form `BC<XXX>M<n>` uses; sounds and shouts by table.
