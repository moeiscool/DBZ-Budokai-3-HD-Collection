#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprueba donde vive el bone real en la ventana (44B) comparando native vs
port: si el port reasigna huesos, el campo 'bone' en +16 diferira entre ambos
para los mismos indices de ventana; pero si el port conserva el bone, la unica
diferencia sera pos/nrm. Tambien prueba offsets alternativos (16,19,28,40).

Uso: bone_probe.py <native.bin> <port.bin>
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer, be32

W = 44


def raw(a, w):
    o = a.vb0 + w * W
    return a.data[o:o + W]


def main():
    a = AwgVertexBuffer.load(sys.argv[1])
    b = AwgVertexBuffer.load(sys.argv[2])
    n = min(a.n, b.n)
    for off in (16, 19, 28, 40):
        diff = 0
        for w in range(n):
            if be32(raw(a, w), off) != be32(raw(b, w), off):
                diff += 1
        print("campo u32 @+%2d : %d/%d ventanas difieren" % (off, diff, n))
    # si el bone NO esta en +16, ver que hay
    print()
    print("=== muestra ventana 0 ===")
    for name, arr in (("native", a), ("port", b)):
        r = raw(arr, 0)
        print(" %s: " % name + " ".join("%02x" % x for x in r))
        print("        u32@16=%d  u32@19=%d  f@0=%.3f" % (
            be32(r, 16), be32(r, 19) if len(r) >= 23 else -1,
            struct.unpack(">f", r[0:4])[0]))


if __name__ == "__main__":
    main()
