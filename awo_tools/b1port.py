#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""b1port.py - Moveset de Budokai 1 (PS2) -> moveset de Budokai 3 (PS2), listo para ps2hd.

RE 2026-10-04 (Zarbon/Dodoria; corpus B1 EU + B3 GH):

  B1 por personaje (DATA_EN.AFS, registro de 564 B en el ELF desde 0x259390, +320..):
    AMM comun (368, compartido, huesos GOK_*), AMM propio, AMM pequeno, BCM, BSK, SPX,
    banco de sonido (IECS + datos).
  B3 por personaje: ANM = #AMB [BSK, AMM propio, AMM 2 (animaciones del rival en los
    agarres, esqueleto generico GOK_*), AMM 3]; CAM = #AMB [AMC camara, AML, BCM, SPX];
    BSP = efectos de tecnicas.

  - Los formatos BSK/BCM/AMM/SPX son los mismos (AMM v2, SPX 0.01, BSK con la misma
    cabecera y sub-bloques de 48 B [anim u16][almacen u16]...; BSK v2 -> v4).
  - Almacenes de animacion del BSK: B1 0 = AMM comun, 1 = AMM propio; B3 3 = AMM propio
    (hijo 1 del ANM) y 0 = almacen global del juego (anim 201/202). El AMM propio nuevo
    = propio B1 + comun B1 (por sufijo de hueso) + las que se injerten del donante.
  - Codigos de ataque: los combos/golpes (0x200+) coinciden en numero y duracion entre B1
    y B3 (comprobado con Goku). B3 usa ~250 codigos que B1 no tiene (mecanicas nuevas:
    modo hiper, definitivos, rafagas...): se injertan del donante B3 (bloque + AP + HR).
  - BCM: mismo bloque de 64 B; B1 marca suelo/aire en w6 con 0/9 y B3 con 1/0x40; el ki
    de B1 va en una escala ~14 veces menor. Se injertan del donante las entradas de
    arranque de mecanicas que B1 no tiene (modo hiper y las que usan codigos injertados).

RE 2026-10-04 (2): revision antes de la prueba en juego (38 movesets B3 + 18 pares B1/B3):

  - Linea AP tipo 1: el codigo HR va en +4 (u16), no en +6 (+6 = 0 / 0xFFFF).
  - Codigos < 0x200: B1 y B3 NO comparten significado salvo 0 (reposo) y 0xEA. B3 deja la
    mayoria al motor (andar, guardia, dano, rafaga de ki... animaciones genericas) y solo
    algunos personajes los redefinen (Freeza ninguno). B1 4/5 = andar con desplazamiento,
    B3 4 = bucle quieto; B1 0x10 = rafaga de ki (entrada BCM), B3 0x10 = bucle agachado.
    -> de B1 solo se conservan 0, 0xEA y 0x200-0x3FF; los de B3 que el motor dispara se
    injertan del donante, salvo los de postura basica (genericos del juego).
  - Agarre (P+G): el golpe del agarre (p. ej. 0x247) lanza el guion SPX 20, que llama a
    una rutina comun con una BASE de codigo propia de cada personaje (0x480 Broly, 0x490
    Nappa, 0x4B8 Vegeta...): los codigos BASE, BASE+1, BASE+8, BASE+9 son las animaciones
    del agarre, no entrada/victoria (prueba en juego 2026-10-04: con la victoria de B1 en
    0x480, Zarbon "se quedaba mirando"). Se injertan del donante tal cual.
  - Pose del select: no sale del moveset sino de los bancos comunes data_cmn 3881/3882
    (una animacion de reposo por ID de personaje); la anade roster_build.
  - Efectos (AP tipo 7, clase 0): el valor es un indice del BSP del personaje, que es el
    del donante; los >= 0x64 de B1 son efectos propios del personaje B1 y en el BSP del
    donante son los suyos (el Dodoria Beam lanzaba antes el ataque 0x64 de Nappa):
    --quitar-efecto los elimina.
  - Lanzamientos B3 = 0x4A0-0x4BB (B1 0x418-0x43F, otra numeracion y otro guion): del
    donante, que trae sus animaciones de la victima en el AMM 2.
  - #SPX (guiones de cinematica, tabla por ranura): B3 usa la ranura 0 para el ataque
    acometida del modo hiper y la 20 para los definitivos; B1 usa 0-5 para sus especiales
    con agarre, y sus ordenes (01 20 nnnn) no existen en el SPX de B3 -> se usa el SPX del
    donante y los golpes HR "con guion" (tipo 3) de B1 pasan a golpe que despide (tipo 2).
  - Dano: B3 = 0.63 x B1 (mediana de 1200 golpes, 15 personajes) -> se escala.
  - Esqueletos: el motor casa las pistas por nombre de hueso. Los modelos B3 de Zarbon y
    Dodoria tienen las mismas medidas que los de B1 (+-2 %), pero otros nombres (prefijo X),
    hombreras/pendientes/trenza con otra orientacion de reposo y la cara con otras
    posiciones: el AMM se escribe con los nombres del modelo B3, sin las pistas de giro de
    los huesos cuyo reposo difiere y con las posiciones corregidas por la diferencia.
    Las animaciones del donante se escalan a la altura de cadera del personaje.

Uso:
  python b1port.py --registro 13 --donante-anm 127 --donante-cam 123 --salida DIR [--hd]
                   [--modelos traje1.amb traje2.amb ...] [--quitar-efecto 64 ...]
