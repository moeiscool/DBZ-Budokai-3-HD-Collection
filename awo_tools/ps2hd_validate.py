#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ps2hd_validate.py - Valida ps2hd.py contra los pares nativos (PS2 GH n, HD n).

Recorre en paralelo los contenedores #AMB de ambas versiones y, para cada bloque hijo
cuyo tipo tiene manejador, compara convert(PS2) con el bloque HD byte a byte.
  python ps2hd_validate.py [--types AMC,AME] [--range 0-3990] [--show 3]
Salida: por tipo -> exactos / mismo tamano pero distintos (1er offset) / tamano distinto.
"""
import argparse
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ps2hd  # noqa: E402
from afs_pair import ps2, hd, table, PS2_GH, CACHE  # noqa: E402


def kids(b, le):
    e = "<" if le else ">"
    if len(b) < 0x20 or b[:4] != b"#AMB":
        return None
    n, t = struct.unpack(e + "II", b[0x10:0x18])
    if n > 4096 or t + 16 * n > len(b):
        return None
    return [struct.unpack(e + "4I", b[t + 16 * k:t + 16 * k + 16])[:3] for k in range(n)]


def first_diff(a, b):
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return i
    return min(len(a), len(b))


def walk(p, h, stats, where, types, show):
    kp, kh = kids(p, True), kids(h, False)
    if kp is None or kh is None or len(kp) != len(kh):
        stats["(estructura)"]["distinta"] += 1
        return
    for i, ((po, ps, _), (ho, hs, _)) in enumerate(zip(kp, kh)):
        P, H = p[po:po + ps], h[ho:ho + hs]
        m = P[:4].decode("latin1")
        if P[:4] == b"#AMB":
            walk(P, H, stats, where + "/%d" % i, types, show)
            continue
        if types and m.strip("#") not in types:
            continue
        try:
            C = ps2hd.convert_block(P)
        except ps2hd.Unsupported:
            stats[m]["sin manejador"] += 1
            continue
        except Exception as e:  # noqa: BLE001
            stats[m]["error"] += 1
            if stats[m]["error"] <= show:
                print("  ERROR %s %s: %r" % (m, where, e))
            continue
        if C == H:
            stats[m]["exacto"] += 1
        elif len(C) == len(H) and sum(x != y for x, y in zip(C, H)) < 0.05 * len(H):
            stats[m]["casi (<5% bytes)"] += 1
        elif len(C) == len(H):
            stats[m]["mismo tam, distinto"] += 1
            if stats[m]["mismo tam, distinto"] <= show:
                d = first_diff(C, H)
                print("  %s %s/%d: 1er diff @%#x conv=%s hd=%s" % (m, where, i, d, C[d:d + 8].hex(), H[d:d + 8].hex()))
        else:
            stats[m]["tam distinto"] += 1
            if stats[m]["tam distinto"] <= show:
                print("  %s %s/%d: tam conv %d hd %d (1er diff @%#x)" % (m, where, i, len(C), len(H), first_diff(C, H)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--types")
    ap.add_argument("--range", default="0-3990")
    ap.add_argument("--show", type=int, default=3)
    a = ap.parse_args()
    lo, hi = map(int, a.range.split("-"))
    types = set(a.types.split(",")) if a.types else None
    stats = collections.defaultdict(collections.Counter)
    n_tab = len(table(os.path.join(PS2_GH, "data_cmn.afs")))
    for n in range(lo, min(hi, n_tab)):
        p = ps2(n)
        if p[:4] != b"#AMB":
            continue
        if not os.path.exists(os.path.join(CACHE, "data_cmn.afs_%d.dec" % n)):
            continue  # HD aun no descomprimida
        walk(p, hd(n), stats, str(n), types, a.show)
    for m, c in sorted(stats.items()):
        print("%-8s %s" % (m, dict(c)))


if __name__ == "__main__":
    main()
