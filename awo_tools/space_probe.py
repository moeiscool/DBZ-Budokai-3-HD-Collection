#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hipotesis de espacio: si el pipeline del port escribio pos en MODEL-space en
vez de bone-local, al aplicarle world saldria deformado. Aqui se prueba cada
vertice del port: comparar 'pos crudo' (tal cual) vs 'worldÂ·pos' contra el
model-space del nativo en el mismo vertice (emparejado por bone+uv).

Si 'pos crudo del port' ~ 'model del nativo', el port esta en model-space (mal).
Si 'worldÂ·pos del port' ~ 'model del nativo', esta en bone-local (bien).

Uso: space_probe.py <native.bin> <port.bin>
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer, mvec


def main():
    a = AwgVertexBuffer.load(sys.argv[1])
    b = AwgVertexBuffer.load(sys.argv[2])
    wa, _ = a.bind_worlds()
    wb, _ = b.bind_worlds()
    va, vb = a.vertices(), b.vertices()
    n = min(len(va), len(vb))

    key_a = {}
    for i in range(n):
        k = (va[i]["bone"], round(va[i]["uv"][0], 5), round(va[i]["uv"][1], 5))
        key_a.setdefault(k, i)
    pairs = []
    for i in range(n):
        k = (vb[i]["bone"], round(vb[i]["uv"][0], 5), round(vb[i]["uv"][1], 5))
        if k in key_a:
            pairs.append((key_a[k], i))

    # model del nativo (referencia)
    def model_native(i):
        v = va[i]
        m = mvec(wa[v["bone"]], [v["pos"][0], v["pos"][1], v["pos"][2], 1.0]); return m[:3]

    e_raw = e_world = 0.0
    for ia, ib in pairs:
        pn = model_native(ia)
        v = vb[ib]
        raw = v["pos"]
        wr = mvec(wb[v["bone"]], [raw[0], raw[1], raw[2], 1.0])[:3]
        e_raw += math.dist(pn, raw)
        e_world += math.dist(pn, wr)
    m = len(pairs)
    print("pares=%d" % m)
    print("  port pos CRUDO       vs model_nativo: err=%.3f" % (e_raw / m))
    print("  port worldÂ·pos       vs model_nativo: err=%.3f" % (e_world / m))
    print()
    if e_raw < e_world:
        print("  => el port parece estar en MODEL-space (falta/sobra la transform)")
    else:
        print("  => el port esta en BONE-LOCAL (worldÂ·pos es lo correcto)")


if __name__ == "__main__":
    main()