"""
import argparse
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "mod center hd")]

B1_ISO = os.path.join(ROOT, "ps2_games", "DragonBall Z - Budokai (Europe) (En,Fr,De,Es,It).iso")
B1_REC = 0x259390
B1_REC_SIZE = 564
KI_SCALE = 14
DMG_SCALE = 0.63
HR_AT = 4                  # codigo HR en la linea AP tipo 1


def code_ranges(spec):
    out = set()
    for part in spec.split():
        a, _, b = part.partition("-")
        out.update(range(int(a, 16), int(b or a, 16) + 1))
    return out


# codigos que el motor de B3 dispara sin entrada BCM (en >= 3 de los 38 movesets)
ENGINE = code_ranges("38-3c ea ec-ed f4-ff 138-13c 1ec-1ed 233 23e 256 259 280-293 2a0-2b1 "
                     "2c0-2d9 2e1-2f7 333 33e 356 359 3c8-3d7 3e1-3f7 433-437 46e-471 480-48d "
                     "490-4bb 4c0-4c1")
# postura basica: si el personaje no la define, el juego usa la generica (p. ej. Freeza)
BASIC = code_ranges("1-37 100-137")
B1_KEEP = code_ranges("0 ea 200-3ff")


# ---------------------------------------------------------------- fuentes
class B1:
    def __init__(self, iso_path=B1_ISO):
        import iso
        self.iso = iso.Iso(iso_path)
        self.f = self.iso.open("/USR/DATA_EN.AFS")
        self.f.seek(4)
        n = struct.unpack("<I", self.f.read(4))[0]
        self.tab = struct.unpack("<%dI" % (2 * n), self.f.read(8 * n))
        self.elf = None

    def entry(self, i):
        self.f.seek(self.tab[2 * i])
        return self.f.read(self.tab[2 * i + 1])

    def record(self, rec):
        if self.elf is None:
            self.elf = self.iso.read("/SLES_512.33")
        r = self.elf[B1_REC + B1_REC_SIZE * rec:B1_REC + B1_REC_SIZE * (rec + 1)]
        v = [struct.unpack_from("<i", r, o)[0] for o in range(320, 360, 4)]
        return dict(common=v[0], amm=v[1], small=v[2], bcm=v[4], bsk=v[5], spx=v[6], snd=v[7:10],
                    models=[x for x in struct.unpack_from("<4i", r, 128) if x > 0])


def amb_kids(d):
    n, t = struct.unpack("<II", d[0x10:0x18])
    out = []
    for k in range(n):
        o, s, ty, _ = struct.unpack_from("<4I", d, t + 16 * k)
        out.append((d[o:o + s] if s else b"", ty))
    return out


def amb_build(kids):
    """#AMB PS2 (version 3) con hijos [(datos, tipo)] alineados a 16."""
    n = len(kids)
    start = (0x20 + 16 * n + 15) // 16 * 16
    out = bytearray(struct.pack("<8I", 0x424D4123, 0x20, 0, 3, n, 0x20, start, 0))
    out += bytes(start - len(out))
    ents = []
    for data, ty in kids:
        out += bytes((-len(out)) % 16)
        ents.append((len(out) if data else 0, len(data), ty & 0xFFFFFFFF, 0))
        out += data
    for k, e in enumerate(ents):
        struct.pack_into("<4I", out, 0x20 + 16 * k, *e)
    out += bytes((-len(out)) % 16)
    return bytes(out)


# ---------------------------------------------------------------- AMM
def bone_key(name):
    s = name.lstrip("X")
    return (name.startswith("X"), s.split("_", 1)[1] if "_" in s else s)


def reduce_track(tr, rot, tol_rot=32, tol_pos=1e-2):
    """Quita las claves intermedias que la interpolacion lineal de sus vecinas reproduce
    (giro: u16, 65536 = 360 grados, tolerancia 32 = 0.18 grados, invisible; posicion: f32)."""
    head = tr[:12]
    nk = struct.unpack_from("<I", tr, 8)[0]
    ks = 8 if rot else 16
    if nk < 3:
        return tr
    keys = []
    for k in range(nk):
        if rot:
            f, x, y, z = struct.unpack_from("<4H", tr, 12 + 8 * k)
        else:
            f, x, y, z = struct.unpack_from("<I3f", tr, 12 + 16 * k)
        keys.append((f, (x, y, z), tr[12 + ks * k:12 + ks * (k + 1)]))
    out = [keys[0]]
    for k in range(1, nk - 1):
        a, b, c = out[-1], keys[k], keys[k + 1]
        if c[0] == a[0]:
            out.append(b)
            continue
        t = (b[0] - a[0]) / (c[0] - a[0])
        ok = True
        for i in range(3):
            if rot:
                d1 = (c[1][i] - a[1][i] + 32768) % 65536 - 32768
                pred = a[1][i] + d1 * t
                err = abs((b[1][i] - pred + 32768) % 65536 - 32768)
                ok &= err <= tol_rot
            else:
                pred = a[1][i] + (c[1][i] - a[1][i]) * t
                ok &= abs(b[1][i] - pred) <= tol_pos
        if not ok:
            out.append(b)
    out.append(keys[-1])
    if len(out) == nk:
        return tr
    return bytes(head[:8]) + struct.pack("<I", len(out)) + b"".join(k[2] for k in out)


class Amm:
    """Animaciones como [ (flags, var, frames, {clave_hueso: [pista giro, pos, escala]}) ]."""

    def __init__(self, b):
        n, t, nb, no = struct.unpack("<4I", b[0x10:0x20])
        self.head = b[:0x20]
        self.names = [b[no + 32 * i:no + 32 * i + 32].split(b"\0")[0].decode("latin1") for i in range(nb)]
        self.anims = []
        for k in range(n):
            flags, var, nf, off = struct.unpack_from("<4I", b, t + 16 * k)
            if not off:
                self.anims.append((flags, var, nf, None))
                continue
            per = 3 if flags & 0x10 else 2
            bones = {}
            for j in range(nb):
                tr = []
                for i in range(per):
                    p = struct.unpack_from("<I", b, off + 4 * (per * j + i))[0]
                    if not p:
                        tr.append(None)
                        continue
                    nk = struct.unpack_from("<I", b, p + 8)[0]
                    ks = 8 if i == 0 else 16
                    tr.append(b[p:p + 12 + ks * nk])
                bones[bone_key(self.names[j])] = tr
            self.anims.append((flags, var, nf, bones))

    def build(self, names, anims, reduce=False):
        """Serializa con la tabla de nombres `names` (las pistas se buscan por sufijo)."""
        keys = [bone_key(n) for n in names]
        nb = len(names)
        out = bytearray(self.head)
        struct.pack_into("<4I", out, 0x10, len(anims), 0x20, nb, 0)
        out += bytes(16 * len(anims))
        for a, (flags, var, nf, bones) in enumerate(anims):
            if bones is None:
                struct.pack_into("<4I", out, 0x20 + 16 * a, flags, var, nf, 0)
                continue
            scale = any(tr and len(tr) > 2 and tr[2] for tr in bones.values())
            per = 3 if scale else 2
            flags = (flags | 0x10) if scale else (flags & ~0x10)
            out += bytes((-len(out)) % 16)
            blk = len(out)
            out += bytes(4 * per * nb)
            for j, key in enumerate(keys):
                tr = bones.get(key)
                if not tr:
                    continue
                for i in range(min(per, len(tr))):
                    if tr[i] is None:
                        continue
                    out += bytes((-len(out)) % 4)
                    struct.pack_into("<I", out, blk + 4 * (per * j + i), len(out))
                    out += reduce_track(tr[i], i == 0) if reduce else tr[i]
            struct.pack_into("<4I", out, 0x20 + 16 * a, flags, var, nf, blk)
        out += bytes((-len(out)) % 16)
        struct.pack_into("<I", out, 0x1C, len(out))
        for n in names:
            out += n.encode("latin1")[:31].ljust(32, b"\0")
        return bytes(out)


