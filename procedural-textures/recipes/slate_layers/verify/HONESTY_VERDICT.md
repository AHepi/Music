# Honesty Verdict

claims hold: True

## Overall

The main claims hold when I re-run them myself.

- **No fitting.** Nothing in the recipe, the layer files or what they import reads a picture, and there are no per-slate lists and no optimiser.
- **Separate layers.** In a fresh Blender the recipe opens as five layer boxes plus COMBINE. Each layer has its own Seed and Amount. The only wire between layers is DAMAGE.Mask -> MOSS.
- **Independence.** My own bakes reproduce their table for DAMAGE, MOSS and OUTLINE AND SHADOW, even with stricter thresholds.
- **Default tile.** My re-bake is identical dot for dot to the delivered tile.
- **Tiling.** A stricter point-sampled half-tile test shows exact wrapping for one tile and for the 2x2 area.
- **2x2 area.** The quadrants really are new content.
- **Resolution.** 512, 1254 and 2508 dots give the same picture.
- **Reuse.** The brick reuse is honestly described (the layers transfer; the look does not match the brick reference).

The problems are in the reporting:
- the normal-score attribution is reversed in the Recipe guide;
- the ladder claim that the outline layer "is worth the most" is wrong for the colour group;
- the round-14 reasoning conflates the spread between seed sets with a same-seed comparison;
- there are a few overstatements and small gaps (listed under problems).

All my scripts and result JSONs are in proc-work/recipes/slate_layers/verify/. The key numbers are in verifier_measurements.json there. I deleted my large pictures afterwards, so verify/ is 0.3 MB.

## Problems

