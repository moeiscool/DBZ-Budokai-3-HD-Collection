# Texture dump fix (issue #11) — 2026-09-21

> Released in **v1.2.8**. Affects **Windows/D3D12** (the dump is a feature of
> the D3D12 layer; it does not exist on Linux/Vulkan or PS5).

## Symptom

User `mellisxboxkp` (issue #11, "Error al dumpear texturas") enabled dev mode,
enabled the texture dump, chose a folder and played: **no file appeared**. The
folder stayed empty.

## Root cause: SHARED cvar registry + discarded duplicate registration

The cvar registry (`rex::cvar::GetRegistry()`) is **single and shared** between
the executable (`dbz3.exe`) and the plugins, because `cvar.cpp` lives in
`rexcore`, an **OBJECT** library whose objects are compiled into
`rexruntime.dll`, which both the exe and `rexgpu-xenos.dll` link.

The **storage** of each cvar (`FLAGS_<name>_storage_()`), on the other hand,
is a `static` **per module**: each DLL that defines the cvar has its own.

`RegisterFlag` **rejects the second definition of the same name**:

```
[error] cvar: duplicate registration of 'dbz3_texture_dump'; second registration ignored
```

Since the launcher is loaded before the plugin, the entry that stays in the
registry is **the launcher's**, and its setter writes **the launcher's**
storage.

But the plugin read the dump path with `REXCVAR_GET`:

```cpp
const std::string dump_dir = REXCVAR_GET(dbz3_texture_dump);  // the plugin's storage
```

**Nobody wrote** that storage (its registration was discarded), so it was
always `""` and `DumpTextureToDds` left through the first branch:

```cpp
if (dump_dir.empty()) return;   // nothing was ever dumped
```

The same happened with `dbz3_texture_packs`, but packs did **not** fail
because they are read with `REXCVAR_QUERY` (resolution by name through the
registry, which returns the launcher's value):

```cpp
const std::string list = REXCVAR_QUERY(std::string, dbz3_texture_packs);
```

> ⚠️ The historical note "the plugin reads its own registration from the TOML"
> was **wrong**: the plugin never reads the TOML. What persisted the path was
> the launcher (its storage -> `SaveConfig`), and the plugin did not see it.

## Fix

1. `rexglue-sdk-0.10/src/graphics/d3d12/texture_cache.cpp`: the dump reads the
   path with **`REXCVAR_QUERY(std::string, dbz3_texture_dump)`** (like the
   packs) and **no longer defines** the cvar (the launcher defines it).
2. `rexglue-sdk-0.10/src/graphics/dbz3_texture_pack.cpp`: the duplicate
   definition of `dbz3_texture_packs` is removed as well (it only produced the
   duplicate-registration error; the value is read via `REXCVAR_QUERY`).

`dbz3_texture_dump_max` does not change: only the plugin defines it, so its
`REXCVAR_GET` does work.

## Verification (measured, same TOML and same harness)

Harness: `%TEMP%\opencode\dump_test.ps1` (writes `dbz3_texture_dump` into
`dbz3_user.toml`, starts the game with `dbz3_skip_launcher=true`, hides the
window, waits and counts the `.dds` files).

| Build | DDS | Log |
|---|---|---|
| **Published v1.2.7 DLL** | **0** | `duplicate registration of 'dbz3_texture_dump'` |
| **DLL with the fix** | **96** (2.5 MB) | `dbz3: volcado de texturas activado en '...'` |

After the fix, with a test pack made from the dumped DDS files themselves
(`mods/_vtest`, 5 files in pack format):

```
dbz3: texture packs detected ... : 1 -> '...\mods\_vtest'
dbz3: pack de texturas '_vtest' -> 5 texturas
dbz3: pack '_vtest' reemplaza 128x512 (fmt 19) -> 128x512 (x1)
dbz3: pack '_vtest' subido 128x512 (10 niveles, 523776 B)
```

And the log has **no** `duplicate registration` or `[error]` lines.

## Note for the future

If a `dbz3_*` cvar is added that the launcher **also** defines, the plugin must
read it with **`REXCVAR_QUERY`**, never with `REXCVAR_GET`: the plugin's
definition is discarded and its storage stays at the default value.
