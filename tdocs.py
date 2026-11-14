"""A README képernyőképei (lemezes változat, tvcsim):
   BUILD=build_disk CAS=build_disk/lemez/KALAND.CAS DISKDIR=build_disk/lemez python3 tdocs.py"""
from play import Play, pages
def start(name):
    p = Play(name)
    p.wait(40); p.shot('cimlap')
    p.key('space', gap=200); p.shot('kalandlap')
    p.key('space', gap=120)                   # varázsital -> előzmények
    p.key('space', gap=120); p.shot('elozmenyek')
    p.key('space', 9, gap=120)                # előzmények két része
    p.shot('fejezet1_lap1'); p.key('space', gap=120); p.key('space', gap=120)
    p.shot('fejezet1_valasztas')
    return p
p = start('docs')
p.sec(243, 0, 'fejezet243_uj_rajz')
p.sec(262, 0, 'szerencsepróba')
p.goto(329); p.key('space', pages(329) + 1, gap=90); p.shot('bolt')
p.run()
p = start('docs2')
p.goto(348); p.key('space', pages(348), gap=90); p.key('space', gap=60)
for i in range(3): p.key('space', gap=40)
p.shot('harc')
p.run()
p = start('docs3')
p.goto(243); p.key('space', pages(243), gap=90)
p.sec(377, 0, 'vege')
p.run()
