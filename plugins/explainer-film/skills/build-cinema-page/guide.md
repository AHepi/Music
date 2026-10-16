# Guide: building one page in the cinema look

What this file is: everything a helper needs to build one page file of a chapter in the cinema look:
what to read, what a page file is, how to test, the lessons already learned, and the strict rules for
what appears on screen. KIT = the film kit folder made by `explainer-film-setup`; <chapter> = the
chapter's folder name. Chapter 2 of the austerity explainer ("inflation-chapter-2", in the kit) is
the worked example.

You are building ONE page file of a vertical film (1080 x 1920, 30 frames a second). The narration
is already recorded. Every page is a 3D scene drawn by three.js in a headless browser, with flat
documentary graphics on top. The look: cinematic (depth of field, glow, film grain, warm lamp light,
painted rooms you can move inside) but every page must also *explain*: each idea in the narration
gets a clear picture or a short word at the moment it is said.

## 1. Read these first

1. Two finished pages, as patterns. Copy their structure:
   - `paper-film/scenes/inflation-chapter-2/page-2.js` (in the kit, a worked example) — set inside a painted room with depth
     ("relief"): cut-outs, 3D banknotes, paper boats, light beams, dust, a dots panel, bars.
   - `paper-film/scenes/inflation-chapter-2/page-3.js` with `two-factories-set.js` (worked example) — a model set on a
     table in front of a painted backdrop: card factories, coins raining, split-flap price counters.
   - Also the commented template `paper-film/scenes/cinema-chapter-template/page-1.js`.
2. The shared building blocks (read, never edit):
   - `paper-film/scenes/cinema-kit.js` — `kit.at(word, n)`, `kit.firstWordAt`, `kit.lastWordEnd`,
     `kit.lightRig({...})`, `kit.relief(name, {near, far, fov})` → `{ mesh, pointAt(u, v), distanceAt }`,
     `kit.backdrop(name, {distance, fov})`, `kit.cutout(pieceName, {at, width, yaw})` → `.set({visible,
     fold, dx, dy, dz, roll, lift, yaw, scale, opacity})` (fold 0 = standing, PI/2 = lying flat),
     `kit.word(lines, {size, colour, at})` (3D words), `kit.card(lines, {size, at})` (printed card),
     `kit.shot(keys, {handheld, seed})`, `kit.shake(time, amount, decay)`, `kit.toScreen(point)`,
     `kit.speaker(name, {at, width})` → `.set(pose, open)` (an invented speaking figure made of
     NAME-face/-jaw/-mouth pieces) with `kit.mouthOpen(t, from, until)` (opens on each spoken word).
     Motions re-exported: `popUp, foldDown, popUpUntil, slapFlat, dropIn, slideIn, spring, clamp01,
     smooth, smoother, ramp, lerp, seededRandom`.
   - `paper-film/scenes/models.js` — `paperFactory, paperHouse, shell, coin, banknoteBundle, priceTag
     (.setText), splitFlap (.pose(t, schedule)), countSchedule, dial, oilBarrel, paperBoat,
     barColumns, threadChart, paperGround, contactShadow, PAPER` colours.
   - `paper-film/scenes/effects.js` — `Motes, LightBeam, DustBurst, Smoke, CoinRain`.
   - `paper-film/scenes/graphics.js` — 2D overlay: `placeTitle, hook, counter, callout, lineChart,
     bars, credit, presence, INK` colours; and, for chapter 2 for newcomers, `dotPanel` (100 dots),
     `ruleCard`, `guessRing`, `nameTag`, `priceArrow`, `pointer`, `topShade` (a soft dark band behind
     words at the top), `buildWords` and the text limits `TEXT_LEFT` (65 px) and `TEXT_RIGHT` (972 px).
   - Places built in 3D and painted over: `paper-film/scenes/projected-set.js`
     (`projectPaintingOnto`, `ownSurface`, a `behind` painting, `skyCard`, `paintedSkyOnly`) and
     `pit-village-effects.js` (flames, sparks, glows, contact shadows); worked examples
     `notice-corner.js`, `people-test.js` and `inflation-chapter-2-newcomers/page-3.js` to `page-5.js`
     (with `works-effects.js`). The whole way to make such a place is the `build-and-paint-a-place` skill.
   - `paper-film/scenes/cinema-chapter.js` — how pages are joined.
