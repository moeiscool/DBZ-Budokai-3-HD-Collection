# 01_WEB — Web research: porting PS2 models → B3 HD Collection (360) and the problem of the 16 face AWGs (bones 48–63)

> Date: 2026-09-10. Author: technical researcher (opencode).
> Goal: gather EVERYTHING public that could help to (a) convert/port Budokai
> PS2 models (`#AMO0`/`#AMG`, LE) to the 360 HD (`#AMB`/`#AWO`/`#AWG`, BE), (b)
> understand the HD Collection's vertex/AWG/AWO format, (c) know the Budokai
> modding community, (d) mesh retargeting techniques between different rigs and
> (e) any mention of Cell (Semi-Perfect) in Budokai HD mods.
>
> **Scope warning**: the project's code was not touched. Everything is external
> research. Each URL carries a usefulness rating (**High / Medium / Low /
> None**) and why.
>
> (Later corrections: the "16 face AWGs" are 10 hands + 6 face; the "positional
> consumption" was a tool bug; B3 HD skins on the CPU — see AGENTS §3.4.)

---

## 0. EXECUTIVE SUMMARY (what really matters)

1. **There is NO public tool that converts `#AWO`/`#AWG` (HD 360) ↔
   `#AMO0`/`#AMG` (PS2).** There is no parser, wiki or Noesis plugin for the
   360 HD format. The project is literally at the frontier of what is public.
   This reframes the search: what is useful is not "the converter that already
   exists" (it does not) but (a) PS2 tools that produce clean geometry and
   bones, (b) generic references for PS3/X360-era vertex/skinning layouts, and
   (c) mesh retargeting tools.
2. **The most actionable finding**: the "matrix palette" skinning references
   (NVIDIA) include the **"Vertex Offset Method"**: vertices are stored *in the
   bone's local space*, with **up to 4 offset positions per vertex** and the
   pool is consumed **sequentially as offsets**, not only through the index
   buffer. This **fits the empirical observation** that the guest consumes the
   pool **positionally** even though the IB is consistent (tests T4/T5/T7). It
   is the most promising RE hypothesis the web provides.
3. **The PS3 port (`gnome41/dbz-budokai-hd`) shows that the HD uses Sony's
   EDGE library (geometry on SPU) + RSX/cellGcm**, not a Dimps pipeline of its
   own. That explains why the vertex format is "odd" (per-bone blocks prepared
   for batching/EDGE). The PS3 port is the best cross-cutting RE clue (same
   pipeline as 360, different endianness/GPU).
4. **Most valuable PS2 tool**: `SamuelDBZMAAM/Budokai-Modding-Tool` (Python) —
   it has **AMB combiner**, **AMG Creator/Addition**, **AMO0 Editor/Creator**,
   **"Removing face AMGs"** modules and a model part editor. It is exactly the
   problem's domain: separating/adding AMGs (incl. the face AMGs) inside an
   AMO0. Its sources (`amo_s.py`, `amg_a.py`, `amg_c.py`) document concrete
   offsets of the PS2 format.
5. **The PS2 extraction ecosystem is well covered** (QuickBMS
   `DragonballBin/AMO/AMG`, killercracker's maxscript for 3ds Max,
   Szkaradek123's AMO unpacker + AMG importer for Blender 2.49). Recurring
   limitation: **they do not import weights/rigging well** ("figured out bones
   but not the rigging"). Good for geometry and scales, not for full skinning.
6. **Communities**: the strong ecosystem is *Budokai Tenkaichi*'s (Sparking),
   not classic Budokai's. There is a "Budokai Modding Community" and hubs on
   GameBanana, but the public technical documentation of the format is
   scarce/closed (mostly Discord).
7. **Cell (Semi-Perfect)**: NO concrete public "Cell Semi-Perfect" mod was
   found for the HD Collection. Only tangential mentions (aura editing mixing
   "Cell Super Perfect" with "SSJ2 Gohan" in the PS2 modding tool; Cell 2nd Form
   exists as a playable form via absorption in Budokai 3). Low priority as a
   source of information.

---

## 1. TOOLS / REPOS FOR CONVERTING OR PORTING BUDOKAI MODELS

### 1.1 Direct HD 360 ↔ PS2 conversion
**Conclusion: it does not exist.** Searches done: "Budokai 3 AWO format",
"Budokai HD model swap", "AMO converter", "PS2 to Xbox360 Budokai model",
"GitHub Budokai HD .amb", etc. There is no repository, forum or plugin that
reads/writes `#AWO`/`#AWG`.

| URL | Usefulness | Notes |
|---|---|---|
| (none) | — | No HD↔PS2 converter was found. |

### 1.2 PS3 recompilation port (same game, other platform) — **HIGH**
- `https://github.com/gnome41/dbz-budokai-hd` — **Static recompilation port of
  the PS3 HD Collection (BLES01658)** on `ps3recomp`. It describes asset loading
  (`LAUNCH/data.afs`), the generic `#A3T` texture decoder, and (very important)
  that the geometry is processed by **Sony's EDGE library on the SPUs**. The
  repo's `CLAUDE.md` is a treatise on RE of the game's startup. **Value: High**
  to understand the HD content pipeline; it does **not** document the vertex
  layout, but gives the context of why the format has that structure.
- `https://github.com/sp00nznet/ps3recomp` — the PS3 PPU→C++ recompilation SDK
  the former is based on. Runtime/HLE reference. **Value: Medium** (context,
  not format).

### 1.3 PS2 modding tools (origin of the data) — **HIGH**
- `https://github.com/SamuelDBZMAAM/Budokai-Modding-Tool` — **The most relevant
  tool of the PS2 ecosystem.** Python. Modules: `amb_c.py` (AMB Combiner),
  `amg_a.py` (AMG Addition), `amg_c.py` (AMG Creator), `amo_a.py` (AMO
  Addition), `amo_s.py` (splits an AMO into one AMG per part), `amo_lgbt.py`
  ("LGBT" merge), `m_p_e.py` (Model Part Editor), Budokai 1 / Shin Budokai
  importers/exporters. The README explicitly mentions **"Removing face AMGs"**
  and creating new AMGs: the same problem as the HD's 16 face AWGs.
  **Value: High** (reusable PS2 format logic and offsets).
- `https://github.com/SamuelDBZMAAM/DBZ-Budokai-3-Modding-Tool` — An earlier
  version/effort by the same author. `B3 Mod Tool.py`, example `amb.bin`.
  Mentions shaders, auras and AMT. **Value: Medium-High**.
- `https://github.com/SamuelDBZMAAM/Budokai-Modding-Tool/blob/master/amo_s.py`
  — **Key code**:
  - Detects parts with `chunk[0] == 0x01 and chunk[8] == 0x46`.
  - `mesh_size = (hex_to_int(hti) - 1610612736) * 16` (1610612736 =
    0x60000000).
  - AMG template offsets: writes at `84`, `116`, `144`, and the `amg_head`
    header.
  Useful to understand how an AMO0 is "cut" into independent AMGs. **Value:
  High**.
- `https://steamcommunity.com/sharedfiles/filedetails?id=1570869204` and
  `https://steamcommunity.com/sharedfiles/filedetails?id=2941023657` — Workshop
  guides documenting the **Budokai 1–3 model rip** pipeline step by step.
  **Value: Medium**.
- `https://www.youtube.com/watch?v=jUArVyOAn7s` — "Modding Tutorial - Blender
  Model Editing for Budokai 3" (video, from the tool author's circle). **Value:
  Medium**.

### 1.4 Classic PS2 extraction chain (QuickBMS/3ds Max/Blender) — **MEDIUM**
- `https://archive.vg-resource.com/thread-29785-post-622917.html` (The VG
  Resource, "Budokai 3" thread, 2016) — Full rip tutorial: Noesis + AFS Explorer
  + Game Graphic Studio + 3ds Max + QuickBMS. Scripts: `2DragonballBin.bms`
  (decompresses bin→AMO/AMT), `3DragonballAMO.bms`, `4DragonballAMG.bms`.
  **killercracker**'s maxscript to import AMO **with bones, but without
  rigging** (`http://www.mediafire.com/download/bdi86yev83hzwm0/budokai_updated.ms`
  — old link, verify; probably dead). **Value: Medium-High** (PS2 pipeline).
- `https://zenhax.com/viewtopic.php@t=1950.html` — "Dragonball Z Budokai 1 PS2
  ?" (ZenHAX): scripts `3DragonballAMO.bms`, `4DragonballAMG.bms`,
  `DragonBallB1MeshFixed.bms` + a contribution by **Szkaradek123**: `.amo`
  unpacker + `.amg` importer for **Blender 2.49**, "**No weights**". **Value:
  Medium-High** (evidence that weights are the historical weak point).
- `https://github.com/DKDave/Scripts` — A huge collection of QuickBMS/Python/
  Noesis scripts by the author (ex-XeNTaX/ZenHAX). I did not confirm a Budokai
  script, but it is the reference repository to find/upload parsers for odd
  formats. **Value: Medium**.
- `https://github.com/MatrixDJ96/DBZBT3` — AFL-Converter + AFS-Manager
  ("successor to AFSExplorer without crashes"). It is for **Budokai Tenkaichi
  3**, but the AFS/AFL container tools are reusable. **Value: Medium**.
- `https://github.com/hopesgit/Budokai3AP` — Archipelago (randomizer) for PS2
  Budokai 3; warns that it "will never work with the PS3/360 HD version".
  Useful only to confirm build differences. **Value: Low**.

### 1.5 Recompilation of the sister game — **LOW (context)**
- `https://github.com/WistfulHopes/DBZ1` — "Dragon Ball Z Budokai HD
  Recompiled" (ReXGlue SDK), 123 stars. Minimal repo (2 commits, no docs), but
  it is the same pipeline and may have useful issues. **Value: Low-Medium**.

---

## 2. REVERSE ENGINEERING OF THE HD #AWG / #AWO FORMAT

### 2.1 Public state: practically non-existent
There is no wiki, XeNTaX/ResHax thread or Noesis plugin dedicated to the HD
Collection's `#AWO`/`#AWG`/`#AMB`. The documentation that exists is **private**
(Discords, modders' internal tools). The closest public source is the PS2 tool
(§1.3) for the **original** format.

### 2.2 References for the HD graphics layer (PS3/X360) — **HIGH**
- `https://github.com/FBobDev/PS3-recomp/blob/master/docs/RSX_GRAPHICS.md` —
  **Golden document** on the drawing pipeline of the PS3/360 era in these
  ports:
  - NV47xx FIFO format (header: type/count/subchannel/method).
  - **`rsx_vertex_formats.h`**: table of vertex attribute types → DXGI:
    `None(0)`, `S1=snorm16(1)`, `F=float32(2)`, `SF=float16(3)`,
    `UB=unorm8(4)`, `S32K=s16(5)`, `CMP=packed 11-11-10(6)`, `UB256=uint8(7)`.
  - Logging of `NV4097_SET_VERTEX_DATA_ARRAY_FORMAT` → type/size/stride/offset
    and `SET_BEGIN_END` with prologue `prim=5` (triangles) / `prim=6`
    (triangle strip).
  - **Value: High**: it is the canonical reference to read a PS3/X360 vertex
    declaration and map the attribute "type" seen in the HD bin (the per-AWG
    `format`s the project observes should fit S1/SF/UB/CMP).
  - The SDK's `runtime_glue.cpp`/`rsx_commands.c` also have vertex state,
    `SET_TRANSFORM_PROGRAM_LOAD`, etc.
- `https://github.com/gnome41/dbz-budokai-hd/blob/master/CLAUDE.md` —
  Confirms:
  - The game uses **EDGE (SPURS SPU geometry library)** for geometry, with MFC
    DMA LS→RSX.
  - Generic `#A3T` texture with a `CellGcmTexture` struct at `gcm_off+0x68`;
    formats R5G6B5 (0xA4/0x84) and A8R8G8B8 (0xA5/0x85); Morton (Z-order)
    swizzle when bit 5 of the format is clear.
  - **Value: High** as a mental map of the pipeline and as a mirror of the PS3
    version to compare with the 360 bins.
- `https://wiki.cloudmodding.com/zgcn/BMD_and_BDL` — GameCube BMD/BDL format
  (chunks INF1/VTX1/EVP1/DRW1/JNT1/SHP1). **Very useful conceptually**: it
  describes how an engine of the era separates *vertex data*, *skinning
  envelopes* (EVP1), the **"Draw Matrix Array" (DRW1)** and *matrix groups*
  (SHP1). The notion of DRW1 —a table of matrices that **references geometry by
  range/offset**— is exactly the pattern the project senses ("positional
  consumption of the pool" + "two descriptor tables"). **Value: High** (mental
  model of skinning/arms).
- `https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_020_Skins.md`
  — A clean skinning reference: `inverseBindMatrices`, `joints`, `WEIGHTS_0`,
  "bind shape matrix". Useful to formalise the per-bone pool maths. **Value:
  Medium**.

### 2.3 "Matrix palette" skinning and the **Vertex Offset Method** — **HIGH (key hypothesis)**
- `https://download.nvidia.com/developer/SDK/Individual_Samples/DEMOS/Direct3D9/src/HLSL_PaletteSkin/docs/HLSL_PaletteSkin.pdf`
  — Matrix-palette skinning: bone transforms in constant registers, **bone
  indices embedded in the vertex stream**, up to 4 bones/vertex, embedded
  weights.
- `https://developer.download.nvidia.com/assets/gamedev/docs/skinning.pdf`
  (Mesh Skinning, S. Dominé, GDC) — **The key document**: it describes the
  **"Vertex Offset Method"**:
  - Up to **12 matrices per primitive, 4 per vertex, 28 accessible**.
  - "Needs to send vertices in bone's space, i.e. **multiple versions of the
    same vertex, but each in the local bone space that the vertex is
    referencing**".
  - Per-vertex data: up to 4 *vertex offsets*, 4 *weights*, 4 *indices*, and
    per-bone normals/bi-normals/tangents.
  - **This fits exactly with**: (i) the sec34 layout has a **bone-local**
    position + weight + bone; (ii) tests T4/T5 (reordered pool, consistent IB)
    **deform** → there is positional/offset consumption; (iii) T6 (range A
    only) normal and T7 (inverted IB) massive → the IB rules connectivity but
    there is an additional path by offset.
  - **Value: High**: it is the best public explanation for the current
    blocker; it suggests looking in the AWG for a table of **offsets per
    bone/per primitive** (not just the IB and descriptor A).
- `https://developer.download.nvidia.com/assets/gamedev/docs/GDC2001_EfficientAnimation.pdf`
  — Comparison of skinning techniques (D3D7 vertex blend, fixed-function matrix
  palette, VS matrix palette) with the **address register `a0.x`** to index the
  palette. Context for why the engine stores "arms"/matrices and indexes them
  per vertex. **Value: Medium-High**.

### 2.4 Structure of the 360 game (to place the bins) — **MEDIUM**
- `https://archive.org` / 7z listing of the USA HD Collection (seen via
  `https://ia801903.us.archive.org/view_archive.php?...Dragon%20Ball%20Z%20-%20Budokai%20HD%20Collection%20(USA).7z`)
  — Build inventory: `default.xex` (3,317,760 B), `DBZ3/yae3_xenon.xex`
  (4,890,624 B), `DBZ3/us/data_cmn.afs` (293,423,104 B),
  `adx_jpn/data_usi/data_fra/data_spn/data_yah`, `lang_jpn/lang_usa`,
  `DBZ1/*`. **Value: Medium** (verifies sizes/structure; the project already
  has this).
- `https://gamefaqs.gamespot.com/xbox360/676304-dragon-ball-z-budokai-hd-collection/data`
  and `https://gamefaqs.gamespot.com/ps3/676303-dragon-ball-z-budokai-hd-collection/data`
  — release sheets (IDs, regions, date). **Value: Low**.
- `http://redump.org/disc/29970` — 360 dump data (regions, tracks). **Value:
  Low**.

---

## 3. BUDOKAI MODDING COMMUNITIES AND PUBLIC DOCUMENTATION

### 3.1 Where people are — **MEDIUM**
- `https://gamebanana.com/games/16989` — **"Dragon Ball Z: Budokai — Mods and
  Modding Resources by the Budokai Modding Community | Budokai Hub"**. Official
  hub of mods/tutorials of the Budokai saga (loads via JS; browse from the
  site). **Value: Medium-High** (entry point to the community and resources).
- `https://www.facebook.com/BudokaiCorp` — "Budokai Modding Community Discord"
  (a page that redistributes mods; link to a `discord.gg/feW` server in the
  snippet, probably expired). **Value: Medium**.
- `https://top.gg/discord/servers/542888166685040642` — **Tenkaichi Modding
  Community** (136 members). It is for *Budokai Tenkaichi* (Sparking), not
  classic Budokai, but it shares AFS/PS2 techniques and has EN/ES channels.
  **Value: Medium**.
- `https://discord.gg/9zT7NHP` — "Programming Discussions" cited in
  SamuelDBZMAAM's tool. **Value: Low**.
- `https://reshax.com/` — **Successor forum of XeNTaX** (the XeNTaX/ZenHAX
  threads are migrating here). It is WHERE to ask about the `#AWO` format.
  Examples of skeleton RE threads:
  `https://reshax.com/topic/18092-how-to-reverse-boneskeleton-file/` (how to
  infer the bone hierarchy from weights and matrices — very relevant to the
  skinning/arms problem). **Value: High** as an RE support channel.
- `https://archive.vg-resource.com/thread-29785-post-622917.html` — Historical
  The VG Resource thread with the whole PS2 tool chain (see §1.4). **Value:
  Medium-High**.

### 3.2 Public documentation of the vertex/extra bones/skinning format
**There is no public wiki of the `#AWO`/`#AWG`.** The closest:
- The PS2 Python tool (§1.3) with the AMO/AMG and face logic.
- PS2 threads on ZenHAX/ResHax (LE endianness, bones without rigging).
- `ps23dformat.wikispaces.com` (the old PS2 formats wiki, which had
  `Dragon+Ball+Z+Budokai+2`) is **DEAD**: today it redirects to
  `site-closed.wikispaces.com`. Only partial Wayback captures and the `.bms`
  that circulated remain. **Value: None (down)** — look for the `.bms` on
  mirrors (ResHax / archive.org) if needed.

---

## 4. MESH REORIENTATION TECHNIQUES / NEAREST POINT ON SURFACE PRESERVING TOPOLOGY

> Context of use: to get around the full port's structural blocker, the PS2
> geometry can be **transferred onto the HD template's topology/pool order**
> (keeping the pool order = Path A's constraint) using "topology transfer"
> tools instead of reordering the pool. This gives a PS2 silhouette with the HD
> connectivity/skinning intact.

### 4.1 Commercial / pro tools — **HIGH for the principle**
- **R3DS Wrap / Faceform Wrap** — Transfers the clean topology of a reference
  mesh to another (scan or mesh) via *landmarks*. It is THE standard for "put
  topology A on shape B".
  - `https://www.versluis.com/2021/11/r3ds-wrap` (explanatory article with a
    character case).
  - `https://www.cgchannel.com/2019/06/r3ds-ships-wrap-3-4` (release notes:
    BlendWrapping, etc.).
  - `https://texturing.xyz/pages/vface-docs-2-2-a-wrap-r3ds` (`Loadgeo` +
    `SelectPointPairs` node workflow, landmark selection). **Value: High**
    (reproducible process; paid).
- **Houdini — Topo Transfer** — "Non-rigidly deforms a surface to match the
  size and shape of a different surface". Topology retargeting with
  **landmarks** over two overlapping meshes.
  `https://www.sidefx.com/docs/houdini/nodes/sop/topotransfer.html`. **Value:
  High** (procedural, exports a deformed mesh; ideal for an offline bake).
- **Autodesk Maya — Mesh > Transfer Attributes** — Transfers UV/CPV/position
  between meshes of **different topology** ("spatially based", different
  vertex/edge counts).
  `https://download.autodesk.com/global/docs/maya2013/en_us/files/Mesh__Transfer_Attributes.htm`.
  **Value: Medium-High**.

### 4.2 Blender (free) — **HIGH**
- **Shrinkwrap Modifier** (Nearest Surface Point / Project / Nearest Vertex /
  Target Normal Project): moves each vertex to the nearest point of the target
  surface.
  `https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/shrinkwrap.html`.
  **Value: High** (native nearest point on surface).
- **Data Transfer** (Transfer Mesh Data): transfers **vertex groups (weights),
  UVs, colours, normals** between meshes with different topologies (1-to-1 or
  many-to-one interpolated mapping).
  `https://docs.blender.org/manual/en/2.80/modeling/meshes/editing/data_transfer.html`.
  **Value: High** (lets you fix the HD mesh and *bake* the PS2 shape/weights
  on top).
- A practical discussion of projecting weights from one mesh to another with
  Data Transfer:
  `https://blenderartists.org/t/project-weight-painting-from-one-mesh-to-another/1474243`.
  **Value: Medium**.
- **Mesh Data Transfer** (addon, Maurizio Memoli) — transfers shape/UV/shape
  keys/vertex groups without needing the same vertex count.
  `https://blender-addons.org/mesh-data-transfer-addon`. **Value: Medium**.
- **Import Export Skin Weights** (official extension, Nguyen-Phuc-Nguyen,
  2025) — exports/imports vertex weights to JSON using position or UV (works
  best with the same topology or the same UV).
  `https://extensions.blender.org/add-ons/import-export-skin-weights`.
  **Value: Medium-High** (useful to move weights between formats/templates via
  script).
- **Rigify Mesh Retargetter** (addon) — retargets weights from a metarig to DEF
  bones in Rigify. `https://github.com/cubedparadox/Rigify-Mesh-Retargetter-`.
  **Value: Low-Medium**.

### 4.3 Algorithms / papers — **MEDIUM**
- **Rig Retargeting for 3D Animation** (Poirier, 2009) — adapts complex
  skeletons to different meshes using *topology graphs* (Reeb graphs) and arc
  matching.
  `http://profs.etsmtl.ca/epaquette/Research/Papers/Poirier.2009/Poirier.2009.gi.pdf`.
  **Value: Medium** (skeleton↔mesh correspondence method; conceptual).
- **Motion2Motion: Cross-topology Motion Transfer with Sparse Correspondence**
  (arXiv 2508.13139) — animation transfer between very different topologies
  and **sparse bone correspondences** (`https://arxiv.org/html/2508.13139v1`).
  **Value: Low-Medium** (animation, not mesh retargeting; useful if animations
  are to be retargeted).
- **HuMoT** (arXiv 2305.18897) — topology-agnostic motion representation.
  `https://arxiv.org/html/2305.18897v3`. **Value: Low**.
- **Retopology Tools (3ds Max)** — QuadriFlow, target face count, sharp edges.
  `https://help.autodesk.com/cloudhelp/2025/ENU/3DSMax-Retopology/files/GUID-5A960813-FBCC-4A5D-A423-3FCD60825B10.html`.
  **Value: Low** (retopo, not transfer).
- **Industrial shrinkwrap** (HyperMesh/Altair, Rhino) — useful as a reference
  for the "loose/tight wrap" algorithm and feature preservation.
  `https://2023.help.altair.com/...` and `http://docs.mcneel.com/rhino/8/help/...`.
  **Value: Low** (engineering, not game meshes).

### 4.4 Engine weight/skinning references — **MEDIUM-HIGH**
- **PMX/MMD 2.0** (`https://gist.github.com/lordscales91/47ae1b7577e52a2babee`
  mirror) — a clear vertex spec: position/normal/UV, weight types
  `BDEF1/BDEF2/BDEF4/SDEF`, bone indices and weights. Useful as a template to
  *re-emit* skinning if the format is ever rebuilt. **Value: Medium**.
- **Unity BoneWeight**
  (`https://docs.unity3d.com/ScriptReference/BoneWeight.html`) — 4 weights
  sorted descending, sum = 1. A reminder of the normalisation the project
  validates. **Value: Low**.
- **DirectXTK VertexTypes**
  (`https://github.com/Microsoft/DirectXTK/wiki/VertexTypes`) — an example of a
  vertex decl with blend weights + indices (typical D3D format of the era).
  **Value: Low**.

---

## 5. CELL (SEMI-PERFECT) IN BUDOKAI HD MODS

**Conclusion: there is no documented public "Cell Semi-Perfect" mod for the HD
Collection.**

Tangential findings:
- `https://github.com/SamuelDBZMAAM/DBZ-Budokai-3-Modding-Tool` (README) — the
  "to be added" list mentions aura editing and gives as an example **"Cell's
  Super perfect aura mix with SSJ2 Gohan aura"**. That is, Cell appears as an
  *aura* use case, not a model/mesh one. **Value: Low** (but it confirms that
  Cell is a PS2 modding subject).
- `https://gamefaqs.gamespot.com/ps2/920505-dragon-ball-z-budokai-3/faqs/33828`
  and
  `https://gamefaqs.gamespot.com/ps2/939644-dragon-ball-z-budokai-tenkaichi-3/faqs/50979`
  — Confirm Cell's forms in Budokai 3: transformation by absorption
  (`#17 Absorption` → Perfect Form). **Semi-Perfect = "2nd Form"**; it does not
  appear as an independent slot/model in the asset listings. **Value: Low**
  (character design context).
- `https://dragonball.fandom.com/wiki/Dragon_Ball_Z:_Budokai_HD_Collection` —
  screenshots of "Cell in Budokai HD" (gallery), no technical data. **Value:
  Low**.
- `https://en.wikipedia.org/wiki/Cell_(Dragon_Ball)` /
  `https://simple.wikipedia.org/wiki/Cell_(Dragon_Ball)` — description of the
  Semi-Perfect form (no wings, more humanoid, boot-like feet, metal plate on the
  ankles). **Value: Low** (visual reference if the mesh is rebuilt).
- Project internal note (AGENTS.md §10): the best validated port is **Cell
  (F2)** with `cell_npm4` / `cell_npm_fix` / `cell_best`. The documented
  limitation is that HD Cell has **17 AWGs** (AWG0 body + 16 single-bone AWGs =
  48–63) and the PS2 only 48 bones. So the "Cell" work is a test case; there is
  no community mod that contributes.

---

## 6. SUMMARY TABLE OF RESOURCES BY USEFULNESS

### HIGH usefulness (read/incorporate now)
| Resource | URL |
|---|---|
| "Vertex Offset Method" skinning (positional-consumption hypothesis) | https://developer.download.nvidia.com/assets/gamedev/docs/skinning.pdf |
| Matrix-palette skinning (bone index/weights in the vertex stream) | https://download.nvidia.com/developer/SDK/Individual_Samples/DEMOS/Direct3D9/src/HLSL_PaletteSkin/docs/HLSL_PaletteSkin.pdf |
| RSX/PS3 vertex formats + FIFO + draw (vertex decl reference) | https://github.com/FBobDev/PS3-recomp/blob/master/docs/RSX_GRAPHICS.md |
| PS3 port of the HD (EDGE/SPU, #A3T, pipeline) | https://github.com/gnome41/dbz-budokai-hd |
| PS2 modding tool (face AMG, AMO0, offsets) | https://github.com/SamuelDBZMAAM/Budokai-Modding-Tool |
| Blender Shrinkwrap (nearest surface point) | https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/shrinkwrap.html |
| Blender Data Transfer (weights/UV between topologies) | https://docs.blender.org/manual/en/2.80/modeling/meshes/editing/data_transfer.html |
| BMD/BDL (DRW1 = matrix table referencing geometry by range) | https://wiki.cloudmodding.com/zgcn/BMD_and_BDL |
| PS2 tool: `amo_s.py` (AMG offsets) | https://github.com/SamuelDBZMAAM/Budokai-Modding-Tool/blob/master/amo_s.py |
| Houdini Topo Transfer | https://www.sidefx.com/docs/houdini/nodes/sop/topotransfer.html |
| RE forum (XeNTaX successor) to ask about the `#AWO` | https://reshax.com/ |

### MEDIUM usefulness
| Resource | URL |
|---|---|
| PS2 QuickBMS/3ds Max extraction chain | https://archive.vg-resource.com/thread-29785-post-622917.html |
| ZenHAX Budokai 1 (Blender 2.49, no weights) | https://zenhax.com/viewtopic.php@t=1950.html |
| GameBanana Budokai Hub | https://gamebanana.com/games/16989 |
| R3DS/Faceform Wrap | https://www.versluis.com/2021/11/r3ds-wrap |
| Maya Transfer Attributes | https://download.autodesk.com/global/docs/maya2013/en_us/files/Mesh__Transfer_Attributes.htm |
| glTF skins (inverse bind, joints, weights) | https://github.com/KhronosGroup/glTF-Tutorials/blob/main/gltfTutorial/gltfTutorial_020_Skins.md |
| Rig Retargeting (topology graphs) | http://profs.etsmtl.ca/epaquette/Research/Papers/Poirier.2009/Poirier.2009.gi.pdf |
| Import Export Skin Weights (Blender ext.) | https://extensions.blender.org/add-ons/import-export-skin-weights |
| DKDave/Scripts (QuickBMS/Noesis parsers) | https://github.com/DKDave/Scripts |
| DBZBT3 AFS tools | https://github.com/MatrixDJ96/DBZBT3 |
| Tenkaichi Modding Community (Discord) | https://top.gg/discord/servers/542888166685040642 |
| Budokai Modding Community (Facebook) | https://www.facebook.com/BudokaiCorp |
| Steam Budokai rip guides | https://steamcommunity.com/sharedfiles/filedetails?id=1570869204 |
| YouTube: Blender model editing Budokai 3 | https://www.youtube.com/watch?v=jUArVyOAn7s |
| Skeleton RE thread (inferring a hierarchy from weights) | https://reshax.com/topic/18092-how-to-reverse-boneskeleton-file/ |

### LOW / NO usefulness
- `ps23dformat.wikispaces.com` — **DEAD** (redirects to
  `site-closed.wikispaces.com`).
- `https://github.com/WistfulHopes/DBZ1` — context, no docs.
- Release sheets (GameFAQs/redump/GameTDB) — no format value.
- Animation retargeting papers (HuMoT, Motion2Motion) — tangential.
- Mentions of Cell in game guides — no technical value.

---

## 7. ACTIONABLE RECOMMENDATIONS (derived from the web)

1. **Look for the per-bone/per-primitive offset table in the AWG** (NVIDIA's
   "Vertex Offset Method" hypothesis). The project already ruled out descriptor
   A (T6) and the IB alone (T7). The next scan should look for **arrays of
   offsets/indices pointing to `sec34 + k*stride`** around the mesh group
   `0x1F80`/`0x2D49` (the "arms" `[bone, ptr, 0, ptr_matrix, 0]`), contrasting
   with NVIDIA's description (4 offsets/vertex in bone space).
2. **Mirror the PS3 port** (`gnome41/dbz-budokai-hd`): extract the PS3
   `data.afs` and compare the PS3 vs 360 model layout. If the pipeline is EDGE
   on both, the "arms"/batching structure should be analogous and RE of the
   EDGE code (even if it is SPU) may reveal how it consumes the pool.
3. **Use retargeting tools to keep the pool order** (Path A's constraint):
   Blender Shrinkwrap (Nearest Surface Point) + Data Transfer of UV/weights to
   *bake* the PS2 shape onto the HD topology, instead of reordering the pool
   (which is what blocks Path B). This turns the "reorder the pool" problem into
   "move vertices", which the guest does accept.
4. **Cannibalise the PS2 tool `SamuelDBZMAAM/Budokai-Modding-Tool`**: its AMG
   Creation/Addition and "Removing face AMGs" modules document how face AMGs are
   structured on PS2 (bones 33–40). That is the direct map to **remap by label
   PS2 bones 33–40 to the HD's AWGs 48–63** (goal stated in AGENTS.md §10).
5. **Ask on ResHax** (`https://reshax.com/`) about the HD Collection's
   `#AWO`/`#AWG` format, attaching a bin and the vertex layout already deduced.
   It is the forum most likely to have someone who has touched the format or can
   help.
6. **Do not spend more time looking for a public converter**: it does not
   exist. The right strategy is own RE + retargeting tools + cannibalising PS2
   tooling.

---

## 8. NOTES ON WHAT WAS **NOT** FOUND (to avoid repeating searches)

- There is no Noesis plugin for `#AWO`/`#AWG`/`#AMB`.
- There is no wiki (Fandom/VG Resource/CloudModding) of the 360 HD format.
- There is no XeNTaX/ResHax thread dedicated to extracting models from the HD
  Collection (360 or PS3).
- There is no AMO↔AWO converter, not even an experimental one.
- There is no public Cell Semi-Perfect mod, nor documentation of the "16 face
  AWGs" on 360.
- The old `ps23dformat.wikispaces.com` wiki no longer exists (only partial
  Wayback).
- The PS2 community's `.ms`/`.bms` files circulate on mirrors/MediaFire and
  many links are dead; look for them on archive.org or ResHax if needed.

---

*End of report 01_WEB.md*
