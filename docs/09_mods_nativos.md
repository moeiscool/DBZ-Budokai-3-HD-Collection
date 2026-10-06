# Native mods

Native mods change the game's progress or behaviour. They are a different
category from the AFS mods for models, textures, audio and movesets.

## Initial catalogue

The launcher already reserves the catalogue for:

- `Save at 100%`: items, techniques and permanent content.
- `Infinite health`: the player's health during fights.
- `Infinite ki`: the player's ki during fights.

These candidates appear as **Under investigation** until their implementation
is validated on the Xbox 360/ReXGlue version. PS2 GameShark offsets are not
applied directly: those codes patch the PS2's MIPS memory and are neither save
offsets nor PowerPC guest offsets.

## Xenia research

Xenia Canary keeps a separate patch repository:

- `xenia-canary/game-patches`
- Format: `patches/<TITLE_ID> - <name>.patch.toml`
- Entries contain `be8`, `be16`, `be32`, `be64`, `array`, `f32`, `f64` or
  string writes at guest addresses.

This project's game has Title ID `4E4D0856`. A search of the official
repository finds no `4E4D0856` entry and no Budokai 3 patch. The Dragon Ball
entries found are for *Burst Limit* (`424107DC`) and are not reusable.

The ReXGlue used by this project does not include Xenia Canary's `patch.toml`
reader either. The original Xenia also has a different XEX patch mechanism
(`default.xexp`), but that is not a cheat and cannot be copied directly into
this project's dual codegen.

That is why `Infinite health` and `Infinite ki` appear as **No code found**.
There is currently no "turn on this cheat and you get everything" instruction
we could honestly recommend for this port.

The Xenia route is still viable as a format reference: if a patch for
`4E4D0856` is found, its writes would have to be converted into hooks/changes
of the recompiled guest, checked on US and EU, and wrapped in a native mod of
our own.

## Saves

The runtime stores the game's content under `user_data/dbz3/`, with a profile
folder, title id, content type and package name. The observed progress file is
`DBZ3/data.bin` and starts with `#SPF 1.0`.

Before implementing a modifier, differential saves of the port must be
obtained: new game, buying a capsule, buying a technique, unlocking a
character and a complete save. That way flags and checksums can be identified
without assuming the PS2 format is reusable.

The launcher detects recognisable `data.bin` files and lets you create a
`data.bin.native.bak` copy. The backup comes before any future transformer and
does not modify the original save.

## Safety rule

A native mod will not be considered ready until it:

1. Creates an automatic backup.
2. Validates the save's format and region.
3. Writes atomically.
4. Lets you restore the previous copy.
5. Is checked so the game loads, saves and reads the progress back.

For memory cheats, in addition:

6. The patch must match Title ID `4E4D0856`, the exact XEX hash/version and the
   correct region.
7. It must be tested in guest memory; a PS2 address or another Xenia game's
   address is no good.
