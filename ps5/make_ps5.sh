#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# One command from your own copy of DBZ Budokai 3 HD Collection (Xbox 360) to
# the game installed on a jailbroken PS5.
#
#   bash ps5/make_ps5.sh --iso /path/to/your.iso [--console 192.168.1.50]
#   bash ps5/make_ps5.sh --game-dir /path/to/extracted/game [--console ...]
#
# Host: Arch Linux, as root (a fresh Arch under WSL2 on Windows works; see
# docs/PS5.md). Everything is built on your machine from your own copy: the
# game is not in this repository, and what this script produces from it is
# yours to keep, not to share.
#
# Adapted from holdmysocks/mcla-recomp (ps5/make_ps5.sh, GPL-3.0-or-later).
# Each step is skipped when its result is already there, so run the same
# command again after a failure or an update.
#
#   --iso PATH        your disc image (US or EU/PAL)
#   --game-dir DIR    or a folder with the game (the executable, e.g.
#                     DBZ3/yae3_xenon.xex or default.xex, and us/ and/or eu/)
#                     Neither is needed again once ps5-game/ has been staged.
#   --console IP      upload the title and the game data to the console (FTP)
#   --ftp-port N      the console's FTP port (default 2121)
#   --title-id ID     the title's id on the console (default PPSA99300)
#   --tile IMAGE      your own picture for the home-screen tile (resized to 512x512)
#   --theme FILE.at9  your own home-screen theme (ATRAC9, 48 kHz stereo)
#   --art-dir DIR     your own icon0.png/pic0.dds/pic1.dds/snd0.at9
#   --with-mods       also upload this repository's mods/ folder contents
#   --test-build      keep the test scaffolding (waits for ps5/title_log_client.py)
#   --jobs N          parallel compile jobs (default: all cores)
#
# Locations, changeable through the environment:
#   PS5VK   (/root/ps5vk)   the Vulkan driver project and its toolchain
#   WORK    (/root/dbz3)    the SDK checkout and all build trees
set -euo pipefail

here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$here/.." && pwd)
PS5VK=${PS5VK:-/root/ps5vk}
WORK=${WORK:-/root/dbz3}
driver="$PS5VK/PS5_Vulkan"
sdk="$driver/.deps/native/ps5-payload-sdk"
rex_src="$WORK/rexglue-sdk"
rex_build="$WORK/build-ps5"
rex_host="$WORK/build-host"
rex_tag=v0.10.0
rex_commit=f5337cdc947ff6d4c4196737e2c807a48f2a1fc2
staged="$repo/ps5-game"

iso= game_dir= console= ftp_port=2121 title_id=PPSA99300 art_dir= tile= theme= play=1 with_mods= jobs=$(nproc)
while [ $# -gt 0 ]; do
    case $1 in
        --iso) iso=$2; shift 2 ;;
        --game-dir) game_dir=$2; shift 2 ;;
        --console) console=$2; shift 2 ;;
        --ftp-port) ftp_port=$2; shift 2 ;;
        --title-id) title_id=$2; shift 2 ;;
        --art-dir) art_dir=$2; shift 2 ;;
        --tile) tile=$2; shift 2 ;;
        --theme) theme=$2; shift 2 ;;
        --with-mods) with_mods=1; shift ;;
        --test-build) play=; shift ;;
        --jobs) jobs=$2; shift 2 ;;
        -h|--help) sed -n '2,37p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
    esac
done

step() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nFAILED: %s\n' "$*" >&2; exit 1; }
mkdir -p "$WORK"
logs="$WORK/logs"; mkdir -p "$logs"
logged() {
    local name=$1; shift
    if ! "$@" > "$logs/$name.log" 2>&1; then
        tail -25 "$logs/$name.log" >&2
        fail "$name (full log: $logs/$name.log)"
    fi
}

[ "$(id -u)" -eq 0 ] || fail "run as root (the driver project's build installs packages and writes under /root)"
command -v pacman > /dev/null || fail "this script needs Arch Linux (pacman); see docs/PS5.md"

# ---------------------------------------------------------------------------
step "1/9 host packages"
logged packages pacman -Sy --noconfirm --needed base-devel clang llvm lld cmake ninja git curl rsync python \
    python-pillow ffmpeg unzip libx11 libxext libxi libxcursor libxrandr libxinerama libxss libxkbcommon \
    libxtst libxfixes libxrender mesa

