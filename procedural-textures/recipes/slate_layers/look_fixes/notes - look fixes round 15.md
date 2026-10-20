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
  Made with `lit_several.py`, which copies the checker's `verify_look/lit_preview.py` scene unchanged. Same light, size and window for all three panels; one asymmetry that the picture does not show: the reference is lit WITHOUT a roughness map (the reference set has none), the before and after tiles WITH theirs (see "Corrections after the honesty check" at the end).
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


---

# Round 2 (20 October, after the look checker judged round 1)

What this part is: the plain-language record of the second tuning round. The look checker (verdict in `../verify_look_after_fixes/round_1/critic_result.json`)
found that round 1 helped (4 problems fixed, 4 better, 3 the same, none worse) but that the tile was "nearly" the same hand, not yet. This round fixes what it found,
in its order: regressions first (what round 1 made worse), then new problems, then problems that were still visible. The method was the same: change one thing, bake
small (900 dots), look, measure, keep only what helps. Then the default tile was baked again at 1254 dots.

Words used: **bake** = Blender draws the maps from the recipe. **Dot** = one picture point. **Reference** = the slate picture that guides the look. **Relief** = the bumps (height map and normal map).
**Raking light** = a low sun that shows the relief. **Facet** = a flat patch of paint with straight edges, like a cut gem. **Layer file** = the program text of one layer of the recipe.

## In short

* The paint has its fine grain back and the slates differ less from each other (the pale and dark outlier slates are mostly gone).
* The moss is now a soft, see-through olive wash that lets the slate streaks show through, as in the reference, instead of small crisp khaki flakes. Moss no longer ends in a straight cut along the side joints.
* The chips along the lower edges are chunkier and cream-tan, not a thin orange line.
* The lower corners are rounder and the lower edges more uneven.
* The overall same-kind score went from 0.705 (old default) and 0.730 (after round 1) to **0.778**. By the tool's own weights the colour group without its fragile feature-size measure goes 0.767, 0.764, 0.801.
* **Still wrong, and I want to say it plainly:** (1) large flat paint facets with straight, slanting edges show on many slates (more obvious than the checker noticed; I tried several settings and none removed them); (2) the relief is only a little better (mean tilt 20.2 against 19.7 after round 1; the reference has 23.7); (3) the paint is more upright-stripy than after round 1 (2.08 against 1.89; reference 1.61); (4) the tile is still a little darker than the reference (mean lightness 23.7 against 25.2).

(Reading note added after the honesty check: in this Round 2 part, a change written "a to b" is measured from the END OF ROUND 1 unless the old default is named. For the whole way from the old default, see the "Measures" tables below and item 5 of "Corrections after the honesty check" at the end.)

## What the checker found and where each point stands now

My own reading, by eye and by the checker's own measures (I copied its script to `round2/independent_measures.py`; with the old tile it gives exactly the numbers in the verdict).