# ---------------------------------------------------------------- BSK
def bsk_head(b):
    return struct.unpack("<4I", b[0x10:0x20])        # n, lista, n_hr, hr


def bsk_blocks(b):
    """{direccion: [offsets de sub-bloques de 48 B]} (misma regla que ps2hd.conv_bsk)."""
    n, lst, n_hr, hr = bsk_head(b)
    addrs = sorted({a for a in struct.unpack("<%dI" % n, b[lst:lst + 4 * n]) if a})
    aset = set(addrs)
    out = {}
    for a in addrs:
        s, subs = a, []
        while s + 48 <= hr:
            pad, n_ap, ap_off = struct.unpack("<3I", b[s + 0x24:s + 0x30])
            if pad != 0 or not (0 <= n_ap < 64) or (n_ap and not (hr > ap_off >= 0x20)):
                break
            subs.append(s)
            s += 48
            if s in aset:
                break
        out[a] = subs
    return out


def bsk_code_list(b):
    n, lst, _, _ = bsk_head(b)
    return list(struct.unpack("<%dI" % n, b[lst:lst + 4 * n]))


def remap_b1_pools(b, new_index):
    """Almacenes B1 (0 comun, 1 propio) -> B3 3 (AMM propio nuevo); new_index(pool, anim)
    da el indice en el AMM nuevo (solo entran las animaciones que el guion usa)."""
    out = bytearray(b)
    for subs in bsk_blocks(b).values():
        for s in subs:
            anim, pool = struct.unpack_from("<HH", out, s)
            if pool in (0, 1):
                struct.pack_into("<HH", out, s, new_index(pool, anim), 3)
    struct.pack_into("<I", out, 0x0C, 4)
    return out


def bsk_graft(dst, src, codes, anim_map, anim_override=None, code_map=None):
    """Injerta en dst (B1 ya remapeado) los codigos `codes` de src (BSK B3): sub-bloques,
    tablas AP, lineas y bloques HR (renumerados). anim_map(anim) -> anim en el AMM nuevo
    (almacen 3 del donante); anim_override {codigo: anim nueva} usa el bloque de src como
    plantilla con otra animacion. Lo nuevo va delante de la seccion HR (que sigue al final)."""
    anim_override = anim_override or {}
    code_map = code_map or {}
    n, lst, n_hr, hr = bsk_head(dst)
    sn, slst, sn_hr, shr = bsk_head(src)
    src_list = bsk_code_list(src)
    sblocks = bsk_blocks(src)
    head = bytearray(dst[:hr])
    tail_hr = bytearray(dst[hr:hr + 128 * n_hr])
    hr_map = {}
    new_addr = {}

    def hr_new(code):
        if code not in hr_map:
            hr_map[code] = n_hr + len(hr_map)
            tail_hr.extend(src[shr + 128 * code:shr + 128 * code + 128])
        return hr_map[code]

    for code in codes:
        a = src_list[code] if code < sn else 0
        if not a or code_map.get(code, code) >= n:
            continue
        ov = anim_override.get(code)
        key = (a, ov)
        if key not in new_addr:
            subs = sblocks.get(a, [])
            if not subs:
                continue
            # tablas AP y lineas de cada sub-bloque
            new_subs = []
            for s in subs:
                blk = bytearray(src[s:s + 48])
                anim, pool = struct.unpack_from("<HH", blk, 0)
                if pool == 3:
                    struct.pack_into("<H", blk, 0, anim_map(anim) if ov is None else ov)
                _, n_ap, ap_off = struct.unpack_from("<3I", blk, 0x24)
                if n_ap:
                    aps = []
                    for k in range(n_ap):
                        t, nl, do = struct.unpack_from("<HHI", src, ap_off + 8 * k)
                        lines = bytearray(src[do:do + 16 * nl])
                        if t == 1:
                            for ln in range(nl):
                                hc = struct.unpack_from("<H", lines, 16 * ln + HR_AT)[0]
                                if hc != 0xFFFF and hc < sn_hr:
                                    struct.pack_into("<H", lines, 16 * ln + HR_AT, hr_new(hc))
                        head.extend(bytes((-len(head)) % 16))
                        aps.append((t, nl, len(head)))
                        head.extend(lines)
                    head.extend(bytes((-len(head)) % 16))
                    new_ap = len(head)
                    for t, nl, do in aps:
                        head.extend(struct.pack("<HHI", t, nl, do))
                    struct.pack_into("<3I", blk, 0x24, 0, n_ap, new_ap)
                new_subs.append(blk)
            head.extend(bytes((-len(head)) % 16))
            new_addr[key] = len(head)
            for blk in new_subs:
                head.extend(blk)
            # un sub-bloque falso de cierre evita que el lector una dos ataques seguidos
            head.extend(b"\xff" * 48)
        struct.pack_into("<I", head, lst + 4 * code_map.get(code, code), new_addr[key])
    head.extend(bytes((-len(head)) % 16))
    new_hr = len(head)
    struct.pack_into("<4I", head, 0x10, n, lst, n_hr + len(hr_map), new_hr)
    return bytes(head + tail_hr), len(hr_map)


