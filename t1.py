from play import Play
p = Play('t1')
p.wait(30); p.shot('cim')
p.key('space', gap=40); p.shot('kalandlap')
p.key('down'); p.shot('ital_valaszt')
p.key('space', gap=90); p.shot('f1_lap1')
p.key('space', gap=60); p.shot('f1_menu')
p.dump('g_sk', 9); p.dump('items', 8)
# Lap: a menüben jobbra a végére
p.key('right', 3, gap=10); p.shot('menu_lap')
p.key('space', gap=40); p.shot('kalandlap_nezet')
p.key('space', gap=90); p.shot('vissza')
p.run()
