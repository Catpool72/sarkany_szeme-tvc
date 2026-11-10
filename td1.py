from play import Play, pages
p = Play('td1')
p.wait(40); p.shot('cim')
p.key('space', gap=60); p.key('down'); p.key('space', gap=90); p.key('space', gap=60); p.shot('f1')
for n in (400, 227, 35, 185, 290, 137, 49):
    p.goto(n); p.key('space', pages(n), gap=60); p.shot(f's{n}')
p.dump('cache_tag', 8)
p.run()
