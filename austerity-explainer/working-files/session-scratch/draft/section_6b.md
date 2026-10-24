## 6b. Round 15 - the look checker's fixes (20 October)

**What happened.** After this guide was first written, a "look checker" (a helper who only looks: it put the default tile next to the reference, at
full size and under a low light, and measured it with small scripts) listed eleven things that looked wrong (`verify_look/LOOK_VERDICT.md`). A "tuner"
fixed them in two rounds of hand-tuning (the notes are `look_fixes/notes - look fixes round 15.md`; `look_fixes/round_1_tuner_result.json` and
`round_2_tuner_result.json` list every setting changed, with its old value, its new value and why). The look checker looked again after each round
(`verify_look_after_fixes/round_1/` and `round_2/critic_result.json`). Last, I (the "re-baker") made again everything in this folder that depends on the
default settings (ladder, variations, seed spread, the 2 x 2 area, the tests, the debug views) and brought the guides up to date. The rules did not
change: hand-tuning only (look, change one thing, look again), the reference only as a guide, nothing traced and no optimiser.

Three words used below. **Relief** = the bumps of the surface (the height map and the normal map made from it). **Raking light** = a low sun,
20 degrees above the surface, which makes bumps show (the look checker's lit pictures). **Facet** = a flat patch of paint with straight edges.

### What each fix does, in plain words

| # | the fault the look checker found | what was changed (old to new) | how it came out (the look checker's second look) |
|---|---|---|---|
| 1 | The paint looked "liquified": narrow pointed flame tongues with a fine wavy ripple along their edges | broader paint bands (`colour_and_fade.streak_width` 0.014 to 0.03); less ripple (`edge_ragged` 0.0035 to 0.0015); the fine grain kept (`grain_amount` 0.05 to 0.04; round 1 had lowered it to 0.02 and the fine grain vanished, round 2 put it back); gentler contrast (`streak_contrast` 1.4 to 1.3); patches a little taller (`mottle_tallness` 1.1 to 1.5); a little more fade (`fade_amount` 0.85 to 0.9) | **better.** Ripple gone, broad flat crisp-edged bands, grain back. Not fixed: the tongues are still pointed and the paint is still more "upright-stripy" than the reference; and the broader bands brought a NEW fault (see "what is still wrong") |
| 2 | Moss: too much, a flat khaki stain, with a row of teeth hanging from the upper edge | `moss.fringe_amount` 0.3 to 0.08 (no teeth); softer, broader clumps (`cluster_size` 0.06 to 0.055, `edge_raggedness` 0.7 to 0.6); moss gathers in fewer areas (`patchiness` 0.75 to 0.9); a wider olive palette (`tone_1` darker, `tone_5` lighter, `tone_centre` 0.7 to 0.55); less light rim (`rim_lightening` 0.5 to 0.2); `coverage` 0.22 to 0.30 (round 1 had lowered it to 0.17; round 2 raised it again because the moss became see-through, so more of it is needed to read as moss); NEW controls `rim_opacity` 0.5, `core_opacity` 1.0 and `fleck_amount` 0.5 (see below) | **better.** The moss is now a soft see-through olive wash that lets the slate streaks show, hanging from the upper edges. Share of slate dots that are moss 13.6 % to 6.5 % (reference 9.0 %). A little too pale and thin |
| 3 | Big solid tan L-shaped chips at the lower corners | `damage.corner_gain` 1 to 0.3; chunkier, less clustered chips (`chip_frequency` 110 to 115, `chip_clustering` 1.0 to 0.55, `chip_breakup` 1.1 to 0.8, `chip_depth` 0.02 to 0.024, `chip_amount` 0.65 to 0.68); a paler lower lip (`outline_and_shadow.lip_brightness` 0.12 to 0.3) | **fixed.** Along most slates the chips are still a thin ragged fringe, not chunky cream flakes |
| 4 | Slate shape: square corners, ruler-straight rows | `layout.corner_bottom_factor` 1.5 to 3.0 (rounder lower corners), `ragged_bottom` 0.0055 to 0.01, `bottom_tilt` 0.02 to 0.08 | **better.** Corner rise 6.8 to 14.8 dots (reference 17.7); rows still straighter than the reference |
| 5 | Relief under a raking light looked like rippled plastic; rims, chips and moss carried little relief | `outline_and_shadow.lip_height` 0.04 to 0.1, `damage.sink_depth` 1 to 1.6, `moss.raise` 1 to 2.5; NEW controls `joint_texture` 0.35 and `joint_texture_size` 150 (a faint mottling of the black joints, see below) | **better, not fixed.** The plank-like ripple is gone, lower lips catch light, moss stands up a little. The relief is still weaker than the reference (mean tilt 20.2 against 23.7) and looks like thin scratch lines, not chunky pitted chips |
| 6 | The shadow under each row: black drips and four grey steps | `outline_and_shadow.black_drips` 0.005 to 0, `shadow_drip` 0.5 to 0.2, `shadow_tiers` 4 to 2 | **fixed.** A clean dark band with one soft step |
| 7 | Pale flat outlier slates | `colour_and_fade.outlier_size` 1.2 to 0.7, `outlier_share` 0.15 to 0.08, `tone_spread` 1.0 to 0.45, more teal and warm slates (`tint_amount` 0.7 to 0.9, `patch_tint` 0.4 to 0.55) | **better.** Spread of the slates' mean grey 8.9 to 5.6 (reference 5.5) by the tuner's rule; the look checker's own rule says 9.2 to 6.9 (reference 5.1), so a few grey-brown flat slates are still visible |
| 8 | One lone crack across a slate | `damage.crack_amount` 0.02 to 0 | **fixed** (a short pale hairline remains in one place) |
| 9 | Lichen discs like polka dots | `moss.lichen_amount` 0.15 to 0.07 | **fixed** (24 round dots against 28 in the reference) |
| 10 | Variations: v6 burnt patches, v5 flat, v4 only lighter, v2 like v1 | not part of the tuner's work; done in this re-bake (section 7.3) | see 7.3 |
| 11 | Moss cut off in a straight line at the side joints | NEW control `moss.side_clearance` 0.012 | **fixed.** Moss within 14 dots of a side joint 12.8 % to 7.2 % (reference 6.5 %) |

The same-kind colour group of the default tile went from 0.701 to 0.822 (section 7.1). **Be careful with that gain**: most of it comes from the
"feature size" measure, which is a cliff (the Lessons guide, section 7). Without that measure the colour group by the tool's own weights went from 0.767
to 0.801. What the eye sees is in the pictures below, and the look checker's verdict is "nearly the same hand" (not yet the same hand).

### The only code that changed: six new controls in two layer files

Only where no setting could do the job. Every new control starts at the value that gives exactly the old picture. Both files are listed in
`integration/CHANGES_TO_LAYER_FILES.md` (rows 3 to 6); the old files are in `look_fixes/round2/layer_files_before_round2/`.

| layer file | new control | in plain words |
|---|---|---|
| `layers/moss.py` | `rim_opacity`, `core_opacity` (both 1 = solid) | how see-through the moss paint is at the rim of a clump and deep inside it; lower = the slate paint and its streaks show through (only the colour mask is see-through; moss height and roughness are unchanged). The default tile uses 0.5 and 1.0 |
| `layers/moss.py` | `side_clearance` (0 = off) | moss growth fades out over this distance (tile units) before a side joint, so a clump no longer stops in a straight cut. The default tile uses 0.012 (15 dots) |
| `layers/moss.py` | `fleck_amount` (1 = as before) | scales the small light and dark flecks inside the moss. The default tile uses 0.5 |
| `layers/outline_and_shadow.py` | `joint_texture` (0 = flat black as before), `joint_texture_size` (600) | a faint, fine mottling of the black joints. The reference joints are faintly mottled (brightness spread 2.8) and ours were flat (0.5), so the relief, which follows the colour, was flat there too. The default tile uses 0.35 at size 150; 0.5 at 600 looked like grit at full size and was rejected |

Checks the tuner ran: with the controls at their starting values the picture is bit for bit the old one (384 dots: colour, height, roughness differ by 0);
and the independence test was run again for both layers (section 7.4, and again at 512 dots by me).

### Before and after, measured

Finished 1254-dot tiles. The first table is the tuner's own measuring script (`look_fixes/measure_look.py`, colour measures made after shrinking
to 900 dots, relief from the strength-7 normal); the second is a copy of the look checker's measuring script. "Before" = the old default
(`outputs/default_before_look_fixes`), "after round 1" = the tile at the end of the tuner's first round, "now" = `outputs/default`.

