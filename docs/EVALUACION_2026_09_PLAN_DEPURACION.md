# EVALUATION 2026-09 + SUPERB DEBUGGING PLAN

> Date: 2026-09-09 (after publishing v1.1.3 "The ISO patch").
> Goal: evaluate the project's real state, diagnose the GitHub issues with new
> messages, and lay out an exhaustive debugging plan.

---

## 1. PROJECT EVALUATION (real state)

### 1.1 What is SOLID (verified)

| Area | State | Evidence |
|---|---|---|
| **Game** | Very functional | D3D12 60fps, keyboard by default, GPU presets, real frame_cap, US+EU (dual core) |
| **ISO / disc** | Functional | v1.1.3: selector always visible, extracts only default.xex, smoke test validated |
| **Launcher** | Polished | i18n audited 0 gaps (ES/EN/IT/DE/FR), 0 warnings, messages for non-technical users |
| **Mods override** | Functional | AfsFindModOverride + virtual mid-insert (100% lightweight, in memory) |
| **B3→B3 swap** | Validated | Goten, Vegeta 424, Babidi, Bulma |
| **PS2→HD injection** | Functional | cell_npm4 (binary threshold 0.8) = best result |
| **Content RE** | Advanced | data_cmn audited (3990 entries), stages located, roster mapped (0x82372818/0x823268C0) |
| **Release pipeline** | Solid | make_release + verify_release (clean zip, baseline DLLs, no leftovers) |

### 1.2 Technical debt / weak points

