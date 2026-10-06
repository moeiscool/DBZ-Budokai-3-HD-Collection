# Session 2026-09-19 (2) — Disk I/O, focus diagnostics and QoL on losing focus

> Origin: SSGPrinceVegeta's slowness report (v1.2.1, RTX 5090,
> `internal_scale=3x` + MSAA, VB-Audio Virtual Cable audio, game on `E:` — see
> `docs/ANALISIS_RENDIMIENTO_LOGS_2026-09-18.md`). **The runtime's real read
> path** was investigated (not just its logs) and it was closed with a batch of
> safeguards + QoL. Release: **v1.2.5**.

## 1. What his logs say (and what they do NOT say)

His logs (part 1 and part 2) are **v1.2.1** and **cannot measure the
slowness**: in that version the AFS override log was unconditional (2 lines +
the full path per EVERY read), so 100% are AFS reads and there is not a single
frametime datum. Quantified: `dbz3_020.log` = 1718 lines / 145 s, bursts of
~24 reads/s and, during transitions, an **almost perfect 50 ms cadence
repeating the SAME entry** (`adx_usa.afs entry=4276`, ~0.5-0.9 s between
reads: the guest's audio streaming). In other words: normal guest behaviour,
not a pathological loop of ours. What did have a real cost: the unconditional
log (fixed in v1.2.3, gated by `dbz1_diag_logging`).

## 2. The runtime's read path (concrete findings)

`HostPathFile::ReadSync` (`rexglue-sdk-0.10/src/filesystem/devices/host_path_file.cpp`)
is **SYNCHRONOUS**: the guest thread blocks in `FileHandle::Read` →
`ReadFile` for the whole physical read. Findings:

1. **Expensive work was done on EVERY read even without mods**:
   `AfsModsPresent`-style lookups with a **`std::string` key per read**
   (allocates), two locks of the AFS index and, for `data_cmn.afs`, a
   **COMPLETE copy of the virtual AFS table** (`AfsGetVirtualTable` returned
   the vector by value) plus `AfsFindEntry` + `AfsFindModOverride` which
   **cannot find anything** when there are no mods.
2. The diagnostic flag was queried with `rex::cvar::GetFlagByName(...) ==
   "true"` (lookup + string conversion + compare per read).
3. **There was no I/O timing instrumentation at all** in the product: it was
   impossible to tell "slow disk" from "host overhead".
4. `FileHandle` opens with `FILE_ATTRIBUTE_NORMAL | FILE_FLAG_BACKUP_SEMANTICS`
   (without `NO_BUFFERING`: the OS cache works; without `SEQUENTIAL_SCAN`, which
   was deliberately **not** added: the guest re-reads the same audio entry,
   and that hint drops the pages behind it).

## 3. Changes (v1.2.5)

### Runtime (SDK)
- **`dbz3_io_logging`** (default **false** since the final v1.2.5; the first
  publication shipped it true and it was fixed under the same tag) +
  **`dbz3_io_slow_ms`** (25): a summary every 5 s (`dbz3: io reads=… phys=…
  cache=… mb=… pre_avg_us=… read_avg_us=… p95_us=… p99_us=… max_us=… slow=…
  opens=…`, percentiles from a log2 histogram) and one line per slow read. It
  is the product's only source of I/O timings → without it, a "it runs slow"
  report is not measurable.
- **Fast path without mods**: `AfsModsPresent()` → if there are no mods, the
  override lookup and the virtual table are skipped entirely (nothing can match).
- **`AfsGetVirtualTableFast`** (pointer to the cached vector, no copy) and
  `AfsFindEntry` only once per read.
- **`dbz1_diag_logging` read as a bool** (`REXCVAR_DECLARE`+`REXCVAR_GET`)
  instead of `GetFlagByName` per read.
- **`AfsIoRecordOpen`**: counts file opens (an open storm on a slow disk is a
  signal).
- **Sequential read-ahead** (`dbz3_io_readahead`, `dbz3_io_readahead_kb` =
  2048): 4 LRU streams per file; if the guest reads consecutively, a bigger
  block is read at once (256 KB..2 MB, adaptive) and the following reads are
  served from RAM. **Only active if there are NO mods** (with mods the
  byte→file mapping changes) and it is invalidated on write. On my SSD it
  **does not speed things up** (same total time: fewer but bigger reads); it
  is meant for **mechanical disks**, where it turns N seeks into 1 sequential
  stream.

### The most important clue: window focus
`dbz3: perf ... fg=0/1` — the focus state. Reason: **Windows/DWM halves the
presentation of a visible unfocused window** (unmistakable signature:
`fps=60.0` → exactly `fps=30.0`, not gradual; and with the window
**off-screen** it goes back to 60 because it is not composited). Without this
field, a log with `fg=0` at 30 fps reads as "the game is slow" when it really
is "the player alt-tabbed". **It is not a bug of ours** and it is not patched
(the only way would be stealing the foreground, which breaks
alt-tab/OBS/multi-monitor).

### QoL on losing focus (validated against other emulators)
- **Mute the audio** (`dbz3_mute_unfocused`, default ON): the app writes
  `dbz3_window_focused` on every focus change (`Dbz3App::OnWindowFocusChanged`)
  and the SDL callback mutes if `dbz3_mute_unfocused && !dbz3_window_focused`.
  It is the standard (Dolphin/RetroArch/PCSX2; Unreal has it as
  `UnfocusedVolumeMultiplier`).
- **Dim the screen** (`dbz3_dim_unfocused`, default ON): a full-screen ImGui
  overlay ("Game in the background" + "Audio is muted." + "Return to the
  window to keep playing."). It makes the state clear at a glance and keeps
  the screen from being "read" from afar.
- **There is NO real pause**: this runtime has no safe pause mechanism
  (`GraphicsSystem::Pause` exists but is dead and does not stop the guest; the
  alternative — suspending the guest's threads — can hang). Left for another
  session, with dedicated tests.

### Launcher
- **"When leaving the window"** section at the top of the **Video** tab (the
  two checkboxes), aimed at non-technical users, with tooltips explaining the
  behaviour without jargon (and clarifying that **the game keeps running**).

### i18n (complete round)
- Audit of 270 `i18n::T()` / 271 entries: **2 keys shown in English in
  IT/DE/FR** were closed (the "Executable detected…" and HD menu messages) and
  **13 new strings** were translated.
- `GpuTierLabel` ("Low/Medium/High") and `ModTypeLabel` ("swap B3"…) were
  already generated in English and painted raw: now they are translated in the
  UI (`ModTypeLabelText`, tier inline). The mod search keeps the raw ids.
- **5 dead entries** remain in `kTable[]` (music/SFX/voice sliders removed in
  v1.2.4) — cosmetic.
- ⚠️ The header of `i18n.cpp` says "GENERATED from …" but **there is no
  versioned generator**: the table is maintained by hand. Recovering one in
  `tools/` would be wise.

## 4. Bugs found and fixed during verification

- **`out_bytes_read` was not written** (our own regression when rewriting the
  physical path: the original passed the pointer straight to
  `FileHandle::Read`). The guest received valid bytes but an uninitialised
  counter and **hung on the loading screen**. Fixed before publishing (lesson:
  when wrapping a call, keep ALL of its observable effects).
- The initial test (offscreen, 60-150 s) saw no I/O because the opening is a
  video that does not go through AFS: you have to **reach the menu** to read
  the containers.

## 5. Verification

- Log: `mute_unfocused=true dim_unfocused=true` in `applied runtime settings`
  and `window focused` / `window in the background` events on every change.
- The ImGui overlay **is drawn in game** (capture with the FPS counter on,
  `Debug##overlay`). Capturing the **unfocused** window is not reliable with
  `PrintWindow` (it reactivates the window), so the dimming is validated by
  its condition (cvar + focus flag) and by the known overlay.
- Launcher: new section visible, no clipping, with "detected level: **High**"
  already translated.
- I/O measured (menu, SSD): without read-ahead `phys=112/112`; with it
  `phys=60 cache=52` in the same 5 s window.

## 6. Final v1.2.5 (asset replaced, same tag)

The diagnostics shipped on from the factory and the log created a file per run
without pruning old ones (138 in testing). Fixed **without bumping the
version**, replacing the v1.2.5 zip:

- `dbz3_io_logging` and `dbz3_perf_logging` → **OFF by default**; they are
  turned on from the Dev tab (the checkbox "Performance logging (every 5 s)",
  which did not exist before, was added).
- `logging.cpp` (`NextSequentialLogPath`) **prunes** the oldest `dbz3_NNN.log`
  at startup, respecting `log_max_files` (20).
- Verified: 138 → 20 files, 0 `dbz3: io` lines and 0 `dbz3: perf` with the
  default values. Canonical DLL `rexruntime.dll` **10,910,208 B**.

> On **PS5** the log goes to `/data/dbz3/dbz3-play.log` (warnings only, replaced
> at every start); see `docs/PS5.md`.
