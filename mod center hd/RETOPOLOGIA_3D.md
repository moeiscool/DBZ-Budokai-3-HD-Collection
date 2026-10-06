# mod center hd — 3D retopology guide (the community's route)

> Updated 2026-08-14. Binary conversion between skeletons with different poses
> is NOT viable (90-180° rotations between games). The community uses **manual
> 3D retopology** with Blender. This document consolidates the pipeline.
>
> **⚠️ UPDATED 17/08**: for swaps BETWEEN HD GAMES (B1↔B3) retopology is **no
> longer necessary** — the runtime draws the complete `#AWO` bin as it is
> (without validating counts). Port = convert seals + material + AZT and
> install the complete bin (B1 lesson 9). **See `GUIA_SWAPS_Y_PORTS.md`.** This
> guide remains as a secondary route (editing existing meshes).

---

## 1. WHY RETOPOLOGY IS THE ROUTE

Verified repeatedly:
- **Injection into slots** (v3/v21): shows the host's topology (Krillin),
  never the new character. The IB (topology) belongs to the host.
- **Re-layout with its own IB** (v20): crash. The B3 guest requires fixed counts.
- **Binary retargeting** (v16-v19): shear/deformation from 90-180° rotations
  between skeletons (SDBH vs KLL).
- **The community ports SDBH/B1/B2/IW→B3 PS2 with manual retopology**:
  EMD→FBX→Blender (re-rig to the target skeleton)→OBJ→AMG.

## 2. RETOPOLOGY PIPELINE (validated)

```
1. SDBH WM (EMD/ESK) → FBX          emdfbx.exe -ExportAscii (LibXenoverse)
2. FBX → Blender 2.78                plugin FBXImporterExporterFromBlender2.78
3. In Blender: re-rig the model      to the Budokai skeleton (KLL labels),
   paint weights per bone, align the pose
4. Export OBJ                         (vertices V + normals VN + UVs VT)
5. OBJ → PS2 mesh parts (AMG)         OBJ to AMG v0.92 (Nexus-sama)
6. AMG → pack PS2 AMB                 Budokai AMB Packer-Unpacker
7. (optional) re-layout to HD         OUR pipeline (awo_tools)
```

### HD PIPELINE (our tools, `mod center hd\`)

```
1. Extract HD Krillin to OBJ:         python awg_to_obj.py <e326.bin> <b327_ps2.bin> krillin.obj
   (1956 verts, world space, ready for Blender)
2. Extract the source model to OBJ:   python json_to_obj.py <model_v2.json> android18.obj
   (SDBH Android 18, 1682 verts, chibi height 1.75)
3. Blender: import krillin.obj + android18.obj,
   SCALE android18 to krillin's height (x7.25 approx),
   overlay and re-rig Android 18's shape onto Krillin's skeleton
   (keep 1956 verts! only move world positions)
4. Re-import into the HD bin:         python obj_to_awg.py <e326.bin> <b327_ps2.bin> krillin_editado.obj salida.amb
5. LZX-compress + install as a mod    (xbcompress /N:2048 + build_afs)
```

**CRITICAL**: the edited OBJ must keep EXACTLY 1956 vertices (those of
Krillin's sec34). The user moves the vertices' world positions in Blender so
they take Android 18's shape, but does NOT add/remove vertices. The importer
rewrites the local positions (inv(mat_world[bone]) * world).

## 3. KEY TOOLS (and where they are)

| Tool | Path | Function |
|---|---|---|
| `emdfbx.exe` | `modding resources\EmdFbx-and-FbxEmd-LibXenoverse` | EMD→FBX |
| `fbxemd.exe` | same | FBX→EMD |
| Blender 2.78 plugin | same `FBXImporterExporterFromBlender2.78` | Import/export FBX |
| `OBJ to AMG v0.92` | `mod center\OBJ to AMG v0.92` (source code.zip) | OBJ→PS2 mesh parts |
| `AMG to OBJ V2` | `modding resources discord\tools\AMG_to_OBJ_V2.zip` | PS2 mesh parts→OBJ |
| `Model Rig Toolset V0.6` | `mod center\Model Rig Toolset V0.6` (Source) | Rig extractor/remover |
| `Bone Addition Tool v1.02` | `mod center\Bone Addition Tool v1.02` (.py) | Add bones |
| `Model Merger Tool` | `mod center\Model Merger Tool` (Source) | Merge models |
| `AMBStudio` | `mod center\AMBStudio` | AMB editor |
| `Budokai Model Editor Preview` | `mod center\Budokai Model Editor Preview` | Visual editor |

## 4. WHAT WE LEARNED FOR THE HD RE-LAYOUT

OBJ to AMG generates PS2 mesh parts by expanding vertices per triangle (48 B:
V+VN+VT) with binary templates. For HD (AWG) the layout is stride 44:
`[nan,u,v,z,x,y,weight,bone@28,nz,-ny,nx]`.

**Key to the skin→mesh mapping** (Model-Rig Extractor v0.9): each bone's rig
has `ch_loc`/`sb_loc` → blocks with the vertex's OFFSET. This resolves 100% of
the body (our SkinData only covered 49-76%).

## 5. REVERSE ENGINEERING OF THE 3D FORMAT (for future ports)

- **HD AWO**: header 0x30 (bones, amg_count, table, labels) + AWG0 (sec34
  stride 44 + vb2 + IB) + mesh group (mesh-ref blocks + arms). See
  `awo_tools\AWO_FORMAT.md`.
- **B3 vertex**: `[nan,u,v,z_local,x_local,y_local,weight,bone@28,nz,-ny,nx]`.
  sec34 ONLY uses bones 0-35 (legs 38-49 go into the static vb2).
- **Fixed counts**: the B3 guest requires sec34=1956, vb2=226, IB=5140.
  Changing them breaks parsing (crash).
- **Mesh-ref blocks**: at AWG0+0x1ED8 (13×0x50). The shadow ones (seal 0x204)
  define IB limits in bytes. Remapping them with different counts → crash.