3. The words and their times: print them with
   `python3 -I narration-tools/print_word_times.py examples/<chapter>/word-times.json` (or read
   `examples/<chapter>/timeline.json`, where times are seconds from the chapter's start). `kit.at('word')` finds the first match on your page,
   `kit.at('word', 2)` the second (lower case, punctuation ignored).
4. Pictures you can use (make contact sheets and look at them with the Read tool):
   - Painted rooms with depth: `assets/reliefs/<chapter>/NAME.jpg` + `NAME-depth.png`
     (`python3 -I paper-film/tools/contact_sheet.py rooms.jpg 6 assets/reliefs/<chapter>/*.jpg`).
   - Cut-out pieces: `paper-film/pieces/<chapter>/` with sizes in `pieces.json`.
5. Facts: the chapter's research ledger (every number on screen must come from it).

## 2. What a page file is

`paper-film/scenes/<chapter>/page-N.js` exports `async function build(kit)` that adds
things to `kit.scene` and returns `{ pose(t), draw2D(ctx, t), join? }`:

- `pose(t)` places everything for moment t (seconds from the start of the chapter) and returns
  `{ camera: shot(t), look: {...} }`. It must NOT remember earlier frames: the film is drawn in
  separate chunks, so every frame is computed from t alone.
- `draw2D(ctx, t)` draws the flat graphics for moment t on a 1080 x 1920 canvas; return true.
- `join` (optional): how this page hands over to the next, `{ kind: 'peel' | 'dissolve' | 'dip',
  after: 0.3, length: 0.85 }` (default: peel, 0.3 s after the last word, lasting 0.85 s). Your page
  is drawn from (previous page's last word + about 0.3 s) until (your last word + about 1.2 s), so
  plan the camera from `kit.firstWordAt - 0.8` to `kit.lastWordEnd + 1.3`.
- `look` fields (all optional): `exposure` (0.9–1.0), `aperture` (focus blur strength, 7–9 good,
  0 = all sharp; in a built-and-painted set 4.0 with `maxBlur: 2`), `maxBlur`, `glowThreshold`
  (0.9–0.95), `glowStrength` (0.55–0.75), `contrast`, `saturation`, `vignette`, `tintAmount`, `fade`
  (0 = normal, 1 = black; use for a dip to black).
- Held shots (log 34): while the camera holds, return `still: true` from `pose(t)` (or a key that changes
  when the set itself changes) and mark everything that changes frame to frame with
  `kit.moving(flames, smoke, ...)` (or `const done = kit.movingFromHere(); ...; done();`). The stage then
  draws the painted set once and only the moving things each frame (measured on the Works: about 0.9 s a
  frame held against 4.3 s sliding). Anything not marked is frozen while the shot holds.
- `join` also takes `'run-on'`: a plain blend for a page that runs on into the next in the same frame.
  In a lazy chapter (`buildCinemaChapter({ ..., lazy: true })`, for long chapters of heavy sets) each page
  file must `export const join = {...}` instead of returning it from `build`.

## 3. How to test (do this often)

```
cd KIT   # the folder made by explainer-film-setup
PAPER_FILM_CHAPTER=<chapter> PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages paper-film/out/stills/pN-a --stills 75.5 79.0 84.2
python3 -I paper-film/tools/contact_sheet.py paper-film/out/stills/pN-a/sheet.jpg 4 paper-film/out/stills/pN-a
```
- Times are separated by spaces (this plugin's `render-paper-film.mjs` also takes commas, and stops
  with a message on anything that isn't a number). Use a new folder letter for each round (pN-a, pN-b …)
  rather than deleting files.
- Before the narration is recorded, test on the estimated timeline:
  `PAPER_FILM_QUERY=timeline=timeline-estimated` reads `examples/<chapter>/timeline-estimated.json`.
- Then look at the sheet with the Read tool, and at single stills when you need detail. Look
  critically, like a film director: is the thing she is talking about clearly visible, lit, in
  focus and not cut off? Is the frame balanced? Are words readable and inside the safe area?
- A browser error prints as `page.evaluate: ...` with the file and line.
- Placing things in a painted room: `python3 -I paper-film/tools/relief_points.py
  assets/reliefs/<chapter> NAME --near 6 --far 70 0.5,0.1 0.3,0.2` prints the 3D point
  behind each spot (u across 0..1 from the left, v up 0..1 from the bottom). Use the same near/far
  you pass to `kit.relief`. In the page, `room.pointAt(u, v)` gives the same point.
- Each still takes about 2–6 seconds. Other pages are being built at the same time on the same
  machine, so keep rounds to 4–8 stills.

## 4. Lessons already learned (follow them)

- Painted rooms with depth: the camera starts at the origin looking along -z (exactly where the
  painting was made from). Keep camera moves small (about 1–2 units) and the view tilt modest: big
  moves tear thin near things and show the stretched edges. Past the painting's edges the picture is
  mirrored, which passes for more floor; still, avoid looking far past the bottom edge.
- Inside a painting, use `kit.lightRig({ ..., reflections: 0.3, keyShare: 0.6–0.8, fillShare: 0.2 })`
  so 3D models match the painting's light (at the default `reflections: 1` paper and notes look
  white). The painting itself glows by its own light; lamps only light the 3D things and cast their
  shadows onto it.
- Cut-out people: place them big and near (foreground), standing on the floor point or with their
  bottom edge below the frame, rather than tiny far away.
- A "cut" to a second place inside one page: build both rooms at the origin and switch which room
  and which props are visible at the cut time (`mesh.visible`), with two `kit.shot` paths chosen by
  t. Hide the switch with a quick dip: `look.fade` rising to 1 and back over about 0.25 s each way,
  or cut hard on a word.
- 2D words (phone buttons, rule 12): anything to read ends left of 0.90 across (972 px) and starts
  right of 65 px; typed words sit in the top band, 0.05 to 0.22 down, with every letter's top at least
  0.06 down (115 px); nothing to read below 0.80 down (the bottom 380 px). Details:
  `camera-and-framing.md` section 2. `callout` keeps itself inside the frame. Big hooks sit around y 250–450.
- Times: use `kit.at(...)` word times for every event; never hard-code seconds.
- Camera keys must be in time order.

## 5. Rules for what appears on screen (strict)

- Words on screen are short forms of what Malina says at that moment. Numbers must be the ones she
  says (or, for an illustrative price tag, plainly illustrative). Never add claims she doesn't make.
- No drawn portraits of real people (no faces of real politicians, bankers, Mattei…). Invented
  figures and crowds are fine. Text credits naming a source are fine.
- Never name or show any political party, or any party colours or logos.
- Never show the letters "MMT".
- Mattei's views are hers: when her argument is on screen, attribute it ("MATTEI:" or a credit
  line "Clara E. Mattei, The Capital Order (2022)").
- No capitals-for-emphasis inside sentences; hooks may be all capitals as titles.
- No real banknote designs (the kit's notes are invented).

## 6. Do not touch shared files

Only create or edit `paper-film/scenes/<chapter>/page-N.js` (and, if you need a helper,
`paper-film/scenes/<chapter>/page-N-something.js`). Do NOT edit cinema-kit.js, models.js,
effects.js, graphics.js, cinema-chapter.js, the stage, two-factories-set.js or other pages — other
people are working in parallel. If a shared piece is missing or broken, work around it inside your
page file and mention it in your report. Do not spend money on any service (no image generation, no
voice). Do not commit with git.

## 7. Finish

First check your page's word lookups by calculation (no browser, about a second):
`python3 calculators/plan_page_timing.py lookups examples/<chapter>/timeline.json paper-film/scenes/<chapter>/page-N.js:N`
(a word said more than once on the page must say which time, even the first: `kit.at('war', 2)`), and your
camera with `camera_audit.py --timeline` (section 1 of `camera-and-framing.md`). The lead runs the heavier
page events, timing and layout checks on the whole chapter afterwards (`explainer-film-preflight pages`);
the rules they apply are in the kit's `docs/LLM tips and tricks.md`, section 13.

Render a final round of 8–12 stills that covers every beat of your page (including the very first
and last moments of your page window), make the sheet, look at it, and fix anything weak. Then
report: the page file path, the final sheet path, a list of beats (time, word, what is seen), every
number or word shown on screen with its research id, and anything you were unsure about.


## 8. Lessons from chapter 2's review (avoid these)

- People in period clothes standing in a present-day scene (use a graphic such as a hundred-dot
  panel for "how many out of work").
- Props lying flat before they flip up read as white slivers: hide them until their moment.
- A label running into a nearby object: move its end point (`dx`, `dy`) and look again.
- A flip counter needs every character it shows in its alphabet; commas and % signs are there.
- Unspoken numbers (a figure the narrator never says) need a reason and a research id, or leave them out.
- A figure counting through in-between values is fine; random digits that settle on nothing read as data.

## 9. Lessons from the independent critique (chapter 2, before filming)

Seven critics and a skeptic found these; each cost a re-film. Check for them yourself first.
- **The key readout must be fully in frame.** A price board that carries the whole argument was cut
  off at the right edge in most close-ups. Frame the readout at x 600-900 of 1080, never right of 0.90
  across (972 px), and check it at every close-up moment.
- **Pale words on pale surfaces vanish.** Light labels over ivory walls or bright sky could not be
  read. Use `callout(..., { plate: true })` (a dark plate behind the words) or place labels over dark
  ground; check legibility at phone size.
- **A label's line must not cross its number.** Lines ending in the middle of a price read as a
  strike-through. Point at the tag's or board's top edge.
- **Hold the key number still.** A figure still counting while it is said, then fading at once, is
  never read. Finish counts on the word and hold for at least a second after.
- **Nothing should move that the narration does not explain.** A dial sliding down "as if rates were
  cut" beside an unemployment figure implies something unsaid. Keep unexplained movements out of
  the frame or out of focus, and cap springs so needles do not overshoot past the value said.
- **Transitions inside a page must read cleanly frame by frame.** Props sinking through the ground,
  a notice hanging in mid-air when its board tips: fade or slide things out, or cut with a short dip.
- **Show the idea, not an inventory.** "Short of workers, materials and machines" needs SHORT OF (or
  empty slots), not just the three things.
- **Label example numbers as examples** ("Example prices") when they sit next to real data.
- **Colours with meaning:** in an election period, avoid ties, flags or props in party colours; use
  charcoal, grey or ivory for invented officials.
- **Caricatures editorialise.** Top-hatted plutocrats add a claim the narration does not make; show
  the money itself instead.
- **Face-down paper is blank.** Notes and envelopes that land face-down read as tan smudges; land
  them face-up or hide them.
- **A model on a bare block looks unfinished.** Give plinths the paper material and a contact shadow,
  or drop them.
- **Fill the frame past painted edges.** Black corners beyond a backdrop read as a rendering fault:
  scale the backdrop up for close shots.
- **Opacity fades on cut-outs snap.** `.set({ opacity })` leaves a piece solid, then it vanishes at
  half opacity: a piece first drawn solid keeps a drawing recipe that ignores see-through, and
  cut-outs are only drawn where at least half solid. Use `setFading(piece, pose)` from
  `cinema-kit.js` instead of `piece.set(pose)` for a piece that fades, on every frame it shows: it builds
  the piece see-through once and lowers `alphaTest` to 0.02 while it fades (the same function as in
  `house-sample/page-1.js`).
- **Two surfaces in one plane flicker when the camera moves.** Keep built walls, floors and ceilings a
  hair (about 0.01 units) apart from the boxes behind them.
- **A place built in 3D and painted over** (plan 3: the austerity project's pit village,
  `paper-film/scenes/lockout-test.js` with `projected-set.js`): Blender draws the set once (the plate),
  Flux repaints it, and the page shines the painting back onto the set. Never turn the camera: slide
  it, once per shot, from one spoken word to another (`camera-and-framing.md` section 1a; this replaces
  the first test's "turn a degree or two and push in with the lens"); give near props a `behind` painting
  (Flux paints them out of the painting) and soft contact shadows; keep signs' own lettering with
  `ownSurface`; put the painted sky on a far card with `skyCard(kit, projection, painting, projector)`;
  draw flames live rather than painting them. Check the `weights` view at the end of each move and the
  moving frames, not only stills. The whole way: the `build-and-paint-a-place` skill.

## 10. Composing a shot (from the austerity project's log 30)

Before placing props or the camera, read the kit's `07 Composing a shot` (in `kit/docs/` as
`paper-look - 07 Composing a shot.md`). The main rule: where the street's lines meet, the brightest
parts, the biggest near props and the warm light must all fall on the subject. Turn the camera
to aim the lines, then move it only by sliding; stand it where a person would stand; group the story
props so they touch; keep work props small and far. For a shot built in Blender, check it with the shot
checker, which measures the 3D scene itself (exact where the lines meet, what stands on what, how far
each prop is) and says what to change in metres:
`BLEND=<the place's .blend> paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER [PICTURE] -- --view end`
(about a minute; the check file names the subject, story props and work props: copy
`kit/examples/notice-corner/shot-check.json` for a still life or
`kit/examples/inflation-chapter-2-newcomers/works-w1-shot-check.json` for a crowd). Fix the first problem,
then check again: a camera fix moves everything. `paper-film/tools/measure_composition.py` is only for
pictures you did not build (a sketch from a picture program, a painting): it finds lines in the picture
and needs about 15 crisp ones. In one run, Nano Banana Pro given the empty set and the prop
pictures, free to choose its own camera, made a useful sketch of the composition; never use a
program's lettering.

