from play import Play, pages
p = Play('doc')
p.wait(30); p.key('space'); p.shot('kalandlap')
p.key('down'); p.key('space', gap=90); p.key('space', gap=60)
p.sec(262, 1, 'szerencse')
p.goto(348); p.key('space', pages(348), gap=60); p.shot('harc_elott'); p.key('space', gap=40)
for i in range(4): p.key('space', gap=30)
p.shot('harc')
p.run()
