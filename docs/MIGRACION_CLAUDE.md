# TEMPORARY MIGRATION TO CLAUDE — handoff and return protocol

> Handover document between **opencode** (this repo, canonical) and **Claude**
> (temporary migration). Goal: work in Claude **without** losing traceability,
> with **every change coming back to this disk as a single `.md`**. Claude does
> **not** push to GitHub's main branch; the maintainer applies and publishes
> from opencode.

Last updated: **2026-10-06** (documentation translated to English; PS5 port
added — see `docs/PS5.md`).

---

## 1. MINIMUM CONTEXT FOR CLAUDE (read in this order)

1. `AGENTS.md` — the project's operational reference (format, constraints,
   commands, invariants). **It is the stable source.**
2. `MEMORY.md` — live state (what was done, what is missing, traps, protocol).
3. `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` — history of Route B;
   **§24** = latest result (skinning RE).
4. `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md` — method/RE with agents.

**Nature of the project**: a PC recompilation of *DBZ Budokai 3 HD Collection
(Xbox 360)* with the **ReXGlue SDK** (derived from Xenia). The main deliverable
is the **native HD↔HD swap**; Route A (PS2→HD injection) is approximate;
Route B (full port) is **parked** but with a new RE finding.

---

## 2. 🟥 MANDATORY INSTRUCTION FOR CLAUDE (produce a handback `.md`)

> **CLAUDE: when you finish your session, your ONLY actionable artefact is a
> Markdown file** named:
>
> ```
> HANDOFF_CLAUDE_<YYYY-MM-DD>_<short-topic>.md
> ```
>
> **Mandatory** structure:
>
> 1. **Summary** — what you did and why, in 3-8 lines.
> 2. **Changes per file** — EXACT list of paths **relative to the repo**
>    (created / modified / deleted). For each one:
>    - If **new**: the complete content in a code block.
>    - If **modified**: a unified `diff` (`--- a/… +++ b/…`) or the whole
>      function before/after. Do not describe: **show the change**.
> 3. **Commands run** and their result (build, tests, scripts).
> 4. **Not done / risk / assumptions** — what was left half-done, what you
>    could not verify, what you assumed.
> 5. **Recommended next step**.
>
> Rules:
> - Do **NOT** push to GitHub's main branch. Do **NOT** open a PR.
> - Do **NOT** rewrite `AGENTS.md`/`MEMORY.md` unless the maintainer explicitly
>   asks for it for this session; if you propose changes there, **describe them
>   in the handback** as text to paste, do not apply them.
> - Use **relative paths** and do **not include** personal paths
>   (`C:\Users\...`), keys or game data (`.bin/.afs/.awo/.xex/...`).
> - If you touched the SDK (`rexglue-sdk-0.10/`), remember the game build
>   **overwrites** `rexruntime.dll`: the canonical DLLs must be copied back with
>   `tools\copy_sdk_dlls.ps1` (AGENTS §7).
> - If your work is **RE/instrumentation**, make clear in the handback how to
>   **revert** and which canonical DLL sizes must remain
>   (v1.4.0, SDK branch `dbz3-burstlimit`: `rexgpu-xenos.dll` **6372864 B**,
>   `rexruntime.dll` **11034624 B**; before, v1.3.0: 6360064 / 10920448).

### 2.1 Empty template (Claude can copy it)
```markdown
# HANDOFF_CLAUDE_<date>_<topic>

## 1. Summary

## 2. Changes per file
### CREATED: path/relative.ext
```
<complete content>
```
### MODIFIED: path/relative.ext
```diff
--- a/path/relative.ext
+++ b/path/relative.ext
@@ ... @@
```
### DELETED: path/relative.ext

## 3. Commands run
## 4. Not done / risk / assumptions
## 5. Recommended next step
```

---

## 3. OPERATING PROTOCOL (both sides)

### 3.1 opencode → Claude (handover)
1. Close the local session: `git -C github status` clean + local commit.
2. Hand over `AGENTS.md` + `MEMORY.md` + this document + the state of `github/`.
3. Set the **scope** of Claude's session (one concrete goal).
4. Remind of the **instruction in §2**.

### 3.2 Claude → opencode (return)
1. Claude produces `HANDOFF_CLAUDE_*.md` (§2).
2. The maintainer places it in the repo (e.g. `docs/handoffs/`) and reviews it
   in opencode.
3. opencode applies the changes, updates `MEMORY.md` (state) and, if needed,
   `AGENTS.md`.
4. `powershell -ExecutionPolicy Bypass -File tools\sync_github.ps1`
   (runs `publish_check.ps1`; exit 1 = **do not publish**).
5. Local commit → **push only if the maintainer authorises it**.

---

## 4. CLOSING CHECKLIST (for opencode)
- [ ] `HANDOFF_CLAUDE_*.md` read and applied.
- [ ] `MEMORY.md` §1/§2 updated.
- [ ] `AGENTS.md` updated if the change is stable/invariant.
- [ ] `sync_github.ps1` → `publish_check.ps1` PASS (or accepted WARNs).
- [ ] Local commit done; push pending approval.
- [ ] Clean build environment (no processes; canonical DLLs; toml without dev
      flags; RE capture artefacts deleted).
