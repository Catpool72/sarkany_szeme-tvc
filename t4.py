from play import Play, pages
p = Play('t4')
p.wait(30); p.key('space'); p.key('down'); p.key('space', gap=90); p.key('space', gap=60)
p.goto(79); p.key('space', pages(79), gap=60)
p.key('right'); p.key('space', gap=40); p.shot('harc_kov')
for i in range(30):
    p.key('space', gap=30)
    if i % 3 == 2: p.shot(f'k{i}')
    if i % 3 == 2: p.dump('f_mst', 4)
p.run()
