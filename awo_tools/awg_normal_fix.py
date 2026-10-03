#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""awg_normal_fix.py - Fix de normales para la Via A (inyeccion PS2->B3 HD).

Toma un bin de port (Via A) y REEMPLAZA el campo `nrm` de TODOS sus AWGs por las
normales del bin NATIVO HD (mismo slot/indice), dejando `pos`/`uv`/`IB`/headers
del port intactos.

Motivacion (docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md §23):
  La Via A reescribe `pos` (malla HD proyectada sobre la superficie PS2) y
  recalcula `nrm` a partir de la normal de la superficie PS2. Esas normales son
  aproximadas -> el render muestra "cascara gris facetada" en brazo/cabeza. Usar
  las normales HD nativas (suaves y bien orientadas) sobre la geometria del port
  elimina el artefacto de sombreado sin tocar la geometria.

Layout de vertice (stride 44, big-endian), ventana `[ib - g(0x2C), ib)`:
  +0 pos.xyz | +12 weight | +16 bone(u32) | +20 nrm.xyz | +32 FFFFFFFF | +36 uv.xy

Uso:
  python awg_normal_fix.py <port.bin> <native.bin> <out.bin>

Nota: ambos bins deben ser el #AMB COMPLETO descomprimido (mismo n de verts por
AWG). Solo se reescribe si n coincide AWG a AWG.
"""
import struct
import sys

WINDOW = 44


def be32(b, o):
    return struct.unpack(">I", b[o:o + 4])[0]


def awg_vertex_region(b, idx):
    """Devuelve (vb0, n) de la region de ventanas del AWG idx."""
    awo = 0x40
    tbl = awo + be32(b, awo + 0x1C)
    a = awo + be32(b, tbl + idx * 4)
    n = be32(b, a + 0x2C) // WINDOW
    ib_abs = a + be32(b, a + 0x30)
    return ib_abs - n * WINDOW, n


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return
    port = bytearray(open(sys.argv[1], "rb").read())
    native = open(sys.argv[2], "rb").read()
    out = sys.argv[3]

    awo = 0x40
    tbl = awo + be32(port, awo + 0x1C)
    n_awg = be32(port, awo + 0x18)
    copied = 0
    for idx in range(n_awg):
        a = awo + be32(port, tbl + idx * 4)
        if port[a:a + 4] != b"#AWG":
            continue
        vb0p, np_ = awg_vertex_region(port, idx)
        vb0n, nn_ = awg_vertex_region(native, idx)
        if np_ != nn_:
            print("AVISO AWG[%d]: n distinto %d/%d -> salto" % (idx, np_, nn_))
            continue
        for k in range(np_):
            op = vb0p + k * WINDOW + 20
            on = vb0n + k * WINDOW + 20
            port[op:op + 12] = native[on:on + 12]
            copied += 1
    open(out, "wb").write(bytes(port))
    print("escrito %s  normales copiadas=%d (de %d AWGs)" % (out, copied, n_awg))


if __name__ == "__main__":
    main()
