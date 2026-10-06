# universal-modder — evaluation and application to the port RE (2026-09-30)

> `github.com/rehan-remade/universal-modder` (MIT, ~2k stars) was
> investigated as a possible aid to port content from other games, extend and
> improve. Cloned into an external directory
> (`%TEMP%\opencode\universal-modder`) for study only; NOTHING was installed
> in the project and no skills/API keys were added.

## What it is (and what it is NOT)

It is NOT a porter or a format converter. It is an **agent plugin** (Claude
Code / Codex / Cursor / Gemini / Copilot / OpenCode) that provides:

- **Skills** in Agent Skills format (11): `mod-any-game`, `game-recon`,
  `reverse-engineering`, `mashup-mods`, `asset-pipeline`, `fal-assets`,
  `game-automation`, `showcase-video`, `publish-mod`, `share-field-notes`.
- **`um` CLI** (Python): `scan`, `kb`, `win` (drive/shot/record), `video`,
  `sprite`, `render3d`, `fal`, `publish check`, `backup`.
- A **knowledge base** of *field notes* (4 games: AoE2, GTA×Minecraft,
  Terraria×2) + 3 techniques. **There are no notes on Budokai or Xbox
  360/recomp.**
- **12 engine playbooks** (Unity, Unreal, .NET/XNA, Godot, Source, Bethesda,
  Minecraft, Genie, RE/FromSoft/RAGE/Cyberpunk, **native C++**, indie, retro).

It is **method + tooling for agents**, not a library. The engine playbooks do
NOT apply to B3 HD (it is not Unity/Unreal/.NET); DBZ B3 HD is a **native
big-endian Xbox 360 recompilation**, so what is reusable is the RE and mashup
method.

## What is directly applicable to this project

### 1. The `reverse-engineering` skill → unblock Route B's bind/skin (F4)

It is exactly the methodology missing for the blocker documented in §3.4.6 /
§3.4.10 (real `M_bind`, bone→slot mapping σ). Points it adopts that fit:

- **Ghidra/IDA via MCP** for RE of `sub_82087F58` (the renderer that applies
  the palette): decompile, rename and type cumulatively; follow xrefs.
- **RenderDoc (`renderdoc-mcp`)** to capture the palette in the BIND/T-pose
  frame: see each draw, the constant buffers (view/proj matrices) and the
  depth buffer. It is the alternative route to pure RE for getting `M_bind`
  without decompiling.
- **Golden rule**: "reverse-engineer a binary file format and prove it with a
  round trip" — we already did the AWO round trip; the method formalises that
  the bind needs its own round trip (apply the palette → reproduce the T-pose →
  compare against the native bin).
- **Make it an oracle**: use `_grow_tpl` (a grown native template, renders
  PERFECTLY) as a **known-good oracle** and compare the port against it by
  variables, not by eye.

> **Update 2026-10-03:** later RE showed skinning is CPU-side (no GPU palette);
> see `SESION_DRAW_SEMANTICS_2026-09-11.md` §24. The oracle method still applies.

### 2. The `mashup-mods` skill Pattern 3: "embed a decomp as a library"

The generalised `libsm64`/`G64` pattern: wrap a decomp/recomp as a library
that takes collision+input and returns state+mesh. **It is the exact
description of what ReXGlue is** (a recomp with a runtime). Transferable ideas:

- **Recomp as a reimplementation oracle** (`retro-decomp.md` explicitly cites
  *"Xbox 360: XenonRecomp / ReXGlue"*). An alternative idiomatic engine
  (pattern 4, IW4L / Skate 3 Rust style) would read the user's
  AWO/`data_cmn.afs` and use the recomp as ground truth. **Too heavy for now**;
  noted as a future route, not as a plan.
- **Publish check** (pattern: "converters that run on the user's files; game
  assets never committed"): reinforces the promise already in force (§9.3: do
  not upload `*.bin/*.afs/*.awo/...`).

