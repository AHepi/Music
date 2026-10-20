# Honesty check of the look-fix work (tuner rounds 1 and 2, and the re-baker) - 20 October

What this file is (plain words): the honesty checker's notes on whether what the slate tuner and the re-baker report is true and fairly shown.
I did not edit any of their files. Everything I made is in this folder (`verify/after_look_fixes/`): scripts, small result files and notes.
The big pictures I baked were deleted afterwards to save disk (numbers and logs are kept); running the scripts bakes them again.

## Verdict

Claims hold: YES. Every number I re-measured reproduced, and the default tile re-bakes identically. I found no wrong claim in substance.
I found eleven small wording or labelling faults (listed below), none of which changes a conclusion.

## What I ran, and what came out

1. **Re-score of `outputs/default`** with `lib/texture_compare.py`: overall 0.778, colour 0.822, height 0.735, normal 0.616, tiling 1.0, and every one of the 14 single measures equals
   `outputs/default/score_same_kind.json` (`rescore_default_stored.json`). The dot-for-dot score (`lib/pixel_compare.py`) also equals the stored file exactly (`rescore_pixel_default.json`).
   The old default re-scores 0.705 / 0.701 / 0.654 / 0.671, as written. These numbers are the same in final_report.json, the 05 Recipe guide (7.1, 7.2, 6b), the 05 Lessons guide, the ladder table,
   the notes and the tuner's and re-baker's reports.
   Both normal-map methods (`rescore_before_both_normals.json`, `rescore_now_both_normals.json`): strength-7 normal: overall 0.705 -> 0.778, normal group 0.671 -> 0.616;
   harness-style normal: overall 0.695 -> 0.789, normal group 0.604 -> 0.690.
2. **One re-bake of the default at 1254 dots** from `recipe/settings.json` (my own Blender run, `-t 2`, `--normal-reference slate`, log in `default_rebake/log.txt`):
   colour, height (16 bit), roughness, metallic and the harness normal are IDENTICAL to `outputs/default`, dot for dot (0 dots differ, largest difference 0; `rebake_vs_delivered_result.txt`).
   No dither difference at all. The strength-7 `normal.png` made from my re-baked height by `integration/make_normal.py` is also identical. I stopped the run by its PID after the harness normal was written, so
   `normal_bumpnode.png` was not re-baked and not checked.
3. **Before and after pictures** (`look_fixes/before_after_colour.jpg`, `before_after_zoom.jpg`): I rebuilt them from `reference/slate`, `outputs/default_before_look_fixes` and `outputs/default` and compared with the stored JPEGs.
   Each panel is closest to its own source (difference about 2.5, which is JPEG noise; to the wrong source 14 to 22). Same default seeds, same 900-dot size, same 0.4-tile window. The raking-light picture uses the same
   light, size and window for all three (`lit_jobs_round2.json`); one asymmetry: the reference has no roughness map, so it is lit without one while ours use theirs. By eye the pictures show what the guide says (rounder lower corners, softer moss, and the facets, e.g. the dark triangles).
4. **`description_audit.py recipe/settings.json --limit-kilobytes 8`**: passes (2464 bytes, 67 numbers, no problems). All 182 effective values of the controls table (`full_effective_description_182.json`) are 5972 bytes, 154 numbers, and also pass at 8 KB,
   so the README's "about 6 KB" is true (the guide says that was "not repeated for the 182"; I did). Every setting value in the guide tables (sections 4.1 to 4.6 and 6b) matches `recipe/settings.json` / `controls.md`;
   all 73 entries of settings.json equal the "default" column of controls.md; the tuner's round-2 list matches settings.json (0 mismatches, every changed entry is listed); 73 entries, 49 before, 46 differ.
