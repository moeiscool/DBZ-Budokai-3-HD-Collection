#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analiza dbz3_vbdump.bin: formato = secuencia de [hdr 12B (addr,size,vfetch)] +
[size bytes]. Lista los dumps y busca el VB del modelo (size 129712 = AWG0 cuerpo;
N*44). Uso: vbdump_info.py <dbz3_vbdump.bin>
"""
import sys, struct


def main():
    d = open(sys.argv[1], "rb").read()
    o = 0
    n = 0
    sizes = {}
    mb = []
    while o + 12 <= len(d) and n < 5000:
        addr, size, vf = struct.unpack("<III", d[o:o + 12])
        o += 12
        if o + size > len(d):
            print("truncado en dump %d (size=%d)" % (n, size))
            break
        sizes[size] = sizes.get(size, 0) + 1
        if size >= 100000:
            mb.append((n, addr, size, vf, o))
        o += size
        n += 1
    print("dumps leidos: %d  bytes consumidos: %d/%d" % (n, o, len(d)))
    print("tamaños (top):")
    for s, c in sorted(sizes.items(), key=lambda x: -x[1])[:12]:
        print("  size=%-10d x%d" % (s, c))
    print("\nVB grandes (>=100KB): %d" % len(mb))
    for (i, addr, size, vf, off) in mb[:10]:
        print("  dump#%d addr=0x%08X size=%d vfetch=%d off=%d" % (i, addr, size, vf, off))


if __name__ == "__main__":
    main()
