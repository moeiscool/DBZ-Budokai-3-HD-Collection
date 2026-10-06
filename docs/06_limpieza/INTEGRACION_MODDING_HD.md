# Integrating modding tools into the HD environment

> Initial audit: 2026-09-08. No tools have been moved or deleted. The PS2
> sources are kept as reference and only the flows validated for X360/HD are
> exposed.

## Principle

`mod center/` mixes PS2, GameCube, Shin Budokai, B3/IW and X360 tools.
`modding resources*` mixes resources, tutorials and Xenoverse/SDBH tools. They
are not a homogeneous toolkit. Copying them wholesale into the release would
bring in wrong formats, duplicated Python runtimes and executables unrelated
to HD.

The integration must have three levels:

| Level | Contents | Action |
|---|---|---|
| `hd/` | Tools validated on B3 HD/X360 | Integrate and document |
| `bridge/` | Input converters towards the HD pipeline | Adapt with tests |
| `reference/` | PS2/SLXS/BPL/IW and historical tools | Keep outside the HD flow |

## HD candidates

| Tool | State | Proposed integration |
|---|---|---|
| `xbcompress.exe` / `xbdecompress.exe` | Validated | Wrapper with `/N:2048`, magic and size |
| `swap_b3.py` | Validated | Per-entry override installer |
| `texture_b3.py` | Validated | AZT/DXT3/BC2 pipeline |
| `awg_to_obj_b3.py` | Validated | Main B3 HD exporter |
| `awg0_export.py` | Validated | Checking formats A/C |
| `awg_cara_export.py` | Validated | Checking face AWGs |
| `afs_scan.py` / `stage_analyze.py` | Validated for RE | Auditors, not destructive editors |
| `catalog_b3.cat` + `data_cmn_map.txt` | Project data | Structured/versioned catalogue |

## Bridge candidates

| Tool/resource | Input | HD usefulness | Work needed |
|---|---|---|---|
| `Model-Rig Extractor` | PS2/Budokai | Labels, bones and correspondences | JSON output, without writing AWO |
| `EMD/ESK → FBX` | SDBH/Xenoverse | Source geometry | Validate axes and names |
| `EMD to AMG` / `OBJ to AMG` | PS2 AMG | Intermediate stage | Separate it from HD packing |
| Blender 2.78 FBX bridge | FBX | Source editing | Documented optional input |
| `parse_ps2_mesh.py`, `pose_matrix.py`, `rig_mapeo.py` | PS2 | Port research | Reproducible JSON |

## Do not present as HD

- SLXS Editor, BPL Editor and SLUS editors: PS2 structures, not HD XEX tables.
- AMO/AMG/AMT packers, Model Part Editor and Bone Addition Tool: they write
  PS2, not X360 `#AWO/#AWG/#AZT`.
- Shin Budokai, GameCube and PS2 IW tools: reference or bridge, not the HD flow.
- `analyze_bin_hd.py`: historical PS3 layout parser, obsolete.
- `build_awo_v20.py`, `build_awo_v22.py`, `build_awo_from_json.py` and
  `inject_a18*.py`: experimental; not a delivery flow.

## Valuable resources

### High priority

- `modding resources update/`: B3/GH lists, capsule IDs and `data_usa.afs`
  breakdowns; consolidate into `docs/03_formatos/` without deleting originals.
- X360 compression tutorial: cross-check it with the validated use of LZX `/N:2048`.
- B3HD texture tutorial: cross-check it with `texture_b3.py` and AZT.
- Discord research: bin lists, AFL and breakdowns for RE, not HD automation.

### Medium priority

- `Infinite World to Budokai 3 Moveset Ports` notes: keep the
  correspondences, without assuming a direct IW→B3 HD conversion.
- `EmdFbx-and-FbxEmd-LibXenoverse`: evaluate as a geometry bridge.
- `lean bone tutorial`: extract the useful documentation, not its whole
  Python runtime.

### Low priority

- SDBH World Mission (`.emm/.emd/.emb/.esk/.ean`): source for port candidates.
- Discord ZIP/RAR, videos, PDFs and executables: catalogue by hash before duplicating.

## Cleanup and integration

1. Exclude `__pycache__`, `.pyc`, `Temp`, logs and tutorial outputs.
2. Do not copy embedded Python runtimes; use the project's Python for bridges.
3. Add to `mod center hd/` only small source scripts, CLI, relative paths.
4. Each integrated tool must declare input, output, region, format,
   compression and reversibility.
5. Compute a hash and record the origin before moving or deduplicating resources.

## First deliverable

`mod center hd/tools_manifest.json` already contains the `hd`, `bridge` and
`reference` categories. Validate it with:

```powershell
python "mod center hd/tools_manifest_check.py"
```

The next step is adding wrappers for compression, OBJ export, textures, swaps
and verification. `mod center/` will remain the complete reference archive.
