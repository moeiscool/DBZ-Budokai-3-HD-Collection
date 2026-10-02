#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compara los VB capturados (dbz3_vbdump.bin) contra la region de ventanas
[vb0, ib) de un bin del juego (#AMB descomprimido). Prueba si el GPU recibe los
bytes del PORT o los del NATIVO.

Formato dump: [hdr LE 12B (addr,size,vfetch)] + size bytes.
Uso: vbdump_vs_bin.py <dbz3_vbdump.bin> <bin.bin> [size=129712]
"""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from awg_vertex_buffer import AwgVertexBuffer
except Exception:
    from importlib import util
    spec = util.spec_from_file_location("avb", os.path.join(os.path.dirname(os.path.abspath(__file__)), "awg_vertex_buffer.py"))
    avb = util.module_from_spec(spec); spec.loader.exec_module(avb)
    AwgVertexBuffer = avb.AwgVertexBuffer


def read_dumps(path):
    d = open(path, "rb").read()
    o = 0; out = []
    while o + 12 <= len(d):
        addr, size, vf = struct.unpack("<III", d[o:o + 12]); o += 12
        if o + size > len(d):
            break
        out.append((addr, size, vf, d[o:o + size]))
        o += size
    return out


def main():
    dump, binpath = sys.argv[1], sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else 129712
    a = AwgVertexBuffer.load(binpath)
    vb_region = bytes(a.data[a.vb0:a.ib_abs])
    print("bin ventanas: vb0=%d ib=%d len=%d (n=%d)" % (a.vb0, a.ib_abs, len(vb_region), a.n))
    print("bin sha1(ventanas): %s" % hashlib.sha1(vb_region).hexdigest()[:16])
    dumps = [x for x in read_dumps(dump) if x[1] == want]
    print("dumps con size=%d: %d" % (want, len(dumps)))
    for (addr, size, vf, data) in dumps[:6]:
        eq = data == vb_region
        # match parcial
        n_eq = sum(1 for i in range(0, min(size, len(vb_region)), 4)
                   if data[i:i+4] == vb_region[i:i+4])
        tot = min(size, len(vb_region)) // 4
        print("  dump addr=0x%08X vf=%d sha1=%s  ==bin:%s  dwords=%d/%d"
              % (addr, vf, hashlib.sha1(data).hexdigest()[:16], eq, n_eq, tot))


if __name__ == "__main__":
    main()
