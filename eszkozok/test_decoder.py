#!/usr/bin/env python3
"""
A decoder.asm tesztje: lefordítja a Z80 forrást a generált táblákkal, majd
mind a 407 fejezetet kicsomagoltatja az emulátorban, és bájtra összeveti a
book_ref.txt-vel. Közben méri a futásidőt (T-ciklus).

Használat: python3 test_decoder.py build1024
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from z80mini import Assembler, CPU

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
build = sys.argv[1]

# --- assembler önellenőrzés néhány ismert kódolással --------------------
known = {
    'ld a,(ix+1)': 'DD7E01', 'sbc hl,de': 'ED52', 'rl c': 'CB11', 'rl b': 'CB10',
    'ld de,(1234h)': 'ED5B3412', 'adc a,(ix+1)': 'DD8E01', 'sub (ix+0)': 'DD9600',
    'sbc a,(ix+1)': 'DD9E01', 'add a,(ix+0)': 'DD8600', 'sla e': 'CB23', 'ld (hl),0': '3600',
    'ld (1234h),de': 'ED533412', 'ld ix,1234h': 'DD213412', 'inc ix': 'DD23',
    'add hl,hl': '29', 'add hl,de': '19', 'ex de,hl': 'EB', 'adc a,a': '8F', 'add a,a': '87',
    'scf': '37', 'or a': 'B7', 'or 1': 'F601', 'and l': 'A5', 'inc a': '3C', 'xor a': 'AF',
    'ld hl,(1234h)': '2A3412', 'ld (1234h),hl': '223412', 'ld a,(1234h)': '3A3412',
    'ld (1234h),a': '323412', 'push bc': 'C5', 'pop hl': 'E1', 'ld h,(hl)': '66',
    'ld e,(hl)': '5E', 'ld a,(hl)': '7E', 'ld (hl),a': '77', 'ld bc,0FFFFh': '01FFFF',
}
for src, hexs in known.items():
    a = Assembler(); out = a.assemble('        ' + src, org=0x100)
    got = ''.join(f'{out[k]:02X}' for k in sorted(out))
    assert got == hexs, f'{src}: {got} != {hexs}'
print(f'assembler: {len(known)} ismert kódolás rendben')

# --- fordítás ------------------------------------------------------------
CODE = 0x4000
src = f"""        org {CODE}
""" + open(os.path.join(ROOT, 'src', 'decoder.asm'), encoding='utf-8').read() + '\n' + \
    open(os.path.join(build, 'book_tables.asm'), encoding='utf-8').read()
asm = Assembler()
img = asm.assemble(src, org=CODE)
code_end = asm.sym['CHARTAB']
print(f'kicsomagoló kód: {code_end - CODE} bájt, táblák: {max(img) + 1 - code_end} bájt,'
      f' összesen {max(img) + 1 - CODE} bájt ({CODE:04X}h–{max(img):04X}h)')

text = open(os.path.join(build, 'book_text.bin'), 'rb').read()
idx = open(os.path.join(build, 'book_index.bin'), 'rb').read()
offs = [int.from_bytes(idx[i:i + 3], 'little') for i in range(0, len(idx), 3)] + [len(text)]
ref = open(os.path.join(build, 'book_ref.txt'), 'rb').read().split(b'\n')

INBUF, OUTBUF = 0xA000, 0xC000
assert max(img) < INBUF
tot_t = 0; worst = (0, 0); tot_chars = 0
for n in range(407):
    mem = bytearray(0x10000)
    for k, v in img.items(): mem[k] = v
    chunk = text[offs[n]:offs[n + 1]]
    mem[INBUF:INBUF + len(chunk)] = chunk          # "betöltés lemezről"
    cpu = CPU(mem)
    cpu.sp = 0xFFF0
    cpu.h, cpu.l = INBUF >> 8, INBUF & 0xFF
    cpu.d, cpu.e = OUTBUF >> 8, OUTBUF & 0xFF
    t = cpu.call(asm.sym['DECODE_SECTION'])
    end = mem.index(0, OUTBUF)
    got = bytes(mem[OUTBUF:end])
    assert got == ref[n], f'{n + 1}. fejezet eltér'
    assert cpu.hl == end, 'HL nem a lezáró 0-ra mutat'
    assert cpu.sp == 0xFFF0, 'verem nincs egyensúlyban'
    used = (cpu.get16(2) - INBUF)
    tot_t += t; tot_chars += len(got)
    if t > worst[0]: worst = (t, n + 1, len(got))
mhz = 3.125
print(f'mind a 407 fejezet bájtra egyezik')
print(f'átlag: {tot_t / 407:,.0f} T/fejezet = {tot_t / 407 / mhz / 1e6 * 1000:.0f} ms (3,125 MHz),'
      f' {tot_t / tot_chars:.0f} T/karakter')
print(f'leglassabb: {worst[1]}. fejezet, {worst[2]} karakter, {worst[0]:,} T = {worst[0] / mhz / 1e6 * 1000:.0f} ms')
