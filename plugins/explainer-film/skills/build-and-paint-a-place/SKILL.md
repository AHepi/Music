---
name: build-and-paint-a-place
description: A place built here (a village, town, harbour, mine, farm, garden, interior or any set) must first pass the surface-and-wear pass and the construction check (skill surfaces-wear-and-construction; preflight stage place), whatever the request says. Build a place for a film in Blender by script (free Poly Haven models and surfaces, scripted props with real lettering, people), plan each view by calculation before drawing it (place facts, the shot planner, the lettering, light and smoke planners, model lint), compose it with the shot checker, draw a plate, check it before paying, have it painted over with an image-edit model on fal, check and line up the painting when it arrives, and shine it back onto the 3D set in a page so the camera can hold or slide without tearing; with held shots, state pictures (people gone, a factory slowed) and the checks before filming. Use for the built-and-painted look (chapter 2 for newcomers), or whenever a page needs a place the camera moves in.
---

# Build a place in 3D and paint it over

> **REQUIRED for every place, set or prop you build in Blender** (also when the request never mentions surfaces, wear or realism). Do it without being asked. In your report say plainly what the pass did, what the audit measured and what you skipped.
> 1. Build it so every part is carried (planks on supports, supports on the ground, nothing floating; a rail tenoned into two posts counts as carried) and at real size, and give every object its role AS YOU MAKE IT (`pk.new_part_object(owner, role, name, mesh)`, or the object property `place_role`). The role ids are listed by `explainer-film-place roles --list`. Never trust a role the kit only guessed from a name. The pass bends, chips and leans parts but never removes one, and it does not darken the ground where things touch or where water runs: build those yourself, as shape, while you build (a missing slate, a gap in the planking, one new board among grey ones; a few big, soft, darker shapes under a crate or a stall, round a post's foot, a rust run below an iron ring, the drip line under the eaves, a spout's spill), and the rubbish of the place's own work where the work happens (chips and bark by a woodpile, ash under a lamp or hearth, the broken pieces of a fallen slate below its gap).
> 2. Run the surface-and-wear pass: `explainer-film-place finish --scene SCENE.blend --settings place-settings.json --save-as FINISHED.blend` (it needs `--save-as`; it drafts `place-settings.json` when there is none, with a road for every dirt-road object). To read and improve a draft first: `explainer-film-place new-settings --scene SCENE.blend --place NAME --type TYPE --out place-settings.json`, where TYPE is the nearest of village, town, harbour, mine, farm, garden, interior or generic. It turns curves, text and instanced props into meshes, then gives each surface a real photographed scan (the person's own library when `own_surfaces` names one, else the free Poly Haven scan, downloaded once per machine; with no network it uses the made-in-code surface and says so in a LOOK line: tell the person) with real normal maps and displacement, roughness and colour variation, then dirt, grime, weathering, wetness, cracks, chips, edge wear, moss, rust, rubbish and damage as shape, and lays weeds, litter, stones and puddles by site (wall feet, verges, fence lines, joints, damp corners), not evenly. Never copy the person's own texture files into the plugin or a repository: the kit reads them where they are.
> 3. Run `explainer-film-place audit --scene FINISHED.blend --settings place-settings.json --out place-audit.json`, then `explainer-film-preflight place --place-audit place-audit.json --blend FINISHED.blend --reports REPORTS_FOLDER`. It must PASS before you draw, render or paint anything. Do not save the scene again after the audit; if you do, audit again.
> 4. Try things in batches, inside a card-time allowance: make every change you plan in ONE sweep, then look once. Build the scene once and save it. For each change to a thing (a tree, a wall, moss) do not try one small change at a time: write about 10 variations whose settings are far apart, check them for free here first (`explainer-film-place variations scout FILE.json`: tiny pictures on this computer, no card time; it says which would not show), and draw them in ONE batch (`explainer-film-place variations run FILE.json --where rented --helper builder-walls --role builder` (`--helper` takes a short name for this helper, never a person's name): it drops near-duplicates and what the scout found would not show, spreads the variations over up to 3 rented cards, measures every picture and makes ONE labelled sheet). Look at the sheet, pick or combine, at most ONE more batch. Small quick pictures until the end (600 x 400 for trying variations, or the tall 360 x 640 for a place marked for the film: the tool picks it; 1200 x 800 for the checkers' previews); full-size pictures once, at the very end. Every card job is written in a ledger and each helper has an allowance (builder 10 minutes, fixer 5): the tool refuses past it. Report the card seconds you used. Read `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/batched-rounds-and-card-time.md` first.
> 5. When the place will be shown in the film (on a phone): its views are 1080 x 1920 (previews in the same tall shape, for example 540 x 960, not 1200 x 800), write `"for_film": true` in `place-settings.json`, and read `${CLAUDE_PLUGIN_ROOT}/skills/build-and-paint-a-place/SKILL.md` before you place a camera.
> The person's words win: if they say not to use this plugin or a named part of it ("plain Blender", "do not use the skill"), that wins over this block and over the reminder. Say in one line what you leave out, and still say what you tested and what you did not.
> Details, every command and the live-Blender route: `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/SKILL.md`.

What this is: the way the austerity project made its places from log 29 to log 35 (the pit village's notice
corner, the people test, the Works of chapter 2 for newcomers, the checkout), as one set of steps, with the
calculators that now work out what used to be found by trial. KIT = the folder made by `explainer-film-setup`;
every path below starts there. The rules for composing are in the kit's `docs/paper-look - 07 Composing a shot.md`;
the short rules and the traps are in `docs/LLM tips and tricks.md` (sections 4 to 12). Read both before step 3.

**Example.** The notice corner (logs 31 and 32): the pit village street built in Blender from Poly Haven
surfaces and props, a lock-out notice on a board with a burning drum, an empty chair with a lit lantern on it
and a pail, composed until the shot checker passed 32 of 38 checks; a plate 1536 x 2730 drawn with EEVEE from
the start of the slide; Flux 3 edit painted it over and a second time with the near props painted out; both
lined up with the plate (the painter had stretched it 0.65% and shifted it 3 pixels); the page
`paper-film/scenes/notice-corner.js` shines the paintings back onto the set and slides 1.5 m toward the notice
without turning. Two paintings cost about 20 to 45 US cents.

**Start small.** Before you draw every view or pay for anything, deliver one small test for the person's reaction:
build and audit the place (free, on this computer), draw only the first view's small picture (and, if asked, one
painting of it), then stop and wait. The other views, the fresh checkers, the fix round and any other painting wait
for the person (the workflow `build-a-place` does exactly this unless told `allViews: true`). Say what it costs and
what it will not show. When the person is choosing a look, show a few versions of the SAME view so only the
look changes (five style samples of one scene cost about US$0.90 in all), and say which you would pick and why.

**What this method cannot do.** A painted plate covers one view and a little more (a slide of about 1.29 times
nearer at most). Do not promise a camera that moves through the whole street, or light that reacts to people moving
about: for that the whole set (every side, the interiors, the people) would need its own light and be drawn live,
which is a later project the person has named. If they ask for it, say so and ask which sequence comes first.

## The tools, in the order you use them

| Moment | Tool (from KIT) | What it works out | Preflight |
|---|---|---|---|
| After building each model, and the dressed scene: roles, surfaces, wear, growth | `explainer-film-place finish` (then `audit`) | the whole surface-and-wear pass and the facts table of the scene (skill `surfaces-wear-and-construction`) | `place` |
| When parts are built by several helpers | `explainer-film-place finish-part`, `combine`, `ownership-diff` | each owner's share, the combined scene, who touched what | `place` |
| After the pass | `explainer-film-place construction`, `normals-test` | every part carried, in reach and the right size; every normal map pointing the right way | `place` |
| Trying variations of a change (before drawing the plate) | `explainer-film-place variations make`, `plan`, `run`, `refine`; `explainer-film-place card-time show` | about 10 measurably different variations in one batch on up to 3 cards, one labelled sheet with measures and the card seconds; every card job in the ledger, each helper inside an allowance | `place` |
| Before drawing | `explainer-film-place renderer-for`, `render` | Cycles where lamps, windows, lanterns or fires are lit, otherwise EEVEE; previews on a rented card | `place` |
| After drawing | `explainer-film-place measure` | value range, detail energy, flat windows, palette and squint against the style guard | `place` |
| After building each model, and the dressed scene | `paper-film/blender/model_lint.py` | stripes, two surfaces on one plane, floors just over the ground, ".001" copies, glass reading its picture's see-through, glowing light bases, sizes against the index, fronts | `plates` (run it while building too) |
| Once the place is built (its facts are read from the finished scene) | `calculators/place_facts.py` | the place facts every later tool reads: views, signs, chimneys and fires, figures, lights, surfaces things stand on, the accepted list | `shots` |
| Before drawing a view | `calculators/plan_shot.py` | the camera spot, eye, turn, the slide and its limit, the plate's lens and rows, the people (6 m rule, crowd across the view), the reach | `shots` |
| Before drawing a view | `calculators/frame_geometry.py` | where any point or box lands, sizes in pixels, reach, eye needed, slide magnification at the nearest painted thing | (by hand; `plan_shot.py` uses the same sums) |
| Before drawing a view | `calculators/view_audit.py` | letter heights per view, drum turns, loud signs nobody names, backs of signs, landmark tops in the words band, heads that could show a face | `shots` |
| Before lighting | `calculators/plan_lights.py plan` (with `paper-film/blender/set_measurements.py beam`) | each light's role, starting watts, reach, cone, links, which few cast shadows; lamps landing on the subject | `shots` |
| Before the page's smoke | `calculators/plan_effects.py wind` | the wind across every view; each plume traced on the frame | `shots` |
| After the assemble script | `paper-film/blender/make_check_file.py` | the view's check file, measured from the scene (only the story roles are yours) | `shots` reads it |
| On every composed view | `paper-film/tools/check-shot.sh` | the shot checker: what breaks the composing rules and what to change, in metres | `plates` reads its report |
| When the page plan is known | `calculators/plan_states.py plan` | every plate a held shot's changes need, one per change on its own word | `shots` |
| After the plate is drawn | `calculators/plan_lights.py render-log` | a plate drawn with a shadow fault is refused | `plates` |
| Before paying | `calculators/paint_request.py request` | the plate's preflight, both prompts, the price; it never sends | `plates` |
| When a painting arrives | `calculators/after_painting.py check` | resize, line-up, figures (count, outline, darkness, skin), style, the behind painting and its kept shadows | `paint` |
| While building the page | `paper-film/tools/camera_audit.py --built-set`; `calculators/plan_effects.py contact-shadows`, `window-change` | no turn during a slide, the frame inside the painting; contact shadows, a teaching change of 15 levels | `pages` (the camera audit) |

Every tool answers `--help`, prints a plain report and lists the house numbers it used (all in
`film-settings.json`). Patterns for the input files are in `calculators/tests/fixtures/` (for example
`notice-corner/notice-corner-place-facts.json`, `shot-planner/notice-corner-shots.json`,
`views-and-models/shot-lists/checkout-c1.json`, `painting/notice-corner-brief.json`,
`painting/works-state-plan.json`).

## 1. Set up (once per machine)

- The full Blender program (5.2.2 was used), not only the `bpy` Python module: plates are drawn with EEVEE and
  the shot checker draws its flat-colour pictures in Blender. EEVEE runs without a graphics card under a
  virtual screen: `Xvfb :96 -screen 0 1920x1080x24 &`, then `DISPLAY=:96 blender -b ...`. EEVEE only where lamps,
  windows, lanterns and fires are off. Where they are lit, use Cycles, on a rented card (the film owner's rule; skill
  `surfaces-wear-and-construction`, `rendering-on-rented-cards.md`).
- `explainer-film-setup` checks for Blender and Xvfb and writes `machine-settings.env` in the kit (BLENDER,
  BLENDER_DISPLAY); `check-shot.sh` and the checker's tests read it. In the commands below, `"$BLENDER"` is
  that program (`set -a; . ./machine-settings.env; set +a` in the kit folder sets it), run with
  `DISPLAY=:96` when it draws with EEVEE.
- Blender's own Python has numpy but no Pillow (and no OpenCV): the place kit needs only numpy inside Blender, and the plain
  Python tools outside it (`calculators/`) may use numpy and Pillow. `explainer-film-setup` notes this.
- Budget a set by how long a frame takes to film, not by a triangle count: on the Works a held frame took
  about 0.9 s and a sliding one about 4.3 s (round 4, one worker). Measure a slow page with
  `node paper-film/tools/profile_frame.mjs PAGE TIME` (or `PROFILE_SCENE=notice-corner ... - 9` for a scene).

## 2. Build the place by script

Copy the pit village as the pattern (`paper-film/blender/pit-village/`):
1. Surfaces and models from Poly Haven (free, CC0): `fetch_street_textures.py`; `props/poly_haven_choices.py`
   lists the models, `props/download_poly_haven.py` fetches them and `props/convert_poly_haven.py` makes the
   prop library (it can paint out a maker's label: `PAINT_OUT` in the choices file). Open every downloaded
   texture at full size and look for stickers, brands and digits.
   **Give every object a role (`place_role`) and an owner (`place_owner`) as you make it, then run the surface-and-wear pass
   (`explainer-film-place finish`).** Poly Haven pictures alone read bland: real normal maps, shape, designed marks and
   plants go on top (skill `surfaces-wear-and-construction`).
2. Props Poly Haven doesn't have are built by script (`props/build_scripted_props.py` with `scripted_kit.py`
   and `prop_library.py`). No blank signs, book covers or plain boxes: every sign carries real lettering
   (`props/paint_prop_pictures.py`; fonts and their OFL licences in `props/fonts/`), and the painter writes
   `lettering-sizes.json` before the builder runs. Check lettering reads at phone size
   (`props/readability_test.py`, `props/make_sheet.py`). Every prop gets a role and an owner too. The place audit's
   check "place: lettering" fails a sign, notice, placard, poster, name board or book that has no lettering. (The
   painter is asked for blank placards only so that it invents no writing: skill `paint-and-cut`.)
   A name written on a prop (a newspaper, a shop, a firm) is either made up on purpose and checked against real
   ones (a newspaper masthead was checked against 1,617 New Zealand newspaper titles), or a real one used
   correctly: never let a made-up name copy a real one by accident. Text on a prop is a claim too: check its
   dates and weekdays (30 April 1926 was a Friday, 1 May a Saturday) and its wording against a real source.
   `python3 calculators/list_prop_lettering.py --out prop-lettering.json` lists every string written on a prop;
   give that file and the pictures to the fact checker (skill `check-facts`) and to the critics.
   When two buildings or objects stand for different things (two factories, a before and an after), make them
   tellable apart at a glance in the half-size picture: a different colour, roof, count and shape of chimneys
   (dark red brick with one round chimney against pale stone with two square chimneys and a tank). Test it: show
   the half-size picture to a blind reader and ask which is which. A background landmark must look like neither.
   (No tool checks this yet: it is judged.)
3. The street: `build_street.py --out FOLDER --name NAME` (it refuses to overwrite without `--replace`). Give its objects roles
   and seat everything on the ground height (`pk.seat_on_ground`).
4. People (each with a role and an owner): `paper-film/blender/figures/build_figures.py` (waiting men, walkers; cloth from
   `fetch_cloth_textures.py`). Check them lit by a lamp from the camera's side (`figure_sheet.py`): that light
   showed bald-looking heads. Dark matt hair, collars up, the back of each head darker than its coat.
5. A second place's props: `paper-film/blender/inflation-chapter-2-newcomers/props/` (built with `--choices`,
   `--library` and `--scratch`).
