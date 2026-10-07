# MEMORY.md — DBZ Budokai 3 HD Collection (live operating memory)

> Companion to `AGENTS.md`. **AGENTS.md = stable reference** (format,
> constraints, commands). **MEMORY.md = live state** (what was done, what is in
> progress, what is missing, and the **protocol for working with Claude**).
> Update this file when closing each session; do not duplicate here what is
> already in AGENTS.

Last updated: **2026-10-06** (PS5 port + documentation translated to English;
before that 2026-10-03: Route B skinning RE + handoff to Claude).

---

## 0. TEMPORARY MIGRATION PROTOCOL TO CLAUDE (READ FIRST)

The maintainer alternates between **opencode** (local, this repo) and
**Claude** (temporary migration). The canonical repo is **this disk**;
`github/` is the versionable copy (manual sync with `tools/sync_github.ps1`).

### 0.1 Golden rule
**Every change Claude makes must come back to this disk as ONE "handback"
`.md`**. Claude does **not** publish to GitHub's main branch. The maintainer
reviews the `.md` here and applies/publishes from opencode.

### 0.2 When **handing** the project to Claude (what opencode does)
1. Make sure `git -C github status` is clean and the local commit is done
   (even if not pushed).
2. Hand over: `AGENTS.md`, `MEMORY.md`, `docs/MIGRACION_CLAUDE.md` and the state
   of `github/` (branch + commits ahead).
