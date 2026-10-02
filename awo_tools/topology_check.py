#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifica la HIPOTESIS de conectividad: el port conserva el IB del nativo pero
con posiciones PS2. Para cada triangulo del IB, si los 3 vertices pertenecen a
huesos no adyacentes (o muy separados en model-space), el triangulo esta
'cruzado' -> malla deforme aunque el bind sea correcto.

Compara nativo (conectividad y geometria coherentes) vs port.
Uso: topology_check.py <native.bin> <port.bin>
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer, mvec


def load(path):
    a = AwgVertexBuffer.load(path)
    world, _ = a.bind_worlds()
    vs = a.vertices()
    model = [mvec(world[v["bone"]], [v["pos"][0], v["pos"][1], v["pos"][2], 1.0])
             for v in vs]
    return a, vs, model


def edge_stats(a, vs, model):
    ib = a.indices()
    tris = [(ib[i], ib[i+1], ib[i+2]) for i in range(0, len(ib) - 2, 3)]
    lens = []
    bone_jumps = 0
    for t in tris:
        if any(v == 0xFFFF or v >= len(vs) for v in t):
            continue
        bset = {vs[v]["bone"] for v in t}
        if len(bset) > 1:
            bone_jumps += 1
        # perimetro del triangulo en model-space
        for (i, j) in ((0, 1), (1, 2), (2, 0)):
            p, q = model[t[i]], model[t[j]]
            lens.append(math.dist(p, q))
    lens.sort()
    n = len(lens)
    return {
        "tris": len(tris),
        "bone_mixed_tris": bone_jumps,
        "edge_med": lens[n//2] if n else 0,
        "edge_p95": lens[int(n*0.95)] if n else 0,
        "edge_max": lens[-1] if n else 0,
    }


def main():
    a1, v1, m1 = load(sys.argv[1])
    a2, v2, m2 = load(sys.argv[2])
    s1 = edge_stats(a1, v1, m1)
    s2 = edge_stats(a2, v2, m2)
    print("%-20s %12s %12s" % ("metrica", "native", "port"))
    for k in ("tris", "bone_mixed_tris", "edge_med", "edge_p95", "edge_max"):
        print("%-20s %12.3f %12.3f" % (k, s1[k], s2[k]))
    # ratio de aristas largas port vs native
    print()
    print("edge_max port/native = %.2fx  (>>1 => triangulos cruzados)"
          % (s2["edge_max"] / max(s1["edge_max"], 1e-9)))


if __name__ == "__main__":
    main()
