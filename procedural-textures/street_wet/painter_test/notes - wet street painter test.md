<!-- NOTE (plain words): the report of ONE painter test on the wet street (20 October 2026). The painter (the image program Flux) was asked, once, to repaint the WET plate of the lockout shot with a brief that keeps the wet look, and I checked whether the wet look survived, in the painting and in the film's stage. Words used: "plate" = the picture drawn from the 3D street in Blender that the painter repaints; "painter" = Flux 3 edit on fal; "stage" = the film program that shines the painting back on the 3D street so the camera can move; "behind painting" = a second painting with the near props painted out, which the stage shows on road the props hid once the camera moves; "megapixel" = a million picture dots; "overlap" = of the brightest patches in two pictures, the share they have in common (1 = identical, 0.05 = what chance would give); "brightness" = a picture's own pixel brightness from 0 (black) to 1 (white). Nothing in the film project was changed. Everything here was run and looked at by me; what I did not do is listed near the end. -->

# Wet street painter test: did the wet look survive the painter?

## 1. The short answer

**Yes, mostly, and better than I expected.** With the brief changed to say "the street is wet after rain; keep the wet look exactly where image 1 has it", the painter kept: the glossy, darker road; the lamp, window and brazier reflections on the road (in the same places); the puddles in the gutters with the houses and lamps mirrored upside down in them; wet highlights on the setts (cobble stones); and soft reflections of the handcart and sacks on the road. It also tamed the blown-out white glare pool under the brazier into a warm painted reflection. It added nothing to the street itself and lined up with the plate almost perfectly (no stretch to undo).

**What it did not keep, or got wrong:** the cottage walls still do not read wet (the plate hardly shows it either); it **added pale white-grey brush-stroke clouds** to a sky that was a plain gradient in the plate (the brief says no bright clouds); it made the far lamp reflections stronger than in the plate; and the brightest bit of road is still a little brighter than the notice.

**In the film's stage** the wet look holds in the plate's own view and in a moved view, **but** the stage shows the film's old DRY "behind painting" on the road and pavement near the props as soon as the camera moves (71 % of the road pixels of the moved picture), which gives dry, pale patches next to the wet road. A wet behind painting (a second repaint, props painted out) would be needed before this could go in the clip. The stage also darkens the wet painting more than the dry one (details in section 7).

**Cost: more than the "about 10 US cents" you approved.** The painter's price is now 4.8 US cents a megapixel (twice the plan) and a 2k picture is about 4 megapixels, so one repaint cost **between US$0.197 and US$0.277** (fal does not show the exact charge; I could not tell which). One repaint, no second call, under the US$0.30 limit. See section 2.

**Good enough to use?** As a proof, yes: the painter keeps the wet look when told to. As the picture for the lockout clip, not yet: needs the sky fixed, a wet behind painting, and a brightness lift for the stage (section 9, each with its cost). Only ONE painting was made, so I cannot say how repeatable it is.

## 2. Money (ledger: `spending.md`)

