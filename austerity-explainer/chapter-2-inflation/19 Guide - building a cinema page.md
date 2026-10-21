# Guide: building one page of chapter 2 ("What really causes inflation")

What this file is: the written guide the eight page helpers followed (log 19). Paths are those of
the working copy of the film kit (`/home/user/work/paper-pop-up-film-kit`); the same files are kept
in this folder under `film-code/` and `pictures/`. In the repository the whole kit is
`austerity-explainer/film-kit/`, and the paths below are inside it. The reference files it names are
`narration/page-words.txt` and `pictures/reliefs/contact-sheet-reliefs.jpg` and
`pictures/pieces/contact-sheet-pieces.jpg` in this folder.

You are building ONE page file of a 4.5-minute vertical film (1080 x 1920, 30 frames a second) for a
general audience. The narrator, Malina, is already recorded. Every page is a 3D scene drawn by
three.js in a headless browser, with flat documentary graphics on top. The look: cinematic (depth of
field, glow, film grain, warm lamp light, painted rooms you can move inside) but every page must also
*explain* — each idea in the narration gets a clear picture or a short word at the moment she says it.

Kit folder: `/home/user/work/paper-pop-up-film-kit` (all paths below are inside it unless absolute).

## 1. Read these first

1. Two finished pages, as patterns. Copy their structure:
   - `paper-film/scenes/inflation-chapter-2/page-2.js` — set inside a painted room with depth
     ("relief"): cut-outs, 3D banknotes, paper boats, light beams, dust, a dots panel, bars.
   - `paper-film/scenes/inflation-chapter-2/page-3.js` with `two-factories-set.js` — a model set on a
     table in front of a painted backdrop: card factories, coins raining, split-flap price counters.
   - Their stills: `/home/user/work/chapter-2/stills/p2d/sheet.jpg`, `/home/user/work/chapter-2/stills/p2b/sheet.jpg`,
     `/home/user/work/chapter-2/stills/p3c/sheet.jpg`, `/home/user/work/chapter-2/stills/p3d/sheet.jpg`.
2. The shared building blocks (read, never edit):
   - `paper-film/scenes/cinema-kit.js` — `kit.at(word, n)`, `kit.firstWordAt`, `kit.lastWordEnd`,
     `kit.lightRig({...})`, `kit.relief(name, {near, far, fov})` → `{ mesh, pointAt(u, v), distanceAt }`,
     `kit.backdrop(name, {distance, fov})`, `kit.cutout(pieceName, {at, width, yaw})` → `.set({visible,
     fold, dx, dy, dz, roll, lift, yaw, scale, opacity})` (fold 0 = standing, PI/2 = lying flat),
     `kit.word(lines, {size, colour, at})` (3D words), `kit.card(lines, {size, at})` (printed card),
     `kit.shot(keys, {handheld, seed})`, `kit.shake(time, amount, decay)`, `kit.toScreen(point)`.
     Motions re-exported: `popUp, foldDown, popUpUntil, slapFlat, dropIn, slideIn, spring, clamp01,
     smooth, smoother, ramp, lerp, seededRandom`.
   - `paper-film/scenes/models.js` — `paperFactory, paperHouse, shell, coin, banknoteBundle, priceTag
     (.setText), splitFlap (.pose(t, schedule)), countSchedule, dial, oilBarrel, paperBoat,
     barColumns, threadChart, paperGround, contactShadow, PAPER` colours.
   - `paper-film/scenes/effects.js` — `Motes, LightBeam, DustBurst, Smoke, CoinRain`.
   - `paper-film/scenes/graphics.js` — 2D overlay: `placeTitle, hook, counter, callout, lineChart,
     bars, credit, presence, INK` colours.
   - `paper-film/scenes/cinema-chapter.js` — how pages are joined.
3. The words and their times: `/home/user/work/chapter-2/reference/page-words.txt` (every word of
   every page with its start time in seconds). `kit.at('word')` finds the first match on your page,
   `kit.at('word', 2)` the second (lower case, punctuation ignored).
4. Pictures you can use (look at them with the Read tool):
   - Painted rooms with depth: `/home/user/work/chapter-2/reference/reliefs-sheet.jpg`
     (files in `assets/reliefs/inflation-chapter-2/NAME.jpg` + `NAME-depth.png`).
   - Cut-out pieces: `/home/user/work/chapter-2/reference/pieces-sheet.jpg` (sizes in pixels; files
     and `pieces.json` in `paper-film/pieces/inflation-chapter-2/`).
5. Facts: `/home/user/Music/austerity-explainer/chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md`.

## 2. What a page file is

`paper-film/scenes/inflation-chapter-2/page-N.js` exports `async function build(kit)` that adds
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
  `toe` (0 = the filmic curve as it always was; 1 = the curve may still brighten a value but never darkens one, so
  dark painted values arrive as painted; for a dark painted street such as the wet lockout, with `vignette` 0.25;
  added in log 37, off unless a scene asks for it).

## 3. How to test (do this often)

```
cd /home/user/work/paper-pop-up-film-kit
PAPER_FILM_PAGES=N timeout 900 node paper-film/tools/render-paper-film.mjs cinema-test-pages /home/user/work/chapter-2/stills/pN-a --stills 75.5 79.0 84.2
python3 -I /home/user/work/chapter-2/sheet.py /home/user/work/chapter-2/stills/pN-a/sheet.jpg 4 /home/user/work/chapter-2/stills/pN-a/still-*.jpg
```
- Times are separated by SPACES (not commas). Use a new folder letter for each round (pN-a, pN-b …)
  rather than deleting files.
- Then look at the sheet with the Read tool, and at single stills when you need detail. Look
  critically, like a film director: is the thing she is talking about clearly visible, lit, in
  focus and not cut off? Is the frame balanced? Are words readable and inside the safe area?
- A browser error prints as `page.evaluate: ...` with the file and line.
- Placing things in a painted room: `python3 -I paper-film/tools/relief_points.py
  assets/reliefs/inflation-chapter-2 NAME --near 6 --far 70 0.5,0.1 0.3,0.2` prints the 3D point
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

Only create or edit `paper-film/scenes/inflation-chapter-2/page-N.js` (and, if you need a helper,
`paper-film/scenes/inflation-chapter-2/page-N-something.js`). Do NOT edit cinema-kit.js, models.js,
effects.js, graphics.js, cinema-chapter.js, the stage, two-factories-set.js or other pages — other
people are working in parallel. If a shared piece is missing or broken, work around it inside your
page file and mention it in your report. Do not spend money on any service (no image generation, no
voice). Do not commit with git.

## 7. Finish

Render a final round of 8–12 stills that covers every beat of your page (including the very first
and last moments of your page window), make the sheet, look at it, and fix anything weak. Then
report: the page file path, the final sheet path, a list of beats (time, word, what is seen), every
number or word shown on screen with its research id, and anything you were unsure about.
