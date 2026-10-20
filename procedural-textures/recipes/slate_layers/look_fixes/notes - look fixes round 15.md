# Notes - look fixes, round 15 (20 October)

What this file is: the plain-language record of the 15th tuning round of the slate in layers. In this round I applied the look checker's fixes
(`verify_look/LOOK_VERDICT.md`) and baked the default tile again. I looked at every step by eye and measured it. Only settings changed:
`recipe/settings.json` went from 49 to 65 entries. No layer file and no line of code in the recipe changed. The old settings are in
`recipe/settings_before_look_fixes.json` and the old maps are in `outputs/default_before_look_fixes/`. I did not change either copy after
making it.

Words used here: a **bake** is Blender drawing the maps of the tile from the recipe. A **dot** is one pixel. The **reference** is the slate
picture the look is guided by. **Relief** means the bumps, which live in the height map and the normal map. A **raking light** is a low sun,
20 degrees above the surface, that shows the relief.

## In short

The new default tile is closer to the reference by eye and by most measures:
* The paint is in broader, flatter bands, and the fine ripple is mostly gone.
* There is less moss, and it is mottled dark and light instead of a flat khaki stain.
* The big tan L-shaped chips at the lower corners are gone. A pale broken lip and small flecks now run along the lower edges.
* The lower corners are rounder. The row shadow is a cleaner two-step band. There are no black drips, no lone crack and fewer lichen dots.

The overall score went from 0.705 to 0.730, and the colour group from 0.701 to 0.755. Almost all of that colour gain comes from one fragile
measure (see "Scores"). The relief is gentler and less streaky. The level edges (lips, chips) still carry less relief than in the reference.
The tile also came out a little darker and bluer than before.

## What changed (kept), in the order I applied it

