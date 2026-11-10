#!/usr/bin/env python3
"""Tesztszkript a tvcsim-hez: végigjár egy fejezet-útvonalat (a tördelés Python-modelljéből
számolja a "tovább" oldalakat), képeket ment, végül Esc."""
import json, sys, collections
W, ROWS = 33, 22
doc = json.load(open('konyv/sarkany_szeme.json', encoding='utf-8'))
S = {s['id']: s for s in doc['sections']}
info = json.load(open('build/info.json'))
demo = set(info['sections'])

def pages(n):
    text = S[n]['text'] if n in demo else 'Ez a fejezet ebben a demóban nem szerepel.'
    col, row, pg = 0, 1, 0            # 1. sor: fejezetszám
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

def path_to(target):
    prev = {1: None}; q = collections.deque([1])
    while q:
        n = q.popleft()
        if n == target: break
        if n not in demo: continue
        for j in S[n]['jumps']:
            if j not in prev: prev[j] = n; q.append(j)
    p = [target]
    while prev[p[-1]] is not None: p.append(prev[p[-1]])
    return p[::-1]

out = []; f = 30
def press(row, mask, hold=3, gap=40):
    global f
    out.append(f'key {f} {row} {mask}'); out.append(f'key {f+hold} {row} 0'); f += hold + gap
out.append(f'shot {f} shots/s00_cim.ppm'); f += 10
press(7, 32)                                    # indulás -> 1. fejezet
route = path_to(int(sys.argv[1])) + [int(x) for x in sys.argv[2:]]
for i, n in enumerate(route):
    f += 40
    for _ in range(pages(n)):
        out.append(f'shot {f} shots/s{i:02d}_{n}_lap.ppm'); f += 5
        press(7, 32, gap=60)
    out.append(f'shot {f} shots/s{i:02d}_{n}.ppm'); f += 5
    if i + 1 < len(route):
        k = S[n]['jumps'].index(route[i + 1]) if n in demo else 0
        for _ in range(k): press(8, 32, gap=8)  # jobbra
        press(7, 32)
press(7, 8)                                     # Esc
open('test_route.txt', 'w').write('\n'.join(out) + '\n')
print('útvonal:', route, 'képkockák:', f + 50)