3. Tell Claude the **exact scope** of the session (e.g. "RE of the CPU
   skinning routine") and ask for the handback (§0.3).

### 0.3 When **receiving** from Claude (instruction to Claude, copy as is)
> **MANDATORY INSTRUCTION FOR CLAUDE**: when you finish your work, produce **a
> single Markdown file** named `HANDOFF_CLAUDE_<YYYY-MM-DD>_<topic>.md` with:
> 1. **Summary** of what was done (what, why).
> 2. **EXACT list of files** created/modified/deleted (paths relative to the
>    repo) and, for each one, **what changes** (ideally a unified `diff`, or
>    the complete content if new).
> 3. **Commands** you ran and their result (build/tests).
> 4. **What you could NOT do** or left half-done + risks/assumptions.
> 5. **Recommended next step**.
> - Do **NOT** push to GitHub's main branch. Do **NOT** rewrite
>   `AGENTS.md`/`MEMORY.md` unless this memory explicitly asks for it;
>   instead, propose the change in the handback. Deliver that `.md` as the only
>   actionable artefact.
> - Use relative paths and avoid personal data (`C:\Users\...` paths).

### 0.4 When **coming back** from Claude to opencode (what opencode does)
1. Read the `HANDOFF_CLAUDE_*.md`, apply the indicated diffs/files.
2. Update `MEMORY.md` (this section + §2) and, if applicable, `AGENTS.md`.
3. `powershell -ExecutionPolicy Bypass -File tools\sync_github.ps1` (runs
   `publish_check.ps1`; exit 1 = failure) → commit → **push only if the
   maintainer asks**.

---

## 1. LIVE STATE (2026-10-06)

### 1.0 New in this session (Claude, 2026-10-06) — see `HANDOFF_CLAUDE_2026-10-06_ps5-port.md`
- **PS5 port** (jailbroken consoles), adapted from
  [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp)
  (GPL-3.0-or-later). New folder `ps5/` (GPL-3), user guide `docs/PS5.md`,
  internals `ps5/README.md`. One command on an Arch Linux host:
  `bash ps5/make_ps5.sh --iso <your.iso> [--console <ip>]`.
  - SDK: `patches/rexglue-sdk/` (DBZ3 overlay) + `ps5/patches/rexglue-v0.10.0-dbz3-ps5.patch`
    (mcla-recomp's PS5 platform layer rebased onto the overlay; 2 conflicts
    merged by hand: vblank clamp+resync, frame_cap+PS5 paint logging;
    `REX_EXECUTABLE_PATH` for `GetExecutablePath()`; `sha256.cpp` endian fix)
    + `ps5/patches/rexglue-ffmpeg-ps5-config.patch`.
  - Host `ps5/main_ps5.cpp`: no ImGui launcher; reads `/data/dbz3/dbz3_user.toml`;
    game data in `/data/dbz3/game`, mods in `/data/dbz3/mods`; DualSense via
    scePad, audio via sceAudioOut; single region (US → `generated/` + hooks,
    EU → `generated_eu/` + `fix_eu_bctr.py`).
  - Verified in the cloud session: the patch applies to clean v0.10.0 + overlay;
    `rexruntime` + `rexgpu-xenos` build for the PS5 target (pinned payload SDK,
    clang 21); DBZ3 host sources + `main_ps5.cpp` (US and EU) compile for PS5
    with no unresolved symbols beyond the codegen's. **Not run on a console.**
  - ⚠️ If `patches/rexglue-sdk/` changes, re-check that the PS5 patch still
    applies (procedure in `ps5/README.md`).
- **All documentation translated to English** (file names kept so links do
  not break).

### 1.1 Git
- Versionable repo: `github/` (NOT the working repo; synced manually).
- **`master` ahead 10** of `origin/master`; **no push** (wait for the user's OK).
- Latest local commits: `f753948` (skinning RE), `a30c8ac` (publish_check),
  `5fc4821` (Route A + normals fix), `7c2fd6c`, `0394903`.
- Clean build environment: no processes, toml without dev flags, canonical
  DLLs (`rexgpu-xenos.dll` 6360064 B / `rexruntime.dll` 10920448 B).
- The Claude session of 2026-10-06 worked on branch
  `claude/sweet-ptolemy-gasuxh` of the GitHub repo.

### 1.2 Releases
- **v1.3.0 = Latest** (2026-09-30) at the time of the 2026-10-03 notes; later
  releases up to 1.4.2.2 exist (see `CHANGELOG.md`). Everything else non-Latest
  (see AGENTS §3.0/§9.2).

### 1.3 Route A (PS2→HD injection) — approximate deliverable
- Works; best result `cell_win2`.
- **Arm/head defect = shading of approximate geometry** (NOT a normal-rotation
  bug). §23.
- **Normals fix**: `awo_tools/awg_normal_fix.py` (copies the native HD `nrm`
  onto the port's bin). Mod `cell_nfix` validated at runtime (clean demo). §23.1.
- Comparator: `awo_tools/awg_diff.py`.

### 1.4 Route B (full port) — 🔴 DIAGNOSTIC UNBLOCK 2026-10-03
- **Skinning RE (new, §24)**: `rexgpu-xenos` was instrumented (REVERTED) and
  shaders + constants were dumped per draw. **Hard** result:
  - **No VS indexes constants dynamically** (no `a0`/`arl`/`lc`) → **no bone
    palette on the GPU**.
  - **No shader uses `memexport`** → no GPU/"compute" skinning.
  - The body VS (`FDF960B5D7869030`) is a **rigid transform** with **a single
    4×4 matrix in `c0..c3`**, **identical** across the ~33 chunks
    (`indx_offset=0`, counts 3..1995).
  - ⇒ **Skinning is CPU-side (Xenon)**: the guest reads the bind pose,
    applies the bone matrices and writes **world space**; the VS only projects.
  - **Refutes the hypothesis "cause = skinning shader"** (§3.4.6/§10 and §22).
- **New focus**: RE of the **CPU skinning routine in the recompiled code**
  (which vertex space/order the guest expects). See §2 "NEXT".

### 1.5 Block C (pre-release lint)
- `tools/publish_check.ps1` (reimplementation of `um publish check`): FAIL on
  game/build files/secrets; WARN on decompiler fingerprints, personal paths,
  missing README. Integrated at the end of `tools/sync_github.ps1`. It
  auto-excludes its own file. State: **PASS (44 WARN, 0 FAIL)** on `github/`.

---

## 2. NEXT (priority)

1. **PS5: first boot on a console** — build with `ps5/make_ps5.sh`, install,
   read `/data/dbz3/dbz3-play.log`; iterate on missing indirect-call targets
   (`dbz3_config*.toml`) and anything PS5-specific.
2. **RE of the CPU skinning routine** (Route B) — the real blocker. Locate in
   `generated/` (US) / `generated_eu/` (EU) the code that reads the bin's
   vertices and applies bone matrices; determine the expected **space/order**
   (bind pose per bone). Historical candidate: `sub_82087F58` (AGENTS §3.4.10).
   - Auxiliary measurement: dump the **final world-space VB** of the body draw
     (not the bin) to compare port vs native in the same frame/pose.
3. **Decide on `cell_nfix`** (adopt it as a reproducible Route A improvement vs
   leave it as a line of work).
4. **Push** of the 10 local commits (waiting for the maintainer's OK).
5. Optional Route A: refine injection (`--bone-aware`/`--normal-only` per zone).

---

## 3. DO NOT REPEAT / TRAPS (derived from this session)

- The hypothesis "the port's problem is the skinning shader" is **REFUTED**
  (§24). Do not go back to shader RE for Route B.
- `dump_shaders` (cvar) dumps the ucode **bin + disasm**; `DumpUcode` is
  already wired in `translator.cpp:340` (no need to wire it).
- The game does NOT advance screens with `PostMessage` (it lacks
  `has_focus_`). To navigate: **visible** window + `SetForegroundWindow` + a
  real `keybd_event` (`SendInput`); with `long_run.ps1` the window is hidden →
  the Returns do not get in.
- Per-draw capture logs can be **hundreds of MB** (656–730 MB); read them
  **streaming** (`Select-String -Context`), never with whole arrays.
- Any SDK instrumentation is **reverted** and the canonical DLLs are copied
  back (`tools\copy_sdk_dlls.ps1`); check the size (6360064 / 10920448).
- PS5: Ubuntu's LLVM 18 cannot build the PS5 runtime (va_list ABI error in
  `xma_decoder.cpp`); use the Arch host (newer clang) or a clang ≥ 20.
- PS5: the pinned payload SDK has no `<endian.h>`; the PS5 patch makes
  `thirdparty/crypto/sha256.cpp` use the compiler's byte-order macros.

---

## 4. KEY REFERENCES
- `AGENTS.md` — complete operational reference (format, commands, invariants).
- `docs/MIGRACION_CLAUDE.md` — detailed handoff + handback template.
- `docs/PS5.md`, `ps5/README.md` — PS5 build.
- `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` — §21 (oracle), §22
  (runtime VB), §23/§23.1 (Route A + normals fix), **§24 (skinning RE, new)**.
- `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md` — origin of Block C.
- `docs/RE_MASTER_2026_09.md`, `docs/HOJA_DE_RUTA_2026_09.md`.
