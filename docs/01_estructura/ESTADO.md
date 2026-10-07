# Current state of the project

> Updated: 2026-09-26 (after **v1.2.9 Latest**), plus the PS5 port
> (2026-10-06). Operational reference: `AGENTS.md`. Release-by-release detail:
> `01_estructura/HISTORICO_RELEASES.md` §A and the session docs. PS2→HD port
> **parked** (AGENTS §3.4.10).

---

## WHAT WORKS

| Thing | State | Notes |
|---|---|---|
| **The game boots and plays** | ✅ | D3D12 main, 60.0 fps, dual US+EU core. `out\build\win-amd64-release\dbz3.exe` |
| **Dual US+EU core** | ✅ | A single exe detects the xex by MD5 (US `A53E…`/EU `C37E…`) |
| **Executable auto-detection (v1.2.2)** | ✅ | Found by **size+MD5** (`DBZ3\yae3_xenon.xex`, `assets\DBZ3\`, …) and cached in `user_data/dbz3/xex_cache\`. No renaming needed |
| **Retail disc dump** | ✅ | Root = HD Collection menu (3317760 B) + `DBZ3\`: mounts `DBZ3\` as the game drive and boots |
| **HD Collection menu / DBZ1 detected** | ✅ | `kHdMenu`/`kDbz1` block Play with a clear message (`XexStatus`) |
| **TOML fix + self-repair (v1.2.2 + v1.2.6)** | ✅ | Idempotent `EscapeTomlStrings` + `LoadUserSettings` validates with toml++ and repairs (`ConfigLoadState`); `.bak` if unrepairable |
| **Disc mode (ISO)** | ✅ | Plays straight from the `.iso` (XDVDFS) without extracting; extracts only the xex to `iso_cache/`; `RegionDiscDevice` remaps the region and prefixes `DBZ3\`; folder→ISO fallback. ⚠️ **Mods are NOT applied in ISO** |
| **EU Dragon Universe crash** | ✅ | Fix `0x8215B378` + `fix_eu_bctr.py` (apply after re-codegen) |
| **Custom launcher** | ✅ | Tabs: Video/Upscaling/Audio/Input/Mods/Model Swap/Textures/Dev |
| **Music mod** (`og_music`) | ✅ | Replaces ADX/SFD (whole-file override) |
| **B3 HD texture mod** | ✅ | `texture_b3.py` + Textures tab; per-entry override (~118 KB) |
| **Texture packs (v1.2.7)** | ✅ | PCSX2 style; dev dump + runtime loader (D3D12 and Vulkan) |
| **Native B3→B3 swap** | ✅ | `swap_b3.py` + Model Swap tab; per-entry override (~100 KB) |
| **Swaps in any direction** | ✅ | **Virtual mid-insert**: bins bigger or smaller than the slot (Goten 107006 B in Krillin's 106496 B slot) |
| **2+ simultaneous mods** | ✅ | Each mod touches different entries of the same AFS |
| **HD texture upscale** | ✅ | `dbz3_hd_textures` x2/x3, native DXT + RGBA8, mips; costs VRAM. Off by default |
| **v1.2.9 diagnostics** | ✅ | ALWAYS-ON warnings (sustained fps, slow disk, mixed installation), `vram=`/`lim=` in `perf`, `entorno` line |
| **HD bin export/verification** | ✅ | `awo_tools/awg_to_obj_b3.py`, `awg0_export.py`, `awg_cara_export.py`; `analyze_bin_hd.py` obsolete |
| **PS2→data extraction** | ✅ | `parse_ps2_mesh.py` (PS2 AMG) |
| **PS5 build (jailbroken)** | 🧪 Experimental | `ps5/make_ps5.sh` (Arch host): runtime + host compile for PS5; **not yet run on a console**. See `docs/PS5.md` |

## WHAT DOES NOT WORK / PARKED

| Thing | State | Cause |
|---|---|---|
| **Full PS2→HD port (Route B)** | ⏸️ Parked (2026-09-13) | Geometry and draw CORRECT (1 strip draw, verbatim VB+IB); blocker = real `M_bind` + bone→slot mapping (σ). See AGENTS §3.4.5/§3.4.10 |
| **PS2→HD injection (Route A)** | ✅ Approximate | Does not re-topologise (PS2 body + HD limbs/head); binary threshold 0.8 |
| **IW→B3 character port** | 🔴 Discarded | Janemba failed (format/retargeting). Do not retry without a validated converter |
| **FPS drops with scale>1x + textures** | 🟡 Watched | Issue #8 open: the v1.2.8.2 fix was commented, waiting for the reporter's `perf` log |
| **Real pause when losing focus** | 🔴 Not viable | There is no safe mechanism; only mute/dim (QoL v1.2.5) |

---

## THE OVERRIDE FIXES (discovered)

1. **The `AfsFindModOverride` hook only supported a direct file**, not a
   folder (`mods/<mod>/us/<afs>/<entry>/<file>`). B1's folder handling was
   ported.
2. **Compression**: the game uses LZX `/N:2048`, not `/N:32`. With `/N:32` the
   bin exceeded the slot → the guest truncated the LZX → crash.
3. **Padding**: the mod's bin is padded to the slot's `to_read`
   (`ceil(size/0x1000)*0x1000`, e.g. 106496 for entry 327).
4. **AFS table off-by-one**: the scripts read the table at offset 0x10, the
   runtime at offset 8 → a 1-entry shift (bin N = physical N+1). Fixed to
   offset 8. It was the cause of tex_91's crash.
5. **🔴 Virtual mid-insert (2026-08-18)**: for bins that EXCEED the slot's
   `to_read`, the runtime presents the guest a **consistent virtual AFS
   table**: the entry grows in place and the later ones shift; reads are
   translated to the physical file (`AfsVirtualRange`), without materialising
   huge files.

> Full detail of the mod pipeline in `AGENTS.md` §6 and
> `02_mods/COMO_HACER_MODS.md`.

---

## HISTORICAL NOTE: EU RE-CODEGEN (2026-09-10)

- The EU re-codegen is **not reproducible** with the current config: the
  recompiler generates symbols WITHOUT the `dbz3eu_` prefix → collision with
  US in the dual build. That is why the EU fixes are applied **MANUALLY** to
  the codegen. (The PS5 build is single-region, so it runs the plain EU
  codegen + `fix_eu_bctr.py` without prefixing.)
- Entries in `dbz3_config_eu.toml` must ALWAYS go inside `[functions]`,
  BEFORE the first `[[switch_tables]]` (otherwise they are lost on every
  re-codegen).
- The `dbz1_diag_logging` cvar lives in `rexruntime.dll`; if the dual build
  fails to link `roster_trace.cpp`, rebuild the baseline runtime and
  reinstall DLL+lib.
- Tested EU codegen backup: `out/analysis/codegen_backup_20260909/`.

## REFERENCE DATA

The data that lived in `%TEMP%\opencode\` (b327_*.bin, cell_*.bin, …) **NO
LONGER exists** (cleanup 2026-09-02): regenerate it from `us/` + `ps2_games/`
with the tools in `awo_tools/` (`rt_327.bin` = Krillin entry 327 decompressed).