def bsk_fix_b1_hits(b, report):
    """Bloques HR de B1: dano a escala B3 y golpes "con guion" (tipo 3, ranura del SPX de B1,
    que en B3 no existe) -> golpe que despide (tipo 2) con el dano del mayor despido."""
    out = bytearray(b)
    n, lst, n_hr, hr = bsk_head(b)
    lines = [hr + 128 * k + 16 * ln for k in range(n_hr) for ln in range(8)]
    knock = [struct.unpack_from("<H", b, o)[0] for o in lines if struct.unpack_from("<H", b, o + 4)[0] == 2]
    conv_dmg = int(round(max(knock or [100]) * DMG_SCALE))
    conv = 0
    for o in lines:
        dmg, grunt, vis, st, sc = struct.unpack_from("<HBBHH", out, o)
        if st == 3:
            struct.pack_into("<HBBHHff", out, o, conv_dmg, grunt, vis, 2, 0, 40.0, 0.0)
            conv += 1
        elif dmg:
            struct.pack_into("<H", out, o, max(1, int(round(dmg * DMG_SCALE))))
    report.append("golpes B1: dano x%.2f; %d lineas con guion de B1 -> despide (dano %d)" % (
        DMG_SCALE, conv, conv_dmg))
    return bytes(out)


def bsk_st3_codes(b, slot=None):
    """Codigos con algun golpe HR de tipo 3 (guion SPX), opcionalmente de una ranura."""
    n, lst, n_hr, hr = bsk_head(b)
    blocks = bsk_blocks(b)
    out = set()
    for c, a in enumerate(bsk_code_list(b)):
        for s in blocks.get(a, []) if a else []:
            _, n_ap, ap_off = struct.unpack("<3I", b[s + 0x24:s + 0x30])
            for k in range(n_ap):
                t, nl, do = struct.unpack_from("<HHI", b, ap_off + 8 * k)
                for ln in range(nl if t == 1 else 0):
                    h = struct.unpack_from("<H", b, do + 16 * ln + HR_AT)[0]
                    for line in range(8 if h < n_hr else 0):
                        st, sc = struct.unpack_from("<HH", b, hr + 128 * h + 16 * line + 4)
                        if st == 3 and (slot is None or sc == slot):
                            out.add(c)
    return out


# ---------------------------------------------------------------- esqueletos
def amo_bind(amo):
    """{sufijo: (nombre, quat, pos)} del esqueleto de un #AMO PS2."""
    g = amo.find(b"#AMG")
    nb, names_at = struct.unpack_from("<I", amo, g + 0x10)[0], struct.unpack_from("<I", amo, g + 0x1C)[0]
    out = {}
    for i in range(nb):
        name = amo[g + names_at + 32 * i:g + names_at + 32 * i + 32].split(b"\0")[0].decode("latin1")
        f = struct.unpack_from("<7f", amo, g + 0x20 + 80 * i)
        out.setdefault(bone_key(name)[1], (name, f[0:4], f[4:7]))
    return out


def model_amo(path_or_bytes):
    d = path_or_bytes if isinstance(path_or_bytes, bytes) else open(path_or_bytes, "rb").read()
    return next(k for k, t in amb_kids(d) if k[:4] == b"#AMO") if d[:4] == b"#AMB" else d


def pos_keys(tr):
    n = struct.unpack_from("<I", tr, 8)[0]
    return [struct.unpack_from("<I3f", tr, 12 + 16 * k) for k in range(n)]


def pos_track(tr, keys):
    return bytes(tr[:12]) + b"".join(struct.pack("<I3f", *k) for k in keys)


def retarget(anims, b1_pairs, report, skip_from=None, hips=((1.0, 0.0), (1.0, 0.0)), common=()):
    """anims [(flags, var, nf, {clave: pistas})] -> mismas con {sufijo: pistas} ajustadas
    al esqueleto B3. b1_pairs [(bind B1, bind B3)] por forma. Desde `skip_from` son del
    donante: sin posiciones de huesos (salvo las a 0, que ocultan); hips = ((escala, +y) de la
    cadera de las de B1, (escala, +y) de las del donante) (ver altura.correccion); las
    `common` (almacen comun de B1, esqueleto GOK) tampoco llevan posiciones de huesos."""
    drop_rot = set()
    for src, dst in b1_pairs:
        for suf in set(src) & set(dst):
            q1, q3 = src[suf][1], dst[suf][1]
            # solo accesorios (hombreras, pendientes, trenza, boca, marcas): en el cuerpo
            # una diferencia pequena de reposo es mejor que congelar el hueso
            if suf not in CORE_BONES and 1 - abs(sum(x * y for x, y in zip(q1, q3))) > 0.015:
                drop_rot.add(suf)
    src, dst = b1_pairs[0]
    delta = {}
    for suf in set(src) & set(dst):
        d = [b - a for a, b in zip(src[suf][2], dst[suf][2])]
        if suf != "WAIST" and max(abs(x) for x in d) > 0.02:
            delta[suf] = d
            if suf not in CORE_BONES and max(abs(x) for x in d) > 0.3:
                drop_rot.add(suf)          # cadena con otra forma (trenza, cara): su reposo
    out = []
    for i, (flags, var, nf, bones) in enumerate(anims):
        if bones is None:
            out.append((flags, var, nf, None))
            continue
        donor = skip_from is not None and i >= skip_from
        foreign = donor or i in common
        nb = {}
        for (x, suf), tr in bones.items():
            if suf in nb and not x:
                continue
            tr = list(tr)
            if suf in drop_rot and not donor:
                tr[0] = None
            if len(tr) > 1 and tr[1]:
                keys = pos_keys(tr[1])
                zero = all(abs(v) < 1e-4 for k in keys for v in k[1:])
                if suf == "WAIST":
                    hs, hy = hips[1] if donor else hips[0]
                    if (hs, hy) != (1.0, 0.0):
                        tr[1] = pos_track(tr[1], [(k[0], k[1] * hs, k[2] * hs + hy, k[3] * hs) for k in keys])
                elif zero:
                    pass
                elif foreign:
                    tr[1] = None
                elif suf in delta:
                    d = delta[suf]
                    tr[1] = pos_track(tr[1], [(k[0], k[1] + d[0], k[2] + d[1], k[3] + d[2]) for k in keys])
            nb[suf] = tr
        out.append((flags, var, nf, nb))
    report.append("esqueleto: sin giro (reposo distinto) %s; posiciones corregidas %s" % (
        sorted(drop_rot), sorted(delta)))
    return out


def target_names(models):
    names, seen = [], set()
    for amo in models:
        for suf, (name, q, p) in sorted(amo_bind(amo).items(), key=lambda kv: amo_order(amo, kv[1][0])):
            if suf not in seen:
                seen.add(suf)
                names.append(name)
    return names


def amo_order(amo, name):
    g = amo.find(b"#AMG")
    return amo.find(name.encode("latin1") + b"\0", g)


