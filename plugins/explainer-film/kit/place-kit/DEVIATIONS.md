# Where the build differs from its design, and why

What this file is: the place kit was designed first and built second. This lists every place where the build is not what the design
said, with the reason and what was measured, and what was found wrong while testing. It says "measured" for numbers that came from a
run on the slow computer the kit was made on, and "judged" for numbers a person chose by looking.

## Found wrong while testing, and fixed

These were real faults in the first version; each now has a test that fails without the fix.

1. **The per-picture normal-map direction check could not fail.** It compared each kit-made normal map with the height picture
   the scene keeps next to it. That picture is stretched to 0..1, so its slope is about 0.005 a pixel, and the check called every
   axis "not informative" (a rule meant for a map with no slope on one axis). Every map passed. The end-to-end test light still
   worked (it draws its own bump), but a normal map flipped by hand in the scene passed `normals-test`. Now the height is scaled
   so its steepest one percent tilts the surface by 30 degrees before its slope is judged. After the fix a map whose green channel
   was flipped by hand fails `normals-test` (exit 1) and the picture is named; every one of the 9 maps in the test yard agrees with
   its own height. (`surfaces/normals.py`, `test_place_blender.py`.)
2. **The construction check had four faults that the first small scenes did not reveal.** A door's "floor close below" ray started
   inside the door and always read a gap of 0, so a door floating 60 cm above the ground passed. A free span was measured with a
   ray from inside the support, which read the plank's own underside and saw no support, so a plank spanning 2.5 m between two
   blocks showed a span of 0. A rail with only 2 cm inside its post counted as joined because the overlap was measured by its
   largest extent instead of the depth it really sits in. A beam resting on posts was called "short" because the rays of its side
   faces counted. Each is fixed and each case is a test (`checks/construction.py`).
3. **Fence rails were called floating and the wrong size.** A rail joined into two posts is carried through them (the fence role may
   now hang); and a rail is not "a fence of 0.14 m high", so the fence-height fact skips a long low piece that lies along the fence.
4. **Plants could stand on the edge of a wheel rut.** The track mask is drawn on 10 cm cells, so a plant within the rut's width but in
   a cell whose centre was outside it was allowed. A cell the rut touches anywhere is now blocked, so the gate is exact-zero on the
   whole nominal rut (measured: 7 roots within 2 cm of a rut edge before, 0 after).
5. **Undo left the ground without its material.** The mesh swapped back after grading still held the kit's material in its slot.
6. **A material rule decided the whole object.** A rule that named only the iron-band material made the whole barrel iron; it now
   gives that slot its role and the barrel stays a barrel (the first test of "one object, two roles" failed).
7. **A graded ground was UV-less and called coarse.** The ground was graded after its UVs were written, so the new mesh had none, and
   the audit judged "coarse" by the mean edge, which a graded grid always fails. UVs are written after grading, and the audit reads
   the 20th percentile edge for ground.
8. **Litter counted just under its minimum.** 57 pieces on 196 square metres is 29 per 100, under 30. The scatter now adds rounds of
   candidates (at most four) until it clears the minimum with a 15 percent margin.
9. **A generic name decided the role of an object.** "Object.012" in a collection called "Roofs" became the generic prop. The
   generic role's name hints now count only when nothing else fits, and a plural collection name ("Roofs") reads as its singular.
10. **The first wear was too faint to see.** The first amounts gave a mean pixel change of 3 percent (kept), 5 (lived in), 9 (neglected)
    and 11 (derelict) on a hut, and the moss, once raised, spread evenly like camouflage. Amounts and dial defaults were raised, the
    foot splash and soot made stronger, and the moss gated by large regions and by height. Measured on the hut: 5.5, 10.4, 15.5 and
    18.2 percent. The numbers are judged, from looking at pictures; they are still first tries.
