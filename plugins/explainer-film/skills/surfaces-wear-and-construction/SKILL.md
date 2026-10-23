---
name: surfaces-wear-and-construction
description: The finishing pass that every place, set or prop built in Blender must go through, whatever the request says. It gives real normal maps and displacement, roughness and colour variation, dirt, grime, stains, weathering, wetness, moss, weeds, rust, cracks, chips, edge wear, damage and rubbish, believable construction (every plank on a support, every support on the ground, nothing floating), real-world sizes, and the place's art-style rule. One command does it (explainer-film-place finish) and an audit proves it (preflight stage place). Use whenever someone asks to build, model, make or improve a village, town, harbour, mine, farm, garden, interior, street, building, house, barn, bridge, road, level, set or props in Blender or in 3D, even if they never mention surfaces, textures, wear or realism, and before drawing, rendering or painting any such place. It also says how to try versions cheaply (one sweep of changes, about 10 measurably different versions in one batch on the rented cards, one labelled sheet) and gives every helper a card-time allowance.
when_to_use: Any request to make a place, set, building or props in Blender, and before any picture of one is drawn.
---

# Surfaces, wear and construction (the finishing pass for every place built in Blender)

> **REQUIRED for every place, set or prop you build in Blender** (also when the request never mentions surfaces, wear or realism). Do it without being asked. In your report say plainly what the pass did, what the audit measured and what you skipped.
> 1. Build it so every part is carried (planks on supports, supports on the ground, nothing floating; a rail tenoned into two posts counts as carried) and at real size, and give every object its role AS YOU MAKE IT (`pk.new_part_object(owner, role, name, mesh)`, or the object property `place_role`). The role ids are listed by `explainer-film-place roles --list`. Never trust a role the kit only guessed from a name.
> 2. Run the surface-and-wear pass: `explainer-film-place finish --scene SCENE.blend --settings place-settings.json --save-as FINISHED.blend` (it needs `--save-as`; it drafts `place-settings.json` when there is none, with a road for every dirt-road object). To read and improve a draft first: `explainer-film-place new-settings --scene SCENE.blend --place NAME --type TYPE --out place-settings.json`, where TYPE is the nearest of village, town, harbour, mine, farm, garden, interior or generic. It turns curves, text and instanced props into meshes, then adds real normal maps and displacement, roughness and colour variation, dirt, grime, weathering, wetness, cracks, chips, edge wear, moss, rust, weeds, rubbish and damage as shape.
> 3. Run `explainer-film-place audit --scene FINISHED.blend --settings place-settings.json --out place-audit.json`, then `explainer-film-preflight place --place-audit place-audit.json --blend FINISHED.blend --reports REPORTS_FOLDER`. It must PASS before you draw, render or paint anything. Do not save the scene again after the audit; if you do, audit again.
> 4. Try things in batches, inside a card-time allowance: make every change you plan in ONE sweep, then look once. Build the scene once and save it. For each change to a thing (a tree, a wall, moss) do not try one small change at a time: write about 10 versions whose settings are far apart and draw them in ONE batch (`explainer-film-place variations run FILE.json --where rented --helper YOUR-NAME --role builder`: it drops near-duplicates, spreads the versions over up to 3 rented cards, measures every picture and makes ONE labelled sheet). Look at the sheet, pick or combine, at most ONE more batch. Small quick pictures (600 x 400) until the end; full-size pictures once, at the very end. Every card job is written in a ledger and each helper has an allowance (builder 10 minutes, fixer 5): the tool refuses past it. Report the card seconds you used. Read `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/batched-rounds-and-card-time.md` first.
> Details, every command and the live-Blender route: `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/SKILL.md`.

What this is: a place built from plain boxes with flat colours is not finished, even when it looks tidy and passes
the model lint. The plugin's own model kit once made a hut of three plain-colour boxes, and the lint printed PASS.
This skill is the pass that gives a place real surfaces, wear and sensible construction, and the check that proves it.
It works for any place: a village, a town, a harbour, a mine, a farm, a garden, an interior.

**A concrete example.** A small canal lock side (a brick wall with stone coping, a flight of stone steps, a gravel
towpath, a timber gate and five props) was built by a helper who had never seen this plugin and followed only its steps.
The brief said nothing about surfaces. The finishing pass gave all 94 objects UVs and 1024 px normal maps, bevelled 33
of them, bent or chipped 70 by the damage step, put nine wear layers into 15 materials, and grew 66 plant pieces and
101 litter pieces, none on the wheel track or in a puddle (measured). The construction check proved 88 of 88 parts
carried from the ground up. The audit failed three times for real faults before it passed, and it lists, material by
material, which treatments are there. The whole walk-through, and the Japanese garden that the construction rules come
from, are in `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/worked-examples-garden-and-canal-lock.md`.
The tests prove the gates work; fresh checkers and the person's own eyes judge the look.

