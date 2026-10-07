# ROUTE B SESSION — RENDER (2026-09-12)

## Goal
Make **Route B** render (full PS2→B3 HD port with the PS2 topology: 44-byte
windows + IB) so that models missing from HD can be ported.

## Summary of the result
- ✅ **2 real `grow()` bugs fixed** (crash + incomplete fetch).
- ✅ Confirmed: the port's geometry is **exact** and **reaches the GPU**.
- ❌ **The model explodes when rendered** → **Route B is NOT validated**.
- ⚠️ **Correction**: the earlier "in-game validation" (2026-09-12) was the
  **native swap `cell_native`**, NOT the port.

## Context: the earlier confusion
No logged session showed an `AFS OVERRIDE HIT` for `cell_native` /
`cell_viab`. **AFS logging does not capture `data_cmn`** in those sessions
(different path/cache), so the absence of a log **proves nothing**; but the
render is visible. The earlier conclusion ("`cell_viab` = perfect Cell") was
based on an observation of the **native swap in Krillin's slot (327)**, not
of the port in 147.

## Verified facts (offline + GPU capture)
1. **Exact geometry**: the port's 5148 windows rebuild the PS2 model
   (identical bbox, nearest-neighbour distance **0.0000**).
2. **It reaches the GPU**: `win0/win100/win500/win1000/win2000/win3000` found
   **contiguous** in `dbz3_vf.bin` (the GPU copied the region verbatim).
3. **The guest splits the IB**: the body is drawn with `prim=4` (list) in ~11
   draws (`dma=1BD0xxxx`), each one a range of indices. It does **NOT** draw
   the whole IB at once.
4. **The vertex fetch** (fc=95) uses the **global** window buffer
   (`addr=1BD02000`) for all the body's draws.

## `grow()` bugs fixed (`awo_tools/awg_vertex_buffer.py`)
1. **Double adjustment of the AWG table** (crash): the AWG table (offsets
   **relative** to `awo`) lives inside `[awo, awg0)`; the `#AWO` header loop
   treated it as **absolute** pointers and shifted it **twice** → 16 entries
   pointed at garbage → the `#AMB` *parser* dispatched null
   (`UNREGISTERED indirect call target=0`, `caller_lr=0x8208018C`).
   **Fix**: exclude `[tbl, tbl+n_awg*4)` from that loop.
2. **`AWG0+0x2C` not updated** (incomplete fetch): that field is the **SIZE of
   the vertex buffer in bytes** (template: `2948*44 = 129712`). The guest sets
   the fetch with that value → it only read 2948 windows; IB indices >2947 read
   garbage → *render in pieces*. **Fix**: `set32(awg0+0x2C, new_n*44)`.
   Verified: after the fix there is a `VFDUMP fc=95 size=56628 dwords = 226512 B`
   (= `5148*44`).

## Diagnosis of the remaining blocker
Although the geometry is correct and complete, the port **explodes**.
**Rigging** ruled out (transferring the HD skin with `--hd-skin` makes it
**worse**). The blocker is:

> The guest **splits the IB by the TEMPLATE's A/B part descriptors/ranges**.
> The port changes the topology (pool + IB) but **leaves the 0x60 descriptors
> and the mesh-refs untouched**. When drawing, the `B` ranges cut the port's
> IB at positions that no longer match the real parts → wrong connectivity →
> "explosion".

### Additional evidence (the guest's IB ≠ the file's IB)
The body draw (`prim=4`, `dma=1BD0…`) draws an IB that **does not match** the
port file's at that offset:
- port file: `IB[127] = 49, 48, 49, 50, …`
- guest (draw `dma=1BD020FE`): `2429 2430 2429 2428 …`
Moreover, `dma=1BD020FE` falls **inside** the vertex buffer's region
(`VFDUMP fc=95 addr=1BD02000`), which suggests the guest **relocates/reorders**
the IB and/or there is a buffer inconsistency (IB vs VB) when growing. This
points to the blocker being deeper than "just recompute the A/B ranges":
**we need to understand how the guest builds/places the IB** (probably it
re-assembles it from the descriptors → memory map).

## Decision (2026-09-12)
**PARK** Route B: the render is **deep RE** (rebuilding the splitting +
the guest's buffer placement) with an uncertain payoff, and the project
already has **validated** routes (native HD→HD swap + Route A injection). The
work is left bounded and documented here, to resume only if a model missing
from HD appears that Route A does not cover. `grow()` stays fixed (a real
bug fix).

See §3.4.8 of `AGENTS.md` (0x60 descriptors and pool partition) and
`awo_tools/phase_c_descriptors.py`, `phase_c_meshgroup.py`.

## Next steps (Route B)
1. **RE of the splitting**: understand how the guest derives the draws (`B`
   ranges) from the descriptors/mesh-refs and whether they also depend on `A`.
2. **Rebuild the A/B ranges + mesh-refs** for the new topology (the port's pool
   + IB), consistently.
3. Re-validate with Cell (which already "fits"/grows) **before** the definitive test.
4. Only then: the definitive test (a model missing from HD).

## Tools / files touched
- `awo_tools/awg_vertex_buffer.py` — `grow()` fixes; `info` mode reads the
  real size via `g(0x2C)`.
- `mod center hd/ports/port_b3_windows.py` — `--hd-skin` (HD skin by nearest
  neighbour; discarded/makes it worse), `--fit`/grow.
- Test mods: `_grow327` (port in Krillin's slot 327), `cell_viab`/`cell_viab_grow`
  (147). `cell_native` (327) = native swap (reference that DOES render).
- Captures: `out/build/win-amd64-release/dbz3_draws.log` + `dbz3_vf.bin`
  (marker `dbz3_drawlog.on`; the `rexgpu-xenos` DLL is still instrumented).
