# Session 2026-09-20 — TOML self-repair + UX against misuse of the scale

> Closes the real problems in SSGPrinceVegeta's logs (v1.2.1) and the
> misunderstanding about GPU usage. **No commit+push until the user validates.**

## 1. Real problems in Prince Vegeta's logs (v1.2.1)

Of his 27 logs reviewed (`Logs SSGPrinceVegeta/`), only **two** unique errors
appear:

1. `Failed to parse config ... unknown escape sequence '\G'` (in almost all).
   Path `E:\Game Roms\...` saved unescaped → **ALL settings are lost**.
2. `XThread::Execute - No function registered at 820D54C8` = it was booting the
   HD Collection menu (already covered by the xex auto-detection in v1.2.2).

Config: `preset=ultra internal_scale=3x msaa aniso=5 fsr=quality sharp=0.2
vrr cap=60` + audio endpoint `VB-Audio Virtual Cable` + `master_vol=0`.
`ultra` no longer exists → it is now an alias of `quality` (which lowers the
scale to 1x); to keep his 3x, use `manual` + 3x scale.

## 2. TOML self-repair (launcher, not SDK)

Before: if the toml did not parse, `rex::cvar::LoadConfig` swallowed the
exception and carried on with **defaults**, silently losing the config (and
the auto-save on close wrote over it → destroying the file).

Now (`src/launcher/settings.cpp`):

- `TomlParses(path)`: validates with **toml++** reading the file's **text**,
  not `parse_file(path.string())` (the path on Windows is ANSI → a folder with
  non-ASCII characters would give a false "corrupt").
- If it does not parse → `EscapeTomlStrings(path)` (idempotent) and retry:
  - **repaired** → `ConfigLoadState::kRepaired` (**green** notice).
  - **still broken** → `ConfigLoadState::kInvalid`, **copied to
    `dbz3_user.toml.bak`** and not loaded (**red** notice); the auto-save on
    close may write defaults, but the original stays in `.bak`.
- `LastConfigLoadState()` → the launcher shows it **above the tabs**
  (`launcher_state.cpp`, next to the game-data notice).
- ⚠️ `LoadUserSettings` runs **twice** per startup (OnConfigurePaths +
  OnPreSetup). The `kRepaired`/`kInvalid` state is **preserved** between calls
  (otherwise the second pass overwrites it with `kOk` and the notice is not
  shown).
- `#include <toml++/toml.hpp>` is available through `rex::runtime` (no CMake
  change).

Verified: corrupt toml → repaired (`\\` escaped) and **idempotent**;
unrepairable toml → `.bak` created and the original untouched; launcher
capture with the green and the orange notice.

## 3. UX against misuse of the internal scale (the cost is NOT the HD textures)

Measured (RTX 4070 SUPER, fight, `dbz3_175..178`):

| Config | GPU | Power | VRAM |
|---|---|---|---|
| **1x + FSR** (native) | **22-23 %** | **29-30 W** | 1.35 GB |
| 3x internal (supersampling) | 51 % | 50 W | 2.9 GB |
| 3x + HD x4 (old version) | **80 %** | **132 W** | 3.1 GB |

The usage in his capture (80 %/132 W) was the **old version with HD x4**.
`draw_resolution_scale` makes the guest **really render at Nx** (true
supersampling); FSR is left **inert** (frontbuffer ≥ output) and **there is no
extra pass** (`presenter.cpp:1065`). **There is no bug.**

Action (the user's request "keep 3x but warn loudly"), in the Video tab:

- **Wrapped** orange notice when `scale > 1` ("the GPU will work much harder…").
- **"Back to native (1x)"** one-click button (1x scale + persisted).
- Combo labels with their cost: "1x (native 720p) - recommended" … "4x … only
  high-end GPUs".
- Preset tooltip: **no preset raises the scale**.
- MSAA tooltip: moderate cost, can be dropped with a high scale.

## 4. i18n

New ES/EN/IT/DE/FR strings in `i18n.cpp` (supersampling notice, native button,
scale labels, tooltips, recovered/invalid config notices).

## 5. Pending

- **The user's visual validation** of the HUD (anti-ringing clamp + min size) —
  cannot be captured offscreen.
- **Commit+push** only with the user's OK.
