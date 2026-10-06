# Budokai 3 HD (US) capsules — format and use for the new characters

RE from 2026-10-04 (US image, `default.xex`). It only describes structures; it
contains no game data. Code: `mod center hd/capsulas.py`,
`mod center hd/roster_build.py` (class `Capsules`) and `src/roster_ext.cpp`.

## The `#SKC` catalogue (data_usi 4; on PS2 `skill.ska`, `#SKA`, little-endian)

A 0x20-byte header (`+0x10` n = 596, `+0x14` start = 0x20) and n records of
40 B (BE in HD). The capsule ID is the record's index.

| Offset | Type | Meaning |
|---|---|---|
| +0 | u64 | owners: bit k = character ID k (0–63). Common items = bits 0–43 |
| +8 | u8 | class: 0x11 ability/transformation, 0x21 attack, 0x17 fusion/awakening, 0x00 derived (appears when something is met: X10 Kamehameha…) |
| +10 | u8 | rarity (high nibble 0–3) |
| +14 | u8 | mask of the forms it can be used from |
| +15 | u8 | cost / level |
| +16 | u32 | required capsule (SSJ2 needs SSJ…) |
| +20..+35 | | effect (items) / attack number; +30 u16 replacement type, +32 base capsule |
| +38 | u16 | price / 100 |

In memory: the game loads the `#SKC` at 0x824A60E8 and uses it through two
pointers, `0x82375608` (header) and `0x8237560C` (records). Several menu
routines loop up to 595/596 with fixed constants; combat indexes by direct ID.

## Where the capsule ID is used

- **Default list** ("Original" custom): `char96` (0x8234ABB8 + 96·ID) `+80`
  u16 n, `+82` 7 × u16.
- **Transformations**: `char372` (0x82329CF0 + 372·ID) `+0xD0` u32 number of
  forms, `+212 + 20·form` u16 = the capsule that form requires (`+214` = the ID
  whose model it loads).
- **Hits**: the character's 64-byte block of the `#CCM` (BCM), word 8 (u16
  `+16`). In HD word 4 is the special's type and word 5 the condition (in the
  PS2 `#BCM` they are swapped): 0x0400 hyper mode, 0x0004 transform, 0x0008
  ultimate, 0x0002 special with a capsule, 0x0001 costs ki; 0x8000 / 0x4000 are
  from Infinite World (see below).
- **Names in the menus**: data_usi 2663 (short) and 2684 (long), `#AZT`
  indexed by ID. Per character: a u16 table at 0x82373D68 → the data_usi entry
  with the names of its capsules (`#AZT`, header `+0x18` = first ID).
- **Ability sheet** (the pause list and the capsule's caption when used in a
  fight): data_usi 5–52 (`SCM<code>.amb`: `#AZT` name + condition per capsule
  and a `#CFC` with the button glyphs; 16-byte rows: u32 capsule, `0xFFFFFFFF`
  = transform). The game picks it with the 16-byte table at 0x82324468 (ID,
  costumes, HUD face in data_cmn, index; ends at ID −1) → record
  `0x82373A00[index + 1]` (u32 fid, u16 attacks ptr, u16 transformations ptr,
  count, count). `sub_820E6D70` reads it when the fight starts and
  `sub_821B5FC0` loads it.

## Inventory, "Custom" list and "Edit Skills" (RE 2026-10-04, second part)

- **Inventory** (u8 = how many you own, per capsule ID): the save in memory at
  0x824BA110 `+0x2AFE9`, **2048 B** (the game only uses 1..594, but the save
  stores 2048: new capsules fit without changing the format). The selection
  works on a copy (the player's save block, pointer in the player state
  `+120`): `+1094` inventory (2048 B), `+68` "Custom" lists. Copy there/back:
  `sub_82179C20` / `sub_82179880` (by pointer).
- **"Custom" list** = 7 × s16 per **select cell** (38): save 0x824BA110 `+4928`
  + 4624·cell; in the copy, `+68 + 14·cell`. `0xFFFF` = empty.
