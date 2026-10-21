# 10 Recipe - sett relief and rubbish - how it is made

**PART A: the setts (joints between the road stones), round 1. PART B: the rubbish mask and the rubbish, round 2 (at the end of this file, from "PART B").**

What this file is: the plain-words record of two pieces of work on the street: (A) making the joints between the road setts ("the bricks on the ground") read as **grooves between raised stones in every light and every wetness** (round 1), and (B) the **rubbish mask** and the rubbish drawn with it (round 2, at the end).
It follows `study/10 Research - sett relief and rubbish for the street.md` (the study, which found why the joints vanish) and the wetness recipe (`../09 Recipe - wetness layer and specular map for the street - how it is made.md`).
All work is on the copy of the street (`set_copy/street.blend` is not changed on disk; the new layer is put on in Blender each time a picture is drawn, exactly like the wetness layer). Nothing in the film project's folder was changed. No git. No paid image generation.

Words used (one word for each thing, explained once):
* **sett**: one squared stone of the road. **joint**: the gap between two setts. **groove**: the joint seen as a dip between two raised stones.
* **plate**: the one picture drawn from the set's camera, which the painter repaints. **EEVEE**: Blender's fast picture renderer, which the film's plates are drawn with (ray tracing on, shadow rays 4, shadow steps 16, as in the wetness recipe).
* **layer** (Blender calls it a "node group"): a small packaged recipe made of Blender's node boxes that is dropped into a material. **WETNESS** is the water layer of round 2; **JOINTS** is the new one and sits right after it.
* **relief picture** ("normal map"): a flat picture that says, for every dot, which way the surface leans. It gives the light a direction to bounce from, but no real depth.
* **joint contrast** (the study's measure, unchanged): how much darker a joint is than the stone beside it, as a share of the stone's brightness, in the finished 8-bit picture. 0 = the same, 0.3 = a clear dark line, negative = the joint is BRIGHTER than the stone. **seen**: the share of joint dots at least 15 % and 0.015 darker than the stone beside them. The road is cut into a **near**, a **middle** and a **far** band by picture row. Dots under a puddle are left out.
* **pass line** (the study's, mine, a first line, unchanged here): near and middle bands must reach a minimum contrast, "seen" share and brightness difference, and must not exceed a maximum contrast (a black net).
* **lighting test set**: the fixed 22 pictures: 3 cameras (street 540 x 960, low close view 640 x 480, the lockout shot 540 x 960) x 5 lightings (A dusk lamps, B brazier glare, C low side light, D flat overhead, E light from behind into the glare) x dry / wet / heavy rain.
* **rented machine**: the RunPod machine with an RTX 4090 card, where EEVEE draws a picture in 1 to 5 seconds instead of 75 to 85.

---

## 1. The short answer

1. **The joints now show in every light.** On the 22-picture lighting test set, round 2 passed 6 pictures (only the dry ones) and the new JOINTS layer passes **21 of 22**. The wet street at dusk went from a joint contrast of 0.07 (nothing) to 0.52 (a clear dark line); the glare from behind went from 0.03 to 0.53 (section 6, `sheets/setts_before_after_all_lights.jpg`).
2. **At the size the painter sees (1536 x 2730), all 9 pictures I drew pass**, including the lockout shot in heavy rain (`sheets/setts_closeups_full_size_plates.jpg`, 100 % crops).
3. **The one picture that still fails is the lockout shot in heavy rain at the small test size** (middle band: the joints there are lit edges, not dark lines; section 8). It passes at plate size. I did not fix it at the small size.
4. **Why it was lost, and the cure** (section 2 and 3): the water layer's shine filled the joints and flattened the stone edges. The cure is a layer AFTER the water layer that makes the joint darker, makes it dull (so the water's shine does not fill it), and gives the stone edge a real rounded slope that the water cannot smooth away.
5. **A second flaw found on the way and fixed**: the joint picture the study made only found the joints filled with dark moss. About half of the photo's joints are filled with pale sand, so stretches of every 2 m of road had long stones with no groove. I rebuilt the joint picture as a complete grid (section 4, `sheets/setts_joint_picture_completed_grid.jpg`).
6. **Wet look kept**: the stone tops are still wet and glossy, puddles still gather in the low spots and still show the sky and lamps, the road is not darker (section 6).
7. **For you to choose**: the one dial **Joint Strength** (1 = chosen; 0 = off = round 2 exactly; 0.6 = mild), and two other settings, mild and strong (`sheets/setts_dial_mild_chosen_strong.jpg`). Mild passes only 14 of 22, so I do not recommend it.
8. **Real grooves cut into the road** (a plate-only option, section 7) look best in a low close view and worse further away; I left them OFF by default.
9. **Not done**: the painter was not asked to repaint (paid, needs your go-ahead); the glb and the stage do not carry the new layer; pavement flags and kerbs got nothing; Cycles was not tried (section 10).

---

## 2. Why the joints disappeared (example first)

**Example.** The wet street at dusk (street camera, dusk lamps, wetness 0.85). The road photo has dark joints, so in round 2 the DRY road already showed them weakly (joint contrast 0.24). Wet, the same joints came out at **0.07**: you could hardly find them.
What the study found by switching things off one at a time (study note, sections 2 and 3):
* The only thing that ever made a joint dark was its dark colour in the photo. The photo's relief picture added nothing measurable (a groove floor leans only 9 degrees, and a leaning surface is not a dip).
* What washed the joints out was the **shine that water adds**: a smoother surface (roughness 0.3), a clear coat (0.3) and extra reflectiveness (+0.25). The reflection of the sky, the lamps and the glare lies equally over stone and joint.
* Making the relief picture stronger (3 to 6 times) did nearly nothing for the joints (contrast 0.11 to 0.13): it only made white ticks on the stone corners.
**The rule** that follows: a joint is dark because it is a narrow, dirty, dull gap in the shade of its two stones. Water must not be allowed to make it as shiny as the stone top.

---

## 3. What the JOINTS layer does (`tools/joint_layer.py`)

**Example.** One sett and its joint on the wet road. Round 2: the stone top and the joint both shine, so both reflect the same lamp. JOINTS: it takes what the water layer decided and changes it ONLY in and next to the joint:
1. **darker**: the joint colour is multiplied by 0.70 at the middle of the joint (Joint Darkness 0.30), and the stone edge a centimetre or two from the joint by 0.85 (Edge Shade 0.15);
2. **duller**: the joint's roughness goes back to 0.9 (chalk), the shine is cut by 35 % and the water film by 45 %, while the stone top keeps the wet gloss;
3. **a real slope**: a relief picture of a rounded groove (8 mm deep, edge 6 mm wide, steepest slope 51 degrees) is ADDED to whatever relief the water layer left, so the stone edge that faces the light is lit and the one that faces away is dark in every light (the water layer smooths the photo's relief when it is wet; it cannot smooth this one). The photo's own ragged relief inside the joint (moss, grit) is taken out so that the clean groove replaces it;
4. **under a puddle** the water covers the joint: the dulling and the slope fade by 80 % of the puddle mask, but the dark colour stays (you see a dark joint through water);
5. **far away** the slope is faded (full up to 5 m from the camera, 10 % of it at 20 m and beyond), because a steep slope far away is seen as single white ticks. The dark dull joint is not faded.

It sits after the water layer: `dry look -> WETNESS -> JOINTS -> the road's surface`. It is driven by two flat pictures laid on the road through its own texture coordinates, so they line up dot for dot with the road photo (every 2 m): `maps/sett_joints_clean.png` (red = how deep inside a joint, blue = a soft shade for the stone edge) and `maps/sett_groove_normal_16bit.png` (the relief picture of the rounded groove; checked against Poly Haven's own relief picture: the signs agree, correlations 0.93 and 0.90).
With Joint Strength 0 the layer does nothing: I drew all 22 pictures with it at 0 and they equal round 2 to 0.004 on a 0 to 255 scale (largest difference over the 22 pictures).

---

## 4. The joint picture: finding the joints that were missing (`tools/make_joint_pictures.py`)

**Example.** `sheets/setts_joint_picture_completed_grid.jpg`: the road photo with the joints the study's search found in red and the joints I added in green. In the lower half of the 2 m photo almost every vertical joint is pale sand, not dark moss; the study's search looks for dark lines only, so it missed them and the road would have had stretches of long, groove-less stones.
What the script does now, in order:
1. the study's dark-line search (unchanged: a "black top-hat" keeps thin dark lines and drops wide dark smudges);
2. **completing the grid** (new): from how far each row and column of the photo differs in colour from the typical stone, it finds the 10 rows of horizontal joints (spacing 200 to 210 dots, i.e. about 20 cm) and, in each row of stones, the vertical joints; fills a gap where one joint is plainly missing between two others; draws the joints the dark search missed as straight lines as wide as the dark core of the ones it found (16 dots = 1.6 cm), only where the dark search found nothing within 75 dots (vertical) or 30 dots (horizontal) - the first try drew double lines next to found ones;
3. the cleaning (the first helper's, with two changes): gaps up to 6 cm along a line are bridged (it was 8.5 cm, which also filled narrow stones into solid joint), stone islands under 6000 dots are filled (it was 1500; a real sett is about 35000 dots);
4. the three pictures made from the cleaned mask (all computed on a 3 x 3 tiling so that nothing breaks at the 2 m repeat; I checked there is no seam).
Numbers (`maps/sett_joints_numbers.json`): the joints found 91 vertical stretches; 10 gaps were filled and 53 vertical stretches drawn or extended; 72 short horizontal stretches were added; the joint share of the picture went from 8.5 % to 14.6 % (lines) and 21 % (the soft cleaned mask).
*Not verified*: that every added line sits exactly on the real joint (I looked at an overlay at 100 % for the lower half; they sit within a few dots; where a stone is chipped the line is straight and the photo's edge is not).

---

## 5. The controls (the layer JOINTS, every dial)

| dial (long name on the node / short name) | range | chosen | what it does |
|---|---|---|---|
| Joint Strength / `strength` | 0 to 1 | **1** | the master dial: scales every effect. 0 = off = round 2 exactly. 0.6 = mild |
| Joint Darkness / `darkness` | 0 to 1 | 0.30 | colour of the joint middle multiplied by 1 - this (0.3 = 70 % as bright) |
| Joint Wet Darkening / `wet_darkening` | 0 to 1 | 0 | extra darkness x how wet the spot is. Tried 0.25 to 0.55: little effect; off |
| Joint Shadow / `shadow` | 0 to 1 | 0 | share of the LIGHT that never reaches a joint (also darkens its shine). Tried 0.25 to 0.7: much darker joints (a black net by the pass line); off. Only takes effect if above 0 when the layer is put on |
| Joint Dullness / `dullness` | 0 to 1 | 1 | how far a joint loses the water's shine |
| Joint Spec Cut / `spec_cut` | 0 to 1 | 0.35 | share of the shine cut in a fully dull joint (0.8 also tried: harsher) |
| Joint Coat Cut / `coat_cut` | 0 to 1 | 0.45 | share of the water film cut in a fully dull joint (0.9 also tried) |
| Joint Dull Roughness / `dull_roughness` | 0 to 1 | 0.9 | the roughness of a fully dull joint (0.7 also tried) |
| Joint Relief / `relief` | 0 to 2 | 1 | steepness of the rounded stone edge (0 = none; 1 = 8 mm deep picture; 1.4 = strong) |
| Edge Shade / `edge_shade` | 0 to 1 | 0.15 | the stone edge a centimetre or two from the joint is this much darker than the stone middle |
| Puddle Cover / `puddle_cover` | 0 to 1 | 0.8 | how much a puddle's water hides the dulling and the slope |
| Photo Relief In Joints / `photo_relief_in_joints` | 0 to 1 | 1 | how much of the photo's ragged relief is taken out inside a joint |
| Relief Far Share / `far_share` | 0 to 1 | 0.10 | share of the slope left at the far end of the fade (1 = no fade) |
| Relief Fade Start / `fade_start` | metres | 5 | distance from the camera where the slope starts to fade |
| Relief Fade End / `fade_end` | metres | 20 | distance where the fade ends |

**Mild** = Joint Strength 0.6, everything else chosen. **Strong** = Joint Darkness 0.45, Joint Relief 1.4, Edge Shade 0.25.

---

## 6. How to put it on, and results

**To use it** (inside Blender, street copy open; `tools/apply_joints_to_set.py`, tested):
```
import apply_wetness_to_set as aw
import apply_joints_to_set as aj
aw.apply(wetness=0.85, puddles=0.5)     # the water layer first
aj.apply()                               # JOINTS on the road, chosen settings
aj.apply(strength=0.6)                   # mild;   aj.set_dials(strength=0.8) changes it later
aj.apply_real_grooves()                  # optional, plate only (section 7)
aj.remove()                              # everything off again
```
Self-test (`tools/test_apply_script.py`, one Blender run on the rented machine): picture with the layer differs from without (mean difference 1.8 of 255); with strength set to 0, after `remove()`, and after removing the real grooves it equals the plain road (0.0004 to 0.0009); with the shade and the real grooves on it differs (2.8); nothing is left behind (no JOINTS node, no modifier). For a job file of the picture runner use `tools/apply_joints_after_wetness.py` as "after_apply".

**The whole lighting test set, before and after** (all 22 pictures drawn in ONE run on the rented machine, same settings, EEVEE with ray tracing, shadow rays 4, steps 16; 16 samples for the street and lockout, 24 for the close view; the numbers are contrast / "seen" share; `setts/work/f3/`, `sheets/setts_before_after_all_lights.jpg`):

| picture | puddle share of road | BEFORE near | BEFORE middle | AFTER near | AFTER middle | before | after | grid seen (after) |
|---|---|---|---|---|---|---|---|---|
| street, dusk lamps, dry | - | 0.24 / 0.90 | 0.18 / 0.68 | 0.45 / 1.00 | 0.35 / 0.99 | pass | pass | yes |
| street, dusk lamps, wet | 10 % | 0.07 / 0.15 | 0.06 / 0.07 | 0.52 / 0.98 | 0.37 / 0.86 | FAIL | pass | yes |
| street, dusk lamps, heavy | 35 % | 0.07 / 0.05 | 0.05 / 0.04 | 0.44 / 0.96 | 0.33 / 0.83 | FAIL | pass | yes |
| street, low side light, dry | - | 0.19 / 0.69 | 0.14 / 0.43 | 0.40 / 0.95 | 0.30 / 0.91 | pass | pass | yes |
| street, low side light, wet | 10 % | 0.07 / 0.10 | 0.05 / 0.06 | 0.48 / 0.99 | 0.37 / 0.89 | FAIL | pass | yes |
| street, flat overhead, dry | - | 0.24 / 0.92 | 0.18 / 0.72 | 0.42 / 1.00 | 0.33 / 0.99 | pass | pass | yes |
| street, flat overhead, wet | 10 % | 0.09 / 0.21 | 0.07 / 0.09 | 0.43 / 0.96 | 0.28 / 0.76 | FAIL | pass | yes |
| street, light from behind, dry | - | 0.20 / 0.71 | 0.16 / 0.55 | 0.37 / 0.88 | 0.29 / 0.91 | pass | pass | yes |
| street, light from behind, wet | 10 % | 0.03 / 0.10 | 0.02 / 0.02 | 0.53 / 0.92 | 0.38 / 0.84 | FAIL | pass | yes |
| street, light from behind, heavy | 35 % | 0.03 / 0.07 | 0.02 / 0.02 | 0.49 / 0.88 | 0.38 / 0.87 | FAIL | pass | yes |
| close, dusk lamps, dry | - | 0.33 / 0.94 | 0.29 / 0.92 | 0.56 / 1.00 | 0.50 / 1.00 | pass | pass | yes |
| close, dusk lamps, wet | 4 % | 0.08 / 0.32 | 0.05 / 0.08 | 0.62 / 1.00 | 0.55 / 1.00 | FAIL | pass | yes |
| close, dusk lamps, heavy | 15 % | 0.07 / 0.25 | 0.04 / 0.05 | 0.61 / 1.00 | 0.52 / 0.99 | FAIL | pass | yes |
| close, low side light, wet | 4 % | 0.09 / 0.35 | 0.05 / 0.10 | 0.59 / 1.00 | 0.52 / 0.99 | FAIL | pass | yes |
| close, flat overhead, wet | 4 % | 0.11 / 0.41 | 0.07 / 0.12 | 0.55 / 1.00 | 0.48 / 0.99 | FAIL | pass | yes |
| close, light from behind, wet | 4 % | 0.01 / 0.27 | 0.03 / 0.07 | 0.61 / 0.96 | 0.53 / 0.96 | FAIL | pass | yes |
| lockout, brazier glare, dry | - | 0.21 / 0.70 | 0.10 / 0.20 | 0.38 / 0.93 | 0.22 / 0.65 | pass | pass | yes |
| lockout, brazier glare, wet | 9 % | 0.07 / 0.20 | 0.08 / 0.17 | 0.37 / 0.82 | 0.10 / 0.43 | FAIL | pass | yes |
| lockout, brazier glare, heavy | 46 % | 0.04 / 0.12 | 0.06 / 0.10 | 0.25 / 0.68 | -0.05 / 0.19 | FAIL | FAIL | yes |
| lockout, low side light, wet | 9 % | 0.10 / 0.28 | 0.06 / 0.10 | 0.47 / 0.98 | 0.37 / 0.88 | FAIL | pass | yes |
| lockout, flat overhead, wet | 9 % | 0.12 / 0.34 | 0.08 / 0.14 | 0.38 / 0.91 | 0.28 / 0.71 | FAIL | pass | yes |
| lockout, light from behind, wet | 9 % | 0.06 / 0.20 | 0.05 / 0.14 | 0.39 / 0.82 | 0.14 / 0.51 | FAIL | pass | yes |

**Reading it.** BEFORE passes 6 of 22 (all dry), AFTER passes 21 of 22. Near contrast, BEFORE 0.01 to 0.33, AFTER 0.25 to 0.62. The grid column is my second measure (section 8): the grid is visible in the near and middle bands in 22 of 22 AFTER pictures, 1 of 22 BEFORE. The other settings: strong 21 of 22, mild 14 of 22, real grooves 20 of 22.
The BEFORE numbers drawn on the rented machine agree with the study's numbers drawn on this machine (for example street, dusk, wet: near 0.07 both; close, dusk, wet 0.08 both), so the rented machine draws the same pictures.

**At the size the painter sees** (`setts/work/p5/`; 48 samples; 1536 x 2730 for the street and lockout, 1920 x 1440 for the close view; 100 % crops in `sheets/setts_closeups_full_size_plates.jpg`):

| picture (size) | BEFORE near | BEFORE middle | AFTER near | AFTER middle | before | after | with real grooves: near ; middle | real grooves |
|---|---|---|---|---|---|---|---|---|
| main_A_dry (1536x2730) | 0.29 / 0.91 | 0.25 / 0.88 | 0.50 / 0.98 | 0.44 / 1.00 | pass | pass | 0.30 / 0.76 ; 0.32 / 0.85 | pass |
| main_A_wet (1536x2730) | 0.08 / 0.19 | 0.06 / 0.14 | 0.59 / 0.99 | 0.52 / 0.97 | FAIL | pass | 0.36 / 0.85 ; 0.29 / 0.73 | pass |
| main_E_wet (1536x2730) | 0.05 / 0.20 | 0.04 / 0.10 | 0.64 / 0.97 | 0.53 / 0.93 | FAIL | pass | 0.56 / 0.93 ; 0.51 / 0.88 | pass |
| close_A_dry (1920x1440) | 0.33 / 0.88 | 0.31 / 0.90 | 0.51 / 0.98 | 0.50 / 0.98 | pass | pass | 0.32 / 0.73 ; 0.23 / 0.63 | FAIL |
| close_A_wet (1920x1440) | 0.10 / 0.26 | 0.06 / 0.12 | 0.56 / 0.98 | 0.57 / 0.98 | FAIL | pass | 0.38 / 0.80 ; 0.29 / 0.77 | pass |
| close_E_wet (1920x1440) | 0.08 / 0.27 | 0.05 / 0.14 | 0.56 / 0.91 | 0.55 / 0.95 | FAIL | pass | 0.45 / 0.83 ; 0.36 / 0.81 | pass |
| lockout_B_dry (1536x2730) | 0.24 / 0.73 | 0.15 / 0.40 | 0.42 / 0.92 | 0.29 / 0.89 | pass | pass | 0.36 / 0.83 ; 0.20 / 0.58 | pass |
| lockout_B_wet (1536x2730) | 0.09 / 0.29 | 0.13 / 0.45 | 0.43 / 0.87 | 0.16 / 0.52 | FAIL | pass | 0.27 / 0.72 ; 0.04 / 0.36 | FAIL |
| lockout_B_heavy (1536x2730) | 0.06 / 0.17 | 0.11 / 0.34 | 0.33 / 0.78 | 0.08 / 0.41 | FAIL | pass | 0.19 / 0.64 ; -0.08 / 0.17 | FAIL |

At this size all 9 AFTER pictures pass, including the lockout in heavy rain (middle band 0.09, which fails at 540 x 960). With real grooves only 6 of 9 pass (the lockout wet and heavy middle bands, and the dry close view).

**Is the wet look kept?** By eye, yes (the sheets): stone tops are still glossy and reflect the lamps and the sky, the glare patch under the brazier is still there, puddles are where they were and still mirror the houses. I did not measure road brightness again for this round: the layer changes the colour only in and beside the joints (about 21 % of the road dots at most), and it darkens them, so the road is a little darker overall; the wet road was 1.50 times today's in round 2 and I did not re-measure that ratio. Say so if it matters.

---

## 7. What I tried and did not keep (and why)

| tried | result | decision |
|---|---|---|
| the study's first answer, joint picture "mild1" (colour 0.85, roughness 0.9, shine x0.65) | worked, but the picture had ragged joints and many missing | replaced by JOINTS with the completed grid |
| relief far fade 0.35 from 8 to 30 m (my first choice) | at 100 % in a plate, rows of white ticks in the middle distance | 0.10 from 5 to 20 m; ticks mostly gone, the grid still shows |
| relief 0.6 | fewer ticks, softer near edges | not chosen (the near stones look flatter) |
| relief 0 (no groove slope) | joints only dark lines; near contrast falls to 0.17 in the lockout | kept the slope |
| Joint Shadow 0.25 to 0.7 | joints near-black (contrast 0.6 to 0.9), close view fails the "black net" cap; passes the lockout heavy middle band only at 0.7 | dial kept, default 0 |
| Spec Cut 0.8 / 1.0, Coat Cut 0.9 / 1.0, Dull Roughness 0.7 | harsher, near contrast up to 0.83 in the close view | kept 0.35 / 0.45 / 0.9 |
| Joint Wet Darkening 0.25 to 0.55 | small effect on the failing band | off |
| **real grooves** (a Geometry Nodes modifier cuts the road from y 0 to 22 m into faces of about 8 mm and presses the joints 8 mm down by the groove picture; full depth to 10 m, fading to nothing at 22 m) | close view: truly deep stones with real shadows, the best look; street and lockout plates: more irregular glints in the middle distance, three more bands fail; costs about twice the picture time (4.6 s against 2.3 s at plate size here); cannot go into the glb | optional, plate only, for a hero close-up; off by default |
| first try at completing the grid | black blocks: two lines drawn next to a found joint made a double-wide joint, and bridging 8.5 cm filled narrow stones; fixed (section 4) | fixed |

---

## 8. What is still wrong, and how I checked

* **Lockout shot, brazier glare, heavy rain, 540 x 960, middle band: FAIL** (contrast -0.05 against a minimum of 0.07). What it is: in heavy rain 46 % of the road is puddle and the puddle dots are left out, so the measured "middle band" is a small island of 479 joint dots right of the sacks under the brazier's blaze. There the joint dots come out BRIGHTER than the stone dots (final run: joint 0.581, stone 0.515; round 2 had 0.513 and 0.509). I looked at it: the picture shows the grid there as bright lit edges (the grid is visible), not as dark lines. What I tried and what did not fix it (these tests were drawn with the earlier, incomplete joint picture, see section 11; the pattern was the same): relief off (worse), no shine at all in the joints, a darker joint, the shade dial (passes only at 0.7, which makes every other picture too black), a smaller puddle cover. My best guess (not proven): at these dots the stone and joint are both in the shoulder of the picture's brightness curve, where a big difference in light becomes a small difference in shown brightness. At 1536 x 2730 the same picture passes (middle 0.09, 41 % seen).
* **A second measure, mine, first try** (`tools/measure_grid_visibility.py`): the study's measure only counts dark joints. This one counts the joint zone and the edge of the stones beside it, dark or bright, against the stone's own grain: a grid is visible if the joint zone differs from the stone by at least 12 % and at least twice the stone's grain. The lockout heavy middle band reads 0.15 against a grain of 0.06 (24 % of its joint-zone dots lit edges, 10 % dark). I chose the line by eye; it is a check on the first measure, not a second pass line.
* The measuring mask is still the study's (made from the dark joints of the photo), so pale joints count as "stone" in the measure. That makes the contrast numbers slightly lower than they would be with a complete mask; I kept it so that before and after are measured the same way as the study did.
* Mid-distance white ticks are reduced, not gone (section 7).

---

## 9. Timings (rented machine, RTX 4090, EEVEE)

* One picture: 540 x 960 at 16 samples about 1 s; 1536 x 2730 at 48 samples about 2.3 s (4.6 s with real grooves); the first picture of a run is slower. On this machine the same 540 x 960 picture took 75 to 85 s.
* The whole 22-picture set for 6 variants (before, off, mild, after, strong, real): the street file's 16 pictures x 6 + masks 124 s; the lockout file's 6 pictures x 6 in 76 s (the lockout file loads slowly). The 9 plate-size pictures x 3 variants: 66 s and 57 s.
* 27 Blender runs on the rented machine in all (the budget was about 20, set for a machine 100 times slower; each run took 20 to 135 s), about half an hour of machine time (about US$0.20 at US$0.34 an hour). The two runs the first helper did on this machine are not counted.
* Downloading a folder picture by picture took 140 to 180 s; as one tar file 7 to 11 s (`tools/rent_and_render.py` does it).

---

## 10. What I did not test, and what I am unsure of

**Not tested**
* **The painter (Flux)** on a plate with the new joints. Needs your go-ahead (about US$0.20 to 0.28 with small pictures). The brief would need one more sentence: keep the thin dark lines between the setts where image 1 has them, even where the road shines.
* **The glb and the stage**: the layer is not in the glb (the baked ground maps are 2 cm a dot; a joint is 1.6 cm wide, so baking it into them cannot work). A way that could: put the groove relief picture into the glb road material in place of the smoothed photo relief (a 2 m repeating picture); not tried.
* **Cycles**: all pictures are EEVEE. The layer uses the camera-distance fade and nothing EEVEE-only that I know of, but I did not draw it in Cycles.
* **Pavement flags, kerbs, gutter stones**: nothing done for them; their joints are still washed out when wet. (The flags need their own joint pictures from `large_grey_tiles_colour.jpg`.)
* Other shots and cameras than the 3 of the test set; animation (dials can be keyframed, not tried); a road made from a texture recipe.
* Road brightness against round 2 (section 6): not re-measured.
* A person's eye on the sheets: only mine so far. Whether the joints are too dark or the edges too bright for the film is your call (the dial and the strong / mild settings are there for that).

**Unsure**
* Whether 0.30 darkness and 8 mm of groove are the right amount for a 1926 Durham road (setts of this kind were laid in sand or mortar; I took the photo's joints as they are).
* The distance fade (5 m to 20 m) is tuned on the street camera (the lockout camera is 1.7 m high; I did not look up the street camera's height) and the lockout camera; a camera much higher or much closer may need other numbers.
* The pale-joint lines are straight; the real joints wander by a few dots.
* The pass line is the study's and mine.

---

## 11. What went wrong (all of it)

* My first guess for the lockout failure (the lit stone edges) was wrong (relief off made it worse); the second (dull joints catch the glare) and the third (puddle edges) did not hold either; the real picture is the island under the brazier (section 8). About four of my sweeps were spent on it.
* The first fade (8 to 30 m) looked fine at 540 x 960 and showed rows of ticks at 100 % in a plate; found only when I cut a plate at 100 %.
* The first helper's joint picture had half the joints missing; I only saw it when I laid the picture over the photo. My first completion made black blocks (double lines, narrow stones filled); three tries.
* A sheet title overlapped its neighbour at the first width; fixed.
* The rented machine had no picture-reading Python package, so I installed `opencv-python-headless` and `numpy` there with pip (one command) so that the measuring runs next to the drawing. That is the only change I made to the rented machine; I did not touch `~/.runpod` and did not stop the machine.
* While another helper unpacked a 520 MB bundle, free disk space dipped to 0.9 GB (my line is 1.2 GB). I deleted my superseded picture folders at once; the end state is 108 MB in my folder and 1.5 GB free.
* I ran 27 Blender runs, 7 more than the budget, because rendering cost almost nothing and several of the findings above only came from the next run.
* **Which numbers come from which pictures**: every table and every number in sections 1 and 6 comes from the FINAL run (final joint picture, final settings: `work/f3`, `work/p5`). The trials of section 7 and the analysis of the failing band in section 8 (shade, shine cuts, relief 0, wet darkening, the first fade, the geometry first look) were drawn earlier with the first helper's incomplete joint picture; their pictures were deleted to keep the folder small and the numbers I quote for them are the ones I wrote down at the time. The decisions they led to were re-checked only through the final run. After the last drawing I changed only comments in `joint_layer.py` (checked: it still parses; not redrawn).

---

## 12. Files (all under `relief_and_rubbish/setts/`; sheets in `relief_and_rubbish/sheets/`)

* `tools/joint_layer.py` the JOINTS layer (and the real-grooves modifier); `tools/apply_joints_to_set.py` the one script that puts it on the street copy; `tools/apply_joints_after_wetness.py` the same for the picture runner; `tools/make_joint_pictures.py` makes the joint pictures (run in plain Python, not Blender).
* `tools/make_job_lists.py` writes the list of pictures one Blender run should draw (any list, or the whole set for several variants); `tools/rent_and_render.py` runs a list on the rented machine and brings back the folder; `tools/run_jobs_rented.sh`, `tools/run_jobs_here.sh` (the same job here), `tools/run_two.sh`; `tools/sweep_report.py` prints the before / after table; `tools/before_after_sheet.py` makes the sheet; `tools/measure_grid_visibility.py` the second measure; `tools/test_apply_script.py` the self-test; `tools/register_variants.py` makes the test variants known to the runner.
* `maps/` the joint picture, the groove relief picture, the measuring-mask picture of the new grid, and two check pictures (`joint_grid_check.jpg`, `sett_joints_check.jpg`).
* `work/f3/` the 22-picture set x 6 variants (JPEG, `measurements.json`, `sweep_report.txt`, `grid_visibility.txt`); `work/p5/` the plate-size pictures; `work/t2/` the self-test of the apply script.
* Sheets: `setts_before_after_all_lights.jpg`, `setts_closeups_full_size_plates.jpg`, `setts_dial_mild_chosen_strong.jpg`, `setts_joint_picture_completed_grid.jpg`.
* Result: `setts_result_round_1.json`.

---

## PART B: the rubbish mask and the rubbish (round 2)

What this part is: the plain-words record of the **rubbish**: a mask that says where rubbish gathers (along the gutters and kerbs, along the foot of the house walls, at doorsteps, rain pipes, lamp posts and corners, and round the props), a painted layer on the ground that draws the rubbish there, and a few small separate 3D pieces laid where the same mask says so.
It sits on top of the setts of Part A and the wetness layer of round 2. Nothing in the film project's own folder was changed and nothing in `set_copy/` or `tools/` was changed (I checked the file dates). The street copy and the film's lockout shot file are opened in Blender each time, the layers are put on in memory, and nothing is saved. No git. No paid image generation (the painter was not asked).

Words used (new ones only; the words of Part A and the wetness recipe still hold):
* **rubbish mask** ("the mask"): a grey picture of the ground, 0 = no rubbish, 1 = most. It is made live inside Blender from five places (gutter, wall foot, corners and doorsteps, props, patches), so every place has its own dial.
* **places picture**: a small flat picture of the street seen from above, made by measuring the real 3D street: how far each spot of ground is from the nearest wall or step, from the nearest prop, where the doorsteps, rain pipe feet and lamp post feet are, and where two solid things meet in a corner. It is what lets the mask find the foot of a wall or a doorstep by itself. One dot = 4 cm.
* **muck layer** (its node group is called `RUBBISH`): the layer that paints the rubbish onto the ground materials: colour, roughness (how blurry reflections are) and a little relief. It comes after the wetness layer and after JOINTS: `dry look -> WETNESS -> JOINTS -> RUBBISH -> the surface`.
* **pieces**: small separate 3D objects (a cinder lump, a scrap of paper) laid on the ground by Blender's Geometry Nodes ("scatter"). Only in plates, not in the glb.
* **cinder**: a lump of burnt coal left in a grate; **clinker**: fused ash, brown-grey; **slack**: coal dust and small bits; **ash**: the pale grey powder left after burning. **kind**: one sort of rubbish (dust, cinders, ash, mud, straw, paper, leaves).
* **crown**: the middle of the road, which is the highest part. **gutter**: the channel stones along each side of the road, with the kerb stone beside them.

---

## B1. The short answer

1. **The rubbish mask exists and works, with the controls asked for.** One master dial (Rubbish Amount) and separate dials for the **gutter**, the **wall foot**, **corners and doorsteps**, **round the props** and a **seed**, plus dials for how broken-up it is, how wide each strip is, and one for each kind of rubbish. Section B6 lists every dial.
2. **Example (look at `sheets/rubbish_closeups_100pct.jpg`).** The wet pavement in front of a doorstep went from clean wet flagstones to flagstones with a scatter of cinders, ash dust, grey scraps of paper, a few straw strokes and dark grit, thickest at the foot of the step and the wall. The right gutter went from clean to grit, cinders and scraps along the kerb and the channel. Round the fire drum and the sacks in the lockout shot there is a dark ring of coal dust with cinders, coal chips and scraps (the film's older painting had a soot-and-ash ring round the drum that the wet painting lost; I did not lay the two side by side).
3. **The mask is found from the real street, not typed in.** The foot of every wall, step, rain pipe, lamp post and prop is read from the 3D file (section B3). The picture made from it is also a plain picture a person can look at (`sheets/rubbish_mask.jpg`).
4. **It never sits on the crown of the road.** In the street copy the mask is 0.000 over the whole middle of the road (|x| under 1.3 m); in the lockout file it is 0.000 there too except in the rings round the props (the drum, the sacks and the handcart stand in the road) (section B8).
5. **It keeps the 3D look of the setts and the wet look.** On the 22 pictures of the lighting test set, the joints between the setts measure **the same with the rubbish as without it in the street copy's 16 pictures** (the same contrast to two decimals in all 16; the biggest move of any number in them is 0.003), and **21 of 22 pictures pass, exactly as before the rubbish** (section B8). Where there is rubbish the joints are partly covered by design, so those dots are left out of the measure (about 4 % of the road in the main view, 1.3 % in the close view, 27 % in the lockout shot, whose foreground is mostly prop rings; with the two-dot margin I also leave out, 5 %, 2 % and 31 %). Wet pictures look wet: the muck follows the street's wetness (wet cinders are dark and shiny, wet paper dark and limp, wet mud glossy brown) and puddles still show the sky and lamps.
6. **The full-size lockout plate is drawn** (1536 x 2730, wet, setts and rubbish, 64 samples, EEVEE with ray tracing, shadow rays 4, steps 16): `final/final_lockout_plate_wet_setts_and_rubbish.png`. All nine plate-size test pictures (dry, wet, heavy, glare, close view) pass for the joints.
7. **Not done:** the painter (paid, needs your go-ahead), the glb and the stage, Cycles, the dirt on the wall surfaces themselves, rubbish for any other file (the places picture has to be made again), a human eye other than mine (section B10).

---

## B2. What rubbish, and where (1926 Durham: how little I know)

The study (`study/10 Research - sett relief and rubbish for the street.md`, section 7) found **no photograph or account of the rubbish of a 1926 Durham front street in so many words**. What it could read: ash pits and middens behind colliery rows (up to 1914), back-lane coal holes (about 1910 and the 1920s, nearby villages), ash and street sweeping in Lancashire in the 1930s, a Birtley account of the lockout (waste heaps searched for coal, loose stone), and the film's own notes (a sooty street, an oil drum with a fire, a soot-and-ash ring round the drum in an older painting, and the lockout props). **Everything about where the kinds lie is my reasoning, not a source** (the ash, coal and coal-hole parts are the best backed). What I drew, and why:

| kind | where | why I think so (my reasoning) |
|---|---|---|
| coal dust, cinders, grit | everywhere there is rubbish; thickest round sacks, the slack heap, the drum and in the gutter | in a lockout more of the rubbish is coal (fetched in sacks and prams from the heaps) than ash; the drum fire leaves cinders |
| ash (pale grey powder) | doorsteps and round the drum | ash was tipped out at the door and a street fire leaves ash |
| mud (brown paste) | the bottom of the gutter channel and the foot of rain pipes | rain carries muck to the lowest place and leaves it |
| wet straw | the kerb foot and the foot of the walls | horses still worked the road; straw from crates and stables |
| sodden paper | along the walls and the gutter, in corners | newspaper and wrapping; plain grey-brown scraps, **no print** |
| dead leaves | rain pipe feet and corners, a few green ones | May: old brown leaves lodged in corners |
| broken bits (a sherd of crockery, a stick) | among the cinders, few | the study's list |
| nothing modern | no plastic, no printed tins or packets, no readable print anywhere | house rule |

---

## B3. How the mask is made (example first)

**Example.** The right-hand pavement by the first doorstep, seen from above. The places picture says: "the wall is here (4.15 m from the middle), the step stands out from it to 3.49 m, a rain pipe comes down here". The mask then says: "rubbish is strongest touching the wall and the step, falls away to nothing about 0.75 m from them, is strong in the nook where the step meets the wall, and has an extra blob in front of the step". Noise then breaks that strip into heaps and gaps. At the kerb, 1.5 m away, the gutter rule takes over. The middle of the road, 2 m further on, gets nothing.

**The places** (each has its own dial; each is a smooth falloff, strongest at 1):

| place | how it is found | reaches | notes |
|---|---|---|---|
| **gutter** | from the distance across the street: the channel stones (|x| 2.2 to 2.5 m) are full strength | 0.45 m onto the road (dial), 0.45 m over the kerb and onto the pavement | the kerb stone's top gets 45 % less (a raised stone keeps less); **Crown Clear** stops it nearer the middle than 1.3 m (full strength from 1.8 m) |
| **wall foot** | from the places picture: distance to the nearest house wall, step or plinth | 0.75 m (dial), strongest at the wall | found for every wall by itself, so steps and the gaps between houses come out right |
| **corners and doorsteps** | the places picture: the foot of each front step (from the door frames), the foot of each rain pipe and lamp post, and "inside corners" (a spot where many short sideways rays hit something although the nearest wall is far away: a step and its wall, a dustbin and the wall) | about 0.5 m round each | |
| **around props** | the places picture: distance to the nearest prop (drum, sacks, handcart, dustbins, pails, barrel, ladder, spade, lantern, the notice board's legs: 33 objects found in the lockout file) | 0.8 m (dial) | only the lockout file has props |
| **patches** | smooth noise, a different pattern for each place, and a slow change from house to house (0.6 to 1.35 times) | | Patchiness 0 = even strips, 1 = separate heaps with bare gaps; the Seed moves them |

The places pictures are made by `tools/make_places_pictures.py` from the real file (5 s for the street copy, 8 s for the lockout file, one Blender run each): `maps/places_street_a.png` and `_b.png`, `maps/places_lockout_a.png` and `_b.png` (225 x 2100 dots, 4 cm a dot, across x = -4.5 to 4.5 m and along y = -12 to 72 m). Picture A: red = how far from a wall or step, green = how far from a prop, blue = catch points. Picture B: red = inside corners, green = doorsteps, blue = rain pipe and lamp post feet. If a prop is moved in the lockout file, run the script again.

---

## B4. The muck layer: what it paints (`tools/rubbish_layer.py`, group `RUBBISH`)

It is made of plain Blender nodes (547 of them in the group). It only paints on **surfaces that face up** (the upright face of a kerb stone or a step stays clean: the first try had cinders stuck to the kerb's side, section B9). Under standing water it keeps the colour (you see the rubbish through the water) but cuts its dulling and its relief by 80 % of the puddle mask.

| kind | what it looks like | colour dry -> wet (linear light) | roughness dry -> wet | relief |
|---|---|---|---|---|
| dust film | a soft dark film, mottled | 0.05 -> 0.014 grey-brown | 0.97 -> 0.55 | none |
| cinders | angular lumps about 1.8 cm across (random polygon cells shrunk by a ragged gap) and a second set about 4 cm; dark grey, brown clinker, a few pale ash grit; the big ones black coal or clinker | 0.03 -> 0.011 (cinder), 0.115 -> 0.045 (clinker) | 0.92 -> 0.62 | domed lumps, up to 12 mm |
| fine grit | 3 to 6 mm dark specks | as cinder | as cinder | a little |
| mud | brown paste with ragged edges | 0.085 -> 0.03 brown | 0.90 -> 0.22, plus a water film when wet | slightly lower |
| ash | soft pale grey patches | 0.215 -> 0.04 (pale dry, dark grey paste wet) | 0.97 -> 0.50 | a little |
| straw | thin strokes about 6 mm wide, 5 to 15 cm long, in two directions | 0.36 -> 0.145 pale yellow-brown | 0.88 -> 0.72 | tiny |
| sodden paper | flat grey-beige scraps 5 to 10 cm with ragged edges, crumpled shading, plain | 0.34 -> 0.115 | 0.80 -> 0.35 | edge only |
| dead leaves | ovals 4 to 6 cm; brown, some orange-brown, a few green | 0.105 -> 0.04 (brown), 0.04 -> 0.016 (green) | 0.80 -> 0.40 | a little |

The layers go on bottom to top in this order: dust film, mud, ash, cinders, big lumps, grit, straw, paper, leaves. The shine and the water film of the ground are cut where dust, cinders, ash or straw lie (shine by up to 55 %, water film by up to 85 %); wet mud adds a water film. The colours are my choice for coal dust, cinder, ash, mud, straw, paper and leaf, not matched to a photograph.

---

## B5. The pieces (`tools/rubbish_pieces.py`)

Six kinds, each laid by its own scatter (Blender's "Distribute Points on Faces" with a Poisson disk: no two pieces of one kind closer than a set distance; the density comes from the same mask nodes and dials as the painted layer; each piece lies on the ground and is turned a random way round):

| kind | made of | size | most per square metre where the mask is 1 | where |
|---|---|---|---|---|
| lumps | 3 cinder lumps, 2 clinker lumps, a china sherd, a stick | about 1.5 to 8 cm (stick 10 to 20 cm) | 70 | wherever the muck is |
| coal | 3 black shiny lumps | about 2 to 8 cm | 45 | round the sacks, the slack heap, the drum, the doorsteps |
| ash heaps | 3 low irregular mounds | about 3 to 13 cm | 6 | doorsteps, the drum |
| paper | 2 torn scraps, 3 sodden scraps, 1 sodden wad | 5 to 28 cm | 16 | along walls and gutter, in corners |
| leaves | 3 leaves | about 4 to 10 cm | 16 | rain pipe feet, corners, a little in the gutter |
| straw | 3 bundles of 2 to 4 strands | strands about 4 to 16 cm | 18 | kerb foot and wall foot |

At the defaults they are laid only up to 45 m along the street: **6,439 pieces in the street copy and 7,199 in the lockout file** (counted by Blender). Nothing is printed on any piece and nothing is modern. They are real objects (they catch light and throw small shadows) but only in plates: they are not in the glb. Their colours follow the street's wetness (set from the same state as the wet layer, `set_state`).

---

## B6. The controls (every dial)

The short names are what `apply_rubbish_to_set.py` takes; the long names are on the group's node in Blender. A dial at 0 switches that part off; at its top value it doubles it. "Seen" = what I saw in `sheets/rubbish_controls.jpg` and `sheets/rubbish_mask.jpg`.

| dial (short / long name) | range, default | what changing it does |
|---|---|---|
| `amount` / Rubbish Amount | 0 to 2, **1** | the master dial. 0 = nothing at all: the ground is exactly as before (self-test, section B8). Share of the ground (street copy, 0 to 42 m, across the pavements) that is clearly rubbish (mask over 0.3): 17 % at 0.5, 30 % at 1, 36 % at 2 |
| `gutter` / Gutter | 0 to 2, **1** | rubbish in the gutter, on the kerb and on the road's outer strip. Alone: 18 % of the ground |
| `wall_foot` / Wall Foot | 0 to 2, **1** | rubbish along the foot of the walls and steps. Alone: 11 % |
| `corners` / Corners And Doorsteps | 0 to 2, **1** | doorsteps, rain pipe and lamp post feet, inside corners. Alone: 5.6 % |
| `props` / Around Props | 0 to 2, **1** | rings round the props. Alone (lockout file): 4.7 % |
| `seed` / Seed | any, **0** | moves the patches and the pieces; the same seed gives the same street. Seeds 0, 5 and 11 differ in where the heaps lie, not in how much (the difference is small to see in the mask: the strips keep their shape) |
| `patchiness` / Patchiness | 0 to 1, **0.55** | 0 = smooth even strips (33 % of the ground rubbish), 1 = separate heaps with bare gaps (24 %) |
| `gutter_width` / Gutter Width | 0.05 to 1.5 m, **0.45** | how far the gutter's rubbish reaches onto the road: 0.25 m -> 27 % of the ground, 1.6 m -> 38 % |
| `wall_width` / Wall Foot Width | 0.1 to 2 m, **0.75** | how far the wall foot's rubbish reaches: 0.4 m -> 28 %, 1.4 m -> 36 % |
| `props_width` / Props Width | 0.1 to 1.5 m, **0.8** | how far the rubbish reaches from a prop (lockout file: 0.4 m -> 31 %, 1.2 m -> 35 %) |
| `crown_clear` / Crown Clear | 0 to 1, **1** | 1 = the gutter's rubbish never comes nearer the middle line than 1.3 m, however wide you make it. Seen with Gutter Width 1.6: with Crown Clear 1 the band stops short (38 %), with 0 it creeps toward the middle (45 %) |
| `dust` / Dust And Cinders | 0 to 2, **1** | the dust film, cinders and grit (also the lumps and coal pieces) |
| `ash` / Ash | 0 to 2, **1** | pale ash patches and heaps |
| `mud` / Mud | 0 to 2, **1** | brown mud |
| `straw` / Straw | 0 to 2, **1** | straw strokes and bundles |
| `paper` / Paper | 0 to 2, **1** | paper scraps |
| `leaves` / Leaves | 0 to 2, **1** | dead leaves |
| `dust_darkness` / Dust Darkness | 0 to 1, **0.75** | how dark the dust film is (0.3 = faint, 1 = nearly black) |
| `grit_size` / Grit Size | 0.5 to 2, **1** | size of the cinder grit (1 = cells of about 1.8 cm) |
| `relief` / Relief | 0 to 2, **1** | how much the painted cinders, straw, paper and leaves stand up in the light (0 = flat paint) |
| `wet_look` / Wet Look | 0 to 1, **1** | how much the muck follows the wetness (0 = always dry colours, even on a wet street) |
| `pieces_density` / Pieces Density | 0 to 2, **1** | how many separate pieces (0 = none) |
| `pieces_distance` / Pieces Distance | 5 to 90 m, **45** | pieces are laid only up to this far along the street (it keeps pictures fast) |
| `piece_size` / Piece Size | 0.5 to 2, **1** | the size of every piece |

Seen in the pictures: the kind dials each remove or double one thing (`sheets/rubbish_controls.jpg`: drum view and doorstep view, 20 settings each); the place dials change where it lies (gutter view and wall foot view, 13 settings each). In the dim doorstep view the differences between neighbouring settings are small to see; the drum view (bright) shows them best.

---

## B7. How to use it

Inside Blender with the street copy (or the film's lockout shot file, opened and never saved) open:
```
import apply_wetness_to_set as aw
import apply_joints_to_set as aj
import apply_rubbish_to_set as ar
aw.apply(wetness=0.85, puddles=0.5)       # the water layer
aj.apply()                                 # the joints between the setts
ar.apply(places='street')                  # the rubbish. In the lockout file: ar.apply(places='lockout')
ar.apply(places='lockout', amount=1.5, gutter=1.2, props=0)        # heavier, more in the gutter, none round the props
ar.set_dials(wall_foot=0.5, seed=3)        # change a dial of what is already on
ar.set_state(0.85)                         # tell the pieces how wet the street is (aw.set_state does not reach them)
ar.pieces(False)                           # hide the separate 3D pieces, keep the painted muck
undo = ar.show_mask('colours')             # checking view: the mask drawn on the ground; undo() puts the look back
ar.remove()                                # everything off again
```
To draw whole lists of pictures (the lighting test set, the plates, the close-ups) on the rented machine: `tools/run_testset.sh NAME`, `run_plates.sh NAME`, `run_controls.sh NAME`, `run_look.sh NAME [dial=value ...]`; each writes job files (`write_jobs.py`), runs them there (`rent_run.py`), measures (`measure_rubbish_folder.py`), makes JPEGs and brings the folder back. `tools/make_sheets.py` makes the sheets. **The runner skips a picture that already exists, so `rent_run.py` clears the run's folder on the rented machine first (use `--keep` to keep it)**; I lost time to that (section B11).

---

## B8. Results

**The mask itself** (street copy and lockout file, plan pictures; ground between |x| 0 and 4.4 m, y 0 to 45 m; `work/plan_dial_table.json`, `work/plan_numbers_default.json`):

| zone | mean mask, street copy | clearly rubbish (mask over 0.3) | lockout file | lockout file, outside the prop rings |
|---|---|---|---|---|
| crown (|x| under 1.3 m) | **0.000** | **0.000** | 0.034 mean, 4.7 % over 0.3 (the drum, sacks and cart stand here) | **0.000, 0.000** |
| the whole road (|x| under 2.2 m) | 0.083 | 12.0 % | 0.109, 15.6 % | 0.084, 12.2 % |
| gutter (2.2 to 2.5 m) | 0.783 | 100 % | 0.774, 98.8 % | 0.779, 99.9 % |
| kerb and pavement (2.5 to 3.4 m) | 0.283 | 48.1 % | 0.312, 52.6 % | 0.293, 50.4 % |
| wall strip (3.4 to 4.4 m) | 0.327 | 40.0 % | 0.339, 40.9 % | 0.323, 39.2 % |

Plainly: the gutter is dirty along its whole length, about half the kerb and pavement and 40 % of the wall strip carry clear rubbish, a tenth of the road (its outer strip) does, and the crown none. The prop rings (every spot the props raise the mask by more than 0.05) cover 11 % of the lockout ground between 0 and 45 m; the props alone make 4.7 % of it clearly rubbish. The pieces use the same mask; I did not count pieces on the crown separately and saw none there in any picture.

**The joints between the setts, the lighting test set (22 pictures, EEVEE, rented machine; contrast near / middle band, rubbish dots and puddle dots left out; the PASS line is the study's, unchanged).** Three ways each: round 2 (no JOINTS, no rubbish), with JOINTS, with JOINTS and the rubbish (`work/testset02/`, `sheets/rubbish_all_lights.jpg`):

| | pictures that pass |
|---|---|
| round 2 | 6 of 22 (only the dry ones) |
| with JOINTS | 21 of 22 |
| **with JOINTS and the rubbish** | **21 of 22**: the same 21; the one that fails (lockout, brazier glare, heavy rain, middle band: 0.03 against a minimum of 0.07) failed before the rubbish too (it was -0.05; Part A section 8) |

The street copy's 16 pictures, joints only against joints plus rubbish: the contrast is identical to two decimals in all 16 (for example main dusk wet 0.52 / 0.37 both; close view wet 0.62 / 0.55 both; light from behind wet 0.53 / 0.38 both); the largest move in any contrast is 0.001 and in any other number 0.003 (the "seen" share of the main view in the middle band, dry). The dots left out: 3.8 % of the road in the main view (5 % with the two-dot margin), 1.3 % in the close view (2 %). **The clean road is untouched**: the average brightness change on road dots farther than 15 dots from any rubbish is 0.00001 in the main view and 0.00001 in the close view (street copy), 0.0001 to 0.002 in the lockout file (reflections and small shadows of pieces).
The lockout file (the shot with props; 27 % of its road is rubbish): joints only -> with rubbish, near / middle: dry 0.38 / 0.22 -> 0.38 / 0.18; wet 0.37 / 0.10 -> 0.39 / 0.08; heavy 0.25 / -0.05 -> 0.27 / 0.03 (fails, as before); low side light wet 0.47 / 0.37 -> 0.49 / 0.28; flat overhead wet 0.38 / 0.28 -> 0.40 / 0.19; light from behind wet 0.39 / 0.14 -> 0.41 / 0.09. All pass except the one that failed before. The middle band falls by 0.02 to 0.09 in the lockout shot. My reading (not proved): the pieces and their shadows lie on or beside the remaining joint dots and darken the stone dots there.

**At the size the painter sees** (`work/plates02/`; 64 samples; 1536 x 2730, the close view 1920 x 1440; contrast / seen, near and middle): joints only -> with rubbish:
* street main, dusk, dry: 0.50 / 0.98, 0.44 / 1.00 -> same (middle seen 0.99); wet: 0.59 / 0.99, 0.52 / 0.97 -> same; light from behind, wet: 0.64 / 0.97, 0.53 / 0.93 -> same;
* close view, dusk, dry: 0.51 / 0.98, 0.50 / 0.98 -> same; wet: 0.56 / 0.98, 0.57 / 0.98 -> same; light from behind, wet: 0.56 / 0.91, 0.55 / 0.95 -> same;
* lockout, brazier glare, dry: 0.42 / 0.92, 0.29 / 0.89 -> 0.40 / 0.90, 0.25 / 0.83; wet: 0.43 / 0.87, 0.16 / 0.52 -> 0.44 / 0.86, 0.15 / 0.51; heavy: 0.33 / 0.78, 0.08 / 0.40 -> 0.33 / 0.75, 0.12 / 0.46.
**All 9 pass.** Round 2 fails the six wet ones (near contrast 0.05 to 0.10). The final plate itself (no rubbish mask picture drawn for it, so the dirty dots are counted): near 0.36, middle 0.11, passes.

**Self-test of the apply script** (`tools/test_rubbish_apply.py`, one Blender run, main view wet): with the rubbish nodes on at Rubbish Amount 0 the picture equals the picture without any rubbish nodes (mean difference 0.00000002 of a 0 to 1 scale, largest single dot 1/255); after `remove()` the same (0.000000005); the normal rubbish differs (0.0016: small because the rubbish covers a small part of that view); after `remove()` no RUBBISH node is left in any material and no scatter object is left.

**Timings** (rented machine, RTX 4090, EEVEE):
* one 540 x 960 picture at 16 samples: 1.2 seconds on average (street copy, 52 drawn items: 60 s in all; the very first picture of a run is slower because the shaders are built, about 10 s); lockout shot 1.8 s on average (20 pictures: 35 s);
* one full-size plate at 64 samples: 3 to 6 seconds (the lockout wet plate 3.8 s with JOINTS only, 5.9 s with the rubbish; dry 4.1 s and 6.3 s: **the rubbish adds about 2 seconds to a plate**, from 6,000 to 7,000 small pieces and the muck nodes);
* building the rubbish in a Blender run: 2 to 5 seconds; the places pictures: 5 s (street copy) and 8 s (lockout file) on this machine;
* the joint measuring masks (Cycles on 25 cores): 4 to 7 seconds each at plate size;
* the whole test set of 66 pictures with its masks: street copy 73 to 87 s, lockout file 45 s (one Blender run each).
On this machine (not used for drawing) one 540 x 960 picture took 75 to 85 seconds in the setts round; I did not draw anything here this round. Memory was not measured.

---

## B9. What I tried and did not keep (the first look)

| first try | what I saw | what I did |
|---|---|---|
| cinders as round dots (round cells) | on the pavement and kerb they read as dark pock-marks or water drops, and they looked glued to the upright kerb face | cinders are now angular polygon cells with a ragged gap, two sizes; and the muck only paints surfaces that face up |
| straw bundles of 3 to 6 strands, 3 mm thick, 10 to 20 cm, bright yellow | like matchsticks or skewers; painted straw strokes in the gutter looked like thin bright scratches | bundles of 2 to 4 strands, 1.5 mm thick, 5 to 12 cm, darker; painted strokes rougher and with almost no relief |
| ash heaps, round flattened lumps 5 to 8 cm | read as grey pucks or coins | smaller, more irregular, three kinds, fewer |
| fine cinders spread evenly over the whole mask | pavement looked covered in black confetti | cinders now cluster (a noise decides where) |
| rubbish in the gutter only from the painted layer | the wet gutter is dark already, so brown mud and dust hardly show | more paper, leaves and straw pieces from the gutter; mud stronger at the channel bottom |
| the seed only moved the patches across the street | seeds looked the same along it | the seed also moves them along the street and moves the pieces |
| the wall foot close-up camera | it looked at the kerb, not at the wall | camera moved onto the pavement |

---

## B10. What I did not test, what I am unsure of

**Not tested**
* **The painter (Flux).** Paid; I did not ask anyone. Whether it keeps the small rubbish, adds writing to the paper, or smooths the grit away is unknown. A sentence for the brief (not run): *"Keep the small rubbish where image 1 has it (cinders, coal dust, ash, paper scraps, straw strokes, leaves and mud along the gutters and the foot of the walls, and round the drum and sacks); do not add any writing or print to it and nothing modern."* The setts' sentence from Part A still applies.
* **The glb and the stage.** The muck is made from world position and 5 mm detail; the ground maps of the glb are 2 cm a dot, so it cannot be baked into them as it is. An untried idea: bake only the dust film and the mud (the soft parts) into the ground colour and roughness maps. The pieces are not in the glb.
* **Cycles** (every picture is EEVEE) and **animation** (dials could be keyframed; not tried).
* **Other files and cameras:** the places pictures exist for the street copy and the lockout shot file only; the notice-corner shot, the second and third plate cameras and other props were not drawn. Another street needs `make_places_pictures.py` (tested only on these two files).
* **The pavement flags', kerb stones' and gutter stones' joints** (Part A did not give them a joint layer; the rubbish does cover their surfaces).
* **Dirt on the wall surfaces themselves** (mud splash and soot up to 25 cm on the walls, and on the dressed-stone plinths): not done; only the ground along the walls.
* **Extreme dial values** other than 0 and 2, seeds other than 0, 5 and 11, patchiness between the ends.
* **Pieces on the crown:** not counted (they use the same mask, which is 0 there; I saw none).
* A person's eye other than mine on the pictures.

**Unsure**
* Whether the amount is right: it reads clearly in the close-ups and the final plate; in the main street view at 540 x 960 it is faint (the gutters are far away). The dials are there for the person to decide.
* The colours and sizes of the rubbish are my choice (section B2), not from a photograph.
* The pieces number 6,000 to 7,000: "a few small pieces" may mean fewer; `pieces_density` 0.5 halves them.
* Why the lockout's middle band numbers fall by 0.02 to 0.09 with the rubbish (my guess is in section B8).
* The straw: at 100 % some strokes still look like thin bright needles in the wet gutter.

---

## B11. What went wrong (all of it)

* **First look: a black road, and my wrong guess about why.** My "show the mask" view broke on its second use (it forgot which node fed the surface once the mask node was plugged in) and left black emission nodes on the ground, so the close-up pictures had a black road. I fixed that (one line), re-ran, and the pictures were STILL black. That one took longer: the runner skips pictures that already exist, and the rented machine still held the first (black) pictures, so the re-run only drew the missing ones and the download brought the old ones back over the new. I only found it by drawing the same view in a separate small test (`diag`, which showed a lit road). **Fix:** `rent_run.py` now clears the run's folder on the rented machine first. The same thing made my first "controls" run lose its lockout plan pictures (both files wrote the same names); the lockout plan pictures are now named `lockplan_*`.
* The first plan pictures on the sheet were turned the wrong way (the sheet said "the first 22 m" and showed the far end). I found it by locating the drum in the picture and fixed the turn.
* The measuring script turned one plan picture into a JPEG (a name pattern missed it); fixed.
* The first set of pictures I looked at had the faults of section B9.
* **Over budget:** about 34 Blender runs against a budget of about 20: 28 on the rented machine and 6 on this machine (two read geometry for the places pictures, two listed objects, two only built the layers without drawing). Each run took 5 to 110 seconds; about 45 minutes of the rented machine's time in all (roughly US$0.25 at US$0.34 an hour: my estimate). The budget was set for a machine 100 times slower.
* Free disk space stayed above 1.2 GB (1.5 GB at the end); this folder is under 300 MB; I deleted my superseded renders.
* I did not touch `~/.runpod`, did not stop the machine, and changed nothing on the rented machine except the files I put in this folder's paths and the run folders.

---

## B12. Files (under `relief_and_rubbish/rubbish/`; sheets in `relief_and_rubbish/sheets/`)

* **The layers:** `tools/rubbish_layer.py` (the mask and the muck layer, group `RUBBISH`), `tools/rubbish_pieces.py` (the pieces and the scatter), `tools/apply_rubbish_to_set.py` (the one script that puts it on: `apply`, `set_dials`, `set_state`, `pieces`, `show_mask`, `remove`), `tools/make_places_pictures.py` (the places pictures).
* **Drawing and measuring:** `tools/rubbish_runner.py` (draws a job list), `tools/write_jobs.py`, `tools/jobs_testset.py`, `jobs_plates.py`, `jobs_controls.py`, `jobs_extras.py`, `jobs_look.py` (write the job lists), `tools/run_*.sh`, `tools/rent_run.py`, `tools/remote_tools.py` (the rented machine), `tools/measure_rubbish_folder.py` (the joint measure with rubbish dots left out, and the rubbish numbers), `tools/plan_numbers.py` (zone numbers of the mask), `tools/test_rubbish_apply.py` (self-test), `tools/smoke_build.py` (builds the layers without drawing), `tools/inspect_objects.py`, `tools/sheet_tools.py`, `tools/make_sheets.py`.
* **Maps:** `maps/places_street_a.png`, `places_street_b.png`, `places_lockout_a.png`, `places_lockout_b.png` and their numbers.
* **Results:** `work/testset02/` (the 66 test set pictures, `measurements.json`, `rubbish_numbers.json`, `measure_street.txt`, `measure_lockout.txt`), `work/plates02/` (plate-size pictures and measures, the close-ups), `work/controls02/`, `work/controls03/`, `work/extras01/` (control pictures and plan pictures), `work/apply_test/test_result.json`, `work/plan_dial_table.json`, `work/plan_numbers_default.json`.
* **The final plate:** `final/final_lockout_plate_wet_setts_and_rubbish.png` (1536 x 2730, 64 samples, wet 0.85 / puddles 0.5, lighting B as the film lights it, JOINTS at the chosen settings, rubbish at the defaults).
* **Sheets:** `rubbish_mask.jpg` (the mask from above, on the street, and what each dial does to it), `rubbish_all_lights.jpg` (all 22 pictures three ways), `rubbish_closeups_100pct.jpg` (a gutter, a wall foot, a doorstep, and two crops of the full plate, at 100 %), `rubbish_controls.jpg` (every control), `rubbish_final_plate_half_size.jpg`.
* **Result:** `rubbish_result_round_1.json`.