- NORMAL SCORE ATTRIBUTION REVERSED. Recipe guide section 7.1 says 'normal group 0.671 = the normal made by the harness (strength fitted to 7.37)'. Section 7.2 says rung 3 shows '0.695 instead of the harness's 0.705'. My re-scoring shows the opposite. The strength-7 3x3 Sobel normal (integration/make_normal.py, which replaced outputs/default/normal.png at 02:43:49, five seconds before score_same_kind.json was written) gives overall 0.705 / normal 0.671. The harness's own fitted normal gives overall 0.695 / normal 0.604, with normal_height_agreement 0.0. The note in integration/takeover/measured_before_clean_up.json ('the harness's own normal gives 0.534') has the same error.
- MIXED-METHOD PROGRESS FIGURE. Round 1 (0.615 overall, normal 0.608) was scored with the harness normal. The quoted end point 0.705 uses the strength-7 normal. Like for like, the end point is 0.695, and the normal group did not improve with tuning (0.608 -> 0.604). This affects the Lessons guide ('13 hand rounds ... to reach 0.705') and the recipe guide's round table.
- LADDER CLAIM WRONG FOR THE COLOUR GROUP. The integrator's summary ('Without outline and shadow it drops to 0.567, so the outline layer is worth the most', under 'Ladder (colour group)') and both guides say the drawing layer is worth the most. Their own ladder_table.md shows colour and fade adds +0.158 and moss +0.156 to the colour group, while removing the outline costs 0.134. Outline is the largest only in the height group (0.287). It is not the largest overall either: colour and fade adds 0.168, outline removal costs 0.156. The comparison also mixes 'added to a partial stack' with 'removed from the full stack'.
- ROUND-14 REASONING. The r14d pair (shadow_darkness 0.4, streak_contrast 1.8) won on all three seed sets in same-seed comparisons (+0.095, +0.011, +0.005). The guide dismisses this as 'smaller than what the seed alone moves', but 0.068 is the spread between different seed sets, not the noise of a same-seed difference. The summary's 'a difference under about 0.07 between two single bakes means nothing' drops the guide's qualifier 'with different seeds'. Inconsistency: round 11 adopted moss coverage 0.22 on a single same-seed gain of 0.037 driven by the same colour_scale cliff that round 14 discounts. Keeping the settings is a defensible cost choice (re-baking everything); the stated statistical reason is not.
- 'IDENTICAL' OVERSTATED (declared link). Recipe guide section 5 says damage_avoid 0, 0.8 and 1 'give identical colour pictures'. Their own pictures differ on 0.12-0.14% of dots, by up to 8 steps of 255. The parenthetical '(0.00% of dots differ by more than 10 steps)' is accurate.
- NO SWEEP STRIPS FOR THE LAYOUT LAYER. The brief asks for 2-3 control strips per layer. controls_sweeps/ has colour_and_fade, damage, moss, outline_and_shadow and whole_recipe, but nothing for LAYOUT. The guide's LAYOUT table has no strip column, and this gap is not listed under known gaps.
- DESCRIPTION SIZE UNDERSTATED IN THE SUMMARY AND README. Both say the tile is made 'from a short list of settings (recipe/settings.json, 1.7 KB)' (49 entries). The look actually depends on 176 values: 127 more are layer-file starting values, many also set after looking at the reference, including 27 colour knobs (the brief speaks of a measured palette of up to 12 colours). The Recipe guide does say '176 settings (49 tuned)'. I dumped all 176 into verify/full_effective_description.json: 6.0 KB, 148 numbers, and it still passes description_audit at 8 KB. So this is a wording issue, not fitting.
- HEIGHT IS 70% COLOUR BRIGHTNESS. combine.tone_blend 0.7 makes the height mostly 2.5 x (brightness - 9.5), a formula fitted globally from the reference maps, not the sum of real relief that brief item 7 asks for. The Recipe guide discloses this ('Honest note'), but the integrator's summary quotes 'height 0.654' without mentioning it.
- FOLDER SIZE. The summary says 'now 392 MB'. Excluding both verifier folders, the integrator's content is 404.2 MB in decimal megabytes (385.5 MiB). It is under 400 only in the units du -h prints. With the other verifier's verify_look/ folder (30.5 MB) the folder is now 435 MB.
- HALF-TILE EXPLANATION INCOMPLETE. The guide attributes the raw colour differences (1.8 steps) to Cycles' 4-sample anti-aliasing. With point sampling, height, all masks and piece_id are exact (at most 0.03% of dots differ, at isolated boundary dots). The colour still differs by 1-2 steps on about 57% of dots, which is Blender's default 8-bit dither (dither_intensity 1.0), not the recipe. The conclusion (seamless) stands, and is stronger than they showed.
- RESOLUTION 1254 FILES ARE LINKS. resolution/whole_recipe/at_1254/ holds symbolic links to outputs/default. This is disclosed in CLEAN_UP_AFTER_RESTART.md but not in guide section 7.7. My separate re-bake confirms that two bakes are identical dot for dot, so the claim itself holds.
- MINOR WORDING. (a) settings.json's '49 tuned entries' include recipe.stack_order and recipe.tiles_across, which are not tuned values. (b) The per-layer strips were made at the builders' old starting values, while the tables beside them show tuned defaults (disclosed at the top of section 4). (c) The Recipe guide is about 9,500 words and uses a few terms it never explains (SSIM, Delta E, Lab, Smooth F1, log-normal, 4D, 1 - |2n - 1|). The Lessons guide is plainer.
- FOR CONTEXT (NOT FAULTS): judged by eye, the default reads as the same kind of material, though more regular than the reference (rectangular slates, uniform rows), as the guide says. The colour group is 0.701 against the brief's 0.8 aim; this is reported honestly as not reached.

## what_i_ran

[
 "Read the brief, the procedural notes (skimmed), recipe/slate_recipe.py, every file in layers/, lib/recipe_tools.py and lib/contrib/builder.py imports, the brick reuse recipe, the tuning-round files, the independence and half-tile scripts, and both 05 guides, README and final_report.json.",
 "grep across the recipe, the layers and lib imports for images.load, imread, PIL, Image.open, .png, np.load, numpy, base64, ImageTexture, OpenImageIO, optimi/minimi/scipy/itertools.product: no picture reading and no optimiser (tune_real.py and measure_sets.py are hand-run variant bakes). The tuning rounds hold 1-4 named variants each.",
 "python3 -I lib/description_audit.py recipe/settings.json --limit-kilobytes 8: 1704 bytes, 45 numbers, no problems. I also dumped all 176 effective controls to verify/full_effective_description.json and audited them: 6019 bytes, 148 numbers, 27 colours, no problems.",
 "verify/scripts/list_node_tree.py in a fresh Blender: SLATE contains LAYOUT (307 nodes, seed 1), COLOUR AND FADE (419, seed 11), MOSS (419, seed 31), DAMAGE (439, seed 21), OUTLINE AND SHADOW (216, seed 41) and COMBINE (19). Each layer has its own Seed and Amount; the only cross-layer wire is DAMAGE.Mask -> MOSS 'Damage Mask'; there are no image nodes. Output in verify/node_tree_listing.json.",
 "Own independence bakes at 448 dots (verify/scripts/bake_variants.py with lib harness building blocks, -t 2) and analyse_independence.py with strict 1-step thresholds. damage Amount 0 / Seed+1, moss Amount 0 / Seed+1, outline Amount 0 / Seed+1: 0 dots of colour changed outside the layer's region; height and roughness at most 1 dot by 1/65535 (float rounding). Other masks and piece_id are unchanged, except the moss mask inside damage (0.88% and 1.54%, theirs 0.92% and 1.57%). colour_and_fade Seed+1 leaves every other mask unchanged. layout Seed+1 changes everything, matching their row.",
 "Re-baked the default tile at 1254 dots with lib/bake_harness.py into verify/default_rebake: colour, height, roughness and metallic are identical to outputs/default dot for dot. lib/texture_compare.py scores it 0.705 overall (colour 0.701, height 0.654, normal 0.671) with the strength-7 normal, and 0.695 (normal 0.604) with the harness's own normal.",
 "Point-sampled half-tile test (1 sample, 0.01 filter) at 512 dots, tiles_across 1, and at 768 dots, tiles_across 2: height, all four masks and piece_id are exact except 0.03% of dots or fewer; colour differs by 1-2 steps on about 57% of dots, which is Blender's default dither (checked: dither_intensity 1.0); 7-dot control differs by 23-68 steps on average.",
 "2x2 area: compared the four quadrants of their area_colour.png and of my own 768-dot tiles_across 2 bake. Quadrants differ about as much as tiles with all-new seeds (correlation 0.26-0.45 against 0.32 for new seeds; 13-17% nearly-equal dots, 2-4% identical). Re-scored the quadrants' colour group: 0.701 / 0.751 / 0.705 / 0.752, matching theirs.",
 "Resolution: shrank their 2508 and 1254 bakes and compared with 1254 and 512. Colour mean difference 0.8-1.4 of 255, height 1.1-2.4, against 20 for a new-seed tile. Their claim holds.",
 "Reuse: read reuse/brick_layers_recipe.py (imports the unchanged layer files; BRICK_SETTINGS has 53 entries; the brick layout has 38 nodes plus 2 input/output boxes). Looked at reuse_sheet.png and brick_settings_round_2.jpg. Checked that b1 and b2 really differ (22% of dots), even though their scores are identical.",
 "Recomputed the declared-link colour differences between damage_avoid 0, 0.8 and 1 from their pictures; read the ladder, round-14, seed-spread and round-11 JSONs; regenerated controls.md with a copy of make_controls_table.py in verify/controls_check: identical to recipe/controls.md (176 rows).",
 "Checked that every file path cited in the guides and README exists (only glob patterns did not match); measured folder sizes excluding the two verifier folders; looked by eye at the default next to the reference, the debug overview, the variations sheet and the reuse sheets."
]