* Price looked up with fal's price tool: US$0.048 per megapixel for `blackforestlabs/flux-3/edit-image`. The project's own lesson 139 says it doubled since the plan.
* The returned picture is 1520 x 2704 = 4.11 megapixels = **US$0.197**. fal does not say whether the pictures you send are charged too (the project's logs 32 and 34 assumed they are). If they are, the old way of working (plate 1536x2730 and style picture 768x1368 sent) would have cost about **US$0.43, over the US$0.30 limit**. So I sent them small (plate 810 x 1440, style 504 x 896, 1.62 megapixels together): worst case then **US$0.277**, best case US$0.197.
* Still not covered: if fal rounds every picture up to a whole megapixel the worst case could have been about US$0.38. I judged that unlikely and could not check it.
* **Calls made: 1** (request id `01a15ab1-7875-7200-b5e1-fb73c814521c`). It finished first time, so no second call was allowed. Everything else (Blender, the stage, the measuring) ran on this machine for free.
* Consequence for later: a repaint now costs about US$0.20 to 0.28 with small pictures, or up to about US$0.43 with full-size ones if inputs are charged. Not "10 cents".

## 3. What I changed in the painter's brief (side by side: `briefs/brief_old_and_new_side_by_side.html`; list of changes: `briefs/brief_changes_list.md`)

The old brief: the lockout painting's own brief (log 29) was not saved anywhere I could find, so the starting point is the brief recorded for the notice corner painting (log 32), the closest descendant (same street, same painter, same settings). It says "matte painted finish" and, in its never-add list, "puddles or reflections".

**Taken out:** "matte painted finish"; "puddles or reflections" from the never-add list.

**Put in (wet):**
* "painted wet shine and painted reflections" instead of "matte painted finish"; "wet after rain" in the opening line;
* one paragraph: the street is wet after rain and image 1 shows exactly where; KEEP, where image 1 has them, at the same size and strength, painted in image 2's hand (flat shapes of colour, a few ink lines, not a photograph, not a mirror): the sheen on the setts and flags; lamp, lit-window and brazier reflections on the road; the reflections of the handcart and sacks under them; the gutter and low-spot puddles with the houses, lamps and windows mirrored upside down; the thin dark wet lines between setts and flags; the darker damp foot of the walls; "the road never looks dry"; "add no wet look where image 1 has none";
* the gutter sentence says the rainwater lies in it as image 1 shows; "warm light stays only where it already is" now includes its reflections on the wet road; the no-halos ban says the road's reflections of the lights are not halos.

**Put in (props, not wet):** the old brief tells the painter to keep a kitchen chair and a lantern that are not in this plate (they are the notice corner's), so I swapped that list for what this plate has (handcart, spade, sacks, coal heap, pail, dustbin, ladder, lamps). Marked PROPS in the changes list.

**Kept as it was:** the camera, shapes, sizes and positions, the light and dark pattern, the thin parts staying thin, edges that must not join, the never-add list (flames, smoke, halos, people, extra props, bright clouds, new signs, new shadows).

Same settings as before: 2k, aspect auto, png, safety 2, prompt expansion off. **Two things differ from the earlier paintings**: the plate and style pictures were sent smaller (money, above), and the style picture is my best match for the earlier `style-glasgow.jpg`, which is not in the repository: I used the chapter 2 Glasgow tenements painting (`403-bg-glasgow-tenements.png`), which is itself a wet street painted in the series' hand. That may help the painter keep the wet look more than the old dry-ish style picture would; I cannot tell how much.

## 4. The painting and how well it lines up

`pictures/wet_painting_as_returned.png` (1520 x 2704), `pictures/wet_painting_lined_up.png` (resized to the plate's 1536 x 2730 and lined up). Lining up used a COPY of the film's `align_painting.py` (`alignment/align_painting_copy.py`; the film's file untouched) with a shot check file I wrote for the lockout shot (the kit has none): **the painter had hardly moved anything: stretch 0.9995, shift -0.5 and +0.5 pixels (of 1080 wide)**. Share of the props' outline points that sit on a painting edge: 0.903 before, 0.904 after. The existing dry lockout painting measured with the same tool: 0.876 before, 0.906 after (stretch 1.0025, shift +2.0 and -1.0 pixels). So the wet painting needed no real correction (the notice corner painting needed 0.70 to 0.96). Weak spots in the outline match, both paintings alike: the colliery gates (0.51; the painter draws arched gates) and the coal heap (0.69; dark on dark). Log: `alignment/align_wet_painting.log`.

## 5. Which wet cues survived (numbers in `numbers/measurements.json`; pictures in `pictures/`)

All measured at 1080 x 1920 on masks Blender made for the lockout camera (road, pavement, gutter, kerb, walls, props, sky), so each number is about the same place in every picture. "Dry painting" = the film's existing `lockout-painted.jpg`. "Dry plate" = the earlier helper's 540 x 960 dry picture of the same shot (the full-size dry plate no longer exists; only averages are taken from it).

| Wet cue | In the wet plate | In the new wet painting | Verdict |
|---|---|---|---|
| **Road darker and glossier than dry** | road brightness 0.364; dry plate 0.303 (1.20 times, but only because of the glare pool: far third 1.04, middle 0.81, brazier third 1.59) | 0.263; dry painting 0.367, so **0.72 times the dry painting** (far 0.58, middle 0.67, near 0.79); colder (blue minus red -0.04 against -0.07) | **Kept, and more convincingly wet than the plate.** Pictures: `compare_crop_road_*_100pct.jpg` |
| **Sheen on the setts** (bright edges on stones) | 0.7 % of road pixels are clearly brighter than their surroundings | 6.9 % (dry painting 3.2 %) | **Kept, stronger than in the plate** (painted white highlights on joints: visible in `compare_crop_road_near_100pct.jpg`) |
| **Lamp, window and brazier reflections on the road** | brightest tenth of the road | the same places: **overlap 0.63 over the whole road** (near third 0.67, middle 0.74, far 0.20); the dry painting 0.04 (chance 0.05). Light pattern likeness (correlation) 0.91, dry painting 0.27 | **Kept in place** |
| **Lamp reflection streaks on the far road** | faint, at x = 205 (0.11 above surroundings), 528 (0.02), 709 (0.03) | at x = 205 (0.23) and 532 (0.16), plus a new one at 440 (0.09) | **Kept in place but made much stronger** (the second one about 7 times); one added. They read well in the film, but they are the painter's, not the 3D street's. `compare_crop_road_far_100pct.jpg` |
| **Brazier glare pool** (a weak spot of the plate: 10 % of road pixels over 0.9) | blown out to white | pool kept in shape (overlap 0.67) but now warm orange with blue-violet shine; 0.1 % of road pixels over 0.9 | **Tamed, as hoped.** The brightest 1 in 1000 road pixels is 0.90, still 1.21 times the notice paper (0.745); dry painting 1.05 times. A small break of "nothing is brighter than the notice" |
| **Puddles in gutters and low spots, houses mirrored** | right gutter, left gutter by the cart, the pool beside the drum | **kept, with the mirrored lit windows and lamps painted as vertical ripples**: brightness along the gutter follows the plate (likeness 0.82; dry painting 0.64); gutter brightness 0.167 against the plate's 0.174 (dry painting 0.319). Pictures: `compare_crop_right_gutter_100pct.jpg`, `compare_crop_left_gutter_and_cart_100pct.jpg`, `compare_crop_right_edge_dustbin_pail_100pct.jpg` | **Kept.** Careful: I had no exact puddle map for the lockout camera, so this is the gutter profile plus my eye on six crops |
| **Handcart and sacks standing wet** (a weak spot: props stood dry) | soft reflection under them | painted dark reflections under the cart wheel and sacks; the sacks' shadow kept | **Kept** (they still look as if they hover over the road, as in the plate) |
| **Wet dark joint lines** | thin dark lines | kept as dark lines between setts and flags, with white highlights on one side | **Kept** |
| **Darker, damp foot of the walls** | weak: foot is 0.725 of mid-wall brightness (dry plate 0.835) | foot 0.689 of mid-wall (dry painting 0.596) | **Not a visible cue in either.** The measure cannot tell wet from dry here (the dry painting has dark plinths). Walls are painted dark overall (mid-wall 0.14; dry painting 0.29) but do not look wet. A weak spot of the plate that the painter did not fix and was not asked to invent |
| **Overall light and dark of the plate** | | blurred brightness likeness to the plate 0.84 (dry painting 0.57) | the wet painting follows the plate's light and dark much more closely than the dry painting did |

## 6. Added, removed, moved or broken, and the style

**Added**
* **Pale white-grey brush-stroke clouds across the sky**: 19 % of the sky is clearly brighter than the plate's plain sky (7.9 % over 0.5 brightness). The brief bans bright clouds; the painter ignored it. The old dry painting had clouds too (darker, 52 % brighter than the plate) and chimney smoke; the new one has no smoke (the new brief bans it, and it obeyed). In the stage the sky card takes this sky, so the clouds are in the film. This is the clearest fault.
* The stronger and extra lamp reflection streaks (section 5).
* A few white paint-like highlights on pavement edges. A small whitish paper-like patch at the drum's rim (the plate has white paper bits there; check by eye in `compare_crop_brazier_area_100pct.jpg`).

**Removed**: nothing from the street. All the props are there (drum, notice board, pail, lamps, cart, spade, sacks, coal heap, dustbin, ladder, gates, chimney, winding wheels). The soot-and-ash ring the dry painting had round the drum is gone (that was an addition of the old painting).

**Moved**: nothing measurable (section 4).

**Broken or changed**
* The notice's small print and the colliery sign are blurred or garbled (expected; the film keeps its own sharp copies of both).
* The gas lamp glass is pale yellow-white rather than the warm amber the brief asks for.
* The colliery gates are drawn as an arched double gate (the dry painting did the same).
* The brick of the chimney and the colliery building is more saturated orange-red than the plate.

**Style against the series** (rough numbers at 768 wide, `numbers/style_match.json`; the real test is your eye): share of dark outline pixels 0.115 (dry lockout painting 0.116, notice corner 0.105, Glasgow style picture 0.20); busy fine texture 0.235 (0.234, 0.189, 0.42); flat colour patches 0.23 (0.35, 0.29, 0.17). So by these numbers it sits where the earlier paintings sit, a little more textured. Dark ink outlines are on 90 % of the props' outline points (dry painting 97 %). By eye: the roads and props are in the series' hand; the sky's coarse white strokes look like another painter and are the part that does not match.

## 7. In the film's stage (pictures: `pictures/stage_*.jpg`; numbers: `numbers/stage_measurements.json`)

I made a COPY of the film's stage, scenes and renderer (`stage/kit_copy/`; the big 3D set files are links, only read), and drew the film's real lockout scene through the film's own renderer, in a hidden browser with software graphics, with the film's dry painting and with the wet painting. The one change in the copy: the painting's file name can be given in the address. Stills at 6.0 s of the clip (no titles on screen; the live fire, flames and smoke are drawn on top the same way in every picture).

* **Plate view** (the plate camera, the first frame of the clip): the wet painting comes through as a wet street (`stage_plate_view_dry_and_wet.jpg`). Likeness of the road's blurred brightness between painting and stage picture: 0.98.
* **Moved view** (the film's street move: 1.4 m forward, 0.3 m right, 0.05 up, turned 5 degrees right, lens 26 degrees; and one mid-move still): the wet cues stay on the road because they are painted on it: the gutter reflections, the sheen, the wet pavement edge (`stage_moved_view_four_ways.jpg`, `stage_mid_move_three_ways.jpg`). Painted reflections do not slide as the camera moves, as real ones would. Estimate (not measured): for the far lamps a real reflection would have moved about 0.9 m along the road; at a 1.4 m move this was not visible to me as a fault.
* **The problem: the behind painting.** As soon as the camera moves, the stage shows the behind painting on road and pavement near the near props. The film's behind painting is DRY. Result (`stage_moved_view_road_close.jpg`, `stage_moved_dry_behind_patches_map.jpg`): about 18 % of the moved frame, **71 % of its road pixels and 70 % of its pavement pixels**, wear the dry behind painting: a pale, dry-looking ghost beside the drum and dry pavement at the foot of the frame, next to the wet road further up. For comparison I also drew the wet painting as its own behind painting: no dry patches, but that is only a stand-in (a real behind painting has the props painted out, which needs a second repaint, not done). Roughly 75 % of the moved frame wears the painting, 18 % the behind painting and 7 % the 3D set's own surface (read from the colour map, by colour).
* **The stage's own brightness curve crushes dark areas, and a wet painting has many.** The same curve acts on both paintings: painting brightness 0.08 becomes 0.02, 0.13 becomes 0.07, 0.17 becomes 0.13, 0.24 stays 0.24, 0.5 becomes 0.59. The dry painting's road arrives at 0.92 of its painted brightness; **the wet painting's road at 0.75** (walls 0.76 against 0.90), so the road is darker in the film than painted (0.19 against 0.26 painted). It makes the sheen stand out more but loses the dark sett joints. I did not look into the cause (a look setting in the film's scene file: contrast 1.04, vignette 0.3 and the stage's finishing step are candidates).

## 8. Failures and slips (all of it)

* The lockout painting's own brief and the exact `style-glasgow.jpg` were not found; I used the notice corner brief and the chapter 2 Glasgow painting instead (section 3).
* The dry full-size plate of the lockout shot no longer exists; I used the 540 x 960 one from the earlier helper for averages only.
* My first shot-measuring run failed (the film's tool allows at most 20 groups and my check file had 25); I merged groups and re-ran. My first brief script stopped on my own safety check because I had written "never matte" into the new brief; I reworded it ("never looks dry"), so the word "matte" is not in the new brief.
* The price turned out to be twice the plan, so I changed how I sent the pictures (smaller) without being able to test whether sending full size would have changed the painting.
* Several of my measures are my own proxies, not film-kit tools: the glint share, the overlap of bright areas, the gutter profile, the ink-line share, the cloud share. They are defined in the scripts' notes (`tools/`). The dark-outline test and the style numbers are rough.

## 9. What would improve it (not done; each with its cost)

| Change | What it fixes | Cost |
|---|---|---|
| **Brief:** "the sky is dark grey-blue cloud with soft edges like image 2; no pale or white clouds"; "do not make the streaks stronger than in image 1" | the white clouds, over-strong streaks | one more repaint: about US$0.20 to 0.28 with small pictures (US$0.43 with full-size ones if inputs are charged). Result not guaranteed: the painter already ignored "no bright clouds" once |
| **Free, here:** put the old dry painting's sky (or the sky of any series painting) into the wet painting, above the rooflines, before the stage | the clouds, without a new paid call | nothing in money; under an hour of work; untested, and the roof edges need a clean cut |
| **Wet behind painting:** repaint the wet painting with the near props painted out (the film's method) | the dry patches when the camera moves (section 7) | one more repaint: about US$0.20 to 0.26 if the picture sent is small (up to about US$0.39 at full size if inputs are charged) |
| **Stage or painting:** lift the dark values of the wet painting before it is projected, or the film's brightness curve for wet scenes | the stage darkening the road to 0.75 of painted | nothing in money; a test of 2 to 3 minutes a picture; untested |
| **Plate** (Blender, free, about 20 to 50 minutes a full-size plate): lower the road's Film Coat and Specular Boost so the pool is not blown out; add visible wet foot to the walls; wet contact under props | the glare slightly brighter than the notice; the walls not reading wet; hovering props | no money, but it needs a new repaint (above) to show up |

## 10. What I did not test, and what I am unsure of

**Not tested**
* The whole lockout clip filmed with the wet painting (only stills at 6.0 s; no frame-by-frame look).
* A wet behind painting; a second try with a better brief; other random draws of the painter (only one painting exists, so how repeatable this is is unknown).
* The plate sent at full size (1536 x 2730); I do not know whether it would paint wetter or drier.
* The sky swap and the brightness lift (section 9).
* The notice board close shot (it keeps its own lettering, not affected by the painting).
* A phone screen.
* Moving reflections: how a sliding real reflection compares with the painted one (only an estimate).

**Unsure**
* How much the Glasgow style picture (itself wet) helped the painter keep the wet look.
* The exact money spent (US$0.197 or US$0.277, or in a rounding case more).
* The reason for the stage's darkening curve.
* Whether my "wall foot" measure is a fair one for walls whose plinths are dark in both pictures.

## 11. Files (folder `painter_test/`)

* `notes - wet street painter test.md` (this file), `result.json` (the structured result), `spending.md` (money ledger), `painter_request_and_result.json` (request id, settings, pictures sent, link of the returned picture).
* `briefs/`: `brief_old.txt`, `brief_new_wet.txt` (exactly as sent), `brief_old_and_new_side_by_side.html` (differences marked), `brief_changes_list.md`, `brief_pair.json`.
* `sent/`: the two small pictures sent to the painter.
* `pictures/`: the painting (`wet_painting_as_returned.png`, `wet_painting_lined_up.png`); `compare_full_picture_three_across.jpg` (wet plate | wet painting | existing dry painting); the 100 % close-ups `compare_crop_*.jpg` (road near, road far, right gutter, wall foot, brazier area, left gutter and cart, left lamp and ladder, right edge, colliery gates); the stage pictures `stage_*.jpg`.
* `numbers/`: `measurements.json` (and its printout), `stage_measurements.json`, `style_match.json`.
* `alignment/`: the copy of the lining-up tool, the two shot check files, Blender's measured outlines (`facts*/`), the lining-up logs.
* `stage/`: `kit_copy/` (the stage copy), `stills/` (the raw stage pictures), the render log.
* `tools/`: every script I wrote, each with a plain note and its run line. `work/`: working logs and small pictures.