- **Select menu** "Normal / Custom / Edit Skills" (per player). Editor state:
  `*0x8247971C + 460·player + 68`: `+28` ID, `+32` slots used, `+36` tab
  (record `+10 & 3`), `+44` pointer to the inventory, `+76 + 28·tab` block (`+0`
  scroll, `+4` cursor, `+8` 9 × u16 visible, `+26` total), `+188` equipped list
  (u32 n + 7 u32).
  - `sub_821B6ED8` (visible) and `sub_821B6FE8` (total and cursor): a fixed
    loop over 594 capsules.
  - `sub_821B7290` loads a list into the editor and drops those ≥ 595.
  - `sub_821B7C50` draws the tray and skips those ≥ 595. The name is requested
    by `sub_82146430` (r3 sprite, `+24` texture; r4 #AZT bank, r5 ID).
  - `sub_821B8470` says whether a capsule can be equipped (0 yes, 1 already
    there, 2 no slots…).
  - `sub_821B8FC8` draws the character's face with the u8 table
    `0x82373D38[ID]` (44 entries, `0xFF` for the cut ones): with a cut ID or
    ≥ 44 → null pointer and a **crash** (it affected every new character).
  - The description panel (`sub_821BB680`) loads data_usi `2079 + ID` and is
    only requested for ID < 595.
- **Before the fight in mode 5** (`cfg +2018`), `sub_820FE3D8` cleans the
  selection's lists and deletes those ≥ 595. In Versus and Practice it is not
  called.

## Health-bar face (`*_HUD.amt`)

data_cmn (US 452–503), chosen by the sheet table 0x82324468 `+8`. It is an
`#AZT` with **one texture per form**: DDS 256 × 128 A8R8G8B8, a useful area of
192 × 120 HD px (128 × 80 logical). Measured on the official ones:
- a render of the model with a fixed camera (~30 px per unit), almost
  front-on and slightly from above;
- head centre at x = 91 and chin at y = 85;
- alpha 205, shoulders cut by an ellipse and the last 4 rows blended;
- a diffuse blue halo (48, 137, 192), with σ ≈ 11 px.

It is generated by `model_render.make_hud` (`roster_build.hud_bin`), or
`ui/hud.png` is used.

## What the runtime does (`src/roster_ext.cpp`)

- Copies the catalogue to its own memory with the new capsules (`[[capsula]]`
  in `roster.toml`, IDs ≥ 596), adds the owner bits of the inherited ones and
  of the common items for IDs 44–63, and moves the two pointers. It is done as
  soon as the `#SKC` is in memory (startup, select or fight).
- Writes the default list (`capsulas`) and each form's capsule
  (`capsulas_forma`).
- Sheets: adds the new characters' entries to the table at 0x82324468 only
  while `sub_820E6D70` runs; their own sheets (index ≥ 1000) are served
  through slot 1 of 0x82373A00 while `sub_821B5FC0` loads them.
- "Edit Skills" with the whole catalogue:
  - `sub_821B6ED8` and `sub_821B6FE8` are rewritten to loop to the end of the
    catalogue.
  - `sub_821B7290` rebuilds the equipped list.
  - In `sub_821B7C50` (tray) and `sub_820FE3D8` (mode 5), each new capsule
    uses a borrowed ID < 595 during the call, with the record swapped.
    `sub_82146430` requests the name with the real ID.
  - In `sub_821B8FC8` the new characters use their donor's face.
- New capsules count as yours: the copy's inventory goes to 1 if it was 0.
  They are not needed in the shop.
- Each new character's own "Custom" list:
  - `select_ext.cpp` swaps it with the host cell's while the player is
    processed.
  - If edited, it is saved in `mods/capsulas_custom.txt`; otherwise it uses
    its Normal list.
  - While swapped, the dump to the save (`sub_82179880`) receives the host's.
  - Before, "Edit Skills" with a new character changed the host's Custom list
    and crashed (see the face, above).
- Extra places 44–63: `char96`/`char372`/aura/BSP/HUD have 105 entries (64–104
  are fusions and fight forms) and 44–63 are empty in all of them; the unlock
  mask is a u64. The select's framing table (0x82372950) ends at 44 → hook of
  `sub_8217FF20`; ID → slot (0x82020668) too → hook of `sub_82159A88` (answers
  the host cell). IDs without a name record get one (`nombre`).

> These hooks use US guest addresses: they are compiled only into builds with
> the US codegen (PC dual/US cores and the US PS5 build).

## Infinite World ports

IW has no hyper mode: its BCM carries an "aura burst" (button B, condition
0x4000), specials carry an IW capsule with slot 1/2 (condition 0x8001) and the
ultimate is ^E without a capsule (0x8009). `capsulas.adapt_iw_bcm()`:

1. "aura burst" → B3's hyper mode entry (P+K+G+E, 0x0400) — on the pad, LT / L2.
2. Hyper mode is triggered by its attack code's animation, whose properties
   (AP) in the `#CSK` set the state: the donor's hyper block is grafted (all of
   B3's use the common animation of bank 3 with the same AP) into the
   converted entry's codes (`csk_graft`). Validated in game: the stage darkens
   and the state holds.
3. Specials → condition 0x0002 with the character's new capsules, in order;
   ultimate → P+K+G+E in hyper mode (0x000A) with its capsule. IW's ki cost is
   kept for the sheet's text.

## Declaring it in a mod (`personaje.toml`)

```toml
[[capsula]]
nombre = "Hell Gate"
tipo = "especial"          # especial | definitiva | transformacion
[[capsula]]
nombre = "Monster Transformation"
tipo = "transformacion"
forma = 1                  # the form it leads to (1 = the first transformation)
```

**Importing a port's capsules** (`roster_build.py capsulas --mod X --importar [auto|iw|b1|b2|b3]`,
or the launcher's "Bring the capsules from its game" button):
- Reads the port's BCM and creates one `[[capsula]]` per hit that requires a
  capsule, with `reemplaza` = the original ID.
- Names:
  - IW: per character, from the sheet `Dragon Ball Z Infinite World Capsule
    List.xlsx` (the IDs in IW's BCM do not match that sheet's).
  - B3: the list `Budokai_3_Capsules_IDs.txt`.
  - Any game: your own "ID: Name" list with `--lista`.
- B1/B2 types: the `#SKA` catalogue from `Budokai 1 and Budokai 2 Capsule Data`
  (28-byte LE records; `+4` class, 0x11 = transformation).
- B3 port: its capsules already exist and go to `capsulas_nativas`.
- If there were capsules already, `personaje.toml.antes_de_importar` is saved.

Without `[[capsula]]` the character uses the donor's (sheet included). With
its own capsules: specials/ultimates replace the donor's in order (or are
bound to a port's hits), and a transformation replaces that form's capsule.
Also from the launcher (New characters → editor → "Capsules") or
`roster_build.py capsulas --mod X --anadir "Name" especial`.

## Pending

- The face in the "Edit Skills" header is the donor's (select sprite table).
- The description panel of a new capsule does not show (data_usi `2079 + ID`
  does not exist for ID ≥ 596).
- Effects of capsules that are not attacks (green/yellow items) for new
  characters.
- B1/B2 names: there is no list in the resources; the importer puts
  "Special 1…" unless given one with `--lista`.
