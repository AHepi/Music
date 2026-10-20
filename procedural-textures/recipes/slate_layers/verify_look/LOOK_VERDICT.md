# Look Verdict

claims hold: True

## Overall

VERDICT: Mostly yes. The default tile reads as the same kind of material as the reference. It has 8 rows of about 6 blue-grey slates, black joints and a dark band under each row, olive moss hanging from the top edges, tan chips on the lower edges, and directional painted streaks rather than camouflage blobs. The overall colour matches closely: mean Lab is 25.1/-1.8/-1.0 against the reference's 25.2/-1.6/-1.0, and moss and chip hues are within 1 unit. Per-slate tone variety is fine (slate-to-slate lightness spread 3.6 against 2.5 in the reference). An art director would still see a different hand right away.

(a) The paint is narrow flame or icicle tongues with soft, wavy, rippled edges, like a liquify filter. The reference uses broad, crisp, flat dry-brush bands.
(b) There is too much moss, and it sits as flat khaki stains with rows of sharp teeth hanging from the top edge.
(c) The chips gather into big tan L-shapes at the lower corners instead of a broken pale rim along the lower edge.
(d) The slates have near-square corners and ruler-straight rows.

Under a raking light the relief looks like rippled plastic or wood planks. The streak outlines dominate, and the lower-edge rims, chips and moss carry too little relief.

The 8 variations mostly read as sensible variants of one roof. v1, v3, v7 and v8 are good. v2 ('more moss') is hard to tell from the default, because the default is already mossy. v4 just reads as a lighter tile. v5 loses the hand-painted look. v6 ('dark and wet') is the one that reads as noise: near-black stain patches merge with the black joints and look burnt or camouflaged.

The 2x2 and 4x4 areas have no visible seams or repeats. I looked at the base-tile lines at full size. Correlation at a shift of one base tile (0.44 / 0.29) equals the background level at other shifts (0.45 / 0.12), and the 4x4 tile cells have mean brightness 55.6 to 59.7.

The debug views make sense on their own. The layout bundle is clean, and the colour-and-fade layer alone reads as a believable painted slate roof. The damage view clearly shows the corner bias, and the outline view shows the stepped shadow tiers.

I tested settings-only fixes for the top problems on colour-only test tiles at 900 dots, in verify_look/tests/. The combined set (t4_all) moves every measured statistic towards the reference:

| measure | default | combined fixes | reference |
|---|---|---|---|
| median colour gradient (fine busy texture) | 10.0 | 7.1 | 5.5 |
| side-to-side over up-down gradient energy (vertical stripiness) | 1.18 | 0.98 | 0.83 |
| olive share | 10.7% | 6.0% | 6.4% |
| tan share | 2.1% | 0.8% | 1.0% |

The comparison is in verify_look/ref_default_suggested.jpg: reference, then default, then combined fixes.

Not tested: the relief changes (tone_blend, sink_depth, lip_height, moss raise) need a height and normal rebake. A wider moss palette is also untested; rim_lightening 0.9 alone did not raise the moss's inner tone spread, which stayed at 4.3 against 6.0 in the reference.

The critic files are in proc-work/recipes/slate_layers/verify_look/. They take 5.8 MB after converting to JPEG. The slate_layers folder was 389 MB before that conversion, close to the 400 MB limit, so delete verify_look/ when done. I edited none of the builders' files.

## Problems

