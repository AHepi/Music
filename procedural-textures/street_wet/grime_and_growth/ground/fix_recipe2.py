import os
WG = os.environ['WG']
p = os.path.join(WG, '14 Recipe - ground - how it is made.md')
s = open(p).read()
def sub(old, new):
    global s
    assert old in s, old[:70]
    s = s.replace(old, new, 1)
sub("Round 6 is the last full round. The files are in the work folder: `measures_r6.json` (everything below), `period_r6.json` (the shares), `selftest_ground.json` (the self-tests).",
    "Round 7 is the last full round (rounds 6 and 7 gave the same numbers except the drawing time and the algae). The files are in the work folder: `measures_r7.json` (everything below), `period_r6.json` and `period_r7.json` (the shares), `selftest_ground.json` (the self-tests).")
sub("(street set, rented machine, round 6)", "(street set, rented machine, round 7)")
sub("| liverwort patches | 0 | 0 to 2 |\n| algae fans | 0 | at every pipe outlet: NOT met |",
    "| liverwort patches | 1 | 0 to 2 |\n| algae fans (patches on the plan picture, after the outlet reach was widened to 0.7; the pipe feet are 5 on the left, plus the lamp posts) | 4 | at every pipe outlet: NOT clearly met (see the end) |")
i = s.index('### Drawing time (P7)')
j = s.index('### Self-tests (P8)')
s = s[:i] + '''### Drawing time (P7) - inside the whole line on the street, one first picture over on the lockout

All four ground layers alone, last round: the street plates take 7.44 s against 5.92 s (1.26 times; the line is 1.30), the street's first picture 2.65 s against 2.26 s (1.17 times; the line is 1.5). Lockout: plates 2.73 s against 2.25 s (1.21 times), first picture 6.38 s against 2.47 s (2.6 times: over the 1.5 line; the round before it measured 2.54 s on the same picture, so the first picture swings with the machine and the shader cache; a first picture costs about 4 s more when the shaders have to be compiled). My share was meant to be +8 percent of drawing time: it is +26 percent, which leaves the other builders only 4 percent before the whole line is crossed. No 3D pieces are added.

''' + s[j:]
sub("`selftest_ground.json` (street and lockout, all four layers)", "`selftest_ground.json` (street, lockout and courtyard; the street was run again after the last code change, key `street`; the first street run is `street_round6`)")
i = s.index('## What is not finished')
s = s[:i] + '''## What is not finished (the honest list)

- Algae fans: with the first outlet reach (0.3) they came out empty on every plan picture; with 0.7 the plan pictures show 4 fans and 1 liverwort patch, but in the drawn pictures (a lamp post foot where a fan sits) the picture does not change (changed share 0.0000 at a threshold of 8/255): the algae colour keeps the stone's brightness and the tint is too small to show at plate or close-view size. So "algae at every pipe outlet" is placed, not seen. Not fixed.
- At close range several elements are very subtle (film, polish, the rust halo, tar on a dark wet road): the dial sheet shows it. The ones that show clearly are the moss ribbons, the flag cracks, the kerb chips, the sunk and tilted setts and all the iron.
- The preset file wins over a default written by the layers, so the tuned values I would like (more cracks near the camera, `near_only` 20 m, `polish_lift` 0, `rust_cover` 0.5) are listed in `looks_ground/sooty_1926.json` under `_proposed` and in REQUESTS.md; they need the integrator.
- The wet look (P2), the plate readability (P3) and the drawing time of the first lockout picture (P7) are open, as above. P1 without the kit's own dots is one picture short.
- The first street self-test and the round-6 numbers were taken before three small code changes (a layer with only tonal parts reports them as its Mask, the algae outlet reach, the position grid for flags); the final street self-test and round 7 were taken after all of them. The courtyard self-test ran after the first change and before the outlet reach change (a default of an extra dial that the courtyard does not use).
- Not measured: the share of flag corners with a chip (5 to 10 percent): no picture of it was made; the courtyard was not measured against the readable and drawing-time lines (it has no plate camera yet).
'''
open(p, 'w').write(s)
print(len(s))
