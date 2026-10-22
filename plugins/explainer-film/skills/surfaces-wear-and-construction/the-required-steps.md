# The required steps (in order, with the village as the example)

What this is: the numbered steps from "build me a place" to a place that passes. Do them in this order, and do not
skip a number. The example is the village in the forest (`a-forest-village-example.md`); the files are called
`village.blend` and `place-settings.json`. Every command is `explainer-film-place VERB`, on the PATH once the plugin
is installed. In a part's own words: a step that is skipped is reported as skipped, never as done.

The order of the film's preflight stages around a place is: `shots` (plan the views), then build the place, then
`place` (this skill's audit), then `plates` (before paying for paintings). `shots` and `place` are different checks.
Passing one does not mean the other was run.

## Step 0. Write down the rules of this place (about 20 minutes)

Before any mesh, write three things. Use the templates in `place-kit/data/templates/` (the workflow's planner does it
for you):
- the **style note** (`style_note.md`): the style rule, the shapes, the edges, the palette, the value range, how much
  detail, what the style does not have;
- the **facts table** (`real_world_facts_template.json`): each size as number, unit, source and confidence;
- **`place-settings.json`**: owners, roles, the lane centre lines, where people walk, where nothing may grow, the look.
  `explainer-film-place new-settings --scene village.blend --place village --type village --out place-settings.json`
  drafts it from your object names, collections and material names and lists what it could not classify.

## Step 1. Plan parts and owners

One part is one piece of the place that one builder shapes: `roads_and_ground`, `cottages`, `stable`, `props`,
`forest_edge`. One collection each, named `Place: <owner>`. Build the ground first and keep its height fixed (the
lane's ruts and banks belong to the ground part), because everything else is seated on it. If the ground changes
later, every part is seated again before the construction check runs (step 4).

## Step 2. Shape the parts

Use the part helpers (inside Blender, `import place_kit as pk`): `pk.begin_part(owner)`,
`pk.new_part_object(owner, role, name, mesh)`, `pk.seat_on_ground(obj)`, `pk.ground_height_at(x, y)`,
`pk.is_keep_clear(x, y)`. Every object gets an owner and a role as it is made.

Build from the ground up, with real sizes from the facts table, and give the shape its own character as geometry:
- every plank on a support, every support on the ground (`construction-and-scale.md`);
- bevel every edge a hand could touch (walls 8 to 15 mm, timber 6 to 12 mm: `place-kit/data/surfaces.json` has the sizes);
- **no two siblings alike**: planks of different widths (9 to 17 cm) and thickness, a bow, a worn or chipped corner on
  some, a replaced board here and there; roof tiles or shingles of different tones, a few slipped, chipped or missing;
  posts a little out of plumb; a thatch roof that sags between rafters. This is what read at film size in the garden
  (the shader wear alone barely did), and it is damage and age as SHAPE.

## Step 3. Give every object a role

`explainer-film-place roles --scene village.blend --settings place-settings.json` lists the role of every visible
object and the ones it could not classify. For each unknown one, add a match rule in the settings (a name pattern, a
collection, a material name) or set the property `place_role` on the object. An object may stay roleless only when a
`never` rule covers it (sky, glow, lights, helpers). A roleless object fails the audit. If `finish` ever gives an
object a fallback role, it prints LOOK; read each one and tag it properly.
A joined mesh or an imported prop with several materials gets one role for each material (the barrel's wood and its
iron bands): match by material name in the settings.

## Step 4. Run the pass

Whole place, in one go:
`explainer-film-place finish --scene village.blend --settings place-settings.json --state damp --save-as village-finished.blend`
The look of each role comes from the settings (`look` and `look_by_role`: in the village, `neglected` for the lanes and
`lived_in` for the rest); `--look ID` changes the default look. It runs, in this order: roles, roads, surfaces (UVs, normal maps, displacement, bevels), wear layers, growth, picture
size, construction check, audit. Run twice it gives the same counts (it is safe to repeat). It never overwrites
`village.blend` unless you say `--overwrite`.

When parts are built by different owners: each owner runs `finish-part --owner NAME --save-as part.blend` on its own
objects (the wear masks come from that part alone, which the audit records as `masks_from: part_only`), and the
integrator combines the parts (`combine`, in plain and in reverse order) and runs `finish` once on the whole.

`--quick` is for trials on a slow computer. A quick pass is not a final: the audit records it.

## Step 5. Read the audit and fix by category

The audit prints one line for each finding: FAIL, LOOK or PASS. Fix by what the line names:

| The line says | Fix |
|---|---|
| a treatment is missing (a name from the sixteen) | run the verb its fix text names (`surfaces`, `age`, `grow`); if the place really cannot have it, write an `off` entry with a reason |
| a layer amount is 0 or missing | the object lacks its `pk_<layer>_amount` property, or the look set it to 0: run `age` again, or write an `off` entry |
| an object has no role | step 3 |
| a part is floating, short or hung | move it, or add the support under it (step 2) |
| scale: out of range | change the size, or correct the facts table with a source |
| keep-out: a plant on a wheel track, a crown or in a puddle | run `grow` again after `roads`; the order is fixed |
| stale audit | the scene was saved after the audit: run `audit` again |
| quick output | run `finish` without `--quick` |

Read the WHOLE output of `finish`, including any list of what it skipped or could not do. A skipped item is reported, never
ignored. The audit also holds budgets (house numbers, section `place_audit`): triangles in all (`place_audit.triangles_total_max`)
and for each builder (`place_audit.triangles_per_builder_max`), scattered pieces (`place_audit.scatter_pieces_max`), the draw time
of a final (`place_audit.draw_seconds_final_max`) and the card's memory (`place_audit.card_memory_gigabytes_max`). Over a budget:
instance small things (pegs, leaves, tufts) instead of copying them, and cut detail nobody can see.

## Step 6. Look at the detail

`explainer-film-place normals-test --scene village-finished.blend` draws a flat test plane for every normal map under a
low light from two sides and says whether each map points the right way (it also tests a flipped copy, which must
fail). `explainer-film-place construction --scene village-finished.blend --out construction.json` lists every part's
supports, gaps, spans and the doorways without floors. Read both.

## Step 7. Light the place

A scene with no sun, no sky and no lamps draws black or flat, and the renderer rule depends on which lamps are lit,
so decide the light before you draw:
- a sun and a sky for daylight; a softer fill from the opposite side so shadows are not black;
- a real lamp inside every lit window or lantern (a light inside its own glow box is blocked in Cycles), with the glow
  box itself hidden from the lamp's own rays;
- a value study of the first preview: nothing blown or crushed (judged: under 0.5 percent of dots clipped at either end).
  Read the picture's actual numbers, not how it looks.
If the kit has a `light` verb (`explainer-film-place --verbs`), use it and read its audit lines; otherwise do these by hand.

## Step 8. Draw previews, then make the style guard

`explainer-film-place renderer-for --scene village-finished.blend` prints CYCLES or EEVEE and the reasons.
`explainer-film-place render --job JOB.json` draws previews with that rule (a rented card when set up:
`rendering-on-rented-cards.md`). Draw the first preview under three lights (flat, side, and wet if the place is wet):
a mark that vanishes under one of them is not carrying the place. Then
`explainer-film-place measure PICTURE.jpg --make-guard --out style-guard.json` makes the guard from the first honest
picture. A guard made from the first picture is PROVISIONAL: it locks in whatever that picture looked like, so a
bland first picture makes a bland guard. Compare it with the style note's numbers, and with a reference picture if
there is one (`style-rule-and-measures.md`).

## Step 9. Fresh checkers

A helper who did not build the place recomputes the builders' claims and judges the pictures (`fresh-checkers.md`).
The workflow `build-a-place` does steps 5 to 9 for you, with a blind reader and one fix round.

## Step 10. The place stage, then go on

`explainer-film-place audit --scene village-finished.blend --settings place-settings.json --out place-audit.json`
then `explainer-film-preflight place --place-audit place-audit.json --blend village-finished.blend`
(add `--place-pictures FOLDER --style-guard style-guard.json` once there are pictures, and `--fresh-check FILE.json`
once a checker has looked). It must PASS. Without `--blend` it cannot tell whether the audit is stale and says so.
Only then go on to the film's `plates` stage and the shots.

## Step 11. Report in plain words

What you did; what the audit measured (numbers); what was measured and what only judged; what you skipped and why
(`off` entries, accepted findings, quick runs); what you did not test; every failure and what you did about it.

## The live-Blender route (a Blender that is already open, or the Blender MCP)

The command line writes a NEW file; an open scene does not change. Two ways:
1. Save the open scene to `village.blend`, run the commands above, then open `village-finished.blend` and carry on there.
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

## When a step fails

Read the first FAIL, fix that, run the step again. Do not run the next step on top of a failure. If a tool crashes,
say so plainly and what you did instead; never write a report that says it passed. If a fix needs a number the kit
does not have, write the number into the facts table with its source and confidence.
