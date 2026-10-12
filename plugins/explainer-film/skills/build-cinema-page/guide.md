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
     bars, credit, presence, INK` colours.
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
  0 = all sharp), `maxBlur`, `glowThreshold` (0.9–0.95), `glowStrength` (0.55–0.75), `contrast`,
  `saturation`, `vignette`, `tintAmount`, `fade` (0 = normal, 1 = black; use for a dip to black).

## 3. How to test (do this often)

```
cd KIT   # the folder made by explainer-film-setup
PAPER_FILM_CHAPTER=<chapter> PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages paper-film/out/stills/pN-a --stills 75.5 79.0 84.2
python3 -I paper-film/tools/contact_sheet.py paper-film/out/stills/pN-a/sheet.jpg 4 paper-film/out/stills/pN-a
```
- Times are separated by SPACES (not commas). Use a new folder letter for each round (pN-a, pN-b …)
  rather than deleting files.
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
- 2D words: keep important words out of the bottom 380 pixels and the right 140 pixels (phone
  buttons). `callout` keeps itself inside the frame. Big hooks sit around y 250–450.
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