### 3. `um publish check` → reusable pre-release lint

A short script (125 lines) that already implements part of our §9.3 policy.
It detects: **game files copied verbatim** (by size+hash against the
install), **secrets** (FAL/Anthropic/OpenAI/GitHub/AWS/private keys, `.env`),
**decompiler fingerprints** (`FUN_xxxx`/`sub_XXXX`/"Decompiled with"/ILSpy),
**absolute user paths**, and **large engine files** (`.pak/.bsa/...`). It fits
as an extra check before `make_release.ps1`. Note: our `.gitignore` for
`github/` already covers much of it; what is new is the **hash match against
the install's AFS** and the **secrets** scan.

### 4. Knowledge: the "Oracles" technique + "Driving real games safely"

- **Oracles** (round trip, trace replay, synthetic host, measurement scene,
  circuit breaker at ~3 failures, `MODLOG.md` journal): matches the lab
  protocol in `RE_MASTER_2026_09.md` §4 (manifest, classification
  NO_EFFECT/INFRA_CRASH/PARSE_CRASH/...). It brings two new ideas: **trace
  replay** (record real positions/velocities per tick and replay them against
  the port) and **synthetic host** (build against a fake host with known
  geometry before having the game set up).
- **Driving real games safely**: overlaps with our harness
  `tools/long_run.ps1` / `press_key.ps1` / `grab_window.ps1`. No immediate action.

### 5. `native.md` (native C++ engine playbook)

Describes exactly what we already do: proxy DLL / hook
`IDXGISwapChain::Present` + ImGui / use the game's view-proj matrices to inject
3D into its pass (ReShade addon). Confirms the approach; brings no new
technique here.

## What is no good / risks

- **`um scan`, engine playbooks, `fal-assets`, `render3d`, `sprite`**: they do
  not apply (a native 360 engine, not a PC with a loader; paid fal.ai assets
  aimed at 2D sprites, not at porting real geometry).
- **Installing the plugin** would add skills to the cwd and a fal MCP; it was
  not done.
- It requires Python 3.10+, ffmpeg, Blender (3D) and `FAL_KEY` (assets).
- **Rule of its KB**: do not publish game files or decompiled code — aligned
  with ours.

## Concrete usage plan (what can be done with this)

Ordered by **return / effort**. None of this runs until it is decided.

### Block A — Unblock Route B (bind/skin) — *biggest impact, biggest effort*

The only live blocker. Here the toolkit provides the **method**, not B3 code.
Three pieces, in this order:

1. **Known-good oracle** (cheap): `_grow_tpl` (grown native template) renders
   PERFECTLY. Turn it into a formal oracle: capture the mesh with `_grow_tpl`
   from the game and compare the port against it by variables (mean position
   per bone, T-pose error), not by eye. It is the "measurement scene" of the
   oracles technique.
2. **Capture `M_bind`** (medium): instead of more trial and error, **RenderDoc**
   (`renderdoc-mcp`) on a frame in BIND/T-pose → read the constant buffers with
   the matrices and the depth. Alternative: RE of `sub_82087F58` with **Ghidra
   via MCP** (MCPServer or pyghidra-mcp): follow xrefs from the AWO format's
   strings and rename until the binding is identified.
3. **Round trip of the binding** (medium): apply the candidate palette to
   `pos` (bone-local) → reproduce the T-pose → compare against the oracle. The
   round trip is the acceptance criterion (the method that already validated
   the AWO).

It unblocks: complete PS2 geometry (correct bind/skin), the end of Route B's
"parked" state — not the current deliverable (HD↔HD swap), but the port of
models that do not exist in HD.

### Block B — Game test harness (low effort, immediate use)

`um win` covers what we already do, but improves two concrete things:

