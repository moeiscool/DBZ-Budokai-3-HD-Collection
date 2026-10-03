#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""awg_diff.py - Diff campo a campo de los AWGs de dos bins #AMB del B3 HD.

Para cada AWG compara pos/nrm/uv/weight/bone/marker/IB entre dos bins. Util para
validar la Via A (inyeccion PS2->HD) contra el nativo y comparar variantes de mod.

Uso:
  python awg_diff.py <binA.bin> <binB.bin> [idx...]   (sin idx = todos)

Campos (layout ventana, stride 44 BE): pos@0, weight@12, bone@16, nrm@20,
FFFFFFFF@32, uv@36. El IB referencia indices de la region `[ib-g(0x2C), ib)`.
"""
import struct
import sys
import numpy as np

WINDOW = 44


def be32(b, o):
    return struct.unpack(">I", b[o:o + 4])[0]


def be16(b, o):
    return struct.unpack(">H", b[o:o + 2])[0]


def load_field(b, idx):
    awo = 0x40
    tbl = awo + be32(b, awo + 0x1C)
    a = awo + be32(b, tbl + idx * 4)
    n = be32(b, a + 0x2C) // WINDOW
    ib_abs = a + be32(b, a + 0x30)
    n_ib = be32(b, a + 0x34) // 2
    vb0 = ib_abs - n * WINDOW
    pos = np.zeros((n, 3))
    w = np.zeros(n)
    bone = np.zeros(n, int)
    nrm = np.zeros((n, 3))
    uv = np.zeros((n, 2))
    mk = np.zeros(n, int)
    for k in range(n):
        o = vb0 + k * WINDOW
        pos[k] = struct.unpack(">3f", b[o:o + 12])
        w[k] = struct.unpack(">f", b[o + 12:o + 16])[0]
        bone[k] = be32(b, o + 16)
        nrm[k] = struct.unpack(">3f", b[o + 20:o + 32])
        mk[k] = be32(b, o + 32)
        uv[k] = struct.unpack(">2f", b[o + 36:o + 44])
    IB = np.array([be16(b, ib_abs + k * 2) for k in range(n_ib)])
    return pos, w, bone, nrm, uv, mk, IB


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    ba = open(sys.argv[1], "rb").read()
    bb = open(sys.argv[2], "rb").read()
    idxs = [int(x) for x in sys.argv[3:]]
    if not idxs:
        n_awg = be32(ba, 0x40 + 0x18)
        idxs = list(range(n_awg))
    for idx in idxs:
        pa = load_field(ba, idx)
        pb = load_field(bb, idx)
        pd = np.abs(pa[0] - pb[0])
        lna = np.linalg.norm(pa[3], axis=1)
        lnb = np.linalg.norm(pb[3], axis=1)
        ndot = (pa[3] * pb[3]).sum(1) / np.clip(lna * lnb, 1e-9, None)
        print("AWG[%2d] pos_mean=%.3f pos_max=%.3f nrm_dot=%.3f nrm_flip=%d "
              "uv_diff=%.4f IB_eq=%s" % (
                  idx, pd.mean(), pd.max(), np.nanmean(ndot),
                  int((ndot < 0).sum()), np.abs(pa[4] - pb[4]).max(),
                  np.array_equal(pa[6], pb[6])))


if __name__ == "__main__":
    main()