5. **Layer-file changes**: only `moss.py` and `outline_and_shadow.py` differ from the copies in `look_fixes/round2/layer_files_before_round2/` (diff read; six new controls, all written so that the starting value gives the old picture). The other layer files are older than the old default's bake.
   All six are in `integration/CHANGES_TO_LAYER_FILES.md` (rows 3 to 6). I re-ran two tests myself:
   * the six new controls at their starting values change nothing: same settings (end of round 1) baked at 320 dots with the old and with the new layer files: colour, height, roughness identical, 0 dots differ (`old_files_test/result.txt`);
   * independence of MOSS and OUTLINE AND SHADOW (Amount 0 and Seed + 1, tuner's scripts, 320 dots, new default settings): every "outside own region" number is 0.0 and no other layer's mask changed (`independence_320/independence_two_layers_table.md`).
   The tuner's 384-dot table, the re-baker's 512-dot table and my 320-dot table agree.
6. **HONESTY_VERDICT.md problems**: the normal-score attribution, the mixed-method progress figure, the ladder claim, the round-14 reasoning, "identical", the missing layout strips, the description size, the 70 % paint height, the folder-size units,
   the half-tile explanation, the resolution links and the minor wording items are all corrected in the guides (and marked "corrected"). Exceptions are in problem 6 below.
7. **Re-scores**: all eight variation pictures re-score as written (v1 0.811, v2 0.700, v3 0.761, v4 0.694, v5 0.534, v6 0.693, v7 0.591, v8 0.732; `rescore_variations.txt`). I also re-baked v4 (new settings) from `variations.json`: identical to the stored picture, 0.694.
   Seed spread: I re-baked seeds_b from its recorded seeds: 0.824, feature size 0.94, as written; its small picture matches the stored JPEG. Seeds c and d, and the 2 x 2 area, I did not re-bake. The four 2 x 2 quarters re-score 0.831 / 0.795 / 0.804 / 0.805 as written,
   and the quarter really is not the default tile (mean difference 14.8 per channel, 18.0 by the largest channel, as the guide says). My own seam check of the area gives 0.81 / 0.51 against the written 0.80 / 0.51. Ladder: all four rungs I could re-score reproduce (rung 0 to 2 and "without outline"; rung 3 is the default).
   The mean and spread of the seed sets (0.810, 0.032) are right.
8. **Links and pictures**: every file, folder and picture named in the two 05 guides and the folder map exists (128 + 16 + 62 names found directly, the rest found by their file name; `link_check_result.json`); the only unmatched items are shorthand (`.json`, `_analysis.py`, `seeds_b/c/d_colour_small.jpg`).
9. **Tuner's measuring numbers**: `look_fixes/measure_look.py` and the copy of the look checker's script (`round2/independent_measures.py`) give the "before" and "now" columns exactly (rerun_*.json); the "after round 1" column equals the look checker's own round-1 file.
   "2 of 59 slates more than 12 grey levels off the middle (reference 3 of 45, before 11)" reproduces; at 8 levels it is 9 of 59 (reference 8 of 45, before 23).

## Problems (all small)

1. `05 Recipe ... how it is made.md` section 7.5: "Nothing got worse" is not quite true. Against `half_tile_table_before_look_fixes.md` the outline-and-shadow mask got slightly worse for one tile (raw 1.54 -> 1.62, blurred 0.37 -> 0.41) and the 2 x 2 area
   (raw 2.99 -> 3.05, blurred 0.68 -> 0.74), and the 2 x 2 damage mask (0.673 -> 0.688 blurred). Should say: "nearly everything got smaller; the outline and damage masks moved up slightly (still tiny)".
2. Same paragraph: "The blurred differences are 18 to 95 times smaller than the controls": over the 16 rows it is 18 to 143 times (the piece-number rows are 143 and 132). Say "18 to 143".
3. Normal group "fell (0.671 to 0.616)" (Recipe 7.1, known gaps, summaries): true for the strength-7 normal, but with the harness-style normal the group ROSE (0.604 -> 0.690). The guide gives both overall numbers but not both normal-group numbers.
   It should say the normal group moves by 0.07 either way depending on the normal-map method, so it is a weak signal, not a loss.
4. Recipe 6b table row 7: "Spread of the slates' mean grey 8.9 to 5.6 (reference 5.5) by the tuner's rule". 8.9 is the value after round 1; the old default's value is 8.48 (and the 5.57 / 5.51 numbers come from the copy of the checker's script,
   not from the tuner's `measure_look.py`, whose own spread is 3.84 -> 2.65 against 2.51). Should say "8.5 to 5.6 (after round 1: 8.9)" and name the right script.
5. Recipe 7.1 / known gaps / Lessons: "almost all" of the colour gain is the feature-size measure. By the tool's weights it is about 78 % (0.094 of 0.121; without it 0.767 -> 0.801). The tuner's notes say the opposite ("the colour gain is real, not only the cliff measure").
   Both are true as numbers; the guides should say "about three quarters" and the tuner's note should not say "real, not only".
6. `look_fixes/rebake_result.json` says the reversed normal-score note in `integration/takeover/measured_before_clean_up.json` was "mentioned in the guide". Neither guide, nor the folder map, nor final_report.json names that file.
   The file still says "the harness's own normal gives 0.534" (wrong). Add one line to the guide, or fix the file.
7. `area/area_2x2/area_measures.json` (new file) and the "area 2 x 2 now" part of final_report.json still carry the old key text "(the default tile scores 0.70)"; the default now scores 0.822. The old score files in `outputs/default_before_look_fixes/` also say candidate "outputs/default" (path written when scored, now moved).
8. `05 Lessons ...` section 6 says the shadow is "4 flat steps"; the default is now 2 (`shadow_tiers` 2). Section 7 still quotes old-default numbers without saying so ("0.632 at 768, 0.701 at 1254"; the moss "15 % olive-or-tan dots ... `moss.coverage` 0.18" bullet). Recipe 4 (line 171) has the same 0.632 / 0.701 but is labelled old.
9. The tuner's round-2 summary and notes lead with changes measured from the end of round 1 (spread 8.9 -> 5.6, side-joint moss 14.5 -> 7.2, tan in big pieces 13.7 -> 25.2). The guide tables show before / after round 1 / now, which is fair; the tuner's own summary text alone is less so
   (for instance, tan in big pieces went from 52.9 % at the start to 25.2 % now, i.e. from above the reference to below it).
10. Folder size: 454.0 MB decimal is right for the folder as the re-baker left it (453.98 MB when I measured, before my own files). The limit is 460, so the margin is only about 6 MB. My own files are about 0.36 MB now.
11. Plain-words rule: "Sobel" (README, recipe section 1) is used without a one-line explanation, and the Recipe guide is about 17,000 words (the first version was 9,500).

## What I did NOT check

The 4 x 4 area, the resolution bakes at 512 and 2508 (I only checked that the old folder is the old default and the links point at it), the brick reuse, the control strips, `links_and_order`, the 2 x 2 area re-bake, the half-tile test (8 runs), the independence of layers that did not change,
the node tree in a fresh Blender (I only summed `node_counts_after_look_fixes.json`: 1872 nodes, 1504 Math = 80 %), the number of Blender launches the helpers say they made, the tuning test bakes (17 variation candidates, round-2 test tiles), the lit renders (I did not re-render them),
v2/v3/v5/v6/v7/v8 and seeds c/d re-bakes (I re-scored the stored variation pictures but could re-bake only v4 and seeds_b), and whether the look checker's second look is itself right. I looked at the colour before/after picture, the raking-light picture and the variations contact sheet by eye only.

## Files in this folder

`rescore_pictures.py`, `rescore_colour_only.py`, `compare_rebake.py`, `check_links.py`: my scripts. `rescore_*.json|txt|jsonl`, `rerun_*.json`, `rebake_vs_delivered_result.txt`, `link_check_result.json`, `controls_parsed.json`, `full_effective_description_182.json`: results.
`default_rebake/log.txt`, `variant_rebakes/` (views and log), `independence_320/` (table, json, log), `old_files_test/` (copy of the old layer files, notes and result).
