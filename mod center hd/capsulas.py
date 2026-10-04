#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capsulas.py - Capsulas (habilidades) de Budokai 3 HD para los personajes nuevos.

Como funcionan en el juego (RE 2026-10-04, ver docs/03_formatos/CAPSULAS_B3.md):

* Catalogo: data_usi 4 = #SKC (PS2: #SKA), cabecera 0x20 (+0x10 n = 596) + n registros
  de 40 B (BE en la HD). El juego lo tiene residente en 0x824A60E8 y lo usa a traves del
  puntero 0x8237560C (registros); el runtime (roster_ext) copia el catalogo, le anade las
  capsulas nuevas (IDs >= 596) y mueve ese puntero.
    +0  u64 duenos: bit k = ID de personaje k (0..63; los objetos comunes = bits 0..43)
    +8  u8 clase (0x11 transformacion/habilidad, 0x21 ataque, 0x17 fusion/despertar...)
    +10 u8 rareza (nibble alto 0..3) | +14 u8 mascara de formas | +15 u8 coste
    +16 u32 capsula requerida (p.ej. SSJ2 pide SSJ)  | +20.. efecto | +38 u16 precio/100
* Lista por defecto ("Original") de cada personaje: char96 +80 (u16 n) +82 (7 x u16 IDs).
* Transformaciones: char372 +212 + 20*forma, +4 u16 = capsula que exige esa forma.
* Ataques: el bloque del #CCM (BCM) de cada golpe lleva la capsula en w8 (u16 en +16).
* Nombres en combate: data_usi[tabla 0x82373D68 (u16 por ID)] = #AZT con las texturas de
  nombre del personaje; la cabecera +0x18 es el primer ID y cada entrada lleva su ID.
  Los menus usan 2663 (nombres cortos) y 2684 (largos), indexados por ID de capsula.

Ports de Infinite World: su BCM usa otra mecanica (sin modo hiper; "aura burst" con el
boton B, especiales con capsula en 2 ranuras, definitivo con ^E). adapt_iw_bcm() lo pasa
a la de Budokai 3: modo hiper (LT/L2) -> Dragon Rush y definitivos, especiales ligados a
sus capsulas.
"""
import io
import os
import struct
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SKC_ENTRY = 4            # data_usi: catalogo #SKC
NAMES_SHORT = 2663       # data_usi: nombres cortos por ID (menus)
NAMES_LONG = 2684        # data_usi: nombres largos por ID
N_NATIVE = 596           # registros del catalogo original
REC = 40
NAME_FONT = "C:/Windows/Fonts/ARLRDBD.TTF"
NAME_H = 28              # alto logico de los nombres (las texturas son de 32)

KINDS = ("transformacion", "especial", "definitiva")


# ---------------------------------------------------------------- catalogo #SKC
def skc_records(skc):
    n, start = struct.unpack(">II", skc[0x10:0x18])
    return [bytes(skc[start + REC * i:start + REC * (i + 1)]) for i in range(n)]


def skc_owner(rec):
    return struct.unpack(">Q", rec[:8])[0]


def make_record(template, owner_ids, requires=0):
    """Registro nuevo a partir de uno nativo de la misma clase."""
    r = bytearray(template)
    mask = 0
    for i in owner_ids:
        mask |= 1 << i
    struct.pack_into(">Q", r, 0, mask)
    struct.pack_into(">I", r, 16, requires)
    r[28:36] = bytes(8)          # sin "se convierte en" (X10 Kamehameha, etc.)
    return bytes(r)


def first_owned(recs, cid):
    """Primer ID de capsula con el bit del personaje (= base de su banco de nombres)."""
    for i, r in enumerate(recs):
        m = skc_owner(r)
        if m & (1 << cid) and m != (1 << 64) - 1 and bin(m).count("1") < 40:
            return i
    return None


def owned(recs, cid):
    """Capsulas propias del personaje (solo su bit; sin los objetos comunes)."""
    return [i for i, r in enumerate(recs) if skc_owner(r) == (1 << cid)]


# ---------------------------------------------------------------- #CCM (BCM HD)
def ccm_child(amb):
    """(offset, tamano) del #CCM dentro del bin de camara (#AMB HD)."""
    n, tbl = struct.unpack(">II", amb[0x10:0x18])
    for k in range(n):
        off, size = struct.unpack(">II", amb[tbl + 16 * k:tbl + 16 * k + 8])
        if size and amb[off:off + 4] == b"#CCM":
            return off, size
    return None


