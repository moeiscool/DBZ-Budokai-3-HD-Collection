#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Build DBZ Budokai 3 for PS5 as an installable title: the recompiled code
# (generated/ for US, generated_eu/ for EU), the DBZ3 host sources the
# recompiled code and the PS5 host call into, ps5/main_ps5.cpp and the
# runtime's static libraries, linked with the PS5 Vulkan driver by
# ps5/title_build.sh. Adapted from holdmysocks/mcla-recomp ps5/game/build.sh.
#
# Run by ps5/make_ps5.sh after the runtime has been built for PS5 and the
# codegen has produced the region's generated folder.
#
# Environment:
#   DBZ3_REGION   us | eu (required)
#   PS5_VULKAN    the driver project (default /root/ps5vk/PS5_Vulkan)
#   REX_SRC       the patched SDK checkout (default /root/dbz3/rexglue-sdk)
#   REX_BUILD     its PS5 build tree (default /root/dbz3/build-ps5)
#   DBZ3_PS5_WORK work folder (default /root/dbz3/game-ps5)
#   TITLE         title id (default PPSA99300)
#   DBZ3_TITLE_NAME  name on the home screen
#   ART_DIR       tile/backgrounds in the console's formats (optional)
#   DBZ3_PLAY=1   a build for playing (log file on the console, no waiting
#                 for ps5/title_log_client.py); DBZ3_LOG_LEVEL (e.g. warning)
#   JOBS          parallel compiles
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$here/.." && pwd)
region=${DBZ3_REGION:?set DBZ3_REGION to us or eu}
driver=${PS5_VULKAN:-/root/ps5vk/PS5_Vulkan}
sdk="$driver/.deps/native/ps5-payload-sdk"
runtime_src=${REX_SRC:-/root/dbz3/rexglue-sdk}
runtime_build=${REX_BUILD:-/root/dbz3/build-ps5}
libs="$runtime_src/out/ps5-amd64"
work=${DBZ3_PS5_WORK:-/root/dbz3/game-ps5}-$region
jobs=${JOBS:-$(nproc)}
title=${TITLE:-PPSA99300}
cxx="$sdk/bin/prospero-clang++"

case $region in
    us) generated_dir=generated; region_define= ;;
    eu) generated_dir=generated_eu; region_define=-DDBZ3_EU_VARIANT=1 ;;
    *) echo "DBZ3_REGION must be us or eu" >&2; exit 2 ;;
esac
[ -f "$repo/$generated_dir/sources.cmake" ] || { echo "$generated_dir/ is missing: run the codegen first" >&2; exit 1; }
mkdir -p "$work/obj" "$work/src"

# A local copy of the sources (LF line endings; fast to read when the
# repository is on a Windows drive under WSL).
rsync -a --delete "$repo/$generated_dir/" "$work/src/$generated_dir/"
rsync -a --delete --include='*/' --include='*.cpp' --include='*.h' --include='*.inc' --exclude='*' \
    "$repo/src/" "$work/src/src/"
mkdir -p "$work/src/ps5"
for file in main_ps5.cpp ps5_pad_input.h ps5_audio.h title_log.h log_fd_sink.h; do
    tr -d '\r' < "$here/$file" > "$work/src/ps5/$file.new"
    cmp -s "$work/src/ps5/$file.new" "$work/src/ps5/$file" 2> /dev/null \
        && rm "$work/src/ps5/$file.new" || mv "$work/src/ps5/$file.new" "$work/src/ps5/$file"
done

