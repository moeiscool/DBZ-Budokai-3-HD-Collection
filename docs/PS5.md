# Building and installing the PS5 version

One command takes **your own copy** of *Dragon Ball Z: Budokai 3 HD Collection*
(Xbox 360) to a title installed on a **jailbroken PS5**. This page is the whole
procedure; it is written so you can follow it yourself or hand it to an AI
coding agent. How it works inside: [`ps5/README.md`](../ps5/README.md).

> **Status: experimental.** The PS5 build is adapted from
> [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp), which
> runs *Midnight Club: Los Angeles* (another ReXGlue recompilation) on PS5
> consoles. The DBZ3 runtime and host compile for the PS5 target, but the
> game has **not yet been run on a console**. Please report what happens
> (see "If something goes wrong").

Nothing of the game is in this repository, and no ready-made PS5 executable can
be offered: the executable contains the game's own code, recompiled, so
everyone builds theirs from their own copy. What the build produces is for you,
not for sharing. The PS5 files (`ps5/`) are GPL-3.0-or-later.

## What you need

| | |
|---|---|
| The game | Your own copy of **DBZ Budokai 3 HD Collection, Xbox 360**, US or EU/PAL: the disc image (`.iso`) or a folder with the extracted files. The Budokai 3 executable must match one of the checksums in [`baserom.md`](../baserom.md). |
| A console | A jailbroken PS5 that can run homebrew titles (mcla-recomp was tested on a PS5 Pro, firmware 13.42, and a PS5 Slim, firmware 12.70). |
| On the console | An FTP server payload (port 2121 by default) and a homebrew mounter that puts folders under `/data/homebrew` on the home screen (e.g. ShadowMountPlus). |
| A PC | Windows 10/11 with WSL2, or Arch Linux. x86-64, about 30 GB free, 16 GB of RAM or more. |
| Time | About 45 minutes the first time (the PS5 Vulkan driver alone takes about 20), plus the upload of the game data (about 2 GB per region). Later builds take a few minutes. |

The build host is **Arch Linux, run as root** (the PS5 Vulkan driver project
builds on Arch and the script installs packages with `pacman`). On Windows,
that is an Arch distribution under WSL2.

### Windows: set up WSL2 with Arch Linux

In PowerShell, as administrator:

```powershell
wsl --install --no-distribution
# restart if asked, then:
wsl --update
wsl --install -d archlinux
wsl -d archlinux -u root
```

Everything from here on is typed in that Linux shell. Your Windows drives are
under `/mnt`: `C:\Games\dbz3.iso` is `/mnt/c/Games/dbz3.iso`.

## Build and install

```bash
pacman -Sy --noconfirm git
cd /root
git clone https://github.com/moeiscool/DBZ-Budokai-3-HD-Collection.git
cd DBZ-Budokai-3-HD-Collection
bash ps5/make_ps5.sh --iso /mnt/c/path/to/your.iso --console 192.168.1.50
```

or, with the game already extracted to a folder:

```bash
bash ps5/make_ps5.sh --game-dir /mnt/c/path/to/game --console 192.168.1.50
```

Use your console's address for `--console`; leave it out to build without
uploading (the script then prints what to copy where). Keep the repository
inside the Linux file system (under `/root`), not under `/mnt/c`: it is much
faster and avoids Windows line endings.

What the script does, in order. Each step is skipped when its result already
exists, so after a failure or an update you run the same command again:

1. Installs the host packages.
2. Builds the PS5 toolchain and Vulkan driver
   ([mihawk-99/PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan), GPL-3)
   into `/root/ps5vk`.
3. Clones the ReXGlue SDK v0.10.0 into `/root/dbz3/rexglue-sdk`, copies in
   DBZ3's runtime (`patches/rexglue-sdk/`) and applies the PS5 patches
   (`ps5/patches/`).
4. Builds the recompiler for your PC.
5. Finds the Budokai 3 executable in your copy by checksum (US or EU), stages
   it with the region data in `ps5-game/`, and recompiles it into
   `generated/` (US) or `generated_eu/` (EU).
6. Builds the runtime for PS5.
7. Makes the tile and backgrounds from the dashboard art on your disc, when
   there is any (or uses yours, see below).
8. Compiles the game for PS5 and packages the title into
   `out/ps5-title/PPSA99300`.
9. Uploads the game data to `/data/dbz3/game` and the title to
   `/data/homebrew/PPSA99300`, checking every file's size.

Logs of every step are in `/root/dbz3/logs`; when a step fails, the script
prints the end of its log and its path.

### Options

| Option | |
|---|---|
| `--iso PATH` / `--game-dir DIR` | Your copy of the game. Not needed again once `ps5-game/` is staged. |
| `--console IP` | Upload to the console. |
| `--ftp-port N` | The console's FTP port (default 2121). |
| `--title-id ID` | The title's id on the console (default `PPSA99300`). |
| `--tile IMAGE` | Your own picture for the home-screen tile (any common format, resized to 512x512). |
| `--theme FILE.at9` | Your own home-screen theme, already in ATRAC9 (48 kHz stereo). |
| `--art-dir DIR` | Your own `icon0.png`, `pic0.dds`, `pic1.dds` (and optionally `snd0.at9`). |
| `--with-mods` | Also upload the contents of this repository's `mods/` folder to `/data/dbz3/mods`. |
| `--test-build` | Keep the test scaffolding: the title waits for `ps5/title_log_client.py` to connect and logs over the network. For development. |
| `--jobs N` | Parallel compile jobs. |

