### 7.7 Resolution (the same settings at 512, 1254 and 2508 dots)

**`resolution/whole_recipe/` is "before the look fixes".** The 512 and 2508 bakes there were made from the OLD default and not made again (the 2508 bake of all three maps took 18 minutes on a quiet-ish machine and would take longer now). Its 1254 entries are symbolic links (corrected: the first version did not say so; the "1254" files are links to the default tile, not a separate bake); after the look fixes the links
would have pointed at the new default, so I pointed them at `outputs/default_before_look_fixes/` and the folder agrees with itself again. The table below is the old one, unchanged:

| bake | colour + height + roughness, seconds | load on the machine |
|---|---|---|
| 512 dots | 35 | about 4 (another bake running beside it) |
| 1254 dots | 179 | about 4 |
| 2508 dots | 1088 | about 4 (another bake running beside it for most of the time) |

| bigger -> smaller (old default) | colour mean difference (of 255) | height mean difference | dots more than 40 steps apart |
|---|---|---|---|
| 2508 -> 1254 | 1.0 | 1.1 | 0.000 % colour, 0.001 % height |
| 1254 -> 512 | 1.7 | 2.4 | 0.000 %, 0.010 % |
| 2508 -> 512 | 1.6 | 2.2 | 0.001 %, 0.007 % |

**Round 15 confirmation at one smaller size** (`tests/confirm_512_after_look_fixes/`, one Blender run; `tests/compare_512_with_1254.py`; `tests/confirm_512_after_look_fixes_differences.json`; picture `confirm_512_after_look_fixes_side_by_side.jpg`).
The new default baked at 512 dots with the same settings and the 1254-dot default shrunk to 512, compared dot by dot:

| picture | mean difference (of 255) | dots more than 40 steps apart | the old default, 1254 -> 512 |
|---|---|---|---|
| colour | 1.52 | 0.000 % | 1.7 |
| height | 2.08 | 0.022 % | 2.4 |
| roughness | 1.27 | 0.000 % | |

So the new default also looks the same at 512 dots (the same slates, streaks, moss and chips; only edges and specks have fewer dots). The colour group of the 512 picture is 0.812 (1254: 0.822; the scorer enlarges a smaller picture, which blurs it). 2508 was not baked again for the new default. The 512 bake of all maps took 112 seconds on a busy machine (35 seconds before, on a less busy one; not comparable).

Baking the same settings twice gives the same picture dot for dot: for the old default the 1254-dot resolution entry and `outputs/default` were checked identical (they are the same file, see above) and the honesty check baked the old default again separately and found the colour, height and roughness identical. The tuner baked its round-1 settings twice and got identical maps (the same fitted strength and the same scores); the new default was not baked twice.

![the same crop at 512, 1254 and 2508 dots (old default)](resolution/whole_recipe/same_crop_at_three_sizes.png)

