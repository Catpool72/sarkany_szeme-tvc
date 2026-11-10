from play import Play, pages
p = Play('t7')
p.wait(30); p.key('space'); p.key('space', gap=90); p.key('space', gap=60)
p.poke('g_st', 30)
p.goto(12); p.key('space', pages(12), gap=60); p.shot('harc_kov'); p.key('space', gap=40)
for i in range(12):
    p.key('space', gap=30)
    if i in (2, 5, 8, 11): p.shot(f'k{i}')
p.dump('res', 1); p.dump('choices', 2); p.dump('nch', 1)
p.run()
