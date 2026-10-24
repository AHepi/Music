**Round 15: independence run again for the two layers whose files changed** (`tests/independence_changed_layers_after_look_fixes/`, 512 dots, NEW default settings; the tuner also ran it at 384 dots,
`look_fixes/round2/independence/`). Only MOSS and OUTLINE AND SHADOW got new code (six new controls, section 6b), so only those two were run again, each with Amount 0 and Seed + 1; the full test above
(all five layers, 384 dots, old default settings) was NOT run again: the files of layout, colour and fade, damage and combine did not change in round 15. The script is the tuner's
`look_fixes/independence_two_layers_bake.py` and `_analysis.py`, which reuse the counting rules of `tests/independence_full.py` (a dot counts as changed when the colour moves by more than 1 step of 255, the height by more than 0.0005, the roughness by more than 0.004).

| layer changed | variant | its own region (% of dots) | colour changed % | ... of which OUTSIDE its region | height changed % (outside) | roughness changed % (outside) |
|---|---|---|---|---|---|---|
| moss | Amount 0 | 17.7 | 16.5 | 0.0 | 17.3 (0.0) | 17.2 (0.0) |
| moss | Seed + 1 | 36.3 | 33.8 | 0.0 | 35.5 (0.0) | 31.8 (0.0) |
| outline and shadow | Amount 0 | 38.4 | 37.4 | 0.0 | 38.0 (0.0) | 34.8 (0.0) |
| outline and shadow | Seed + 1 | 40.8 | 30.7 | 0.0 | 39.3 (0.0) | 11.5 (0.0) |

Every other layer's own mask (colour and fade, damage, moss, outline and shadow, slate numbers) is exactly unchanged, inside and outside, whichever of the two layers is switched off or re-seeded. So the two changed layers are still independent.
Also checked by the tuner: with the six new controls at their starting values the picture is bit for bit the old one (384 dots: colour, height, roughness differ by 0).

