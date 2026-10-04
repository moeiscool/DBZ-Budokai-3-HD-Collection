#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iso.py - Lectura directa de imagenes ISO 9660 (PS2 y PSP), sin extraerlas.

Sirve para que el importador trabaje con la ISO tal cual la tiene el jugador:

    iso = Iso("DragonBall Z - Budokai (Europe).iso")
    iso.files()                     -> {"/SLES_515.05": (lba, tamano), ...}
    iso.read("/USR/DATA_CMN.AFS", offset, n)
    iso.open("/USR/DATA_CMN.AFS")   -> objeto tipo fichero (seek/read) para el lector de AFS

`python iso.py <iso>` lista su contenido.
"""
import io
import os
import struct
import sys

SECTOR = 2048


class Iso:
    def __init__(self, path):
        self.path = path
        self._f = open(path, "rb")
        pvd = self._sector(16)
        if pvd[1:6] != b"CD001":
            raise ValueError("no es una imagen ISO 9660: %s" % path)
        self.label = pvd[40:72].decode("ascii", "replace").strip()
        root = pvd[156:156 + 34]
        self._files = {}
        self._walk(struct.unpack_from("<I", root, 2)[0], struct.unpack_from("<I", root, 10)[0], "")

    def _sector(self, lba, n=1):
        self._f.seek(lba * SECTOR)
        return self._f.read(n * SECTOR)

    def _walk(self, lba, size, prefix, depth=0):
        if depth > 16:
            return
        data = self._sector(lba, (size + SECTOR - 1) // SECTOR)
        o = 0
        while o < len(data):
            ln = data[o]
            if ln == 0:              # resto del sector vacio
                o = (o // SECTOR + 1) * SECTOR
                continue
            rec = data[o:o + ln]
            o += ln
            elba, esize = struct.unpack_from("<I", rec, 2)[0], struct.unpack_from("<I", rec, 10)[0]
            flags, nlen = rec[25], rec[32]
            name = rec[33:33 + nlen]
            if name in (b"\x00", b"\x01"):
                continue
            name = name.decode("ascii", "replace").split(";")[0]
            full = prefix + "/" + name
            if flags & 2:
                self._walk(elba, esize, full, depth + 1)
            else:
                self._files[full] = (elba, esize)

    def files(self):
        return dict(self._files)

    def find(self, name):
        """Ruta de un fichero sin distinguir mayusculas; `name` puede ser solo el nombre."""
        low = name.lower().lstrip("/")
        for p in self._files:
            if p.lower().lstrip("/") == low or p.lower().rsplit("/", 1)[-1] == low:
                return p
        return None

    def read(self, path, offset=0, n=None):
        lba, size = self._files[path]
        n = size - offset if n is None else min(n, size - offset)
        self._f.seek(lba * SECTOR + offset)
        return self._f.read(max(0, n))

    def open(self, path):
        return _Sub(self.path, *self._files[path])


class _Sub(io.RawIOBase):
    """Fichero dentro de la ISO como objeto de solo lectura (seek/read/tell)."""

    def __init__(self, path, lba, size):
        self._f = open(path, "rb")
        self._base, self._size, self._pos = lba * SECTOR, size, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def seek(self, off, whence=0):
        self._pos = off if whence == 0 else (self._pos + off if whence == 1 else self._size + off)
        return self._pos

    def tell(self):
        return self._pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self._size - self._pos
        n = max(0, min(n, self._size - self._pos))
        self._f.seek(self._base + self._pos)
        b = self._f.read(n)
        self._pos += len(b)
        return b

    def close(self):
        self._f.close()
        super().close()


if __name__ == "__main__":
    iso = Iso(sys.argv[1])
    print(iso.label)
    for p, (lba, size) in sorted(iso.files().items()):
        print("%12d  %s" % (size, p))
