---
name: build-cinema-page
description: Build one page file of an explainer film in the cinema look (a 3D scene timed to the narrator's words, with documentary graphics on top), check its timing, on-screen words, layout and camera by calculation (page events, the timing and layout checks, the camera audit), test it with stills and fix it; or build many pages at once with parallel helpers. Use after the narration timeline (or the estimated one), painted rooms, cut-outs or painted 3D places exist.
---

# Build a cinema page

Read the full guide first: `${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/guide.md` (what to read in
the kit, what a page file is, how to test, lessons, and the strict on-screen rules), then
`${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/camera-and-framing.md` (strict, from a viewer's
feedback on chapter 2):
- **In a place built in 3D and painted over** (`projected-set.js`; skill `build-and-paint-a-place`)
  the only move is one slide per shot: the position changes, the way the camera faces never does
  (`camera-and-framing.md` section 1a). The rest of this list is for painted rooms and card models.
- **The camera holds still** and moves only to land a point, each move meaning one thing: zoom in
  (narrow onto what matters now), zoom out (make room), pan left/right (shift perspective), pan up
  (ideals), pan down (pressure), move up (the bigger picture), move down (the small details). **At
  most 3 moves per shot**; more means cut to another shot. Write it with `kit.stillShot(start,
  moves, { name })` (it refuses a 4th move or an unknown kind) and check it with
  `node paper-film/tools/render-paper-film.mjs SCENE --camera FILE.json 3` then
  `python3 -I paper-film/tools/camera_audit.py FILE.json [--window FROM TO]` (must say 0 problems).
- **Fill the tall frame**: the subject 60-80% of the width; something in the top third (sky, smoke,
  chimneys) and the bottom third (soft near props), never big empty dark floor. Frame with numbers
  first: `python3 -I paper-film/tools/frame_check.py CAM TARGET FOV name=x,y,z ...`, or for whole boxes
  against the phone-button margins `python3 calculators/frame_geometry.py boxes ...`. (A built place is
  planned with `calculators/plan_shot.py`, composed by the kit's `07 Composing a shot` and measured with
  `paper-film/tools/check-shot.sh`: skill `build-and-paint-a-place`.)
- **Room for phone buttons** (rule 12): words end left of 0.90 across (972 px), typed words sit in the
  top band 0.05-0.22 down with letters at least 0.06 down, nothing to read below 0.80 down, story props
  left of 0.95 across between 0.45 and 0.95 down.
- **Nothing passes through anything**: `room.clearance(object)` (distance in front of the painting;
  negative = poking through), `boxesOverlap(a, b)`; standing things sit ON the floor point; falling
  things stop on the surface they land on.
- Plain card models look poor next to paintings: make detailed ones in Blender (skill `make-3d-models`). Keep one way
  of making pictures for a film: chapter 2's look read as a collage of five kinds of picture, and plain code-built props
  (banknote bundles) looked like soap beside the paintings and the real models.
- Words at the top over a busy set need a soft dark band behind them (see chapter 2 page 8, or
  `topShade` in `graphics.js`).
- A cut-out that fades: `setFading(piece, pose)` from `cinema-kit.js`, not `piece.set({ opacity })`
  (which snaps off half way).

**Example.** Page 2 of chapter 2 ("Britain, 1915"): the camera holds on a painted munitions hall
with sunlight and dust, moves down to the floor once as new money lands, and pans right once to the
benches; on "Unemployment" munition women rise in the foreground and a panel of 100
dots fills, all but one, under UNDER 1%; on "new money" banknote bundles drop and stack; on
"Submarines" paper boats sink in a puddle; on "doubled" two bars show prices ×2.

## One page by hand

1. Copy `paper-film/scenes/cinema-chapter-template/page-1.js` (heavily commented) to
   `paper-film/scenes/<chapter>/page-N.js`, and the chapter file
   `paper-film/scenes/cinema-chapter-template.js` to `paper-film/scenes/<chapter>.js` (list every page).
2. Print the page's words with times and plan beats: for each idea, the word it lands on, what is
   seen (3D) and what is written (2D, a short form of what is said).
3. Build, then test often (guide section 3):
   `PAPER_FILM_CHAPTER=<chapter> PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages OUT/pN-a --stills T1 T2 T3`
   then `python3 -I paper-film/tools/contact_sheet.py OUT/pN-a/sheet.jpg 4 OUT/pN-a` and LOOK at it.
4. Check the word lookups by calculation (no browser, a second):
   `python3 calculators/plan_page_timing.py lookups examples/<chapter>/timeline.json paper-film/scenes/<chapter>/page-N.js:N`.
   A word said more than once on the page must name which time (`kit.at('war', 2)`), even the first.
5. Finish with a round of 8-12 stills covering every beat, including the page's first and last moments.

## Check the pages by calculation (preflight `pages`)

Single stills miss what happens between frames: a label readable for under a second, words fading a frame
before a cut, a one-frame pop, a held shot that films five times slower. These tools measure it from the page
code itself, so run them before the critique and after every round of fixes (or run
`explainer-film-preflight pages`, which runs them and writes one report). The rules behind them, with the
traps they catch: the kit's `docs/LLM tips and tricks.md`, section 13.

1. **Page events** (what every page does, 30 times a second, without filming; about 12 seconds for light
   pages, minutes and about 2 GB for heavy painted sets, so one run at a time):
   `node paper-film/tools/page_events.mjs <chapter> EVENTS.json` (`--pages 3,4,5` for some pages).
2. **Timing and words:** `python3 calculators/plan_page_timing.py check EVENTS.json --ledger NUMBERS.json`.
   It finds lookups that leave out which time a word is meant; words readable under 1 s (a conclusion under
   1.2 s) with the earlier word that would fix it; words that fade before a cut (`fadeOut: 0`); a new line
   over a fading one; margins (65 and 972 px, letter tops at least 0.06 down, nothing to read below 0.80);
   typed words and numbers the narrator doesn't say; counts that don't land on their number and hold; too many
   word groups; slides not tied to words. It also prints the pause each page needs (as the `--pauses` line for
   `narration-tools/assemble_chapter_narration.py` and `--pause-after` for `narration-tools/estimate_timeline.py`:
   write holds into the join and the timeline, never as seconds in the page), the stills to draw (one
   `render-paper-film.mjs` command, so page turns are drawn in one run) and the planned cuts for
   `paper-film/tools/find_jumps.py`.
3. **Layout:** `node paper-film/tools/check_page_layout.mjs EVENTS.json`: pops and one-frame jumps away from a
   planned cut, effects that come out different drawn out of order or are shared between pages, held-shot keys
   while the camera moves, holds with no held-shot key (mark smoke, flames and flicker with `kit.moving`), and
   drawn things on top of each other at each event.
4. **The camera:** `node paper-film/tools/render-paper-film.mjs <chapter> --camera CAMERA.json 3`, then
   `python3 -I paper-film/tools/camera_audit.py CAMERA.json --timeline examples/<chapter>/timeline.json --page N --page-files paper-film/scenes/<chapter>`
   (the page's window worked out for you), and for a place built in 3D and painted over add
   `--built-set --place-facts place-facts.json --view VIEW` (no turn during a slide, the magnification at the
   nearest painted thing, the frame inside the painted plate). Any PROBLEM line is a must-fix.
5. **Effects:** paper-look pages make every effect through `kit.effect`
   (`python3 calculators/plan_effects.py lint PAGE.js`); a picture change that teaches a word must change it
   by at least 15 levels (`plan_effects.py window-change`).
6. A problem you choose to keep goes in an accepted list (`--accepted A.json`: check, page, text, reason, who,
   date) and is reported as known.

## Many pages at once (helpers in parallel)

Build one or two pattern pages yourself first, then run the bundled workflow:

```
Workflow({ name: "explainer-film:build-pages", args: {
  kit: "/abs/path/film-kit", chapter: "<chapter>",
  guide: "${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/guide.md",
  patterns: "paper-film/scenes/<chapter>/page-2.js and page-3.js",
  pages: [ { number: 4, brief: "Page window: first word 74.94 s, last word ends 93.98 s. Narration: \"...\". Facts: C2-H04. Plan: ..." } ],
  effort: "medium" } })
```

Each brief: the page window, the exact narration, the research ids, and a beat-by-beat plan naming
the painted room, pieces, models and short on-screen words (see chapter 2's briefs as examples in
`${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/example-briefs.md`). Without workflows, start one
Agent per page (agent type `explainer-film:page-builder`) with the same brief, all at once.

Afterwards check every page's final sheet yourself, fix what is weak, then run `check-and-critique`.
