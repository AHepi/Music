# Tuning log (integrator)

## Round 2 (after round 1 numbers)
* soot.stack_mult: 0.8 -> 1.4
* soot.roof_mult: 0.8 -> 1.2
* paint.paint_dark: 0.78 -> 0.93
* dirt.film: 0.6 -> 0.5
* dirt.polish_rough: 0.3 -> 0.2
* soot role wall.industrial film_mult 1.4 -> 1.65

## Round 3 (after round 2 numbers)
* soot.stack_mult: 1.4 -> 1.15
* soot.roof_mult: 1.2 -> 1.0
* iron.rust_cover: 0.35 -> 0.5
* groundcracks.crack_contrast: 0.11 -> 0.16
* groundcracks.crack_dots: 3.5 -> 4.5
* groundcracks.near_only: 15.0 -> 20.0
* groundmoss.ribbon_dots: 4.0 -> 6.0
* dirt.polish_lift: 0.05 -> 0.0
* groundcracks.site_bias: (default 0.6) -> 0.9 (ground builder proposal)
* apply.paint.roles: [timber.paint] -> [] (layer off in the street; roles kept under roles_when_tuned)

## Findings from the time run (t1, t2), no setting changed
* Growth alone cost +70 percent of a plate (3.65 s against 2.15 s), where its builder measured +1 to +6 percent. Cause: the second painter round's rubbish has 58,753 separate 3D pieces (the first round's had 6,439) and the plants keep 5 cm clear of every piece (a nearest-point query over all of them). With that clearance switched off the growth costs +0.5 percent (2.18 s), but then 79 percent of the weeds (138 of 174) stand within 5 cm of a litter piece (the line allows 3 percent) and the plant count doubles (235 to 440). Kept ON. The switch is growth.avoid_pieces_of.objects in the set file ([] turns it off).
* The other eleven layers cost, each alone: steps +1, runoff +2, groundcracks +2, dirt +3, groundmoss +3, foot +4, soot +5, wallcracks +5, wallgrowth +6, iron +0 percent. Everything together: +117 percent, with growth 70 of it.

## Round 4 (final settings)
* dirt.film 0.5 -> 0.4 and groundcracks.dull 1.0 -> 0.6: the road lost shine wet (road wet/dry fell 0.15 under base in light E); the small pictures (t3) now give main C wet +0.003, main A wet +0.022, close A wet -0.016, close A heavy 0.000, main E wet -0.118 (was -0.152), main A heavy +0.051.
* growth.cushions_amount 1.0 -> 0.6: 38 percent of the plant dots of the main plate fall inside puddles (both like the low ground beside the gutter and the kit cannot see the water layer's puddles); the flat green moss strings floated on the water, fewer of them look less wrong.
* Round 4 result: crack readability fell (18 good marks of 257 on the main plate, against 37 of 258 at dull 1.0) because a less dull crack has less contrast with the shiny wet setts, so groundcracks.dull went back to 1.0 (kept: dirt.film 0.4, cushions_amount 0.6). Round 5 = the final settings.

## Fix round (after the two checkers; all values are in presets/sooty_1926.json, `old -> new`)
* soot: film_mult 0.60 -> 0.80, washed_share 0.17 -> 0.07, washed_pale 0.8 -> 0.5, edge_sharp 0.85 -> 0.55, grey_pull 0.25 -> 0.10, pale_warm (new) -> 1.0. The film goes up because fewer pale patches means a darker average wall (a first try at 0.72 left the walls at 0.86 of base on the left terrace); the set's soot role values go down to keep trims and the colliery as they were: trims film_mult 1.4 -> 1.2, colliery 1.65 -> 1.25 (a first try that left them at 1.4 and 1.65 made the colliery lighter than the clean brick, 1.33 of base).
* steps: white_cream (new) -> 1.0, white_value (new) -> 0.85.
* dirt: ring_pale (new) -> 0.0 (was 0.45 built in), dip_dark (new) 0.12 (as built in), film_max_share 0.25 -> 0.15.
* groundcracks: open_joint_share 0.14 -> 0.07, open_depth_mm (new) -> 0.8 (was 3 built in), sett_disturb 0.7 -> 0.35. A test of what makes the near road busy (sett_disturb 0, open joints 0, relief 0, water marks 0, film 0) showed the thin pale lines on the setts come from tilted setts and open joints, not from the film or the marks.
* growth: colour_gain 1.0 -> 0.55 (8 times -> 4.4 times), colour_sat (new) -> 0.85, cushions_amount 0.6 -> 0.3, dead_grass_share 0.15 -> 0.08, weed_cover 0.01 -> 0.02, gutter_tuft_share 0.05 -> 0.10 (weeds counted against 18 m of ground; the puddle and litter rules take plants out of the gutter, so the targets go up a little). With the puddle and litter pictures in, a first look with the old counts showed only 22 plant blobs on the main wet plate; the final settings give 42.
* foot: salt_bloom 0.02 -> 0.008. runoff: width_dots 10 -> 14, stain_value 0.9 -> 1.0, iron_rust 0.5 -> 0.9, leak_share 0.15 -> 0.3, source_share 0.8 -> 0.9, pair_share 0.8 -> 1.0. iron: `rust_bright` was tried at 1.0, 1.4, 1.7 and 3.0 on the main plate: no visible change on the lamp posts (the posts are too dark for the dial to matter), so the look does not name it and the lamp-post red stays as it was.
* Two baked pictures stamped into the street and lockout packs: above_water (puddles, margin 3 cm, line 0.5) and litter_dist (picture plus the pieces' centres). A first litter picture without the centres lost 44 percent of the pieces (thin straws narrower than a dot) and left 170 of 236 weeds within 5 cm of a piece's centre; with the centres 0 of 101.
* Time (best of three, 48 samples): street 2.06 -> 1.39 times the earlier layers, lockout 1.75 -> 1.32.