| step | problem (from the verdict) | setting | before | after | why kept |
|---|---|---|---|---|---|
| a | 1 paint | `colour_and_fade.streak_width` | 0.014 | 0.03 | broader, flatter bands (checker's tested set t4_all) |
| a | 1 paint | `colour_and_fade.mottle_tallness` | 1.1 | 2.2 | same set |
| a | 1 paint | `colour_and_fade.edge_ragged` | 0.0035 (layer file) | 0.0015 | ripple on band edges mostly gone |
| a | 1 paint | `colour_and_fade.grain_amount` | 0.05 | 0.02 | less fine busy texture |
| a | 1 paint | `colour_and_fade.streak_contrast` | 1.4 | 1.2 | same set |
| a | 2 moss | `moss.coverage` | 0.22 | 0.15, then **0.17** | less moss; raised again to 0.17 in step c, because the darker moss tones moved some moss out of the olive count (5.1 % against 6.4 % in the reference) |
| a | 2 moss | `moss.fringe_amount` | 0.3 (layer file) | 0.08 | the rows of teeth hanging from the top edge are gone |
| a | 2 moss | `moss.drip_stretch` | 1.8 (layer file) | 1.4 | same set |
| a | 2 moss | `moss.cluster_size` | 0.06 | 0.04 | clumps break into smaller pieces |
| a | 2 moss | `moss.tone_patch_size` | 0.02 (layer file) | 0.008 | finer mottling inside the moss |
| a | 2 moss | `moss.edge_raggedness` | 0.7 | 1.0 | same set |
| a | 9 lichen | `moss.lichen_amount` | 0.15 | 0.05 | fewer "polka dots" |
| a | 3 chips | `damage.corner_gain` | 1 (layer file) | 0.3 | no more big L-shapes at the lower corners |
| a | 3 chips | `damage.chip_frequency` | 110 | 160 | smaller flecks |
| a | 3 chips | `damage.chip_clustering` | 1.0 | 0.5 | flecks spread along the whole edge |
| a | 3 chips | `outline_and_shadow.lip_brightness` | 0.12 | 0.3 | the pale lip along the lower edge shows, as in the reference |
| a | 4 shape | `layout.corner_bottom_factor` | 1.5 (layer file) | 2.5 | rounder lower corners |
| a | 4 shape | `layout.ragged_bottom` | 0.0055 (layer file) | 0.008 | more uneven lower edges |
| a | 6 shadow | `outline_and_shadow.black_drips` | 0.005 | 0 | no black teeth under the rows |
| a | 6 shadow | `outline_and_shadow.shadow_drip` | 0.5 (layer file) | 0.2 | a cleaner lower border of the shadow |
| a | 8 crack | `damage.crack_amount` | 0.02 | 0 | the lone "hair" crack is gone (the heavily damaged variation can keep cracks) |
| b | 5 relief | `outline_and_shadow.lip_height` | 0.04 (layer file) | 0.1 | the lip and chipped lower edge catch more light |
| b | 5 relief | `damage.sink_depth` | 1 (layer file) | 1.6 | chips sit deeper |
| b | 5 relief | `moss.raise` | 1 (layer file) | 2.5 | moss stands up a little |
| c | 6 shadow | `outline_and_shadow.shadow_tiers` | 4 (layer file) | 2 | the shadow reads as a cleaner dark band with fewer visible steps |
| c | 7 pale slates | `colour_and_fade.outlier_size` | 1.2 | 0.8 | the brightest slate goes from 38.0 to 36.8 lightness (reference at most 34.6); the pale slate on the left is less loud |
| c | 4 shape | `layout.bottom_tilt` | 0.02 (layer file) | **0.06** | 0.035 made no visible change. 0.06 gives small steps between neighbouring lower edges. My rough measure of how much the row edge wanders goes 3.8 to 4.1 dots (reference 5.0) |
| c | 2 moss palette | `moss.tone_1` | #2b2c23 (layer file) | #23241c | darker darkest moss |
| c | 2 moss palette | `moss.tone_5` | #545342 (layer file) | #63614a | lighter lightest moss |
| c | 2 moss palette | `moss.tone_centre` | 0.7 (layer file) | 0.55 | with the wider palette alone the moss became too light (mean lightness 31.6 against 29.4 in the reference). At 0.55 the moss is 28.9 on average, and the lightness spread inside the moss is 5.9 against 6.0 in the reference (it was 4.3) |
| extra | 3 chips | `damage.chip_amount` | 0.65 | 0.72 | after step a the tan share was too low (0.79 % against 1.0 %); 0.8 overshot (1.34 %), so I chose a value in between (0.72 gives 1.03 % at 900 dots) |

`combine.tone_blend` stays at 0.7, which is NOT what the verdict suggested (see "Tried and dropped").

## Tried and dropped (with the reason)

| setting tried | result | why dropped |
|---|---|---|
| `combine.tone_blend` 0.7 to 0.45, the verdict's suggestion, alone and together with the three relief changes | Under the raking light the slate faces went flatter and the lip showed as a thin raised line. The slope measures moved AWAY from the reference: up-down slope 9.44 to 9.06, side slope 12.04 to 11.52 at 900 dots (reference 11.57 and 12.90). At 1254 dots, with the three relief changes, the overall score was 0.693 (height group 0.602, normal group 0.567). Keeping 0.7 with the same three changes scored 0.724 (height 0.650, normal 0.678) | worse by eye, by the measures and by the score |
| `combine.tone_blend` 0.55 with the three relief changes | in between (tilt 96.1, up-down 9.26, side 11.76 at 900 dots) | still below keeping 0.7 |
| `colour_and_fade.outlier_share` 0.15 to 0.08 | brightest slate unchanged (38.0) | the brightest slates are not outliers; `outlier_size` does the job |
| `damage.side_share` 0.12 to 0.05 | only 0.036 % of dots changed | invisible once `corner_gain` is 0.3 |
| `layout.bottom_tilt` 0.035 | no visible change; row wander 3.96 to 4.00 | too small; 0.06 kept instead |
| `moss.tone_centre` 0.45 (with the wider palette) | moss too dark and too little of it counts as olive (4.4 %) | 0.55 is closer |
| `moss.joint_preference` 0.15 to 0 (a try at problem 11) | olive share 5.8 to 5.2 %; the moss still stopped in a straight line at the joint | did not fix problem 11 |
| `outline_and_shadow.lip_breakup` 0.4 to 0.6 | the lip looked slightly more broken, but the up-and-down stripe measure moved from 1.00 to 1.04, away from the reference's 0.83 | spoils a measure, helps the eye only a little |
| `colour_and_fade.tone_centre` 3.7 to 3.85 and 4.0 (to undo the darker overall colour) | mean lightness 24.2 went to 24.7 and 25.3 (reference 25.2), but the brightest slate rose from 36.6 to 37.2 and 37.5. I baked 3.85 at 1254 dots: the colour group FELL from 0.755 to 0.692, almost all of it in the feature-size measure (0.722 to 0.419), and the overall score was 0.703 | it worked against problem 7 and the score; I set it back to 3.7 and baked again |

Problem 11 (moss cut off with straight edges at side joints): no small settings change fixed it. With the smaller moss clumps of step a, the
rectangular blocks from edge to edge are much rarer, but a clump that reaches a joint still ends in a straight line. A real fix would need code
in `layers/moss.py`, for example fading the growth near the side edges. I did not try that.

## Measures: before, after, reference

How it was measured: `look_fixes/measure_look.py` (rules at the top of the file). The colour measures are made at 900 dots, the way the look
checker made them. Two sets are shown because a 900-dot bake and a 1254-dot tile shrunk to 900 do not give identical numbers.

**900-dot bakes** (the checker's way; "before" = the old settings baked at 900 dots, "after" = the new settings baked at 900 dots):

| measure | before | after | reference |
|---|---|---|---|
| median colour gradient (fine busy texture) | 10.00 | 7.46 | 5.55 |
| side-to-side over up-down gradient energy (above 1 = upright stripes) | 1.18 | 1.00 | 0.83 |
| olive (moss) share | 10.7 % | 6.0 % | 6.4 % |
| tan (chip) share | 2.06 % | 1.03 % | 1.00 % |
| lightness spread inside the moss | 4.3 | 6.0 | 6.0 |
| largest moss clump (dots at 1254) | 15,334 | 8,673 | 7,013 |
| brightest slate, mean lightness | 38.7 | 36.6 | 34.6 |
| slate-to-slate lightness spread | 3.85 | 3.83 | 2.51 |

**The finished 1254-dot tiles** (`outputs/default_before_look_fixes`, `outputs/default`, reference; for the colour measures each tile is shrunk to 900 dots):

| measure | before | after | reference |
|---|---|---|---|
| median colour gradient | 9.44 | 7.54 | 5.55 |
| side-to-side over up-down gradient energy | 1.15 | 0.98 | 0.83 |
| olive share | 10.4 % | 5.7 % | 6.4 % |
| tan share | 1.91 % | 0.88 % | 1.00 % |
| lightness spread inside the moss | 4.4 | 5.8 | 6.0 |
| largest moss clump (dots) | 16,056 | 9,294 | 7,013 |
| brightest slate, mean lightness | 38.9 | 36.8 | 34.6 |
| slate-to-slate lightness spread | 3.84 | 3.84 | 2.51 |
| normal map: 99th-percentile tilt (steps of 255) | 98.7 | 103.0 | 112.6 |
| normal map: average up-down slope (level edges) | 11.2 | 10.3 | 13.5 |
| normal map: average side-to-side slope (upright edges) | 16.4 | 13.7 | 15.6 |
| up-down over side-to-side slope | 0.68 | 0.75 | 0.87 |
| mean colour (Lab: lightness, green-red, blue-yellow) | 25.1, -1.8, -1.0 | 24.2, -1.7, -1.7 | 25.2, -1.6, -1.0 |

Reading the relief rows honestly: the steepest relief is closer to the reference, and the balance between level and upright edges is better.
That is mainly because the upright streak edges fell (16.4 to 13.7). The level edges (lips, chips, row bands) did NOT get stronger: 11.2 to 10.3
against 13.5 in the reference. The three relief settings helped a little (at 1254 dots, 10.10 to 10.29), but the broader paint bands removed more
edges than they added. Problem 5 is only partly fixed.

## Scores (same-kind, `lib/texture_compare.py` against slate; the before was re-scored the same way: identical to the stored 0.705)

| | before | after |
|---|---|---|
| **overall** | 0.705 | **0.730** |
| colour group | 0.701 | 0.755 |
| - colour distribution | 0.926 | 0.890 |
| - colour spectrum | 0.609 | 0.541 |
| - colour orientation | 0.630 | 0.742 |
| - colour scale (feature size) | 0.452 | 0.722 |
| - colour gradient | 0.753 | 0.826 |
| height group | 0.654 | 0.649 |
| normal group | 0.671 | 0.678 |
| tiling (seam) | 1.0 | 1.0 |

Be careful with the colour-group gain. It comes almost entirely from the feature-size measure (0.452 to 0.722; correlation length along the rows
258 to 119 dots against 64 in the reference). That measure is a cliff. The tone-centre test showed it: one small brightness change (3.7 to 3.85)
put it back at 0.419. Without that measure, the colour group is flat: by the tool's own weights it is 0.767 before and 0.764 after. The colour
distribution and spectrum went down a little, because the tile is a little darker and bluer (see below). The score file is
`outputs/default/score_same_kind.json`, and the sheet is `outputs/default/sheet_same_kind.jpg`.

Dot-for-dot numbers (`lib/pixel_compare.py`), **for transparency only**. These are new slates, so they cannot match dot for dot:
colour difference (Delta E) 10.45 to 10.15, structure (SSIM) 0.530 to 0.549, edge skill 0.167 to 0.150, height error after best fit 37.7 to
37.6, normal angle 16.9 to 16.3 degrees. The tier is still "none" (`outputs/default/score_pixel_for_transparency.json`).

## Pictures (all in this folder)

* `before_after_colour.jpg`: reference | before | after, the whole tile.
* `before_after_zoom.jpg`: the same 0.4-tile window (dots 376 to 877 across and down) of each, at full size.
* `before_after_lit.jpg`: under the raking light (top row the whole tile, bottom row the same 0.4-tile window), reference | before | after.
  Made with `lit_several.py`, which copies the checker's `verify_look/lit_preview.py` scene unchanged.
* `maps_after.jpg`: the five maps of the new default (colour, 16-bit height, normal at strength 7, roughness, metallic, which is all 0).
* `tuning_pictures/`: every side-by-side I looked at while tuning, the lit test pictures (JPEG), and the settings and log of every test run.

What I see in them: at full size, the after tile reads as the same roof with cleaner paint, less and more varied moss, and pale broken lower
edges in place of tan corner flakes. Under the raking light the after tile looks less like rippled planks than the before tile. It is still
flatter than the reference, whose blotchy patches and chipped rims cast sharp little shadows.

## New faults I noticed (not fixed)

* **Faint horizontal "contour lines" under the raking light.** With the broader paint bands, the boundary between two steps of the fade down
  the slate becomes a long wavy horizontal line. The height follows the paint brightness (`tone_blend` 0.7), so the line shows as a thin lit
  edge across some slates (`before_after_lit.jpg`, bottom right; `tuning_pictures/view_lines.jpg` shows it in the normal map). It is small,
  but it is new.
* **Slightly darker and bluer overall.** Mean lightness is 24.2 against 25.2. The share of near-black dots is 13.8 % against 12.4 %, from the
  rounder corners, the rougher lower edges, the tilt and the darker two-step shadow. The slate paint itself is bluer than the reference's, and
  it always was: before, the extra moss hid that. Raising `colour_and_fade.tone_centre` fixes the lightness but brings back the pale slate
  (see "Tried and dropped").
* The moss's light flecks are thin upright yellow-olive strokes; the reference's moss is more dabbed. The moss also sits more as separate
  flecks than as the reference's soft olive cast over the streaks.

## How the measuring script was checked (calibration)

`measure_look.py` reproduces the checker's numbers. On a fresh 900-dot bake of the old settings it gives 10.00 / 1.18 / 10.7 % / 2.06 %
(checker: 10.0 / 1.18 / 10.7 % / 2.1 %). On the reference it gives 5.55 / 0.83 / 6.4 % / 1.00 % (checker: 5.5 / 0.83 / 6.4 % / 1.0 %).
On the checker's own t4_all settings it gives 7.06 / 0.98 / 5.8 % / 0.79 % (checker: 7.1 / 0.98 / 6.0 % / 0.8 %).
Also reproduced at 1254 dots: largest moss clump 16,056 / 7,013 (checker: 16,056 / 7,012); moss lightness spread 4.3 / 6.4 at 1254 and
6.0 for the reference at 900; brightest slate 38.9 (checker "38-39") / 34.6; normal tilt 98.7 / 112.6 (checker 99 / 113); up-down slope
11.2 / 13.5 (checker 11.1 / 13.4); side slope 16.4 / 15.6 (checker 16.3 / 15.6).
I found the olive and tan colour rules by trying a few round thresholds on the old default and the reference. The olive rule is b* above 6
and a* below 1; the tan rule is b* above 6, a* above 0 and lightness above 30. They are guesses that give the checker's numbers, not
necessarily the checker's own code.

**Numbers I could not reproduce:**
* The checker's slate-to-slate spread: I get 3.84 for the old default, the checker gave 3.6. The reference agrees: 2.51 against 2.5.
* The checker's row-band numbers (the row edge wanders 4.4 against 5.7 dots; the band is solid black over 95 % against 85 % of its length).
  My quick rule gives 3.2 against 5.0 and 100 % against 89 to 94 %. That is the same direction but different numbers, so I left it out of
  `measure_look.py` and used it only to compare tilt settings with each other.
* The relief numbers of 900-dot bakes cannot be compared with the 1254 numbers: shrinking softens the normal map. That is why there is a
  `reference@900` option, which measures the reference the way a 900-dot bake is measured.

## Tested, not tested, unsure

Tested (ran and looked at):
* every step on 900-dot test bakes next to the reference and the old default;
* the relief options at 1254 dots under the raking light, plus their scores;
* the finished tile at 1254 dots: five maps, the strength-7 normal, both scores, the measures and the lit pictures.

Baking the same settings twice gave identical maps (same fitted normal strength 7.775 and same scores).

Not tested:
* Other seeds. Everything was tuned on the default seeds, and the previous round showed the seed alone moves the colour group by about 0.07.
* The eight variations, the seed spread, the 2 x 2 and 4 x 4 areas, the ladder and the guides. None of them were re-baked (a later helper
  does that once the look is accepted). They now show the OLD default look.
* Problem 10 (the variations' own settings).
* The independence and half-tile tests. They were not re-run because no layer file changed (the task asks for them only then). The seam
  score of the new tile is 1.0.
* Other light directions than the checker's one. I did not render a 3D roof.

Unsure:
* Whether `bottom_tilt` 0.06 reads better to other eyes; the change is small.
* Whether 0.72 is the best `chip_amount`. I picked it between two tested values; the final tile confirms 1.03 % tan at 900 dots.

Left for a later helper (outside my folders, so I did not edit them):
* `recipe/controls.md`: its "default" column now disagrees with `settings.json`. It is rebuilt with
  `python3 -I recipes/slate_layers/recipe/make_controls_table.py`.
* `05 Recipe - slate in layers - how it is made.md`, the README and `final_report.json` still quote the old default's scores (0.705).

## Failures and mistakes

* My first Blender command failed straight away: "blender: command not found", because Blender is not on the PATH in this shell. Nothing
  ran. After that I used the full path `/home/user/work/blender-app/blender-5.2.2-linux-x64/blender`.
* The tone-centre detour (3.85) cost two extra Blender runs: a 1254 bake and its lit pictures. Setting it back cost two more.
* One waiting command hit the 10-minute limit of a foreground call and was moved to the background. It finished correctly (the normal map
  and the lit pictures were made).

Blender runs used: 14 of about 18. That is six test-bake runs (900 or 1254 dots, several variants each), two lit runs while tuning,
three 1254 harness bakes (3.7, 3.85, then 3.7 again) and three lit runs for the final pictures. The last bake is the one in
`outputs/default/`. Disk stayed above 2.4 GB free. The slate_layers
folder is about 420 MB (limit 460). All test bakes were deleted after measuring; only JPEG pictures and small text files are kept.

## Which of these tools work on other surfaces (brick, wood, metal, mud, gravel)

* `lit_several.py`: yes, as it is. It lights any colour + normal + roughness set.
* `views.py`: yes for any pictures. The word "reference" in it means the slate reference.
* `measure_look.py`: in part.
  - These measures work on any surface: the gradient and stripe measures, the relief measures, and the `reference@SIZE` way of comparing
    sizes. Only the reference folder name would need to change.
  - These are slate-only: the olive and tan colour rules, the moss clump and moss spread measures, and the brightest slate (it finds slates
    by their dark joints). Their thresholds were set on the slate reference.
* `bake_variants.py` and `make_pictures.py`: they point at the slate recipe and slate folders. Each would need its path changed (a few lines).

## What is in this folder

* Scripts:
  - `measure_look.py`: the measures.
  - `bake_variants.py`: several settings variants in one Blender run.
  - `lit_several.py`: raking-light pictures.
  - `views.py`: side-by-side pictures.
  - `make_pictures.py`: the four pictures above.
* Settings sets:
  - `set_t4_all.json`: the checker's set.
  - `set_relief.json`: the checker's relief suggestion.
  - `set_candidate_a.json`, `set_candidate_b.json`: steps on the way.
  - `set_final.json`: everything changed in this round.
* Measures and scores:
  - `tuning_measures.json`, `tuning_measures_round8.json`: every test bake.
  - `measures_before_after_reference.json`: before, after and reference.
  - `score_before_same_kind_rescored.json`: the before re-scored.
* Logs:
  - `final_bake.log`: the last harness bake (also copied to `outputs/default/log.txt`).
  - `lit/`: the logs of the lit runs.
  - `lit_jobs.json`, `lit_jobs_after.json`: what the lit runs drew.
