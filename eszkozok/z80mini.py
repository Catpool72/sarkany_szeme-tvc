#!/usr/bin/env python3
"""
Minimális Z80 assembler + emulátor a kicsomagoló teszteléséhez.
Csak a decoder.asm és a teszt által használt utasításokat ismeri; a flagek
közül S, Z, C pontos (H és P/V nincs modellezve – a kicsomagoló nem használja).
A T-ciklusok a hivatalos Z80 értékek.
"""
import re

R8 = {'b': 0, 'c': 1, 'd': 2, 'e': 3, 'h': 4, 'l': 5, '(hl)': 6, 'a': 7}
R16 = {'bc': 0, 'de': 1, 'hl': 2, 'sp': 3}
R16AF = {'bc': 0, 'de': 1, 'hl': 2, 'af': 3}
CC = {'nz': 0, 'z': 1, 'nc': 2, 'c': 3}
ALU = {'add': 0, 'adc': 1, 'sub': 2, 'sbc': 3, 'and': 4, 'xor': 5, 'or': 6, 'cp': 7}
CBOP = {'rlc': 0, 'rrc': 1, 'rl': 2, 'rr': 3, 'sla': 4, 'sra': 5, 'srl': 7}


class AsmError(Exception):
    pass


class Assembler:
    def __init__(self):
        self.sym = {}

    def num(self, s):
        s = s.strip()
        if re.fullmatch(r'[0-9][0-9a-fA-F]*[hH]', s):
            return int(s[:-1], 16)
        if s.startswith('$') and len(s) > 1:
            return int(s[1:], 16)
        if s.startswith('0x'):
            return int(s, 16)
        if re.fullmatch(r'%[01]+', s):
            return int(s[1:], 2)
        if re.fullmatch(r'\d+', s):
            return int(s)
        if s == '$':
            return self.pc
        if s in self.sym:
            return self.sym[s]
        if self.final:
            raise AsmError(f'ismeretlen szimbólum: {s}')
        return 0

    def expr(self, s):
        s = s.replace(' ', '')
        toks = re.findall(r'[+-]|[^+-]+', s)
        val = 0; sign = 1
        for t in toks:
            if t == '+': sign = 1
            elif t == '-': sign = -1
            else: val += sign * self.num(t)
        return val

    def split_ops(self, s):
        out = []; depth = 0; cur = ''
        for ch in s:
            if ch == '(' : depth += 1
            if ch == ')' : depth -= 1
            if ch == ',' and depth == 0:
                out.append(cur.strip()); cur = ''
            else:
                cur += ch
        if cur.strip():
            out.append(cur.strip())
        return out

    def ixd(self, op):
        m = re.fullmatch(r'\(ix([+-].*)?\)', op.replace(' ', ''))
        if not m:
            return None
        d = self.expr(m.group(1)) if m.group(1) else 0
        return d & 0xFF

    def mem(self, op):
        m = re.fullmatch(r'\((.*)\)', op)
        return m.group(1) if m else None

    def w(self, v):
        v &= 0xFFFF
        return [v & 0xFF, v >> 8]

    def enc(self, mn, ops):
        lo = [o.lower() for o in ops]
        E = self.expr
        if mn == 'nop': return [0x00]
        if mn == 'halt': return [0x76]
        if mn == 'scf': return [0x37]
        if mn == 'ccf': return [0x3F]
        if mn == 'ret':
            if not ops: return [0xC9]
            return [0xC0 | CC[lo[0]] << 3]
        if mn == 'ex' and lo == ['de', 'hl']: return [0xEB]
        if mn in ('push', 'pop'):
            base = 0xC5 if mn == 'push' else 0xC1
            if lo[0] == 'ix': return [0xDD, base + 0x20]
            return [base | R16AF[lo[0]] << 4]
        if mn in ('jp', 'call'):
            if len(ops) == 1:
                return [0xC3 if mn == 'jp' else 0xCD] + self.w(E(ops[0]))
            return [(0xC2 if mn == 'jp' else 0xC4) | CC[lo[0]] << 3] + self.w(E(ops[1]))
        if mn in ('jr', 'djnz'):
            tgt = E(ops[-1]); off = tgt - (self.pc + 2)
            if self.final and not -128 <= off <= 127: raise AsmError('jr túl messze')
            if mn == 'djnz': return [0x10, off & 0xFF]
            if len(ops) == 1: return [0x18, off & 0xFF]
            return [0x20 | CC[lo[0]] << 3, off & 0xFF]
        if mn in ('inc', 'dec'):
            o = lo[0]
            if o == 'ix': return [0xDD, 0x23 if mn == 'inc' else 0x2B]
            if o in R16: return [(0x03 if mn == 'inc' else 0x0B) | R16[o] << 4]
            if o in R8: return [(0x04 if mn == 'inc' else 0x05) | R8[o] << 3]
        if mn in CBOP:
            return [0xCB, CBOP[mn] << 3 | R8[lo[0]]]
        if mn == 'bit':
            return [0xCB, 0x40 | E(ops[0]) << 3 | R8[lo[1]]]
        if mn in ALU:
            if mn in ('add', 'adc', 'sbc') and lo[0] in ('hl', 'ix'):
                rr = R16[lo[1]]
                if mn == 'add': return ([0xDD] if lo[0] == 'ix' else []) + [0x09 | rr << 4]
                if mn == 'adc': return [0xED, 0x4A | rr << 4]
                return [0xED, 0x42 | rr << 4]
            src = ops[-1]; s = lo[-1]
            if len(ops) == 2 and lo[0] != 'a': raise AsmError('alu cél csak A')
            d = self.ixd(s)
            if d is not None: return [0xDD, 0x86 | ALU[mn] << 3, d]
            if s in R8: return [0x80 | ALU[mn] << 3 | R8[s]]
            return [0xC6 | ALU[mn] << 3, E(src) & 0xFF]
        if mn == 'ld':
            d, s = lo
            D, S = ops
            if d in R8 and s in R8: return [0x40 | R8[d] << 3 | R8[s]]
            if d in R8 and self.ixd(s) is not None: return [0xDD, 0x46 | R8[d] << 3, self.ixd(s)]
            if s in R8 and self.ixd(d) is not None: return [0xDD, 0x70 | R8[s], self.ixd(d)]
            if d == 'a' and s in ('(bc)', '(de)'): return [0x0A if s == '(bc)' else 0x1A]
            if s == 'a' and d in ('(bc)', '(de)'): return [0x02 if d == '(bc)' else 0x12]
            if d == 'a' and self.mem(S) is not None: return [0x3A] + self.w(E(self.mem(S)))
            if s == 'a' and self.mem(D) is not None: return [0x32] + self.w(E(self.mem(D)))
            if d in R8: return [0x06 | R8[d] << 3, E(S) & 0xFF]
            if d == 'ix':
                if self.mem(S) is not None: return [0xDD, 0x2A] + self.w(E(self.mem(S)))
                return [0xDD, 0x21] + self.w(E(S))
            if d == 'sp' and s == 'hl': return [0xF9]
            if d in R16:
                if self.mem(S) is not None:
                    if d == 'hl': return [0x2A] + self.w(E(self.mem(S)))
                    return [0xED, 0x4B | R16[d] << 4] + self.w(E(self.mem(S)))
                return [0x01 | R16[d] << 4] + self.w(E(S))
            if self.mem(D) is not None and s in R16:
                if s == 'hl': return [0x22] + self.w(E(self.mem(D)))
                return [0xED, 0x43 | R16[s] << 4] + self.w(E(self.mem(D)))
            if self.mem(D) is not None and s == 'ix': return [0xDD, 0x22] + self.w(E(self.mem(D)))
        raise AsmError(f'nem támogatott: {mn} {",".join(ops)}')

    def assemble(self, text, org=0):
        lines = text.splitlines()
        for final in (False, True):
            self.final = final
            self.pc = org; out = {}
            for ln, raw in enumerate(lines, 1):
                line = raw.split(';')[0].rstrip()
                if not line.strip(): continue
                try:
                    m = re.match(r'^([A-Za-z_.][\w.]*):?\s*(.*)$', line) if not line[0].isspace() else None
                    label = None
                    if m:
                        label, rest = m.group(1), m.group(2)
                    else:
                        rest = line.strip()
                    parts = rest.split(None, 1)
                    mn = parts[0].lower() if parts else ''
                    arg = parts[1] if len(parts) > 1 else ''
                    if mn == 'equ':
                        self.sym[label] = self.expr(arg); continue
                    if label:
                        if not final and label in self.sym and self.sym[label] != self.pc and label != label:
                            pass
                        self.sym[label] = self.pc
                    if not mn: continue
                    if mn == 'org':
                        self.pc = self.expr(arg); continue
                    if mn in ('db', 'defb'):
                        bs = []
                        for o in self.split_ops(arg):
                            if o.startswith('"'): bs += list(o.strip('"').encode('latin-1'))
                            else: bs.append(self.expr(o) & 0xFF)
                    elif mn in ('dw', 'defw'):
                        bs = []
                        for o in self.split_ops(arg): bs += self.w(self.expr(o))
                    elif mn in ('ds', 'defs'):
                        bs = [0] * self.expr(arg)
                    else:
                        bs = self.enc(mn, self.split_ops(arg))
                    for i, b in enumerate(bs): out[self.pc + i] = b
                    self.pc += len(bs)
                except AsmError as e:
                    raise AsmError(f'{ln}. sor: {raw.strip()} -> {e}')
                except KeyError as e:
                    raise AsmError(f'{ln}. sor: {raw.strip()} -> rossz operandus {e}')
        return out