def ccm_blocks(ccm):
    """[(offset, es_starter)] de todos los bloques de 0x40 B alcanzables."""
    n = struct.unpack(">H", ccm[0x1E:0x20])[0]
    starters = [struct.unpack(">I", ccm[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(n)]
    seen, out, todo = set(), [], [(o, True) for o in starters]
    while todo:
        o, st = todo.pop(0)
        if o in seen or not (0x50 <= o <= len(ccm) - 0x40):
            continue
        seen.add(o)
        out.append((o, st))
        nb = struct.unpack(">H", ccm[o + 0x0E:o + 0x10])[0]
        for k in range(min(nb, 64)):
            q = o + 0x40 + 4 * k
            if q + 4 <= len(ccm):
                todo.append((struct.unpack(">I", ccm[q:q + 4])[0], False))
    return out


def w(ccm, o, i):
    return struct.unpack(">H", ccm[o + 2 * i:o + 2 * i + 2])[0]


def setw(ccm, o, i, v):
    struct.pack_into(">H", ccm, o + 2 * i, v & 0xFFFF)


# Bloque de golpe del #CCM (64 B, u16 BE salvo +8 que es u32: en la HD su mitad alta es la
# condicion y la baja el tipo de especial; en el #BCM de la PS2 van al reves):
#   w0 direccion | w1 botones (1 P, 2 K, 4 G, 8 E) | w2-w3 ventana | w4 tipo de especial (IW:
#   ranura 1/2, +0x10 = tras combo) | w5 condicion (0x0400 modo hiper, 0x0004 transformar,
#   0x0008 definitivo, 0x0002 especial con capsula (B3), 0x8000 idem (IW), 0x4000 aura IW,
#   0x0001 cuesta ki) | w6 condicion 2 | w7 ramas | w8 capsula | w9 ki | w10 formas |
#   w12-w15 codigos de ataque (#CSK)
TYPE, COND = 4, 5


def bcm_summary(ccm):
    """Lo que importa para las capsulas: modo hiper, especiales, definitivos, transformar."""
    out = {"hiper": False, "aura_iw": False, "especiales": [], "definitivos": [], "transforma": False}
    for o, st in ccm_blocks(ccm):
        c1, cap = w(ccm, o, COND), w(ccm, o, 8)
        if st and c1 & 0x0400:
            out["hiper"] = True
        if st and c1 & 0x4000:
            out["aura_iw"] = True
        if st and c1 & 0x0004:
            out["transforma"] = True
        if c1 & 0x0008 and (cap or c1 & 0x8000):
            out["definitivos"].append(cap)
        elif cap and c1 & 0x8002:
            out["especiales"].append(cap)
    for k in ("especiales", "definitivos"):
        out[k] = list(dict.fromkeys(out[k]))
    return out


UNUSED_CAP = 595         # registro vacio del catalogo: nadie la lleva -> el golpe no sale
KI = {}                  # capsula -> barras de ki (del BCM de IW), para el texto de la ficha


def adapt_iw_bcm(ccm, special_ids, ultimate_ids):
    """BCM de Infinite World -> mecanica de Budokai 3 (in place). special_ids: IDs de capsula
    B3 para la 1a, 2a... capsula especial del BCM; ultimate_ids: para los definitivos.
    Devuelve lineas de informe."""
    rep = []
    KI.clear()
    blocks = ccm_blocks(ccm)
    iw_specials = []
    for o, _ in blocks:
        c1, cap = w(ccm, o, COND), w(ccm, o, 8)
        if c1 & 0x8000 and cap and not c1 & 0x0008 and cap not in iw_specials:
            iw_specials.append(cap)
    for o, st in blocks:
        c1, cap = w(ccm, o, COND), w(ccm, o, 8)
        # aura burst de IW (boton B) -> activar el modo hiper de B3 (LT / L2)
        if st and c1 & 0x4000 and w(ccm, o, 1) == 0x20:
            setw(ccm, o, 0, 0)
            setw(ccm, o, 1, 0x0F)
            setw(ccm, o, COND, 0x0400)
            setw(ccm, o, 6, 0x0001)
            rep.append("modo hiper: entrada de 'aura burst' de IW convertida (LT/L2)")
            continue
        # definitivo (^E en IW, sin capsula) -> P+K+G+E en modo hiper con su capsula
        if c1 & 0x0008 and c1 & 0x8000:
            k = len([1 for r in rep if r.startswith("definitivo")])
            cid = ultimate_ids[min(k, len(ultimate_ids) - 1)] if ultimate_ids else 0
            setw(ccm, o, 0, 0)
            setw(ccm, o, 1, 0x0F)
            setw(ccm, o, COND, 0x000A)
            setw(ccm, o, TYPE, 0)
            setw(ccm, o, 6, 0x8001)
            setw(ccm, o, 8, cid)
            KI[cid] = max(KI.get(cid, 0), (w(ccm, o, 9) + 500) // 1000)
            setw(ccm, o, 9, 0)
            setw(ccm, o, 11, 0)
            rep.append("definitivo -> capsula %d" % cid)
            continue
        # especiales: en IW la direccion elige la ranura (1 = >E, 2 = <E) y cada capsula
        # tiene entradas para las dos; en B3 cada capsula tiene su direccion fija.
        if c1 & 0x8000 and cap in iw_specials:
            k = iw_specials.index(cap)
            slot = w(ccm, o, TYPE) & 0x0F
            cid = special_ids[k] if k < len(special_ids) else 0
            setw(ccm, o, COND, (c1 & ~0x8001) | 0x0002)
            setw(ccm, o, TYPE, 0)
            setw(ccm, o, 11, 0)
            setw(ccm, o, 8, cid if (slot == k + 1 or slot == 0) and cid else UNUSED_CAP)
            if cid:
                KI[cid] = max(KI.get(cid, 0), (w(ccm, o, 9) + 500) // 1000)
    for k, cap in enumerate(iw_specials):
        rep.append("especial %d (IW %#x) -> capsula %s" % (k + 1, cap, special_ids[k] if k < len(special_ids) else "-"))
    if hyper_first(ccm):
        rep.append("modo hiper: su entrada pasa delante de los definitivos (mismos botones)")
    return rep


def hyper_first(ccm):
    """El modo hiper y los definitivos usan los mismos botones (P+K+G+E) y el juego se queda
    con la primera entrada de la lista: en todos los personajes de B3 la del modo hiper va
    antes. Mueve su entrada delante de la primera de definitivo. Devuelve si cambio algo."""
    n = struct.unpack(">H", ccm[0x1E:0x20])[0]
    st = [struct.unpack(">I", ccm[0x50 + 4 * k:0x54 + 4 * k])[0] for k in range(n)]
    hyp = [k for k, o in enumerate(st) if w(ccm, o, COND) & 0x0400]
    ult = [k for k, o in enumerate(st) if w(ccm, o, COND) & 0x0008 and w(ccm, o, 1) == w(ccm, st[hyp[0]], 1)] if hyp else []
    if not hyp or not ult or hyp[0] < ult[0]:
        return False
    st.insert(ult[0], st.pop(hyp[0]))
    for k, o in enumerate(st):
        struct.pack_into(">I", ccm, 0x50 + 4 * k, o)
    return True


def remap_caps(ccm, mapping):
    """Cambia IDs de capsula en todos los golpes (p.ej. las del donante por las propias)."""
    n = 0
    for o, _ in ccm_blocks(ccm):
        cap = w(ccm, o, 8)
        if cap in mapping:
            setw(ccm, o, 8, mapping[cap])
            n += 1
    return n


# ---------------------------------------------------------------- nombres (#AZT)
def render_name(text, h=NAME_H, color=(255, 255, 255, 255)):
    """Nombre de capsula al estilo del juego (blanco con borde oscuro): mismo tamano y
    posicion que los nativos (calibrado con "Kamehameha" de los bancos 2682 / SCMKLL)."""
    f = ImageFont.truetype(NAME_FONT, 18)
    wid = int(f.getlength(text)) + 10
    out = Image.new("RGBA", (min(wid, 508), h), (0, 0, 0, 0))
    ImageDraw.Draw(out).text((3, h // 2 - (0 if h >= 28 else 1)), text, font=f, anchor="lm", fill=color,
                             stroke_width=2, stroke_fill=(30, 20, 20, 255))
    return np.array(out)


# ---------------------------------------------------------------- panel de descripcion
# data_usi 2079 + ID: #AZT de 5 texturas que el panel de "Edit Skills" pinta en columna:
# 0 nombre (como los rotulos), 1 quien la usa, 2 que hace, 3 botones y coste, 4 nota
# (16 x 24 vacia si no hay). Texto oscuro (18, 10, 0) sobre transparente, ~16 px, 19-20 px
# por linea, 6 px arriba, ajustado a 208 px (medido sobre Kamehameha, Spirit Bomb, LSSJ).
DESC_FONT = "C:/Windows/Fonts/arial.ttf"
DESC_W, DESC_PITCH, DESC_TOP = 208, 19, 6
DESC_COLOR = (18, 10, 0, 255)


def _wrap(text, f, width):
    out = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split(" "):
            cand = (line + " " + word).strip()
            if line and f.getlength(cand) > width:
                out.append(line)
                line = word
            else:
                line = cand
        out.append(line)
    return out


def render_lines(text):
    if not text:
        return np.zeros((24, 16, 4), np.uint8)
    f = ImageFont.truetype(DESC_FONT, 16)
    lines = _wrap(text, f, DESC_W)
    wid = min(DESC_W + 8, int(max(f.getlength(t) for t in lines)) + 6)
    h = DESC_TOP + DESC_PITCH * len(lines) + 5
    out = Image.new("RGBA", (max(16, wid), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    for k, t in enumerate(lines):
        d.text((1, DESC_TOP + DESC_PITCH * k), t, font=f, fill=DESC_COLOR)
    return np.array(out)


def desc_texts(kind, name, who, ki, extra=None):
    """Textos por defecto (estilo de las nativas) de una capsula nueva."""
    extra = extra or {}
    if kind == "definitiva":
        what = "Can launch Ultimate-move\n" + name
        cmd = "P+K+G+E attack hits\nopponent in Hyper Mode\n(Consumes %d Ki Gauge%s)" % (ki, "" if ki == 1 else "s")
    elif kind == "transformacion":
        what = "Fight as\n" + name
        cmd = "P+K+G\nWith %d or more Ki Gauges" % ki
    else:
        what = "Can launch Death-move\n" + name
        cmd = "(Consumes %d Ki Gauge%s)" % (ki, "" if ki == 1 else "s")
    return (extra.get("quien") or who, extra.get("descripcion") or what,
            extra.get("botones") or cmd, extra.get("nota") or "")


def build_desc(name, who, what, cmd, note=""):
    """#AZT del panel de descripcion (data_usi 2079 + ID de las nativas)."""
    return build_bank(0, {0: render_name(name), 1: render_lines(who), 2: render_lines(what),
                          3: render_lines(cmd), 4: render_lines(note)}, tall=True)


def _pow2(v):
    p = 16
    while p < v:
        p *= 2
    return p


def _dds_dxt3(w_, h_):
    return (b"DDS \x7c\x00\x00\x00\x07\x10\x08\x00" + struct.pack("<IIIII", h_, w_, h_ * w_, 0, 0) +
            bytes(44) + b"\x20\x00\x00\x00\x04\x00\x00\x00" + b"DXT3" + bytes(20) +
            struct.pack("<I", 0x1000) + bytes(16))


def _tex_blob(rgba, tall=False):
    """DXT3 de un rotulo: alto 32 (nombres) o, con tall, el de las descripciones nativas
    (potencia de 2, minimo 64; las lineas de texto miden hasta ~84 px)."""
    from texture_b3 import encode_dxt3  # noqa: PLC0415
    lh, lw = rgba.shape[:2]
    W, H = _pow2(lw), (max(64, _pow2(lh)) if tall else 32)
    canvas = np.zeros((H, W, 4), np.uint8)
    canvas[:lh, :lw] = rgba[:H, :W]
    return _dds_dxt3(W, H) + encode_dxt3(canvas), W, (lw, lh)


def azt_entries(b):
    n, idx = struct.unpack(">II", b[0x10:0x18])
    return [struct.unpack(">I", b[idx + 4 * k:idx + 4 * k + 4])[0] for k in range(n)]


def azt_read(b, k):
    o = azt_entries(b)[k]
    if not o:
        return None
    do, ds = struct.unpack(">II", b[o + 0x14:o + 0x1C])
    lw, lh = struct.unpack(">HH", b[o + 0x10:o + 0x14])
    img = np.array(Image.open(io.BytesIO(bytes(b[do:do + ds]))).convert("RGBA"))
    return img[:lh, :lw]


def build_azt(base, items, flag28=0x400):
    """#AZT con las texturas items = {id: rgba}, indice disperso desde `base`."""
    return build_bank(base, items, flag28)


def build_bank(base, items, flag28=0x400, tall=False):
    """#AZT de nombres de un personaje: items = {id_capsula: rgba (alto 28)}. Indice disperso
    desde `base` (cabecera +0x18) hasta el ID mas alto."""
    ids = sorted(items)
    n = ids[-1] - base + 1
    idx = 0x20
    first = idx + 4 * n
    first = (first + 0xF) // 0x10 * 0x10
    data_base = (first + 0x30 * len(ids) + 0x7F) // 0x80 * 0x80
    index = bytearray(4 * n)
    ent, body = bytearray(), bytearray()
    vram = 0
    for cid in ids:
        blob, W, (lw, lh) = _tex_blob(items[cid], tall)
        H = max(64, _pow2(lh)) if tall else 64
        k = cid - base
        struct.pack_into(">I", index, 4 * k, first + len(ent))
        ent += struct.pack(">II", cid, 0x21) + struct.pack(">HHHH", lw, lh, (W - 1).bit_length(), (H - 1).bit_length())
        ent += struct.pack(">HH", lw, lh) + struct.pack(">II", data_base + len(body), len(blob))
        ent += struct.pack(">IIIII", 1, 0, 0, vram, flag28)
        vram += len(blob) // 0x20
        body += blob + bytes((-len(blob)) % 0x80)
    hdr = struct.pack(">4s7I", b"#AZT", 0, 0, 0, n, idx, base, 0)
    out = bytearray(hdr) + index
    out += bytes(first - len(out)) + ent
    out += bytes(data_base - len(out)) + body
    struct.pack_into(">I", out, 0x1C, zlib.crc32(bytes(body)))
    return bytes(out)


def extend_bank(b, items):
    """Anade texturas (id_capsula -> rgba) a un #AZT existente indexado por ID (base de la
    cabecera), alargando el indice disperso. No mueve los datos existentes."""
    base = struct.unpack(">I", b[0x18:0x1C])[0]
    offs = azt_entries(b)
    n_new = max(len(offs), max(items) - base + 1)
    offs = offs + [0] * (n_new - len(offs))
    out = bytearray(b)
    out += bytes((-len(out)) % 0x80)
    last = max(offs)
    vram = struct.unpack(">I", b[last + 0x24:last + 0x28])[0] + struct.unpack(">I", b[last + 0x18:last + 0x1C])[0] // 0x20
    ents = []
    for cid in sorted(items):
        blob, W, (lw, lh) = _tex_blob(items[cid])
        do = len(out)
        out += blob + bytes((-len(blob)) % 0x80)
        e = struct.pack(">II", cid, 0x21) + struct.pack(">HHHH", lw, lh, (W - 1).bit_length(), 6)
        e += struct.pack(">HH", lw, lh) + struct.pack(">II", do, len(blob))
        e += struct.pack(">IIIII", 1, 0, 0, vram, 0x400)
        vram += len(blob) // 0x20
        ents.append((cid, e))
    out += bytes((-len(out)) % 0x10)
    for cid, e in ents:
        offs[cid - base] = len(out)
        out += e
    new_idx = len(out)
    out += struct.pack(">%dI" % n_new, *offs)
    out += bytes((-len(out)) % 0x10)
    struct.pack_into(">II", out, 0x10, n_new, new_idx)
    return bytes(out)


# ---------------------------------------------------------------- #CSK (BSK HD)
# El modo hiper de B3 lo activa la animacion de su codigo de ataque: su bloque del #CSK
# lleva las propiedades (AP) que ponen el estado. El "aura burst" de IW tiene otras, asi
# que en un port se injerta el bloque hiper de un personaje de B3 (todos usan el mismo:
# animacion comun del banco 3 y las mismas AP).
def amb_children(b):
    n, tbl = struct.unpack(">II", b[0x10:0x18])
    return [list(struct.unpack(">4I", b[tbl + 16 * k:tbl + 16 * k + 16])) for k in range(n)]


def amb_rebuild(b, replace):
    """#AMB HD con los hijos `replace` {indice: bytes} sustituidos (hijos alineados a 32)."""
    kids = amb_children(b)
    n = len(kids)
    tbl = struct.unpack(">I", b[0x14:0x18])[0]
    start = (tbl + 16 * n + 0x1F) // 0x20 * 0x20
    out = bytearray(b[:start])
    for k, (off, size, typ, z) in enumerate(kids):
        data = replace.get(k, b[off:off + size]) if size else b""
        if size or k in replace:
            out += bytes((-len(out)) % 0x20)
            kids[k] = [len(out), len(data), typ, z]
            out += data
    out += bytes((-len(out)) % 0x20)
    for k, e in enumerate(kids):
        struct.pack_into(">4I", out, tbl + 16 * k, *e)
    return bytes(out)


def csk_child(amb):
    for k, (off, size, typ, _) in enumerate(amb_children(amb)):
        if size and amb[off:off + 4] == b"#CSK":
            return k, off, size
    return None


def csk_graft(dst, dst_code, src, src_code):
    """Copia el bloque de ataque src_code de otro #CSK (con sus AP) al final de dst y lo
    enlaza en dst_code. Devuelve el #CSK nuevo."""
    n, lst = struct.unpack(">II", src[0x10:0x18])
    so = struct.unpack(">I", src[lst + 4 * src_code:lst + 4 * src_code + 4])[0]
    blk = bytearray(src[so:so + 48])
    nap, apo = struct.unpack(">II", blk[0x28:0x30])
    aps = [struct.unpack(">HHI", src[apo + 8 * a:apo + 8 * a + 8]) for a in range(nap)]
    out = bytearray(dst)
    out += bytes((-len(out)) % 0x10)
    new_lines = []
    for t, nl, do in aps:
        new_lines.append((t, nl, len(out)))
        out += src[do:do + 16 * nl]
    out += bytes((-len(out)) % 0x10)
    new_apo = len(out)
    for t, nl, do in new_lines:
        out += struct.pack(">HHI", t, nl, do)
    out += bytes((-len(out)) % 0x10)
    struct.pack_into(">II", blk, 0x28, nap, new_apo)
    new_blk = len(out)
    out += blk
    dn, dl = struct.unpack(">II", dst[0x10:0x18])
    if dst_code >= dn:
        raise ValueError("codigo %#x fuera de la lista del #CSK" % dst_code)
    struct.pack_into(">I", out, dl + 4 * dst_code, new_blk)
    return bytes(out)


def hyper_codes(ccm):
    """Codigos de ataque (suelo, aire) de la entrada de modo hiper de un #CCM B3."""
    for o, st in ccm_blocks(ccm):
        if st and w(ccm, o, COND) & 0x0400:
            return w(ccm, o, 12), w(ccm, o, 13)
    return None


# ---------------------------------------------------------------- ficha de habilidades (SCM)
# data_usi 5..52 = "SCM<codigo>.amb": la lista de habilidades de la pausa y el rotulo de la
# capsula al usarla en combate. #AMB HD con un #AZT (por capsula, en el orden
# transformaciones + ataques: nombre y condicion/coste) y un #CFC (filas de 16 B: u32
# capsula (0xFFFFFFFF = transformarse), u8 variante, glifos de los botones). El juego la
# elige por personaje con la tabla 0x82324468 (ID, trajes, HUD, indice) y el indice apunta
# a un registro de 16 B (u32 fid, ptr ataques u16, ptr transformaciones u16, n, n).
def scm_parts(b):
    kids = amb_children(b)
    azt = cfc = None
    for off, size, typ, _ in kids:
        if b[off:off + 4] == b"#AZT":
            azt = b[off:off + size]
        elif b[off:off + 4] == b"#CFC":
            cfc = b[off:off + size]
    rows = []
    if cfc:
        n, start = struct.unpack(">II", cfc[4:12])
        rows = [cfc[start + 16 * i:start + 16 * (i + 1)] for i in range(n)]
    imgs = [azt_read(azt, k) for k in range(len(azt_entries(azt)))] if azt else []
    return imgs, rows


def build_scm(imgs, rows):
    """#AMB HD de ficha de habilidades: imgs = [rgba] (nombre, condicion, ...), rows = [16 B]."""
    azt = build_azt(0, {k: im for k, im in enumerate(imgs)}, 0x40)
    cfc = bytearray(b"#CFC" + struct.pack(">III", len(rows), 0x10, 0))
    for r in rows:
        cfc += r
    kids = [(azt, 2), (bytes(cfc), 0xFFFFFFFF)]
    hdr = bytearray(struct.pack(">4s7I", b"#AMB", 0x20, 0, 2, len(kids), 0x20, 0x60, 0))
    hdr += bytes(0x20 * 2)
    out = bytearray(hdr[:0x20]) + bytes(16 * len(kids))
    out += bytes((-len(out)) % 0x20)
    ents = []
    for data, typ in kids:
        out += bytes((-len(out)) % 0x20)
        ents.append((len(out), len(data), typ, 0))
        out += data
    out += bytes((-len(out)) % 0x20)
    for k, e in enumerate(ents):
        struct.pack_into(">4I", out, 0x20 + 16 * k, *e)
    struct.pack_into(">I", out, 0x18, ents[0][0])
    return bytes(out)


def ki_text(n):
    return "%d Ki gauge%s consumed" % (n, "" if n == 1 else "s")
