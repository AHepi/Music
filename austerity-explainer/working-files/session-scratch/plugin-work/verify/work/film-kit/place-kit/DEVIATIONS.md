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

## Left out or not done (said plainly)

- **A real village was not built here.** The tests built a one-hut place and a 36 by 26 m yard (41 objects, one lane). The wear,
  growth, masks and audit were not tried at hundreds of buildings, and Cycles with the kit was not run on a place that size.
- **The rented-card client was never run against a real endpoint.** The endpoint was switched off while this was made and the
  person's settings were never read. The tests send its jobs to a pretend card that hands each one to the real job taker. The
  `balance` action (a read-only query of the money left) was written from RunPod's documented query and never run.
- **The style guard is provisional.** It is made from the first honest picture and locks in whatever that picture looked like until
  a person accepts it; the preflight says so as a LOOK.
- **Visual quality is judged, not measured.** The plaster has seams and hairline cracks and the lane shows ruts, but nobody has
  decided yet whether they look right; fresh checkers and the person's own eyes do that.
