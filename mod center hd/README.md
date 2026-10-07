# mod center hd — Tools for the PS2→HD pipeline (Budokai 3 HD Collection)

> Folder created on 14/08/2026. Goal: refactor and improve the community's
> tools (which are primitive and PS2-specific) for the HD target (Xbox 360 /
> ReXGlue).
>
> **UPDATED 2026-09-08 — READ `GUIA_SWAPS_Y_PORTS.md` FIRST.** The sibling
> project B1 validated that model swaps work by **installing the complete bin**
> (the runtime does NOT validate fixed counts): the geom+tex pair of the SAME
> character, with correct bin seals. 3D retopology and binary reconstruction
> (v20/v22) have been **superseded**.

---

## 1. WHY THIS FOLDER EXISTS

The tools in `mod center hd\` are **primitive Python 2/3 scripts** (tkinter,
15-20 KB, no error handling, hardcoded to a specific format) or **old compiled
binaries** (2006-2018). The community uses them for the **PS2** format
(AMO/AMG/AMT), which is solved.

**This project's goal is the HD format (360/AWO/AWG/AZT)**, which the
community's tools do NOT cover. This folder holds the refactored and adapted
tools.

---

## 2. PORT VIABILITY VERDICT (research 14/08/2026)

**Porting between games IS VIABLE** (contrary to how it looked):

1. **The community ports SDBH WM / B1 / B2 / IW → B3 PS2 successfully**. SDBH
   WM's EMD format uses the SAME skeleton as Budokai (labels `waist`,
   `llegrot`, `stmc`, `chest`, `neck`, `head`...). Verified: Android 18's
   `bc18gb00.esk` → direct mapping to KLL bones (28 bones).

2. **The correct pipeline** (what the community does, not "slot injection"):
   ```
   Source model (EMD/OBJ/FBX)
     → convert to PS2 mesh parts (AMG) WITH a rebuilt IB    [EMD to AMG / OBJ to AMG]
     → pack a PS2 AMB (#AMO0 + #AMT)                        [AMB Packer]
     → (NEW) re-layout to HD (#AWO + #AZT)                  [OUR pipeline]
   ```

3. **⚠️ UPDATE 17/08 (from the B1 project)**: for swaps BETWEEN HD GAMES
   (B1↔B3 and within each one) retopology and reconstruction are NO longer
   needed. The runtime draws the complete `#AWO` bin as it is (mesh group,
   IB, bones, UVs) without validating the slot's counts. **Port = convert
   seals + material + AZT, and install the complete bin.** See
   `GUIA_SWAPS_Y_PORTS.md`. 3D retopology (original README §2.3-§4 and
   `RETOPOLOGIA_3D.md`) remains a secondary route.

4. **The PS2→360 jump is a RE-LAYOUT** (endianness + renamed magics +
   re-layout of mesh groups), not a different format. Documented in AWO_FORMAT.md.

---

## 3. KEY TOOLS (source) and their state

| Tool | State | Comment |
|---|---|---|
| `EMD to AMG v0.90` (mod center) | 🔬 primitive | 15 KB Python script with a tkinter UI. Converts EMD→PS2 mesh part. Rebuilds the mesh part from binary templates. |
| `OBJ to AMG v0.92` (mod center) | 🔬 primitive | 10 KB Python script. OBJ→PS2 mesh part. |
| `EmdFbx-and-FbxEmd-LibXenoverse` (modding resources) | ✅ works | emdfbx.exe converts EMD→binary FBX (3 MB). fbxemd reverses it. Blender 2.78 plugin included. |
| `Model-Rig_Extractor_v0.9.py` (discord tools) | 🔬 key | Documents the skin→mesh mapping (ch_loc/sb_loc → vertex offsets). |
| `B3-IW AMO Converter + Shadows` (mod center) | ✅ community | B3/IW→B1 PS2 (re-layout of mesh-part headers). |
| `AFS Toolset`, `AMB Packer-Unpacker` | ✅ | Packing. |
| `xbcompress/xbdecompress` (XDK) | ✅ | LZX compression /N:2048. |

## 4. PROPOSED HD PIPELINE (goal)

```
1. Source model: SDBH WM EMD / Xenoverse / B1/B2/IW PS2 / OBJ
2. Convert to PS2 mesh parts with a real IB    (EMD to AMG / OBJ to AMG)
3. (optional) Edit in Blender via FBX          (EmdFbx + Blender 2.78 plugin)
4. Re-layout to HD #AWO                        (OUR build_awo / build_janemba2)
   - header + bone zones + mesh group + arms
   - sec34 (stride 44: [nan,u,v,z,x,y,weight,bone,nz,-ny,nx])
   - vb2 (static, 0xFFFFFFFF)
   - rebuilt IB
5. Pack the AMB (#AWO + #AZT)                  (build_janemba2)
6. LZX-compress /N:2048                         (xbcompress)
7. Install as a mod (per-entry override)       (build_afs)
```

## 5. FILES IN THIS FOLDER

- `GUIA_SWAPS_Y_PORTS.md` — **READ FIRST (17/08)**: the principle of swaps,
  real state (B1→B1 ✅, B3→B1 ✅, B3→B3 pending), step-by-step pipeline,
  tool diagnosis and B3 roadmap.
- `awg_to_obj.py` — **FIXED 17/08**: exports an HD `#AWO`/`#AMB` to OBJ in
  world space (offsets `+0x28..+0x34`, v10+ vertex layout). Verified with B3
  Gero (2501 verts, 1814 faces).
- `obj_to_awg.py` — inverse of awg_to_obj (retopology; needs the same
  offsets/layout fix; secondary route).
- `emd_to_awo_hd.py` — v1: parsing of ESK (SDBH WM skeleton) + bone mapping to
  KLL (28 verified mappings). Phase 2 pending: complete EMD parsing.
- `build_awo_v20/v22.py`, `build_awo_from_json.py`, `inject_a18*.py`,
  `empaquetar_v20.py` — **experimental/archivable** (fixed-count, retopology
  and injection routes; do not use as a deliverable). See GUIA_SWAPS_Y_PORTS.md §6.
- `tools_manifest.json` + `tools_manifest_check.py` — curated inventory of HD
  tools, bridges and references; the checker neither runs tools nor modifies
  assets.
- `EMD_NOTAS.txt` — Xenoverse EMD format (big-endian, header, model at 0x100).

> These tools run on the PC. On the **PS5** build, ready-made mods are copied
> to `/data/dbz3/mods/` (see `docs/PS5.md`).
