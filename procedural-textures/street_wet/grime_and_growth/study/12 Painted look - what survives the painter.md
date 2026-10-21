<!-- NOTE (plain words): a measuring study (21 October 2026) of what the painter (the image program Flux 3 edit on fal) keeps when it repaints a plate, and what the film's stage then does to the painting. It was done to give the weathering kit (grime, cracks, stains, weeds, moss) targets that can be measured in a plate: how small, how faint, how dark, how much. Words used: "plate" = the picture drawn from the 3D set in Blender that the painter repaints, 1536 x 2730 dots; "painting" = what the painter sends back, lined up on the plate; "stage" = the film's program that shines the painting back on the 3D set; "mark" = one separate small thing in a picture (a crack, a speck, a chip, a moss dot, a weed tuft); "width" = the narrow side of a mark in plate dots at 1536 wide (a dot = a pixel); "contrast" = how much brighter or darker a mark is than the ring of surface around it, on the picture's own 0 (black) to 1 (white) brightness scale, measured on the saved picture's numbers (so 0.05 means five hundredths of the way from black to white); "come back" = the painting has the same mark in the same place (+-2 dots) with at least half the plate's contrast and at least 0.02, and more than 90 % of what the painter's own brush marks give by chance at other places; "sent at 0.53" = the plate was shrunk to 810 x 1440 before it went to the painter (the way both wet tests were done), "sent full size" = 1536 x 2730 (the way the three old dry paintings were done); "film black" = a brightness that arrives on the film as under about 0.03. No paid painter call was made for this study. Nothing in the film project, set_copy, tools, relief_and_rubbish, painter_round_2 or painter_test was written to (they were only read). All numbers were measured by me with the scripts in painted_look/scripts; the plates and paintings used are listed in section 2. -->

# 12 Painted look - what survives the painter

## 1. The short answer

**What reads in the finished film is what survives two filters in a row: the painter, then the film's own finishing step.** I measured both on five plate and painting pairs (three old dry paintings, two wet rounds) and on the film's own stills. The numbers a builder can check in a plate:

| what | target in the plate (1536 x 2730; the painter gets it at about 0.5) | why (section) |
|---|---|---|
| **Marks** (chips, specks, moss dots, weed tufts, rust specks) | width **5 dots or more and contrast 0.08 or more** comes back about 80 % of the time. 8 dots wide needs 0.05, 12 dots wide needs 0.04. 3 dots wide needs 0.12. Under 3 dots wide: treat as texture, it will not be kept (2 dots needs 0.17). | 4, 5 |
| **Lines** (cracks, drips, thin streaks, joints) | width **3 dots and contrast 0.11**, or **5 dots and 0.08**, or 8 dots and 0.055, or 12 dots and 0.04. A hairline of 1 to 2 dots is lost unless it is very strong (0.14 or more). | 4, 5 |
| **Patches** (soot masses, soft stains, damp, moss patches) | **15 dots or wider, contrast 0.04 or more** (0.06 to be safe). They come back in place at about 1.3 times the plate's contrast (0.9 to 1.8). | 4, 5 |
| **Nothing under 0.03** | A mark fainter than 0.03 (and narrower than 8 dots) comes back only 11 to 38 % of the time, no better than the painter's own brush marks give by chance: it is gone, whatever its size. | 5 |
| **Darkest value that is not crushed** | Painted 0.135 arrives on the film as 0.07 to 0.085, painted 0.12 as about 0.05, painted 0.10 as 0.015 to 0.03, painted 0.08 and under as black. So in the plate **keep the darkest part of anything you want seen at 0.10 to 0.12 or more**, and its surround at 0.18 or more. | 6 |
| **Walls of the lockout street** | They are already too dark to take dark grime: 57 to 83 % of their plate dots are under 0.13. Weather the walls with pale or coloured grime (salts, lichen, rust runs, moss), or only on their lit parts. | 7 |
| **How much is too much** | Dark grime on a surface: **about a quarter of its area and a darkening of about a third (to 65 %)** still reads as dirty but legible; **45 % of the area at half brightness is mush** (a fifth to a quarter of the walls turn black, brick courses vanish). | 8 |
| **Order of importance** | 1 big tonal masses, 2 colour accents, 3 a few clean cracks and joints, 4 grit and chips near the camera, 5 weeds as tufts, 6 anything finer: skip. | 9 |