# ---------------------------------------------------------------------------
step "2/9 PS5 toolchain and Vulkan driver (about 20 minutes the first time)"
if [ -f "$driver/.deps/native/radv-release/lib/libvulkan_radeon.ps5.a" ] && [ -x "$driver/build/host/ps5-native-tool" ]; then
    echo "already built: $driver"
else
    [ "$PS5VK" = /root/ps5vk ] || fail "the driver build script works in /root/ps5vk; leave PS5VK unset"
    bash "$here/build_ps5_vulkan_driver.sh" || true
    grep -q "ALL STEPS DONE" /root/ps5vk-arch.log || { tail -25 /root/ps5vk-arch.log >&2; fail "driver build (log: /root/ps5vk-arch.log)"; }
fi
[ -f "$sdk/toolchain/prospero.cmake" ] || fail "the PS5 toolchain is missing under $sdk"

# ---------------------------------------------------------------------------
step "3/9 ReXGlue SDK $rex_tag with DBZ3's runtime patches and the PS5 port"
if [ ! -f "$rex_src/.dbz3-ps5-patched" ]; then
    if [ ! -d "$rex_src/.git" ]; then
        logged sdk-clone git clone --recursive --branch "$rex_tag" https://github.com/rexglue/rexglue-sdk.git "$rex_src"
    fi
    [ "$(git -C "$rex_src" rev-parse HEAD)" = "$rex_commit" ] || fail "the SDK checkout is not $rex_tag ($rex_commit)"
    git -C "$rex_src" diff --quiet || fail "the SDK checkout has changes: remove $rex_src and run again"
    # 1. DBZ3's runtime (AFS mid-insert, mods, texture packs, ...): whole files.
    cp -a "$repo/patches/rexglue-sdk/." "$rex_src/"
    # 2. The PS5 platform layer, rebased onto those files.
    git -C "$rex_src" apply "$here/patches/rexglue-v0.10.0-dbz3-ps5.patch" \
        || fail "the PS5 SDK patch does not apply (patches/rexglue-sdk changed? see ps5/README.md)"
    git -C "$rex_src/thirdparty/FFmpeg" apply "$here/patches/rexglue-ffmpeg-ps5-config.patch" \
        || fail "the FFmpeg patch does not apply"
    touch "$rex_src/.dbz3-ps5-patched"
else
    echo "already patched: $rex_src"
fi

# ---------------------------------------------------------------------------
step "4/9 the recompiler (rexglue), for this machine"
rexglue=$(find "$rex_host" "$rex_src/out" -maxdepth 4 -name rexglue -type f -perm -u+x 2> /dev/null | head -1 || true)
if [ -z "$rexglue" ]; then
    logged host-configure cmake -S "$rex_src" -B "$rex_host" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_CXX_STANDARD=23 \
        -DCMAKE_C_FLAGS=-march=x86-64-v2 -DCMAKE_CXX_FLAGS=-march=x86-64-v2 \
        -DREXGLUE_USE_VULKAN=ON -DREXGLUE_ENABLE_TRACY=OFF -DREXGLUE_ENABLE_FIDELITYFX=OFF \
        -DREXGLUE_BUILD_TESTS=OFF
    logged host-build ninja -C "$rex_host" -j "$jobs" rexglue
    rexglue=$(find "$rex_host" "$rex_src/out" -maxdepth 4 -name rexglue -type f -perm -u+x | head -1)
fi
[ -x "$rexglue" ] || fail "the recompiler was not built"
echo "recompiler: $rexglue"

# ---------------------------------------------------------------------------
step "5/9 your game: stage it, then recompile its executable"
if [ ! -f "$staged/default.xex" ] || [ ! -f "$staged/region.txt" ]; then
    if [ -n "$iso" ]; then
        [ -f "$iso" ] || fail "no such file: $iso"
        logged stage python3 "$here/stage_game.py" --iso "$iso" --out "$staged" --xex-out "$repo" --art-out "$WORK/title-art-source"
    elif [ -n "$game_dir" ]; then
        [ -d "$game_dir" ] || fail "no such folder: $game_dir"
        logged stage python3 "$here/stage_game.py" --game-dir "$game_dir" --out "$staged" --xex-out "$repo" --art-out "$WORK/title-art-source"
    else
        fail "ps5-game/ is empty: give your disc image with --iso or your game folder with --game-dir"
    fi
