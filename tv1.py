from play import Play
p = Play('tv1')
p.wait(40); p.shot('cim')
p.key('space', gap=60); p.key('space', gap=120); p.shot('elozmenyek')
for i in range(6): p.key('space', gap=70)
p.shot('f1')
p.run()