## On the console

1. Start your FTP server payload before running the script with `--console`.
2. After the upload, let your homebrew mounter pick up
   `/data/homebrew/PPSA99300`. "DBZ Budokai 3 HD" then appears on the home
   screen.
3. Start it. The first start takes longer while shaders are compiled and
   cached; later ones load them from the cache.

| Path on the console | |
|---|---|
| `/data/homebrew/PPSA99300` | The title |
| `/data/dbz3/game` | The game data from your copy, unmodified (`default.xex`, `us/` and/or `eu/`) |
| `/data/dbz3/dbz3_user.toml` | Settings: the same file the PC launcher writes (copy yours over to reuse it) |
| `/data/dbz3/mods/` | Mods, exactly as in the PC `mods/` folder |
| `/data/dbz3/user_data/dbz3/` | Saves and the shader cache |
| `/data/dbz3/dbz3-play.log` | Warnings, errors and the crash report of the last start |

### Differences from the PC version

- **No launcher.** The game boots straight in. Change settings by editing
  `/data/dbz3/dbz3_user.toml` (language, region, internal resolution scale,
  volume, etc.), or make the file with the PC launcher and copy it.
- **Region.** The build is made from the executable you supply (US or EU) and
  plays that region only.
- **Controller.** The DualSense is presented to the game as an Xbox 360 pad:
  Cross/Circle/Square/Triangle = A/B/X/Y, L1/R1 = shoulders, L2/R2 = triggers,
  OPTIONS = Start, touchpad click = Back.
- **Not available:** Model Swap and the mod tools (use ready-made mods), the
  D3D12-only features (HD texture upscale, texture dump, DLSS/FSR 3). Texture
  packs work.
- **Audio** is stereo.

## Updating

```bash
cd /root/DBZ-Budokai-3-HD-Collection
git pull
bash ps5/make_ps5.sh --console 192.168.1.50
```

Only what changed is rebuilt, and only the title is uploaded again. If an
update changes `patches/rexglue-sdk/` or `ps5/patches/`, remove the SDK checkout
so it is cloned and patched afresh:
`rm -rf /root/dbz3/rexglue-sdk /root/dbz3/build-ps5 /root/dbz3/build-host`.

## If something goes wrong

| Symptom | What to do |
|---|---|
| `this script needs Arch Linux` | Install Arch under WSL2 as above. |
| Step 2 fails | Its log is `/root/ps5vk-arch.log`. Usually a failed download: run again. |
| `the PS5 SDK patch does not apply` | Remove `/root/dbz3/rexglue-sdk` and run again. If it still fails, `patches/rexglue-sdk/` changed without `ps5/patches/` being updated (see `ps5/README.md`). |
| `no Budokai 3 executable (US or EU)` | The copy is not the supported release, or the executable is modified. Compare with `baserom.md`. |
| `no FTP server at ...` | Start the FTP payload, check the address and `--ftp-port`. |
| "Call to invalid or unregistered function at guest address ..." in `dbz3-play.log` | The recompiler missed a function reached only through a pointer. Open an issue with that line; the fix is an entry in `dbz3_config.toml` (or `dbz3_config_eu.toml`). |
| An overlay with frame rate/temperatures over the game | That is your homebrew enabler's monitor, not the game (with OnionHEN: `[overlay] enabled=false` in `/data/OnionHEN/config.ini`). |
| The game closes with nothing useful in the log | Fetch `/data/dbz3/dbz3-play.log` over FTP before starting again (it is replaced at every start) and open an issue with it, your console model and firmware. A test build (`--test-build`) streams the full log to the PC: run `python3 ps5/title_log_client.py <console ip>` while it starts. |

## For an AI agent doing this for someone

- Ask the user for their game copy (ISO path or folder) and the console's IP.
  Never look for or download game files; the user must supply their own.
- Check the host first: `/etc/os-release` must say Arch Linux and `id -u` must
  be 0. On Windows, drive the Linux side with `wsl -d archlinux -u root -- <command>`.
- The whole job is the one command above; it is safe to run again and resumes
  at the first missing result. A failed step prints `FAILED: <step>`; read its
  log in `/root/dbz3/logs/<step>.log`, fix the cause, run again. Do not edit
  generated files or the SDK checkout by hand.
- Writing to the console happens only in step 9 and only with `--console`; it
  writes to `/data/dbz3` and `/data/homebrew/<title id>` and deletes nothing.
  Confirm with the user before uploading if they have not asked for it.
- Never commit or share `ps5-game/`, `generated*/`, `out/`, `*.xex` or anything
  built from them.

## Credits

- [holdmysocks/mcla-recomp](https://github.com/holdmysocks/mcla-recomp) — the
  PS5 runtime port, host, title packaging and build scripts this is adapted
  from (GPL-3.0-or-later).
- [mihawk-99/PS5_Vulkan](https://github.com/mihawk-99/PS5_Vulkan) — the RADV
  Vulkan driver and toolchain for PS5 homebrew (GPL-3).
- [ps5-payload-dev/sdk](https://github.com/ps5-payload-dev/sdk) — the PS5
  payload SDK.
- The ReXGlue SDK (BSD-3) and Xenia.
