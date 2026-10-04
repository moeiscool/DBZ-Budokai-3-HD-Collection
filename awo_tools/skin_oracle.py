#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skin_oracle.py - Lint offline del DOMINIO del campo `bone` de un bin #AMB B3 HD.

Comprueba si los vertices de AWG0 estan codificados con `bone` = SLOT de paleta
(lo que consume la GPU; correcto) o con `bone` = indice de hueso de esqueleto
(error de las herramientas de port antes de 2026-10-03). Reconstruye el bind-pose
con ambas interpretaciones y compara la longitud de las aristas (la correcta no
desgarra la malla).  Ver awo_tools/skin_slots.py.

Uso:  python skin_oracle.py <bin_amb_descomprimido> [<bin2> ...]
Sale con 1 si algun bin parece usar el dominio equivocado.
"""
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from awg_vertex_buffer import AwgVertexBuffer  # noqa: E402
from skin_slots import SkinSlots  # noqa: E402


def check(path):
    avb = AwgVertexBuffer.load(path)
    ss = SkinSlots(avb)
    worlds, _ = avb.bind_worlds()
    W = np.array(worlds)
    raw = bytes(avb.data[avb.vb0:avb.ib_abs])
    n = len(raw) // 44
    a = np.frombuffer(raw[:n * 44], dtype=">f4").reshape(n, 11)
    pos = a[:, 0:3].astype(np.float64)
    bone = (np.frombuffer(raw[:n * 44], dtype=">u4").reshape(n, 11)[:, 4] & 0xFF).astype(int)
    ib = [v for v in avb.indices() if v != 0xFFFF and v < n]
    pairs = np.array([(ib[i], ib[i + 1]) for i in range(len(ib) - 1)
                      if ib[i] != ib[i + 1]])

    def model(frame_of):
        out = np.full((n, 3), np.nan)
        for i in range(n):
            k = frame_of(int(bone[i]))
            if k is None or k >= len(W):
                continue
            out[i] = W[k][:3, :3] @ pos[i] + W[k][:3, 3]
        return out

    def stat(P):
        e = np.linalg.norm(P[pairs[:, 0]] - P[pairs[:, 1]], axis=1)
        bad = int(np.isnan(e).sum())
        e = e[np.isfinite(e)]
        return float(np.percentile(e, 90)), float(np.percentile(e, 99)), bad

    p_slot = stat(model(lambda s: ss.bone_of.get(s, 0) if s > 0 else 0))
    p_idx = stat(model(lambda s: s))
    ok = (p_slot[0] <= p_idx[0] * 1.05) and p_slot[2] <= p_idx[2]
    print("%s\n  bone=SLOT de paleta : edge p90 %.3f p99 %.3f (vertices sin marco: %d)"
          % (os.path.basename(path), *p_slot))
    print("  bone=indice esqueleto: edge p90 %.3f p99 %.3f (vertices sin marco: %d)" % p_idx)
    print("  => %s" % ("OK (dominio slot)" if ok else
                       "ATENCION: parece codificado con indices de esqueleto"))
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if all([check(p) for p in sys.argv[1:]]) else 1)