CORE_BONES = {"BODY", "WAIST", "STMC", "CHEST", "NECK", "HEAD", "LCHN", "RCHN", "LARMROT", "RARMROT",
              "LARM1", "RARM1", "LARM2", "RARM2", "LHANDROT", "RHANDROT", "L00_LHAND", "L00_RHAND",
              "LLEGROT", "RLEGROT", "LLEG1", "RLEG1", "LLEG2", "RLEG2", "LFOOT1", "RFOOT1",
              "LFOOT2", "RFOOT2", "M_JAW"}


# ---------------------------------------------------------------- poses (comparacion de animaciones)
POSE_BONES = ("WAIST", "STMC", "CHEST", "NECK", "HEAD", "LARM1", "LARM2", "RARM1", "RARM2",
              "LLEG1", "LLEG2", "RLEG1", "RLEG2")


def pose(anim, fr):
    out = {}
    for (x, suf), tr in (anim[3] or {}).items():
        if suf in POSE_BONES and tr[0]:
            n = struct.unpack_from("<I", tr[0], 8)[0]
            val = struct.unpack_from("<3H", tr[0], 14)
            for k in range(n):
                f = struct.unpack_from("<H", tr[0], 12 + 8 * k)[0]
                if f > fr:
                    break
                val = struct.unpack_from("<3H", tr[0], 14 + 8 * k)
            out[suf] = val
    return out


def pose_dist(p, q):
    ks = [k for k in p if k in q]
    if not ks:
        return 1e9
    return sum(abs((p[k][i] - q[k][i] + 32768) % 65536 - 32768) for k in ks for i in range(3)) / len(ks) / 3 * 360 / 65536


# ---------------------------------------------------------------- BCM
def bcm_parse(c):
    n = struct.unpack("<H", c[0x1E:0x20])[0]
    starters = [struct.unpack_from("<I", c, 0x50 + 4 * k)[0] for k in range(n)]
    blocks = {}

    def walk(o):
        if o in blocks or not (0x50 <= o <= len(c) - 0x40):
            return
        nb = struct.unpack_from("<H", c, o + 0x0E)[0]
        kids = [struct.unpack_from("<I", c, o + 0x40 + 4 * k)[0] for k in range(min(nb, 64))]
        blocks[o] = [bytearray(c[o:o + 0x40]), kids]
        for k in kids:
            walk(k)

    for s in starters:
        walk(s)
    return starters, blocks


def bcm_build(head, starters, nodes):
    """nodes: {clave: [bloque 64 B, [claves hijas]]}; starters: [claves]."""
    order, seen = [], set()

    def visit(k):
        if k in seen:
            return
        seen.add(k)
        order.append(k)
        for ch in nodes[k][1]:
            visit(ch)

    for s in starters:
        visit(s)
    base = 0x50 + 4 * len(starters)
    pos, at = base, {}
    for k in order:
        at[k] = pos
        pos += 0x40 + 4 * len(nodes[k][1])
    out = bytearray(head[:0x50])
    struct.pack_into("<I", out, 0x04, len(order) + 1)
    struct.pack_into("<H", out, 0x1E, len(starters))
    for s in starters:
        out += struct.pack("<I", at[s])
    for k in order:
        blk = bytearray(nodes[k][0])
        struct.pack_into("<H", blk, 0x0E, len(nodes[k][1]))
        out += blk
        for ch in nodes[k][1]:
            out += struct.pack("<I", at[ch])
    out += bytes((-len(out)) % 16)
    return bytes(out)


def w16(blk, i):
    return struct.unpack_from("<H", blk, 2 * i)[0]


def set16(blk, i, v):
    struct.pack_into("<H", blk, 2 * i, v & 0xFFFF)


def bcm_hyper_codes(c):
    """Codigos del subarbol de la entrada de modo hiper (condicion 0x400)."""
    st, bl = bcm_parse(c)
    out, seen = set(), set()
    stack = [o for o in st if w16(bl[o][0], 4) & 0x0400]
    while stack:
        o = stack.pop()
        if o in seen:
            continue
        seen.add(o)
        out.update(x for x in (w16(bl[o][0], i) for i in (12, 13, 14)) if x)
        stack += bl[o][1]
    return out


def convert_bcm(b1c, donor_c, report, code_remap, throw_map):
    """BCM de B1 -> B3. code_remap {codigo B1: codigo B3} (rafaga de ki, transformacion);
    throw_map {codigo del donante: codigo nuevo} para su agarre (P+G)."""
    st1, bl1 = bcm_parse(b1c)
    nodes = {}
    w6_seen = {}
    for o, (blk, kids) in bl1.items():
        w6 = w16(blk, 6)
        nw6 = {0: 0x0001, 0x0009: 0x0040}.get(w6, w6)
        w6_seen[w6] = nw6
        set16(blk, 6, nw6)
        if w16(blk, 9):
            set16(blk, 9, min(0xFFFF, w16(blk, 9) * KI_SCALE))
        for i in (12, 13, 14):
            if w16(blk, i) in code_remap:
                set16(blk, i, code_remap[w16(blk, i)])
        nodes[("b1", o)] = [blk, [("b1", k) for k in kids]]
    starters = []
    dropped = 0
    caps_start = {}
    for o in st1:
        blk = bl1[o][0]
        # P+K+G+E sin condicion: en B3 es el modo hiper y el definitivo
        if w16(blk, 1) == 0x000F:
            dropped += 1
            continue
        # P+K+G sin transformacion B3 (el donante no tiene 0x2E0): se quedaria colgado
        if w16(blk, 1) == 0x0007 and w16(blk, 4) & 0x0004 and w16(blk, 12) != 0x2E0:
            dropped += 1
            continue
        # tecnica con boton propio (P+G en B1): P+G es el agarre en B3 -> entrada directa
        if w16(blk, 8) and w16(blk, 1) != 0x0008:
            caps_start[w16(blk, 8)] = blk
            dropped += 1
            continue
        starters.append(("b1", o))
    # tecnicas: en B1 solo cierran combos; en B3 tienen entrada directa (direccion + E)
    for o, (blk, kids) in bl1.items():
        cap = w16(blk, 8)
        if cap and o not in st1 and w16(blk, 1) == 0x0008 and cap not in caps_start:
            caps_start[cap] = blk
    for n, (cap, blk) in enumerate(sorted(caps_start.items())):
        nb = bytearray(blk)
        set16(nb, 0, 1 + n % 2)
        set16(nb, 1, 0x0008)
        set16(nb, 2, 0)
        set16(nb, 3, 0)
        set16(nb, 4, 0x0002)
        set16(nb, 6, 0x0001)
        set16(nb, 7, 0)
        nodes[("cap", cap)] = [nb, []]
        starters.append(("cap", cap))
        report.append("BCM: tecnica %d con entrada directa %s + E (codigo %#x)" % (
            cap, "->" if n % 2 == 0 else "<-", w16(nb, 12)))
    report.append("BCM B1: %d entradas (%d quitadas o movidas), %d bloques; suelo/aire %s; "
                  "codigos cambiados %s" % (len(st1), dropped, len(bl1),
                                            {hex(k): hex(v) for k, v in w6_seen.items()},
                                            {hex(k): hex(v) for k, v in code_remap.items()}))
    # entradas del donante: modo hiper y agarre
    st2, bl2 = bcm_parse(donor_c)
    add = 0
    for o in st2:
        blk = bl2[o][0]
        cond, cap, code = w16(blk, 4), w16(blk, 8), w16(blk, 12)
        hyper = bool(cond & 0x0400)
        throw = w16(blk, 1) == 0x0005 and not cond and not cap and code in throw_map
        if not (hyper or throw):
            continue

        def copy(k):
            key = ("d", k)
            if key not in nodes:
                nb = bytearray(bl2[k][0])
                for i in (12, 13, 14):
                    if w16(nb, i) in throw_map:
                        set16(nb, i, throw_map[w16(nb, i)])
                nodes[key] = [nb, []]
                nodes[key][1] = [copy(ch) for ch in bl2[k][1]]
            return key
        starters.append(copy(o))
        add += 1
        report.append("BCM: entrada del donante %s (botones %#x, condicion %#x, codigo %#x)" % (
            "modo hiper" if hyper else "agarre", w16(blk, 1), cond, w16(nodes[("d", o)][0], 12)))
    return bcm_build(b1c, starters, nodes), add


