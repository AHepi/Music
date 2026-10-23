# Explainer film (a Claude Code plugin)

What this is: everything an agent needs to make a narrated, fact-checked explainer film for a phone
screen (1080 x 1920), one chapter at a time, in the cinematic look of "What really causes
inflation" (chapter 2 of the austerity explainer) or the simpler paper pop-up look of chapter 1.
Written so that smaller models can follow it step by step. Since version 1.3.0 the numbers this project
once found by trial and error over 35 logs (where a prop lands on the frame, how far back the camera may
stand, how long a slide may be, how loud the music sits, how long filming takes, what a painting costs) are
worked out automatically by calculators in the kit, and a preflight command runs the right checks at each
stage of the work. Since version 1.4.0 a place built in Blender (a village, a town, a harbour, a mine, a farm, a garden,
an interior, a set or props) goes through a surface-and-wear pass and a construction check automatically, and a preflight
stage `place` fails when a material or the scene lacks them.

## Install

```
/plugin marketplace add AHepi/Music
/plugin install explainer-film@ahepi-music
```
Then, in the project's working folder: `explainer-film-setup /path/to/work/film-kit`
(copies the kit and installs its drawing engine; needs Node.js 18+, Python 3.10+ with numpy, Pillow
and opencv, ffmpeg, and a Chromium browser). Paid steps use the ElevenLabs (voice) and fal
(paintings) connectors, and always ask the user before spending.
Optional, only for drawing places on a rented graphics card: the person's own settings are read at run time from the
environment (`RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`, optionally `RENDER_STORE_FOLDER`, which is `/workspace` when not set) or
from a file named by `RENDER_SETTINGS_FILE` that sits outside any repository (lines `NAME=VALUE` with the same names; a JSON
file with those names as keys is read too). `explainer-film-place rent status` says which setting is missing. Never write them
in a file the plugin or a repository holds.

## How to use it

1. Read the `make-explainer-film` skill (it routes to the others) and the tips guide,
   `kit/docs/LLM tips and tricks.md`.
2. At each stage, run the preflight and fix what its report lists before moving on:
   `explainer-film-preflight STAGE`, where STAGE is `script` (before recording), `record` (after
   recording), `shots` (before building or drawing a place's views), `place` (after a place is built, before its views are
   drawn), `plates` (before paying for paintings), `paint` (after each painting arrives), `pages` (while building pages), `film` (before
   filming) or `finish` (after finishing): nine stages. Add `--project FILM_FOLDER`; name the film's files once in its
   `preflight-plan.json` (`explainer-film-preflight --example-plan`); `--list` names every stage's inputs and
   the tool that makes each. It spends nothing and changes no project file.
2b. For any place, set or props built in Blender, even when the request names no surfaces or wear, run the surface-and-wear
   pass first: `explainer-film-place finish`, then `explainer-film-place audit`, then `explainer-film-preflight place` (skill
   `surfaces-wear-and-construction`; `explainer-film-place roles --list` prints every role id). Nothing is drawn, rendered or
   painted until it passes. A small reminder hook (`hooks/`) prints these three lines at the start of a turn when the request is
   about building a place, a set or props, so the skill is read even when other Blender skills compete for the request.
