from play import Play
p = Play('t3')
p.wait(30); p.key('space'); p.key('down'); p.key('space', gap=90); p.key('space', gap=60)
p.sec(258, 1, 'gain')            # +1 arany, tükördarab
p.shot('menu258')
p.sec(262, 1, 'luck')
p.shot('menu262')
p.sec(389, 1, 'skill')
p.shot('menu389')
p.sec(329, 0, 'shop')
p.key('down'); p.key('space'); p.shot('vett1'); p.key('space')
p.key('down', 2, gap=15); p.key('space'); p.shot('vett2'); p.key('space')
p.key('down', 2, gap=15); p.key('space'); p.shot('nincsmeg'); p.key('space')
p.key('down', 10, gap=10); p.shot('kesz'); p.key('space', gap=60)
from play import pages
p.key('space', pages(329), gap=60); p.shot('menu329')
p.dump('g_sk', 9); p.dump('items', 8)
p.sec(79, 0, 'harcmenu')
p.run()