11. **The squint test could not tell opposite pictures apart.** Two opposite pictures (light where the other is dark) scored 0.61 on the structural similarity, which reads as "much the
    same"; the small stability constant added to the contrast part of the sum was too large for pictures reduced to a blur. It is now (0.004) squared and the same pair scores low
    (`picture_measures.py`, `test_picture_measures.py`).

## Found wrong by the first full check, and fixed (the fix round, 23 October 2026)

A first helper built a 12 m canal lock using only the plugin's steps; a second read the code and docs and ran the commands on small scenes; a third followed two plans blind. Each fault
below was reproduced, fixed, and given a test that ALSO shows the old behaviour (a control), in `test_place_fixes.py` unless another file is named.

1. **A scene whose objects had no material at all passed the audit** (the treatments were counted material by material, so no material meant nothing to fail). The audit now lists every
   treatment missing on an object with no kit material, and the judge fails it; plants and litter are required per ground role whatever the materials. (`test_place_audit_check.py`, `test_place_fixes.py`.)
2. **`undo` crashed after the kit itself had added the sun** (it read the light's name after removing the object). Names are read first now.
3. **A road drawn as one curved strip was replaced by a grid over its whole box**, and a hole cut in a towpath was filled (which also moved the steps in it up 2 m, silently). Coarseness is
   now judged from the area per face; a plain rectangle is regraded, any other outline is subdivided in place and keeps its shape and holes; the audit fails a ground whose area grew more than
   1.5 times (`pk_area_before`); and `finish` prints every object a re-seat moved by more than 3 cm, with the distance.
4. **The ground-seat check read the raw box corners**, while `seat_on_ground` reads points pulled in. Both use the same footprint points now, a point with no ground under it is unknown (not
   height 0), and the report names the ground object and height it found.
5. **Only roles that REQUIRE a bevel got one**, while the audit counted every object: stone, steps, iron and crates stayed sharp. Every object whose surface has a bevel width is bevelled; the plain-box
   check counts the same set.
6. **Correct joinery failed.** A rail set 4 cm or more into two carried posts is carried ("framed in"), a part sunk up to 4 cm into its carrier is resting (the real overlap is reported in
   millimetres), a stake driven into the top of a carried part is carried, a part standing in water and rising through its surface is carried (a boat afloat).
7. **Steps had no role** and fell under `floor.stone`, whose indoor skip switched off moss, wetness, plants and litter outdoors. There is now `stone.step`; the indoor skip covers only indoor floors; the
   step-rise fact is matched by role and measured top to top; `roles --list` prints every role id with a line of meaning.
8. **A plain sky failed every picture** ("flat windows ... below the sky" when the sky was most of them), and one guard served all views. The sky is found by itself (flat windows joined to the top edge,
   inside the top 40 percent); a guard records its own allowance for a place that is already teal or red; one guard file may hold a guard per view (`make-guard --view`). While testing this a fourth fault
   appeared: the second `make-guard --view` wiped the first view, because the report's `--out` and the guard file are the same file and the report was written first. (`test_picture_measures.py`.)
9. **`combine --order both` failed with the ground in the list** (everything is seated on it). The recipe (the ground alone first, then the rest in both orders) is in the README and the steps.
10. **Draft settings and output.** `new-settings` prints one line per role, not per object, says which look and state it started from, and checks a road's rut depth against the relief floor.
11. **`light` treated a world colour as a light.** Only lamps count as the scene's light for the sun now (a world colour alone is no key light and gets a sun).
12. **`finish` did the whole job and then failed for want of `--save-as`;** it checks first. The `NEXT` line carries `--reports`; the preflight writes beside the audit when it has one (a run started from the
    plugin's own folder no longer litters it); `finish`, `audit` and the preflight take the facts file as `--facts` (the preflight's `--real-world-facts` is the same option).
13. **A close-up was saved as `closeup_closeup.jpg`, and one local picture cost a preview as well.** Files are named by view and kind once; a view may say `"kinds": ["final"]` for exactly the pictures it wants.
    (`test_place_render.py`.)
14. **`finish-part` always exited 1** (it forced a quick pass and the judge failed a quick pass). A part's audit now gives a LOOK for the quick pass; a clean part exits 0.
15. **Curves with a bevel, text, metaballs, surfaces and collection instances escaped the whole pass** (only meshes were looked at). They are turned into meshes at the start of `finish` (originals hidden,
    `undo` restores them); a drawn object that cannot be converted (hair curves, grease pencil, volumes) is named as a failure.
16. **A mirrored wall was "inside out" and its roof "floated"** (the winding was not flipped for a negative scale); a wall turned 45 degrees was not size-checked (a world-axis box); a sun lamp was "inside a solid".
    All three fixed (oriented size, flipped winding, lamps skipped for the sun).
17. **The ground part could not make the cameras it was told to make** (they are frozen for everyone). `frozen.set_by` in the ownership file names the one owner that may make them.
18. **A plain request never got ruts.** `finish` drafted `roads: []`. It now drafts a road entry for every object with a road role (centre line from the object's shape, the width from its short side) and
    takes `--type` and `--place`; the road's centre line is read from the road skeleton (its ends can be about 1 m short, and a U-shaped road cannot be read: write the polyline).
19. **The rented-card client printed the endpoint id in one error, and the docs and the code disagreed about the settings file.** Messages never hold the part of the address after `/v2/` and every message is scrubbed;
    the client reads `NAME=VALUE` lines and a JSON file; the default store folder is `/workspace` everywhere. (`test_place_render.py`.)
20. **`render --where auto` kept previews tiny even when the renderer is Cycles and a card is set up.** It now sends them to the card (and says so). A water-in-view scene draws with Cycles (switchable:
    `place_render.cycles_when_water_in_view`), because a flat dark slab of water was the weakest picture of the first full check.
21. **A kept material (a lettered sign with its own picture) failed the audit for ever.** It keeps its picture and gets roughness variation and a normal map as `pk_augment` nodes (`undo` removes them).
22. **An empty scene crashed `finish` with "cannot convert float infinity to integer"**, and an empty audit passed. Both stop with a sentence now.
23. **Water was a solid, and nothing wetted the ground beside it.** Water is its own class in the wear masks and the ground within about 3 m of it is damp (measured on a toy quay: 0.00 at 0.1 m from the water before, at least 0.4 after, fading to 0 by 3 m).
24. **Name hints misread harbour and mill words** (a waterwheel was a cart wheel, reeds a thatch roof, a haystack a chimney, a quay wall plaster). Fixed in `roles.json`; "Cart wheel" is a wheel, not a cart.
25. **After `finish` a roleless object became the grey generic prop and only warned** until half the objects were so. Above 15 percent (`place_audit.fallback_role_share_fail`, invented) it fails.
26. **The plates stage skipped the audit without a word when no scene was named.** It now says, as a LOOK, that no audit could be required. (`test_preflight_place.py`.)
27. **The house number for rut depth cited "the yard's ruts were 4 to 9 cm deep"; the yard's own code says 0.15 m.** The source now says the 4 to 9 cm is the plugin's own earlier test yard; the kind stays invented.

Not fixed in the plugin (and why): the repository's marketplace file (`.claude-plugin/marketplace.json` in the folder above `plugins/`) is outside the plugin folder and still says 1.3.0; the main session or the person sets it. The workflow and agents have not run
under the real Workflow tool. The choice of two repair rounds before drawing (the design said both "at most 2 rounds" and "fails twice stops") is the person's to confirm.

## What the workflow builder added to the design

- A **Ground phase** before the parts (the ground is built alone first and frozen, then the other parts are seated on it), on a checker's advice. No paid Concept phase: reference pictures come in as arguments.
- Extra arguments (`scene`, `references`, `accepted`, `ledger`, `environment`, `planEffort`, `maxRepairRounds`) and extra fields in the reports (the plan's `ground_owner`, `scene_file`, `look`, `state`, `notes`;
  a part's `work_file`, `steps_finished`, `failures`, `not_tested`, `views_to_redraw`; the render report's `half_path` and `guard_provisional`; "not judged" as a verdict; `audit_scene_sha1`).
- The blind reader's prompt does not start with "First read <agent file>" and holds no word of the feature list; the skeptic is a sixth mode of the checker agent.
- Builders never use the rented card (only the renderer does, to avoid several wake-ups).

## Where the build chose differently from the design

- **Displacement is on more roles than the design listed.** The design had real displacement on roads, mud, thatch and rock ground.
  Earth, forest floor, gravel, paving and stone-rubble walls now also displace, because a plain request for ground and stone should
  get it by itself. A ground mesh too coarse to show it is replaced by a graded grid (0.12 m squares near the viewer growing 9 percent
  a step to 5 m), keeping the old surface height. The audit requires it for those roles.
- **Plan masks are drawn in plain numpy, not baked in Blender.** The ground and the objects are drawn from above into a grid
  (default 0.10 m cell, or the larger of that and the place's extent over 1500, with a time budget), blurred and measured with a
  chamfer distance transform; the shade is a plan-view shadow estimate, not rays. They are stored in three 8-bit pictures. This is
  the lighter route the design allowed. Measured: 0.4 s for the hut, 8 s for the 36 by 26 m yard. Not tried on a larger place.
- **Roads are a height function applied to the ground's vertices**, not a node network: a uniform 0.12 m grid when the ground
  would stay under 150,000 faces (the 36 by 26 m yard became 72,478), else the graded grid. The audit measures the ruts from the real
  surface by rays: in the yard the median depth was 7.2 cm against 8 cm in the settings and the gauge was within 15 cm of 1.3 m.
- **Plants and litter are real small pieces built in numpy and joined per kind**, not instanced by geometry nodes. A tuft has 5 to 9
  blades; no piece has more than 200 triangles. The yard got 485 plants and 646 litter pieces in 11 objects.
- **The audit and the judge are two programs.** Blender writes facts (hashing the saved file, never re-saving it); plain Python
  decides with the house numbers. `finish` saves, reopens the saved file and audits that, so what was audited is what is on disk.
- **Local pictures are tiny on purpose.** On this computer a 1200 by 800 EEVEE picture took 94 s and Cycles 35 to 90 s a frame, so
  local previews are capped (480 x 320 at 8 samples for EEVEE, 320 x 240 at 16 for Cycles) and say so; real sizes go to a card.

## D7: a normal map and displacement together (measured)

The design asked whether both together double the relief. A flat 120 by 120 plane, one tile of the surface, a sun 10 degrees above
it, Cycles on the processor, relief contrast = spread of the light and dark over their mean:

| Surface | Normal map alone | Displacement alone | Both, normal at 0.6 times | Both, normal at full strength |
|---|---|---|---|---|
| packed earth | 0.67 | 0.27 | 0.65 (0.97 times the larger) | 0.79 (1.18 times the normal alone) |
| dirt road | 0.76 | 0.53 | 0.84 (1.10 times the larger) | 0.95 (1.25 times the normal alone) |

No doubling was found at either strength. Both together add at most 25 percent over one alone, and with the normal strength at 0.6
the pair stays within about 10 percent of the larger one. The kit keeps the factor 0.6 where displacement is on (the coal-mine
yard's decision), so the fine grain comes from the normal map and the displacement adds silhouette, not a second copy of the same
bumps. The test is `test_place_blender.py` ("D7 low-angle test"); the Scenario texturing skill's "never both" is therefore not followed.

## Changes made to the film's older tools while building this

Each of these is small, has its own test, and leaves the old behaviour reachable or word for word the same unless the new option is used.

- **`model_kit.py` (the film's model builder).** A bevelled edge now carries hardened normals and a Weighted Normal modifier, and its faces are smooth-shaded, so a big flat face
  shades evenly to its edge. Measured on a 2 m box with a 0.1 m bevel: the jump between neighbouring strips of the bevel is 50.2 degrees flat-shaded and 16.5 hardened; the big
  face stays exactly flat in both. `model_kit.HARDEN_BEVEL_NORMALS = False` gives the old shading. Normal maps are now saved as PNG files (a JPEG's blocks show as faint squares in
  the shading) and a colour picture is a PNG when Pillow is missing. The one-tile brick normal map as a PNG is 1.29 MB; a block with a slate material and both pictures makes a .glb of
  0.98 MB. Models made earlier are not rebuilt by this; a model made again looks slightly different at its edges. (`test_model_kit_surfaces.py`.)
- **`textures.py`.** It no longer imports Pillow when loaded (Blender's own Python has none, and the module used to fail there). A made picture is a `Picture` holding its pixels in
  numpy; `.save("x.png")` writes a PNG with numpy and zlib (each row stored as the difference from the row above, checked to read back exactly), and a JPEG still needs Pillow and says so
  in a plain sentence when it is missing. The build scripts that draw text with Pillow are untouched.
- **`model_lint.py --surfaces`.** Warns (never fails) about a model whose materials have no normal picture. (`test_model_lint.py`.)
- **`make_check_file.py`.** A check file made from a saved scene now carries `scene_file`, the scene's path from the check file's folder. The preflight's `plates` stage reads it and
  then requires that scene's place audit before a painting is paid for. Proved with a real run on a saved yard scene (`../scene.blend`); the path sums are in `test_make_check_file.py`.
- **`paint_request.py --keep-wetness`** (or `"keep_wetness": true` in the brief). By default the painter prompt forbids every puddle and reflection, word for word as before. With
  the option, the wet ground the place was built with is in the Keep list and only NEW puddles and reflections are forbidden. Tried on the template's words only; no paid painting was
  made, so how the painter treats the new words is not known. (`test_paint_request.py`.)
- **`plan_budget.py` push check.** It now also refuses a file with a RunPod-style key (it begins `rpa_`; that form is a belief, not read from RunPod's documents), a setting named
  `RUNPOD_API_KEY` or `RUNPOD_ENDPOINT_ID` set to a value, or a rented-card address with its id. The help text that shows those names with placeholders is not refused, and the whole
  plugin folder has nothing refused. The test makes its pretend key and id at run time. (`test_plan_budget.py`.)
- **`explainer-film-setup`.** It checks the files the skills name under `place-kit/` too, says whether Blender's own Python has Pillow (normally no, and nothing in the place kit needs it),
  says whether `xvfb-run` is there, and says whether the person's rented-card settings are set in the shell: yes or no, never a value, and it never reads the settings file.
- **`test_preflight.py`.** The film stage reads the free disk of the computer it runs on, so the test failed whenever the disk was nearly full (a fault from before this work).
  The test now passes `--free-disk-gb 40`; `preflight.py` gained the option `--free-disk-gb` for the film stage to make that possible.

## Added in the batching step (23 October 2026)

- **`variations` and `card-time`** (new verbs; design in `skills/surfaces-wear-and-construction/batched-rounds-and-card-time.md`). The design asked for jobs that "measure" their pictures. The measures are made HERE, from the small
  JPGs after they come back (Pillow is not in Blender's Python, and measuring costs no card seconds), so the card only draws.
- **Two ways to reach a card.** The plugin's own client, and any command-line client with `upload`, `run`, `job` and `download` (`--card-client`). The real proof batches used the second one with the project's own client, because the
  plugin's client needs the person's settings, which a helper may not read. A command-line client cannot say what an upload billed, so those steps are counted from the wall clock and marked as an estimate in the ledger and on the sheet.
- **The card gate is in every command that starts a paid step** (`rent upload|run|status`, `render --where rented`, `variations run`); `render` and `rent` got `--helper`, `--role`, `--ledger` and `--over-allowance`.
- **The difference threshold is 8 percent of a setting's range** (first written as 15): ten values of ONE dial must fit in its range, 10 percent apart. A first real batch showed that settings far apart can still give nearly the same picture
  (moss at 0.15 and 0.75 in a scene where moss hardly shows); so the pictures decide after drawing, and the sheet says which variations did not show.
- **The sheet stays under 400,000 bytes** (not 400 KiB): the quality and then the size are lowered until it fits.
- **The scene is stored on the card's store under its checksum** (`place-jobs/scenes/<8 letters>/`), so the second and last batch for a change does not upload the scene again.
- **The free scout (`variations scout`) was added after the first real batches** (a second helper, the same day). The first real moss batch drew 10 variations whose settings were far apart, yet 5 showed nothing on the card:
  the settings check before drawing cannot know which part of a dial shows. The task asked for a check BEFORE drawing; the scout is that check made with pictures, drawn here for free. Its own limits were calibrated on the two
  real batches (see `place_kit/variations/scout.py`); `plan` and `run` use it by themselves. It is only as good as one scene and two cameras have shown.
- **`amount.<layer>` and `master` now SCALE the saved scene (0 to 2, 1 = as saved).** They first SET the layer's strength (0 to 1, 1 = "the look as written"), which could only ever try less wear than a scene whose look
  already set a layer to full strength, and whose "saved" value was not known before drawing. A file written for the first meaning reads differently now; the two earlier real batch files used it.
- **The saved scene's own dial values are read** (by the scout, and by every job: `saved_values`), shown under the baseline on both sheets, and used by the settings check before drawing; a dial's default is used only
  when there is no scout.
- **`make --range KEY LOW HIGH`** spreads a setting over the part of its range that shows (the cracks of the lock disappear below a density of about 0.5).
- **A job is written into the ledger when it is SENT** ("sent", with an estimate) and again with its billed seconds; the run folder keeps `run-state.json`, and `variations collect RUN-FOLDER` finishes a batch whose command
  was cut off (the earlier design wrote the ledger only after every job had come back, so a command stopped by a time limit wrote nothing although the cards had billed). `rent run` and `render --where rented` write a
  "sent" line too. The set-up uploads are written before the long wait, the downloads after it (two lines instead of one).
- **The ledger file is locked while a line is written** (`fcntl` where the system has it), so helpers writing at the same moment never mix their lines.

## Found by the last check and the second newcomer round, and fixed (23 October 2026)

- **The Poly Haven list was one place's shopping list.** It is now a small, even-handed sample read from the public Poly Haven list (one or two pictures per kind of surface, a
  few everyday props, real sizes read from the list), with no "not found" list, and its text says to search the site for what your own place needs. Three per-surface picks in
  `surfaces.json` were wrong (a gravel name that is not on the site, a wall slate for roof slate, a mossy brick floor for a brick wall) and were changed.
- **"Measurably" is not always "visibly".** A pair that differs only by its mean (a faint, even tint; in every camera almost no pixel moved by more than the pixel step) is now
  named "may not be visible" on the sheet, in the report and in the scout, and `plan` repeats it from the scout. It is NOT dropped. Changing the rule itself to the changed
  share alone was tried on the two saved real batches (from their saved numbers, nothing drawn again): the card's verdict changed on 7 moss pairs and the scout then missed one
  of them (21 of 22), so the measured rule was kept and only the note added.
- **`finish` and `new-settings` count roles by where they came from**: place_role tags, settings rules, guesses from names. Tagged roles were reported as "guessed from names".
- **Weak name hints.** The bare words "roof", "wall" and "house" name the thing but not what it is made of; any other hint found at the same place (the name, a collection,
  a material) now beats them, and the name still counts more than a material, so "Station roof slate" is a slate roof, "Roof tiles" a tile roof and "Timber wall" a plank wall. "Railway track", "Water tower", "Water crane" and "Canopy column" no longer read as a dirt road,
  still water or foliage (they stay unknown, so the builder must say), and "Market floor flagstones" is a stone floor. (A rule "the longer match wins" was the first idea; it
  would have made "Fence post 3" a fence, so the weak hints were used instead.)
- **The harbour preset's `quay_no_growth` switch is gone**: it switched plants and litter off on the whole quay, for a reason no tool kept (footfall already keeps the
  walking strip clear). The canal lock, a harbour-type place with no off entry, passed the audit with 66 plant and 101 litter pieces.
- **Words**: the pass never removes a piece and does not darken the ground where things touch or where water runs (the builder builds those as shape); the trade's own
  rubbish is built as shape too; the state is `damp` outdoors near water or deep shade when the words say nothing (`dry` switches every wet mark off); a local batch counts
  as one of the two; `--helper` takes a helper's short name, never a person's; the names `make` writes are percent of a setting's range.
- **`explainer-film-setup --help`** printed mkdir's help and could then copy the kit into a folder named after cd's help text; it now prints its use line, and any other word
  that starts with - stops before a folder is made.

## Left out or not done (said plainly)

- **Measured on a real card four times, and not through the plugin's own client.** Two batches of 10 variations of the finished canal lock (3 jobs each, two cameras, Cycles 600 x 400) took 180 and 158 card seconds (about US$0.05 each at
  the price of the day; an estimate, not a bill), and the one more batch the rule allows, 6 variations around the picks in 2 jobs, took 104. The first two plans estimated 250 s each (too high); the house numbers for the seconds of opening a scene and drawing a picture were then refitted to what was measured, and the same plans now estimate 208 s (real: 180 and 158) and, for the refined batch, 148 s
  (real: 104): always a little above, so an estimate is never too small. Wake-up times were 0.8 to 24.3 s. Whether the scene was really not uploaded again in the third batch was shown with the pretend card only; on the real card the set-up time fell from 31 s to 28 s, too little to call it proof.
  The fourth, the final proof (cracks and chips, made with `--range`, scouted first): the scout here took 38 s and found all 10 measurably different; on the cards all 10 came out measurably different too (the closest pair
  0.76 to 0.78 of 255 and 0.46 to 0.57 percent of pixels, just above the limits), in 178 card seconds (estimate 208), wake-ups 0.8, 19.9 and 23.3 s, 48 s from sending to the last result, 92 s for the whole command.
  Its file is `data/examples/canal-lock-cracks-variations.json`. Two files scouted before it each had one pair too alike and never went to a card. `collect` was proved only with the pretend card.
- **A script hook that needs more than its own file does not travel to a card** (only the hook file is uploaded): the template says so and offers local drawing for tiny scenes.
- **The workflow's card-time rules ran only against canned helpers.**

- **A large place was not built here.** The tests built a one-hut place and a 36 by 26 m yard (41 objects, one road); a smoke test by hand built a 12 m canal lock (94 objects). The wear,
  growth, masks and audit were not tried at hundreds of buildings, and Cycles with the kit was not run on a place that size.
- **The rented-card client was never run against a real endpoint.** The endpoint was switched off while this was made and the
  person's settings were never read. The tests send its jobs to a pretend card that hands each one to the real job taker. The
  `balance` action (a read-only query of the money left) was written from RunPod's documented query and never run.
- **The style guard is provisional.** It is made from the first honest picture and locks in whatever that picture looked like until
  a person accepts it; the preflight says so as a LOOK.
- **Visual quality is judged, not measured.** The plaster has seams and hairline cracks and the road shows ruts, but nobody has
  decided yet whether they look right; fresh checkers and the person's own eyes do that.
