# Babidi session — PS2 source validation — 2026-09-08

## Result

The phase did not get as far as generating geometry or a mod. The selected
entry is not a PS2 source compatible with the extractor.

| File | Entry | Decompressed result |
|---|---:|---|
| `ps2_games/Budokai 3 Greatest Hits (USA)/USR/data_cmn.afs` | 96 | `#AMB` + `#AWO` + `#AWG` + `#AZT`, big-endian |
| `ps2_games/Budokai 2 (USA)/USR/data_cmn.afs` | 282 | `#AMB` + `#AWO` + `#AWG`, big-endian |

The extractor `port_ps2_b3_extract.py` expected little-endian `#AMO0/#AMG` and
failed when interpreting HD offsets as PS2 pointers. Explicit detection was
added so it aborts with a clear message instead of producing a buffer
traceback.

## Conclusion

- Babidi's PS2 rig cannot be verified from these AFS files yet.
- No JSON, bin or mod was generated.
- An `#AWO` entry must not be treated as if it were `#AMO0` by swapping
  endianness: they are different layouts.
- Next step: locate a real PS2 source (`#AMO0/#AMG`) or recover the documented
  PS2 reference bins (`b327_ps2.bin`, etc.).
