# Technique cameras: `#ACC` (HD) / `#AMC` (PS2)

RE from 2026-10-06 (exploration `docs/07_ports/GOHAN_FUTURO_EXPLORACION_2026-10-06/05_studio`).
Code: `mod center hd/studio/studio_core.py` (reading, writing, validation, glTF).
Checked: the **633 clips** of the 38 characters, in HD and in PS2, decode and
re-encode **byte for byte** (`python studio_core.py selftest`).

## Where it is

Each character has a **CAM bin** in `data_cmn.afs` (column `cam` of
`mod center hd/roster_db.json`; Goku = 288). It is an `#AMB` with 4 children:

| Child | Type | Contents |
|---|---|---|
| `#ACC` (PS2 `#AMC`) | 5 | **camera clips** (this document) |
| `#ACL` | 6 | 5-byte stub |
| `#CCM` (PS2 `#BCM`) | 0xFFFFFFFF | combo and input table (see `CAPSULAS_B3.md`) |
| `#SPX` | 8 | technique **scripts** (virtual machine; little-endian in HD too) |

- HD = big-endian; PS2 = little-endian. The `#ACC` goes from one to the other
  by byte-swapping 32-bit words.
- Alignment of the `#AMB`'s children: 32 B in HD, 16 B in PS2. PS2 does not
  pad the end.

## `#ACC` format

```
+0x00 "#ACC"   +0x04 0x20   +0x0C 2
+0x10 n_clips  +0x14 table (0x20)  +0x18 1 (n_bones)  +0x1C 0
table (0x20): n_clips × 16 B  [flags 0x1D][variant 0][n_frames][clip offset]
clip (aligned to 8): 4 pointers (offsets from the start of the #ACC) -> 4 tracks
track: [u32 0][u32 1][u32 n_keys] + keys
   eye, target : [u32 frame][f32 x][f32 y][f32 z]     (16 B per key)
   roll, fov   : [u32 frame][f32 value in radians]    (8 B per key)
end of the #ACC aligned to 8
```

| Track | What it is | Range in game |
|---|---|---|
| eye | camera position | — |
| target | **aim point** (not a rotation: the community guide calls it "rotation") | eye-target distance 3.5–1058 (median 32.7) |
| roll | camera rotation about its view axis | −π..π (median 0) |
| fov | vertical field of view | 0.066–1.306 rad (3.8°–74.8°, median 37.8°) |

- **Time:** 1 frame = 1/60 s. The last key of each track is at
  `n_frames − 1` (633 of 633).
- **Interpolation:** linear. Normally 1 key per frame; there are sparse clips
  (Zarbon: 46 keys for 80 frames) and 2-key tracks (fixed roll and fov).
- **Space:** Y up, model units, centred on the attacker (Goku's target in clip
  0 is (0; 10.5; 0), chest height). **Still to confirm in game** where the
  opponent is and whether there is left/right mirroring.
- Future Gohan (SB2) brings no clips: its `#ACC` is an empty stub.

## How the `#SPX` script requests clips

```
pad -> #CCM -> attack code -> #CSK (AP lines) -> HR hit type 3 + slot
      -> #SPX slot -> subroutine:  CAMERA_CLIP(0, g[0x60]+K, 0, 0.5, 0, 0, 0)   builtin 0xA7
                                   wait N frames                                push N; call sub 0
```

- `#SPX` header: `+0x14` = code base (0x74 in almost all), `+0x18` = n slots,
  `+0x20` = slot table (u32 relative to the base; 0xFFFFFFFF = empty).
- Safe opcodes: `08 10/20/30` push 8/16/32 bits, `09 30` push float,
  `08 5c 60` global variable 0x60, `01 10/20/30` + `02 80 02` builtin call,
  `01 30` + `02 73 02` subroutine call, `12 10 n` pop, `0b` end of statement.
- The clip index is usually **relative**: `g[0x60] + K`. Each technique sets
  the base; the Studio **estimates** it by comparing each clip's duration with
  its wait, and it can be changed.
- Slots: 0 = hyper mode / ultimate (32 of 38 characters), 20 = throw (38 of
  38), 10 in 5 characters.
- **Editing the script is not safe yet** (incomplete VM). Only clips are
  edited; if a clip lasts longer than the script's wait, it is cut; if
  shorter, the camera stays on its last frame.

## Camera mods

| Character | Where the edited camera goes |
|---|---|
| Native (Goku, Vegeta…) | `mods/studio_<character>/us/data_cmn.afs/<CAM fid>/geom.bin` |
| Port or new character | the `camara.bin` of its source mod (mounted by `roster_build` when PLAY is pressed) |

Rules for the native override (applied by `studio_core.save_native`):
1. LZX `xbcompress /N:2048` (never `/N:32`).
2. **Zero padding up to a reserved size**: `max(slot's to_read, LZX + 64 KB)`,
   rounded to 0x1000. It is stored in `studio.json` (`reservado`) and every
   later version is written with that same size. That way the AFS virtual
   table (which the runtime computes once per session) stays valid and the
   camera can be **reloaded without restarting** (Pause → "Re-select
   characters").
3. If an edit does not fit in the reservation, the reservation is enlarged
   and the **game must be restarted**. The first time the mod is created too
   (the mod list is read at startup).
4. The entry's folder may hold only **one file** (the runtime serves the
   first): backups go to `mods/<mod>/respaldo/<date>/`, never inside `us/`.
5. `studio.json` stores the edited clips (complete keys): it is the source of
   truth and allows regenerating the bin.

Validation before writing (if it fails, nothing is written): increasing
frames, last key at `n_frames − 1`, finite values, fov 0.05–2.5 rad, roll
−π..π, eye and target more than 0.1 apart, and **no clips are deleted** (the
script requests them by number; they are only appended at the end).

## glTF (Blender or another 3D program)

- Export: camera node with translation = eye, rotation = looking from the eye
  to the target with the roll (glTF camera: looks down −Z, Y up) and `yfov`
  animated with `KHR_animation_pointer` (Blender ≥ 4.2). A per-frame copy of
  the fov in `extras.fov_rad_por_frame`. Optional: the character with its
  skeleton and an animation from the moveset.
- Import: the camera is sampled at 60 fps; the **target** is rebuilt at the
  distance the clip had (glTF stores no aim point) and the roll comes from
  the orientation.
- Round trip through Blender 5.2.1 without touching anything: error ≤ 0.00002
  units. With the camera moved +5 in X inside Blender, it arrives exactly +5
  in X.
