#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprueba los campos que el guest usa para dimensionar el fetch del VB y el
IB: AWG0+0x2C (tamano VB en bytes), +0x30 (ib_rel), +0x34 (tamano IB en bytes),
+0x38 (end). Son la causa documentada de la 'explosion' si no coinciden con el
bin del port. Uso: awg_fields.py <bin> [<bin2> ...]
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from awg_vertex_buffer import AwgVertexBuffer, be32


def show(path):
    a = AwgVertexBuffer.load(path)
    g = lambda o: be32(a.data, a.awg0 + o)
    print("=== %s ===" % os.path.basename(path))
    print("  awg0=%d  n_awg=%d  bones=%d" % (a.awg0, a.n_awg, a.bone_count()))
    print("  +0x2C (VB size bytes) = %d   (n=%d -> %d*44=%d)"
          % (g(0x2C), a.n, a.n, a.n * 44))
    print("  +0x30 (ib_rel)        = %d   ib_abs=%d" % (g(0x30), a.ib_abs))
    print("  +0x34 (IB size bytes) = %d   (n_ib=%d -> %d*2=%d)"
          % (g(0x34), a.n_ib, a.n_ib, a.n_ib * 2))
    print("  +0x38 (end_rel)       = %d   end_abs=%d" % (g(0x38), a.awg0 + g(0x38)))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        show(p)
