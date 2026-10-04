#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_select_wheel.py - Genera src/select_wheel_gen.inc (US) a partir del codigo
recompilado (generated/): copias de las funciones de la RUEDA del select con la
estructura ampliada de 39 a 64 celdas.

Estructura de la rueda (1448 B, sub_8217E6D8):
  +12 s8 n celdas | +16 u64 mascara de slots | +40 celda actual | +44 celdas[39] x 28 B
  +1136 posiciones[39] x 8 B (u16 +2 visible, u32 +4 angulo)
Ampliada (2368 B): celdas[64] en +44 (hasta +1836) y posiciones[64] en +1840.

  python tools/gen_select_wheel.py        # regenera src/select_wheel_gen.inc
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "generated")
OUT = os.path.join(ROOT, "src", "select_wheel_gen.inc")
POS_OLD, POS_NEW = 1136, 1840
SIZE_NEW = 2368

# funcion -> [(regex, reemplazo, apariciones esperadas)]
SUBS = {
    "8217D710": [(r"\+ 1136;", "+ %d;" % POS_NEW, 1), (r"\+ 1138\b", "+ %d" % (POS_NEW + 2), 1),
                 (r"\+ 1140\b", "+ %d" % (POS_NEW + 4), 1), (r"\+ 142;", "+ %d;" % (POS_NEW // 8), 2)],
    "8217DB20": [(r"\+ 1138\b", "+ %d" % (POS_NEW + 2), 2), (r"\+ 1140\b", "+ %d" % (POS_NEW + 4), 3)],
    "8217DC38": [(r"\+ 1138\b", "+ %d" % (POS_NEW + 2), 2), (r"\+ 1140\b", "+ %d" % (POS_NEW + 4), 3)],
    "8217DE80": [(r"\+ 1138\b", "+ %d" % (POS_NEW + 2), 1), (r"\+ 1140\b", "+ %d" % (POS_NEW + 4), 1)],
    "8217E410": [(r"\+ 1140\b", "+ %d" % (POS_NEW + 4), 1)],
    "8217E6D8": [(r"= 1448;", "= %d;" % SIZE_NEW, 2)],
}


def body(name):
    for f in sorted(os.listdir(GEN)):
        if not re.match(r"dbz3_recomp\.\d+\.cpp$", f):
            continue
        txt = open(os.path.join(GEN, f), encoding="utf-8").read()
        m = re.search(r"^DEFINE_REX_FUNC\(sub_%s\) \{\n(.*?)^\}\n" % name, txt, re.S | re.M)
        if m:
            return m.group(1)
    raise SystemExit("no encuentro sub_%s en generated/" % name)


def main():
    out = ["// GENERADO por tools/gen_select_wheel.py a partir de generated/ (US). NO EDITAR.",
           "// Funciones de la rueda del select con la estructura ampliada a 64 celdas",
           "// (posiciones %d -> %d, tamano 1448 -> %d). Los ganchos estan en select_ext.cpp."
           % (POS_OLD, POS_NEW, SIZE_NEW), ""]
    for name, subs in SUBS.items():
        b = body(name).replace("\tREX_FUNC_PROLOGUE();\n", "")
        for rx, rep, n in subs:
            b, k = re.subn(rx, rep, b)
            if k != n:
                raise SystemExit("sub_%s: %r aparece %d veces (esperado %d)" % (name, rx, k, n))
        b = "\n".join(l for l in b.splitlines() if not l.strip().startswith("//"))
        out.append("static void Wheel_%s(PPCContext& ctx, uint8_t* base) {\n%s\n}\n" % (name, b))
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print("->", OUT)


if __name__ == "__main__":
    sys.exit(main())
