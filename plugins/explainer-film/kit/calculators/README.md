# Calculators: the hand-found numbers, worked out automatically

What this folder is: small tools that work out, from a new film's own files, the numbers this project found by trial
and error over 35 logs. Examples are where a prop lands on the phone frame, how far away the camera may stand, how
long a slide may be before the painting goes soft, and which composing rules apply to a crowd. Each tool says which
house numbers it used. All the house numbers live in one table, `kit/film-settings.json`.

Run every test: `python3 kit/calculators/tests/run_all.py` (plain Python 3 with numpy, OpenCV and Pillow; node for
the JavaScript twin; no pytest). Every tool answers `--help`.

## The core (built)

Every other calculator builds on these.

| File | What it is for |
|---|---|
| `../film-settings.json` | One table of every house number (344 entries in 21 sections: frame, camera, composing, safe area, lettering, people, light, effects, state pictures, painting, timing, sound, filming, money, delivery, models, checking, script, page graphics, the paper look, shot-kind profiles). Each entry has a `value`, `unit`, `kind` and `source`. The kind is **measured**, **judged** or **invented**, which tells you whether you may change it and how. Prices carry the date they were read. |
| `settings.py` | Reads the table. `settings.value('frame.width_pixels')` gives a value. A misspelt key stops with the nearest real names. It records every value a tool reads, so the tool's report can list them. `python3 settings.py show SECTION`, `get KEY`, `check`, `profile crowd dark_subject`. `resolve_profile()` gives the composing rules for a view's kinds of shot, and `judge()` judges a measured number against one rule. |
| `frame_geometry.py` | The camera sums, done once. It says where a point lands on the frame or the plate, sizes in pixels, metres per pixel, where a street's lines meet, and the reach (how far away a thing may stand and still land at a given "down"). It also gives the eye height needed, what a turn or a sideways slide moves, parallax, the slide-magnification limit (from the painting's **returned** height, 2672 rows, so 1.29 rather than 1.314) measured at the nearest painted surface, the turn and sideways allowance inside the plate, and whole boxes against the phone-button margins. Commands: `project`, `boxes`, `meeting-point`, `size`, `reach`, `eye`, `turn`, `slide`, `parallax`, `allowance`. |
| `../paper-film/scenes/frame-geometry.js` | The same sums for page files (no three.js needed; it also takes a three.js camera). A parity test proves it gives the same numbers as the Python on 2,358 cases. |
| `place_facts_schema.json`, `place_facts.py` | The standard **place facts** file every place's assemble script should write. It holds views (camera spots, turn, lenses, slide, subject, kind of shot), signs (centre, facing, letter height, words, must-read), emitters (chimney mouths, fires), figures (feet, facing, height), lights (place, target, watts, linking), landmark tops, support surfaces (road, pavement, floor, counter) and an **accepted** list (rule, view, reason, who, date) of exceptions the project chose to keep. `place_facts.py check FILE` checks one. The converters `from-works`, `from-notice-corner` and `from-people-test` build one from the files the project already has, and `from-shot-facts` builds one for any place measured by shot_facts.py. |
| `calculator_output.py` | The shared ending of every calculator: the plain report, the settings it used, and `--json`, `--out` and `--report`. |
| `tests/` | `run_all.py` runs every `test_*.py` (builders add theirs just by naming them so). `checks.py` is the shared helper. Each line prints the number got, the number recorded, where it is recorded, and what the check proves or only repeats. `fixtures/` holds small JSON copies from the project. `fixtures/sources.json` says where each came from. |

### Shot-kind profiles (in film-settings.json)

The notice corner's rules were measured on one still life. The Works' accepted round 5 views break them, so each view
now names its **kinds of shot**, and the profile relaxes only what that kind of shot needs. The loosest wins when a
view names several.