# ---------------------------------------------------------------- port
def first_waist_y(anim):
    tr = (anim[3] or {}).get((False, "WAIST")) or (anim[3] or {}).get((True, "WAIST"))
    return pos_keys(tr[1])[0][2] if tr and len(tr) > 1 and tr[1] else None


def spx_slot_span(s, slot):
    """(inicio, fin) del guion de la ranura `slot` de un #SPX (None si no tiene)."""
    ns = struct.unpack_from("<I", s, 0x18)[0]
    T = struct.unpack_from("<%dI" % ns, s, 0x20)
    if slot >= ns or T[slot] == 0xFFFFFFFF:
        return None
    offs = sorted(set(x for x in T if x != 0xFFFFFFFF)) + [len(s)]
    return T[slot], offs[offs.index(T[slot]) + 1]


def spx_code_refs(s, slot):
    """Codigos de ataque (0x200-0x3FF) que el guion de la ranura empuja (08 20 nnnn):
    {codigo: [posiciones]}. La acometida del modo hiper termina asi con la rafaga de ki
    del donante (Cooler 0x21c: efecto 1 en el frame 12)."""
    span = spx_slot_span(s, slot)
    out = {}
    if span:
        for i in range(span[0], span[1] - 3):
            if s[i] == 0x08 and s[i + 1] == 0x20:
                v = struct.unpack_from("<H", s, i + 2)[0]
                if 0x200 <= v < 0x400:
                    out.setdefault(v, []).append(i)
    return out


def renumber(lines):
    """AP tipos 3-7: el byte +2 de las lineas es SIEMPRE una permutacion de 0..n-1 (los 77 000
    de SB y B3); al quitar lineas se vuelve a numerar conservando el orden relativo."""
    rank = {v: i for i, v in enumerate(sorted(x[2] for x in lines))}
    return [x[:2] + bytes([rank[x[2]]]) + x[3:] for x in lines]


def bsk_drop_effects(b, codes, effects, report):
    """Quita de los codigos `codes` las lineas de efecto (AP tipo 7, clase 0) con valor en
    `effects` (la tabla de lineas se compacta y se renumera; el resto del bloque no cambia)."""
    out = bytearray(b)
    blocks = bsk_blocks(b)
    L = bsk_code_list(b)
    done, removed = set(), 0
    for c in codes:
        for s in blocks.get(L[c], []) if L[c] else []:
            _, n_ap, ap_off = struct.unpack_from("<3I", out, s + 0x24)
            for k in range(n_ap):
                t, nl, do = struct.unpack_from("<HHI", out, ap_off + 8 * k)
                if t != 7 or do in done:
                    continue
                done.add(do)
                lines = [bytes(out[do + 16 * i:do + 16 * i + 16]) for i in range(nl)]
                keep = [ln for ln in lines
                        if not (struct.unpack_from("<H", ln, 4)[0] == 0 and struct.unpack_from("<H", ln, 8)[0] in effects)]
                if len(keep) != nl:
                    removed += nl - len(keep)
                    keep = renumber(keep)
                    out[do:do + 16 * nl] = b"".join(keep) + bytes(16 * (nl - len(keep)))
                    struct.pack_into("<HHI", out, ap_off + 8 * k, t, len(keep), do)
    report.append("efectos quitados %s: %d lineas" % ([hex(e) for e in sorted(effects)], removed))
    return bytes(out)


def amm_tracks(anim):
    """Frame 0 de una animacion de Amm como {sufijo: (giro, pos)} (para altura)."""
    out = {}
    for (x, suf), tr in (anim[3] or {}).items():
        rot = struct.unpack_from("<3H", tr[0], 14) if tr[0] and struct.unpack_from("<I", tr[0], 8)[0] else None
        pos = struct.unpack_from("<3f", tr[1], 16) if len(tr) > 1 and tr[1] and struct.unpack_from("<I", tr[1], 8)[0] else None
        out.setdefault(suf, (rot, pos))
    return out