| measure (tuner's script) | before | after round 1 | now | reference |
|---|---|---|---|---|
| median colour gradient (how sharp the edges are; a 900-dot artefact) | 9.44 | 7.54 | 7.54 | 5.55 |
| side-to-side over up-down gradient energy (above 1 = upright stripes) | 1.15 | 0.98 | 0.98 | 0.83 |
| olive (moss) share by a colour rule (under-counts see-through moss) | 10.4 % | 5.7 % | 4.0 % | 6.4 % |
| tan (chip) share | 1.91 % | 0.88 % | 1.19 % | 1.00 % |
| lightness spread inside the moss | 4.4 | 5.8 | 5.6 | 6.0 |
| largest moss clump (dots) | 16,056 | 9,294 | 8,439 | 7,013 |
| brightest slate, mean lightness | 38.9 | 36.8 | 34.1 | 34.6 |
| slate-to-slate lightness spread | 3.84 | 3.84 | 2.65 | 2.51 |
| normal map: steepest 1 % tilt | 98.7 | 103.0 | 103.5 | 112.6 |
| normal map: average up-down slope (level edges) | 11.2 | 10.3 | 10.6 | 13.5 |
| normal map: average side-to-side slope (upright edges) | 16.4 | 13.7 | 14.2 | 15.6 |

| measure (copy of the look checker's script, 1254 dots) | before | after round 1 | now | reference |
|---|---|---|---|---|
| paint median slope (small = flat paint) | 3.06 | 1.25 | 1.91 | 1.86 |
| flat-paint share | 7.4 % | 18.9 % | 9.9 % | 10.9 % |
| hard-edge share | 28.4 % | 24.7 % | 23.8 % | 15.1 % |
| side-to-side over up-down paint slope | 2.44 | 1.89 | 2.08 | 1.61 |
| fine grain level | 1 | 0 | 1 | 1 |
| inner spread of a slate (mean / smallest) | 11.7 / 6.7 | 10.8 / 6.2 | 11.2 / 6.6 | 12.3 / 7.8 |
| spread of slate mean greys | 8.48 | 8.89 | 5.57 | 5.51 |
| slates more than 12 grey levels off the middle | 11 of 59 | 9 of 59 | 2 of 59 | 3 of 45 |
| moss within 14 dots of a side joint | 12.8 % | 14.5 % | 7.2 % | 6.5 % |
| tan share (checker's rule) / tan in pieces of 300+ dots | 2.23 % / 52.9 % | 1.18 % / 13.7 % | 1.47 % / 25.2 % | 1.56 % / 35.6 % |
| lower-edge wobble / corner rise (dots) | 1.33 / 6.8 | 1.78 / 12.3 | 2.21 / 14.8 | 2.98 / 17.7 |
| relief: steepest 1 % tilt / mean tilt | 98.7 / 22.5 | 103.0 / 19.7 | 103.5 / 20.2 | 112.6 / 23.7 |
| mean colour (Lab: lightness, green-red, blue-yellow) | 25.1, -1.8, -1.0 | 24.2, -1.7, -1.7 | 23.7, -1.8, -1.3 | 25.2, -1.6, -1.0 |
| share of dark dots (grey under 30) | 10.9 % | 12.5 % | 12.9 % | 11.3 % |

(Lab is a colour description in which the first number is lightness and the other two are the green-red and blue-yellow leanings; the "reference" column is
the reference picture measured the same way.) Most numbers moved towards the reference. Three moved away or stood still: the paint is still more
upright-stripy than the reference (2.08 against 1.61), the tile is a little darker (mean lightness 23.7 against 25.2), and the relief is still weaker.

### Pictures

![reference, before the look fixes, after](look_fixes/before_after_colour.jpg)

*Left: the reference (a guide only). Middle: the default tile before the look fixes. Right: after. At this size the after tile reads as the same roof with
cleaner paint, softer and rarer moss, pale broken lower edges in place of tan corner flakes, and rounder lower corners. The straight-edged flat
patches of paint (facets) that the look checker found are visible in it, for example the dark triangles.*

![the same, under a raking light](look_fixes/before_after_lit.jpg)

*The same three, lit from a low sun (top: whole tile; bottom: a 0.4-tile window). The after tile looks less like rippled planks than the before tile,
and still flatter than the reference, whose blotchy patches and chipped rims cast sharp little shadows.*

More pictures: `look_fixes/before_after_zoom.jpg`, `look_fixes/maps_after.jpg` (the five maps of the new default), `look_fixes/tuning_pictures/`, the look checker's
crops in `verify_look_after_fixes/round_2/`.

### What was tried and did not help (kept out of the default)

| tried | what happened |
|---|---|
| `combine.tone_blend` 0.7 to 0.45 or 0.55 (the look checker's suggestion for more relief) | worse by eye, by the slope measures and by the score (overall 0.693 against 0.724 with 0.7). The slate faces went flatter and the lip showed as a thin line |
| `combine.tone_blend` 0.8 | slopes about 4 % higher, not different by eye under the raking light, and more paint-edge relief (faint contour lines) |
| `combine.height_gain` 1.7 with `tone_height` 0.4, and 2.4 with 0 | LOWERED the relief |
| `damage.sink_depth` 2.2 with `lip_height` 0.14 and `shadow_height` 0.2 | changed the relief by 0.01: nothing, because `tone_blend` 0.7 scales the real relief to 30 % |
| `colour_and_fade.tone_centre` 3.85 or 4.0 (to undo the darker tile) | raised the brightest slate and dropped the colour group from 0.755 to 0.692 (the feature-size cliff); set back to 3.7 |
| `moss.joint_preference` 0 | lowered the moss but left the straight cut at the joint; the new `side_clearance` fixed it |
| `outline_and_shadow.lip_breakup` 0.6, `damage.side_share` 0.05, `colour_and_fade.outlier_share` alone | moved a stripe measure away from the reference / invisible / no change in the brightest slate |
| `streak_width` 0.024, `edge_ragged` 0.002 to 0.003, `streak_bend` 0.012 to 0.02, `mottle_tallness` 1.2, fade 1.0 or 1.15 | none removed the straight-edged facets; the smaller streak width made the paint more upright-stripy; more fade gave a little more relief and inner contrast but more dark dots and more stripes |
| `outline_and_shadow.joint_texture` 0.5 at size 600 | looked like grit at full size; 0.35 at size 150 kept |

### What is still wrong (the look checker's second look, 20 October)

* **Straight-edged flat facets (a new fault, the first thing a person would point at).** About 14 slates carry a flat dark or pale polygon with
  straight slanting edges, like cut glass. The old tile and the reference have none. They come from the broader, taller paint cells (Voronoi cells in
  `colour_and_fade.py`) once the edge wobble was turned down. They also show as straight scratch lines under the raking light. The look checker tried
  `colour_and_fade.streak_bend` 0.045 on colour-only test tiles (the edges curve into soft lobes and the stripes fall from 2.20 to 1.98) and with
  `mottle_tallness` 1.1 the facets nearly vanish but the paint turns swirly. A proper fix needs a change in the code of that layer (idea: bend the cell
  coordinates with a medium-sized noise before the Voronoi, so no cell border runs straight for 60 dots). **Not done.**
* The lower rim reads as frayed or chewed (a thin pale-grey lip with a pink-orange fringe) instead of the reference's smooth pale line with a few chunky chips.
* The moss is slightly too pale and thinly spread at 3 x 3 scale (strong olive dots 2.3 % against 5.0 % in the reference).
* The relief is weaker than the reference and different in character.
* Landmarks that repeat when the tile is tiled: a grey-brown flat slate pair near the bottom, a dark mossy slate, the facet triangles. No seams.
* Small: the whole tile is a little darker; a short pale hairline; a black wedge where an upright joint meets a rounded corner.

### What this re-bake re-made, and what it did not

Re-made on the new default (sections 7.1 to 7.6): the default tile (by the tuner), the ladder, the eight variations (four with new settings), the seed
spread, the 2 x 2 area, the half-tile test, the independence re-test of the two changed layers, a 512-dot confirmation, the debug views, the controls table.
**Not re-made**: the 4 x 4 area (marked "before the look fixes"), `resolution/` (the 512 and 2508 pictures there are of the old default; its 1254 entries are
links which I pointed at the old default's pictures so the folder agrees with itself), `controls_sweeps/` (strips made at the layer builders' starting values or
on the old default), `reuse/` (the brick; the unchanged layer files with the new controls at their starting values should give the same brick,
but that was not baked again), `links_and_order/`, the independence of the three layer files that did not change.

