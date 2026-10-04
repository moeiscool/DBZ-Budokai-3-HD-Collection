#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""importar.py - Asistente de importacion de personajes (lo usa el launcher).

Lee los juegos y colecciones que ya estan en disco (sin extraer nada) y crea el mod fuente
de un personaje nuevo (mods/<carpeta>/personaje.toml + modelos + moveset) con
roster_build.new_char; el montaje (_roster) se hace como siempre al pulsar JUGAR.

Fuentes:
  b1         Budokai 1 (ISO PS2): modelo + moveset + combos + gritos propios (b1port.py)
  b2         Budokai 2 (ISO PS2): modelos (#AMB [AMO, AMT]); moveset del donante
  b3         Budokai 3 / mods de la comunidad: .amb y parejas .amo/.amt en "modding resources"
             (y en la carpeta que se pase con --carpeta)
  iw         Infinite World (carpeta del juego PS2): modelos, voces y gritos de IW; si hay un
             port de la comunidad (moveset IW->B3), su moveset y sus capsulas
  sb1 / sb2  Shin Budokai / Another Road (ISO PSP): en desarrollo (formato PSP)
  sdbh       Super Dragon Ball Heroes World Mission (PC): en desarrollo (otro motor)

Modelos de un AFS de PS2: entradas #AMB cuyos dos primeros hijos son #AMO y #AMT; el
prefijo de los huesos (X16G_, XFRZ_...) da el personaje (catalog_b3.cat) y el donante.

Uso (salida en lineas TAB para el launcher):
  python importar.py fuentes
  python importar.py lista FUENTE [--carpeta DIR]
  python importar.py importar FUENTE CLAVE --mod CARPETA --nombre NOMBRE [--donante ID]
                     [--id ID] [--despues-de ID] [--carpeta DIR]
"""
import argparse
import glob
import json
import os
import re
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, "awo_tools")]

PS2 = os.path.join(ROOT, "ps2_games")
RESOURCES = os.path.join(ROOT, "modding resources")
PORTS = os.path.join(RESOURCES, "Infinite World to Budokai 3 Moveset Ports")
CACHE = os.path.join(HERE, "__pycache__", "importar_cache.json")
MAX_COSTUMES = 4

GAMES = [
    # id, nombre, estado por defecto
    ("b1", "Budokai 1", "listo"),
    ("b2", "Budokai 2", "listo"),
    ("b3", "Budokai 3 (mods de la comunidad)", "listo"),
    ("iw", "Infinite World", "listo"),
    ("sb1", "Shin Budokai", "desarrollo"),
    ("sb2", "Shin Budokai: Another Road", "desarrollo"),
    ("sdbh", "Super Dragon Ball Heroes: World Mission", "desarrollo"),
]
NOTES = {
    "b1": "Modelo, golpes, combos y gritos del Budokai 1 original.",
    "b2": "Modelo de Budokai 2; golpes del personaje donante.",
    "b3": "Modelos de la comunidad (.amb / .amo+.amt); golpes del donante.",
    "iw": "Modelo, voces y gritos de Infinite World; golpes del donante o del port de la comunidad.",
    "sb1": "Los modelos de PSP usan otro formato: el conversor aun no esta listo.",
    "sb2": "Los modelos de PSP usan otro formato: el conversor aun no esta listo.",
    "sdbh": "Juego de PC con otro motor: el conversor aun no esta listo.",
}

# Budokai 1: registro del ELF -> ID de B3 cuyo moveset sirve de base (agarre, modo hiper...)
B1_NAMES = ["Goku", "Kid Gohan", "Teen Gohan", "Vegeta", "Krillin", "Trunks", "Piccolo", "Tien",
            "Yamcha", "Raditz", "Nappa", "Ginyu", "Recoome", "Zarbon", "Dodoria", "Frieza",
            "Android 16", "Android 17", "Android 18", "Android 19", "Cell", "Hercule",
            "Saibaman", "Cell Jr.", "Great Saiyaman"]
B1_DONOR = [0, 2, 3, 7, 10, 8, 11, 12, 13, 18, 19, 20, 21, 38, 19, 27, 28, 29, 30, 32, 33, 14,
            42, 43, 5]


def str_list(v):
    return "[" + ", ".join('"%s"' % x for x in v) + "]"


def emit(*cols):
    print("\t".join(str(c).replace("\t", " ").replace("\n", " ") for c in cols))


# ---------------------------------------------------------------- utilidades
def find_iso(*patterns):
    for pat in patterns:
        hits = sorted(glob.glob(os.path.join(PS2, pat)))
        if hits:
            return hits[0]
    return None


def iw_dir():
    for d in sorted(glob.glob(os.path.join(PS2, "*Infinite World*"))):
        if os.path.isdir(d):
            return d
    return None


def sdbh_dir():
    hits = glob.glob(os.path.join(RESOURCES, "Super Dragon Ball Heroes*"))
    return hits[0] if hits else None


def source_path(game):
    if game == "b1":
        return find_iso("*Budokai (Europe)*.iso", "*Budokai (USA)*.iso")
    if game == "b2":
        return find_iso("*Budokai 2*.iso")
    if game == "b3":
        return RESOURCES if os.path.isdir(RESOURCES) else None
    if game == "iw":
        return iw_dir()
    if game == "sb1":
        return find_iso("*Shin Budokai (*.iso")
    if game == "sb2":
        return find_iso("*Another Road*.iso")
    if game == "sdbh":
        return sdbh_dir()
    return None


def catalog():
    """prefijo de huesos -> nombre (catalog_b3.cat) e ID de B3 que lo usa."""
    names = {}
    with open(os.path.join(HERE, "catalog_b3.cat"), encoding="utf-8") as fh:
        for ln in fh:
            if ln.startswith("#") or "|" not in ln:
                continue
            b, nm, lab, var, j = ln.rstrip("\n").split("|")[:5]
            names.setdefault(lab.split("_")[0], (nm, int(b)))
    import roster_build  # noqa: PLC0415
    by_fid = {}
    for e in roster_build.DB["ids"]:
        for m in e.get("models") or []:
            if m < 0xFFFFFFFF:
                by_fid.setdefault(m, e["id"])
    return {p: (nm, by_fid.get(b)) for p, (nm, b) in names.items()}


EXTRA_NAMES = {  # personajes que B3 no tiene (prefijos de B2 / IW)
    "XBAB": "Babidi", "XGKG": "Goku GT", "XGKT": "Goku GT", "XVGB": "Baby Vegeta",
    "XS17": "Super 17", "XJNB": "Janemba", "XPKN": "Pikkon", "XPAN": "Pan",
    "XGVT": "Vegeta GT", "XGS2": "Great Saiyaman 2", "XBBR": "Broly Super",
    "XGTA": "Gogeta", "XVTO": "Vegito", "XGXL": "Gotenks (adulto)", "XGXG": "Gotenks fantasma",
    "XKBT": "Kibito", "XKOK": "Kibito Kai", "BCDBR": "Dabura (alternativo)", "SNR": "Shenron",
}
EXTRA_DONORS = {"XRCM": ("Recoome", 21), "XSBM": ("Saibaman", 42), "TSH": ("Tenshinhan", 12)}


def cache_load():
    try:
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def cache_save(c):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(c, fh)


class AfsFile:
    """AFS de PS2 leido en su sitio (fichero suelto o dentro de una ISO)."""

    def __init__(self, path, inner=None):
        self.key = "%s|%s" % (path, inner or "")
        if inner:
            import iso  # noqa: PLC0415
            self.f = iso.Iso(path).open(inner)
        else:
            self.f = open(path, "rb")
        st = os.stat(path)
        self.stamp = "%d-%d" % (st.st_size, int(st.st_mtime))
        self.f.seek(4)
        n = struct.unpack("<I", self.f.read(4))[0]
        self.tab = struct.unpack("<%dI" % (2 * n), self.f.read(8 * n))
        self.n = n

    def entry(self, i):
        self.f.seek(self.tab[2 * i])
        return self.f.read(self.tab[2 * i + 1])

    def head(self, i, size=0x60):
        self.f.seek(self.tab[2 * i])
        return self.f.read(size)


BONE_RE = re.compile(rb"([A-Z0-9]{2,5})_(?:WAIST|HIPS|BODY|HEAD)")


def model_prefix(d):
    m = BONE_RE.search(d)
    return m.group(1).decode() if m else None


def scan_models(afs):
    """[(fid, prefijo)] de los modelos (#AMB [AMO, AMT]) de un AFS, con cache en disco."""
    c = cache_load()
    hit = c.get(afs.key)
    if hit and hit.get("stamp") == afs.stamp:
        return [tuple(x) for x in hit["models"]]
    out = []
    for i in range(afs.n):
        s = afs.tab[2 * i + 1]
        if s < 60000 or s > 4000000:
            continue
        h = afs.head(i)
        if h[:4] != b"#AMB" or struct.unpack_from("<I", h, 0x10)[0] < 2:
            continue
        o0 = struct.unpack_from("<I", h, 0x20)[0]
        o1 = struct.unpack_from("<I", h, 0x30)[0]
        if o0 + 4 > s or o1 + 4 > s:
            continue
        afs.f.seek(afs.tab[2 * i] + o0)
        t0 = afs.f.read(4)
        afs.f.seek(afs.tab[2 * i] + o1)
        t1 = afs.f.read(4)
        if (t0, t1) != (b"#AMO", b"#AMT"):
            continue
        afs.f.seek(afs.tab[2 * i] + o0)
        p = model_prefix(afs.f.read(o1 - o0))
        if p:
            out.append((i, p))
    c[afs.key] = {"stamp": afs.stamp, "models": out}
    cache_save(c)
    return out


def group_by_character(models):
    """Modelos con el mismo prefijo de huesos = un personaje (sus trajes)."""
    cat = catalog()
    groups = {}
    for fid, p in models:
        groups.setdefault(p, []).append(fid)
    out = []
    for p, fids in groups.items():
        nm, donor = cat.get(p) or EXTRA_DONORS.get(p) or (EXTRA_NAMES.get(p), None)
        out.append({"clave": p, "nombre": nm or "Modelo %s" % p, "modelos": fids, "donante": donor})
    # mismo nombre (Gohan adulto / joven...): se distinguen por el personaje de B3 que lo usa
    import roster_build  # noqa: PLC0415
    b3 = {e["id"]: e["name"].title() for e in roster_build.DB["ids"]}
    seen = {}
    for e in out:
        seen.setdefault(e["nombre"].lower(), []).append(e)
    for same in seen.values():
        if len(same) > 1:
            for e in same:
                e["nombre"] += " (%s)" % (b3.get(e["donante"]) if e["donante"] is not None else e["clave"])
    out.sort(key=lambda e: e["nombre"].lower())
    return out


def amb_pair(amo, amt):
    """#AMB PS2 de un modelo a partir de su AMO y su AMT (como los de Budokai 1)."""
    import b1port  # noqa: PLC0415
    return b1port.amb_build([(amo, 1), (amt, 2)])


# ---------------------------------------------------------------- colecciones (b3)
IW_MODELS = os.path.join(RESOURCES, "All Character Models from IW into AMB format")


def community_files(roots):
    out = {}
    for d in roots:
        for dp, _, files in os.walk(d):
            for fn in files:
                low = fn.lower()
                if low.endswith(".amb") or low.endswith(".amo"):
                    out[os.path.join(dp, fn)] = fn
    return out


SKIP = re.compile(r"scouter|hair\.amb|forearms|\[npc\]|\[cutscene|\[select|\[overworld|question mark|"
                  r"shenron \[|bubbles|giru", re.I)


def donor_by_name(name):
    """ID de B3 cuyo nombre (catalogo) aparece en el del modelo (el mas largo gana)."""
    low = name.lower()
    ids = {}
    for nm, did in catalog().values():
        if did is not None and nm:
            ids[nm.lower()] = min(did, ids.get(nm.lower(), did))
    for alias, did in (("hercule", 14), ("frieza", 27), ("tien", 12), ("captain ginyu", 20),
                       ("kid gohan", 2), ("teen gohan", 3), ("adult gohan", 4), ("kid trunks", 9),
                       ("future trunks", 8), ("majin buu", 34), ("kid buu", 36), ("super buu", 35)):
        ids[alias] = did
    hits = [n for n in ids if n in low]
    return ids[max(hits, key=len)] if hits else None


def community_list(roots):
    """Un personaje por modelo base: 'Goku (GT) (Default).amb' con sus formas
    'Goku (GT) (Default) - SSJ.amb'... (la misma pieza en .amb y .amo cuenta una vez)."""
    groups = {}
    for path, fn in sorted(community_files(roots).items()):
        if SKIP.search(fn):
            continue
        if fn.lower().endswith(".amo") and not os.path.exists(os.path.splitext(path)[0] + ".amt"):
            continue
        stem = re.sub(r"^\d+[a-z]?\.\s*", "", os.path.splitext(fn)[0]).strip()
        parts = stem.split(" - ")    # 'Goku (EoZ) - (Halo) - SSJ': variante (Halo), forma SSJ
        if len(parts) > 1 and not parts[-1].startswith("("):
            base, form = " - ".join(parts[:-1]), parts[-1]
        else:
            base, form = stem, ""
        g = groups.setdefault(base.lower(), {"nombre": base.replace(" - ", " "), "formas": {}})
        g["formas"].setdefault(form.lower(), path)        # duplicados .amb/.amo: el primero
    out = []
    for k, g in sorted(groups.items()):
        files = [g["formas"][f] for f in sorted(g["formas"], key=lambda f: (f != "", ))]
        nm = re.sub(r"\s*\((default|default armour)\)", "", g["nombre"], flags=re.I).strip()
        out.append({"clave": "c:" + k, "nombre": nm, "ficheros": files, "donante": donor_by_name(nm)})
    return out


def community_model(path):
    if path.lower().endswith(".amo"):
        return amb_pair(open(path, "rb").read(), open(os.path.splitext(path)[0] + ".amt", "rb").read())
    return open(path, "rb").read()


# ---------------------------------------------------------------- fuentes
def b1_list():
    import b1port  # noqa: PLC0415
    b1 = b1port.B1(source_path("b1"))
    out = []
    for i, nm in enumerate(B1_NAMES):
        r = b1.record(i)
        ms = [m for m in dict.fromkeys(r["models"]) if m > 0]
        out.append({"clave": str(i), "nombre": nm, "modelos": ms, "donante": B1_DONOR[i]})
    return out


def iw_ports():
    """Ports IW -> B3 de la comunidad: {nombre en minusculas: carpeta B3}."""
    out = {}
    for d in sorted(glob.glob(os.path.join(PORTS, "*"))):
        b3 = os.path.join(d, "B3")
        if os.path.isdir(b3):
            out[os.path.basename(d).lower()] = b3
    return out


def port_for(name, ports=None):
    ports = iw_ports() if ports is None else ports
    norm = re.sub(r"[^a-z0-9]", "", re.sub(r"\(alt colou?r pallete\)", "", name.lower()))
    return next((p for k, p in ports.items() if norm == re.sub(r"[^a-z0-9]", "", k)), None)


def list_source(game, extra=None):
    if game == "b1":
        return b1_list()
    if game == "b2":
        return group_by_character(scan_models(AfsFile(source_path("b2"), "/USR/DATA_CMN.AFS")))
    if game == "iw":
        if os.path.isdir(IW_MODELS):      # la coleccion de modelos de IW ya trae los nombres
            lst = community_list([IW_MODELS])
        else:
            lst = group_by_character(scan_models(AfsFile(os.path.join(source_path("iw"), "USR", "DATA_CMN.AFS"))))
        ports = iw_ports()
        for e in lst:
            e["port"] = port_for(e["nombre"], ports)
        return lst
    if game == "b3":
        return community_list([d for d in (RESOURCES, extra) if d and os.path.isdir(d)])
    raise ValueError("fuente en desarrollo: %s" % game)


def suggested_name(game, e):
    """El de B3 ya existe: 'Vegeta B1' para distinguirlos en la rueda."""
    if game in ("b1", "b2") and e.get("donante") is not None:
        same = e["donante"] == B1_DONOR[int(e["clave"])] and int(e["clave"]) not in B1_OWN if game == "b1"             else True
        if same:
            return "%s %s" % (e["nombre"], game.upper())
    if e.get("ficheros"):        # 'Goku (GT) (ALT Colour Pallete)' -> 'Goku GT'
        short = re.sub(r"\s*\((?:alt colou?r pall?ete|default|recolou?r)\)", "", e["nombre"], flags=re.I)
        return re.sub(r"[()]", "", short).strip()
    return e["nombre"]


B1_OWN = (13, 14, 19)          # Zarbon, Dodoria y Androide 19 no estan en B3


def note_for(game, e):
    if game == "b1":
        return "%d modelos; golpes, combos y gritos de B1" % len(e["modelos"])
    if e.get("ficheros"):
        n = min(len(e["ficheros"]), 6)
        extra = "; moveset del port de la comunidad" if e.get("port") else ""
        return ("1 traje" if n == 1 else "1 traje, %d formas" % n) + extra
    n = min(len(e["modelos"]), MAX_COSTUMES)
    extra = "; moveset del port de la comunidad" if e.get("port") else ""
    return "%d trajes%s" % (n, extra)


# ---------------------------------------------------------------- importar
def port_files(b3dir):
    """Ficheros de un port IW->B3 de la comunidad (unnamed_<fid>.bin, fids del personaje que
    sustituia) -> (ID donante, {'anm': [...], 'cam': path, 'bsp': path})."""
    import roster_build  # noqa: PLC0415
    bins = {}
    for fn in os.listdir(b3dir):
        m = re.match(r"(?:unnamed_)?(\d+)\.bin$", fn, re.I)
        if m:
            bins[int(m.group(1))] = os.path.join(b3dir, fn)
    for e in roster_build.DB["ids"]:
        anm = [a for a in (e.get("anm") or []) if a < 0xFFFFFFFF and a]
        if anm and anm[0] in bins:
            return e["id"], {"anm": [bins[a] for a in anm if a in bins], "cam": bins.get(e.get("cam")),
                             "bsp": bins.get(e.get("bsp"))}
    return None, {}


def iw_voice_name(nombre):
    import voces  # noqa: PLC0415
    try:
        iw = voces.IwVoices(source_path("iw"))
    except Exception:  # noqa: BLE001
        return None
    key = re.sub(r"[^a-z0-9]", "", nombre.lower())
    alias = {"janemba": "janenba", "pikkon": "paikuhan", "gokugt": "gtgokou", "vegetagt": "gtvegeta",
             "babyvegeta": "vegetababy", "super17": "superandroidno17", "greatsaiyaman2": "greatsaiyaman2"}
    key = alias.get(key, key)
    for nm in iw.names:
        if re.sub(r"[^a-z0-9]", "", nm.lower()) == key:
            return nm
    return None


def do_import(a):
    import roster_build as rb  # noqa: PLC0415
    game = a.fuente
    work = tempfile.mkdtemp(prefix="importar_")
    lst = list_source(game, a.carpeta)
    e = next((x for x in lst if x["clave"] == a.clave), None)
    if e is None:
        raise SystemExit("ERROR: no encuentro %r en %s" % (a.clave, game))
    donor = a.donante if a.donante is not None else (e.get("donante") if e.get("donante") is not None else 21)
    models, keys, port = [], {}, None
    forms = 1
    if game == "b1":
        import b1port  # noqa: PLC0415
        b1 = b1port.B1(source_path("b1"))
        for m in e["modelos"][:MAX_COSTUMES]:
            p = os.path.join(work, "traje%d.amb" % (len(models) + 1))
            open(p, "wb").write(amb_pair(b1.entry(m), b1.entry(m + 1)))
            models.append(p)
    elif e.get("ficheros"):            # colecciones: modelo base y sus formas (un traje)
        for f in e["ficheros"][:6]:
            p = os.path.join(work, "traje%d.amb" % (len(models) + 1))
            open(p, "wb").write(community_model(f))
            models.append(p)
        forms = len(models)
        port = e.get("port") or port_for(e["nombre"])
    else:                             # modelos de un AFS: un traje cada uno
        afs = (AfsFile(source_path("b2"), "/USR/DATA_CMN.AFS") if game == "b2"
               else AfsFile(os.path.join(source_path("iw"), "USR", "DATA_CMN.AFS")))
        for m in e["modelos"][:MAX_COSTUMES]:
            p = os.path.join(work, "traje%d.amb" % (len(models) + 1))
            open(p, "wb").write(afs.entry(m))
            models.append(p)
        port = e.get("port")
    rb.log("importando %s de %s: %d modelos, donante %d" % (e["nombre"], dict((g, n) for g, n, s in GAMES)[game],
                                                         len(models), donor))
    if port:
        pd, files = port_files(port)
        if pd is not None and files.get("anm"):
            donor = pd
            rb.log("port de la comunidad: moveset de %s (sustituia al ID %d)" % (os.path.dirname(port), pd))
    if game == "b1":                  # golpes, combos y gritos de B1 sobre el moveset del donante
        import afs_pair  # noqa: PLC0415
        import ps2hd  # noqa: PLC0415
        dn = next(x for x in rb.DB["ids"] if x["id"] == donor)
        rep = []
        anm, cam = b1port.port(b1, int(e["clave"]), afs_pair.ps2(dn["anm"][0]), afs_pair.ps2(dn["cam"]), rep,
                               models, [0x64], b1port.donor_model(dn["anm"][0]))
        for ln in rep:
            rb.log("   " + ln)
        # con transformacion (P+K+G) los modelos van de dos en dos: traje 1 normal, traje 1 forma 2...
        if any(ln.startswith("transformacion:") for ln in rep) and len(models) >= 2 and len(models) % 2 == 0:
            forms = 2
        b1_anm, b1_cam = bytes(ps2hd.convert_block(anm)), bytes(ps2hd.convert_block(cam))
    ns = argparse.Namespace(mods=a.mods, us=a.us, mod=a.mod, nombre=a.nombre, donante=donor, id=a.id,
                            modelo=models, cara=None, icono=None, retrato=None, retrato_p1=None,
                            retrato_p2=None, captura=None, despues_de=a.despues_de, por_traje=forms)
    rb.new_char(ns)
    d = os.path.join(a.mods or rb.default_mods(), a.mod)
    toml = os.path.join(d, "personaje.toml")
    os.makedirs(os.path.join(d, "moveset"), exist_ok=True)
    if game == "b1":
        open(os.path.join(d, "moveset", "anm.bin"), "wb").write(b1_anm)
        open(os.path.join(d, "moveset", "camara.bin"), "wb").write(b1_cam)
        keys.update({"moveset": str_list(["moveset/anm.bin"] * forms), "camara": '"moveset/camara.bin"',
                     "gritos": '"b1:%s"' % e["clave"], "voces": '"ninguna"'})
        if forms > 1:
            keys["formas"] = str(forms)
    elif port and files.get("anm"):
        import shutil  # noqa: PLC0415
        rel = []
        for k, f in enumerate(files["anm"]):
            r = "moveset/anm_forma%d.bin" % (k + 1)
            shutil.copyfile(f, os.path.join(d, r))
            rel.append(r)
        keys["moveset"] = str_list(rel)
        if files.get("cam"):
            shutil.copyfile(files["cam"], os.path.join(d, "moveset", "camara.bin"))
            keys["camara"] = '"moveset/camara.bin"'
        if files.get("bsp"):
            shutil.copyfile(files["bsp"], os.path.join(d, "moveset", "tecnicas.bin"))
            keys["tecnicas"] = '"moveset/tecnicas.bin"'
    if game in ("iw", "b3"):
        vn = iw_voice_name(e["nombre"]) if source_path("iw") else None
        if vn:
            keys["voces"] = '"iw:%s"' % vn
            rb.log("voces y gritos de Infinite World: %s" % vn)
    if keys:
        rb.set_toml_keys(toml, keys)
    if keys.get("camara"):     # capsulas propias desde su moveset (B1 / IW)
        try:
            cap_args = argparse.Namespace(importar="b1" if game == "b1" else "auto", lista=None, catalogo=None)
            with open(toml, "rb") as fh:
                c = rb.tomllib.load(fh).get("personaje", {})
            caps = rb.import_caps(cap_args, toml, c, d)
            if caps:
                rb.write_caps(toml, caps)
                rb.log("capsulas propias: %d (renombralas en el editor si quieres)" % len(caps))
        except Exception as ex:  # noqa: BLE001
            rb.log("aviso: capsulas sin importar (%s)" % ex)
    rb.log("listo: %s (se monta al pulsar JUGAR o Reconstruir ahora)" % a.mod)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fuentes")
    p = sub.add_parser("lista")
    p.add_argument("fuente")
    p.add_argument("--carpeta")
    i = sub.add_parser("importar")
    i.add_argument("fuente")
    i.add_argument("clave")
    i.add_argument("--mod", required=True)
    i.add_argument("--nombre", required=True)
    i.add_argument("--donante", type=int)
    i.add_argument("--id", type=int)
    i.add_argument("--despues-de", type=int)
    i.add_argument("--carpeta")
    i.add_argument("--mods")
    i.add_argument("--us")
    a = ap.parse_args()
    if a.cmd == "fuentes":
        for g, nm, st in GAMES:
            path = source_path(g)
            emit("fuente", g, nm, st if path else "falta", path or "", NOTES[g])
        return 0
    if a.cmd == "lista":
        for e in list_source(a.fuente, a.carpeta):
            # clave, nombre, donante, clase (b1 | trajes | formas), cuantos, port, nombre sugerido
            if a.fuente == "b1":
                kind, n = "b1", len(e["modelos"])
            elif e.get("ficheros"):
                kind, n = "formas", min(len(e["ficheros"]), 6)
            else:
                kind, n = "trajes", min(len(e["modelos"]), MAX_COSTUMES)
            emit("personaje", e["clave"], e["nombre"], "" if e.get("donante") is None else e["donante"],
                 kind, n, 1 if e.get("port") else 0, suggested_name(a.fuente, e))
        return 0
    return do_import(a)


if __name__ == "__main__":
    sys.exit(main())