- 1 (most noticeable, everywhere at full size, worse at 2508 dots) PAINT HANDLING. Inside every slate the paint is narrow pointed flame or icicle tongues whose edges have a fine horizontal wavy ripple, which looks liquified. The reference has broad, flat, crisp-edged vertical bands. See verify_look/edge_zoom3x.jpg and flat_outliers.jpg, and resolution/whole_recipe/same_crop_at_three_sizes.png at 2508. Measured at 900 dots: median colour gradient 10.0 against 5.5 in the reference; side-to-side over up-down gradient energy 1.18 against 0.83 (too stripy). Suggested change: colour_and_fade.streak_width 0.014->0.03, mottle_tallness 1.1->2.2, edge_ragged 0.0035->0.0015, grain_amount 0.05->0.02, streak_contrast 1.4->1.2. Tested (tests/t1_paint): median gradient 10.0->7.5, the ripple mostly gone, bands broader and flatter.
- 2 MOSS. There is too much of it, it is too flat, and it ends in rows of icicle teeth. Olive covers 10.8% of the default tile against 6.6% in the reference (same measuring rule). The largest moss clump is 16,056 dots against 7,012. Lightness variation inside the moss is 4.3 against 6.4, so it reads as a khaki stain, not mottled moss. A row of sharp teeth hangs from the upper edge of many slates; examples are default tile row 3 (x 680-1000, y 380-560) and row 5 on the right. Suggested change: moss.coverage 0.22->0.15, fringe_amount 0.3->0.08, drip_stretch 1.8->1.4, cluster_size 0.06->0.04, tone_patch_size 0.02->0.008, edge_raggedness 0.7->1.0, lichen_amount 0.15->0.05. Tested (tests/t2_moss): olive 10.7%->5.9%, teeth gone, clumps break into flecks. Still needed: a wider moss palette (tone_1 darker, about #23241c; tone_5 lighter, about #63614a). Untested; rim_lightening 0.9 did not raise the spread.
- 3 CHIPS AND DAMAGE. They gather into big solid tan or white L-shaped flakes that hug a lower corner and run up the side joint, repeated on many slates. Examples: default tile x 830-1000, y 90-250 (verify_look/crack_and_corner.jpg, right), the top-row corners, and the debug damage mask. The reference instead has a broken pale-grey rim and small flecks along the whole lower edge. Tan share is 2.1% against 1.0%. Suggested change: damage.corner_gain 1->0.3, chip_frequency 110->160, chip_clustering 1->0.5, outline_and_shadow.lip_brightness 0.12->0.3; also side_share 0.12->0.05 (untested). Tested (tests/t3_edges): tan 2.1%->0.9%, corner L-shapes gone, the pale lip along the lower edge now visible as in the reference.
- 4 SLATE SHAPE. Corners are near-square and rows are ruler-straight; the reference has clearly rounded lower corners and more uneven lower edges. Measured: the top of the row band wanders with a spread of 4.4 dots against 5.7, and the row band is solid black over 95% of its length against 85%. Visible in verify_look/height_ref_def_rough.jpg (left is the reference) and side_colour.jpg. Suggested change: layout.corner_bottom_factor 1.5->2.5 (or corner_radius 0.0064->0.009), ragged_bottom 0.0055->0.008 (both tested inside t3/t4, which look better), bottom_tilt 0.02->0.035 (untested).
- 5 RELIEF UNDER A RAKING LIGHT (verify_look/lit_side_full.jpg and lit_side_zoom.jpg: reference left, default right; Cycles, sun 20 degrees above the surface, colour + normal + roughness). The default relief reads as rippled plastic or wood-plank grain from the paint-streak outlines; the lower-edge rims and chips catch little light, and moss is not visibly raised. Normal map: 99th-percentile tilt 99 against 113; average up-down slope 11.1 against 13.4 (weak horizontal edges) while side-to-side slope is 16.3 against 15.6 (too many vertical streak edges). The top-to-bottom ramp of each slate is fine (0.26 of the height range, same as the reference). Suggested change: combine.tone_blend 0.7->0.45, outline_and_shadow.lip_height 0.04->0.1, damage.sink_depth 1->1.6, moss.raise 1->2.5. Untested; needs a height and normal rebake. Fixing problem 1 also cleans the relief, because the height follows the paint.
- 6 SHADOW UNDER EACH ROW. It is drawn as black drippy teeth plus 4 visible stepped grey tiers (debug_views/sheet_outline_and_shadow.png mask; the top of every slate in edge_zoom3x.jpg). The reference has a clean dark band. Suggested change: outline_and_shadow.black_drips 0.005->0, shadow_drip 0.5->0.2 (both tested in t3, cleaner), shadow_tiers 4->2 (untested).
- 7 PALE FLAT OUTLIER SLATES. Some slates are lighter than any slate in the reference (mean lightness 38-39 against a reference maximum of 34.6) and almost streak-free, so they pop out. Examples: default tile top-left slate (x 0-160, y 0-65), 2x2 area x 1859-1994, y 1186-1322, and seed_spread seeds_c row 5. When the single tile is repeated they become the main repeat landmark (verify_look/default_tiled_3x3.jpg: the pale slate in row 5 on the left repeats every tile). Suggested change: colour_and_fade.outlier_size 1.2->0.8 or outlier_share 0.15->0.08. Untested.
- 8 LONE CRACK. One crack in the default tile is drawn as a pale wire with a dark outline running across a slate (row 7, x 430-560, y 1040-1090; verify_look/crack_and_corner.jpg, left). It reads as a hair on the picture; the reference has no such marks. Suggested change: damage.crack_amount 0.02->0 for the default (keep cracks for v3_heavily_damaged), or draw cracks in the dark hole colour.
- 9 LICHEN DISCS. Small perfectly round tan dots are sprinkled over the slates (2x2 area centre crop, verify_look/area2_centre.jpg) and read as polka dots. Suggested change: moss.lichen_amount 0.15->0.05 (tested inside t2 and t4; less distracting).
- 10 VARIATIONS. v6_dark_and_wet: near-black stain patches as dark as the joints wipe out the slate outlines and read as burnt or camouflage (contact sheet, bottom row, second tile; verify_look/default_v4_v6.jpg, right). Suggested change: colour_and_fade.stain_amount 0.9->0.5, stain_cover 0.5->0.3, tone_centre 2.3->2.8. v5_fresh_and_clean: flat vector fills lose the hand-painted character; keep fade_amount about 0.5 and streak_contrast about 0.8. v4_faded_sun_bleached: reads only as a lighter tile; the bleached areas are not legible as areas; try bleach patch_size 0.35 with a stronger bleach_amount. v2_more_moss: hard to tell from v1 because the default is already moss-heavy; it becomes distinct once the default moss is reduced (problem 2). v1, v3, v7 and v8 are good. All v-suggestions are untested.
- 11 (minor) The moss mask cuts clumps off with straight vertical edges at the side joints, so some slates carry a rectangular block of moss edge to edge (debug_views/sheet_moss.png, row 4). The 'moss colour everywhere' debug view shows a marbled swirl rather than moss texture. joint_preference and drip rules could feather the clump edges near joints instead. Untested.
- 12 (not a problem, checked) The 2x2 and 4x4 areas show no seams or repeats. I looked at 1:1 crops on the base-tile lines (verify_look/area2_centre.jpg, area2_hline_left.jpg, area2_vline_top.jpg). Correlation at one base-tile shift (0.44 / 0.29) equals the background level at other shifts. The 4x4 tile-cell means are 55.6-59.7: the top-left cell is slightly darker, which is not visible.

## what_i_ran

[
 "Read the brief (look target section), the folder map README, settings.json and the controls table (recipe/controls.md)",
 "Side-by-side and 1:1 / 3x crops of reference/slate/colour.png and normal.png against outputs/default (verify_look/side_colour.jpg, side_normal.jpg, crop_colour_mid.jpg, edge_zoom3x.jpg, crack_and_corner.jpg)",
 "Looked at every debug sheet (overview_masks_and_colours, bundle_sheet, sheet_colour_and_fade/damage/moss/outline_and_shadow), the variations contact sheet and seed_spread, area_2x2 and area_4x4 overviews plus 1:1 crops on the base-tile lines, the whole_recipe sweep strips and the resolution crop",
 "Measurements with numpy/OpenCV: olive and tan shares and colours, moss clump sizes and inner spread, gradient statistics and stripe direction, shifted correlations, per-slate tone spread and flattest slates, straightness of the row joints, normal-map tilt percentiles, top-to-bottom height ramp, 4x4 tile-cell means and correlation at one base-tile shift",
 "Lit check: wrote verify_look/lit_preview.py (Cycles CPU, -t 2, 24 samples, orthographic camera, sun 20 degrees above the surface from the upper left); rendered the reference (colour + normal, roughness 0.8) and the default (colour + normal + roughness) at full tile and at a 0.4-tile zoom (verify_look/lit_side_full.jpg, lit_side_zoom.jpg)",
 "Test tiles: colour-only bakes at 900 dots with the existing damage_work/window_render.py (it uses lib/bake_harness.py), output only into verify_look/tests: t0 default, t1 paint fixes, t2 moss fixes, t3 edge/chip/shadow fixes, t4 all combined; measured them against the reference scaled to 900 dots (verify_look/tests_crops2x.jpg, tests_full.jpg, ref_default_suggested.jpg)",
 "Tiled the default 3x3 to look for repeat landmarks (verify_look/default_tiled_3x3.jpg)",
 "Converted my pictures to JPEG to keep the folder under the size limit (verify_look is 5.8 MB; slate_layers was 389 MB before the conversion); edited none of the builders' files"
]