- **still_life**: the base, from the picture the user liked (log 30).
- **crowd**: a story box up to 0.80 wide. Rule 4 is off between figures and replaced by head spacing. Story things may cover 2% of the bottom-left. A dark band replaces "titles in sky".
- **overview**: a wider eye range. A fill prop (a handcart) may make the 0.70 reach. Wider limits for the box, the story spread and the quiet side.
- **interior**: props rest on declared surfaces (a counter), not the street. The ceiling is the dim top. Eye 1.5 to 1.7 m. This one is provisional: it comes from checkout C1, which is not yet accepted.
- **dark_subject**: the "subject brightest" and "lit from below" tests are off. A silhouette contrast of at least 2.2 replaces them. An opening counts as the subject's outline for rule 1.

There is also a written order for when rules conflict (camera first; the quiet side's weight last).

## All 17 calculators of the design (log 35)

| # | Calculator | File(s) | State |
|---|---|---|---|
| 0 | Frame geometry core and shared film settings (plus place facts and shot-kind profiles) | `frame_geometry.py`, `frame-geometry.js`, `film-settings.json`, `settings.py`, `place_facts.py` | **built** |
| 1 | Check file generator: writes a view's shot-check file from the Blender scene | `paper-film/blender/make_check_file.py` | **built** |
| 2 | Shot planner: the camera, slide, plate and people before anything is drawn | `calculators/plan_shot.py` (`paper-film/blender/solve_shot.py` not built) | **built** (plus the shot checker's `kind_of_shot` and `accepted`) |
| 3 | Camera path audit for moving shots (no turn during a slide, plate coverage) | `paper-film/tools/camera_audit.py` (extended: `--built-set`, `--timeline`) | **built** (relief mode not built) |
| 4 | Lettering, figure and landmark audit per view | `calculators/view_audit.py` | **built** |
| 5 | Light planner and tuner | `calculators/plan_lights.py` (+ `paper-film/blender/set_measurements.py`; `tune_lights.py` not built) | **built** (the planner; the tuner left for later) |
| 6 | Painter's request builder and plate preflight (prompt, pictures, price) | `calculators/paint_request.py` (+ `templates/`) | **built** |
| 7 | Painting arrival checks (line-up, kept shadows, figure outlines, colour) | `calculators/after_painting.py` | **built** |
| 8 | State picture planner (every helper plate, cut or blend) | `calculators/plan_states.py` | **built** |
| 9 | Effects planner (wind, smoke traces, fire, dust, contact shadows) | `calculators/plan_effects.py` (+ `paper-film/blender/set_measurements.py`) | **built** (dust placement left for later) |
| 10 | Script and narration gate (lint, estimated timeline, cost) | `narration-tools/lint_script.py` | being built |
| 11 | Page timing and words-on-screen planner | `calculators/plan_page_timing.py` (+ `paper-film/tools/page_events.mjs`) | **built** |
| 12 | Page pose sampler (slim: pops, effects, held shots, overlaps) | `paper-film/tools/check_page_layout.mjs` | **built** |
| 13 | Sound calculator and gates | `narration-tools/sound_gates.py` | being built |
| 14 | Budget, filming time, memory and disk planner | `calculators/plan_budget.py` | being built |
| 15 | Model lint (Blender and .glb) | `paper-film/blender/model_lint.py` | **built** |
| 16 | Preflight runner, report and kit sync | `calculators/preflight.py` (+ `bin/explainer-film-preflight`) | being built |

## The shot planner (built)

`plan_shot.py` plans a shot from a place's **place facts** and a short **shot list** (subject, story things, kind of shot;
the format is in the file's note), before anything is built, drawn or painted. Pure geometry with the core's sums.

- **Plan** (`"camera": {"plan": true}` or `--view NAME --plan`): stand in line with the subject's or its support's near edge
  (rule 1), a standing eye above the surface under the camera (rule 2), as far back as the nearest story thing still reaches
  0.72 down (rule 7 plus a 0.02 margin), turn so the lines meet where wanted, then slide sideways (never turn) to clear the
  phone buttons (rule 12). An overview raises the eye instead, never tilts. The slide starts back toward the subject's middle,
  level. A `crowd_layout` proposes a loose crowd two deep across the view; `turn_toward` turns a prop's stored front axis at a target.
- **Judge** (the view as built, `--at x,y,z` for another spot, or a shot list): predicts what the shot checker will measure
  (the lines' meeting point and the gap, the eye, the reach, right edges, the story box, the main rule's spots, the subject's
  share, work props, the bottom-left quarter), the people (backs turned at 6 m or more from every camera place along the
  slide; a face that shows gets the painter's "face lost in shadow" words and a skin check, **never a silhouette**; a crowd's
  long axis at least 60 degrees to every view that sees it; two deep; shoulders 0.3-0.5 m apart; heads a head width apart),
  the signs' facing, the slide's magnification at the nearest painted thing, and the plate's lens and rows. Every failure
  says by how much, in metres.
- Verdicts: **fail**, **known** (in the place's accepted list), **look** (a box estimate past its limit, or a judgement:
  confirm with the shot checker), **pass**, **info**. Upright boxes over-estimate extents, so a box failing a "max" limit
  is a look, not a fail.
- Tested on the Works (round 4's spot fails at 0.653 and asks for 2.2 m nearer; round 5's passes; round 3's and 4's single
  file fails the crowd rule), the notice corner, the people test, and checkout C1 as a hold-out (`tests/test_plan_shot.py`).

**The shot checker's new check-file keys** (`paper-film/tools/check_shot.py`, plugin kit only): `"kind_of_shot"` applies
the shot-kind profiles (a rule switched off or loosened is listed under "Known and allowed"; a crowd's rule 4 between
figures is replaced by heads apart and every figure half seen, for the groups in `"figures"`; a dark subject's brightness
tests by its outline against the light round it); `"accepted"` lists problems the project chose to keep (rule, things,
reason, who, date, measured), reported as known unless they have grown past what was accepted. Without either key the report
is word for word the same as before (`tests/test_check_shot_kinds.py` proves it on a box world and, when the project's files
are present, on the notice corner and W1). With either key a `known.json` is written for other tools.

## Views and models (built)

Three tools, their house numbers in `film-settings.json` section `views_and_models`.

- **`view_audit.py`** (plain Python, from a place facts file). For every view it gives:
  - every sign's letter height in pixels. Turning a board sideways narrows its letters; tipping it shortens them (WAGES lying flat: 1.4 px). Words the page needs fail under 20 px and warn under 25 px, with the letter size that would reach them.
  - the drums' best turn toward every camera that reads them.
  - readable signs the page never says aloud. Loudness is letter pixels times letter brightness, against the least legible named sign that still reads; the limit, 0.55, was set on BANK. The tool gives the dim needed.
  - backs of signs that show, and landmark tops in or just under the words band.
  - each figure: head pixels, whether its face can show, how near it stands.
  - continuity counts by view and state.
  - with `title-contrast`: the dark band a title needs on a still.

  Tested in `tests/test_view_audit.py` (55 checks). It reproduces the Works' letter sizes and round 2-5's lettering, BANK, chimney and board findings. Hold-outs: Blender's own frame boxes for 37 men, the people test's figure heights (within 6% of the masks), and the checkout helper's letter sizes.
- **`paper-film/blender/make_check_file.py`** (inside Blender, after a place's assemble script). It writes a view's check file. The story choices (subject, support, story, work, groups the author merges, splits or adds) come from a short shot list. It measures the rest from the scene:
  - groups: one per prop root, one per figure, loose parts joined to their prop, only those in the frame.
  - must_read (from lettering materials) and pairs_also.
  - on_ground and stands_on, from rays down from each group's lowest points; indoors only on a declared floor, never on a counter.
  - light props: story groups whose own surface glows over 15% (the lantern 21-23%, the brazier 6-11%).
  - from the view's shot-kind profile: the eye range, rule 7 and the sky.
  - a title zone that is sky, or `"band": true`.
  - the keys check_shot reads: `kind_of_shot`, `figures`, `support_surfaces`, `accepted`.
  - `match_excludes` (dark, thin, lettered and repeated figures), for the next checker.

  It rebuilt every group of the hand-made notice corner (15), W1 (17), W3 (18) and checkout C1 (14) files, with the same roles. It added facts the hand files missed (the lantern stands on DIESEL's lid; W3's drums belong in must_read). Tested in `tests/test_make_check_file.py`.
- **`paper-film/blender/model_lint.py`** (.glb files with plain Python, or the open Blender scene). It finds:
  - stripes, with round 3's find_stripes.py thresholds: 15, 27, 33 parts in round 3; 0 in round 4, except the lane's four roofs.
  - surfaces on one plane, and floors just over another ground (round 2's yards).
  - copy-numbered roots (round 1's eight props).
  - glass whose see-through comes from its picture (log 32's lamps).
  - glows with light bases.
  - index sizes against the saved model (round 1's jacket).
  - fronts. `--write-index` writes measured sizes and fronts into a copy of the index.

  Tested in `tests/test_model_lint.py` (24 checks; parts B and C use the project's git history and Blender when they are on the machine).

## Painting tools (built)

Three tools for the paid painting step and the pictures a held shot cuts to. Their numbers are in `film-settings.json`
section `painting_tools`; they share `painting_measures.py` (loading a view as the shot checker does, figure and skin
measures, the stage's colour finish ported from cinema-stage.js, and running the kit's own align, shadow and state tools).
Nothing here spends money: a paid step still needs the user's yes.

- **`paint_request.py`** (before paying). `preflight` checks the plate: render faults and the light rules (it refuses a
  request without a render log and a shot report), thin parts, lettering, even bright discs and black holes in the set
  (log 32's doorway), a glow inside a hollow prop's top (lesson 138: over 2% of the top twice as bright as the prop's body),
  heads paler than coats, cloth the film's finish turns red (round 2's 26/1/0), figures barely darker than their surround,
  figures casting long shadows (lesson 135, with the plate drawn without them), real people's names. `prompt` writes the
  main and behind prompts from `templates/paint-prompt.txt` and `behind-prompt.txt`: the parts it names (which groups,
  their order, where warm light stays, thin parts, near pairs, how many people near and far and which way they face, no
  faces when a head is over 24 px, the behind painting's near list from the slide's parallax) are measured; the words
  for each thing are a person's (check file `paint_as`, a short brief). `price`: the dated rate times the megapixels
  returned and sent, an estimate until `fit-price` fits it to real fal charges. `request` does all of it and writes the
  request file (and a planned ledger entry); it never sends.
  Tested in `tests/test_paint_request.py`: it rebuilds the notice corner's and the people test's prompts (warm-light
  sentence word for word; the five thin parts, the near pairs, the people counts; it corrects the ledger's "six" far
  walkers to the five that show), fails the people test plate on lesson 138 and 135, round 2's plate on red coats, the
  notice corner's plates 1 and 2 on the lit drum lining and the black doorway, and passes plate 3, which was painted. Hold-out:
  W1's plate (round 5): seven men from behind, no long shadows; it predicts W1's brazier top (15% lit) would be painted
  as a band.
- **`after_painting.py`** (when a painting comes back). Resizes to the plate (Lanczos, as the ledgers did), always lines
  it up (fails only under 0.85, at the edge of the search, or with no gain on a painting that does not sit on its outlines),
  checks each figure's outline against its own plate baseline (within 0.05), person-sized dark shapes the plate does not
  have, each figure's darkness against its surround (people test: 0.15 to 0.50, a must-fix), skin added on heads, the style
  against the standard painting (warnings), and the behind painting: lined up against the painting, painted shadows kept
  round near props (ground beside them within 2 levels), leaving people's shadows gone. Writes PNG only.
  Tested in `tests/test_after_painting.py` on the real paintings: it reproduces both ledgers' line-ups exactly (people
  test 0.874 to 0.903 at 1.0010, +1, +0.5, pixel for pixel the film kit's painting; notice corner 0.70 to 0.96 and the behind
  painting's 0.990 to 0.991), the figures helper's outline numbers within 0.004, flags walkers 4 and 5 (the two real changes)
  and none of the five near men, the men's lift to 0.47-0.51, and the shadows left in the people-out painting.
- **`plan_states.py`** (for held shots that change on a word). From a page plan of state changes and the place facts: every
  plate (one per view and state, plus a behind plate for a slide past people), errors for a change inside a slide and for
  two sub-changes on one plate (round 4's slowed plate), warnings for people-only changes (lesson 136), a cue in the words
  band, and busy states; with `--measure`, the swap share on the plates (a time cut up to 0.12 of the frame, else the
  stepped blend, 0.8 s in 3 steps), the long-shadow ratio and the thresholds from the plates' noise; then the exact
  make_state_picture.py and make_behind_picture.py commands. Tested in `tests/test_plan_states.py` on the Works' pages
  3, 4 and 12 (it finds the windows-only slowed plate round 4 said was missing) and the people test (42.3%, 5.6 times the
  people's outlines).

## Page timing (built)

Three tools, their house numbers in `film-settings.json` section `page_timing`.

- **`paper-film/tools/page_events.mjs`** runs a cinema chapter in the stage without filming it and writes, 30 times a
  second, everything the pages do: every word lookup (with every time that word is said), each shot and slide, every flat
  graphic (words, labels, cards, rings, tags, arrows) with its box in pixels and how visible it is, the held-shot value,
  the live things (marked with `kit.moving`) and the joins. `graphics.js` and `cinema-kit.js` note these only when the tool
  switches the notes on; filming never does, and stills drawn with the notes on and off (and with the film kit's files
  from before the notes) are the same byte for byte. Pages 3 to 5 of chapter 2 for newcomers take about 2.5 minutes and
  about 2 GB; old chapter 2 takes 12 seconds. `--pages 3,4,5`, `--from/--to`, `--serve /assets=DIR` (a film's assets kept
  elsewhere), `--render-stills DIR T...`. It also draws some moments again out of order to catch an effect left on from
  an earlier frame (lesson 29).
- **`plan_page_timing.py check EVENTS.json`** works out, from the events: lookups that leave out which time a word said
  more than once is meant (lessons 12, 28, 46); the pause each page needs (its join's wait + length + 0.15 s, plus a
  guess ring's 4 s hold; clamped to 1.1-1.7 s only for a plain peel), as `--pauses` for assemble_chapter_narration.py and
  `--pause-after` for estimate_timeline.py; run-on joins between the same view; how long each group of words is readable
  before it goes or the picture cuts (at least 1 s; a conclusion 1.2 s), with the appear delay of each kind read from
  graphics.js and the earlier word of the sentence that would fix it; words that fade a frame before a cut; a new line
  over a fading one; margins (65 and 972 px, letter tops 0.06 down, nothing to read below 0.80); every typed word against
  the narration; numbers against a research ledger and counts that land on their spoken number and hold still; word
  groups per page; slides on words; stretches where nothing changes; the stills to check, in one run; and the planned cuts
  for find_jumps.py. `lookups TIMELINE PAGE.js:N` reads lookups from page files with no browser; `refilm OLD NEW --chunks`
  lists the filmed chunks to film again after a re-record; `delays` prints graphics.js's appear delays.
- **`paper-film/tools/check_page_layout.mjs EVENTS.json`** (the skeptic's slim pose sampler): pops (something that comes
  or goes in two frames or fewer, or jumps across the frame, away from a planned cut), effects that come out different
  drawn out of order or are shared between pages, held-shot keys while the camera moves and state changes during a move,
  holds without a held-shot key (about five times slower), and drawn things in the same place at each event.

Tested in `tests/test_plan_page_timing.py` (57 checks), `tests/test_check_page_layout.py` (10) and
`tests/test_page_events.py` (13, needs a browser). They reproduce, on pages 3 to 5: MACHINES readable 0.84 s (round 5:
about 0.85) and 0.40 s with the usual wait (round 4 measured about 0.4 on the film); → PRICES UP 1.05 s at full strength
and up 1.19 s before the cut, and round 3's version on "up" failing at 0.53 s and 0.68 s; the 29 typed lines with nothing
unsaid; MOST ECONOMISTS AGREE 0.061 down; the 4.0 s and 3.0 s pauses the design's clamp would have cut. Hold-outs:
the six typed lines' boxes against round 4's filmed stills (within 3.4 px), the six jumps find_jumps.py measured on the
round 4 film all among the planned cuts, the round 4 helpers' hand-picked stills (53 of 56 event moments covered), old
chapter 2's page 10 before its critique (5.6% held 0.01 s, lesson 53) and after (1.35 s), and old chapter 2's numbers
against the fact recheck.

## Script, sound and budget (built)

- **`narration-tools/lint_script.py before SCRIPT.json --word-times EARLIER.json`** stops a script before any credits
  are spent: the one cue on every page, no capitals, names in their sound spelling, sentences (mean at most 12 words,
  none over 20), spoken figures a minute of speech (at most 6: the recorded chapter 2 had 8.1 by its count, the
  newcomer script 3.6), the main rule said twice word for word, a page marked `"key": true` no faster than the
  median page, out-of-date ledger facts. It fills the 4 s guess holds from the text, makes the estimated timeline
  with `estimate_timeline.py` (each chapter's speech predicted from the OTHER chapter's recording within 1.2%) and
  prices the credits. `after` checks the recordings: a cue read aloud (each cue word over 0.2 s), words that differ,
  names heard wrongly, each "..." (chapter 2's left 0.08-0.45 s of silence), words placed late after a pause.
- **`narration-tools/sound_gates.py`** measures the sound and stops the step that got it wrong: `length` (0.05 s),
  `loudness` (the encoded file: -15 LUFS +/- 0.5, -14 for music only, true peak at most -1 dBTP), `alignment`
  (2 ms), `gaps` and `duck` (the music 18 dB under the voice while she speaks, found for any soundtrack in two
  passes), `voice` (page pitch and spread), `mouth`, `music-start`. The mix scripts, `finish_film.sh` and
  `add_music_bed.sh` call it as gates.
- **`plan_budget.py`** prices paid steps (megapixels returned and sent; credits), keeps the spend ledger against the
  allowance from its start date (refusing a larger step), and plans filming from frame kinds read in the page events,
  priced by a short profile filmed first (rounds 3, 4 and 5 of pages 3-5 predicted within about 5% from 8 stretches;
  the round 4 table alone missed round 5 by 52%): workers, piece size, lazy loading, memory, disk, stretches under
  2 hours with their FILM_FROM/FILM_TO commands, a push check and a filming status.

## For a builder adding a calculator

- Start the file with a plain note: "What this does: ...". Use full plain-word names. Give it `--help` through argparse, and end with `calculator_output.finish(...)` so the report names its settings. `tests/test_house_rules.py` checks the note and the `--help`.
- Read every house number from `film-settings.json` through `settings.py`. Add your own section with an `"about"` line, and mark each number measured, judged or invented. Do not change another section's numbers without saying so in your report. `tests/test_settings.py` catches a tool that keeps its own copy of a number and lets it drift.
- Read places from **place facts**, not from one place's one-off keys. Read a view's rules with `resolve_profile(settings, view['kind_of_shot'])`. Report an entry in the place's `accepted` list as known, not as a failure.
- Write `tests/test_YOURTOOL.py`. Reproduce the project's recorded cases and give each number's source. Add a hold-out case where you can (checkout C1, the people test). Say plainly when a check only repeats the sum it came from.
- Fixtures must stay small (under 1 MB each; no pictures or models). Add each one to `tests/fixtures/sources.json`.

## Tips for a model using these tools

- Never guess where something lands or how big it comes out: `frame_geometry.py project` or `boxes` answers in a second, before any render. Then let the shot checker confirm on the render. Boxes are upright, so a turned thing comes out a little wider than it renders.
- Measure reach above the surface a thing stands on (the counter, not the floor). On a level street the lines meet at 0.5 down. A turn moves everything together; a sideways slide moves near things more. Close a gap by sliding, never by turning.
- A slide magnifies the **nearest painted** thing most (the notice corner's pail 1.45x, against 1.30x for the notice). Check the slide with `frame_geometry.py slide`, using the painter's returned height.
- Before failing a view, read its kinds of shot and its accepted list. The Works' crowd, dark gates and title band are profile matters. A petrol drum in the bottom-left is not.
- Treat an **invented** number as a guess, and say so whenever a result rests on it.
- Plan the camera with `plan_shot.py` before building a view, and judge it again before rendering: the reach, the 6 m rule,
  the crowd's axis and the slide's limit are sums, not tries. A "look" means: confirm with the shot checker on the render.
- Never answer a face that shows with a black silhouette (lesson 137). Turn the figure away, or keep it and give the painter
  "face lost in shadow"; check the head for skin pixels after painting.
- Put a view's kinds of shot and its accepted problems in its check file (`kind_of_shot`, `figures`, `accepted`), so the
  checker reports a kept shot as known instead of failing it every time.

- Before painting, run `view_audit.py audit` on the place facts with the page's narration (`--timeline --page`). A word the
  page needs under 20 px will not read on a phone. A readable sign the page never says is read first. Dim it to the value
  the tool gives, or take it out of frame.
- Write a view's check file with `make_check_file.py` after the assemble script. Write by hand only the shot list: the
  story roles, and the groups you merge, split or add. Never hand-list must_read, pairs_also or on_ground: those are the
  lists the hand-made files got wrong.
- Run `model_lint.py` on every model you build or download, and on the dressed scene, before any plate. A stripe, a
  floor 2 cm over the ground, or glass reading its picture's alpha costs a repaint once painted.
- Before any paid painting, run `paint_request.py request` with the render log and the shot report. Fix every preflight
  failure in 3D, not in the prompt: the painter copies the plate's light and dark, lifts a glowing hollow into a band,
  reads a black opening as open, smears thin parts and leaves people's long shadows. Write each story prop's `paint_as`
  words (what it is, its colour, its state, what it must not become); never write the rest of the prompt by hand.
- Say every person in the prompt: how many, near or far, which way they face. Far walkers are "flat dark shapes with no
  pale spots"; a facing man's face is "lost in deep shadow under the cap, no lit cheek"; "keep the figures as dark as in
  image 1". Never let the painter letter anything: signs stay on their own surfaces.
- Quote the price as an estimate (rate x megapixels out and in, dated) until real fal charges have been fitted with
  `paint_request.py fit-price`. Ask the user before every paid call.
- Run `after_painting.py check` on every painting as it arrives, before anything uses it, and keep the PNG it writes.
  A painting that only passes because its outlines were already near is fine; one at the edge of the search was moved
  further than the tool looks. Figures painted paler than in the plate turn mid-grey on a phone: darken them back.
- Plan held-shot changes with `plan_states.py` before rendering helper plates: one plate per change spoken on its own word,
  the behind plate in the main state with only the near people left out, nothing changing during a slide, and something
  besides the people changing at a cut. People who come and go cast no long shadows (a soft patch at their feet).

- Before filming any page, run `page_events.mjs` on it and then `plan_page_timing.py check` and `check_page_layout.mjs` on
  the events. Never pick still times by eye: use the stills command it prints (space-separated, one run so page turns are
  right), and hand find_jumps.py the planned cuts it prints. Run them again on the real timeline once the narration is in.
- Always give `kit.at('word', n)` the time it is said when the word is said more than once on the page, even when you mean
  the first: a later script edit can move "the first".
- Write a page's holds into its `join.after` (and the timeline's pause), never as seconds in the page. Use the pause the
  tool prints: a run-on inside a guess hold needs the hold, not the 1.1-1.7 s of a plain peel.
- A label that is up for under a second before a cut cannot be read: bring its words in with the line (`wordsWithLine`),
  start it on an earlier word of its sentence, or move the cut. A conclusion starts on the first word of its clause.
- Anything that ends on a cut gets `fadeOut: 0`. A new line in the same place starts only after the old one has gone.
- Return `still: false` while the camera moves and a held-shot key whenever it holds; set every effect from the moment
  alone, never leave it on from an earlier frame.

## Not done yet (the core's part)

- The kit's tools still keep their own copies of house numbers (check_shot.py, frame_check.py, the timeline tools and the mix scripts). `test_settings.py` compares 74 such copies with the table. Two differ: estimate_timeline.py's 1.5 s default pause (the table says 1.4) and frame_check.py's 140 px margins (0.87 across, against 0.90). Making each tool read the table belongs to whoever next changes that tool.
- The Works' place facts have an empty accepted list. The round 5 final checks list 13 to 29 problems per view that nobody has marked accepted or fixed. The profiles cover the systematic ones. `test_shot_kind_profiles.py` prints the rest, view by view.
- A judgement for a person: the painted ground at the frame's bottom edge comes nearer than any prop during a slide (W1 1.41 times, the notice corner about 1.53, against the painting's 1.29). If the ground counts as "the nearest painted surface", every slide made so far is too long, yet the user kept the notice corner. `frame_geometry.py slide` shows the ground but counts it only with `--count-ground`.
- The crowd, overview and interior profiles come from views the user has not yet seen. Their limits are marked judged and should be checked again once the user has judged those views.

## The effects planner, the light planner and the camera audit's built-set mode (built)

- **`plan_effects.py`** (effects; settings section `effects_planner`). `wind` picks the wind most across every view that
  sees a chimney, traces both signs with ChimneySmoke's own sums, and keeps the sign that passes everywhere. For each
  plume and view it gives the travel while seen (at least 0.15 of the width), the puffs' **top edges** against word cards
  (the skeptic's test), the fade before another factory's chimney, thick smoke over a figure, and which emitters to drop
  (a plume that never enters, or whose chimney is out of the held frame). `colour` measures the plume against the sky on
  the plate (not much lighter, but a different colour) and the mouth against the chimney top. `contact-shadows` sizes a
  shadow from a prop's measured base. `window-change` checks a teaching event changes the windows by 15 levels. `fire`
  checks the glow's pulse and the flames' variety. `lint` checks paper pages make every effect through `kit.effect`.
- **`plan_lights.py`** (lights; settings section `light_planner`). `plan` works light by light: role, which few cast
  shadows, starting watts by the inverse square from the subject's own light, reach from Blender ray hits (or the place
  facts' boxes), cones, links (its housing; the props round a fire), lamps that land on the subject or where the lines
  meet, lights behind the camera that flood the near ground, a lamp lighting the face it hangs on, how much light the
  subject gets against its key (a burnt-out risk), and a plan for a **dark subject** (light behind it; judge it by
  silhouette contrast). `contrast` measures that contrast the people test's way. `exposure` sets each view from the
  others' brightness. `render-log` refuses a picture drawn with a shadow fault and reads each plate's drawing time.
  The tuner (`tune_lights.py`: one named light changed per small render) is not built yet.
- **`../paper-film/blender/set_measurements.py`** (Blender, read only): `footprints` (a prop's base), `beam` (every surface
  a light's cone meets) and `objects` (where the set's lamps are), for the two planners.
- **`../paper-film/tools/camera_audit.py`**: the old audit, unchanged (its old reports reproduce word for word), plus
  `--timeline` (the page's window from the timeline and page files, equal to the stage's own page edges) and
  `--built-set` (no turn during a move, where the lines meet, magnification at the nearest painted thing with the place's
  accepted list, and the frame staying 0.03 inside the painted plate, held frames included; settings section
  `camera_audit_built_set`).
- Tests: `tests/test_plan_effects.py`, `tests/test_plan_lights.py`, `tests/test_camera_audit.py`; fixtures in
  `tests/fixtures/effects-camera-light/` (sources in its `sources.json`).
