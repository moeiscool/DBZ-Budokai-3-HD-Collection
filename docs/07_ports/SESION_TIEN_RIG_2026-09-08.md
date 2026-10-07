# Tien with cape session — PS2 rig against HD Tenshinhan — 2026-09-08

## Source

```text
modding resources update 2/MOD EJEMPLO/Tien With Cape/IW/Tien (With Cape).amo
```

The file starts with `#AMO0` and the real PS2 extractor works.

```text
PS2: base=0x0 n_bones=52 parts=15 verts=4565 skinned=3346
```

Temporary extraction JSON:

```text
C:\Users\javie\AppData\Local\Temp\opencode\ps2_candidates\tien_with_cape.json
```

## HD template

```text
us/data_cmn.afs entry 400
root label: TSH_BODY
AWG: first HD Tenshinhan group
HD bones: 42
```

## Comparison

- All 42 HD Tenshinhan labels exist in the PS2 source.
- The 42 common labels keep exactly the same order.
- PS2 adds 10 cape labels: `XTSH_MANT*`, `XTSH_RMANT`, `XTSH_LMANT`.
- No HD labels are missing from PS2.
- Verdict: **passes the 1:1 base rig**.

## Technical decision

This candidate is much better than Krillin for validating the full port:

1. Keep HD Tenshinhan as the structural template.
2. Convert only the geometry of the 42 common bones first.
3. Isolate the cape as a second experiment; do not mix it into the first
   diagnosis.
4. Check the OBJ and bounds before packing.
5. Install temporarily over Krillin, slot 327, with a single active mod.

No HD bin or playable mod has been generated yet.
