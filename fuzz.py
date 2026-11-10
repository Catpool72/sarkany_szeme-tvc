"""Véletlen billentyűzés hosszú futásra: összeomlás, rossz írás, lemezhiba keresése."""
import random, sys
from play import Play
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
n = int(sys.argv[2]) if len(sys.argv) > 2 else 600
random.seed(seed)
p = Play(f'fuzz{seed}')
p.wait(40); p.shot('cim')
for i in range(n):
    k = random.choice(['space'] * 6 + ['right', 'right', 'left', 'down', 'up'])
    p.key(k, gap=random.choice([12, 20, 35]))
    if i % 150 == 149: p.shot(f'k{i}')
p.dump('cur_sec', 2); p.dump('g_sk', 9)
p.run()
