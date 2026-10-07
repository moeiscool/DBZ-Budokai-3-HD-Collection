# FINDING: THE COMMUNITY ECOSYSTEM FOR MODEL TRANSFER

> Discovered on 2026-08-14. The community ALREADY solved the IW→B3 (PS2)
> conversion. The remaining step is PS2→HD 360 (the recomp's format).

---

## 1. WHAT THE COMMUNITY ALREADY HAS (verified)

### 1.1 IW models converted to B3 PS2 (#AMB)
`modding resources\All Character Models from IW into AMB format\`
- **241 .amb models** of ALL IW characters: Janemba, Pikkon, Pan,
  Super 17, Super Baby Vegeta 2, Gogeta, Vegito, every Freeza/Buu, etc.
- Each .amb is a **PS2 LE #AMB** (3 entries: #AMO0 + #AMT + padding).
- `Janemba.amb` (934 KB) = identical to IW bin 541 (48 bones, 17 AMGs).
- The IW→B3 moveset ports already exist (AGENTS.md).

### 1.2 Community tools (mod center)
- **AMO Decompiler.py / AMO Compiler.py** (Model Compiling Tools): decompile/
  recompile PS2 #AMO0 (LE). Basis of the pipeline.
- **B3_IW Model Converter** (amb_model.py): packs/unpacks #AMB.
- **Model Rig Toolset V0.6** (Model-Rig Extractor/Remover): handles rigs.
- **Model Merger Tool**: merges models.
- **Bone Addition Tool**: adds bones.
- **OBJ to AMG / Bin to OBJ**: OBJ pipeline (conversion to editable formats).
- **EMD to AMG / FbxEmd**: Xenoverse ecosystem (EMD↔FBX).

## 2. THE FORMAT (what we know)

| | PS2 (B3/IW) | HD 360 (recomp) |
|---|---|---|
| Container | #AMB LE | #AMB BE (AWO + AZT) |
| Model | #AMO0 LE | #AWO BE |
| Mesh | #AMG | #AWG |
| Texture | #AMT | #AZT |
| Skeleton | identical | identical |
| Endian | little | big |

## 3. THE LOGICAL TRANSFER (what is missing)

**Krillin PS2 vs HD** (verified):
- PS2: 3216 triangles, 4252 unique positions
- HD: 1713 triangles, 2182 slots (~50% reduction)

**The HD 360 halves the PS2 geometry** (decimates/re-topologises). The
developers did this for the characters present.

**For Janemba** (4415 positions, 3141 triangles):
- The HD equivalent would be ~2200 positions, ~1700 triangles.
- The decimated geometry ALREADY works (loads without crashing, sec34=2386).
- The problem is that Krillin's **mesh-ref blocks + arms** draw Janemba's
  triangles with the wrong IB ranges → deformed mass.

## 4. THE REAL TECHNICAL BLOCKER

The HD AWO format uses a **mesh group with mesh-ref blocks + arms** that
define HOW the runtime draws each part:
- Arm = list of bones + IB offsets (draw ranges).
- Dat = material + recursive chain to the next part.
- The runtime draws each part as [previous_offset, bone_offset).

When Janemba's geometry is injected with a different IB, Krillin's arms point
at the wrong ranges. **The arms have to be rebuilt** for Janemba's geometry
(group its triangles by material, map bones JNB→KLL, update offsets).

## 5. VIABLE NEXT STEPS

1. **Rebuild the mesh group's arms** for Janemba's geometry (group triangles
   by material in the order the runtime draws).
2. **Re-rigging**: transform Janemba's positions into the local space of
   Krillin's bones (mapping by label JNB_HEAD→KLL_HEAD, etc.).
3. **Validate** with a minimal part (just the body) before all 13 parts.

## 6. KEY RESOURCES (paths)

- IW models already converted: `modding resources\All Character Models from IW into AMB format\Janemba.amb`
- AMO Decompiler/Compiler: `mod center\Model Compiling Tools\`
- B3_IW Model Converter: `mod center\B3_IW Model Converter\`
- Mapped HD format: `awo_tools/CONSOLIDADO.md`, `awo_tools/RE_PROGRESO.md`