## The words (one word for each thing; every file here uses these)

- **role**: what an object is (`wall.brick`, `ground.dirt_road`, `stone.step`). Every visible mesh gets exactly one. Give it as the object is made (`pk.new_part_object(owner, role, name, mesh)` does it, or the
  object property `place_role`). The ids and what each is for: `explainer-film-place roles --list` (every role, one plain line each; the data is `kit/place-kit/data/roles.json`). The kit also GUESSES a role from an
  object's name, but a guess can be wrong (a "Waterwheel" used to read as a cart wheel): read the roles it guessed, not only the ones it could not.
- **surface**: a recipe that makes a material (height picture, normal strength, displacement depth, roughness range,
  colours, tile size): `dirt_road`, `roof_tile_clay`, `timber_weathered`.
- **layer**: one wear effect put on a material: dirt, grime, weathering, wetness, cracks_and_chips, edge_wear,
  moss_and_algae, rust, rubbish. 3D plants and litter are scattered as separate pieces.
- **treatment**: a thing the audit looks for. There are seventeen: normal_map, displacement, roughness_variation,
  colour_variation, bevelled_edges, dirt, grime, weathering, wetness, cracks_and_chips, edge_wear, moss_and_algae,
  rust, rubbish, plants, litter_pieces, shape_damage (bent boards, chipped corners, no two parts alike). Each role says which are REQUIRED (missing = FAIL) and which are WANTED (LOOK).
- **look**: a mood preset (kept, lived_in, neglected, derelict). **state**: dry, damp or wet.
- **owner** and **part**: one builder is responsible for one piece of the place. **audit**: `place-audit.json`, the
  facts table of the scene (Blender writes the facts, plain Python judges them). **fresh checker**: a helper who did
  not build the thing and recomputes its claims.

## Choose the look and state from the person's words

| The words | look |
|---|---|
| kept, tidy, clean, swept, new, cared for | `kept` |
| (nothing said), lived in, working, ordinary | `lived_in` (the default) |
| unkempt, untidy, overgrown, muddy, run down, neglected, forgotten | `neglected` |
| ruined, derelict, collapsed, ancient, abandoned for years | `derelict` |

Wet, rainy, after rain, puddles: state `wet`. Damp, misty, drizzle, dew, shaded ground under trees: `damp`.
Otherwise `dry`. Different roles may have different looks (`look_by_role` in the settings): for example `neglected`
for a towpath and `lived_in` for the walls beside it.