fi
region=$(tr -d '\r\n ' < "$staged/region.txt")
case $region in
    us) manifest=dbz3_manifest.toml; generated=generated; xex=yae3_xenon.xex ;;
    eu) manifest=dbz3_manifest_eu.toml; generated=generated_eu; xex=yae3_xenon_eu.xex ;;
    *) fail "ps5-game/region.txt says '$region' (expected us or eu)" ;;
esac
[ -f "$repo/$xex" ] || cp "$staged/default.xex" "$repo/$xex"
echo "region: $region ($xex)"
# The recompiled code depends on the function lists and on the recompiler:
# regenerate when any of them is newer than the result.
stamp="$repo/$generated/.generated-ps5"
if [ ! -f "$stamp" ] || [ -n "$(find "$repo/dbz3_config.toml" "$repo/dbz3_config_eu.toml" "$repo/$manifest" "$rexglue" -newer "$stamp" -print -quit)" ]; then
    ( cd "$repo" && logged codegen "$rexglue" codegen "$manifest" )
    if [ "$region" = eu ]; then
        # EU bctr sites mis-detected as one-entry jump tables (AGENTS.md 9.1).
        logged fix-eu-bctr python3 "$repo/tools/fix_eu_bctr.py" --apply "$repo/$generated"
    fi
    grep -q 'REX_PLATFORM_PS5' "$repo/$generated"/*_pch.h || fail "the generated header lacks the PS5 rule (unpatched recompiler?)"
    touch "$stamp"
else
    echo "generated code is up to date"
fi
echo "generated sources: $(ls "$repo/$generated"/*.cpp | wc -l)"

# ---------------------------------------------------------------------------
step "6/9 the runtime, for PS5"
if [ ! -f "$rex_build/build.ninja" ]; then
    # -flto=thin: 5-8% more draws a second on the console (mcla-recomp).
    logged ps5-configure cmake -S "$rex_src" -B "$rex_build" -G Ninja \
        -DCMAKE_TOOLCHAIN_FILE="$sdk/toolchain/prospero.cmake" \
        -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=23 \
        -DCMAKE_C_FLAGS="-march=znver2 -flto=thin" \
        -DCMAKE_CXX_FLAGS="-march=znver2 -fexperimental-library -flto=thin" \
        -DREXGLUE_USE_D3D12=OFF -DREXGLUE_USE_VULKAN=ON -DREXGLUE_ENABLE_TRACY=OFF \
        -DREXGLUE_ENABLE_FIDELITYFX=OFF
fi
logged ps5-runtime ninja -C "$rex_build" -j "$jobs" rexruntime rexgpu-xenos

# ---------------------------------------------------------------------------
step "7/9 the title's tile and backgrounds"
if [ -z "$art_dir" ] && [ -f "$WORK/title-art-source/nxeart" ]; then
    art_dir="$WORK/title-art"
    if [ ! -f "$art_dir/icon0.png" ]; then
        # From the dashboard art on your own disc; none is in the repository.
        if python3 "$here/make_title_art.py" "$WORK/title-art-source" "$WORK/title-art-source" > "$logs/art-extract.log" 2>&1; then
            [ -d "$driver/.deps/native/bc7enc_rdo" ] || ( cd "$driver" && logged art-tools bash tools/setup-asset-dependencies.sh )
            mkdir -p "$art_dir"
            ( cd "$driver" && logged art-convert bash tools/prepare-assets.sh --icon "$WORK/title-art-source/icon.png" \
                --background "$WORK/title-art-source/background.png" --output-directory "$art_dir" )
        else
            echo "no dashboard art usable on the disc (see $logs/art-extract.log); the driver's default tile is used"
            art_dir=
        fi
    else
        echo "already made: $art_dir"
    fi
fi
if [ -n "$tile$theme" ]; then
    [ -z "$tile" ] || [ -f "$tile" ] || fail "no such file: $tile"
    [ -z "$theme" ] || [ -f "$theme" ] || fail "no such file: $theme"
    rm -rf "$WORK/title-art-own"; mkdir -p "$WORK/title-art-own"
    [ -z "$art_dir" ] || cp -r "$art_dir/." "$WORK/title-art-own/"
    art_dir="$WORK/title-art-own"
    if [ -n "$tile" ]; then
        python3 - "$tile" "$art_dir/icon0.png" <<'PY' || fail "the tile could not be converted"
import sys
from PIL import Image
Image.open(sys.argv[1]).convert("RGBA").resize((512, 512), Image.LANCZOS).save(sys.argv[2])
PY
    fi
    [ -z "$theme" ] || cp "$theme" "$art_dir/snd0.at9"
fi
echo "art: ${art_dir:-default tile of the driver project}"

# ---------------------------------------------------------------------------
step "8/9 the game for PS5 (10 to 30 minutes the first time)"
export PS5_VULKAN="$driver" REX_SRC="$rex_src" REX_BUILD="$rex_build" DBZ3_PS5_WORK="$WORK/game-ps5" JOBS="$jobs"
export DBZ3_REGION="$region" TITLE="$title_id" DBZ3_TITLE_NAME="DBZ Budokai 3 HD" ART_DIR="$art_dir"
if [ -n "$play" ]; then
    export DBZ3_PLAY=1 DBZ3_LOG_LEVEL=warning
fi
logged game-build bash "$here/build_game.sh"
dist="$driver/dist/$title_id"
[ -f "$dist/eboot.bin" ] || fail "no eboot.bin in $dist"
out="$repo/out/ps5-title/$title_id"
rm -rf "$out"; mkdir -p "$(dirname "$out")"; cp -r "$dist" "$out"
echo "title: $out ($(du -sh "$out" | cut -f1))"

# ---------------------------------------------------------------------------
step "9/9 the console"
if [ -z "$console" ]; then
    cat <<EOF
No --console given, so nothing was uploaded. To install by hand, copy
  $out          ->  /data/homebrew/$title_id   on the console
  $staged       ->  /data/dbz3/game             on the console
and see docs/PS5.md, "On the console".
EOF
    exit 0
fi
ftp="ftp://$console:$ftp_port"
curl -s --max-time 15 "$ftp/data/" > /dev/null || fail "no FTP server at $console:$ftp_port (start one on the console first)"
remote_size_of() {
    { curl -s --max-time 30 -I "$ftp$1" 2> /dev/null || true; } | tr -d '\r' | awk '/Content-Length/{print $2}'
}
put() {
    local source=$1 target=$2 local_size remote_size
    local_size=$(stat -c %s "$source")
    remote_size=$(remote_size_of "$target")
    if [ "$local_size" = "$remote_size" ] && [ "${3:-}" != always ]; then
        echo "  same size, kept: $target"
        return
    fi
    echo "  uploading $target ($local_size bytes)"
    local attempt
    for attempt in 1 2 3; do
        curl -s -S --ftp-create-dirs -T "$source" "$ftp$target" && break
        [ "$attempt" -lt 3 ] || fail "upload of $target (run the same command again to continue; files already there are kept)"
        echo "  retrying $target"
        sleep 10
    done
    remote_size=$(remote_size_of "$target")
    [ "$local_size" = "$remote_size" ] || fail "$target is $remote_size bytes on the console, $local_size here"
}
echo "game data to /data/dbz3/game"
( cd "$staged" && find . -type f ! -name region.txt | sed 's#^\./##' | sort ) | while read -r file; do
    put "$staged/$file" "/data/dbz3/game/$file"
done
if [ -n "$with_mods" ] && [ -d "$repo/mods" ]; then
    echo "mods to /data/dbz3/mods"
    ( cd "$repo/mods" && find . -type f ! -name README.md | sed 's#^\./##' | sort ) | while read -r file; do
        put "$repo/mods/$file" "/data/dbz3/mods/$file"
    done
fi
echo "title to /data/homebrew/$title_id"
( cd "$out" && find . -type f | sed 's#^\./##' | sort ) | while read -r file; do
    put "$out/$file" "/data/homebrew/$title_id/$file" always
done
cat <<EOF

Done. On the console, "DBZ Budokai 3 HD" appears on the home screen once your
homebrew mounter has picked up /data/homebrew/$title_id (see docs/PS5.md,
"On the console").
EOF
