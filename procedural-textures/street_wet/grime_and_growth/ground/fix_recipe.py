import os, re
WG = os.environ['WG']
p = os.path.join(WG, '14 Recipe - ground - how it is made.md')
s = open(p).read()
i = s.index('## What was tested')
head = s[:i]
table = open(os.path.join(WG, 'p1_table.md')).read()
tail = '''## What was tested (street set, rented machine, round 6) - plain numbers

Round 6 is the last full round. The files are in the work folder: `measures_r6.json` (everything below), `period_r6.json` (the shares), `selftest_ground.json` (the self-tests).

### Sett joints (P1) - nearly met

21 of 22 lighting pictures pass with the kit's own dots left in (the frozen baseline: 20 of 22). The one that fails is the heavy-rain lockout picture (it failed before as well). 20 pass with every dot counted. With the kit's own dots left out as well, 19 pass; the line asks for the baseline's 20, so that line is NOT met (the verdict says `without_kit_equals_base: False`). The highest joint contrast next to the camera is 0.622 (limit 0.75). The 22 pictures:

''' + table + '''

### Wet look (P2) - NOT met

The road's wet-to-dry ratio is within 0.05 of the baseline in 11 of 16 pictures and outside it in 5 (for example 3.387 against 3.665 in the strongest light, 2.487 against 2.581 in the close picture). Pavement and kerb are inside. The first round had 6 road pictures outside; halving the dulling brought it to 5, and I stopped there. On top of that, the line that asks each element's own dots to be no brighter wet than dry fails for all four layers (ratios from 1.0 to 3.5, 40 lines). One more line fails that I cannot explain: the highlight share of the main picture in light C (0.0347 against the 85 to 115 percent window). Total lines failing in P2: 44.

### Readable at the painter's size (P3) - NOT met, except two rows

(Measured on each element's own part picture at the painter's scale 0.45, then 0.40: at least 60 percent of the marks GOOD, at most 15 percent LOST, at most 15 percent crushed, and the minimum number of GOOD marks.)

- All crack parts together (the foundation's row, first 15 m): main 110 marks, 26 good (24 percent), 58 lost (53 percent); lockout 124 marks, 17 good (14 percent); notice 139 marks, 75 good (54 percent), 43 lost (31 percent). FAIL on all three plates; the notice plate is the closest.
- Flag cracks (fine and broken) alone: no marks at all on the main and lockout plates (the flags in view within 15 m are too few and too small for a period share of cracks to land on them), 14 marks on the notice plate, 2 good. Tilted flags and chipped corners: none on any plate. This is what the plates can show with the period caps kept; the close views show them.
- Kerb chips, open kerb joints: passes on the notice plate (15 marks, 13 good), main 0 marks, lockout 2 marks.
- Disturbed setts and open sett joints: main 110 marks, 26 good; the soft sunk patches are the lost ones.
- Tar: passes on the notice plate (1 patch, good); main 2 marks, 1 good; lockout 2 marks, 0 good.
- Film, polish and water marks (tone only): main 680 marks, 59 good. The film and polish are broad soft tone shifts and the measure counts them as lost, so this row cannot pass by design: read it as "tone present".
- Rust halos, drum ring, scrubbed strips: 3 to 10 marks per plate, 0 to 3 good (need 4).
- Moss ribbons and algae: main 67 marks, 4 good (need 8); lockout 1 good (need 4); notice 11 good.
- Rust on iron: 0 marks on the main and lockout plates, 2 (none good) on the notice plate (need 4). The rust shows in the close views; on the plates the iron is small.

### Period caps (P4) - inside, with two exceptions

Counted on plan pictures from straight above (`period_r6.json`, 2 cm per dot):

| element | measured | cap |
|---|---|---|
| flags with fine cracks (share of flag area) | 10.4 % | 8 to 15 % |
| flags with broken cracks | 2.5 % | 2 to 4 % |
| tilted flags | 3.2 % | 3 to 6 % |
| kerb chips (share of kerb length) | 31 % | 20 to 35 % |
| setts disturbed (share of road area) | 4.9 % | 3 to 6 % |
| open sett joints (share of joint area) | 15.7 % | 10 to 20 % |
| tar (share of the road) | 0.7 % | at most 4 % |
| tar patches in the first 30 m | 2 | 1 to 3 |
| moss in kerb and gutter joints (share of joint length) | 10.6 % | 5 to 15 % |
| moss in road joints / in pavement joints (any joint length at most 15 %) | 11.7 % / 10.9 % | at most 15 % |
| liverwort patches | 0 | 0 to 2 |
| algae fans | 0 | at every pipe outlet: NOT met |
| chipped flag corners (5 to 10 % of flags) | not measured | |

### Not one dark mush (P5) - nearly met

Main, notice and close_road plates: every line passes (plate mean ratio 0.989, 0.987, 0.976). Lockout plate: the road is 0.45 percent brighter than the baseline in the 5 to 10 m band (1.0045; the line is 0.80 to 1.00), the rest passes. Earlier rounds showed why this line is touchy: before the even dust and the soot on iron were added, rust and polish made the road and the iron 0.2 to 1.4 percent brighter in several bands.

### Zones (P6) - met

Painted moss is 0.0 percent of the crown, the lanes, the fire zone and the doorstep strips on the street and lockout pictures (limit 0.2 percent).

### Drawing time (P7) - inside the whole line, over my share

All four ground layers alone: the street plates take 7.53 s against 5.92 s (1.27 times; the line is 1.30), the first picture 2.96 s against 2.26 s (1.31 times; the line is 1.5 and 40 s). Lockout: plates 2.64 s against 2.25 s, first picture 2.54 s against 2.47 s. My share was meant to be +8 percent of drawing time: it is +27 percent, which leaves the other builders only 3 percent before the whole line is crossed. No 3D pieces are added.

### Self-tests (P8)

`selftest_ground.json` (street and lockout, all four layers): each layer acts on strong dial values; at amount 0 and with the master dial at 0 the picture equals the plain one within the plan's line (at most one 8-bit step on at most 1 percent of dots; worst measured 0.03 percent of dots, biggest single difference 0.0118 on a 0 to 1 scale); alone a layer changes only the dots of its own roles; taking a layer out (in another order, twice) restores every material exactly; two draws of the same picture are the same within noise; every layer goes in and out without a crash. NOT identical in 16 bit: the renderer's own noise is of the same size (two draws of one picture differ by up to 0.0004, the layers' amount-0 difference is up to 0.012).

The courtyard (dirt and moss only; the cracks and iron layers have no roles there and the test says so): the first run failed the isolation test for the dirt layer, because a layer that carries only tonal elements gave an empty Mask. I fixed `finish_parts` (a layer with only tonal parts now reports them as its whole Mask) and repeated the run: see `selftest_ground.json`, keys `courtyard` (first run) and `courtyard_after_fix`.

## What is not finished (the honest list)

- The algae fans under the downpipes never appeared in any picture (the masks that should place them are there; the fan comes out 0 everywhere; not found in time). Liverwort: also none.
- At close range several elements are very subtle (film, polish, the rust halo, tar on a dark wet road): the dial sheet shows it. The ones that show clearly are the moss ribbons, the flag cracks, the kerb chips, the sunk and tilted setts and all the iron.
- The preset file wins over a default written by the layers, so the tuned values I would like (more cracks near the camera, `near_only` 20 m, `polish_lift` 0, `rust_cover` 0.5) are listed in `looks_ground/sooty_1926.json` under `_proposed` and in REQUESTS.md; they need the integrator.
- The wet look (P2) and the plate readability (P3) are open, as above.
'''
open(p, 'w').write(head + tail)
# repair the earlier part: words lost to the shell the first time
s = open(p).read()
print(len(s))