**A place type is only a starting point.** `new-settings --type harbour` writes look `neglected` and state `wet` (a harbour preset's own starting values); `generic` writes `lived_in` and `dry`. The types are
village, town, harbour, mine, farm, garden, interior and generic; a canal or a mill has no preset, so take the nearest (harbour for a canal) and then change the look and the state in `place-settings.json` to what the
person's words say. `new-settings` prints the look and state it started from, so you can see them. The state and the dials are the SAME for every role: to change one role, use `look_by_role`, or an `off` entry with a true
reason (a dial such as the wall-foot splash is not per role).

A request with no word "Blender" still counts when you will use Blender to do it. Treat "village", "town",
"set", "level", "scene", "props", "in 3D" and a named kind of place the same way.

## The commands (one door: `explainer-film-place VERB`)

The verbs that work on a scene take `--scene FILE.blend`, `--settings place-settings.json`, `--out FILE`, `--json`,
`--report FILE`, `--kit DIR`, `--blender PATH`, `--quick`, `--owner NAME` and `--save-as FILE.blend`, and every verb prints
lines that start FAIL, LOOK or PASS. Exit 0 = pass (read the LOOK lines), 1 = fail, 2 = an input is missing (the sentence names the
file and the tool that makes it). `explainer-film-place --verbs` lists the verbs; `VERB --help` lists the options.

| Job | Verb and its main options |
|---|---|
| Draft the settings from names and collections (also a road for each dirt-road object, from its shape) | `new-settings --place NAME --type TYPE --out place-settings.json` |
| One role per object; the list of role ids | `roles --write` (needs `--save-as`); `roles --list` (no scene needed) |
| UVs, normal maps, roughness and colour variation, bevels, displacement | `surfaces --map-size PIXELS --maps-folder DIR` |
| Shaped roads: wheel ruts, banks, optional hoof prints, grass crown, puddle hollows | `roads` |
| Damage as shape: bent boards, chipped corners, leaning posts, sag, no two parts alike | `damage --amount X` |
| Wear layers in their fixed order | `age --look ID --state dry\|damp\|wet --master X --layers a,b --layers-off a,b --mask-cell-metres X` |
| 3D plants, moss cushions, litter | `grow --density X` |
| A sun, sky, fill and lamps for glowing things, when the scene has none (no light draws black) | `light --sun-only` |
| The whole pass, then the audit | `finish --save-as OUT.blend --look ID --state S --map-size P --type TYPE --place NAME --facts FACTS.json` (it stops at once if there is no `--save-as`; `--type`, `--place` matter only when it drafts the settings) |
| A part builder's share of the pass (always a quick trial; its audit accepts that) | `finish-part --owner NAME --save-as OUT.blend --out part-audit.json` |
| Is everything carried, in reach and the right size? | `construction --out construction.json` |
| Do the normal maps point the right way? | `normals-test --size 96 --samples 24 --out normals.json` |
| The facts table and its verdict | `audit --out place-audit.json --no-judge` |
| Take back everything the kit added | `undo --save-as OUT.blend` |
| Combine parts built by different owners | `combine --stages stage_a.py stage_b.py --order plain\|reverse --owners ownership.json --save-as OUT.blend --out combine-report.json` |
| Did a stage touch what is not its own? | `fingerprint --out fp.json`, then `ownership-diff --start FP1.json --end FP2.json --owners ownership.json --out diff.json` |
| Which renderer, and why | `renderer-for` |
| Draw the pictures with that rule (the job file's shape is in `rendering-on-rented-cards.md`) | `render --job JOB.json --where rented\|local\|auto --engine auto\|cycles\|eevee --finals` |
| The rented graphics card | `rent status`, `rent upload`, `rent run`, `rent job`, `rent wait`, `rent download`, `rent balance` |
| About 10 measurably different versions of ONE change, drawn small on up to 3 cards at once, on ONE labelled sheet (the batch rule: `batched-rounds-and-card-time.md`) | `variations make`, `variations plan` (free), `variations run FILE.json --where rented --helper NAME --role builder`, `variations refine RESULT.json --pick NAME`, `variations sheet`, `variations keys` |
| The card-time ledger and each helper's allowance | `card-time show`, `card-time check --estimate-seconds N`, `card-time add`, `card-time start --team-minutes N` |
| Measure pictures against the style (one guard file can hold one guard per view) | `measure PICTURE... --guard G --make-guard --view NAME --previous PICTURE`, `crops --picture P --boxes x,y,w,h --out-folder DIR` |
| Are the data files consistent and private? | `check-presets` |

`--quick` makes trial sizes (256 px maps, 0.5 m mask cells) for a fast look on a slow computer. A quick
result is for trying things; the audit records that it was quick and the place stage does not accept it for a final.

## Stop lines

1. You may not draw, render, paint or call the place built until `explainer-film-preflight place` passes.
2. Never lower a requirement to make it pass. The only two allowed ways to skip a treatment are an `off` entry with a
   reason in `place-settings.json`, and a signed accepted entry (who, date) in the preflight plan. Both are reported as
   KNOWN in the report. An amount of 0 with no `off` entry fails.
3. The audit is a fact about one saved file. Run `audit` last, on the exact file you will draw, and do not save
   after it. A changed file makes the audit stale and the preflight says so.
4. If a squint test or a picture measure misses, report it plainly with the region that loses most. Never remove
   character to chase a number: the person decides.
5. Tell the person what you did: what the pass did, what the audit measured, what you skipped, what you did not test,
   every failure. Measured and judged are different words; use both correctly.
6. Card time is limited. Make every change in one sweep and look once; try a change as about 10 measurably different versions in ONE batch
   (`variations`), at most one more batch; small quick pictures until the end, full-size pictures once at the very end; stay inside your allowance and
   report the card seconds you used. A tool that refuses because of the allowance is not worked around: write the reason it asks for, or tell the person.

## Where a smaller model skips it, and what stops that

| You will be tempted to ... | What happens |
|---|---|
| skip this skill because the request says nothing about surfaces | the descriptions and first lines of three skills, the README and the tips guide say it; `preflight place` refuses, and `plates` refuses when a scene is named (it says so as a LOOK when none is) |
| build plain boxes and finish (they pass the model lint) | `finish` replaces plain materials by role; the audit fails plain boxes; `model_lint.py --surfaces` warns on .glb files |
| leave out UVs | `finish` writes them; the audit fails an object under a normal-mapped material with no UV layer |
| use Bump only, a green channel the wrong way up, or sRGB colour on a normal map | wiring check plus `normals-test` with a flipped control |
| put a displacement node on a flat plane, or leave the material on Bump Only | the audit's displacement check |
| set a layer to 0, or forget its `pk_<layer>_amount` property (the layer silently reads 0) | audit "layer amounts" fails; 0 needs an `off` entry with a reason |
| grow weeds on wheel tracks, in puddles, on doorsteps, or no weeds at all | exact-zero keep-out counts; weeds and moss are required by role and look |
| leave a plank floating or a post short | the construction check is required and exits 1 (a rail tenoned into two carried posts counts as carried; a boat afloat counts as carried by the water) |
| leave an object with no material, or build a rope from a bevelled curve, a sign from text, a prop by instancing | the audit fails an object with no material by name, `finish` turns curves, text and instances into meshes, and the audit fails what is still not a mesh |
| let a name decide a role and never look (a "Reed bed" read as a thatch roof) | tag the role as you make the object; the audit warns on every fallback role and fails above 15 percent of the objects |
| make a door 1.0 m high | the facts table and the scale check |
| add photographic noise instead of a few big designed marks | the style rule, the guard and detail-energy band, the fresh look checker |
| say "it looks fine" | fresh checkers recompute the claims without seeing your numbers |
| use the wrong renderer, or run up a bill | `renderer-for`, `render`, the balance and worker checks |
| draw from a scene you changed after the audit | the audit's scene hash no longer matches: stale |
| build parts in parallel and overwrite each other | owners, idempotent stage files, a scene fingerprint diff, both orders |
| write a key, an id or a personal detail into a file | the client reads settings at run time; `check-presets` and the push guard scan for them |
| try one small change, look, change again; rebuild the scene for every test; draw every test at full size; run 25 versions of one tree one after another (the garden spent US$10.89 of card time this way) | the `variations` tool draws about 10 far-apart versions of a change in one batch from the saved scene, small and quick; the card-time ledger writes every job and the allowance refuses past it; a third batch for one change is refused |

## Rules that conflict, and which wins

- **Normal map and displacement together.** The Scenario texturing skill says never both. The coal-mine yard used both
  (normal strength x 0.6) and the cookbook measured no doubling. Decision (judged): a real normal map carries the fine
  grain on every surface; displacement is added only where `roles.json` says `displace` (nine roles: dirt road, mud, forest floor, stone paving, gravel, rock ground, plain earth ground, stone wall and thatch) and
  the mesh is dense or adaptive; where it is on, normal strength is multiplied by 0.6. A low-angle test result is in
  `place-kit/DEVIATIONS.md`.
- **Cycles when lit.** The Scenario skills default to EEVEE for finals. The film owner's rule wins: Cycles where lamps,
  windows, lanterns or fires are lit, EEVEE when they are off (`renderer-for`).
- **Painter template words on wet places.** "Matte painted finish" and "never puddles or reflections" make the painter
  remove wet ground (measured on a wet street: the ground came back dry). Change those words for wet views.
- **Bump only is not enough.** Bump changes only the shading, and at its default Distance it is nearly flat.
- **"glTF has no displacement"** is true for the card-model route (.glb into three.js). It is not true for pictures
  drawn in Blender with Cycles.
- **Realism against the style rule.** When more detail would make the picture photographic, the style rule wins:
  fewer, bigger, cleaner marks (`style-rule-and-measures.md`).

## Read next

- `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/the-required-steps.md`: the numbered steps, the live-Blender route, the shortcuts that fail.
- `surface-recipes.md`: surface by surface, with sizes, maps and the Poly Haven picks.
- `wear-recipes.md`: where each kind of wear goes, how much, how big, in what order, and a road cut by heavy carts.
- `construction-and-scale.md`: building from the ground up, the facts table, what the construction check measures.
- `style-rule-and-measures.md`: the style rule, the style note, the picture measures.
- `fresh-checkers.md`: how to be checked honestly.
- `rendering-on-rented-cards.md`: cheap Cycles on rented cards, set-up by the person, daily use.
- `batched-rounds-and-card-time.md`: the batch rule, the `variations` tool, the sheet and its measures, the card-time ledger and the allowance.
- `blender-5-traps.md`: the Blender 5.2 traps that cost whole rounds.
- `worked-examples-garden-and-canal-lock.md`: two real places walked through, with their measured numbers.
- Also: the workflow `build-a-place` builds a place in parts with fresh checkers; the tips guide section 8a.