3. Compute before you render: every calculator answers `--help`, prints a plain report and names the house
   numbers it used. What no tool can judge (history, what a detail reads as on a phone, newcomer
   understanding, story choices, the user's yes to spend) goes to the critics.

## What is inside

| Part | What it does |
|---|---|
| `skills/make-explainer-film` | The master steps, costs and rules, and which preflight stage goes with each step; start here. `house-rules.md`: how to talk to the user, money, notes, file names. |
| `skills/research-and-script` | Research ledger with sources, about three outlines, the script for the voice, and how to write it for newcomers. |
| `skills/check-facts` | Skeptical fact checking of spoken and on-screen claims (workflow `verify-facts`). |
| `skills/record-narration` | ElevenLabs recording page by page, word times, timeline, mix, voice checks. |
| `skills/paint-and-cut` | fal paintings, depth maps to make rooms with depth, cut-out pieces. |
| `skills/build-cinema-page` | Building a page file; `guide.md` is the full guide; `camera-and-framing.md` the strict camera rule (still, at most 3 named moves per shot), filling a tall frame and no clipping; parallel helpers via workflow `build-pages`. |
| `skills/make-3d-models` | Detailed models (buildings, a town, a desk, props) built in Blender by script, with the official Blender MCP server (set-up, client, and the modelling notes learned through it); EEVEE under a virtual screen. |
| `skills/build-and-paint-a-place` | A whole place built in Blender by script (Poly Haven models and surfaces, lettered props, people), each view planned by calculation (place facts, shot planner, lettering, light and smoke planners, model lint) and composed with the shot checker, the plate checked before paying, painted over, checked and lined up on arrival, and shone back onto the set in a page that holds or slides. |
| `skills/surfaces-wear-and-construction` | The finishing pass for every place, set or prop built in Blender: real normal maps and displacement, roughness and colour variation, dirt, grime, weathering, wetness, cracks, chips, edge wear, moss, rust, weeds, rubbish; every part carried and at real size; the place's art-style rule; the audit that proves it; fresh checkers; cheap Cycles on rented cards. Start with `SKILL.md`; the steps are in `the-required-steps.md`. |
| `skills/check-and-critique` | Stills, page turns, and an independent critique (workflow `critique-film`). |
| `skills/film-and-finish` | Filming in parallel stretches, sound, sendable copy, captions, cover, measurements. |
| `agents/` | `page-builder`, `fact-checker`, `film-critic`, `place-planner`, `place-builder`, `place-integrator`, `place-renderer`, `place-checker` (eight, all at medium effort unless the workflow raises it). |
| `workflows/` | `verify-facts`, `test-script-with-newcomers`, `critique-film`, `check-fixes`, `build-pages`, `build-a-place` (builds a place in parts with fresh checkers; run as `/explainer-film:NAME`, or with the Workflow tool). |
| `hooks/` | `hooks.json` and `place-reminder.py`: a prompt-time reminder (a `UserPromptSubmit` hook) that names the surface-and-wear skill and its three commands when a request is about building a place, a set or props in 3D; it prints nothing for any other request and never stops the person's work. |
| `bin/explainer-film-setup` | Sets up the kit in a working folder (on the PATH once installed); checks the browser, Blender and its virtual screen, the soundtrack and every kit file the skills name, and writes `machine-settings.env`. |
| `bin/explainer-film-place` | `explainer-film-place VERB`: the one door to the place kit (draft the settings, roles, surfaces, roads, wear, growth, `finish`, `audit`, construction and normal-map checks, renderer choice, rented-card client, picture measures). `--verbs` lists them. |
| `bin/explainer-film-preflight` | `explainer-film-preflight STAGE`: runs the checks for one stage (script, record, shots, place, plates, paint, pages, film, finish) and writes one report (on the PATH once installed). |
| Calculators (`kit/calculators/`) | Small tools that work out, from a new film's own files, what was found by trial: `frame_geometry.py` (where things land, sizes, reach, slides), `place_facts.py` (the standard facts of a place), `plan_shot.py` (camera, slide, plate and people before anything is drawn), `view_audit.py` (letter sizes, signs, landmark tops, heads), `plan_lights.py`, `plan_effects.py` (wind and smoke, contact shadows, fire), `paint_request.py` (the plate's preflight, the painter's prompt and price; never sends), `after_painting.py` (line-up, figures, style), `plan_states.py` (state pictures, cut or blend), `plan_page_timing.py` (reading times, pauses, word lookups, stills to check), `plan_budget.py` (money, filming time, workers, pieces, disk, pushes), `place_audit_check.py` (the verdict on a place's audit: treatments, layer amounts, normal maps, construction, scale, keep-out; and on a fresh checker's result) and `picture_measures.py` (value range, detail energy, flat windows, palette, squint, crops). Their guide is `kit/calculators/README.md`; tests: `python3 kit/calculators/tests/run_all.py`. |
| Place kit (`kit/place-kit/`) | Own work of the plugin, made generic from the project's texture, street, garden and mine work: roles, the seventeen treatments, surfaces, looks (kept, lived_in, neglected, derelict), wear layers, 3D plants and litter, construction and scale checks, the audit, the renderer choice and the rented-card client. `kit/place-kit/README.md` is its guide; `SOURCES-AND-LICENCES.md` says where each part came from. |
| House numbers (`kit/film-settings.json`) | One table of every number the tools share, each marked measured, judged or invented with its source; prices carry the date they were read. Change numbers only here (`kit/calculators/settings.py`). The place kit's numbers are in the sections named `place_...`. |
| Tips guide (`kit/docs/LLM tips and tricks.md`) | The short rules for a model making the next film, grouped by stage, each naming the tool that checks it or saying "ask a critic"; the numbers to know; the people test's lessons; money; the traps that cost the most rounds; what only critics can judge. |
| Checking tools | `paper-film/tools/camera_audit.py` (measures every camera move per shot; `--timeline` finds the page's window, `--built-set` checks a built-and-painted slide), `frame_check.py` (where things land in the frame for a camera, before rendering), `check-shot.sh` (the shot checker: measures a Blender shot against the composing rules and says what to change, in metres; reads a view's kinds of shot and accepted problems), `page_events.mjs` and `check_page_layout.mjs` (what every page draws, frame by frame, without filming; pops, held shots, overlaps), `find_jumps.py` (sudden jumps in a finished film), `tone_piece.py` (calms an over-coloured cut-out), `room.clearance()` and `boxesOverlap()` in the engine (nothing passing through anything); in `paper-film/blender/`, `make_check_file.py` (a view's check file measured from the scene) and `model_lint.py` (stripes, same-plane faces, names, glass, sizes); in `narration-tools/`, `lint_script.py` (the script before recording, the recordings after) and `sound_gates.py` (length, loudness, alignment, music under the voice), which the mix and finish scripts call. |
| `kit/` | The film kit: `paper-film/` (stage, scenes, tools, templates, Blender scripts), `narration-tools/`, `examples/` (word timelines of chapters 1 and 2, the estimated timeline of chapter 2 for newcomers, check files of the built places), `docs/` (the full how-to; start with `paper-look - 00 START HERE.md`). `kit-sync-notes.md` says when it was last brought up to date with the austerity project's film kit and what waits. |

The kit holds code and timelines, not pictures, sound or models: a chapter's paintings, cut-outs,
recordings and Blender models stay in its own project (the austerity explainer keeps them in
`austerity-explainer/film-kit/` and `austerity-explainer/chapter-2-inflation/`).

## A concrete example

In chapter 2 the narrator says "and prices climb" at 66.98 seconds. Page 3's file asks for
`kit.at('climb')` and at that moment a flip counter on a card factory flips £1.25 → £1.60 → £2.00,
coins stack beside it, and a red label PRICES CLIMB points at the counter. The whole film is timed
to spoken words like that.

## Changes

**1.4.0 (22 October 2026): places that look lived in, automatically.**
- New skill `surfaces-wear-and-construction`: the finishing pass for every place, set or prop built in Blender (real normal
  maps and displacement, roughness and colour variation, dirt, grime, weathering, wetness, cracks, chips, edge wear, moss,
  rust, weeds, rubbish, damage as shape, believable construction, real sizes, the style rule). The skills a model reads first
  (`make-3d-models`, `build-and-paint-a-place`, `make-explainer-film`) now make the pass and the construction check required
  steps, and their descriptions carry the words so they are picked even when the request names no surfaces.
- New command `explainer-film-place VERB` (the verbs are listed by `--verbs`) and the place kit behind it (`kit/place-kit/`).
- New preflight stage `place` (nine stages now) and new `place_...` house numbers in `film-settings.json`; the plates stage
  refuses a paid painting when its audit fails; it knows the scene from `--blend` or from the `scene_file` its check file records
  (the shot-check files the kit makes now record it), and with no scene named it says, as a LOOK, that no audit could be required.
- New calculators `place_audit_check.py` and `picture_measures.py`.
- New workflow `build-a-place` (builds a place in parts, with fresh checkers) and five agents (`place-planner`, `place-builder`,
  `place-integrator`, `place-renderer`, `place-checker`).
- New: `model_lint.py --surfaces` (flat models without normal maps or roughness variation); `model_kit.py` and `textures.py`
  run inside Blender's own Python without Pillow.
- Conflicts settled in the skills: displacement and a normal map together (displacement only where the role says, normal
  strength x 0.6), the Cycles rule (Cycles where lights are lit), the painter template's words for wet places, glTF having no
  displacement (true for the card route only).
- A prompt-time reminder hook (`hooks/hooks.json`, `hooks/place-reminder.py`): when a request is about building a place, a set or
  props, it prints the three lines (the skill to read, the three commands) at the start of the turn.
- Fix round (23 October 2026), after a first full check built a canal lock with the plugin alone and a second check read the code
  and docs: an object with no material at all can no longer pass the audit; a lane drawn as a separate curved strip keeps its
  outline when its ground is made fine, and a road is drafted for every road-role object; curves, text, metaballs and instanced
  collections are turned into meshes so nothing drawn escapes the pass; `finish-part` ends cleanly for a part; the ground part may
  make the cameras, lights and world; the ground-seat, joinery, mirrored-wall, turned-wall, step, boat-afloat and sun checks stopped
  failing correct work; `undo` works after the kit added the sun; a material that carries its own picture gets roughness variation
  and a normal map without losing its picture; a plain sky and teal water no longer fail the picture measures, and one guard file
  holds a guard per view; the rented-card client never prints the endpoint id, reads `NAME=VALUE` lines and JSON, and sends Cycles
  previews to the card; a close-up is saved once as `closeup`, not `closeup_closeup`; a role id for steps (`stone.step`),
  `roles --list`, better name hints, damp ground near water, and the docs say what the kit does not make (a tide line, reeds).
  The faults each have a test that also shows the old behaviour (`test_place_fixes.py`).
- NOT tested, said plainly: a real village of hundreds of buildings (only a hut, a 36 by 26 m yard, small test scenes and a 12 m
  canal lock were run; the wear masks are numpy-only and were timed at hut and yard size); Cycles with the kit on a village-size
  place; the rented-card client against a real endpoint (its tests use a pretend card; one real card job was run by hand through
  the project's own client, not through this one); the blind reading test; the workflow `build-a-place` and its agents under the
  real Workflow tool (they ran only against canned helpers); that a smaller model, asked only for "a village in the forest", loads
  the skill by itself (the new hook should help, and its format was written from Claude Code's documented plugin hook form but was not
  run inside Claude Code here). The tests prove the gates work, not that a village looks good: fresh checkers and the person's own
  eyes judge that.

**1.3.0 (16 October 2026): calculations instead of searches.**
- New: calculators in `kit/calculators/` that work out what used to be found by trial, each tested on the
  austerity project's recorded cases (and on the checkout, a place the rules were not built from). One
  table of house numbers, `kit/film-settings.json`, each marked measured, judged or invented.
- New: `explainer-film-preflight STAGE`, one report of the right checks at each of eight stages.
- New: the tips guide for models, `kit/docs/LLM tips and tricks.md`.
- New tools in the kit: `page_events.mjs` and `check_page_layout.mjs` (pages checked frame by frame without
  filming), `make_check_file.py` and `model_lint.py` (Blender), `lint_script.py` and `sound_gates.py`
  (narration and sound), and two new modes of `camera_audit.py` (`--timeline`, `--built-set`).
- The shot checker reads a view's kinds of shot (still life, crowd, overview, interior, dark subject) and
  an `accepted` list of problems the project chose to keep, and reports those as known.
- The mix and finish scripts now stop on a FAIL line when the sound is the wrong length, too loud or out of
  line. `finish_film.sh` takes the timeline as a 6th argument; without it, it makes the files but ends with
  exit 3 (the alignment was not checked). `check-shot.sh` now needs `BLEND` to be named.
- The kit was brought up to date with the austerity project's film kit (the built-and-painted look, the
  newcomer chapter's pages, the people test), with the new skill `build-and-paint-a-place`; the setup
  command checks Blender, the virtual screen and the soundtrack and writes `machine-settings.env`.
- The skills now call the calculators and the preflight at the right moments instead of describing hand
  searches.

**1.2.0** (15 October 2026): writing for newcomers and the workflow `test-script-with-newcomers`.
**1.1.x** (13 October 2026): the official Blender MCP server notes, the camera tools, fixes to the test page.
**1.0.0** (12 October 2026): the first version: skills, agents, workflows and the film kit.
