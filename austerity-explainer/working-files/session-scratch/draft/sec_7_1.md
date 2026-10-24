### 7.1 The default tile against the reference (a guide, not a target)

**Round 15 update.** The numbers below are for the NEW default tile (after the look fixes), baked by the tuner at 1254 dots through the harness (`outputs/default/`);
scores are read from `outputs/default/score_same_kind.json` and `score_pixel_for_transparency.json`. The "before" column is the old default
(`outputs/default_before_look_fixes/`, same measuring; the old file was re-scored by the tuner and gave the same numbers).

| same-kind measure | now | before the look fixes | in plain words |
|---|---|---|---|
| **overall** | **0.778** | 0.705 | |
| colour group | 0.822 | 0.701 | the brief's aim was 0.8 or more: **reached by this number** at the default seeds (0.822) and on average over five sets of seeds (0.810, section 7.3), but see the caution below |
| - colour distribution | 0.867 | 0.926 | the same colours in the same amounts (a little lower: the tile is a bit darker and bluer) |
| - colour spectrum | 0.707 | 0.609 | how much variation there is at each size |
| - colour orientation | 0.709 | 0.630 | which way the edges run |
| - colour scale (feature size) | 0.899 | 0.452 | how far the picture stays similar to itself sideways: 54 dots on ours now (258 before), 64 on the reference |
| - colour gradient | 0.858 | 0.753 | how sharp the edges are |
| height group | 0.735 | 0.654 | with `combine.tone_blend` 0.7: about 70 % of this height is paint brightness, not real relief (section 5) |
| normal group | 0.616 | 0.671 | a fall: the tilt measure went 0.611 to 0.525 and the components 0.830 to 0.781; normal-to-height agreement 0.534 to 0.560 (a tiny raw distance that jumps about) |
| tiling | 1.0 | 1.0 | seamless |

**Which normal map?** (corrected: the first version of this guide had the two normal maps the wrong way round.) The normal group above is for
`outputs/default/normal.png`, made by `integration/make_normal.py` (3 x 3 slope of the 8-bit height, strength 7, the rule the reference's own normal map was made with).
The harness's own normal (`normal_harness_sobel.png`, a two-neighbour slope with a strength fitted to the reference's slope spread, 8.0 now) scores differently: for the old default the
strength-7 normal gave overall 0.705 (normal group 0.671) and the harness's normal 0.695 (normal group 0.604). For the new default the ladder table (7.2) shows both: overall 0.778 with the strength-7 normal,
0.789 with a harness-style normal made by `integration/score_set.py`.

**Caution about the colour group gain (0.701 to 0.822).** Almost all of it is the "feature size" measure (0.452 to 0.899), which is a cliff: one small change of brightness
moved it by 0.3 in round 1 of the tuning. Without that measure the colour group, by the tool's own weights, went from 0.767 to 0.801. The gain also shows on all five seed sets
(section 7.3: feature size 0.90 to 0.96 on every set), so it is not a lucky draw; but the same-kind score is a guide, not a judgement of the look. The look checker, judging
by eye, said "nearly" the same hand (section 6b).

Mean colour (Lab): reference 25.2, -1.6, -1.0; default now 23.7, -1.8, -1.3 (before 25.1, -1.8, -1.0): a little darker and bluer. Height follows colour with correlation 0.989 (reference 0.993; before 0.987).

The dot-for-dot numbers, **for transparency only** (these are new slates, so they cannot match dot for dot), now / before: colour mean difference 9.9 / 10.5 (Delta E), structure (SSIM) 0.555 / 0.530,
edge skill 0.166 / 0.167, height error after best fit 37.3 / 37.7 steps of 255, normal error 16.3 / 16.9 degrees; tier "none" both times. The first slate build, which traced the reference, reached tier "close";
this build is not meant to.

