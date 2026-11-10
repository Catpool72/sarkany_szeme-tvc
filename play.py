#!/usr/bin/env python3
"""Tesztforgatókönyv-író a tvcsim-hez: billentyűk, várakozás, képmentés, memória-poke.
   python3 play.py <név>  -> test_<név>.txt, futtatás és PNG-k a shots/ mappában"""
import os, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
SYM = {}
for line in open(os.path.join(HERE, os.environ.get('BUILD', 'build'), 'kaland.sym')):
    p = line.replace(':', ' ').split()
    if len(p) >= 3 and p[1].upper() == 'EQU':
        SYM[p[0]] = int(p[2].replace('0x', ''), 16)
KEYS = {'space': (7, 0x20), 'esc': (7, 0x08), 'up': (8, 0x02), 'down': (8, 0x04), 'fire': (8, 0x08),
        'right': (8, 0x20), 'left': (8, 0x40)}

import json
_doc = json.load(open(os.path.join(HERE, 'konyv', 'sarkany_szeme.json'), encoding='utf-8'))
_S = {x['id']: x for x in _doc['sections']}
def pages(n, W=33, ROWS=22):
    text = _S[n]['text']
    col, row, pg = 0, 1, 0
    def nl():
        nonlocal col, row, pg
        col = 0; row += 1
        if row >= ROWS: pg += 1; row = 0
    for w in text.split(' '):
        if col and col + len(w) > W: nl()
        for ch in w:
            col += 1
            if col >= W: nl()
        if col and col < W: col += 1
    return pg

class Play:
    def __init__(s, name, seed=None):
        s.name, s.f, s.lines, s.shots = name, 20, [], []
    def wait(s, n): s.f += n
    def key(s, k, n=1, gap=40):
        for _ in range(n):
            row, m = KEYS[k]
            s.lines += [f'key {s.f} {row} {m}', f'key {s.f + 3} {row} 0']
            s.f += gap
    def shot(s, tag):
        p = f'shots/{s.name}_{len(s.shots):02d}_{tag}.ppm'
        s.lines.append(f'shot {s.f} {p}'); s.shots.append(p); s.f += 2
    def poke(s, addr, *vals):
        if isinstance(addr, str): addr = SYM[addr]
        for i, v in enumerate(vals): s.lines.append(f'poke {s.f} {addr + i} {v}')
        s.f += 1
    def dump(s, addr, n):
        if isinstance(addr, str): addr = SYM[addr]
        s.lines.append(f'dump {s.f} {addr} {n}'); s.f += 1
    def goto(s, sec):
        """a menü első választását átírja, és lapoz (a menüben kell állnunk)"""
        s.poke('choices', sec & 255, sec >> 8)
        s.key('space', gap=90)
    def sec(s, n, msgs=0, tag=None):
        """lapozás az n. fejezetre a menüből; a 'tovább' oldalak és msgs üzenet nyugtázása előtt kép"""
        s.goto(n)
        s.key('space', pages(n), gap=60)
        s.shot(tag or f's{n}')
        s.key('space', msgs, gap=40)
    def run(s):
        fn = f'test_{s.name}.txt'
        open(os.path.join(HERE, fn), 'w').write('\n'.join(s.lines) + '\n')
        r = subprocess.run([os.path.join(HERE, 'harness', 'tvcsim'), os.environ.get('CAS', os.environ.get('BUILD', 'build') + '/kaland.cas'), fn, str(s.f + 20)],
                           cwd=HERE, capture_output=True, text=True, errors='replace')
        print(r.stdout[-3000:], r.stderr[-2000:])
        for p in s.shots:
            q = os.path.join(HERE, p)
            if os.path.exists(q):
                Image.open(q).save(q[:-4] + '.png'); os.remove(q)
        return r
