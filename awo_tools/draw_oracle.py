#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""draw_oracle.py - Oraculo OFFLINE de dibujo de un bin #AMB B3 HD (AWG0).

Recorre la TABLA DE DRAWS exactamente como el guest (A/B/prim por draw, B_count =
primitivas) y reconstruye el bind-pose:
  * prim 5 (strip skinneado): pos_model = world[bone_of[slot]] . pos_ventana
  * prim 4 (lista rigida):    pos_model = world[group_bone] . pos_ventana
Comprueba (lint, sale con 1 si algo falla):
  - TABLA DE PALETA (AWG0+0x38 puntero, +0x3C n): slot 0 = FFFFFFFF, huesos validos.
    Si no, el guest no escribe la paleta -> cuerpo skinneado INVISIBLE en juego.
  Por draw:
  - indices dentro de [0, N) y dentro del rango A del draw
  - el IB del draw no invade el del siguiente (B_start + lectura <= B_start siguiente)
  - slots validos (prim 5) y huesos validos
  - WINDING: % de triangulos cuya normal geometrica coincide con la media de las
    normales de vertice (el nativo da ~95-100 %; <70 % = caras invertidas -> se
    cullean en juego)
  - aristas largas (p99) -> desgarros
Y pinta frente+perfil a PNG (pintor por profundidad, sombreado plano).

Uso: python draw_oracle.py <bin> [<bin2> ...] [--png carpeta]
"""
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from awg_vertex_buffer import AwgVertexBuffer  # noqa: E402
from b3_gateway import DrawTable, strip_tri  # noqa: E402
from skin_slots import SkinSlots, palette_table  # noqa: E402


def draw_tris(d, ib):
    b0, bn = d["B"]
    if d["prim"] == 5:
        seq = ib[b0:b0 + bn + 2] if bn else []
        return [strip_tri(seq, i) for i in range(len(seq) - 2)], b0 + (bn + 2 if bn else 0)
    seq = ib[b0:b0 + 3 * bn]
    return [tuple(seq[i:i + 3]) for i in range(0, len(seq) - 2, 3)], b0 + 3 * bn


def analyse(path, png_dir=None):
    avb = AwgVertexBuffer.load(path)
    table = DrawTable(avb)
    ss = SkinSlots(avb)
    errs = []
    if palette_table(avb) is None:
        b, a0 = avb.data, avb.awg0
        p = a0 + struct.unpack(">I", bytes(b[a0 + 0x38:a0 + 0x3C]))[0]
        errs.append("TABLA DE PALETA (+0x38 -> AWG0+%#x, n=%d) invalida: %s" % (
            p - a0, struct.unpack(">I", bytes(b[a0 + 0x3C:a0 + 0x40]))[0],
            [hex(x) for x in struct.unpack(">4I", bytes(b[p:p + 16]))]))
    W = np.array(avb.bind_worlds()[0])
    raw = bytes(avb.data[avb.vb0:avb.vb0 + avb.n * 44])
    f = np.frombuffer(raw, dtype=">f4").reshape(avb.n, 11).astype(np.float64)
    u = np.frombuffer(raw, dtype=">u4").reshape(avb.n, 11)
    pos, nrm, slot = f[:, 0:3], f[:, 5:8], (u[:, 4] & 0xFF).astype(int)
    ib = avb.indices()
    n = avb.n
    P = np.full((n, 3), np.nan)
    N = np.full((n, 3), np.nan)
    tris_all, draw_of = [], []
    ends = sorted((d["B"][0], i) for i, d in enumerate(table.draws) if d["B"][1])
    for di, d in enumerate(table.draws):
        tris, end = draw_tris(d, ib)
        a0, an = d["A"]
        nxt = [b for b, j in ends if b > d["B"][0]]
        if nxt and d["B"][1] and end > nxt[0]:
            errs.append("draw %d lee IB hasta %d > inicio del siguiente %d" % (di, end, nxt[0]))
        vs = {v for t in tris for v in t}
        if any(v >= n for v in vs):
            errs.append("draw %d: indice >= N (%d)" % (di, max(vs)))
            continue
        out = [v for v in vs if not (a0 <= v < a0 + an)]
        if out:
            errs.append("draw %d: %d indices fuera de A=[%d,%d)" % (di, len(out), a0, a0 + an))
        for v in vs:
            if d["prim"] == 5:
                b = ss.bone_of.get(int(slot[v]))
                if b is None:
                    errs.append("draw %d: vertice %d con slot %d sin hueso" % (di, v, slot[v]))
                    break
            else:
                b = d["group_bone"]
            M = W[b]
            P[v] = M[:3, :3] @ pos[v] + M[:3, 3]
            N[v] = M[:3, :3] @ nrm[v]
        for t in tris:
            if len(set(t)) == 3:
                tris_all.append(t)
                draw_of.append(di)
    T = np.array(tris_all)
    A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    gn = np.cross(B - A, C - A)
    vn = N[T[:, 0]] + N[T[:, 1]] + N[T[:, 2]]
    dot = np.einsum("ij,ij->i", gn, vn)
    agree = float((dot > 0).mean())
    e = np.concatenate([np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)])
    e = e[np.isfinite(e)]
    print("%s: N=%d IB=%d draws=%d tris=%d | winding OK %.1f%% | arista p50 %.3f p99 %.3f max %.3f"
          % (os.path.basename(path), n, len(ib), len(table.draws), len(T), 100 * agree,
             np.percentile(e, 50), np.percentile(e, 99), e.max()))
    per = {}
    for di, ok in zip(draw_of, dot > 0):
        per.setdefault(di, []).append(ok)
    bad = [(di, 100 * np.mean(v)) for di, v in per.items() if np.mean(v) < 0.7]
    if bad:
        errs.append("draws con winding invertido (<70%%): %s"
                    % ", ".join("%d:%.0f%%" % x for x in bad))
    for x in errs[:20]:
        print("  [X]", x)
    if png_dir:
        render(P, T, gn, os.path.join(png_dir, os.path.splitext(os.path.basename(path))[0] + "_oracle.png"))
    return not errs


def render(P, T, gn, out, size=600):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (size * 2, size), (24, 24, 30))
    d = ImageDraw.Draw(im)
    ok = np.isfinite(P).all(axis=1)
    lo, hi = np.nanmin(P[ok], axis=0), np.nanmax(P[ok], axis=0)
    sc = (size - 40) / max(hi - lo)
    for view, (ax, ay, az, ox) in enumerate([(0, 1, 2, 0), (2, 1, 0, size)]):
        depth = P[T].mean(axis=1)[:, az]
        order = np.argsort(depth if view == 0 else -depth)
        L = np.array([0.3, 0.5, 1.0]) if view == 0 else np.array([1.0, 0.5, 0.3])
        L = L / np.linalg.norm(L)
        for k in order:
            t = T[k]
            if not ok[t].all():
                continue
            g = gn[k]
            ln = np.linalg.norm(g)
            s = 0.25 + 0.75 * abs(float(g @ L)) / ln if ln > 0 else 0.3
            c = (int(90 * s), int(200 * s), int(120 * s))
            pts = [(ox + 20 + (P[v, ax] - lo[ax]) * sc, size - 20 - (P[v, ay] - lo[ay]) * sc) for v in t]
            d.polygon(pts, fill=c)
    im.save(out)
    print("  png ->", out)


def main():
    args = sys.argv[1:]
    png = None
    if "--png" in args:
        i = args.index("--png")
        png = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__)
        return 1
    res = [analyse(p, png) for p in args]
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