def port(b1, rec, donor_anm, donor_cam, report, models=(), drop_effects=(), donor_model=None):
    r = b1.record(rec)
    report.append("registro B1 %d: %s" % (rec, r))
    own, common = Amm(b1.entry(r["amm"])), Amm(b1.entry(r["common"]))
    pools = {0: common, 1: own}
    raw = b1.entry(r["bsk"])
    n, lst, _, _ = bsk_head(raw)
    L1 = bsk_code_list(raw)

    def b1_anim(code):
        pool, anim = struct.unpack_from("<HH", raw, L1[code])[::-1]
        return pool, anim

    idle = pools[b1_anim(0)[0]].anims[b1_anim(0)[1]]
    # numeracion B3 de las entradas de B1 que cambian de codigo
    dk = amb_kids(donor_anm)
    d_bsk, d_amm = dk[0][0], Amm(dk[1][0])
    d_list = bsk_code_list(d_bsk)
    d_used = {c for c, a in enumerate(d_list) if a}
    d_bcm = next(d for d, t in amb_kids(donor_cam) if d[:4] == b"#BCM")
    st1, bl1 = bcm_parse(b1.entry(r["bcm"]))
    taken = {c for c, a in enumerate(L1) if a and c in B1_KEEP} | d_used | ENGINE

    def free_pair():
        for c in range(0x260, 0x280):
            if c not in taken and c + 0x100 not in taken:
                taken.update((c, c + 0x100))
                return c
        raise ValueError("no quedan codigos libres 0x260-0x27F")

    code_remap, transform = {}, None
    for o in st1:
        blk = bl1[o][0]
        cs = sorted({w16(blk, i) for i in (12, 13, 14)} - {0})
        if cs and all(c < 0x200 for c in cs):          # rafaga de ki (E): 0x10/0x110 en B1
            k = free_pair()
            code_remap.update({c: k + (0x100 if c >= 0x100 else 0) for c in cs})
        elif w16(blk, 1) == 0x0007 and w16(blk, 4) & 0x0004 and len(d_list) > 0x3E0 and d_list[0x2E0]:
            transform = (w16(blk, 12), w16(blk, 13))   # P+K+G: en B3 la transformacion es 0x2E0
            code_remap.update({transform[0]: 0x2E0, transform[1]: 0x3E0})
    throw_map = {}
    st2, bl2 = bcm_parse(d_bcm)
    b1_keep_used = {c for c, a in enumerate(L1) if a and c in B1_KEEP}
    for o in st2:
        blk = bl2[o][0]
        if w16(blk, 1) == 0x0005 and not w16(blk, 4) and not w16(blk, 8):   # agarre (P+G)
            cs = sorted({w16(blk, i) for i in (12, 13, 14)} - {0})
            g = min(cs)
            k = g if g not in b1_keep_used and g + 0x100 not in b1_keep_used else free_pair()
            for c in cs:
                throw_map[c] = k + (0x100 if c >= 0x300 else 0)
    # de B1 solo lo que significa lo mismo en B3
    bsk = bytearray(raw)
    for c, k in code_remap.items():
        if c < 0x200:
            struct.pack_into("<I", bsk, lst + 4 * k, L1[c])
    cur = bsk_code_list(bytes(bsk))
    dropped = [c for c, a in enumerate(cur) if a and c not in B1_KEEP]
    for c in dropped:
        struct.pack_into("<I", bsk, lst + 4 * c, 0)
    # su bloque queda muerto: un cierre 0xFF evita que el lector lo una al ataque anterior
    kept_addr = {a for c, a in enumerate(cur) if a and c not in dropped}
    for a in {cur[c] for c in dropped} - kept_addr:
        bsk[a:a + 48] = b"\xff" * 48
    bsk = bsk_fix_b1_hits(bytes(bsk), report)
    if drop_effects:
        bsk = bsk_drop_effects(bsk, [c for c in range(n) if c in B1_KEEP], set(drop_effects), report)
    anims, idx = [], {}

    def new_index(pool, anim):
        if (pool, anim) not in idx:
            src = pools[pool].anims
            idx[(pool, anim)] = len(anims)
            anims.append(src[anim] if anim < len(src) else (9, 0, 1, None))
        return idx[(pool, anim)]

    bsk = remap_b1_pools(bsk, new_index)
    report.append("B1: %d codigos conservados, %d quitados (significan otra cosa en B3); "
                  "%d animaciones usadas" % (len(set(c for c, a in enumerate(L1) if a)) - len(dropped),
                                             len(dropped), len(anims)))
    i_trans = [new_index(*b1_anim(c)) for c in transform] if transform else None
    b1_used = {c for c, a in enumerate(bsk_code_list(bsk)) if a}
    rush = bsk_st3_codes(d_bsk, 0)
    d_bcm = next(d for d, t in amb_kids(donor_cam) if d[:4] == b"#BCM")
    hyper = bcm_hyper_codes(d_bcm)
    graft = sorted(((d_used & (ENGINE | rush | hyper)) - b1_used - BASIC)
                   | (d_used & hyper))
    if transform:
        graft = [c for c in graft if c not in code_ranges("2e0-2e7 3e0-3e7")]
    report.append("modo hiper del donante: codigos %s; acometida (SPX 0): %s" % (
        sorted(hex(c) for c in hyper), sorted(hex(c) for c in rush)))
    skip_from = len(anims)
    dmap = {}

    def anim_map(a):
        if a not in dmap:
            dmap[a] = len(anims)
            anims.append(d_amm.anims[a] if a < len(d_amm.anims) else (9, 0, 1, None))
        return dmap[a]

    bsk, n_hr_new = bsk_graft(bsk, d_bsk, graft, anim_map)
    report.append("guion: %d codigos del motor injertados del donante (%d animaciones, %d bloques "
                  "de dano)" % (len(graft), len(dmap), n_hr_new))
    if throw_map:
        bsk, _ = bsk_graft(bsk, d_bsk, sorted(throw_map), anim_map, code_map=throw_map)
        report.append("agarre (P+G) del donante: %s" % {hex(k): hex(v) for k, v in throw_map.items()})
    # codigos que los guiones del donante (acometida 0, agarre/definitivos 20) piden por numero:
    # si B1 usa ese numero para otro golpe, el del donante va a un codigo libre y el guion se
    # reescribe (sin esto la acometida acababa sin la rafaga de ki final)
    d_spx = next(d for d, t in amb_kids(donor_cam) if d[:4] == b"#SPX")
    spx_patch = {}
    cur = bsk_code_list(bsk)
    for sl in (0, 20):
        for v, where in sorted(spx_code_refs(d_spx, sl).items()):
            ok = [i for i in where if i + 4 < len(d_spx) and d_spx[i + 4] in (0x01, 0x02, 0x08, 0x09, 0x12)]
            if not ok or not (v < len(d_list) and d_list[v]):
                continue
            if v < len(cur) and cur[v] and v in b1_used:
                band = 0x360 if v >= 0x300 else 0x260         # 0x3xx = version en el aire
                k = next((c for c in range(band, band + 0x20) if c not in taken and not cur[c]), None)
                if k is None:
                    report.append("aviso: sin codigo libre para %#x del guion %d" % (v, sl))
                    continue
                taken.add(k)
                bsk, _ = bsk_graft(bsk, d_bsk, [v], anim_map, code_map={v: k})
                spx_patch.update({i: k for i in ok})
                report.append("guion %d del donante: codigo %#x (en B1 es otro golpe) -> %#x" % (sl, v, k))
            elif v < len(cur) and not cur[v]:
                bsk, _ = bsk_graft(bsk, d_bsk, [v], anim_map)
                report.append("guion %d del donante: codigo %#x injertado" % (sl, v))
            cur = bsk_code_list(bsk)
    if spx_patch:
        d_spx2 = bytearray(d_spx)
        for i, k in spx_patch.items():
            struct.pack_into("<H", d_spx2, i + 2, k)
        d_spx_new = bytes(d_spx2)
    else:
        d_spx_new = d_spx
    # plantillas del donante con animaciones de B1: reposo 2 (seleccion) y transformacion
    ov = {}
    if d_list[2]:
        ov[2] = new_index(*b1_anim(0))
    if transform:
        for k in range(8):
            ov[0x2E0 + k], ov[0x3E0 + k] = i_trans[0], i_trans[1]
    for c in sorted(ov):
        src = 0x2E0 if 0x2E0 <= c < 0x2E8 else 0x3E0 if 0x3E0 <= c < 0x3E8 else c
        if d_list[src]:
            bsk, _ = bsk_graft(bsk, d_bsk, [src], anim_map, {src: ov[c]}, {src: c})
    if transform:
        report.append("transformacion: P+K+G -> 0x2E0/0x3E0 (bloque B3) con la animacion B1 de %s" % (
            [hex(c) for c in transform]))
        # el 0x64 del BSP es el efecto de transformacion propio del donante (todos los B3 lo usan)
        if drop_effects:
            bsk = bsk_drop_effects(bsk, code_ranges("2e0-2e7 3e0-3e7"), set(drop_effects), report)
    if models:
        import altura  # noqa: PLC0415
        b3 = [model_amo(m) for m in models]
        pairs = [(amo_bind(model_amo(b1.entry(m1))), amo_bind(m3)) for m1, m3 in zip(r["models"], b3)]
        names = target_names(b3)
        # altura: tobillos a la altura relativa del esqueleto de origen (B1 / donante)
        sk3 = altura.skeleton(models[0] if isinstance(models[0], bytes) else open(models[0], "rb").read())
        hips = [(1.0, 0.0), (1.0, 0.0)]
        hips[0] = altura.correccion(sk3, altura.skeleton(b1.entry(r["models"][0])), amm_tracks(idle))
        if donor_model:
            hips[1] = altura.correccion(sk3, altura.skeleton(donor_model), altura.idle_tracks(donor_anm))
        report.append("altura: cadera de B1 x%.3f %+.2f, del donante x%.3f %+.2f" % (*hips[0], *hips[1]))
        rt = retarget(anims, pairs, report, skip_from, hips, {i for (pl, a), i in idx.items() if pl == 0})
        anims = [(f, v, nf, None if b is None else
                  {bone_key(nm): b[bone_key(nm)[1]] for nm in names if bone_key(nm)[1] in b})
                 for f, v, nf, b in rt]
        missing = [nm for nm in own.names if bone_key(nm)[1] not in {bone_key(x)[1] for x in names}]
        report.append("huesos: %d del modelo B3; de B1 sin hueso en el modelo: %s" % (len(names), missing))
    else:
        names = own.names
    amm = own.build(names, anims, reduce=True)
    anm = amb_build([(bsk, 0xFFFFFFFF), (amm, 3), (dk[2][0], 3), (dk[3][0], 3)])
    ck = amb_kids(donor_cam)
    bcm, added = convert_bcm(b1.entry(r["bcm"]), d_bcm, report, code_remap, throw_map)
    # el SPX es el del donante: los guiones de B1 usan ordenes que el de B3 no tiene
    cam = amb_build([(bcm, t) if d[:4] == b"#BCM" else (d_spx_new, t) if d[:4] == b"#SPX" else (d, t)
                     for d, t in ck])
    return anm, cam


