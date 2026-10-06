# Archive of old PortForge versions

History of the entries that have gone through the 1-click installer
(`../.forge.json`). **PortForge only reads `../.forge.json`**, so this
directory does not affect installation: it is a record so retired entries are
not lost.

- `forge-versions-old.json` — retired entries, ready to copy/paste back into
  the `builds` array of `../.forge.json`.
- `_retired` (inside the JSON) — the reason each version was retired.

## Current state (2026-10-04)

Versions **visible** in PortForge (the last three working ones):

| Version | Notes |
|---|---|
| `1.4.0` | Current (Latest). Default. In-game quick menu (F1 / Back+Start), new F3 FPS panel, live video and "More FPS with FSR", redesigned launcher with controller support (starts in <1 s), new characters and importer (they need the extracted folder: PortForge installs in ISO mode). |
| `1.3.0` | Repair installation, button labels (Xbox/PS/Switch), DRED by default, `gamecontrollerdb.txt`, texture extractor fix (#13), launcher polish and optimisation. Immediate fallback. |
| `1.2.9` | Self-explanatory diagnostics: sustained-fps, slow-disk and mixed-installation warnings; `vram=`/`lim=` in the `perf` line; VRAM guard. |

**Archived**: `1.2.8.2`, `1.2.8.1`, `1.2.8`, `1.2.7`, `1.2.5`, `1.2.6`, `1.2.4-EX`, `1.2.4`, `1.2.3`, `1.2.2-EX`, `1.2.2` (retired), `1.2.1`, `1.1.4`, `1.1.2`.

## How to bring a version back

1. Open `forge-versions-old.json` and copy that version's `builds` object.
2. Paste it into the `builds` array of `../.forge.json` (the order is the list
   order; the first entry is the one offered by default together with
   `defaultVersion`).
3. Check that the `releases/download/<tag>/...` URL answers 200.

> Note: versions marked **DO NOT REUSE** in `_retired` fail or are
> incompatible with the current layout; do not bring them back without fixing
> them.
