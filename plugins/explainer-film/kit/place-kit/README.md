# The place kit

What this is: everything the plugin knows about making a believable place in Blender, as code you can run, so a model that
is only told "build a place" still gets real normal maps, real displacement, dirt, grime, weathering, damage, weeds and parts
that stand on the ground, and is stopped when it forgets one. You do not need to read this to use it: the skill
`skills/surfaces-wear-and-construction/SKILL.md` sends you here at the right moment, and every command says what to do next.

## A concrete example first

You built a hut of plain boxes in Blender and saved it as `hut.blend`. Two commands:

```
explainer-film-place finish --scene hut.blend --save-as hut-finished.blend
explainer-film-preflight place --place-audit place-audit.json --blend hut-finished.blend
```

The first one gives every object a role (a wall, a roof, a door), puts a real normal map, roughness and colour variation on it,
bevels the edges, bends and chips the shapes, adds nine layers of wear in a fixed order, stands weeds, leaves and litter on the
ground (never on a wheel rut), adds a sun if there is no light, saves the file, opens the saved file again and audits it. It took
about 8 seconds on the slow computer this was made on (full size: 1024 pixel maps). The second one is the gate: it fails, with the
reason in plain words, when anything is missing. On the plain hut the audit says, for example, "role wall.plaster: missing
normal_map, roughness_variation, colour_variation, dirt, grime, weathering ...", and names the plank that floats 6 cm above the
ground. After `finish` it passes.

## The rule behind it (said once)

A model asked for a place builds boxes and flat colours, because that is the cheapest thing that looks like an answer. The kit
makes the full treatment the cheapest thing to do instead of the most expensive to skip: one command per job, settings for each
place, presets, a gate that fails when a treatment is missing, and a way to build in parts with fresh checkers. Nothing in the
kit names a kind of place: a village, a harbour, a mine and a room all use the same code with different settings.

## The commands (`explainer-film-place VERB`)

`--verbs` prints them. Every verb takes `--scene FILE.blend`, `--settings place-settings.json` (a missing one is drafted for you),
`--out FILE.json`, `--json`, `--save-as OUT.blend` (the input is never overwritten without `--overwrite`) and `--quick`.
Exit 0 is a pass (read the LOOK lines), 1 is a fail, 2 is an input that is missing or unusable.

| Verb | What it does |
|---|---|
| `new-settings` | drafts `place-settings.json` from the object names, collections and materials, and lists what it could not classify |
| `roles` | gives every object exactly one role (exit 1 when one is unknown); `--write` stores it on the object; `--list` prints every role id with one line of meaning (no scene needed), and the roles it GUESSED are worth reading, not only the unknown ones |
| `surfaces` | UVs in metres first, then real normal maps made from designed height pictures, roughness and colour variation, bevels with hardened normals, displacement where the role needs it |
| `roads` | grades the ground and cuts two wheel ruts a gauge apart with banks, puddle hollows and (when the settings ask) hoof prints, as real geometry |
| `damage` | damage as shape: boards that bow, chipped corners, leaning posts; no two parts alike |
| `age` | the nine wear layers (dirt, grime, weathering, wetness, cracks and chips, edge wear, moss, rust, rubbish) in their fixed order |
| `grow` | weeds, tufts, ferns, nettles, moss cushions, leaves, sticks, straw and clods as small 3D pieces, with exact keep-out gates |
| `light` | adds a sun, a sky, a fill and lamps for glowing things when the scene has none (a scene with no light draws black) |
| `finish` | everything above in the right order, then save, reopen, audit; safe to run twice |
| `finish-part` | one builder's share (`--owner NAME`): only that owner's objects, masks from that part alone |
| `construction` | the construction check alone: every part carried from the ground up, doorways, spans |
| `normals-test` | proves every normal map points the right way, against its own height and with a test light |
| `audit` | gathers the facts into `place-audit.json`, then judges them |
| `undo` | removes everything the kit added and puts the original materials back |
| `combine`, `fingerprint`, `ownership-diff` | build in parts by different builders at the same time and check who changed what |
| `renderer-for`, `render`, `rent` | which renderer, drawing pictures (here, tiny; or on a rented card), the rented-card client |
| `measure`, `crops` | measure pictures against a style guard; cut 100 percent crops |
| `check-presets` | checks the kit's own data and code (see Tests) |

From Python, inside Blender: `import place_kit as pk` gives one function per job (`pk.read_settings`, `pk.finish_place`,
`pk.age_place`, `pk.begin_part`, `pk.new_part_object`, `pk.seat_on_ground` ...). The data files are in `data/`; a stage file for
building a part is `data/templates/stage_template.py`.

