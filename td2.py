from play import Play
p = Play('td2')
p.wait(40); p.key('space', gap=60); p.key('space', gap=120); p.shot('elozmenyek')
p.run()
