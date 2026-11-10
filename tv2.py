from play import Play
p = Play('tv2')
p.wait(40); p.key('space', gap=60); p.key('space', gap=120)
for i in range(3): p.key('space', gap=70)
p.shot('elo2')
p.run()