6. **Lint every model before you place it, and the dressed scene before any plate** (a stripe, a floor 2 cm
   over the ground or glass reading its picture's see-through costs a repaint once painted):
   `python3 paper-film/blender/model_lint.py MODELS.glb --index props/index.json` (add `--prop` for a prop file,
   `--as-set` for a set; `--write-index NEW.json` records each model's measured size and front), or inside
   Blender on the open scene: `"$BLENDER" -b SCENE.blend --disable-autoexec --python paper-film/blender/model_lint.py`.
   Measure a model before fitting anything to it; never use a size from a helper's picture.
7. **Write the place facts** (`calculators/place_facts_schema.json`): the assemble script should write them
   itself; for a place measured with `shot_facts.py`, build them with
   `python3 calculators/place_facts.py from-shot-facts --facts facts.json --check CHECK.json --place NAME --view VIEW --kind KIND --out place-facts.json`.
   Name each view's kinds of shot (still_life, crowd, overview, interior, dark_subject) and the surfaces
   things stand on (a counter as well as the floor). Check it:
   `python3 calculators/place_facts.py check place-facts.json`.

## 2b. Check the place (preflight `place`)

A place that is built but flat is not finished, and a model that passes the model lint can still be three plain boxes.
1. `explainer-film-place finish --scene SET.blend --settings place-settings.json --save-as FINISHED.blend`, then
   `explainer-film-place audit --scene FINISHED.blend --settings place-settings.json --out place-audit.json`.
2. `explainer-film-preflight place --place-audit place-audit.json --blend FINISHED.blend` must PASS before any view is drawn.
   It fails when a material or the scene lacks a required treatment (normal map, displacement, dirt, grime, weathering,
   wetness, cracks, edge wear, moss, rust, rubbish, plants), when a part floats, when a size is wrong, or when the audit is
   stale. The order is: `shots` once from the brief for the rough camera plan, build, `place`, then `shots` again once the scene exists to read the place facts from, then `plates`; both `shots` runs and `place` must pass before any plate.
3. The steps, the shortcuts that fail and the live-Blender route are in
   `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/the-required-steps.md`.

## 2c. Try changes in batches, inside a card-time allowance (before any plate)

Trying things one small change at a time, with a look after each, is what turned a US$10.89 card bill in the Japanese garden into pictures that cost about 5 cents. The rule: **plan every change, make them all in one sweep, then look once.** Build the scene once and save it (`FINISHED.blend`). For each change to a thing (a tree, a wall's moss, a gate's lean), write about 10 variations whose settings are far apart and draw them in ONE batch: `explainer-film-place variations make` writes the file, `variations plan` checks it for free, `variations run FILE.json --where rented --helper builder-walls --role builder` (a short name for this helper, never a person's name) draws it on up to 3 rented cards at once (600 x 400, or 360 x 640 for a place marked `"for_film": true`, EEVEE or low-sample Cycles by the renderer rule), measures every picture against the baseline and makes ONE labelled sheet. Look at the sheet with the Read tool, pick or combine, and draw at most ONE more batch (`variations refine`). Small quick pictures until the end; the plate and the full-size pictures once, at the very end. Every card job is written in the card-time ledger (`explainer-film-place card-time show`), and each helper has an allowance (builder 10 minutes, fixer 5, integrator 10, renderer 10, checker 3, planner 0: judged): the tool refuses past it. Report the card seconds you used. The whole rule, the sheet's measures and a variations file written by hand are in `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/batched-rounds-and-card-time.md`.

## 3. Plan each view by calculation, before drawing it (preflight `shots`)

1. **The camera:** `python3 calculators/plan_shot.py --place-facts place-facts.json --view VIEW --plan`, or a
   shot list for several (`--shots SHOTS.json`; the format is in the file's note). It stands the camera where a
   person would stand (eye 1.5 to 1.9 m above the surface under it, level, in line with the subject's near
   edge), as far back as the nearest story thing still reaches 0.72 down, turns it once so the street's lines
   meet beside the subject, then slides it sideways (never turns) to clear the phone buttons. It gives the
   slide's limit at the nearest painted thing, the plate's lens and rows, and judges the people: backs to the
   camera at 6 m or more from every spot along the slide, a crowd across the view, two deep, heads a head
   width apart. A "look" means: confirm on the render with the shot checker. It never offers a silhouette
   (lesson 137); a face that shows gets the painter's "face lost in shadow" words.
2. **The slide:** `python3 calculators/frame_geometry.py slide --place-facts place-facts.json --view VIEW`
   (about 1.29 times nearer at most, judged at the nearest painted thing with the painter's returned height;
   `--count-ground` shows the painted ground too, which is a judgement).
3. **The lettering and figures:**
   `python3 calculators/view_audit.py audit --place-facts place-facts.json --timeline timeline-estimated.json --page N` (a word the page needs under 20 px fails; a readable sign the
   page never says is read first, so dim it or take it out of frame; drum turns toward every camera that reads
   them; landmark tops below 0.24 down).
4. **The lights:** `python3 calculators/plan_lights.py plan --place-facts place-facts.json --view VIEW`
   (better with each light's ray hits:
   `"$BLENDER" -b SET.blend --python paper-film/blender/set_measurements.py -- beam --check CHECK.json --light NAME --out beam.json`,
   then `--beam-hits NAME=beam.json`). Give the subject its own narrow key from below, linked to it alone;
   only a few lights cast shadows; people get foot patches, not long shadows (lesson 135); a dark subject is
   shown against a lit background and judged by silhouette contrast (`plan_lights.py contrast`).
5. **The smoke:** `python3 calculators/plan_effects.py wind --place-facts place-facts.json` picks a wind
   across every view and traces each plume on the frame. Smoke blown away from the camera piles into rings
   (lesson 134).
6. Then `explainer-film-preflight shots --project FILM_FOLDER --place-facts place-facts.json --shot-list SHOTS.json`
   (or with the film's `preflight-plan.json`) and read its report; `--list` names every input it takes.

## 4. Compose each view with the shot checker

1. Write the shot's assemble script (pattern: `pit-village/assemble_notice_corner.py`; shared steps in
   `pit-village/set_dressing.py`: `place_prop` stands a prop on the first surface a ray straight down meets,
   give every object it places a role (`place_role`), `light_reaches` limits a light to some objects, `glow_material`, `brazier_fire`, `render`,
   `export_for_film`). Use the planned camera from step 3.
2. **Write the check file from the scene**, not by hand. Only the story roles are yours, in a short shot
   list (subject, support, story, work, and any groups you merge, split or add):
   `"$BLENDER" -b BASE.blend --python ASSEMBLE.py --python paper-film/blender/make_check_file.py -- --shot-list SHOT_LIST.json --check-file CHECK.json --place-facts place-facts.json`.
   It measures the rest (groups, `must_read` from lettering materials, `pairs_also`, what stands on what,
   light props, the eye range, the title zone) and writes the keys the checker reads: `kind_of_shot`,
   `figures`, `support_surfaces`, `accepted`. Hand-made files got `must_read`, `pairs_also` and `on_ground`
   wrong. (The hand-made `examples/notice-corner/shot-check.json` and
   `examples/inflation-chapter-2-newcomers/works-w1-shot-check.json` show the format.)
3. Run the checker (about a minute):
   `BLEND=assets/models/<place>/<scene>.blend paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER -- --view end`
   then read `OUT_FOLDER/report.md` and look at `marked.jpg`. Fix the first problem only, then run it again:
   the camera first (it moves everything), then the props, then the light. (This is for measured checks that run here and cost no card time; a look at a picture follows the batch rule: one sweep, then one look.) Give a finished EEVEE still and
   its log (`RENDER_LOG=...`) to judge the light rules; a log with "Shadow buffer full" or "Could not allocate
   shadow atlas" means the light can't be judged.
4. **Kinds of shot and accepted problems.** The rules came from a still life. A crowd, an overview, an
   interior or a dark subject breaks some on purpose: `kind_of_shot` in the check file relaxes exactly those
   (`python3 calculators/settings.py profile crowd dark_subject` prints the rules a view is held to). A
   problem the project chooses to keep goes in the check file's `accepted` list with the rule, the reason, who
   accepted it and the date; the checker then reports it under "Known and allowed", and fails it again only if
   it grows past what was accepted. Whether to accept is a judgement: ask the person or a critic.
5. Before trusting a change to the checker itself, run its tests:
   `paper-film/blender/tests/run-checker-tests.sh OUT_FOLDER` (eleven faults planted on purpose; each report's
   first fix must name its fault; needs the pit village street, see the note in that file).

## 5. Draw the plate and export the set (preflight `plates`)

- Draw the plate from the start of the slide, with the lens the planner gave (the notice corner: 64.4 degrees
  against the film's 60.4), 1536 x 2730, with the renderer rule: EEVEE only where lamps, windows, lanterns and fires are off (about 6 to 11 minutes
  under a virtual screen; a 540 x 960 preview about a minute); where they are lit, Cycles on a rented card
  (`explainer-film-place renderer-for` says which, `render` draws it; about 40 s for a 2400 x 1600 final on a card).
- Check its render log before anything else: `python3 calculators/plan_lights.py render-log RENDER.log`
  refuses a plate drawn with a shadow fault.
- Draw people so they cast no long shadows (only a small soft shadow under their feet): the painter leaves
  long shadows behind when asked to remove the people (lesson 135). Draw a helper plate without them for the
  preflight's long-shadow check.
- Darken a faint glow inside a hollow (a drum's inner glow) before painting: the painter lifts it into a
  bright band (lesson 138).
- **Plan the held shot's other plates now** (people gone, a factory slowed, the behind plate):
  `python3 calculators/plan_states.py plan --plan STATE_PLAN.json` lists every plate, one per change on its own
  word, and stops on a change during a slide or two changes on one plate.
- Export the set for the film: `assemble_notice_corner.py --plate PLATE --export` writes the set and signs as
  .glb and the camera as `notice-corner-camera.json` (`set_dressing.export_for_film` needs its folder).

## 6. Paint it over (paid: confirm the cost with the person first)

**Draw every plate of one place with the same renderer.** EEVEE streets came out cold blue and Cycles streets warm
gold (mostly because EEVEE's light cut-off stops lamp light reaching the road), and the painter follows the mood of
the plate it is given, so do not mix renderers inside one place or compare pictures across them (the plates stage
gives a LOOK when the plates of one place were drawn with different engines). This rule wins over the per-scene rule:
if any plate of a place needs Cycles (a lamp, window, lantern or fire lit, or water in view), draw every plate of that
place with Cycles (`"renderer": "cycles"` in place-settings.json), the unlit ones too. Not yet tried: whether the painting
checks, tuned on EEVEE plates, hold for Cycles plates (the plates stage says so as a LOOK), and Cycles in a moving
shot (its noise clean-up could flicker). Test one before sending a Cycles plate to the paid painter.

1. **Before paying**, run the request builder. It checks the plate, writes both prompts and prices them; it
   never sends anything:
   `python3 calculators/paint_request.py request --check CHECK.json --facts PLATE_FACTS --plate PLATE.png --brief BRIEF.json --place-facts place-facts.json --view VIEW --render-log RENDER.log --shot-report OUT_FOLDER/report.md --helper-plate PLATE_WITHOUT_PEOPLE.png --style STYLE.png --out-folder REQUEST_FOLDER`
   (PLATE_FACTS is `shot_facts.py`'s folder for the plate's own camera and lens). It refuses a plate with a
   render fault, a light-rule failure, a glow in a hollow, a pure-black opening, people's long shadows, heads
   paler than coats or cloth the film's finish turns red. Fix every failure in 3D, not in the prompt. Write
   only each story prop's `paint_as` words in the check file (what it is, its colour, its state, what it must
   not become) and the short brief; the rest of the prompt is built from the template (every person counted;
   far walkers "flat dark shapes with no pale spots"; no flames, smoke, glows or new shadows).
   **Wet or dusk places:** the template's words "matte painted finish" and "never puddles or reflections" make the painter
   remove wet ground (a wet street came back dry). Change them for that view, so the painted finish keeps the sheen of wet
   ground, its puddles, mirrored lights, joints and gutters (or use `paint_request.py`'s `--keep-wetness`).
2. **The price.** Prices change between plan and purchase (Flux 3 edit was 2.4 US cents a megapixel when
   planned and 4.8 a day later, lesson 139): read fal's live price, then
   `python3 calculators/paint_request.py price --rate-cents CENTS` (the returned picture and every picture sent,
   about 44 cents for a 2k repaint with a style picture at 4.8) and
   `python3 calculators/plan_budget.py ledger LEDGER.json --next-cost DOLLARS`. Then
   `explainer-film-preflight plates` (it needs the check file, the plate, the plate's facts folder, the render
   log and the shot checker's report), and ask the person once with the exact cost. A vague reply is not a yes.
   Right before paying, `explainer-film-preflight plates --gate` says whether that report still stands.
3. Flux 3 edit on fal: image 1 the plate, image 2 the place's master painting in the film's style (send it at
   about 1 million pixels). Paint the master view first and use it as the style picture for the rest.
4. **When it arrives**, check it before anything uses it:
   `python3 calculators/after_painting.py check --painting RETURNED.png --plate PLATE.png --check CHECK.json --facts PLATE_FACTS --out-folder D`
   It resizes to the plate, lines it up (the notice corner's painter had stretched it 0.65% and shifted it 3
   pixels), counts the figures and checks their outlines, darkness (painted men lifted from 15% to 50% of their
   surroundings turned mid-grey on a phone) and skin on heads, and compares the style. It writes PNG only.
   Read its LOOK lines too: "bottom fifth" (the bottom fifth is more than 30 percent darker than the middle, so
   the bottom is going empty: the nearest story thing should reach about 0.70 down) and "clouds" (the painted sky
   has more contrast than a plain sky: the painter added clouds). Then `explainer-film-preflight paint`.
4b. **A plain sky.** The painter adds heavy pale clouds even when told not to (three sentences against them did not
   hold). Do not rely on words, and do not write your own masking code: run
   `python3 calculators/after_painting.py sky --painting ALIGNED.png --plate PLATE.png --facts PLATE_FACTS --to NEW.png`
   (ALIGNED.png is the lined-up painting, the `-aligned.png` picture that `check` wrote in its folder). It lays the plate's own plain sky in exactly inside the
   plate's sky area (Blender's exact sky outline, from the plate's facts folder), keeps thin rails and roof edges as
   painted, never writes over the painting or the plate, and keeps an earlier NEW.png as NEW-previous.png. Look at the
   edges at full size (by hand it took four tries to keep thin rails and wires clean), read the "clouds" LOOK again on
   the new picture, and say that you did it.
5. **A "behind" painting** for what the near props hide. The better route: draw a twin plate in Blender with
   exactly the props the page hides left out (read the page to find them), have that painted, then match its
   brightness to the front painting (free). The older route: ask Flux once more, with the lined-up painting as the
   only picture, to paint the near props out. Check either with
   `after_painting.py check ... --behind RETURNED_BEHIND.png --near-list REQUEST_FOLDER/near-list.json`, which
   lines it up against the painting and keeps the first painting's shadows round the near props (the painter
   takes them away, lesson 122). It FAILs with a "pale patch" line when the behind painting is lighter than the
   front one where the near props stood. For a slide past people with no painting of them gone,
   `paper-film/tools/make_behind_picture.py` fills in their outlines from round about (free; look at its
   `--look` picture). The page hands over from the painting to the behind painting as soon as the camera starts
   to move (`projected-set.js` does it; waiting for more movement showed the gap, and it took three tries to find).
5b. **Wet and dry paintings go in and out as a pair.** Never put a wet front painting over a dry behind painting:
   where the camera uncovers what a near prop hid, a pale dry patch shows (59 percent of the road dots came out
   lighter, measured; `after_painting.py check --behind` fails it as a "pale patch"). Draw the plate and the behind
   plate in the same state, paint both, and swap both at once together with the page's look line (section 7). Keep
   the other pair beside them under clear names (for example `NAME-dry.png` beside `NAME-wet.png`) with a short
   note saying how to go back (a few renames and one look line). Never write over a painting the person liked.
5c. **After a slide, look for these** (stills of the move, and the filmed clip): pale or dry-looking patches where
   the behind and front paintings differ; painted shadows or outlines left on the road where a prop stood; a seam
   between the front and behind paintings; a halo along the roofline; jumps other than the planned cut
   (`paper-film/tools/find_jumps.py`); more flicker than before.
6. **State pictures**: `python3 calculators/plan_states.py plan --plan STATE_PLAN.json --measure` measures how
   much of the frame each change swaps (a time cut up to about 12%, otherwise a blend of 0.8 s in 3 steps) and
   prints the exact `paper-film/tools/make_state_picture.py` commands.
7. The older hand tools still work on their own: `paper-film/tools/align_painting.py`,
   `paper-film/tools/keep_painted_shadows.py`.

## 7. The page: shine the painting back onto the set (preflight `pages`)

```js
import { loadProjector, projectPaintingOnto, skyCard } from '../projected-set.js';
const projector = await loadProjector('/assets/models/<place>/<view>-camera.json');
const projection = projectPaintingOnto(kit, set, painting, projector, { behind: { painting: behind, hide: nearProps } });
const sky = skyCard(kit, projection, painting, projector);   // the painted sky on a far card
```
- Lettered materials keep their own sharp surfaces (`ownSurface`): the painter garbles small print.
- Soft contact shadows under the near props, faded in as the camera starts to move
  (`contactShadow` in `pit-village-effects.js`), sized by
  `python3 calculators/plan_effects.py contact-shadows --place-facts place-facts.json`; flames and sparks drawn
  live (`Flames`, `Sparks`).
- One slide per shot, never a turn (`skills/build-cinema-page/camera-and-framing.md` section 1a); lens blur
  `aperture: 4.0, maxBlur: 2`. Measure it:
  `python3 -I paper-film/tools/camera_audit.py CAMERA.json --built-set --place-facts place-facts.json --view VIEW`
  (no turn during a slide, where the lines meet holds, the magnification at the nearest painted thing, the
  frame inside the painted plate).
- While the camera holds, return `still: true` and mark flames, smoke and flicker with `kit.moving(...)`: the
  stage draws the painted set once.
- State changes on a held shot: `projection.setPainting(picture)` (a time cut), `projection.blendTo(picture,
  amount)` (a short blend), `projection.setView(projector, picture)` (another view of the same set). A state
  picture changes only where something changed. When only people vanish at a cut, change something else
  with them (the fire lower, the light later), or it reads as a glitch (lesson 136). A change that teaches a
  word must move the picture by 15 levels: `python3 calculators/plan_effects.py window-change --box l,t,r,b STILL_AT_WORD STILL_LATER`.
- Long chapters of heavy sets: `buildCinemaChapter({ ..., lazy: true })`; each page exports its `join`.
- **A dark, dusk or wet page.** The stage's film curve darkens dark values: in the wet lockout test the wet road
  arrived at 0.75 to 0.86 of how bright it was painted, and some of it crushed to black (measured). For such a page
  set `toe: 1` and `vignette: 0.25` in its look (`toe` 1 means the curve may still brighten a value but never darkens
  one; 0, the default, is the old behaviour, so no other scene changes; `paper-film/scenes/lockout-test.js` is the
  pattern). After every new painting run
  `python3 calculators/after_painting.py check --painting P --plate PLATE --check C --facts F --out-folder D --toe 1`:
  it prints how bright the road "arrives at" against its painting. The wet lockout reached 0.935 and the dry one with the same look 0.96 (measured); there is no limit yet, so treat
  anything under about 0.9 as a reason to look (invented). A wet painting also reads differently from a dry one (a
  detailed picture with a paint finish, no thick ink outlines and a plain dark sky, against flat colour with thick
  outlines): tell the person when two shots of one film differ in look like this.
- **Define each place's look once**, in one shared set file that every page showing the place loads: one works'
  door looked different on pages 3 and 8 when it was built twice.

## 8. Check before filming

1. Four stills: the projector's own view (it must match the painting), the end of the move, a middle moment,
   and the `weights` view (orange wears the painting, blue its own surface; blue at a frame edge means the
   camera left the painted area).
2. The page tools (skill `build-cinema-page`): `paper-film/tools/page_events.mjs`, then
   `calculators/plan_page_timing.py check` and `paper-film/tools/check_page_layout.mjs` on its events, or
   `explainer-film-preflight pages`.
3. The shot checker on the page's own end frame, independent critics on the stills (what they must still
   judge: section 19 of the tips guide), then `explainer-film-preflight film` and film (`skills/film-and-finish`),
   and look at the film in motion: `paper-film/tools/find_jumps.py` lists sudden jumps between frames (give it
   the planned cut times), and a clip without narration gets music with `paper-film/tools/add_music_bed.sh`.

## Worked examples in the kit

- The notice corner: `paper-film/blender/pit-village/assemble_notice_corner.py`, `examples/notice-corner/`,
  `paper-film/scenes/notice-corner.js`.
- The people test (painted men leaving): `pit-village/assemble_people_test.py`, `examples/people-test/`,
  `paper-film/scenes/people-test.js`.
- The first built test (log 29): `pit-village/assemble_lockout.py`, `paper-film/scenes/lockout-test.js`.
- The Works (chapter 2 for newcomers, pages 3 to 5): `paper-film/scenes/inflation-chapter-2-newcomers/` with
  `works-effects.js`, its check files in `examples/inflation-chapter-2-newcomers/`, state changes in
  `paper-film/scenes/works-states-test.js`. Its Blender scripts are still being changed in the austerity
  project and come in a later copy (`kit-sync-notes.md`).
- The calculators' inputs for these places (place facts, shot lists, briefs, state plans) are in
  `calculators/tests/fixtures/`, with the checkout as a place the rules were not built from.
- None of the pictures or models are in the plugin; the scripts rebuild the pit village, and the austerity
  project's film kit has everything.

## Traps (and the tool that catches each now)

- A flat, clean model passes the model lint (a hut of three plain boxes got PASS): run the place audit (`explainer-film-preflight place`).
- A stale audit: the scene was saved again after it, so the facts no longer match (`place` compares the scene's hash).
- Wear that vanishes on dark, edge-on walls at film size: lean on shape, normal maps and plants, and look at a 100 percent
  crop and a phone-sized one (`explainer-film-place measure`, `crops`).

- Never put a picture program's lettering on screen; use the set's own lettered props (`paint_request.py prompt`).
- A turn during a move slides where the lines meet across the frame: slide only (`camera_audit.py --built-set`).
- A full-frame helper pass must not test depth (`runPass` turns it off).
- Smoke blown away from the camera piles up into rings: blow it across the view (lesson 134; `plan_effects.py wind`).
- The main rule can pass while the bottom of the frame is empty: a story object must reach about 0.70 down
  (lesson 133; `plan_shot.py`, and the shot checker's rule 7).
- A single file of people seen end-on is one dark column: stand them across the view, two deep (lesson 132;
  `plan_shot.py`).
- Dark silhouettes laid over a painting read as shadow puppets (lesson 137; `plan_shot.py`, `after_painting.py`).
- Line up every painting with its plate, and keep the painted shadows in the props-removed copy (lessons 122,
  123; `after_painting.py check`).
- People's long shadows stay behind when the painter removes the people (lesson 135; `paint_request.py preflight --helper-plate`).
- One small change, then a look, then the next, with the scene rebuilt and the picture drawn at full size each time, ran up US$10.89 of card time in the garden: batch about 10 far-apart variations, small, from the saved scene, and stay inside the allowance (`explainer-film-place variations`, `card-time`).
- A mark in a picture that nobody can explain (a white shape, a streak): hide one group of objects at a time and draw a small
  picture each time until the mark goes. In the Japanese garden it was the pond mirroring the glowing paper screens: roughen the
  water slightly, dim the glowing thing, or hide the lamps from reflections.
- A wet front painting over a dry behind painting shows a pale dry patch when the camera moves (`after_painting.py check --behind`, "pale patch").