| # | the checker's point | round 1 (its words) | now |
|---|---|---|---|
| 1 | paint: liquified tongues, wavy edges | better | the fine grain is back (grain level 0 -> 1, the reference has 1). Median paint slope 1.91 (reference 1.86; round 1: 1.25). Flat share 9.9 % (reference 10.9 %; round 1: 18.9 %). Hard-edge share 23.8 % (reference 15.1 %), unchanged. Side-to-side over up-down slope 2.08 (reference 1.61): worse than round 1 (1.89). New: straight-edged flat facets, see "Not fixed". |
| 2 | moss: too much, flat stain, teeth | better | amount right; the moss is a see-through wash. Inside the moss the steepest edges are 10.6 (reference 7.1; round 1: 16.6); at the moss edge 17.0 (reference 15.9; round 1: 24.0). Largest clump 8,439 dots (reference 7,013). Looks like soft clouds, not flakes. By the tuner's hue rule the olive share fell to 4.0 % (reference 6.4 %) because see-through moss is greyer; with the greenish-grey wash counted (b* 2 to 6, a* below 0) it is 4.0 + 7.5 = 11.5 % against 6.4 + 5.9 = 12.3 %. |
| 3 | chips: L-shapes gone, but thin | fixed | chunkier: tan share 1.47 % (checker's rule; reference 1.56 %), tan in pieces of 300+ dots 25.2 % (reference 35.6 %; round 1: 13.7 %), largest piece 1,293 dots (reference 1,047). |
| 4 | slate shape | better | lower-edge wobble 2.21 dots (reference 2.98; round 1: 1.78); corner rise 14.8 dots (reference 17.7; round 1: 12.3). Rows are still straight. |
| 5 | relief | better, weaker | only slightly better: see "Relief". |
| 6 | shadow under rows | fixed | unchanged. |
| 7 | pale flat outlier slates | same | slate-to-slate spread of mean grey 5.57 (reference 5.51; round 1: 8.89); lightest slate 80.8 (reference 79.4; round 1: 88.8); slates more than 12 grey levels off the middle: 2 of 59 (reference 3 of 45; round 1: 9). The tuner's own measure: spread 3.84 -> 2.65 (reference 2.51), brightest slate 36.8 -> 34.1 (reference 34.6). Plain slates (inner spread under 8): 3 of 59 (reference 1 of 45; round 1: 4). |
| 8 | lone crack | fixed | still none. The short pale hairline the checker found near the right edge was not touched. |
| 9 | lichen discs | fixed | 24 round tan dots (reference 28; round 1: 29). |
| 10 | variations | same | looked at, not changed: see "The variations". |
| 11 | moss cut straight at side joints | same | fixed with a small code change: share of moss dots within 14 dots of a side joint 14.5 % -> 7.2 % (reference 6.5 %). |
| new 1 | moss reads as flakes / peeling paint | - | fixed: see-through moss (code change), see point 2. |
| new 2 | chips thin | - | better, see point 3. |
| new 3 | relief flatter, contour lines, scratch-like ridges | - | partly: mean tilt a little higher; contour lines and ridges are still there. |
| new 4 | paint grain gone, less contrast inside slates, more plain slates | - | grain back; inner spread 11.15 (reference 12.27; round 1: 10.83); plain slates 3 against 4. |
| new 5 | slate colour varies less (b* spread), darker and bluer | - | I raised `tint_amount` and `patch_tint`; the slate-face blue-yellow spread is 1.80 against 1.64 in the reference. Mean b* of the slates went from -1.87 to about -1.56 in the test (reference -1.04). Overall mean lightness is still 23.7 against 25.2. |
| new 6 | tiled 3 x 3: repeat landmarks | - | the outlier slates that made the landmarks are mostly gone. No seam: the wrap-round difference across the tile edge is no bigger than between two inside neighbours (grey 2.85 against 3.74 left-right, 1.24 against 1.58 top-bottom). See `round2/tiled3x3_seam_crop_1to1.jpg`. |

## What changed in this round (settings, all in `recipe/settings.json`; the file now has 73 entries, round 1 ended with 65)

| step | for | setting | after round 1 | now | why |
|---|---|---|---|---|---|
| a | grain | `colour_and_fade.grain_amount` | 0.02 | 0.04 | the checker's tested fix: fine grain back (flat-paint noise level 0 -> 1, reference 1) |
| a | outliers | `colour_and_fade.tone_spread` | 1.0 | 0.45 | slate-to-slate spread: the checker's 0.6 gave 3.06 (reference 2.51); 0.45 with the two settings below gave 2.78 on a 900-dot test |
| a | outliers | `colour_and_fade.outlier_share` | 0.15 | 0.08 | fewer pale and dark slates |
| a | outliers | `colour_and_fade.outlier_size` | 0.8 | 0.7 | the remaining ones are less far off |
| b | colour | `colour_and_fade.tint_amount` | 0.7 | 0.9 | more teal-green and warm slates, less blue |
| b | colour | `colour_and_fade.patch_tint` | 0.4 (layer file) | 0.55 | same |
| c | chips | `damage.chip_frequency` | 160 | 115 | chunkier flakes (the checker's untested suggestion was 130) |
| c | chips | `damage.chip_amount` | 0.72 | 0.68 | keeps the tan share near the reference with the bigger flakes |
| c | chips | `damage.chip_clustering` | 0.5 | 0.55 | flakes gather into stretches with clean edge between |
| c | chips | `damage.chip_breakup` | 1.1 | 0.8 | fewer holes and loose flecks: chunkier |
| c | chips | `damage.chip_depth` | 0.02 | 0.024 | flakes reach a little further in |
| d | shape | `layout.corner_bottom_factor` | 2.5 | 3.0 (the top of its range) | rounder lower corners |
| d | shape | `layout.ragged_bottom` | 0.008 | 0.01 (the top of its range) | more uneven lower edges |
| d | shape | `layout.bottom_tilt` | 0.06 | 0.08 | small steps between neighbouring lower edges |
| e | moss | `moss.coverage` | 0.17 | 0.30 | the moss is now see-through, so more of it is needed to read as much |
| e | moss | `moss.patchiness` | 0.75 | 0.9 | moss gathers in a few areas, as in the reference |
| e | moss | `moss.edge_raggedness` | 1.0 | 0.6 | softer, less flaky edges (the checker's tested value) |
| e | moss | `moss.cluster_size` | 0.04 | 0.055 | broader clumps (the checker's tested value) |
| e | moss | `moss.tone_patch_size` | 0.008 | 0.02 | broader tone patches: calmer inside (back to the layer file's value) |
| e | moss | `moss.rim_lightening` | 0.5 (layer file) | 0.2 | no light yellow rim: that made the flakes |
| e | moss | `moss.lichen_amount` | 0.05 | 0.07 | the bigger chips had swallowed some lichen discs |
| e | moss | `moss.rim_opacity`, `core_opacity`, `side_clearance`, `fleck_amount` | (did not exist) | 0.5, 1.0, 0.012, 0.5 | the four new controls, see "Code changes" |
| f | relief | `outline_and_shadow.joint_texture`, `joint_texture_size` | (did not exist) | 0.35, 150 | new controls, see "Code changes" |
| g | paint | `colour_and_fade.streak_contrast` | 1.2 | 1.3 | a little more contrast inside the slates |
| g | paint | `colour_and_fade.fade_amount` | 0.85 | 0.9 | a little more fade (1.0 and 1.15 gave more relief and inner contrast but also more upright stripes and more dark: see below) |
| g | paint | `colour_and_fade.mottle_tallness` | 2.2 | 1.5 | shorter paint patches: a little less upright-stripy |

## Code changes (two layer files; both listed in `../integration/CHANGES_TO_LAYER_FILES.md`, rows 3 to 6)

I changed code only where no setting could do it. Every new control starts at the value that gives the OLD picture, so nothing moves unless the default tile's settings turn it on.
* `layers/moss.py`
  - `rim_opacity` and `core_opacity`: the moss paint can be see-through. Opacity runs from the rim value at the edge of a clump to the core value inside it. Only the paint is see-through; the raised height and roughness of moss are unchanged. This is what turns crisp flakes into a soft wash and lets the slate streaks show through.
  - `side_clearance`: moss growth fades out near the side joints, so a clump no longer ends in a straight cut along the joint (problem 11).
  - `fleck_amount`: strength of the small light and dark flecks inside the moss (they were a fixed amount, and made the moss much busier than the reference's).
* `layers/outline_and_shadow.py`
  - `joint_texture`, `joint_texture_size`: the black of the joints varies faintly from dot to dot, as the reference joints do (they have a brightness spread of 2.8 in the black core; ours was 0.5). The relief follows the colour, so the joints get a faint texture in the relief too. I first tried 0.5 at 600 mottles per tile and it looked like grit at 1:1, so the default tile uses 0.35 at 150. Its effect on the relief numbers is very small.
* The old copies of both files: `round2/layer_files_before_round2/`. `recipe/controls.md` was rebuilt with `recipe/make_controls_table.py` (it also fixes the stale default column left from round 1).

Tests for the code changes:
1. **Nothing moves at the old values:** the settings of the end of round 1 (copy in `round2/settings_after_round1.json`) baked at 384 dots with the old files and with the new files gave identical colour, height and roughness pictures (largest difference 0 in all three).
2. **Independence re-run for the two changed layers** (moss and outline_and_shadow; each switched off and given a new seed, with the settings of the new default tile): no dot changed outside the layer's own region, and no other layer's pattern changed. Table in `round2/independence/independence_two_layers_table.md` and in the changes file. The layers that did not change were not re-tested.
3. Not re-run: the half-tile shift test. The new controls read the same slate coordinates and seamless noise as the old ones, and the finished tile has no seam (above), but I did not run the half-tile test itself.

## Relief (problem 5): what I tried and what is left

The reference's relief is steeper everywhere. Where the gap is biggest (finished tiles, steps of 255): 

| measure | before round 1 | after round 1 | now | reference |
|---|---|---|---|---|
| steepest 1 % tilt | 98.7 | 103.0 | 103.5 | 112.6 |
| mean tilt | 22.5 | 19.7 | 20.2 | 23.7 |
| average up-down slope | 11.2 | 10.3 | 10.6 | 13.5 |
| average side slope | 16.4 | 13.7 | 14.2 | 15.6 |

* What I found: most of the height comes from the paint brightness (`combine.tone_blend` 0.7), so the "real" relief settings (lip, chip depth, shadow height) are scaled down to 30 % and change almost nothing: lip_height 0.14 + sink_depth 2.2 + shadow_height 0.2 moved the up-down slope from 10.22 to 10.23.
* In the reference the joints are much steeper than ours (mean tilt in the joint areas about 42 against 26): their black is faintly textured, ours was flat. That is why I added joint texture. At the strength that looks right it only adds about 1 %.
* Tried and dropped: `combine.tone_blend` 0.8 (slopes +4 %, but under the raking light I could not tell it from 0.7, and more of the height would come from paint edges, which is the source of the contour lines); `combine.height_gain` 1.7 with `colour_and_fade.tone_height` 0.4 and 2.4 with 0 (these LOWERED the slopes: the paint-following part carries more than I expected); `colour_and_fade.fade_amount` 1.0 and 1.15 (more relief, mean tilt 18.0 and 18.8 against 17.2 at 0.85 in 900-dot tests, but the paint got more upright-stripy and darker).
* Honest summary: the relief is still weaker and smoother than the reference, with the same faint contour lines and thin ridges. A real fix needs a different way of making the height (not from the paint brightness alone), which is a larger change.

## Measures (finished 1254-dot tiles)

The tuner's measures (`measure_look.py`; colour measures after shrinking to 900 dots):

| measure | before round 1 | after round 1 | now | reference |
|---|---|---|---|---|
| median colour gradient (900-dot artefact, see the checker) | 9.44 | 7.54 | 7.54 | 5.55 |
| side-to-side over up-down gradient energy | 1.15 | 0.98 | 0.98 | 0.83 |
| olive share (hue rule; under-counts see-through moss) | 10.4 % | 5.7 % | 4.0 % | 6.4 % |
| tan share | 1.91 % | 0.88 % | 1.19 % | 1.00 % |
| lightness spread inside the moss | 4.4 | 5.8 | 5.6 | 6.0 |
| largest moss clump (dots) | 16,056 | 9,294 | 8,439 | 7,013 |
| brightest slate mean lightness | 38.9 | 36.8 | 34.1 | 34.6 |
| slate-to-slate lightness spread | 3.84 | 3.84 | 2.65 | 2.51 |

The checker's measures (`round2/independent_measures.py`, native 1254 dots):

| measure | before round 1 | after round 1 | now | reference |
|---|---|---|---|---|
| paint median slope | 3.06 | 1.25 | 1.91 | 1.86 |
| flat-paint share | 7.4 % | 18.9 % | 9.9 % | 10.9 % |
| hard-edge share | 28.4 % | 24.7 % | 23.8 % | 15.1 % |
| side-to-side over up-down slope (paint) | 2.44 | 1.89 | 2.08 | 1.61 |
| fine grain level | 1 | 0 | 1 | 1 |
| inner spread of a slate (mean / smallest) | 11.7 / 6.7 | 10.8 / 6.2 | 11.2 / 6.6 | 12.3 / 7.8 |
| spread of slate mean greys | 8.48 | 8.89 | 5.57 | 5.51 |
| moss near side joints | 12.8 % | 14.5 % | 7.2 % | 6.5 % |
| moss in pieces of 1500+ dots | 71.6 % | 51.7 % | 51.0 % | 52.8 % |
| tan share (checker's rule) | 2.23 % | 1.18 % | 1.47 % | 1.56 % |
| tan in pieces of 300+ dots | 52.9 % | 13.7 % | 25.2 % | 35.6 % |
| lower-edge wobble / corner rise (dots) | 1.33 / 6.8 | 1.78 / 12.3 | 2.21 / 14.8 | 2.98 / 17.7 |
| mean colour (Lab) | 25.1, -1.8, -1.0 | 24.2, -1.7, -1.7 | 23.7, -1.8, -1.3 | 25.2, -1.6, -1.0 |
| share of dark dots (grey under 30) | 10.9 % | 12.5 % | 12.9 % | 11.3 % |

Full numbers: `measures_round2.json`. Moss character (my own small script `round2/moss_character.py`, general numbers only): at the moss edge the steepest slope is 17.0 (reference 15.9, round 1: 24.0), inside the moss 10.6 (reference 7.1, round 1: 16.6).

## Scores (same-kind tool `lib/texture_compare.py`, and `lib/pixel_compare.py` for transparency)

| | before round 1 | after round 1 | now |
|---|---|---|---|
| **overall** | 0.705 | 0.730 | **0.778** |
| colour group | 0.701 | 0.755 | 0.822 |
| - distribution | 0.926 | 0.890 | 0.867 |
| - spectrum | 0.609 | 0.541 | 0.707 |
| - orientation | 0.630 | 0.742 | 0.709 |
| - scale (feature size, fragile) | 0.452 | 0.722 | 0.899 |
| - gradient | 0.753 | 0.826 | 0.858 |
| height group | 0.654 | 0.649 | 0.735 |
| normal group | 0.671 | 0.678 | 0.616 |
| tiling (seam) | 1.0 | 1.0 | 1.0 |

* The colour group without the fragile feature-size measure (by the tool's weights): 0.767, 0.764, 0.801. So about three quarters of the colour gain (78 %: 0.094 of 0.121, by the tool's weights) is the cliff measure, and about a quarter is real and not the cliff (0.767 to 0.801 without it; corrected after the honesty check, this line first said "the colour gain is real, not only the cliff measure"). The best gain is the colour spectrum (0.541 -> 0.707: the pale and dark outlier slates are gone). The colour distribution is a little lower (the tile is a little darker).
* The height group rises (0.649 -> 0.735; the distribution and spectrum of the height improved), the normal group falls (0.678 -> 0.616; with the strength-7 normal of this table only: with the harness's own normal it rose 0.604 -> 0.690 from before round 1 to now, so it is a weak signal, not a loss; see "Corrections after the honesty check" at the end). The normal tilt measure is 0.525 (round 1: 0.541), the components 0.781 (0.804). The normal-to-height agreement measure (0.560; round 1: 0.836; before: 0.534) is a tiny raw distance (0.005) and jumps about between runs; the correlations behind it are close to the reference's in all three tiles. I did not chase this.
* Dot-for-dot (transparency only; these are new slates, so they cannot match): colour difference (Delta E) 10.45 -> 10.15 -> 9.89, structure (SSIM) 0.530 -> 0.549 -> 0.555, edge skill 0.167 -> 0.150 -> 0.166, height error after best fit 37.7 -> 37.6 -> 37.3, normal angle 16.9 -> 16.3 -> 16.3 degrees. Tier: none (unchanged).
* The first 1254 bake of this round (joint texture 0.5 at 600, fade 1.0, tallness 2.2) scored overall 0.780 (colour 0.822, height 0.727, normal 0.646). I rejected it by eye (grit in the joints, too upright-stripy), and the second bake with the settings above scores about the same. Score files: `outputs/default/score_same_kind.json`, `score_pixel_for_transparency.json`; the first bake's are in `round2/first_final_bake_notes/`.
* Scores move about with the random seed by about 0.07 (round 1 notes), so a gain of 0.05 is real but not a precise number.

## Pictures

* `before_after_colour.jpg`, `before_after_zoom.jpg`, `before_after_lit.jpg`, `maps_after.jpg`: remade (before = `outputs/default_before_look_fixes`, after = the new default). The round-1 versions are kept in `round_1_pictures/`.
* `round2/`: the pictures I looked at while tuning (moss variants, chips, joints, facets), `final2_full3.jpg` and `final2_crop_a.jpg` (reference | after round 1 | now), `lit_blend_test.jpg`, `variations_on_new_default_small.jpg`, `variations_v6_v2_v3_512.jpg`, `tiled3x3_after_round2.jpg`, `tiled3x3_seam_crop_1to1.jpg`.

What I see: at 1:1 the moss is a soft olive wash that follows the slate streaks, the chips are chunky cream-tan flakes along the lower edges, the lower corners are rounder, the grain is back. Under the raking light the tile looks about as flat as after round 1: the reference's crumbly chipped surface is not reached.

## The variations (problem 10)

I baked the eight variations on the new default at 512 dots, colour only (`round2/variations_on_new_default_small.jpg`). All eight still read as the intended roof types. The "dark and wet" one (v6) is very dark, with several nearly black faceted patches (the checker called them burnt patches); "heavily damaged" (v3) has very chunky chips; "more moss" (v2) and the rest look fine. I did NOT change `variations/variations.json` and did not re-bake the variation pictures at 1254 dots: they still show the OLD default look. A later helper should re-bake them. My untested suggestion for v6: `stain_amount` 0.9 -> 0.6, `stain_cover` 0.5 -> 0.35, `tone_centre` 2.3 -> 2.8.

## Tried and dropped in this round

| tried | result | why dropped |
|---|---|---|
| `streak_contrast` 1.35 alone | inner spread 10.47 -> 10.82, relief +1 % | tiny; 1.3 kept together with the fade change |
| `damage` chips: freq 85 / 110 / 100 with clustering 0.9 to 1.2, depth 0.03 | tan share 1.5 to 2.3 %, big pieces 46 to 56 % (reference 35.6 %), largest piece 1,464 to 1,564 (reference 1,047), lichen discs 8 to 11 | too big and too much; 115 / 0.68 / 0.55 / 0.024 is in between |
| `mottle_tallness` 1.7 | slate spread worse (3.21) | not kept (1.5 was kept later with fade 0.9, which is a different mix) |
| `tint_amount` 0.9 + `patch_tint` 0.55 | kept | - |
| `moss` opacity: rim 0.35 / 0.25 with core 0.85 / 0.7 | the moss became too faint, almost invisible | rim 0.5, core 1.0 with coverage 0.30 kept |
| `moss.tone_spread` 0.6 + `fleck_amount` 0.2 + `drip_stretch` 1.2 + rim 0.4 ("calm") | inside and edge steepness too low (5.1 and 9.4 against 7.1 and 15.9), the moss too dark and too smooth | too calm |
| `combine.tone_blend` 0.8 | see "Relief" | no visible gain |
| `combine.height_gain` 1.7 / 2.4 with `tone_height` 0.4 / 0 | relief went DOWN | dropped |
| `colour_and_fade.fade_amount` 1.0 and 1.15 | inner spread 11.55 / 12.22 (reference 12.27), relief +4 / +9 %, but upright-stripiness 2.08 / 2.19, dark share 13.6 / 14.6 %, colour score down | 0.9 kept as a middle |
| facet fixes: `streak_width` 0.024 with `edge_ragged` 0.002; `edge_ragged` 0.003; `streak_bend` 0.012 and 0.02 with `edge_ragged` 0.0025; `mottle_tallness` 1.5 and 1.2 | the straight-edged facets stayed in every one (g1 changed which slates have them and made the paint more stripy: 2.24) | none of them fixes it; see "Not fixed" |
| `joint_texture` 0.5 at 600 mottles | looked like grit at 1:1 in the 1254 bake | 0.35 at 150 kept |

## Not fixed (what the next person should know)

* **Facets.** Many slates carry flat patches of paint with straight, slanting edges (best seen in `round2/tiled3x3_seam_crop_1to1.jpg` and `before_after_zoom.jpg`, lower left slate). The cause is in `colour_and_fade.py`: the mottling uses tall Voronoi cells (cells whose borders are straight lines) about 56 dots wide and 130 to 290 dots tall, so a cell is as tall as a whole slate and its slanting border is long and straight. They were already there after round 1 (the checker did not mention them), and the wider paint bands of round 1 made them bigger. The reference has organic, ragged patch outlines. Idea (not tried, it is a code change): bend the cell coordinates with a medium-size noise (wavelength about 20 to 40 dots, push about 10 dots) before the cells are drawn, so no border stays straight over a long run.
* Relief: see above.
* Upright stripes: still more than the reference (2.08 against 1.61).
* Overall a little darker (23.7 against 25.2) and a little bluer (b* -1.3 against -1.0). `colour_and_fade.tone_centre` is a cliff for the feature-size score (round 1), so I did not touch it.
* The 1254-dot variation pictures, seed spread, 2 x 2 and 4 x 4 areas, ladder and guides still show the OLD default.
* The hairline near the right edge (checker: "x1175 to 1254, y660") was not touched.

## Tested, not tested, unsure

Tested (ran and looked at, or measured): every step on 900-dot test bakes (colour, and height where the relief mattered), next to the reference and the earlier tile; the moss, chip, joint and fade options by eye and by numbers; the finished 1254 tile (five maps, strength-7 normal, both scores, all measures, raking-light pictures, a 3 x 3 tiling check); the code changes (nothing moves at old values, independence of the two changed layers); the eight variations at 512 dots (looked at only).

Not tested: other seeds (everything was tuned on the default seeds); other light directions than the checker's one; a 3D roof render; the half-tile shift test; independence of the layers whose files did not change; the variations at 1254 dots; the colour-tint change on other seeds. The facets fix is only an idea.

Unsure: whether 0.35 at 150 for the joint texture is worth having at all (its relief effect is about 1 %; I kept it because the joints look more like the reference's and because the band is no longer perfectly flat); whether the see-through moss will read the same under other lights; whether fade 0.9 and tallness 1.5 are better than round 1's 0.85 and 2.2 (the numbers say yes on colour score, stripiness, slate spread and dark share, and no on inner contrast and relief; I chose by those numbers and by eye).

## Failures and mistakes (round 2)

* One Blender launch failed at once: I wrote the variants file with a repeated setting name, the script stopped, and the launch still started with an empty argument ("JSONDecodeError"). Nothing was baked; I corrected the file and launched again.
* The first finished bake (joint texture 0.5 at 600 mottles, fade 1.0, tallness 2.2) had to be thrown away and re-baked: the joints looked like grit at 1:1 (my 900-dot tests showed it only faintly) and the paint was too upright-stripy. That cost one extra 10-minute run.
* An early try: lip_height 0.14 + sink_depth 2.2 + shadow_height 0.2 changed nothing measurable (the "real" relief is scaled to 30 %).
* `combine.height_gain` / `tone_height` lowered the relief instead of raising it.
* Measurement trap: the harness's own normal map (`normal_harness_sobel.png`) is a different normal from the strength-7 one; I first measured the wrong one for a minute (tilt 109 instead of 104) before noticing.

Blender launches in this round: 12 (11 real runs and the failed one): 7 test-bake runs (each with 3 to 9 variants of moss, chips, colour, shape, relief, fade, joints or facets; one of them also baked the independence-test pictures), 1 raking-light test, 2 finished 1254 bakes, and 1 final raking-light-and-variations run. Disk free stayed above 1.8 GB; `slate_layers` is about 430 MB (limit 460 MB). All test bakes were deleted after measuring; only JPEG pictures and small text files are kept.

## What is new in this folder (round 2)

* `round2/independent_measures.py` (the checker's measures, copied), `round2/moss_character.py` (moss numbers), `independence_two_layers_bake.py` and `independence_two_layers_analysis.py` (the independence re-test), `round2/run_facets_and_independence.py` and `round2/run_lit_and_variations.py` (run several jobs in one Blender process), `bake_variants.py` (a variant can now name its own bake size).
* `round2/run1.json` to `run7.json`: the variants of each test run; `round2/*_measures.json`, `*_independent*.json`: their measures. `round2/set_F_round2_all_changes.json`: all settings of this round. `round2/settings_after_round1.json`: the settings at the end of round 1.
* `measures_round2.json`, `round_2_tuner_result.json`, `final_bake_round2.log`.

## Corrections after the honesty check (20 October, after the second honesty check, `verify/after_look_fixes/HONESTY_VERDICT_AFTER_LOOK_FIXES.md`)

What this list is (plain words): the honesty checker re-measured the round-15 numbers and found they held, but listed wording and labelling faults. This is what the corrector (a later helper) changed, in these notes, the two guides, the folder map, `final_report.json`, `rebake_result.json`, `round_2_tuner_result.json` and a few small files. No setting, layer file, picture or bake was changed; two scores were re-run without Blender (`corrections_after_honesty_check/`).

1. **Half-tile "nothing got worse" was not quite true.** The outline-and-shadow mask rose slightly (one tile: raw 1.54 to 1.62, blurred 0.37 to 0.41; 2 x 2: raw 2.99 to 3.05, blurred 0.68 to 0.74) and so did the 2 x 2 damage mask (blurred 0.673 to 0.688). Nearly everything else got smaller; all are still tiny next to the controls.
2. **Half-tile ratio** is 18 to 143 times smaller than the controls over all sixteen rows, not 18 to 95.
3. **Normal group "fell (0.671 to 0.616)"** is true only for the strength-7 normal; with the harness's own normal it rose 0.604 to 0.690 (re-scored both ways). About 0.07 either way: a weak signal, not a loss. Fixed in the Recipe guide (7.1, known gaps), `rebake_result.json`, the round-2 notes above and `round_2_tuner_result.json`.
4. **Slate-grey spread:** 8.9 is the value after round 1; the old default's is 8.48. The 5.57 / 5.51 numbers come from the copy of the look checker's script; the tuner's own `measure_look.py` gives 3.84 to 2.65 (reference 2.51). Recipe guide 6b row 7 now says "8.5 to 5.6 (after round 1: 8.9)" and names the script.
5. **My round-2 summary measured from the end of round 1:** from the old default, spread 8.5 to 5.6, side-joint moss 12.8 % to 7.2 %, tan in big pieces 52.9 % to 25.2 % (from above the reference's 35.6 % to below it), not 8.9 to 5.6, 14.5 to 7.2 and 13.7 to 25.2. The guide's three-column tables were fair; the summary text alone was not.
6. **Colour gain:** about three quarters (78 %: 0.094 of 0.121) is the feature-size cliff; without it the group goes 0.767 to 0.801. The guides said "almost all" and the line above in these notes said "real, not only the cliff measure"; both now say about three quarters.
7. **Wrong note in `integration/takeover/measured_before_clean_up.json`:** it said the harness's own normal gives 0.534; it is the strength-7 normal that does (the harness's gives 0.0). Fixed in that file and in `final_report.json`; the Recipe guide (7.1) and the folder map now name the file.
8. **Old text in new files:** "(the default tile scores 0.70)" in `area/area_2x2/area_measures.json` and `final_report.json` is now 0.822; the score files in `outputs/default_before_look_fixes/` (and the "before" part of `final_report.json`) now name that folder instead of the leftover `outputs/default`.
9. **Lessons guide:** the shadow has 2 flat steps now, not 4; the 768-dot score example and the moss example are labelled as the OLD default; the two slate-grey rules in section 11 are named correctly.
10. **Plain words and length:** "Sobel" is explained where it first appears; the Recipe guide (about 17,000 words, first version about 9,500) has a short reading route at the top. I did not shorten it.
11. **Folder size** is about 454.2 MB against a limit of 460 MB: the margin is only about 6 MB (now stated in the folder map).
12. **Raking-light picture** (`before_after_lit.jpg`): same light, size and window for all three panels, but the reference is lit without a roughness map (the reference set has none) and the tiles with theirs, so their shine is not strictly comparable. Now stated in the Recipe guide and the folder map.

Not checked by the honesty checker or by the corrector: the 4 x 4 area, the 512 and 2508 bakes of the old default, the brick, the control strips, `links_and_order`, the 2 x 2 area re-bake, the half-tile runs themselves, seeds c and d and variations v2, v3, v5 to v8 (re-scored only), the node tree in a fresh Blender, and the lit pictures (not re-rendered).
