# User mods

This folder is empty and reserved for user-built mods. Mods live in
`mods/<name>/` and override AFS entries without touching the original game
files:

```
mods/<mod>/us/data_cmn.afs/<entry>/geom.bin   # override of one AFS entry
mods/<mod>/.disabled                          # if present, the mod is OFF
```

Manage mods visually in the launcher (Mods tab) or with `mod center hd/`.
See `docs/02_mods/` for the full guide.

On **PS5** the same layout is used under `/data/dbz3/mods/` on the console
(see `docs/PS5.md`).

## Example: original (OG) music mod

To replace the music with the game's **original soundtrack (OG)**, create a mod
that replaces the audio files per region. Just place the files in the mod's
matching folder:

```
mods/<mod>/us/adx_jpn.afs   # JPN audio for the USA region
mods/<mod>/us/adx_usa.afs   # USA audio for the USA region
mods/<mod>/us/opening.sfd   # opening (if you replace it)
mods/<mod>/us/Ending00.sfd  # ending
mods/<mod>/eu/adx_jpn.afs   # same structure for the EU/PAL region
mods/<mod>/eu/adx_usa.afs
```

The whole-file override (`.afs`, `.sfd`) is applied per region without
touching the originals. A reference mod is `og_music` (validated end to end).
Enable/disable it from the launcher's **Mods** tab.