- **WinDrive** (`um/ps1/WinDrive.ps1`, PowerShell with embedded C#, no build):
  `drag`, `rel` (relative mouse for cameras/raw input), `hold`, `scanmode`
  (hardware scan codes for DirectInput/raw games that ignore VK), `size` (fix
  the client size), `idle` (check the human is not typing), `fg` (process in
  the foreground) and `kill` by exact PID. Our `press_key.ps1` uses
  `PostMessage`; WinDrive uses real `SendInput` + a **safety guard** (it only
  sends if the game is in the foreground, or nothing is and the cursor is over
  it) → more robust for the 3D demo and for testing input.
- **GPU-safe capture**: confirms GDI gives black in GPU games; `gfxcapture`
  (Windows.Graphics.Capture) captures the real window even when covered. Our
  `grab_window.ps1` already goes that way; note `--scale 0.33` (reading
  thumbnails saves tokens) and the ×3 coordinate protocol.

### Block C — `um publish check` as a pre-release lint (low effort)

Adopt (reimplement, ~125 lines) in `tools/` before `make_release.ps1`: it
detects **game files copied verbatim** (size+hash against `us/`+`eu/`),
**secrets** (keys, `.env`), **decompiler fingerprints** (`FUN_xxxx`,
`sub_XXXX`, "Decompiled with"), **absolute user paths** and **large engine
files**. It complements §9.3 (`.gitignore`) with what that does not cover:
hash match against the install's AFS and the secrets scan.
*(Done 2026-10: `tools/publish_check.ps1`.)*

### Block D — Oracles / journal / circuit breaker (process, no code)

Formally adopt in `RE_MASTER_2026_09.md`: **trace replay** (record real
positions/velocities per tick and replay them against the port), **synthetic
host** (build against a fake host with known geometry), **circuit breaker**
(~3 identical failures → stop and change approach) and **journal**
(`MODLOG.md`, survives context compaction). Our §4 protocol is already half
way; this adds the two new techniques.

### Block E — Generative assets with fal.ai (NOT recommended now)

`um fal` / `um render3d` generate sprites/3D/audio (paid, `FAL_KEY`). It would
serve to create **new content** (not to port real geometry): e.g. icons,
portraits or an intro. It clashes with the current goal (authentic game
content). Noted and discarded unless explicitly requested.

### Block F — `libsm64`/Skate-3 style reimplementation (future route, heavy)

`retro-decomp.md` and `mashup-mods` pattern 4: use the **recomp as an oracle**
to write an alternative idiomatic engine that reads the user's
AWO/`data_cmn.afs`. It is what IW4L (MW2 in Rust) and the Skate 3 engine did.
Too heavy and risky; **only noted** as a long-term direction.

## Conclusion

Real value = **RE method** (Ghidra/IDA/RenderDoc via MCP + oracles + round
trips), applicable to the only live blocker (Route B's bind/skin, §3.4.6). It
does not change the deliverable (native HD↔HD swap). Route B stays
**parked**; if it is resumed, this document fixes the protocol: (1) the
known-good `_grow_tpl` oracle, (2) capture `M_bind` with RenderDoc in
BIND/T-pose or RE of `sub_82087F58` with Ghidra via MCP, (3) round trip of the
binding (apply palette → reproduce T-pose → compare). Optional: adopt
`um publish check` as a pre-release lint.

**Suggested priority**: A (real unblock) > B/C (harness + lint, cheap) > D
(process) > E/F (discarded for now).

## References

- Repo: `github.com/rehan-remade/universal-modder` (MIT).
- Key skills: `skills/reverse-engineering/SKILL.md`,
  `skills/mashup-mods/SKILL.md`,
  `skills/mod-any-game/references/engines/{native,retro-decomp}.md`.
- `knowledge/techniques/oracles-how-agents-know-a-mod-works.md`.
- `um/publish.py`.
- Our blocker: `AGENTS.md` §3.4.6/§3.4.10,
  `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`,
  `docs/RE_MASTER_2026_09.md` §4/§5 (F4).