pch_header=$(ls "$work/src/$generated_dir"/*_pch.h 2> /dev/null | head -1 || true)
[ -n "$pch_header" ] || { echo "no *_pch.h in $generated_dir/" >&2; exit 1; }
# The generated header has its own copy of the rule for the 0xE0000000
# physical range's 4 KiB host offset, and it must name PS5 (16 KiB pages) as
# the runtime does, or the game stalls waiting for a GPU that never sees its
# commands (mcla-recomp). The SDK patch fixes the codegen template.
grep -q 'REX_PLATFORM_PS5' "$pch_header" \
    || { echo "$(basename "$pch_header") lacks the PS5 rule: regenerate with the patched recompiler" >&2; exit 1; }

# The runtime's own defines and include paths, taken from its build.
ninja -C "$runtime_build" -t commands rexruntime > "$work/commands.txt"
command=$(grep -m1 'xmemory\.cpp\.o ' "$work/commands.txt")
inherited=$(printf '%s' "$command" | tr ' ' '\n' | grep -E '^(--sysroot=|-D|-I)' | grep -v -E '^-DNDEBUG$' | tr '\n' ' ')
inherited_system=$(printf '%s' "$command" | grep -o -E -- '-isystem [^ ]+' | tr '\n' ' ')
# -ffp-contract=off: the desktop build never fuses a multiply and an add;
# with znver2 the compiler would, and guest floating point would differ.
flags="$inherited $inherited_system -march=znver2 -fexperimental-library -O3 -DNDEBUG -std=c++23 -fPIC \
  -mcmodel=large -fno-strict-aliasing -fno-char8_t -ffp-contract=off -g0 -w $region_define \
  -I$work/src -I$work/src/src -I$work/src/$generated_dir -I$runtime_src/thirdparty/tomlplusplus/include"
printf '%s' "$flags" > "$work/flags.new"
if ! cmp -s "$work/flags.new" "$work/flags.txt" 2> /dev/null; then
    rm -f "$work"/obj/*.o "$work"/obj/*.pch
    mv "$work/flags.new" "$work/flags.txt"
fi

pch="$work/obj/$(basename "$pch_header").pch"
if [ ! -e "$pch" ] || [ -n "$(find "$work/src/$generated_dir" -name '*.h' -newer "$pch" -print -quit)" ]; then
    echo "precompiling $(basename "$pch_header")"
    ( cd "$runtime_build" && eval "\"$cxx\" $flags -x c++-header -o \"$pch\" -c \"$pch_header\"" )
    rm -f "$work"/obj/gen_*.o
fi

# The DBZ3 host sources the game needs on the console. Left out: src/main.cpp
# (the windowed ReXApp host), the ImGui launcher (launcher_state, ui_kit,
# mod_pipeline, update_check) and the in-game ImGui menu.
host_sources=(region mods native_mods launcher/settings launcher/i18n)
if [ "$region" = us ]; then
    # As in CMakeLists.txt: the hooks and the roster/select extensions use US
    # guest addresses and are only in builds with the US codegen.
    host_sources+=(hooks roster_trace roster_ext select_ext)
fi

: > "$work/todo.txt"
for source in "$work/src/$generated_dir"/*.cpp; do
    object="$work/obj/gen_$(basename "$source" .cpp).o"
    [ "$object" -nt "$source" ] || printf '%s\t%s\t%s\n' "$source" "$object" "-include-pch $pch" >> "$work/todo.txt"
done
for name in "${host_sources[@]}"; do
    source="$work/src/src/$name.cpp"
    object="$work/obj/host_${name//\//_}.o"
    [ "$object" -nt "$source" ] && [ -z "$(find "$work/src/src" -name '*.h' -newer "$object" -print -quit)" ] \
        || printf '%s\t%s\t%s\n' "$source" "$object" "" >> "$work/todo.txt"
done
count=$(wc -l < "$work/todo.txt")
echo "compiling $count sources with $jobs jobs"
if [ "$count" -gt 0 ]; then
    export cxx flags runtime_build
    compile_one() {
        IFS=$'\t' read -r source object extra <<< "$1"
        ( cd "$runtime_build" && eval "\"$cxx\" $flags $extra -o \"$object\" -c \"$source\"" ) 2> "$object.log" \
            || { echo "FAILED $(basename "$source")"; head -20 "$object.log"; rm -f "$object"; return 1; }
        rm -f "$object.log"
    }
    export -f compile_one
    nice -n 10 xargs -a "$work/todo.txt" -d '\n' -P "$jobs" -I{} bash -c 'compile_one "$1"' _ {} \
        || { echo "compile failed" >&2; exit 1; }
fi

extra="-DDBZ3_TITLE"
[ -z "${DBZ3_PLAY:-}" ] || extra="$extra -DDBZ3_PLAY"
[ -z "${DBZ3_LOG_LEVEL:-}" ] || extra="$extra -DDBZ3_LOG_LEVEL=\\\"$DBZ3_LOG_LEVEL\\\""
( cd "$runtime_build" && eval "\"$cxx\" $flags $extra -I\"$work/src/ps5\" -o \"$work/obj/title_main.o\" -c \"$work/src/ps5/main_ps5.cpp\"" )

bash "$here/title_build.sh" "$title" "${DBZ3_TITLE_NAME:-DBZ Budokai 3 HD}" \
    "$work/obj/title_main.o" "$work"/obj/gen_*.o "$work"/obj/host_*.o \
    --start-group $(ls "$libs"/*.a | tr '\n' ' ') "$sdk/target/lib/libc++experimental.a" --end-group
