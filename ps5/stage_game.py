#!/usr/bin/env python3
"""Stage the user's own copy of Budokai 3 for the PS5 build.

    stage_game.py (--iso IMAGE | --game-dir DIR) --out GAME_DIR --xex-out REPO_DIR

Reads either an Xbox 360 disc image (XDVDFS, the usual raw and redump layouts)
or a folder that already holds the game, finds the Budokai 3 executable by its
checksum (the HD Collection disc keeps it at DBZ3/yae3_xenon.xex, next to the
collection's own menu as default.xex) and writes:

    GAME_DIR/default.xex   the Budokai 3 executable, unmodified
    GAME_DIR/us/ or eu/    the region's data folder(s) found next to it
    GAME_DIR/region.txt    "us" or "eu": which executable it is
    REPO_DIR/yae3_xenon.xex or yae3_xenon_eu.xex
                           a copy for the recompiler (dbz3_manifest*.toml)

Nothing is decrypted or modified. The output is the user's own data: it is
gitignored and must never be committed or shared. Files already present with
the same size are kept, so the script can be run again.
"""
import argparse
import hashlib
import os
import shutil
import struct
import sys

# docs/baserom.md (SHA-256) and src/launcher/settings.cpp (MD5).
XEX_SIZE = 4890624
KNOWN = {
    "b40bba40cfd6c90cb269ebf5020818924f43109bcc86827a3cc37124c052a26b": "us",
    "7193803aee6124c8d0782ef2c37ff2e8d41db8a11286d198c23352ea7622e924": "eu",
    "a53e324b5d2a65ebcbf648e4f85a7271": "us",
    "c37eb979b762da0ab5b8c9ba8037ce4e": "eu",
}
DBZ1_MD5 = "5a6ab28a4911851fca955b5925cdfebb"

SECTOR = 0x800
MAGIC = b"MICROSOFT*XBOX*MEDIA"
PARTITION_OFFSETS = (0x0, 0xFD90000, 0x2080000, 0x18300000, 0x89D80000)


def classify(path):
    """'us', 'eu' or None for a candidate executable."""
    try:
        if os.path.getsize(path) != XEX_SIZE:
            return None
    except OSError:
        return None
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
            md5.update(chunk)
    return KNOWN.get(sha.hexdigest()) or KNOWN.get(md5.hexdigest())


# --- XDVDFS -----------------------------------------------------------------------


def find_partition(f, size):
    for base in PARTITION_OFFSETS:
        if base + 32 * SECTOR + 28 > size:
            continue
        f.seek(base + 32 * SECTOR)
        if f.read(20) == MAGIC:
            root_sector, root_size = struct.unpack("<II", f.read(8))
            return base, root_sector, root_size
    raise SystemExit("error: no XDVDFS volume found; is this an Xbox 360 disc image?")


def walk(f, base, sector, dir_size, path, out):
    """Every file in the directory tree as (path, sector, size)."""
    f.seek(base + sector * SECTOR)
    data = f.read(dir_size)
    pending = [0]
    while pending:
        offset = pending.pop() * 4
        if offset + 14 > len(data):
            continue
        left, right, file_sector, file_size, attributes, name_length = struct.unpack_from(
            "<HHIIBB", data, offset)
        if left == 0xFFFF:
            continue
        name = data[offset + 14:offset + 14 + name_length].decode("latin-1")
        full = f"{path}/{name}" if path else name
        if attributes & 0x10:
            if file_size:
                walk(f, base, file_sector, file_size, full, out)
        else:
            out.append((full, file_sector, file_size))
        if left:
            pending.append(left)
        if right:
            pending.append(right)


def copy_range(f, base, sector, size, dest):
    if os.path.exists(dest) and os.path.getsize(dest) == size:
        print(f"  kept  {dest}")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  write {dest} ({size / 2**20:.1f} MiB)")
    f.seek(base + sector * SECTOR)
    remaining = size
    with open(dest + ".part", "wb") as o:
        while remaining:
            chunk = f.read(min(remaining, 1 << 24))
            if not chunk:
                raise SystemExit(f"error: image truncated while reading {dest}")
            o.write(chunk)
            remaining -= len(chunk)
    os.replace(dest + ".part", dest)