**Four things that surprised me:**
1. **The painter keeps what it can see and ignores the rest.** Marks of 5 dots and 0.08 come back as inked, slightly stronger marks (about 1.1 to 1.3 times the contrast). Marks under 0.03, or under 3 dots wide, are replaced by the painter's own brushwork. Most of a plate's natural fine texture (87 % of the 3,320 marks, 0.03 deep or more, that a scan finds on the walls of the round 2 plate) is in that lost group, and that is fine.
2. **The painter's treatment of darks is not stable.** A wall dot of 0.07 in the plate came back as 0.12 in the first wet painting, and as 0.175 and 0.18 in the second wet painting and the old dry one. So no dark detail should depend on the painter either keeping or rescuing it.
3. **The film's finishing step works like a gate at painted 0.10 to 0.13.** Anything painted under 0.10 is black on the film, whatever is in it.
4. **In the far third of the road the painter makes up its own sett texture** (2 to 6 times the plate's energy, correlation with the plate only 0.3 to 0.6). Detail planted there is not reproduced; spend nothing on it.

**Not done, and the one cheap test that would settle most of the open points** (section 13): no plate has ever had moss or weeds, so colour and weed survival are inferred, not seen. One repaint of a plate with a chart of test patches (a grid of widths and contrasts, in grey, rust and green) would replace my extrapolations with measured numbers.

---

## 2. What I looked at

**Plate and painting pairs** (all lined up locally: the film's tool fixes stretch and shift for the whole picture only, so I corrected the remaining 1 to 3 dots of drift tile by tile; afterwards the leftover drift is 0.8 to 1.4 dots at the 90th percentile; `scripts/a2_register_all.py`):

| pair | plate | painting | plate sent at | what the plate has |
|---|---|---|---|---|
| lockout, dry (14 Oct) | `plan3/assemble/round3/plate.png` | the film's `lockout-painted.jpg` | full size | dry street, soot ring round the drum, brick and stone texture |
| notice corner, dry | `plan3/corner/final/notice-corner-plate-3.png` | the film's `notice-corner-painted.jpg` | full size | pavement flags with real cracks, pale stains, specks; setts; brick |
| people test, dry | the film's `people-test-plate.jpg` | `people-test-painting.png` | full size | the same street at another lens |
| lockout, wet, round 1 (20 Oct) | `street_wet/work/r35/main_wet_plate.png` | `painter_test/pictures/wet_painting_lined_up.png` | 810 x 1440 (0.527) | wet look, no joints layer, no rubbish |
| lockout, wet, round 2 (21 Oct) | `painter_round_2/plate/lockout_plate_wet_round2.png` | `painter_round_2/paint/front_painting_lined_up.png` | 810 x 1440 (0.527) | wet look, JOINTS layer, rubbish pieces and painted muck, the brief says "keep the small rubbish" |

The second round's painting existed while I worked (made 06:41, one call), so it is included. It is the closest thing to the next painting: a plate with real small marks painted at the size the next rounds will use.

**Also read:** the 20 backgrounds of the series (chapters 1 and 2, made by the painter from words, not from plates) to see its own hand with grime; the style picture (found at `plan3/assemble/style-glasgow.jpg`, which the first wet test could not find); the film's stage code (`cinema-stage.js`, `lockout-test.js`) and its stills from the first wet test (`painter_test/stage/stills`), to measure what the stage does.

**Not available:** any plate that had moss, weeds, cracks drawn by a layer, or stains drawn by a layer. The "marks" I measured are the natural small features of the existing plates: pavement cracks and specks, setts and joints, brick and stone texture, rubbish, rust, soot.

---

## 3. How I measured (so the numbers can be repeated)

1. **Find the marks in the plate.** A dark mark is a place darker than its surroundings by 0.03 or more at a scale of up to 17 dots (a standard "top-hat" test: close the picture with a disc and subtract); a bright mark the same the other way. Each mark is one connected piece. For each: **width** (twice the biggest distance to its edge), **length** (long side of its smallest box), **contrast** (mean of the ring around it minus mean of the mark; sign made positive). A mark at least 4 times longer than wide is a *line*, under 2.5 times a *speck*.
2. **Look for it in the painting.** The painting's contrast on the same shape, the best of 25 positions within 2 dots (the painter moves things a little).
3. **Chance level.** The same test on the same shape moved to 12 other places 35 to 90 dots away. A mark **comes back** when the painting's contrast is at least half the plate's, at least 0.02, and bigger than 90 % of the 12 chance values. (The painter's brushwork alone beats "0.02" in 12 to 70 % of random places, which is why I do not count a mark as kept just because something dark is nearby. My first try did exactly that and said 95 to 100 % for everything; I threw it away.)
4. **Smooth fit.** 17,942 marks from the full-size pairs and 8,624 from the two wet pairs were found; for each kind (speck, line) and each plate size, a logistic fit of "comes back" on ln(width) and ln(contrast), using the marks with contrast 0.02 to 0.30 and width 1 to 30 (3,667 specks and 2,025 lines full size; 1,632 specks and 1,686 lines wet). It reproduces the binned counts (`numbers/c11_logistic_printout.txt`, check lines under each fit).
5. **A fair test of the fit.** I fitted it on round 1 only and asked it about round 2's marks, which it had not seen. Marks it called **GOOD** (80 % or more) really came back **95 %** (specks) and **75 %** (lines) of the time; called **RISKY**: 60 % and 47 %; called **LOST**: 21 % and 16 % (`scripts/c14_holdout.py`). So the fit is fair for specks and a little optimistic for lines (about 10 to 15 points).

Everything is brightness only (Rec.709 weights on the saved picture's numbers), the way the earlier tests measured it.

---

## 4. What the painter does to each kind of thing

Pictures are at 100 %, plate on the left, painting on the right.

![cracks, pale stain, specks, soot ring](12%20Painted%20look%20-%20crops/12-fig1-flags-cracks-stains-specks.jpg)

![soot ring round the drum](12%20Painted%20look%20-%20crops/12-fig2-soot-ring-round-the-drum.jpg)

* **Cracks (dark lines) in the notice corner flags:** kept in the same place (within 1 to 2 dots), drawn as a dark inked line. The big crack in the picture is 0.088 deep in the plate and 0.147 in the painting, 12 dots wide at half depth in the plate and 11 in the painting (an average over 100 rows of a wavy crack). Hairlines of 1 to 2 dots with contrast under 0.05 mostly vanish or are replaced by a painted scratch somewhere near.
* **Pale stains on the flags:** kept as soft patches in the same place, painted with visible brush strokes, with the strongest spots turning into white paint strokes. Measured on the 8 strongest soft pale blobs of the flags at two scales (`scripts/c15_soft_blobs.py`): the painting's contrast is 0.9 to 1.8 times the plate's, median 1.3; the 6 darkest soft blobs 1.0 to 1.4, median 1.3. The white strokes you see are the strongest bits of that, drawn with a loaded brush; on average the stains do not get much stronger.
* **Soot ring round the drum (dry painting):** the plate already has a soft dark ring (it was not invented). The painter makes it a flat patch with a hard edge and adds dashes and flecks of ink round it that are not in the plate. So **soft grime comes back harder-edged and with extra flecks.**
* **Specks and chips (round 2, plate sent at 0.53):** cinders and chips of 5 to 25 dots come back as inked dark blobs with a white glint, in the right places, a little rounder and more even than the plate. Dust and fine grit at the foot of walls (2 to 4 dots) comes back as scattered dots, not the plate's dots.

![round 2 rubbish](12%20Painted%20look%20-%20crops/12-fig3-round2-rubbish-chips-and-joints.jpg)

* **Sett joints:** with the JOINTS layer in the plate (round 2) the painter followed the grid. Correlation with the plate at the scale of a joint (a band of 1.6 dots) is 0.82 to 0.86 out to about 15 m, 0.78 at 20 m, 0.69 at 30 m (the dry painting 0.77 to 0.81 to 10 m, 0.74 at 15 to 20 m). Without joints in the plate (round 1) it is 0.50 to 0.60 near and the painter draws joints of its own. Rows of joints across the street are under one dot thick beyond about 10 m (1.6 cm x 53 dots a metre) and under half a dot beyond about 13 m (1.6 cm x 36 dots a metre), yet the grid still reads: it comes from the lengthwise joints (3 to 5 dots wide at 10 to 16 m) and the painter's own pattern.
* **The far third of the road:** the plate has little there (energy 0.004); the painter fills it with 2.7 to 6 times that energy, correlation with the plate 0.3 to 0.6. **It is the painter's own.**
* **Fine texture** (brick grain, stone grain, hessian weave, 2 to 3 dots): replaced by brushwork. Correlation of the 3-dot band with the plate is 0.26 to 0.69 over roads, pavements and walls (0.31 on the dry painting's walls, 0.50 on round 2's), and the painting has 1.1 to 2.3 times the plate's energy there (6 times on round 1's far road): it is mostly the painter's own. At 6 dots the correlation is 0.46 to 0.89, at 12 dots mostly 0.8 to 0.95 (0.5 to 0.7 on the far and near wet road and the dry walls), at 24 and 48 dots mostly 0.86 to 0.97 (the exceptions are the dry painting's walls, 0.66 to 0.68, where the painter redrew the stonework, and the wet road, 0.53 to 0.71): **things 12 dots or wider are mostly kept** (`numbers/b2_band_transfer_printout.txt`; the band is a difference of two blurs, "3 dots" means features about 3 dots wide).
* **Wall foot:** the painter does not darken it by itself. Foot brightness over mid-wall brightness: dry 0.72 in the plate, 0.76 in the painting; round 1 0.61 and 0.62; round 2 0.62 and 0.75 (it lifted it). So the "dark plinths" of the old dry painting are in the plate; and dark grime at a wall foot loses a third of its contrast to the painter's lifting in round 2.
* **Colour:** the painter weakens colour. Red and orange saturation in the plate to the painting: 0.46 to 0.21, 0.36 to 0.19, 0.50 to 0.43, 0.38 to 0.24, 0.48 to 0.31 (in the order lockout dry, notice corner, round 1 wet, people test, round 2 wet). Blue: 0.47 to 0.44, 0.46 to 0.29, 0.47 to 0.42, 0.45 to 0.25, 0.41 to 0.17. Hue moves only 0 to 10 degrees (once 32 degrees, for the reds and oranges of the old dry lockout painting), except dark olive and yellow-brown (hue 40 to 75, brightness 0.13 to 0.16), which stayed in its family only 0 to 26 % of the time: it went grey-teal or pale and weak (`numbers/e1_hue_printout.txt`). There is almost no green in any plate (under 1,500 dots), so I could not test green directly.
* **It invents other things too** (sky clouds, smoke) but, in these pairs, not surface grime, except the flecks round the soot ring.

**The series' own hand with grime** (the painter painting from words only):

![series paintings](12%20Painted%20look%20-%20crops/12-fig4-the-series-own-grime-hand.jpg)

Soot is a dark mass on the tops and sides of piers and chimneys, with blunt drips; grit is a scatter of pale and rust-coloured round blobs of about 6 to 14 dots at 1536 wide, with ink rims; damp walls are large vertical dark and pale strokes with hairline cracks drawn as 1 to 2 dot dark lines; puddles are flat sheets. **I saw no moss and no weeds in the contact sheet of the 24 backgrounds** (looked at small, so a few small tufts could be missed), and green is under 2 % of most of them. Where green is painted on objects it is dark, weak and teal-leaning: median hue about 150 to 165 degrees, saturation 0.20 to 0.36, brightness 0.23 to 0.39 (parliament benches, conference table, council-house hedges; some of the teal in the measure is sky); only the farmland picture (hue 79), the noodle shop (hue 93) and the NZ suburb (hue 127) show yellow-green foliage (`numbers/e2_series_greens.txt`).

---

## 5. How small and how faint (the numbers behind the table)

Share of marks that come back, from the fit (width in plate dots at 1536, contrast as defined above):

![survival map](12%20Painted%20look%20-%20crops/12-fig6-survival-map-width-by-contrast.jpg)

Contrast needed, **plate sent at 0.53** (this is the case the next rounds use):

| width | specks: 50 % | specks: 80 % | lines: 50 % | lines: 80 % |
|---|---|---|---|---|
| 2 dots | 0.079 | 0.166 | 0.066 | 0.143 |
| 3 dots | 0.056 | 0.118 | 0.050 | 0.109 |
| 4 dots | 0.044 | 0.092 | 0.041 | 0.089 |
| 5 dots | 0.036 | 0.076 | 0.035 | 0.077 |
| 8 dots | 0.024 | 0.051 | 0.025 | 0.055 |
| 12 dots | 0.017 | 0.036 | 0.019 | 0.042 |

**Plate sent full size** (the old dry paintings): specks 80 % needs 0.065 at 3 dots, 0.058 at 5, 0.052 at 8, 0.047 at 12; lines 0.076, 0.061, 0.049, 0.041. So a full-size plate keeps 3 dot marks at about half the contrast a 0.53 plate needs; from 5 dots up the two are close.

**The painter's input size.** What the painter literally receives is the plate shrunk. Share of a mark's contrast left in the shrunk picture (measured on the round 2 plate, area-average shrinking, `scripts/c12_input_loss.py`):

| mark width | at 0.53 | at 0.45 | at 0.40 | at 0.30 |
|---|---|---|---|---|
| under 2.5 dots | 69 to 74 % | 58 to 66 % | 55 to 56 % | 35 to 37 % |
| 2.5 to 4.5 | 79 to 85 % | 71 to 78 % | 67 to 75 % | 50 to 59 % |
| 4.5 to 8 | 89 to 93 % | 86 to 91 % | 84 to 90 % | 74 to 81 % |
| 8 to 16 | 94 to 95 % | 92 to 93 % | 92 % | 86 to 87 % |

**If the plate goes at 0.4 instead of 0.5, give every contrast in the table 10 to 25 % more (3 dot marks 30 % more), or every width 25 % more.** I did not test a painting at 0.4; the 0.4 numbers are the 0.53 fit shifted by this measured loss. They are an extrapolation.

**Where the evidence is thin:** high contrast (over 0.14) is rare in natural plate marks, so the top of each column rests on few marks (8 to 30 per cell); widths of 2 dots and under, and over 16 dots, are outside what I measured (patches I measured in a different way, below). For patches (15 dots and wider) there are two views. The mark test fits widths up to about 14 dots and says 80 % at contrast 0.036 to 0.047 (12 dots). A second, stricter test (the share of "feature pixels" of 17 to 48 dots width that have a same-sign feature within 2 dots in the painting, minus the chance rate; `numbers/c3_net_tables.txt`) gives, pooled over the pairs: contrast 0.015 to 0.03: 22 to 40 %; 0.03 to 0.06: 45 to 66 %; 0.06 to 0.12: 58 to 74 %; 0.12 and over: 67 to 89 %. Large soft patches are kept at 0.9 or better correlation from 24 dots up (section 4). **I therefore give 0.04 as the floor for patches and 0.06 as the safe number.** The second test also counts the edges of bigger things (walls, props), so I trust the mark test for small things and the second only as a cross-check.

**Size in the real world (lockout camera).** Dots a metre at the middle of the street, from the camera's own maths (`scripts/g1_footprint.py`, agrees with the earlier study at 10.6 m: 325 across and 53 along, against 323 and 47):

| ground ahead | dots/m across the street | dots/m along it | 3 dots = (across / along) | 5 dots | 15 dots |
|---|---|---|---|---|---|
| 6.8 m (bottom of the frame) | 517 | 135 | 0.6 cm / 2.2 cm | 1.0 / 3.7 cm | 2.9 / 11 cm |
| 9.0 m | 383 | 74 | 0.8 / 4.1 cm | 1.3 / 6.8 cm | 3.9 / 20 cm |
| 12.9 m | 267 | 36 | 1.1 / 8.3 cm | 1.9 / 14 cm | 5.6 / 42 cm |
| 16.4 m | 209 | 22 | 1.4 / 14 cm | 2.4 / 23 cm | 7.2 / 68 cm |
| 22.6 m | 151 | 12 | 2.0 / 25 cm | 3.3 / 42 cm | 9.9 / 125 cm |
| 36.5 m | 93 | 4 | 3.2 / 75 cm | 5.4 / 125 cm | 16 / 375 cm |

Two rules follow. **Design in picture dots, not in centimetres:** a real 2 mm crack is under one dot at 9 m; to read it must be drawn 3 dots (8 mm) wide, four times too thick for the real thing. **Marks are squashed along the street:** a crack across the road needs to be 4 cm thick at 9 m and 25 cm thick at 22 m to be 3 dots; a crack along the road needs 8 mm and 20 mm. Beyond about 15 to 20 m, thin things across the road do not exist for the painter.

---

## 6. What the film does after the painter

The stage's finishing step (`cinema-stage.js`, read, not changed): the painting's colours are made linear, passed through an ACES film curve, a contrast of 1.04, a cool-shadow and warm-light tint, a lift of 0.015, back to the screen's brightness, then **dark edges (up to 30 % off at the corners), grain and a lens blur**. I wrote it out in Python (`scripts/stage_curve.py`) and checked it on the film's own stills against the paintings they show (stage zoom 1.281 about the middle, lined up by edge correlation 0.77): the written-out step is on average 0.017 to 0.02 darker than the real stills (grain, glow, haze; mean absolute error 0.018 to 0.019). Painted brightness to film brightness, measured on the stills (dry painting and wet painting give the same curve):

![film curve](12%20Painted%20look%20-%20crops/12-fig5-film-curve-darks.jpg)

| painted | 0.05 | 0.08 | 0.10 | 0.135 | 0.165 | 0.195 | 0.23 | 0.27 | 0.34 | 0.44 | 0.53 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| on the film | 0.01 | 0.01 | 0.015 to 0.03 | 0.07 to 0.085 | 0.11 to 0.12 | 0.155 | 0.215 | 0.28 to 0.29 | 0.39 to 0.41 | 0.53 | 0.64 to 0.66 |

* **Under painted 0.10 is black.** Between 0.10 and 0.13 the film goes from 0.03 to 0.07. From 0.13 up to about 0.5 the curve is steeper than 1 (1.3 to 1.6 times), so contrasts there get stronger, not weaker.
* **Scale.** The film's first frame is the plate camera with a 40 degree lens (the plate has 44), so **1 plate dot = 0.78 film dots** at the start, and 1.23 film dots at the end of the push-in (26 degree lens): marks look bigger, and borderline ones better, as the camera moves in.
* **Fine detail that reaches the film** (energy of the stage picture over energy of the painting, in bands at film dots; `scripts/b3_stage_mtf.py`): near road 0.59 to 0.61 at 2.4 film dots, 0.67 to 0.69 at 3, 0.79 to 0.83 at 4.2, 0.88 to 0.96 at 6; walls 0.66 to 0.71, 0.76 to 0.81, 0.96 to 0.99, 1.15 to 1.19; pavement 0.72 to 0.78, 0.80 to 0.87, 0.93 to 1.03, 1.06 to 1.21; middle road about 0.9 to 1.2, far road 1.0 to 1.4. So **marks under 3 film dots (4 plate dots) lose a fifth to 40 % of their contrast; from 6 film dots (8 plate dots) up, walls, pavement and the far road gain 6 to 45 % from the curve, the near road does not gain.**
* **Grain** is plus or minus 0.0175 per dot (standard deviation 0.01, less in the lights), so a mark under 0.03 and 3 dots is buried, and the video compression after that I have not measured.
* **Lens blur** at the lockout start frame is small: 0.8 film dots at 6.8 m, 0 at the focus at 9 m, 1.1 at 16 m, 1.9 at 36 m (aperture 2.5, focus 9 m), so it is not what weakens fine detail; the shrinking by 0.78 is.
* **Dark edges** take up to 30 % off the picture's brightness at the corners; since the side walls are the darkest part, they are the part pushed into black first.

---

## 7. The darkest value that is not crushed, and what the street's walls allow

**The painter's treatment of darks differs from run to run.** Painting brightness for plate dots that are 0.06 to 0.08 on a wall: dry lockout 0.180, round 1 wet 0.119, round 2 wet 0.175, notice corner 0.154, people test 0.182. For plate 0.02 to 0.04: 0.077 (round 1), 0.109 (round 2), 0.128 (corner), 0.157 (people). So in round 1 the painter kept the plate's darks (and 45 % of the wall dots ended under 0.13, which is film black or nearly: the film walls were 0.59 of their painted brightness); in the other four it lifted a plate 0.07 by 0.08 to 0.11, and only 3 % (lockout dry) and 12 % (round 2) of the wall dots are under 0.13 (corner and people test: none of the upper half).

| share of wall dots under | plate | painting |
|---|---|---|
| 0.10, lockout dry | 21 % | 2 % |
| 0.10, round 1 wet | 61 % | 23 % |
| 0.10, round 2 wet | 61 % | 6 % |
| 0.13, lockout dry | 57 % | 3 % |
| 0.13, round 1 wet | 82 % | 45 % |
| 0.13, round 2 wet | 83 % | 12 % |

The ground is much lighter: under 0.10 in the plate 0 % (dry), 5 % (round 1), 7 % (round 2); in the painting 0, 7, 1 %.

**Rules:**
1. A mark's **darker side** should be at plate 0.10 to 0.12 or more (this is what survives if the painter behaves as in round 1; if it behaves as in round 2 you get a margin of 0.05 to 0.1 for free, but do not count on it).
2. The **surround** of a dark mark should be at 0.18 or more, so that the contrast (0.08) fits above the gate.
3. **The lockout walls have no headroom.** The median wall dot in the wet plates is about 0.085 (61 % of them are under 0.10). Dark soot there is crushed whether or not it is drawn. Use pale grime (salts, whitewash, lichen), warm grime (rust runs), green (moss) or only the lit strips. The cheapest fix is a lighter wall in the plate; then dark grime has room.
4. Anything under plate 0.06 is a black hole (door, window, under the cart): leave it alone.

---

## 8. How much is too much

I laid soft synthetic soot (noise, vertical streaks on walls, blotches on the ground) on the round 2 painting at five levels, passed it through the film's finishing step (scale, curve, grain) and counted what is lost. The soot is only a stand-in for tone and area; it is not a recipe (`scripts/f1_grime_ladder.py`).

![walls, five levels](12%20Painted%20look%20-%20crops/12-fig7-grime-ladder-walls-on-the-film.jpg)

![road, five levels](12%20Painted%20look%20-%20crops/12-fig8-grime-ladder-ground-on-the-film.jpg)

| level | area covered, darkening | walls: film black (under 0.03) | road: film black | structure kept, walls / road (correlation of the 3 to 10 dot detail with the clean film picture) |
|---|---|---|---|---|
| 0 none | 0 | 7 % | 3 % | 1.00 / 1.00 |
| 1 light | 10 %, to 80 % | 8 % | 4 % | 0.99 / 1.00 |
| 2 medium | 25 %, to 65 % | 11 % | 6 % | 0.93 / 0.97 |
| 3 heavy | 45 %, to 50 % | 23 % | 13 % | 0.80 / 0.90 |
| 4 smothered | 70 %, to 40 % | 44 % | 29 % | 0.68 / 0.76 |

By eye: level 1 is invisible, level 2 is clearly dirty and still legible (brick courses, window frames and sett joints are still there), **level 3 is where the brick and the setts start to go (soot reads as black drapes) and level 4 is mush.** So:

* **Budget for dark grime on one surface: no more than about 25 % of its area at no more than about 35 % darkening; keep the surface's film-black share (painted under 0.10) at or under about 15 % for walls and 10 % for ground, and its structure kept at 0.9 or better.** In round 2's painting the walls were at 6 % and the ground at 1 % (painted under 0.10), so there is room; in round 1's walls were at 23 % and there was none.
* The budget is for the part of the grime that is above the gate: soot put where the wall is already under painted 0.12 uses none of it and shows nothing.
* **Pale and coloured grime has a different budget**: it is not crushed. I did not run a ladder for it; my guess is that over about 20 % of a surface the pale patches start to read as a second surface rather than as weathering (not tested).
* **Count marks, too.** A plate with hundreds of chips of 5 dots and 0.08 would be accepted by every number above and still look like noise; in the series' own pictures grit is sparse blobs (I did not count them). I did not measure a limit for this. Round 2's plate (rubbish amount 1.4, patchiness 0.7) came back looking right in the crops I viewed (section 4), so the street's present amount is at least a known good.

---

## 9. Order of importance for the viewer

The viewer sees 1080 x 1920 at phone size, a moving picture, for a few seconds. In that order of what they can see, and what the painter and the film keep:

1. **Big tonal masses with a clear shape**: soot on tops, ledges, chimney, drips of 8 to 20 dots wide, the damp, dark foot of a wall, wet patches. Seen at once; kept at 0.9 correlation; the painter even enlarges their edges. Budget: section 8.
2. **Colour accents of 15 dots and more**: rust runs, moss patches, lichen, pale salts. Colour is the thing the brown and blue palette of these pictures lacks. The painter weakens colour (0.4 to 0.9 times the saturation) and moves dark olive to grey, so make them stronger than wanted (section 11).
3. **A few long, clean cracks and joint lines** in the first 15 m: 3 to 5 dots wide at 0.08 to 0.11. They come back as inked lines and tell the viewer "old". Many short cracks do not read: they are individual 1 to 2 dot marks.
4. **Grit, cinders, chips, litter near the camera and at the wall foot** (5 to 25 dots, 0.08 or more): each becomes an inked blob with a glint; the rubbish round 2 shows it works. A few dozen are enough.
5. **Weeds as tufts** (5 dots and wider, 0.08, in a colour that is not the ground's), only at the wall foot and in joints in the first 10 to 15 m. Single blades (1 to 3 dots) are lost.
6. **Everything finer**: hairlines, dust speckle, grain, pitting, stone and brick micro-texture. **Skip it**: the painter replaces it with its own, and the film's grain would bury it anyway.

---

## 10. Targets for a builder, and the script that measures them

**Per layer** (all in plate dots at 1536 wide; contrast as defined; set for a plate sent at 0.5; at 0.4 add 25 % to every width):

| layer | element | shape | minimum width | minimum contrast | notes |
|---|---|---|---|---|---|
| grime | soot masses, wet foot, soft darkening | patches, drips of 8 to 20 dots | 15 | 0.04 (0.06 safe) | keep the darker side at 0.10 to 0.12 or more; at most about 25 % of a surface at about 35 % darkening; on dark walls use pale or coloured grime |
| cracks | long clean cracks and joints | lines | 3 (at 0.11) / 5 (at 0.08) | 0.08 to 0.11 | a few, in the first 15 m; draw them thicker than real; across the street they must be 4 cm thick at 9 m |
| stains | rain streaks, rust runs, lime, damp | soft streaks and patches | 8 to 15 | 0.04 to 0.05 | the painter keeps them in place and about 1.3 times stronger |
| weeds | tufts at wall foot, kerb, joints | specks | 5 | 0.08 (0.05 if 8 wide) | not single blades; strongly different from the ground in colour; first 10 to 15 m only |
| moss | patches, edges of stones, between setts | patches 15 and up, dots 5 and up | 15 (patch) / 5 (dot) | 0.04 (patch) / 0.08 (dot) | lighter than the stone when the stone is dark; saturation 0.45 or more (section 11) |
| rubbish (existing) | chips, cinders | specks | 5 | 0.08 | confirmed by round 2 |

**The script `painted_look/tool/plate_detail_check.py`** does the measuring for any plate: with the mask picture of one layer (white = where its marks are) it reports for each mark its width, contrast, the surround's brightness, and GOOD / RISKY / LOST; without a mask it scans the plate. It also adds the share of a surface (a second mask) that is darker than 0.08, 0.10 and 0.12, writes a JSON report and an overlay picture (green good, amber risky, red lost, blue outline = a dark mark on a surround under 0.12). It needs only Python with numpy and opencv, runs in about 2 seconds per plate, and works on a plate of any size (it measures at 1536 wide). Run line:

```
python3 -I plate_detail_check.py PLATE.png --mask LAYER_MASK.png --painter-scale 0.5 --surfaces WALLS_MASK.png --out report.json --overlay overlay.jpg
```

I tested it on the round 2 plate with a made-up mask of dark chips (1,810 marks: 191 GOOD, 519 RISKY, 1,100 LOST at 0.53; 154, 426, 1,230 at 0.4), with a half-size copy of the plate and its mask (it gives the same kind of answer: 87 GOOD, 252 RISKY, 1,143 LOST of 1,482), and as a scan of the walls (107 of 3,320 marks GOOD, 2,895 LOST, and 52 % of the wall dots under 0.08, 68 % under 0.10, 80 % under 0.12). I did not test it on a real layer mask, because none exists yet. It belongs in the kit's `harness`; the fit file `painter_survival_fit.json` must stay beside it.

---

## 11. Colour: moss and weeds

Known: the painter's saturation is 0.2 to 0.9 times the plate's, hue moves 0 to 10 degrees except dark olive and yellow-brown, which go grey or teal. The series paints green dark, weak and teal-leaning (hue 150 to 165, saturation 0.2 to 0.36, brightness 0.23 to 0.39) except for a farmland picture and a suburb picture.

Not known: what the painter does to a green moss patch in a plate. No plate has had green. So: **put moss and weeds in the plate stronger and lighter than the finished look, and plan to check one painting.** Starting values: hue 85 to 120 degrees (yellow-green, so a drift toward teal still ends in green), saturation 0.45 or more, brightness 0.25 to 0.45 (lighter than the stone, because anything painted under 0.12 is black on the film), the patch 15 dots or wider, contrast against the stone 0.06 or more in brightness as well as in colour. Add one sentence to the brief, in the style that worked for the rubbish in round 2 ("Keep the small rubbish where image 1 has it"): *keep the green moss and the weeds where image 1 has them, green and not grey-blue, at the same size and strength*. It is not tested.

---

## 12. What carries over to the Japanese forecourt

* **All the dot numbers carry over**: they are about the plate and the painter, not about the street. What changes is how many dots a thing is: use the camera's own maths (section 5) for the courtyard's cameras. A raked gravel line 1 cm wide is 5 dots at 7 m in a camera like the lockout's and under 3 dots beyond about 11 m (looking along the lines; across them the picture is squashed several times more), where the painter will paint its own raking; pebbles, moss on stepping stones, lantern moss and tile soot are all patches or marks in the sizes above.
* **The headroom is likely bigger**: a daylit courtyard with light gravel and stone has surfaces at 0.3 to 0.5, so dark grime there is above the gate; the budget of section 8 is about areas and darkening and still applies; measure it with the script's `--surfaces` mask.
* **The set's own style prompt may change the painter's habits** (the street brief says wet, dusk, blue-grey). Moss in a green courtyard is the case where my colour doubts matter most.
* **No courtyard plate exists yet**, so none of the numbers were measured on it.

---

## 13. What I tested, what I did not, what I am unsure of, what went wrong

**Tested:** five plate and painting pairs (four different plates, two of the five wet at 0.53); 26,566 marks found, a fit on the 9,010 of them that are clear specks or lines in range, and a hold-out test of it; the film's finishing step against two stills; the stage's loss of detail by region; the sett grid by distance; hue and saturation; the film's response to synthetic grime at five levels; the plate-measuring script on three inputs.

**Not tested:**
* **No painter call.** Moss, weeds, drawn cracks and drawn stains have never been painted from a plate, so their survival is inferred from natural marks of the same size and contrast, and their colour from numbers about other colours.
* **Plate sent at 0.4.** Extrapolated from 0.53 and the measured shrinking loss.
* **How repeatable the painter is.** One draw per pair. The darks differ by run (section 7); other things may too.
* **Full films**: only stills at the first frame; no look at moving frames; no video compression.
* **Pale grime budget**, **many-marks budget** (section 8).
* **Cycles plates or other lighting**: the plates are EEVEE.
* **The notice-board close shot**, other lenses, a phone screen.

**Unsure:**
* My "comes back" test is mine: the half-contrast and 0.02 rules and the 90 % chance rule were chosen by me. Other choices shift every threshold (a stricter test raises them). The ratios between sizes and between the two plate sizes should hold better than the absolute numbers.
* The fit is a straight line in the logarithm of width and contrast; outside the measured range (2 dots, over 0.14, over 16 dots) it is a guess.
* Natural marks are not weathering-layer marks: layer marks may be more regular, which the painter could treat differently (for example, a mask of uniform dots might be taken as texture).
* The contrast of marks is measured on brightness only; a green mark of the same brightness as the stone has contrast 0 here and could still read by colour.
* The synthetic soot is soft noise; real soot recipes with sharp edges may cost the budget differently.

**What went wrong on the way** (and was fixed):
* My first survival test (`c1`, edges and chance included) said 95 to 100 % for nearly everything; the painter's own brushwork is dense enough to pass it. I replaced it with the shape-specific test with a chance level (section 3); the first is kept only as a cross-check.
* My first components test (`c6`) had the same fault; deleted.
* The region masks I first used (the "solo" pictures of the earlier job) include ground behind the props, so the sacks and the drum counted as road. I redid every region number with the visible-surface masks.
* My first stage check lined the painting up on the stage still at the wrong scale (the film's lens is 40 degrees, the plate's 44) and said the stage was brighter than painted; corrected (zoom 1.281).
* An early automatic alignment of the stage still failed (correlation 0.12); replaced by a scan of scales, peak 0.77 at 1.28.
* I swapped "along" and "across" in my sett-by-distance table once; fixed.
* Matplotlib is not installed here, so the charts are drawn with PIL.

**Disk and money:** about 7 MB written (this folder under `study/painted_look` and `study/12 Painted look - crops`, plus 7 pictures in the pictures folder); the big working pictures (the five lined-up paintings, 33 MB) were deleted and are made again by `scripts/a2_register_all.py`; 1.8 GB was free at the end. No paid calls, no rented machine, nothing in any protected folder.

---

## 14. Files

Everything under `proc-work/street_wet/grime_and_growth/study/`:

* `12 Painted look - what survives the painter.md` (this file); `12 Painted look - crops/` the figures (fig1 cracks and stains, fig2 soot ring, fig3 round 2 rubbish, fig4 the series' own hand, fig5 film curve, fig6 survival map, fig7 and fig8 the grime ladders).
* `painted_look/tool/plate_detail_check.py` and `painter_survival_fit.json`: the plate measuring script and its fit.
* `painted_look/scripts/`: every script, in the order of the sections (`a` line-up, `b` bands and the stage, `c` marks and the fit, `d` darks, `e` colour, `f` grime ladder, `g` footprints and setts, `h` figures); `paths.py` lists the input pictures; `run_all_masks_fixed.sh` reruns the region analyses (run `a2_register_all.py` first: it makes the lined-up paintings, which were deleted to save space). The refit scripts (`c9`, `c10`, `c11`, `c14`) read `numbers/c7_marks.json.gz` directly.
* `painted_look/numbers/`: every result as JSON or printout (`c7_marks.json.gz` holds all 26,566 marks with their plate and painting contrasts and 12 chance values each).
* Seven pictures for showing are in `proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/` (names start "25 Painted look").
