#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xenos_vm.py - Interprete minimo (vectorizado, numpy) de ucode de vertex shader Xenos.

Ejecuta el DESENSAMBLADO TEXTO que escribe el runtime con `dump_shaders="<dir>"`
(ficheros `shader_<hash>.ucode.vert`) sobre un VB de 44 B/vertice y una paleta de
huesos (48 B/entrada) capturados, y devuelve `oPos`.  Cubre solo el subconjunto de
ops de los VS de B3 HD (rigidos y de skinning por paleta).  Verificado (2026-10-03):
reproduce el skinning real de la GPU (malla coherente, aristas intra-hueso ratio
1.0000) y `palette[slot]` a weight=1 == matriz de pose del hueso (error 0.00000).

API:
    vm = run_skin("DA9A3E04256563FF", vb_bytes, palette_bytes, consts, shader_dir)
    pos = vm.out[("oPos", 0)][:, :3]        # con c0..c3 = I y c8..c11 = I => marco 'objeto'
    consts: {indice_constante: [x, y, z, w]};  c255 = [1, 0, -1, 0.5] (1/0/-1 literales
    del shader; solo importan x,y,z).  Para ver la proyeccion real, pasar c0..c3 reales.

Convenciones: VB big-endian tal cual la memoria del guest; `FMT_8_8_8_8` con endian
8in32 => componente x = ULTIMO byte de la palabra BE (el byte bajo de `bone`).
"""
import os
import re

import numpy as np

SW = {'x': 0, 'y': 1, 'z': 2, 'w': 3}


SCALAR_OPS = {'rcp','sgts','adds','subsc','maxs','muls','sqrt','rsq','addsc','setp_ge','mulsc','mulsc_sat','adds_prev','muls_prev'}


class Slot:
    def __init__(self):
        self.vec = None   # (pred, op, dst, srcs)
        self.sca = None
        self.fetch = None


def parse_src(tok):
    tok = tok.strip()
    m = re.match(r'(-)?(?:(r|c)_abs\[(\d+)\]|(r|c)(\d+))(?:\.(\w+))?$', tok)
    if not m:
        raise ValueError('bad src %r' % tok)
    neg = bool(m.group(1))
    if m.group(2):
        kind, idx, ab = m.group(2), int(m.group(3)), True
    else:
        kind, idx, ab = m.group(4), int(m.group(5)), False
    sw = [SW[c] for c in (m.group(6) or 'xyzw')]
    return (neg, kind, idx, ab, sw)


def parse_dst(tok):
    tok = tok.strip()
    m = re.match(r'(r|o|oPos)(\d*)(?:\.(\w+))?$', tok)
    if not m:
        raise ValueError('bad dst %r' % tok)
    kind = m.group(1)
    idx = int(m.group(2)) if m.group(2) else 0
    mask = m.group(3) or 'xyzw'
    lanes = [(i, 'xyzw'.index(c) if c in 'xyzw' else None) for i, c in enumerate(mask)]
    return kind, idx, mask


def split_args(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '[':
            depth += 1
        if ch == ']':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip())
            cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def parse(text):
    slots = []
    cur = None
    for raw in text.split('\n'):
        l = raw.rstrip()
        if not l.strip():
            continue
        s = l.strip()
        m0 = re.match(r'/\*\s*([\d.]+)\s*\*/\s*(.*)$', s)
        body = None
        is_new = False
        if m0:
            body = m0.group(2)
            # exec / alloc markers have fractional numbering like 0.0 and no real op
            if re.match(r'^\d+\.\d+$', m0.group(1)):
                continue
            is_new = True
        else:
            body = s
        if body.startswith('+'):
            body = body[1:].strip()
            kind = 'sca'
        else:
            kind = 'vec'
        body = body.strip()
        if body in ('exec', 'exece', 'cnop', 'serialize') or body.startswith('alloc') or body.startswith('(!p0) exec') or body.startswith('(p0) exec') or body.startswith('exec'):
            continue
        pred = None
        mp = re.match(r'\((!?)p0\)\s*(.*)$', body)
        if mp:
            pred = 'not' if mp.group(1) else 'p0'
            body = mp.group(2)
        # strip trailing comments
        body = re.sub(r'//.*$', '', body).strip()
        if not body:
            continue
        parts = body.split(None, 1)
        op = parts[0]
        args = split_args(parts[1]) if len(parts) > 1 else []
        if op.startswith('vfetch'):
            sl = Slot(); sl.fetch = (op, args); slots.append(sl); cur = None
            continue
        if kind == 'vec' and is_new:
            cur = Slot(); slots.append(cur)
            cur.vec = (pred, op, args)
        elif kind == 'vec':
            cur = Slot(); slots.append(cur)
            cur.vec = (pred, op, args)
        else:
            if cur is None:
                cur = Slot(); slots.append(cur)
            cur.sca = (pred, op, args)
    return slots


class VM:
    def __init__(self, N, consts):
        self.N = N
        self.R = np.zeros((32, N, 4))
        self.consts = consts  # dict idx -> 4-vector
        self.p0 = np.zeros(N, bool)
        self.ps = np.zeros(N)
        self.out = {}

    def rd(self, src, nlanes=4):
        neg, kind, idx, ab, sw = src
        if kind == 'r':
            v = self.R[idx]
        else:
            v = np.broadcast_to(np.asarray(self.consts.get(idx, [0, 0, 0, 0]), float), (self.N, 4))
        if ab:
            v = np.abs(v)
        if len(sw) == 1:
            sw = sw * 4
        v = v[:, sw] if len(sw) else v
        if neg:
            v = -v
        return v

    def wr(self, dst, val, pmask):
        kind, idx, mask = dst
        if kind == 'r':
            tgt = self.R[idx]
        else:
            key = (kind, idx)
            if key not in self.out:
                self.out[key] = np.zeros((self.N, 4))
            tgt = self.out[key]
        val = np.asarray(val, float)
        if val.ndim == 1:
            val = np.repeat(val[:, None], 4, axis=1)
        for lane, c in enumerate(mask):
            if c == '_':
                continue
            lane_idx = 'xyzw'.index(c) if c in 'xyzw' else lane
            tgt[:, lane_idx] = np.where(pmask, val[:, lane], tgt[:, lane_idx])

    def pm(self, pred):
        if pred is None:
            return np.ones(self.N, bool)
        return self.p0 if pred == 'p0' else ~self.p0

    def run(self, slots, fetch_cb):
        for sl in slots:
            if sl.fetch:
                fetch_cb(self, *sl.fetch)
                continue
            writes = []
            newps = None
            newp0 = None
            if sl.vec and sl.vec[1] in SCALAR_OPS:
                # scalar op issued in the vector column: treat as the slot's scalar op
                if sl.sca is None:
                    sl.sca = sl.vec
                    sl.vec = None
            if sl.vec:
                pred, op, args = sl.vec
                pm = self.pm(pred)
                res = self.vec_op(op, args, pm)
                if res is not None:
                    writes.append((parse_dst(args[0]), res[0], pm))
                    if len(res) > 1 and res[1] is not None:
                        newp0 = (res[1], pm)
            if sl.sca:
                pred, op, args = sl.sca
                pm = self.pm(pred)
                r = self.sca_op(op, args)
                if r is not None:
                    val, p0v = r
                    if args and not args[0].startswith('r0._') or True:
                        pass
                    dst = parse_dst(args[0])
                    newps = (val, pm)
                    if dst[2].replace('_', ''):  # has written lanes
                        writes.append((dst, val, pm))
                    if p0v is not None:
                        newp0 = (p0v, pm)
            for dst, val, pm in writes:
                self.wr(dst, val, pm)
            if newps is not None:
                val, pm = newps
                self.ps = np.where(pm, val, self.ps)
            if newp0 is not None:
                v, pm = newp0
                self.p0 = np.where(pm, v, self.p0)

    # ---- vector ----
    def vec_op(self, op, args, pm):
        S = [parse_src(a) for a in args[1:]]
        rd = self.rd
        if op == 'mul':
            return (rd(S[0]) * rd(S[1]),)
        if op == 'add':
            return (rd(S[0]) + rd(S[1]),)
        if op == 'mad':
            return (rd(S[0]) * rd(S[1]) + rd(S[2]),)
        if op == 'max':
            return (np.maximum(rd(S[0]), rd(S[1])),)
        if op == 'min':
            return (np.minimum(rd(S[0]), rd(S[1])),)
        if op == 'dp3':
            a, b = rd(S[0]), rd(S[1])
            return (np.repeat((a[:, :3] * b[:, :3]).sum(1)[:, None], 4, 1),)
        if op == 'dp4':
            a, b = rd(S[0]), rd(S[1])
            return (np.repeat((a * b).sum(1)[:, None], 4, 1),)
        if op == 'dp2add':
            a, b, c = rd(S[0]), rd(S[1]), rd(S[2])
            return (np.repeat((a[:, 0] * b[:, 0] + a[:, 1] * b[:, 1] + c[:, 0])[:, None], 4, 1),)
        if op == 'max4':
            a = rd(S[0])
            return (np.repeat(a.max(1)[:, None], 4, 1),)
        if op == 'sne':
            return ((rd(S[0]) != rd(S[1])).astype(float),)
        if op == 'cndge':
            a, b, c = rd(S[0]), rd(S[1]), rd(S[2])
            return (np.where(a >= 0, b, c),)
        if op == 'setp_ne_push':
            a, b = rd(S[0]), rd(S[1])
            p = (a[:, 3] == 0) & (b[:, 3] != 0)
            r = np.where((a[:, 0] == 0) & (b[:, 0] != 0), 0.0, a[:, 0] + 1.0)
            return (np.repeat(r[:, None], 4, 1), p)
        if op == 'setp_gt_push':
            a, b = rd(S[0]), rd(S[1])
            p = (a[:, 3] == 0) & (b[:, 3] > 0)
            r = np.where((a[:, 0] == 0) & (b[:, 0] > 0), 0.0, a[:, 0] + 1.0)
            return (np.repeat(r[:, None], 4, 1), p)
        if op == 'setp_pop':
            a = rd(S[0])
            p = (a[:, 3] - 1.0) <= 0
            r = np.where((a[:, 0] - 1.0) <= 0, 0.0, a[:, 0] - 1.0)
            return (np.repeat(r[:, None], 4, 1), p)
        if op in ('rcp', 'sgts', 'adds', 'subsc', 'maxs', 'muls', 'sqrt', 'rsq', 'addsc'):
            # scalar op issued in the vector slot
            r = self.sca_op(op, args)
            return (np.repeat(r[0][:, None], 4, 1), r[1])
        raise NotImplementedError(op)

    # ---- scalar ----
    def sca_op(self, op, args):
        S = [parse_src(a) for a in args[1:]]
        rd = self.rd

        def two(src):
            v = rd(src)
            return v[:, 0], v[:, 1] if v.shape[1] > 1 else v[:, 0]
        p0v = None
        if op == 'maxs':
            a, b = two(S[0]); r = np.maximum(a, b)
        elif op == 'adds':
            a, b = two(S[0]); r = a + b
        elif op == 'muls':
            a, b = two(S[0]); r = a * b
        elif op == 'adds_prev':
            a = rd(S[0])[:, 0]; r = a + self.ps
        elif op == 'muls_prev':
            a = rd(S[0])[:, 0]; r = a * self.ps
        elif op == 'subsc':
            a = rd(S[0])[:, 0]; b = rd(S[1])[:, 0]; r = a - b
        elif op == 'addsc':
            a = rd(S[0])[:, 0]; b = rd(S[1])[:, 0]; r = a + b
        elif op == 'mulsc':
            a = rd(S[0])[:, 0]; b = rd(S[1])[:, 0]; r = a * b
        elif op == 'mulsc_sat':
            a = rd(S[0])[:, 0]; b = rd(S[1])[:, 0]; r = np.clip(a * b, 0, 1)
        elif op == 'sqrt':
            a = rd(S[0])[:, 0]; r = np.sqrt(np.maximum(a, 0))
        elif op == 'rcp':
            a = rd(S[0])[:, 0]
            with np.errstate(divide='ignore', invalid='ignore'):
                r = np.where(a == 0, np.inf, 1.0 / a)
        elif op == 'rsq':
            a = rd(S[0])[:, 0]
            with np.errstate(divide='ignore', invalid='ignore'):
                r = np.where(a <= 0, np.inf, 1.0 / np.sqrt(np.abs(a)))
        elif op == 'sgts':
            a = rd(S[0])[:, 0]; r = (a > 0).astype(float)
        elif op == 'setp_ge':
            a = rd(S[0])[:, 0]; r = (a >= 0).astype(float); p0v = a >= 0
        else:
            raise NotImplementedError(op)
        return r, p0v




def load_shader(hash16, shader_dir):
    return parse(open(os.path.join(shader_dir, 'shader_%s.ucode.vert' % hash16)).read())


FMT_N = {'FMT_32_32_32_32_FLOAT': 4, 'FMT_32_32_32_FLOAT': 3, 'FMT_32_32_FLOAT': 2, 'FMT_32_FLOAT': 1,
         'FMT_8_8_8_8': 4}


def make_fetch_cb(streams):
    """streams: {0: (bytes, stride_bytes), 1: (bytes, stride_bytes)}"""
    state = {'stream': 0, 'idx': None, 'stride': 11}

    def cb(vm, op, args):
        kv = {}
        pos = [a for a in args if '=' not in a]
        for a in args:
            if '=' in a:
                k, v = a.split('=', 1)
                kv[k] = v
        dst = pos[0]
        if op == 'vfetch_full':
            idx_src = pos[1]
            stream = int(pos[2][2:])
            idx = vm.rd(parse_src(idx_src))[:, 0].astype(np.int64)
            state['stream'] = stream
            state['idx'] = idx
            state['stride'] = int(kv.get('Stride', state['stride']))
        stream = state['stream']
        idx = state['idx']
        stride = state['stride']
        off = int(kv.get('Offset', 0))
        fmt = kv.get('DataFormat')
        buf, _ = streams[stream]
        nb = len(buf)
        base = idx * stride * 4 + off * 4
        n = FMT_N[fmt]
        N = len(idx)
        out = np.zeros((N, 4))
        arr = np.frombuffer(buf, dtype='>u4')
        ok = (base + 4 * n <= nb) & (base >= 0)
        b = np.where(ok, base, 0) // 4
        if fmt == 'FMT_8_8_8_8':
            w = arr[b].astype(np.uint32)
            comp = [(w >> 0) & 0xFF, (w >> 8) & 0xFF, (w >> 16) & 0xFF, (w >> 24) & 0xFF]
            integer = kv.get('NumFormat') == 'integer'
            for i in range(4):
                out[:, i] = comp[i].astype(float) if integer else comp[i] / 255.0
        else:
            f = np.frombuffer(buf, dtype='>f4')
            for i in range(n):
                out[:, i] = f[b + i]
        out[~ok] = 0
        # dest swizzle: token like r6.yzxw / r0._x__ / r1.xyz1
        m = re.match(r'r(\d+)(?:\.(\w+))?$', dst)
        reg = int(m.group(1))
        sw = m.group(2) or 'xyzw'
        for lane, c in enumerate(sw):
            if c == '_':
                continue
            if c == '0':
                vm.R[reg][:, lane] = 0.0
            elif c == '1':
                vm.R[reg][:, lane] = 1.0
            else:
                vm.R[reg][:, lane] = out[:, 'xyzw'.index(c)]
    return cb


def run_skin(hash16, vb, pal, consts, shader_dir):
    sl = load_shader(hash16, shader_dir)
    N = len(vb) // 44
    vm = VM(N, consts)
    vm.R[0][:, 0] = np.arange(N)
    vm.run(sl, make_fetch_cb({0: (vb, 44), 1: (pal, 48)}))
    return vm
