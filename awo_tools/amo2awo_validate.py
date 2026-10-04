#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""amo2awo_validate.py - Valida amo2awo.py contra los pares nativos #AMO0 (PS2 GH n) /
#AWO (HD n) seccion a seccion.

  python amo2awo_validate.py [--range 0-3990] [--show 3] [--pairs <dir con n.amo/n.awo>]

Por seccion: exacta / distinta. Ventanas: iguales salvo el ultimo bit de la normal.
IB: mismos triangulos por draw (la tira skinneada se re-encadena; las listas son exactas).
"""
import argparse
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import amo2awo  # noqa: E402


def be(b, o):
    return struct.unpack_from(">I", b, o)[0]


def awg_sections(b, a):
    g = lambda o: be(b, a + o)
    nb, nmat = g(0x10), g(0x24)
    s = {"hdr_fixed": b[a:a + 0x28], "names": b[a + g(0x1C):a + g(0x1C) + 32 * nb]}
    s["mats"] = b[a + g(0x20):a + g(0x20) + 0x50 * nmat] if nmat else b""
    s["axes"] = b[a + g(0x14):a + g(0x14) + 80 * nb]
    arms = []
    for i in range(nb):
        arm = be(b, a + g(0x14) + 80 * i + 0x34)
        arms.append(arm)
    s["arm_ptrs"] = arms
    arm_rec, boxes, groups = [], [], []
    for i, arm in enumerate(arms):
        if not arm:
            arm_rec.append(None)
            continue
        w = struct.unpack_from(">5I", b, a + arm)
        arm_rec.append(w)
        if w[3]:
            boxes.append(b[a + w[3]:a + w[3] + 0x40])
        if w[1]:
            n = be(b, a + w[1])
            for k in range(n):
                d = a + w[1] + 0x10 + 0x60 * k
                groups.append((i, k, b[d:d + 0x30], struct.unpack_from(">4I", b, d + 0x20),
                               struct.unpack_from(">2I", b, d + 0x30), b[d + 0x38:d + 0x60]))
    s["arm_rec"] = arm_rec
    s["boxes"] = boxes
    s["draws"] = groups
    s["pal"] = [be(b, a + g(0x38) + 4 * i) for i in range(g(0x3C))]
    n = g(0x2C) // 44
    s["windows"] = [b[a + g(0x28) + 44 * i:a + g(0x28) + 44 * i + 44] for i in range(n)]
    s["ib"] = [struct.unpack_from(">H", b, a + g(0x30) + 2 * i)[0] for i in range(g(0x34) // 2)]
    return s


def win_eq(x, y):
    if x[:20] != y[:20] or x[32:] != y[32:]:
        return False
    for k in range(3):
        u, v = be(x, 20 + 4 * k), be(y, 20 + 4 * k)
        if abs(u - v) > 4 and not (u & 0x7FFFFFFF < 0x30000000 and v & 0x7FFFFFFF < 0x30000000):
            return False
    return True


def tri_set(ib, prim, a0, n):
    seg = ib
    out = set()
    if prim == 4:
        for i in range(0, 3 * n, 3):
            t = tuple(seg[i:i + 3])
            k = t.index(min(t))
            out.add(t[k:] + t[:k])
    else:
        for i in range(n):
            t = (seg[i], seg[i + 1], seg[i + 2]) if i % 2 == 0 else (seg[i + 1], seg[i], seg[i + 2])
            if len(set(t)) == 3:
                k = t.index(min(t))
                out.add(t[k:] + t[:k])
    return out


def compare(conv, hd, stats, tag, show):
    def bad(sec, msg=""):
        stats[sec]["distinta"] += 1
        if stats[sec]["distinta"] <= show:
            print("  %s %s %s" % (tag, sec, msg))

    def ok(sec):
        stats[sec]["exacta"] += 1
    # nivel AWO
    nb = be(hd, 0x10)
    for sec, (x, y) in {"awo_hdr": (conv[:0x30], hd[:0x30]),
                        "bones": (conv[0x30:0x30 + 0x20 * nb], hd[0x30:0x30 + 0x20 * nb])}.items():
        ok(sec) if x == y else bad(sec, "%s / %s" % (x[:32].hex(), y[:32].hex()))
    na = be(hd, 0x18)
    ta, tc = be(hd, 0x1C), be(conv, 0x1C)
    awg_h = [be(hd, ta + 4 * i) for i in range(na)]
    awg_c = [be(conv, tc + 4 * i) for i in range(na)]
    ok("awg_table") if awg_h == awg_c else bad("awg_table", "%s / %s" % (awg_c[:4], awg_h[:4]))
    ok("size") if len(conv) == len(hd) else bad("size", "%d / %d" % (len(conv), len(hd)))
    for k in range(na):
        sc, sh = awg_sections(conv, awg_c[k]), awg_sections(hd, awg_h[k])
        for sec in ("hdr_fixed", "names", "mats", "axes", "arm_rec", "boxes", "pal"):
            if sc[sec] == sh[sec]:
                ok(sec)
            else:
                d = ""
                if isinstance(sc[sec], bytes):
                    i = next((i for i in range(min(len(sc[sec]), len(sh[sec]))) if sc[sec][i] != sh[sec][i]),
                             min(len(sc[sec]), len(sh[sec])))
                    d = "@%#x conv=%s hd=%s" % (i, sc[sec][i:i + 8].hex(), sh[sec][i:i + 8].hex())
                else:
                    d = "%s / %s" % (str(sc[sec])[:120], str(sh[sec])[:120])
                bad(sec, "awg%d %s" % (k, d))
        # draws: todo salvo B (re-encadenado) y la cola de la etiqueta
        dc, dh = sc["draws"], sh["draws"]
        if len(dc) != len(dh):
            bad("draws", "awg%d n %d / %d" % (k, len(dc), len(dh)))
            continue
        good = True
        for x, y in zip(dc, dh):
            if x[:2] != y[:2] or x[2][:0x20] != y[2][:0x20] or x[3][1:] != y[3][1:]:
                good = False
                bad("draws", "awg%d bone %d k %d conv %s %s hd %s %s" % (k, x[0], x[1], x[2][:0x30].hex()[32:],
                                                                      x[3], y[2][:0x30].hex()[32:], y[3]))
                break
            stats["prim"]["igual" if x[3][0] == y[3][0] else "distinto (%d/%d)" % (x[3][0], y[3][0])] += 1
        if good:
            ok("draws")

        def labkey(r):
            z = r.find(b"\x00", 1)
            return (r[0], r[1:z], r[17:21] if z <= 16 else b"")
        lab = all(labkey(x[5]) == labkey(y[5]) for x, y in zip(dc, dh))
        ok("labels") if lab else bad("labels", "awg%d %s / %s" % (k, dc[0][5][:28], dh[0][5][:28]))
        wc, wh = sc["windows"], sh["windows"]
        if len(wc) != len(wh):
            bad("windows", "awg%d n %d / %d" % (k, len(wc), len(wh)))
        elif all(win_eq(x, y) for x, y in zip(wc, wh)):
            ok("windows")
        else:
            i = next(i for i, (x, y) in enumerate(zip(wc, wh)) if not win_eq(x, y))
            bad("windows", "awg%d #%d %s / %s" % (k, i, wc[i].hex(), wh[i].hex()))
        # IB por draw
        tri_ok = True
        for x, y in zip(dc, dh):
            pc, ph = x[3][0], y[3][0]
            tc_ = tri_set(sc["ib"][x[4][0]:], pc, x[3][2], x[4][1])
            th_ = tri_set(sh["ib"][y[4][0]:], ph, y[3][2], y[4][1])
            if tc_ != th_:
                tri_ok = False
                break
        ok("triangles") if tri_ok else bad("triangles", "awg%d bone %d" % (k, x[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", help="carpeta con <id>.amo / <id>.awo ya extraidos")
    ap.add_argument("--show", type=int, default=3)
    ap.add_argument("--only")
    a = ap.parse_args()
    stats = collections.defaultdict(collections.Counter)
    errors = collections.Counter()
    files = sorted(f[:-4] for f in os.listdir(a.pairs) if f.endswith(".amo"))
    if a.only:
        files = [f for f in files if f in a.only.split(",")]
    for f in files:
        p = open(os.path.join(a.pairs, f + ".amo"), "rb").read()
        h = open(os.path.join(a.pairs, f + ".awo"), "rb").read()
        try:
            c = amo2awo.convert_amo(p)
        except Exception as e:  # noqa: BLE001
            errors[type(e).__name__ + ": " + str(e)[:60]] += 1
            if sum(errors.values()) <= a.show:
                print("  ERROR %s: %r" % (f, e))
            continue
        compare(c, h, stats, f, a.show)
    for sec, c in stats.items():
        print("%-10s %s" % (sec, dict(c)))
    if errors:
        print("errores:", dict(errors))


if __name__ == "__main__":
    main()
