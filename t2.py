from play import Play
p = Play('t2')
p.wait(30); p.key('space'); p.key('down'); p.key('space', gap=90); p.key('space', gap=60)
p.key('right', 2, gap=10); p.key('space', gap=40); p.shot('lap')
p.key('space', gap=90)
# harc: 348 Üvöltő Farkas
p.goto(348); p.shot('f348')
for i in range(12):
    p.key('space', gap=25)
    if i in (0, 3, 7, 11): p.shot(f'kor{i}')
p.dump('g_sk', 9); p.dump('f_mst', 4); p.dump('nch', 1); p.dump('choices', 4)
p.run()