def stage_from_iso(iso, out_dir, art_out=None):
    with open(iso, "rb") as f:
        base, root_sector, root_size = find_partition(f, os.path.getsize(iso))
        files = []
        walk(f, base, root_sector, root_size, "", files)
        # Candidates: every executable of the right size; classify each by
        # extracting it to a scratch file first.
        scratch = os.path.join(out_dir, ".xex-candidate")
        os.makedirs(out_dir, exist_ok=True)
        found = None
        for path, sector, size in files:
            if size != XEX_SIZE or not path.lower().endswith(".xex"):
                continue
            if os.path.exists(scratch):
                os.remove(scratch)
            copy_range(f, base, sector, size, scratch)
            region = classify(scratch)
            if region:
                found = (path, region)
                break
        if not found:
            if os.path.exists(scratch):
                os.remove(scratch)
            raise SystemExit("error: no Budokai 3 executable (US or EU) in this image")
        path, region = found
        os.replace(scratch, os.path.join(out_dir, "default.xex"))
        print(f"executable: {path} ({region.upper()})")
        folder = os.path.dirname(path)
        prefix = (folder + "/") if folder else ""
        copied = 0
        for sub in ("us", "eu"):
            for original, sector, size in files:
                if original.lower().startswith((prefix + sub + "/").lower()):
                    rel = original[len(prefix):]
                    copy_range(f, base, sector, size, os.path.join(out_dir, *rel.split("/")))
                    copied += 1
        if not copied:
            raise SystemExit(f"error: no us/ or eu/ folder next to {path} in the image")
        if art_out:
            for original, sector, size in files:
                if original.lower() == "nxeart":
                    copy_range(f, base, sector, size, os.path.join(art_out, "nxeart"))
    return region


def stage_from_folder(game_dir, out_dir, art_out=None):
    found = None
    for current, dirs, names in os.walk(game_dir):
        depth = os.path.relpath(current, game_dir).count(os.sep)
        if depth >= 3:
            dirs[:] = []
        for name in names:
            if name.lower().endswith(".xex"):
                candidate = os.path.join(current, name)
                region = classify(candidate)
                if region:
                    found = (candidate, region)
                    break
        if found:
            break
    if not found:
        raise SystemExit(f"error: no Budokai 3 executable (US or EU) under {game_dir}")
    xex, region = found
    print(f"executable: {xex} ({region.upper()})")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, "default.xex")
    if not (os.path.exists(dest) and os.path.getsize(dest) == XEX_SIZE and classify(dest) == region):
        shutil.copyfile(xex, dest)
    source_root = os.path.dirname(xex)
    copied = 0
    for sub in ("us", "eu"):
        source = os.path.join(source_root, sub)
        if not os.path.isdir(source):
            continue
        for current, _, names in os.walk(source):
            for name in names:
                src = os.path.join(current, name)
                rel = os.path.relpath(src, source_root)
                dst = os.path.join(out_dir, rel)
                if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                print(f"  copy  {rel}")
                shutil.copyfile(src, dst)
        copied += 1
    if not copied:
        raise SystemExit(f"error: no us/ or eu/ folder next to {xex}")
    if art_out:
        for candidate in (os.path.join(game_dir, "nxeart"), os.path.join(source_root, "..", "nxeart")):
            if os.path.isfile(candidate):
                os.makedirs(art_out, exist_ok=True)
                shutil.copyfile(candidate, os.path.join(art_out, "nxeart"))
                break
    return region


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--iso")
    source.add_argument("--game-dir")
    parser.add_argument("--out", required=True)
    parser.add_argument("--xex-out", required=True)
    parser.add_argument("--art-out", help="where to copy the disc's nxeart (dashboard art), if any")
    args = parser.parse_args()

    if args.iso:
        region = stage_from_iso(args.iso, args.out, args.art_out)
    else:
        region = stage_from_folder(args.game_dir, args.out, args.art_out)
    with open(os.path.join(args.out, "region.txt"), "w") as f:
        f.write(region + "\n")
    name = "yae3_xenon.xex" if region == "us" else "yae3_xenon_eu.xex"
    shutil.copyfile(os.path.join(args.out, "default.xex"), os.path.join(args.xex_out, name))
    print(f"ok: {region.upper()} executable staged; recompiler input {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