## The settings file (`place-settings.json`)

Everything is optional; an empty file means "a lived-in place, dry, every role from object names". A worked example is
`data/examples/canal-lock-place-settings.json` with `data/examples/canal-lock-ownership.json` (a small canal lock that was really built with this kit). The keys that matter:

- `look`: `kept`, `lived_in` (the default), `neglected`, `derelict`. It sets the amount of every wear layer and of the weeds and litter. `look_by_role` says "roads are neglected, walls lived in" (a role pattern may end in `*`: `"prop.*": "neglected"`).
- `state`: `dry`, `damp`, `wet`. It sets the wetness layer (a dry place has none, and the audit knows that).
- `place_type`: a starting preset (`data/place_types/`: village, town, harbour, farm, garden, mine, interior, `generic`) with its own look, state and allowed skips. `new-settings` prints the look and state it started from, so you can see and change them. `generic` is the default.
- `roles`: rules that say what an object is, by name, collection, material or property. A rule that matches only a material gives that slot its own role (a barrel's wood and its iron bands). `roles --list` prints the role ids.
- `never`: rules for objects that have no surface to give (a measuring helper, a hidden sky dome), each with a reason: `{"role": "never.helper", "match": {"names": ["^Helper"]}, "reason": "a measuring helper hidden in every picture"}`.
- `require_more`: treatments that a whole class must have on top of what the kit already requires, for a place that needs them: `"require_more": {"timber": ["moss_and_algae"], "stone": ["wetness"]}` (the harbour preset does this: wood by water goes green, stone by water stays wet).
- `owners`: for a place built in parts, the path of the ownership file (who owns which objects, collections and materials; what is frozen and who sets it). Example: `"owners": "canal-lock-ownership.json"`.
- `roads`: a polyline, a width, a cart gauge, a rut depth, and optionally `"hoof": true` (hoof prints, for a track that animals walk) or `"centre_grass": true`. When none is written, `finish` drafts one for every object whose role is a road role (its centre line from the object's own shape) and says so; a road drawn as one strip is shaped in place (the strip keeps its outline).
- `footfall`, `keep_clear`: where people walk (nothing grows there) and where nothing may grow or stand.
- `off`: a treatment switched off for some roles, with a reason of at least 15 letters. It is listed in the audit as KNOWN with the reason and is capped: a place that skips most of the pass is not finished.
- `dials`: a layer's own numbers (how high the foot splash reaches, how many cracks). A dial name that is not in `data/dial_table.json` is an error, so a typo cannot hide. **Dials and the state are the same for every role.** To treat one role differently (more moss on the waterside timber), give it its own look with `look_by_role`, or switch a treatment off for it with an `off` entry and a true reason.
- `picture`: the camera and picture height, so marks are sized in picture dots (a crack is never thinner than three dots).

What the kit makes and what it does not: the plants it grows are only the species in `data/species.json` (tuft, clover, nettle, fern, bramble, moss cushion, with leaves, pine needles, sticks, straw and clods as litter). Reeds, seaweed, barnacles and foam are NOT made by `grow`: build them as a few big designed shapes in the part that owns the props. Near water, the wear masks make the ground damp (full at the water's edge, nothing from about 3 m away; measured on a quay) and the water itself is not treated as a solid, but a tide line (a band at the height of the water) is not made by any layer: build it as shape.

## The seventeen treatments

A plain request that says "normals, displacements, dirt, grime, weeds, weathering, damage" is a request for these. Each has its
plain words, the words a person uses for it, the function that makes it, the test that proves it and the check that reads it
(`data/treatments.json`). A role's class decides which are REQUIRED and which WANTED: walls need all of the wear layers, a
bevel and a normal map; iron needs rust; ground needs plants and litter pieces; roads, mud, thatch and rock ground, and earth,
forest floor, gravel, paving and stone walls too, need real displacement.

| Treatment | What you see | Made by |
|---|---|---|
| normal_map | fine relief on every surface, lit correctly from any side | `surfaces` |
| displacement | real relief at the silhouette and in a low light; the mesh is made fine enough to show it | `surfaces` |
| roughness_variation, colour_variation | shine and colour change across a surface and from one object to the next | `surfaces` |
| bevelled_edges | no knife-sharp box edges; clean shading | `surfaces` |
| dirt, grime, weathering, wetness | mud at the foot of a wall, soot under an eave, silvered wood and faded colour, damp and puddles | `age` |
| cracks_and_chips, edge_wear | hairline cracks, chipped corners, rubbed edges | `age` |
| moss_and_algae, rust, rubbish | green growth in damp shade, rust on iron, scraps where litter gathers | `age` |
| plants, litter_pieces | weeds, ferns, nettles, moss cushions, leaves, sticks as real pieces | `grow` |
| shape_damage | bent boards, leaning posts, sag: no two parts alike | `damage` |

How the wear works: each layer is one node group in the material (a recipe with a fixed set of inputs and outputs), wired in a
fixed order so dirt is under the water and the cracks stay dull when wet. A layer reads *masks* about where it is (how low, how
trodden, how sheltered, how damp, how near a wall) that are drawn once from above and stored in three small pictures. A layer's
strength is "Amount" times a number written on each object (`pk_<layer>_amount`); an object with no such number reads 0 in every
renderer, so the audit checks that every object has them. Amount 0 gives exactly the picture without the layer.

## The audit and the gate

`audit` writes `place-audit.json`: FACTS only (which material has which treatment, how deep the ruts really are, which part
floats, how big a door is), measured from the saved file (it records the file's hash, so a changed file makes the audit stale).
`place_audit_check.py` judges the facts with the house numbers (`kit/film-settings.json`, sections `place_...`) and prints
PASS, LOOK, FAIL or KNOWN with a fix. `explainer-film-preflight place` runs the judge, checks the audit is about this file, and
looks at the preview pictures against a style guard. The `plates` stage asks for the same audit when it is given a scene (`--blend`, or the `scene_file` its check file records), so a
place that was never audited cannot reach a paid painting; when no scene is named at all it cannot know, and says so as a LOOK. The order: shots, build the place, `place`, then `plates`.

## Building in parts

Several builders can build a place at the same time. Each writes a stage file (`stage_<owner>.py` with `apply(options)`; the
template is `data/templates/stage_template.py`) that removes what an earlier run made and makes its part again. `combine` runs
the stage files one after another, takes a fingerprint of the whole scene before and after each, and checks every change
against `ownership.json`: nobody may change what another owner made, a shared material or node group, the camera, the lights,
the world or the render settings. `--order both` runs the chain in plain and in reverse order from the same saved start and says
whether the scene came out the same.

The ground is the one part everything else stands on, so `--order both` cannot start with it in the list (a reversed chain would
seat the other parts on a ground that does not exist yet). The recipe, in two steps with the real commands:

```
explainer-film-place combine --scene start.blend --stages stage_ground.py --owners ownership.json --save-as ground-only.blend
explainer-film-place combine --scene ground-only.blend --stages stage_walls_and_steps.py stage_lock_gate.py stage_props.py --owners ownership.json --order both --save-as parts-combined.blend
```

The first makes the ground alone and freezes it into `ground-only.blend` (the ground part is the one that may make the cameras,
lights and world: `frozen.set_by` in the ownership file). The second runs the other stages in plain and in reverse order from that
file and says whether the scene came out the same.

A part that stands on the ground uses `pk.seat_on_ground` (it reads the ground's real height at points inside its footprint); a part
that joins another (a rail tenoned into two posts) must reach into both by a few centimetres: the construction check calls a part
that is sunk up to 4 cm into its carrier "resting" and reports the real overlap in millimetres. A boat afloat or a pile in a river:
a part whose underside is below the water's top and whose top is above it is carried by the water (the hull may be modelled whole,
with its waterline above its keel); a hull that hovers above the water and the mud fails as floating.

## Drawing pictures

`render --job JOB.json` draws the views of a job file with the film owner's renderer rule: Cycles when a lamp that is not the sun
is on, a material glows, or an object has the glow role; EEVEE when nothing is lit. On this kind of computer it draws tiny
previews only; `--where rented` sends the job to a pay-per-second card on your own RunPod account, and `--where auto` does so by itself
(previews too) when a card is set up and the renderer is Cycles. The client reads `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` (and
`RENDER_STORE_FOLDER`, default `/workspace`) from the environment, or from a file named in `RENDER_SETTINGS_FILE` that sits outside
every repository (lines `NAME=VALUE`, or a JSON file with the same names), and never prints, stores or sends them anywhere else. It stops and says so when a job has waited five minutes
in line while workers show idle (the account may be out of money); it never cancels, empties the line or changes the endpoint.
The worker side (`place_kit/render/worker/`) is a small job taker you copy to the card's store once; `copy_libraries.sh` and
`cycles_check.py` are its set-up and its proof. A price shown on the day is not a bill: never promise a cost from seconds alone.

The job file is a small JSON file (the full note is at the top of `place_kit/render/render_job.py`):

```
{ "scene": "FINISHED.blend", "out_folder": "pictures/round1", "views": [
  { "name": "towpath_wide", "camera": "View wide", "width": 1200, "height": 800, "samples": 96 },
  { "name": "lock_gate", "camera": "View lock gate", "kinds": ["final"], "width": 1600, "height": 1067 } ] }
```

A view is drawn as a preview (and with `--finals` also as a final) unless it says `"kinds"`: exactly the pictures to draw for it
(`"preview"`, `"close_up"`, `"final"`). One local picture at one size is therefore `"kinds": ["final"]` with the width and height, and no
preview is wasted. Files are named by view and kind once (`towpath_wide_preview.jpg`; a view already called `closeup` is not named
`closeup_closeup`), each with a `.json` log beside it.

## What was measured and what was only judged

Measured here (the tests run these): the audit fails a flat hut and passes the finished one; every normal map agrees with its own
height and a flipped copy reads wrong; the master at 0 gives exactly the picture without wear; drawing twice gives the same
picture; finishing twice, and the same scene finished twice, give the same scene and the same pictures; the road's ruts, measured
by rays, are about as deep as the settings say and a gauge apart, and no plant stands in a rut or the road's centre strip; the
construction check finds each of its faults on small scenes; a normal map and displacement together do not double the relief
(`DEVIATIONS.md` has the numbers); and finish takes seconds on a hut and about half a minute on a 36 by 26 metre yard.

Only judged (a person's eye decides, and the tests cannot): that the places look good. The wear amounts of each look are first
tries, tuned against pictures of a hut and a yard; the numbers marked invented in `kit/film-settings.json` and in the data files
are first tries too. The style rule (few, big, clean, designed marks; no photographic noise) is enforced by measures, not by taste.

## Not tested (said plainly)

- A large place: only a hut, a 36 by 26 m yard and a 12 m canal lock were built and finished here. The plan masks, the wear and the growth are untested at
  hundreds of buildings, and Cycles was not run with the kit on a place that size.
- The rented-card client was tested against a pretend card (a fake service that hands each job to the real job taker), never
  against a real endpoint: the endpoint was switched off while this was made and the settings were never read.
- `paint_request.py --keep-wetness` (the painter prompt for a place built wet) was tried on the template's words only; no painting was paid for, so how the painter treats the words is not known.
- The `balance` action of the client was written from RunPod's documented query and never run.

## Tests

`python3 kit/calculators/tests/run_all.py` runs them all (set `BLENDER` to run the parts that need Blender; without it they say
so and are skipped). The files for this kit: `test_place_data.py` (data and the checker of the data), `test_place_roles.py`,
`test_place_shapes.py` (recipes, normal maps, roads, grids, pieces), `test_place_audit_check.py` (the judge),
`test_preflight_place.py` (the place stage), `test_place_blender.py` (everything inside Blender), `test_place_combine.py`,
`test_place_render.py`, `test_picture_measures.py`, `test_place_fixes.py` (the faults a first full check found, each with the old behaviour as a control) and `test_place_hook.py` (the prompt reminder in `hooks/`); and for the film's model builder, which the kit's bevel rule and PNG normal maps also reach, `test_model_kit_surfaces.py`. `python3 kit/place-kit/check_presets.py` checks that every number has a
kind and a source, the data agree, every treatment a class requires is made by a real function and proved by a test, no kit code
names a kind of place, no code that runs in Blender imports Pillow, OpenCV or SciPy, and nothing private is written anywhere.

## Where things are

`place_command.py` is the launcher (it finds Blender and runs the verb in it); `blender_run.py` is what runs inside Blender;
`place_kit/` is the package: `commands.py` and `cli.py` (the verbs), `roles.py`, `settings_file.py`, `surfaces/` (heights,
normals, UVs, materials, bevels, displacement, roads, damage), `wear/` (the nine layers, their masks and the chain),
`growth/` (the 3D pieces, the scatter and its keep-out recount), `checks/` (audit, construction, scale, normal-map test, ownership,
fingerprint, combine), `render/` (the renderer rule, the render job, the rented-card client and the worker), `parts.py`,
`undo.py`, `light.py`, `convert.py` (curves, text, metaballs and collection instances are turned into meshes at the start of `finish`, so no drawn object escapes the pass; `undo` brings the originals back). `data/` holds the roles, surfaces, looks, place types, dial table, species, real-world facts, templates and
examples. `SOURCES-AND-LICENCES.md` says where every part came from; `DEVIATIONS.md` says where the build differs from its design and why, and lists the small changes made to the film's older tools
(`model_kit.py`, `textures.py`, `model_lint.py`, `make_check_file.py`, `paint_request.py`, `plan_budget.py`, `explainer-film-setup`).
