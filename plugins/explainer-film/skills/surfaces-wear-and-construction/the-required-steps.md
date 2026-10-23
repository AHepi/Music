# The required steps (in order, with a small canal lock as the example)

What this is: the numbered steps from "build me a place" to a place that passes. Do them in this order, and do not
skip a number. The example is the small canal lock (`worked-examples-garden-and-canal-lock.md`); the files are called
`lock.blend` and `place-settings.json`. Every command is `explainer-film-place VERB`, on the PATH once the plugin
is installed. In a part's own words: a step that is skipped is reported as skipped, never as done.

The order of the film's preflight stages around a place is: `shots` (plan the views), then build the place, then
`place` (this skill's audit), then `plates` (before paying for paintings). `shots` and `place` are different checks.
Passing one does not mean the other was run. Run `shots` twice: once from the brief for the rough camera plan, before
anything is built, and again once `place` passes, when the scene exists and the place facts can be read from it; both
must pass before any plate.

## Step 0. Write down the rules of this place (about 20 minutes)

Before any mesh, write three things. Use the templates in `place-kit/data/templates/` (the workflow's planner does it
for you):
- the **style note** (`style_note.md`): the style rule, the shapes, the edges, the palette, the value range, how much
  detail, what the style does not have;
- the **facts table** (`real_world_facts_template.json`): each size as number, unit, source and confidence;
- **`place-settings.json`**: owners, roles, the road centre lines, where people walk, where nothing may grow, the look.
  `explainer-film-place new-settings --scene lock.blend --place lock --type harbour --out place-settings.json`
  drafts it from your object names, collections and material names and lists what it could not classify (a canal has
  no type of its own, so it takes the nearest, harbour; the look and state it starts from are printed, and the person's words decide).

## Step 1. Plan parts and owners

One part is one piece of the place that one builder shapes: `ground_and_water`, `walls_and_steps`, `lock_gate`,
`props`. One collection each, named `Place: <owner>`. Build the ground first and keep its height fixed (a
road's ruts and banks belong to the ground part), because everything else is seated on it. If the ground changes
later, every part is seated again before the construction check runs (step 4). A road must be PART of the ground
mesh or its own ground object; either way the kit keeps its outline (a curved road stays curved, a trench cut in a
towpath stays a trench) and makes it fine by splitting its faces in place.

The ground part also makes the view cameras, the lights, the world and the render settings, and they are frozen
from then on: write `"frozen": {..., "set_by": "<the ground owner>"}` in `ownership.json`, or the ground part's own
camera is reported as a violation.

Combine the parts in two steps, because every other part is seated on the ground (a combine that lists the ground
with the others fails the order test, since the ground cannot come last):
`explainer-film-place combine --scene start.blend --stages stage_ground.py --owners ownership.json --save-as ground-frozen.blend`
then
`explainer-film-place combine --scene ground-frozen.blend --stages stage_walls_and_steps.py stage_lock_gate.py stage_props.py --owners ownership.json --order both --save-as combined.blend`
The second run does the plain order, the reverse order and the idempotent test, each from the frozen ground.

## Step 2. Shape the parts

Use the part helpers (inside Blender, `import place_kit as pk`): `pk.begin_part(owner)`,
`pk.new_part_object(owner, role, name, mesh)`, `pk.seat_on_ground(obj)`, `pk.ground_height_at(x, y)`,
`pk.is_keep_clear(x, y)`. Every object gets an owner and a role as it is made (the ids: `explainer-film-place roles --list`).
A rail tenoned about 5 cm into each of two posts is framed in and counts as carried, even in a role that may not hang;
a board bedded up to 4 cm into its support rests on it; a boat afloat is carried by the water if its underside is below
the water plane and its top above it. A step needs the role `stone.step`; its rise is measured top to top (17 cm for
a stack of 17 cm slabs, and for a flight of solid blocks each 17 cm higher than the one before).

Build from the ground up, with real sizes from the facts table, and give the shape its own character as geometry:
- every plank on a support, every support on the ground (`construction-and-scale.md`);
- bevel every edge a hand could touch (walls 8 to 15 mm, timber 6 to 12 mm: `place-kit/data/surfaces.json` has the sizes);
- **no two siblings alike**: planks of different widths (9 to 17 cm) and thickness, a bow, a worn or chipped corner on
  some, a replaced board here and there; roof tiles or shingles of different tones, a few slipped, chipped or missing;
  posts a little out of plumb; a roof that sags between its rafters. This is what read at film size in the garden
  (the shader wear alone barely did), and it is damage and age as SHAPE (the treatment `shape_damage`). Make it as you
  shape the part, or let `explainer-film-place damage --amount 0.5` bend, chip and vary the parts afterwards (`finish` runs
  it); the audit lists groups of siblings that are exact copies.

## Step 3. Give every object a role

Tag every object WHEN YOU MAKE IT (`pk.new_part_object(owner, role, name, mesh)` or the property `place_role`). The
ids and what they mean: `explainer-film-place roles --list`. The kit also guesses a role from a name, and a guess can
be wrong (measured on 70 plain names: "Waterwheel" read as a cart wheel, "Reed bed" as a thatch roof, "Quay wall" as
plaster; the hints were fixed for those, but others will exist), so read the roles it GUESSED as well as the unknown ones.
`explainer-film-place roles --scene lock.blend --settings place-settings.json` lists the role of every visible
object and the ones it could not classify. For each unknown one, add a match rule in the settings (a name pattern, a
collection, a material name) or set the property `place_role` on the object. An object may stay roleless only when a
`never` rule covers it (sky, glow, lights, helpers). After `finish`, an object nothing matched becomes `prop.generic`
(a grey stone prop) with a LOOK line; the audit warns on each, and FAILS when more than 15 percent of the objects are
fallbacks (`place_audit.fallback_role_share_fail`). Read each one and tag it properly. Steps are `stone.step`, not
`floor.stone`; the indoor-floor skip of the place types does not cover `floor.stone`, so a patio or a step outdoors keeps
its moss, weathering, wetness, plants and litter.
A joined mesh or an imported prop with several materials gets one role for each material (the barrel's wood and its
iron bands): match by material name in the settings.

## Step 4. Run the pass

Whole place, in one go (it needs `--save-as`; without it the command stops at once, before doing anything):
`explainer-film-place finish --scene lock.blend --settings place-settings.json --state damp --save-as lock-finished.blend`
(with no settings file it drafts one, using `--type TYPE --place NAME` if you give them; add `--facts FACTS.json` when the place has its own facts table)
The look of each role comes from the settings (`look` and `look_by_role`: for example `neglected` for a towpath and
`lived_in` for the rest); `--look ID` changes the default look. It runs, in this order: convert (a bevelled curve, a text sign or an instanced collection becomes meshes; the originals are kept, hidden), roles (an object that no
rule matches gets a fallback role and a LOOK line; a dirt-road object that the settings name no road for gets a road drafted from its own shape and written into the settings), the ground (roads, then
everything is seated on it again; every object that moves more than 3 cm is named with the distance), surfaces (UVs, normal maps, displacement, bevels), damage as shape, the plan masks, the
wear layers, growth, light, the picture size; then it saves the file, reopens the saved file and audits it (the audit holds
the construction check). Run twice it gives the same counts (it is safe to repeat). It never overwrites `lock.blend`
unless you say `--overwrite`.

When parts are built by different owners: each owner runs `finish-part --owner NAME --save-as part.blend` on its own
objects (it is always a quick trial, the wear masks come from that part alone, which the audit records as `masks_from: part_only`,
and its audit accepts that as a LOOK, so a clean part exits 0), and the integrator combines the parts (`combine`, in plain
and in reverse order, as in step 1) and runs `finish` once on the whole.

`--quick` is for trials on a slow computer. A quick pass is not a final: the audit records it.

## Step 5. Read the audit and fix by category

The audit prints one line for each finding: FAIL, LOOK or PASS. Fix by what the line names:

| The line says | Fix |
|---|---|
| a treatment is missing (a name from the seventeen) | run the verb its fix text names (`surfaces`, `age`, `grow`); if the place really cannot have it, write an `off` entry with a reason |
| a layer amount is 0 or missing | the object lacks its `pk_<layer>_amount` property, or the look set it to 0: run `age` again, or write an `off` entry |
| an object has no role | step 3 |
| a part is floating, short or hung | move it, or add the support under it (step 2) |
| scale: out of range | change the size, or correct the facts table with a source |
| keep-out: a plant on a wheel track, a crown or in a puddle | run `grow` again after `roads`; the order is fixed |
| stale audit | the scene was saved after the audit: run `audit` again |
| quick output | run `finish` without `--quick` |
| an object has no material with a surface (named) | `finish` gives it one; nothing in the scene may be left without a material |
| things drawn that are not meshes (named) | `finish` turns curves, text, metaballs and instanced collections into meshes (undo shows the originals again) |
| ground: a dirt-road object with no road entry, or an outline that grew | the settings need a `roads` entry for the road (`new-settings` drafts one from its shape); a grown outline means the road was reshaped into a box: `undo` and give the road its own fine mesh |
| plain boxes (a share of the objects) | `surfaces` bevels every hard-edged role; objects of a role it does not bevel (ground, water, glass, plants, trees) need a chamfer you make yourself |
| light: only the world lights the scene | `light` adds a sun (a world colour alone is no key light) |

Read the WHOLE output of `finish`, including any list of what it skipped or could not do. A skipped item is reported, never
ignored. The audit also holds budgets (house numbers, section `place_audit`): triangles in all (`place_audit.triangles_total_max`)
and for each builder (`place_audit.triangles_per_builder_max`), scattered pieces (`place_audit.scatter_pieces_max`), the draw time
of a final (`place_audit.draw_seconds_final_max`) and the card's memory (`place_audit.card_memory_gigabytes_max`). Over a budget:
instance small things (pegs, leaves, tufts) instead of copying them, and cut detail nobody can see.

## Step 6. Look at the detail

`explainer-film-place normals-test --scene lock-finished.blend` draws a flat test plane for every normal map under a
low light from two sides and says whether each map points the right way (it also tests a flipped copy, which must
fail). `explainer-film-place construction --scene lock-finished.blend --out construction.json` lists every part's
supports, gaps, spans and the doorways without floors. Read both.

## Step 7. Light the place

A scene with no sun, no sky and no lamps draws black or flat, and the renderer rule depends on which lamps are lit,
so decide the light before you draw:
- a sun and a sky for daylight; a softer fill from the opposite side so shadows are not black;
- a real lamp inside every lit window or lantern (a light inside its own glow box is blocked in Cycles), with the glow
  box itself hidden from the lamp's own rays;
- a value study of the first preview: nothing blown or crushed (judged: under 0.5 percent of dots clipped at either end).
  Read the picture's actual numbers, not how it looks.
`explainer-film-place light --scene lock-finished.blend --save-as lock-lit.blend` adds a sun, a sky, a fill and a lamp
for every glowing thing when the scene has none (`--sun-only` adds just a sun); `finish` runs it too. Its numbers are starting
values, not tuned: look at the first preview and adjust. If the scene has its own lights, do these by hand.

## Step 7b. Plan every change, then make them in one sweep

Before you try anything on the finished place, write down EVERY change you mean to make (the moss, the wall damage, the gate's lean, the towpath ruts, the light). Make them all in one sweep, save the scene (`lock-finished.blend`), and only then look. Build the scene once and keep that file: every test starts from it. A change made one at a time, with a look after each, costs one look and one card wake-up each (the garden spent US$10.89 of card time this way; the finished pictures cost about 5 cents). The rule and the tools are in `batched-rounds-and-card-time.md`: for each change to a thing, about 10 measurably different versions in ONE batch (`explainer-film-place variations`), one sheet, pick or combine, at most one more batch.

## Step 8. Draw previews, then make the style guard

`explainer-film-place renderer-for --scene lock-finished.blend` prints CYCLES or EEVEE and the reasons.
`explainer-film-place render --job JOB.json` draws previews with that rule (a rented card when set up:
`rendering-on-rented-cards.md`). Small and quick until the end; the full-size pictures (`--finals`) are drawn once, at the very end, from the last audited file; every card job goes into the card-time ledger and is limited by your allowance. Draw the first preview under three lights (flat, side, and wet if the place is wet):
a mark that vanishes under one of them is not carrying the place. Then
`explainer-film-place measure PICTURE.jpg --make-guard --out style-guard.json` makes the guard from the first honest
picture. A guard made from the first picture is PROVISIONAL: it locks in whatever that picture looked like, so a
bland first picture makes a bland guard. Compare it with the style note's numbers, and with a reference picture if
there is one (`style-rule-and-measures.md`).

## Step 9. Fresh checkers

A helper who did not build the place recomputes the builders' claims and judges the pictures (`fresh-checkers.md`).
The workflow `build-a-place` does steps 5 to 9 for you, with a blind reader and one fix round.

## Step 10. The place stage, then go on

`explainer-film-place audit --scene lock-finished.blend --settings place-settings.json --out place-audit.json`
then `explainer-film-preflight place --place-audit place-audit.json --blend lock-finished.blend`
(add `--place-pictures FOLDER --style-guard style-guard.json` once there are pictures, and `--fresh-check FILE.json`
once a checker has looked). It must PASS. Without `--blend` it cannot tell whether the audit is stale and says so.
Only then go on to the film's `plates` stage and the shots.

## Step 11. Report in plain words

What you did; what the audit measured (numbers); what was measured and what only judged; what you skipped and why
(`off` entries, accepted findings, quick runs); what you did not test; every failure and what you did about it.

## The live-Blender route (a Blender that is already open, or the Blender MCP)

The command line writes a NEW file; an open scene does not change. Two ways:
1. Save the open scene to `lock.blend`, run the commands above, then open `lock-finished.blend` and carry on there.
2. In the open Blender: add the kit folder to `sys.path`, `import place_kit as pk`,
   `settings = pk.read_settings('place-settings.json')`, `pk.finish_place(settings)`. Then save the scene to a file
   and run `audit` (and the preflight) on THAT file. The audit reads the saved file; an unsaved scene is refused.
Do not save over the file after the audit. If you must, run the audit again.

## The shortcuts that fail (real cases)

- **Flat boxes pass the model lint.** A hut of three plain-colour boxes got PASS from `model_lint.py`. The place audit
  fails it by treatment name; `model_lint.py --surfaces` warns for .glb files.
- **Bump only.** It changes the shading and nothing else, and at its default Distance (0.001) it is nearly flat.
- **A normal map with the green channel flipped, or in sRGB colour space.** The light then comes from the wrong side
  (a flipped map reads as dents where bumps should be). `normals-test` catches it.
- **No UVs.** A tangent-space normal map needs a UV layer; an object without one shows nothing.
- **Displacement on a flat plane, or with the material left on Bump Only.** Nothing moves. Both need a dense or
  adaptive mesh and the material's displacement method changed.
- **A layer with amount 0, or an object with no `pk_<layer>_amount`.** An Attribute node on an object that lacks the
  property reads 0 in Blender (tested in EEVEE and Cycles), so the layer is silently off on that object.
- **Weeds on the wheel tracks, or in puddles.** The gates are exact zeros; the audit counts roots in the keep-out places.
- **A stale audit after edits.** The audit names the scene's hash; a changed file fails it.
- **Photographic noise instead of a few big designed marks.** See `style-rule-and-measures.md`.
- **Wrong sizes.** A 1 m door passes every other check; only the scale check catches it.
- **One small change, then a look, then the next.** Twenty-five looks at one tree cost real money and tell you little: ten versions that are far apart, in one batch on one sheet, tell you more. `variations` drops versions that are too close before drawing and flags pictures that came out the same after.
- **Rebuilding the scene for every test, or drawing every test at full size.** Save the finished scene once; a batch starts from it, at 600 x 400.

## When a step fails

Read the first FAIL, fix that, run the step again. Do not run the next step on top of a failure. If a tool crashes,
say so plainly and what you did instead; never write a report that says it passed. If a fix needs a number the kit
does not have, write the number into the facts table with its source and confidence.
