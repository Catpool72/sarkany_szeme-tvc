# A Sárkány szeme – szövegtömörítés és Z80 kicsomagoló TVC-hez

A 407 fejezet szövege tömörítve, fejezetenként külön kicsomagolhatóan.
A kicsomagoló 162 bájtos Z80 rutin. Ki van próbálva: Z80 emulátorban
mind a 407 fejezet bájtra pontosan egyezik az eredetivel.

## Tartalom

| Fájl | Mi ez |
|---|---|
| `sarkany_szeme.json` | A könyv adatbázisa: lektorált szöveg, bevezető, ugrások, harcok, pontváltozások, kulcs-mechanika |
| `sarkany_szeme_lektoralt.txt` | A lektorált szöveg olvasható formában (bevezető + 407 fejezet) |
| `src/decoder.asm` | Z80 kicsomagoló (`DECODE_SECTION`) |
| `build1024/` | **Ajánlott** készlet: `book_text.bin`, `book_index.bin`, `book_tables.asm`, `book_ref.txt` |
| `build512/`, `build2048/` | Kisebb táblás, ill. kisebb szövegű változat |
| `tools/encode.py` | A tömörítő (Python 3, csak a standard könyvtár kell hozzá) |
| `tools/test_decoder.py` | Teszt: lefordítja a `decoder.asm`-et, és emulátorban kicsomagolja mind a 407 fejezetet |
| `tools/z80mini.py` | A teszthez írt mini Z80 assembler és emulátor (csak a kicsomagoló utasításait ismeri) |

## Méretek és sebesség

A sebesség 3,125 MHz-en, emulátorban mért T-ciklusból számolva, várakozási ciklusok nélkül.

| Változat | Szöveg | Rezidens táblák | Index | Összesen | Átlag / leghosszabb fejezet |
|---|---|---|---|---|---|
| 512 token | 80,4 KB | 2,8 KB | 1,2 KB | 84,4 KB | 105 ms / 563 ms |
| **1024 token** | **71,6 KB** | **5,8 KB** | **1,2 KB** | **78,6 KB** | **97 ms / 534 ms** |
| 2048 token | 63,4 KB | 11,7 KB | 1,2 KB | 76,2 KB | 90 ms / 497 ms |

A nyers (lektorált) szöveg 184 KB. A leghosszabb fejezet (49.) 2406 karakter, ezért a kimeneti puffer legyen legalább 2407 bájt.

## Formátum

- **book_index.bin**: 407 × 3 bájt, little endian. Az *n*-edik fejezet kezdőcíme a `book_text.bin`-ben (*n* = 1…407). A fejezet hossza a következő bejegyzésig tart; a 407. fejezet a fájl végéig.
- **book_text.bin**: a fejezetek bájthatáron kezdődnek. Mindegyik egy kanonikus Huffman-kódolt tokenfolyam, END tokennel lezárva.
- **book_tables.asm** (ezek maradnak a memóriában):
  - `CHARTAB`: alapkarakter → kimeneti kód; a 0 jelöli az END-et.
  - `RULES`: `dw bal, jobb` minden BPE-tokenhez.
  - `LIMOFF`: `dw LIM, OFF` kódhosszanként, legfeljebb 15 bitig.
  - `SYMS`: a tokenek kanonikus sorrendben.

## Használat

```asm
        include "decoder.asm"
        include "book_tables.asm"

; lemezes változat: a fejezet bájtjait (index[n] .. index[n+1]) betöltöd egy pufferbe
        ld hl,LOADBUF           ; a fejezet első bájtja
        ld de,TEXTBUF           ; kimenet (>= 2407 bájt)
        call DECODE_SECTION     ; -> TEXTBUF: 0-val lezárt szöveg
```

- **Lemezről (TVC 64K):** a fejezet a `book_text.bin` összefüggő tartománya, átlagosan 180 bájt, legfeljebb kb. 1 KB. Általában egy, legfeljebb három 512 bájtos szektorba esik. A memóriában csak a kód, a táblák és az index marad, ez az 1024-es változatnál kb. 7,2 KB.
- **Egyben a memóriában (TVC 64+):** a szöveg több 16 KB-os lapon helyezkedik el. A `DEC_FETCH` címkénél (`ld a,(hl) / inc hl`) kell lapot váltani, amikor HL átlépi a lap határát. A rutin máshol nem olvas a szövegből.
- A rutin rontja az AF, BC, DE, HL regisztereket. Az IX-et, az IY-t és a kiegészítő regisztereket nem használja, és a megszakításokat sem tiltja le.

## Karakterkódok – teendő

Az `encode.py` alapból ISO-8859-2 kódokat ír a `CHARTAB`-ba. **A TVC saját karakterkódjaihoz** a `default_charmap()` függvényt kell átírni. Elég, ha az ékezetes betűknél a TVC-s kódot adja vissza. Ezután újra kell futtatni az `encode.py`-t; a kicsomagolón ehhez nem kell változtatni.

Az alapkarakterek listája (87 db) a `build*/stats.json` fájlban van, az `alphabet` mezőben. A szöveg csak ASCII-írásjeleket használ (az idézőjel egyszerű `"`), az ékezetes betűk: á é í ó ö ő ú ü ű és nagybetűs párjaik közül Á É Í Ó Ö Ő Ú Ü.

## Újragenerálás

```
python3 tools/encode.py sarkany_szeme.json --tokens 1024 --out build1024
python3 tools/test_decoder.py build1024
```

A javított szöveget a `sarkany_szeme.json` `sections[].text` mezőjébe kell írni.
