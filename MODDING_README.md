# DBZ Budokai 3 HD Collection — Mods and toolkit

This package includes the **modding toolkit** (`mod center hd/`) next to the
executable, so the launcher's **Model Swap** and **Textures** work directly,
with no extra steps.

## What it includes

- `mod center hd/swap_b3.py` — native B3 HD -> B3 HD model swap.
- `mod center hd/texture_b3.py` — texture extraction/rebuild (PNG).
- `mod center hd/catalog_b3.cat` — catalogue of B3's 183 characters.
- `mod center hd/tools/` — xbcompress/xbdecompress (the game's LZX compression)
  and their DLLs (MSVCR71/MSVCP71/xbdm).

These scripts need **Python** installed on the system (`python` on the PATH,
or the `DBZ3_PYTHON` variable pointing at the interpreter). The texture mod
also needs the `Pillow` and `numpy` libraries (`pip install pillow numpy`).

## Model Swap / Textures from the launcher

1. Run `dbz3.exe` and go to the **Model Swap** or **Textures** tab.
2. Choose the source character and the target slot.
3. Press the button. The mod is generated in `mods/` and enabled by itself.

## How to install a downloaded mod

Mods are folders inside `mods/` (next to `dbz3.exe`), each with its own
`manifest.txt`:

```
mods/
└── my_mod/
    ├── manifest.txt          # metadata (name, description, author...)
    ├── .disabled             # if present, the mod is disabled
    └── us/
        └── data_cmn.afs/
            └── 327/
                └── geom.bin  # override of one AFS entry
```

To install a mod:
1. Open the launcher's **Mods** tab and press **"Open mods folder"**
   (it creates `mods/` if missing and opens it in Explorer).
2. Copy your mod's folder there (or unzip its ZIP).
3. The launcher lists it automatically; enable it with its checkbox.

> Music mods (og_music) replace whole files:
> `mods/<mod>/us/adx_usa.afs`, `us/opening.sfd`, etc.

On **PS5** there is no launcher: copy the mod folders to `/data/dbz3/mods/` on
the console (same layout; a `.disabled` file turns a mod off). See
`docs/PS5.md`.

## New characters (v1.4.0)

The launcher's **New characters** tab adds characters in their own select
cells, without replacing anyone (experimental; USA version and data in a
folder). There are two optional downloads:

- **`DBZ3HD-1.4.0-Personajes.zip`** ([Google Drive](https://drive.google.com/file/d/1zpwuuU7ITKZlC43nsTbp6s2wceBcwO85/view?usp=sharing)) — Janemba, Android 19, Zarbon, Dodoria,
  Guldo, Jeice and Burter, ready to play. Copy the ZIP's `mods` folder next to
  `dbz3.exe` (accept merging folders), open the launcher and press **PLAY**.
  To remove one, untick it in **New characters → Installed**.
- **`DBZ3HD-1.4.1-Kit-Modding.zip`** — the tools to create and **import**
  characters (Budokai 1, Budokai 2, Infinite World and community models),
  capsules, voices and shouts. Copy all of its contents next to `dbz3.exe`,
  install Python 3.11+ and run `instalar_requisitos.bat` once (it installs
  numpy, Pillow and scipy). Then: **New characters → Import character from
  another game**.

Your saved games are never touched.

## About the tools

The package's toolkit is the subset **needed at runtime** (swap and
textures). The new-character tools are in the **Modding Kit** (separate
download). The GitHub repository has the rest of the research/RE tools in
`mod center hd` and `awo_tools`, if you want to dig deeper.
