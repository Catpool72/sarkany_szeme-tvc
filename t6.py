from play import Play, pages
p = Play('t6')
p.wait(30); p.key('space'); p.key('space', gap=90); p.key('space', gap=60)
p.poke('items', 0xFF, 0x7F, 0xFF, 0xFF, 0xF0, 0xFF, 0x0F)
p.key('right', 2, gap=10); p.key('space', gap=40); p.shot('lap'); p.key('space', gap=90); p.key('space', gap=60)
p.poke('g_st', 99)
p.goto(12); p.key('space', pages(12), gap=60); p.key('space'); p.key('space')   # +1 Sz nincs üzenet; harc következik
for i in range(10): p.key('space', gap=30)
p.shot('boszorkany')
p.dump('res', 1); p.dump('choices', 2)
p.run()
