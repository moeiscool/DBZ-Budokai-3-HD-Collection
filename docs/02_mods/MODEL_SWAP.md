# MODEL SWAP — Complete research

> Updated: 2026-08-14. What we know, what fails, and what the community's
> documentation says about how the model swap was done in the original B3.
>
> **Later outcome (2026-09-10):** the native HD↔HD swap works when the
> **complete** bin of a character is installed (see
> `docs/07_ports/SESION_SWAP_NATIVO_2026-09-10.md`). This document records the
> research as of 2026-08-14.

---

## SUMMARY

The **model swap** (putting one character's model in another's slot) is the
goal. Current state: **the override mechanism works** (the bin is served
whole), but **the guest crashes when processing another character's bin**.
The research is still open.

---

## 1. WHAT WE KNOW WORKS

| Technique | Result |
|---|---|
| Replacing Krillin's bin with **the same bin** (afstest) | ✅ Loads perfectly |
| **Texture** mod (#AZT only) | ✅ Works |
| **Per-entry override** (mechanism) | ✅ The bin is served whole |
| Replacing the bin with **another character's** (Goten→Krillin) | 🔴 Crashes |
| Injecting **another character's body** into the slots (Goten body→Krillin) | 🔴 Crashes |

> The key conclusion: the guest does NOT simply accept another character's
> bin. The problem is NOT the mechanism, it is the bin's CONTENT/structure.

---

## 2. WHAT THE COMMUNITY'S DOCUMENTATION SAYS

### 2.1 LGBT Method (Lean's Ginyu Bodyswap Technique) — `modding resources discord\tutorials\LGBT_Method.zip`

The community's method for bodyswaps in B3 PS2:

1. **They NEVER replace the character's complete bin**.
2. They identify which **axes** are needed: for legs `WAIST STMC RLEGROT RLEG1 RLEG2 RFOOT1 RFOOT2 LLEGROT LLEG1 LLEG2 LFOOT1 LFOOT2`; for the body `WAIST CHEST STMC RCHN RARMROT...`.
3. They locate those axes' **model parts** in the donor.
4. They copy the parts into the recipient, adjusting offsets and pointers.
5. They adjust the texture/shader.

**Lesson**: the swap is selective by axes, not the whole bin.

### 2.2 Tutorial "Add AMG manually" (JaromSc) — `modding resources update 2\Tutorial #1 Añadir AMG manualmente`

1. Copy the donor's AMG (mesh part) → paste it at the end of the base model.
2. Edit the **file length** and the **part count** in the header.
3. Copy the **bone names** (from "Body" to the last one).
4. Find the target **bone's offset** (e.g. NH=0x1E) and replace its pointer
   with the location of the new AMG.
5. Assign the texture and shader.

**Lesson**: adding a part means adjusting: length, part count, bone pointers,
texture/shader.

### 2.3 The community has NO PS2→HD converter

- All the community's tooling (OBJ to AMG, Model Rig Toolset, AMO Decompiler)
  works with the **PS2 (#AMO0 LE)** format.
- The HD format (#AWO BE) is edited with 010 Editor + the `B3_AMB_PS3.bt` template.
- The PS2→HD jump is a **re-layout** (endianness + magics + offset table), not
  a different format. Documented in AWO_FORMAT.md.

---

## 3. WHAT WE HAVE VERIFIED BY RE

### 3.1 HD bin structure (with the B3_AMB_PS3.bt template)

```
AMB: #AMB + entry table (loc+size)
  entry0: #AWO (model)
  entry1: #AZT (textures)

AWO: +0x10 numberOfBones, +0x14 ptrConnections, +0x18 numberOfAWGs,
     +0x1C pointerAWGoffsets, +0x24 ptrBoneNames,
     +0x30 AWOunk[bones](32B) → bone zones, + AWGptr table + BoneNames

AWG (per mesh group): +0x10 numberOfBones, +0x14 rigging_data_ptr,
     +0x1C ptrBones, +0x24 unk_Count(80B blocks), +0x28 ptrVertexBlock,
     +0x2C VertexBlockSize, +0x30 ptrFaceData, +0x34 FaceDataSize,
     +0x38 unk_ptr_28, +0x3C sizeOfunk_ptr_28
```

### 3.2 Krillin vs Goten comparison (both HD, same game)

| | Krillin (entry 327) | Goten (entry 298) |
|---|---|---|
| Bones | 51 | 56 |
| AWGs | 18 | 21 |
| AWG0 (body) | vb=2190, face=233 | vb=2035, face=225 |
| Fingers | 10 (L01-L10 L/R) | 12 (L01-L38 L/R) |
| Faces | 7 (L01-L23) | 8 (L01-L41 S00) |
| Labels | KLL_*/XKLL_* | GTN_*/XGTN_* |

**Conclusion**: almost identical structure (same pattern), they differ in
counts and labels. A humanoid from the same game should be compatible... but
it crashes.

### 3.3 The HD vertex (stride 44)

```
+00 nan (flag)  +04 u  +08 v
+12 z_local     +16 x_local   +20 y_local
+24 weight      +28 BONE(u32)  +32 nz  +36 -ny  +40 nx
```

### 3.4 The 3 override fixes (critical)

See [02_mods/COMO_HACER_MODS.md](COMO_HACER_MODS.md). Summary:
1. The hook must support folders (ported from B1).
2. `/N:2048` compression (not /N:32).
3. Padding to the slot's exact size.

---

## 4. CRASH HYPOTHESES (to investigate)

Having confirmed that the override works and the bin is served whole, the
crash when loading another character's bin could be due to:

| Hypothesis | Explanation | How to verify it |
|---|---|---|
| **A. The guest validates labels/counts** | Krillin's moveset/animations reference KLL_* bones by index; Goten's bin uses GTN_* | Compare how the guest indexes bones |
| **B. The guest uses the slot's mesh group** | Slot 327 expects a certain structure of mesh-ref blocks | Instrument the guest's parser |
| **C. The crash is in another field** | Some internal AWG offset does not match | Instrument the guest |

### 4.1 Confirmed: the crash is NOT from LZX truncation (2026-08-14)

The last `goten_body` test (Goten's body in Krillin, LZX `/N:2048`, padding to
106496) showed in the logs:
```
AFS MOD READ: bin 327 mod_off=0x0 to_read=106496 got=106496 mod_size=106496
UNHANDLED EXCEPTION: Code=0xC0000005 Addr=0x7ff7bdfe87ee
```
→ The bin was served **whole** (got=106496, the complete LZX) and it still
  crashed.
→ The crash is about the **bin's content** (the model's geometry/structure),
  not the override mechanism or the compression.

### 4.2 Finding: the rigData differs between characters (2026-08-14)

Comparing the `rigData` (pose matrices) of Krillin's AWG0 vs Goten's:

| Bone | Krillin | Goten |
|---|---|---|
| bone 2 | scale=(0, 0, 0) | scale=(-0.7071, -0.7071, 0) |
| bone 5 | pos=(-0.33, 0, 0.52) | pos=(2.30, 0, 0) |

→ **Each character has its own rigData** (bone position/rotation/scale).
→ The guest of slot 327 expects Krillin's skeleton. Goten's bin brings another
  rig → mismatch → crash.
→ **The model swap is NOT copying geometry**: the donor's geometry has to be
  transformed into the recipient's skeleton SPACE
  (`local_donor → world → local_recipient`).
→ This invalidates the earlier assumption of "identical world matrices" (that
  was only for the SAME character PS2 vs HD).

---

## 5. NEXT STEPS (real RE of the guest)

The community's documentation does NOT document the whole-bin swap between B3
characters (they never did it). To move forward we need **reverse engineering
of the guest's parser**, which lives in `generated/dbz3_recomp.*.cpp`:

1. **Locate the function that parses bin 327** in the recompiled guest code
   (the crash addr `0x7ff7...` points there).
2. **Instrument**: log which offsets the guest reads from the bin (as we did
   with `AFS327 READ` but at the model-parsing level).
3. **Compare** the parsing flow of the original bin vs Goten's bin: see exactly
   which field causes the crash.

### Tools available for this RE
- `awo_tools/awg_to_obj_b3.py` — recommended exporter to check B3 HD bins
- `awo_tools/awg0_export.py` — AWG0 exporter with A/C auto-detection
- `awo_tools/analyze_bin_hd.py` — historical PS3 parser, obsolete
- `generated/dbz3_recomp.*.cpp` — recompiled guest code (the real parser)
- `rexglue-sdk-0.10/` — instrumentable runtime (C++), where the hook lives
- Tracy profiling (build `win-amd64-tracy`)
- `mod center hd/` — HD tools we have created

---

## 6. REFERENCES

- `AWO_FORMAT.md` (root) — complete AFS/AFL/LZX/#AMB/#AWO format
- `modding resources discord\tutorials\LGBT_Method.zip` — bodyswap method
- `modding resources update 2\Tutorial #1 Añadir AMG manualmente` — adding an AMG
- `modding resources discord\research\B3_AMB_PS3.bt` — 010 template of the format
- `modding resources discord\research\00000002-00000002-b3.AMO.json` — aerithdevs intermediate format
- `mod center\OBJ to AMG v0.92` — OBJ→AMG PS2 pipeline
- `mod center\Model Rig Toolset V0.6` — PS2 rig
