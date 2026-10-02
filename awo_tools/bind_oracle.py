#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compara la geometria en model-space (world[bone]·pos) de dos bins #AMB.
Sirve de ORACULO para la Via B: si el port mantiene la estructura de huesos,
aplicar el world de los ejes debe devolver una malla coherente; el oraculo
mide el error por hueso entre el nativo (referente bueno) y el port.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from awg_vertex_buffer import AwgVertexBuffer, mvec


def model_positions(awo_path):
    a = AwgVertexBuffer.load(awo_path)
    world, par = a.bind_worlds()
    vs = a.vertices()
    out = []
    for i, v in enumerate(vs):
        b = v["bone"]
        if not (0 <= b < len(world)):
            out.append((i, b, None, v))
            continue
        m = mvec(world[b], [v["pos"][0], v["pos"][1], v["pos"][2], 1.0])
        out.append((i, b, (m[0], m[1], m[2]), v))
    return a, world, par, out


def bounds(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def main():
    if len(sys.argv) < 3:
        print(__doc__); return 1
    a1, w1, p1, m1 = model_positions(sys.argv[1])
    a2, w2, p2, m2 = model_positions(sys.argv[2])
    print("=== ESTRUCTURA ===")
    print("  N=%d vs %d   IB=%d vs %d   bones=%d vs %d"
          % (a1.n, a2.n, a1.n_ib, a2.n_ib, a1.bone_count(), a2.bone_count()))
    # world por hueso: comparar
    nb = min(len(w1), len(w2))
    wmax = 0.0
    for b in range(nb):
        for i in range(4):
            for j in range(4):
                wmax = max(wmax, abs(w1[b][i][j] - w2[b][i][j]))
    print("  world[bone] max diff: %.3e" % wmax)
    # positions model-space: mismo indice de ventana
    n = min(len(m1), len(m2))
    dmax = 0.0; dcount = 0
    for k in range(n):
        if m1[k][2] is None or m2[k][2] is None:
            continue
        d = max(abs(m1[k][2][i] - m2[k][2][i]) for i in range(3))
        dmax = max(dmax, d)
        if d > 1e-3:
            dcount += 1
    print("=== GEOMETRIA model-space (mismo indice de ventana) ===")
    pts1 = [m[2] for m in m1 if m[2]]
    pts2 = [m[2] for m in m2 if m[2]]
    print("  bounds native: x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]" % bounds(pts1))
    print("  bounds win2  : x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]" % bounds(pts2))
    print("  max diff por vertice: %.3f   (vertices con diff>1e-3: %d/%d)"
          % (dmax, dcount, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