class CPU:
    def __init__(self, mem):
        self.m = mem
        self.a = self.b = self.c = self.d = self.e = self.h = self.l = 0
        self.f = 0; self.ix = 0; self.sp = 0xFFFE; self.pc = 0; self.t = 0; self.halted = False

    # flags: S=0x80 Z=0x40 C=0x01
    def rd(self, a): return self.m[a & 0xFFFF]
    def wr(self, a, v): self.m[a & 0xFFFF] = v & 0xFF
    def rw(self, a): return self.rd(a) | self.rd(a + 1) << 8
    def ww(self, a, v): self.wr(a, v); self.wr(a + 1, v >> 8)
    def fetch(self):
        v = self.rd(self.pc); self.pc = (self.pc + 1) & 0xFFFF; return v
    def fw(self):
        return self.fetch() | self.fetch() << 8
    def get16(self, i):
        return [(self.b << 8) | self.c, (self.d << 8) | self.e, (self.h << 8) | self.l, self.sp][i]
    def set16(self, i, v):
        v &= 0xFFFF
        if i == 0: self.b, self.c = v >> 8, v & 0xFF
        elif i == 1: self.d, self.e = v >> 8, v & 0xFF
        elif i == 2: self.h, self.l = v >> 8, v & 0xFF
        else: self.sp = v
    @property
    def hl(self): return (self.h << 8) | self.l
    def r8(self, i):
        return [self.b, self.c, self.d, self.e, self.h, self.l, None, self.a][i] if i != 6 else self.rd(self.hl)
    def w8(self, i, v):
        v &= 0xFF
        if i == 6: self.wr(self.hl, v); return
        setattr(self, 'bcdehl_a'[i] if i != 7 else 'a', v) if False else None
        if i == 0: self.b = v
        elif i == 1: self.c = v
        elif i == 2: self.d = v
        elif i == 3: self.e = v
        elif i == 4: self.h = v
        elif i == 5: self.l = v
        else: self.a = v
    def szf(self, v):
        return (0x80 if v & 0x80 else 0) | (0x40 if (v & 0xFF) == 0 else 0)
    def cond(self, cc):
        return [not self.f & 0x40, bool(self.f & 0x40), not self.f & 1, bool(self.f & 1)][cc]
    def push(self, v):
        self.sp = (self.sp - 2) & 0xFFFF; self.ww(self.sp, v)
    def pop(self):
        v = self.rw(self.sp); self.sp = (self.sp + 2) & 0xFFFF; return v
    def alu(self, op, v):
        a = self.a; c = self.f & 1
        if op in (0, 1):
            r = a + v + (c if op == 1 else 0); self.a = r & 0xFF; self.f = self.szf(r) | (1 if r > 0xFF else 0)
        elif op in (2, 3, 7):
            r = a - v - (c if op == 3 else 0)
            f = self.szf(r & 0xFF) | (1 if r < 0 else 0) | 0x02
            if op != 7: self.a = r & 0xFF
            self.f = f
        elif op == 4: self.a = a & v; self.f = self.szf(self.a)
        elif op == 5: self.a = a ^ v; self.f = self.szf(self.a)
        elif op == 6: self.a = a | v; self.f = self.szf(self.a)

    def step(self):
        op = self.fetch()
        T = 4
        if op == 0x00: pass
        elif op == 0x76: self.halted = True; self.pc -= 1
        elif op == 0x37: self.f |= 1
        elif op == 0x3F: self.f ^= 1
        elif op == 0xEB:
            self.d, self.e, self.h, self.l = self.h, self.l, self.d, self.e
        elif op & 0xC0 == 0x40:
            T = 7 if (op & 7) == 6 or (op >> 3 & 7) == 6 else 4
            self.w8(op >> 3 & 7, self.r8(op & 7))
        elif op & 0xC7 == 0x06:
            r = op >> 3 & 7; self.w8(r, self.fetch()); T = 10 if r == 6 else 7
        elif op & 0xCF == 0x01:
            self.set16(op >> 4 & 3, self.fw()); T = 10
        elif op & 0xC0 == 0x80:
            r = op & 7; self.alu(op >> 3 & 7, self.r8(r)); T = 7 if r == 6 else 4
        elif op & 0xC7 == 0xC6:
            self.alu(op >> 3 & 7, self.fetch()); T = 7
        elif op & 0xCF == 0x09:
            r = self.hl + self.get16(op >> 4 & 3)
            self.set16(2, r); self.f = (self.f & ~1) | (1 if r > 0xFFFF else 0); T = 11
        elif op & 0xCF == 0x03: i = op >> 4 & 3; self.set16(i, self.get16(i) + 1); T = 6
        elif op & 0xCF == 0x0B: i = op >> 4 & 3; self.set16(i, self.get16(i) - 1); T = 6
        elif op & 0xC7 == 0x04:
            r = op >> 3 & 7; v = (self.r8(r) + 1) & 0xFF; self.w8(r, v); self.f = (self.f & 1) | self.szf(v); T = 11 if r == 6 else 4
        elif op & 0xC7 == 0x05:
            r = op >> 3 & 7; v = (self.r8(r) - 1) & 0xFF; self.w8(r, v); self.f = (self.f & 1) | self.szf(v) | 2; T = 11 if r == 6 else 4
        elif op == 0x2A: self.set16(2, self.rw(self.fw())); T = 16
        elif op == 0x22: self.ww(self.fw(), self.hl); T = 16
        elif op == 0x3A: self.a = self.rd(self.fw()); T = 13
        elif op == 0x32: self.wr(self.fw(), self.a); T = 13
        elif op == 0x0A: self.a = self.rd(self.get16(0)); T = 7
        elif op == 0x1A: self.a = self.rd(self.get16(1)); T = 7
        elif op == 0x02: self.wr(self.get16(0), self.a); T = 7
        elif op == 0x12: self.wr(self.get16(1), self.a); T = 7
        elif op == 0xF9: self.sp = self.hl; T = 6
        elif op & 0xCF == 0xC5:
            i = op >> 4 & 3
            self.push(((self.a << 8) | self.f) if i == 3 else self.get16(i)); T = 11
        elif op & 0xCF == 0xC1:
            i = op >> 4 & 3; v = self.pop()
            if i == 3: self.a, self.f = v >> 8, v & 0xFF
            else: self.set16(i, v)
            T = 10
        elif op == 0xC3: self.pc = self.fw(); T = 10
        elif op & 0xC7 == 0xC2:
            a = self.fw(); T = 10
            if self.cond(op >> 3 & 3): self.pc = a
        elif op == 0xCD: a = self.fw(); self.push(self.pc); self.pc = a; T = 17
        elif op & 0xC7 == 0xC4:
            a = self.fw(); T = 10
            if self.cond(op >> 3 & 3): self.push(self.pc); self.pc = a; T = 17
        elif op == 0xC9: self.pc = self.pop(); T = 10
        elif op & 0xC7 == 0xC0:
            T = 5
            if self.cond(op >> 3 & 3): self.pc = self.pop(); T = 11
        elif op == 0x18:
            d = self.fetch(); self.pc = (self.pc + (d - 256 if d > 127 else d)) & 0xFFFF; T = 12
        elif op & 0xE7 == 0x20:
            d = self.fetch(); T = 7
            if self.cond(op >> 3 & 3): self.pc = (self.pc + (d - 256 if d > 127 else d)) & 0xFFFF; T = 12
        elif op == 0x10:
            d = self.fetch(); self.b = (self.b - 1) & 0xFF; T = 8
            if self.b: self.pc = (self.pc + (d - 256 if d > 127 else d)) & 0xFFFF; T = 13
        elif op == 0xCB:
            o = self.fetch(); r = o & 7; v = self.r8(r); T = 15 if r == 6 else 8
            if o < 0x40:
                k = o >> 3; c = self.f & 1
                if k == 0: nc = v >> 7; v = (v << 1 | nc) & 0xFF
                elif k == 1: nc = v & 1; v = (v >> 1) | (nc << 7)
                elif k == 2: nc = v >> 7; v = (v << 1 | c) & 0xFF
                elif k == 3: nc = v & 1; v = (v >> 1) | (c << 7)
                elif k == 4: nc = v >> 7; v = (v << 1) & 0xFF
                elif k == 5: nc = v & 1; v = (v >> 1) | (v & 0x80)
                elif k == 7: nc = v & 1; v = v >> 1
                else: raise RuntimeError('CB?')
                self.w8(r, v); self.f = self.szf(v) | nc
            elif o < 0x80:
                b = o >> 3 & 7; self.f = (self.f & 1) | (0x40 if not (v >> b) & 1 else 0); T = 12 if r == 6 else 8
            else:
                raise RuntimeError(f'CB {o:02X}')
        elif op == 0xED:
            o = self.fetch()
            if o & 0xCF == 0x42:
                r = self.hl - self.get16(o >> 4 & 3) - (self.f & 1)
                self.set16(2, r); self.f = (0x80 if r & 0x8000 else 0) | (0x40 if r & 0xFFFF == 0 else 0) | (1 if r < 0 else 0) | 2; T = 15
            elif o & 0xCF == 0x4A:
                r = self.hl + self.get16(o >> 4 & 3) + (self.f & 1)
                self.set16(2, r); self.f = (0x80 if r & 0x8000 else 0) | (0x40 if r & 0xFFFF == 0 else 0) | (1 if r > 0xFFFF else 0); T = 15
            elif o & 0xCF == 0x4B: self.set16(o >> 4 & 3, self.rw(self.fw())); T = 20
            elif o & 0xCF == 0x43: self.ww(self.fw(), self.get16(o >> 4 & 3)); T = 20
            else: raise RuntimeError(f'ED {o:02X} @ {self.pc:04X}')
        elif op == 0xDD:
            o = self.fetch()
            def dd():
                d = self.fetch(); return (self.ix + (d - 256 if d > 127 else d)) & 0xFFFF
            if o == 0x21: self.ix = self.fw(); T = 14
            elif o == 0x2A: self.ix = self.rw(self.fw()); T = 20
            elif o == 0x22: self.ww(self.fw(), self.ix); T = 20
            elif o == 0x23: self.ix = (self.ix + 1) & 0xFFFF; T = 10
            elif o == 0x2B: self.ix = (self.ix - 1) & 0xFFFF; T = 10
            elif o == 0xE5: self.push(self.ix); T = 15
            elif o == 0xE1: self.ix = self.pop(); T = 14
            elif o & 0xC7 == 0x46 and o != 0x76: self.w8(o >> 3 & 7, self.rd(dd())); T = 19
            elif o & 0xF8 == 0x70 and o != 0x76: a = dd(); self.wr(a, self.r8(o & 7)); T = 19
            elif o & 0xC7 == 0x86: self.alu(o >> 3 & 7, self.rd(dd())); T = 19
            elif o & 0xCF == 0x09:
                rr = [self.get16(0), self.get16(1), self.ix, self.sp][o >> 4 & 3]
                r = self.ix + rr; self.ix = r & 0xFFFF; self.f = (self.f & ~1) | (1 if r > 0xFFFF else 0); T = 15
            else: raise RuntimeError(f'DD {o:02X} @ {self.pc:04X}')
        else:
            raise RuntimeError(f'ismeretlen opkód {op:02X} @ {(self.pc - 1) & 0xFFFF:04X}')
        self.t += T

    def call(self, addr, limit=50_000_000):
        """Meghív egy rutint; a visszatérési cím egy HALT-ra mutat."""
        self.wr(0x0000, 0x76)
        self.push(0x0000)
        self.pc = addr; self.halted = False
        t0 = self.t; n = 0
        while not self.halted:
            self.step(); n += 1
            if n > limit: raise RuntimeError('végtelen ciklus?')
        return self.t - t0