1. **The EU crash in Dragon Universe is still alive** (issue #4, NEW message from Goten46).
2. **Intermittent `std::terminate` from `LaunchModule`** (mitigated with try/catch, exact throw not located).
3. **`roster_trace.cpp`** is F3.1 diagnostics; gated by F10/dev (it does not get in the way).
4. **`out/analysis/guest_image/build/`** (dump_image) left as an artefact — useful, keep it.
5. **EU codegen**: it is not known which exact EU xex generated it (see §3.2). Reproducibility risk.
6. `docs/01_estructura/ESTADO.md` is **outdated** (it says "2026-08-18" and does not reflect v1.1.2/1.1.3 or the ISO).

---

## 2. GITHUB ISSUES — COMPLETE AUDIT

| # | Title | State | New message after the reply? | Action |
|---|---|---|---|---|
| 6 | PS2 soundtrack instead of HD? + save states | OPEN | **NO reply from the owner** | **Reply** (§4.1) |
| 5 | Add to PortForge? | OPEN | zamiba (PortForge's owner) promised to reply "in a day or two" (2026-09-09) | **Wait/remind**; reply if it appears (§4.2) |
| 4 | [BUG] Crash Dragon Universe + START (EU) | OPEN | **YES — Goten46: START NO longer crashes, but Dragon Universe STILL crashes with `0x8215B378`** | **EU codegen fix** (§3) |
| 3 | Apple Silicon Mac CrossOver | OPEN | No (only the owner's reply; the red "Press START" splash stays open) | Wait for Vulkan confirmation on Mac; the splash is cosmetic |
| 2 | It does not start | CLOSED | Solved by the community (place the assets at the root) | Close ✓ |
| 1 | [v.1.0.4] Potential Bugs | OPEN | No (the owner asked for a re-test on v1.1.2) | Wait for a repro on v1.1.2/v1.1.3 |

### Action priority
1. **#4**: a real EU codegen bug with a new report → technical fix (§3).
2. **#6**: a legitimate community question without a reply → reply (PS2 soundtrack + save states).
3. **#5**: follow up with zamiba (PortForge) — pending his promised reply.

---

## 3. DIAGNOSIS OF THE EU CRASH (#4) — `0x8215B378`

### 3.1 The report (Goten46, 2026-09-09)

```
[critical] UNREGISTERED indirect call: target=0x8215B378 caller_lr=0x8209F390
[critical] [FATAL] Call to invalid or unregistered function at guest address 0x8215B378
```

- It confirms the v1.1.2 fix (`sub_820F2398` registered) **did solve the
  START-in-a-fight crash**.
- Dragon Universe (character select) still crashes: **another function
  dispatched through a pointer table that the recompiler did not register**.

### 3.2 Findings of the analysis

1. **`0x8215B378` was NOT registered** in `generated_eu/` (neither `dbz3_eu_register.cpp` nor `dbz3_eu_init.cpp`).
2. It falls between two registered functions: `0x8215B368` and `0x8215B388` → a
   gap of **0x20 bytes (8 instructions)** → the same category as `0x820F2398`
   (a function folded as a dead fall-through, reachable only via a function
   pointer).
3. The caller `0x8209F390` is in `dbz3_eu_recomp.19.cpp:1718` — a
   `REX_CALL_INDIRECT_FUNC` (vtable dispatch: `lwz r11,0(r31)` → `+68` →
   `slot*8` → `bctrl`).
4. **PPC body of `0x8215B378`** (extracted from the real EU xex): `lis r11,-32234;
   addi r11,r11,-28880; stw r11,16(r3); b 0x82158F88` (0x10 bytes) — it writes
   a vtable pointer at `+16(r3)` and branches. Identical in pattern to its
   sibling `sub_8215B368`.
5. **The xex `yae3_xenon_eu.xex` (C37EB979) IS the right one**: the diff of
   registered addresses between the tested codegen and the re-codegen of the
   current xex showed that the ONLY difference was `0x820f2398` (lost because
   of a misplaced config). The earlier finding of "the dump does not match" was
   an artefact of the badly generated dump (`dbz3_us_image.bin`).

### 3.3 Fix route — CARRIED OUT (2026-09-10)

1. **Config corrected**: `0x820F2398` and the new `0x8215B378` moved INSIDE
   `[functions]` (before `[[switch_tables]]`) in `dbz3_config_eu.toml`. ⚠️ Rule
   from history L2726-27: entries after `[[switch_tables]]` are ignored.
2. **Re-codegen tried but DISCARDED**: the current recompiler generates names
   WITHOUT the `dbz3eu_` prefix → symbol collision with the US codegen in the
   dual build. The tested codegen (with the prefix) came from an earlier
   rexglue.exe. *(Single-region builds such as the PS5 EU build do not need
   the prefix.)*
3. **MANUAL fix applied in 4 places of the EU codegen** (the same pattern as
   the `0x820F2398` fix):
   - `generated_eu/dbz3_eu_recomp.16.cpp`: `DEFINE_REX_FUNC(dbz3eu_sub_8215B378)` (after `sub_8215B368`).
   - `generated_eu/dbz3_eu_funcs.16.h`: declaration `DECLARE_REX_FUNC(dbz3eu_sub_8215B378)` + `DECLARE_REX_FUNC(dbz3eu_sub_82158F88)` (the cross call to partition 18).
   - `generated_eu/dbz3_eu_funcs.h`: `DECLARE_REX_FUNC(dbz3eu_sub_8215B378)`.
   - `generated_eu/dbz3_eu_register.cpp`: `SetFunction(0x8215B378, dbz3eu_sub_8215B378)`.
   - `generated_eu/dbz3_eu_init.cpp`: `{ 0x8215B378, dbz3eu_sub_8215B378 }`.
4. **Problem found along the way — the `dbz1_diag_logging` cvar**: the SDK
   installed in `rexglue/bin` (rebuilt 2026-09-09 23:29) did NOT have the cvar
   → the dual build failed to link `roster_trace.cpp`. Solution: rebuild the
   baseline runtime (`rexglue-sdk-0.10/out/build-win-vulkan-baseline`, targets
   `rexruntime rexgpu-xenos`) and reinstall DLL+lib in `rexglue/`.
5. **Dual + release builds compiled and linked** (11792 EU functions, +1). EU
   boot validated without FATAL (reads `data_eng.afs`, `data_cmn.afs`
   3983-3985, `data_yah.afs`).

### 3.4 Validation
- Headless EU boot (skip_launcher): process alive 25s+, without `UNREGISTERED
  indirect call`, the guest loading normal AFS.
- **Pending**: validation in the real game by the issue #4 user (Dragon
  Universe EU + START). For v1.1.4.

---

## 4. REPLIES TO ISSUES

### 4.1 Issue #6 — PS2 soundtrack + save states (reply)

Proposed reply:

- **PS2 soundtrack**: technically YES it is possible. The music is ADX audio
  in the game's audio AFS files (`adx_*.afs`); the runtime already supports a
  music mod (`og_music`, replaces the audio AFS per region). The ADX would
  have to be extracted from PS2 Budokai 3 (or from the RPCS3 mod) and packed
  as a music mod. Promise a guide / try it.
- **Save states**: NOT viable in the short term. The port is a **static
  recompilation** (not an emulator): there is no CPU/memory state to freeze as
  in an emulator. What CAN be offered: the game's native saving (memory cards)
  already works; and to "not lose the tournament" suggest retrying from the
  game's save. Explain the difference between an emulator and a recompilation.

### 4.2 Issue #5 — PortForge

- zamiba (PortForge's owner) replied that he will update `portforge-mediaitems`
  and come back "in a day or two" (2026-09-09). The owner already provided the
  `.forge.json`/`.mediaitem.json` in `portforge/`.
- **Action**: wait for his reply; if it does not come in ~5-7 days, send a
  polite ping. There is nothing to fix in our repo for now.

### 4.3 Issue #3 — Mac CrossOver

- Both findings are fixed in v1.1.2/v1.1.3 (ResolveRegion + gpu_backend). The
  red "Press START" splash is still open (cosmetic, D3DMetal/16-bit).
- **Action**: there is no new message. If the Mac tester tries the Vulkan
  backend in v1.1.3 and replies, evaluate the splash. Do not reply until they do.

### 4.4 Issue #1 — v1.0.4 bugs

- The owner asked for a repro in v1.1.2. No new reply.
- **Action**: do not reply yet. If the user confirms on v1.1.3 (real frame
  cap, language), address it point by point.

---

## 5. SUPERB DEBUGGING PLAN (design)

### Guiding principle
*Do not guess: read from the guest.* The codegen `generated/` +
`generated_eu/` is the REAL parser. Each diagnosis is validated with runtime
logs (guest PC, AFS reads, indirect calls).

### Phase D0 — Diagnostic instrumentation (the basis of everything)
1. **Capture module for unregistered indirect calls**: the runtime already logs
   `UNREGISTERED indirect call` with target/caller_lr/r3/r4/r11. Add an option
   to **dump the complete context** (guest callstack, source pointer table) to
   speed up diagnosing each new appearance.
2. **Image dump by MD5**: automate the `dump_image` tool so the log includes
   the source xex's MD5 and the section mapping → avoids §3.2's blocker (wrong
   xex).
3. **Trace of the 0x8201E348 table**: log which pointers of the
   event/combat table are dispatched, to detect ALL folded functions in one
   pass (not crash after crash).

### Phase D1 — Close the EU crash (#4)
1. Get the right EU xex (the one `generated_eu/` was generated from).
2. Apply Option A (re-codegen) or B (manual) from §3.3.
3. Validate Dragon Universe EU + START + EU demo battle (regression).

### Phase D2 — Intermittent `std::terminate` of `LaunchModule`
1. The try/catch already exists; the exact throw is missing. Instrument: log
   the exception + stack in the catch (there is already a minidump).
2. Strategy: ask the community for `logs/` + the minidump when it happens
   (rare); meanwhile, review the `LaunchModule` code in `src/` and the SDK
   (`rex_app.cpp`) looking for possible unexpected throws.

### Phase D3 — State hygiene
1. **Update `docs/01_estructura/ESTADO.md`** (it reflects 2026-08-18; it should
   say v1.1.3, ISO, i18n audited, EU crash pending).
2. Decide the fate of `out/analysis/guest_image/build/` (dump_image is useful →
   document it in `docs/04_herramientas/TOOLS.md` or leave it as it is).
3. Clean up dead cvars/code pending from Phase 2.1 of the roadmap (if not done:
   `dbz3_enabled_mods`, `PrepareRegionData`, `analyze_bin_hd.py`).

### Phase D4 — Game regression (community validation)
1. With v1.1.3 published, ask for a re-test in the open issues (#1
   framerate/language, #3 Vulkan Mac, #4 EU).
2. Establish a **report template** (log + xex MD5 + steps) so users give
   actionable data.

---

## 6. SUGGESTED ORDER OF EXECUTION

1. ✅ **D1 (EU crash #4)** — SOLVED (2026-09-10): `0x8215B378` registered
   manually; builds compiled; EU boot validated. Pending the user's validation.
2. ✅ **Reply to issues** — #6 (PS2 soundtrack + save states) replied; #4
   replied; #5 waiting for zamiba (PortForge, he promised "a day or two").
3. **D0** (instrumentation) — dump by MD5 + callstack on an indirect call:
   still pending (useful for the next crash of this pattern).
4. **D2** (terminate) — passive (wait for logs), low priority.
5. **D3** (docs/state hygiene) — ESTADO.md updated (2026-09-10); still to clean
   up `out/analysis/codegen_backup_20260909` when the fix is confirmed, or keep
   it as the reference of the tested EU codegen.
6. **D4** (community regression) — after publishing v1.1.4 (with the #4 fix),
   a mass re-test with a report template (log + xex MD5 + steps).

## 7. SUCCESS CRITERIA

- The Dragon Universe EU crash closed (validated by the issue #4 user).
- A reply given to #6 (and follow-up on #5).
- D0 instrumentation operational (dump by MD5 + callstack on an indirect call).
- `ESTADO.md` up to date (v1.1.3 + known debt).
- 0 regressions in US (in-game validation after touching the EU codegen).