def donor_model(anm_fid):
    """Modelo (PS2 GH) del personaje B3 cuyo moveset es `anm_fid` (tabla de roster_build)."""
    import afs_pair  # noqa: PLC0415
    import roster_build  # noqa: PLC0415
    for e in roster_build.DB["ids"]:
        if e["anm"] and e["anm"][0] == anm_fid and e["models"]:
            return afs_pair.ps2(e["models"][0])
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registro", type=int, required=True, help="personaje de B1 (13 Zarbon, 14 Dodoria)")
    ap.add_argument("--donante-anm", type=int, required=True, help="fid data_cmn del ANM B3 donante (PS2 GH)")
    ap.add_argument("--donante-cam", type=int, required=True, help="fid data_cmn de la CAM B3 donante")
    ap.add_argument("--modelos", nargs="*", default=[],
                    help="modelos B3 del personaje (#AMB PS2), en el orden de los de B1")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--hd", action="store_true", help="convertir a HD (ps2hd)")
    ap.add_argument("--quitar-efecto", nargs="*", default=[],
                    help="efectos de B1 (hex) que se quitan: en el BSP del donante son otros")
    a = ap.parse_args()
    import afs_pair
    b1 = B1()
    report = []
    anm, cam = port(b1, a.registro, afs_pair.ps2(a.donante_anm), afs_pair.ps2(a.donante_cam), report,
                    a.modelos, [int(x, 16) for x in a.quitar_efecto], donor_model(a.donante_anm))
    if a.hd:
        import ps2hd
        anm, cam = bytes(ps2hd.convert_block(anm)), bytes(ps2hd.convert_block(cam))
    os.makedirs(a.salida, exist_ok=True)
    open(os.path.join(a.salida, "anm.bin"), "wb").write(anm)
    open(os.path.join(a.salida, "camara.bin"), "wb").write(cam)
    print("\n".join(report))
    print("ok: anm %d B, camara %d B -> %s" % (len(anm), len(cam), a.salida))


if __name__ == "__main__":
    main()
