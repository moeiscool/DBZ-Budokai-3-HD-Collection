#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analiza el error model-space nativo vs port POR HUESO, y comprueba si el
error es 'rigido por hueso' (la forma local se conserva) o 'disperso'
(la asignacion de hueso esta mal).

Si un vertice del port pertenece al hueso B, y aplicando world[B] la posicion
cae cerca de la posicion model-space del vertice equivalente del nativo
(mismo hueso), el bind es correcto aunque la malla sea de otro modelo.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer, mvec, minv_affine
import math


def load_model(path):
    a = AwgVertexBuffer.load(path)
    world, par = a.bind_worlds()
    vs = a.vertices()
    return a, world, vs


def model_pts(world, vs):
    out = []
    for v in vs:
        b = v["bone"]
        m = mvec(world[b], [v["pos"][0], v["pos"][1], v["pos"][2], 1.0])
        out.append((b, (m[0], m[1], m[2])))
    return out


def main():
    a1, w1, v1 = load_model(sys.argv[1])
    a2, w2, v2 = load_model(sys.argv[2])
    p1 = model_pts(w1, v1)
    p2 = model_pts(w2, v2)

    # error por hueso: para cada hueso, comparar centroide y dispersion
    print("bone  n1   n2   centroid_delta        radius1  radius2")
    worst = []
    for b in range(a1.bone_count()):
        g1 = [p for (bb, p) in p1 if bb == b]
        g2 = [p for (bb, p) in p2 if bb == b]
        if not g1 and not g2:
            continue
        def centroid(pts):
            n = len(pts)
            return (sum(p[0] for p in pts)/n, sum(p[1] for p in pts)/n, sum(p[2] for p in pts)/n)
        def radius(pts, c):
            return max(math.dist(p, c) for p in pts) if pts else 0.0
        c1 = centroid(g1) if g1 else (0,0,0)
        c2 = centroid(g2) if g2 else (0,0,0)
        cd = math.dist(c1, c2)
        r1 = radius(g1, c1); r2 = radius(g2, c2)
        worst.append((cd, b, len(g1), len(g2), r1, r2))
    for cd, b, n1, n2, r1, r2 in sorted(worst, reverse=True)[:16]:
        print("%4d  %4d %4d   d=%.3f              r=%.3f  r=%.3f" % (b, n1, n2, cd, r1, r2))


if __name__ == "__main__":
    main()
