#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba si las posiciones del port estan PERMUTADAS respecto al nativo.
Empareja ventanas por UV (identico en ambos) y compara pos bajo las 6
permutaciones: si una da error mucho menor, hay error de orden de ejes.

Uso: axis_probe.py <native.bin> <port.bin>
"""
import sys, os, struct, math
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer

PERMS = {
    "xyz": (0, 1, 2), "xzy": (0, 2, 1), "yxz": (1, 0, 2),
    "yzx": (1, 2, 0), "zxy": (2, 0, 1), "zyx": (2, 1, 0),
}
SIGNS = [(1, 1, 1), (1, 1, -1), (1, -1, 1), (-1, 1, 1),
         (1, -1, -1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)]


def main():
    a = AwgVertexBuffer.load(sys.argv[1])
    b = AwgVertexBuffer.load(sys.argv[2])
    va, vb = a.vertices(), b.vertices()
    n = min(len(va), len(vb))
    # emparejado por (bone, uv) para comparar el mismo punto del modelo
    key_a = {}
    for i in range(n):
        k = (va[i]["bone"], round(va[i]["uv"][0], 5), round(va[i]["uv"][1], 5))
        key_a.setdefault(k, i)
    pairs = []
    for i in range(n):
        k = (vb[i]["bone"], round(vb[i]["uv"][0], 5), round(vb[i]["uv"][1], 5))
        if k in key_a:
            pairs.append((key_a[k], i))
    print("pares por (bone,uv): %d/%d" % (len(pairs), n))
    if not pairs:
        return
    best = None
    for pname, p in PERMS.items():
        for s in SIGNS:
            err = 0.0
            for ia, ib in pairs:
                pa = va[ia]["pos"]; pb = vb[ib]["pos"]
                q = (s[0] * pb[p[0]], s[1] * pb[p[1]], s[2] * pb[p[2]])
                err += math.dist(pa, q)
            err /= len(pairs)
            if best is None or err < best[0]:
                best = (err, pname, s)
    print("MEJOR: perm=%s signos=%s  err_medio=%.4f" % (best[1], best[2], best[0]))
    # baseline sin permutar
    base = sum(math.dist(va[ia]["pos"], vb[ib]["pos"]) for ia, ib in pairs) / len(pairs)
    print("baseline xyz/+++: err_medio=%.4f" % base)


if __name__ == "__main__":
    main()
