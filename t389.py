from play import Play, pages
p = Play('t389')
p.wait(30); p.key('space'); p.key('space', gap=90); p.key('space', gap=60)
p.poke('g_sk', 2)                    # alacsony ÜGYESSÉG: biztosan nem sikerül
p.goto(389); p.key('space', pages(389), gap=60); p.shot('menu')
p.key('space', gap=60); p.shot('proba')
p.key('space', gap=90); p.key('space', pages(389), gap=60); p.shot('ujra389')
p.key('right'); p.shot('88_kijelolve')
p.dump('g_st', 2)
p.run()
