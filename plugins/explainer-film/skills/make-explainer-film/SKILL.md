---
name: make-explainer-film
description: Make a narrated, fact-checked explainer film for a phone screen (1080x1920) chapter by chapter, from research to a finished video with captions, in a cinematic look (places built in 3D and painted over, painted rooms with depth, card models, paper cut-outs, film grain, documentary graphics) or the simpler paper pop-up look, with automatic checks (calculators and a preflight) at every stage. Use when someone asks for an explainer video, a documentary-style chapter, or "the next chapter" of such a film. Also use when the work includes building any place or props in Blender (a village, town, harbour, mine, farm, garden, interior, building, set or props), even if the request never mentions surfaces or wear, because that work goes through the skill surfaces-wear-and-construction.
when_to_use: The person wants a short documentary or explainer video made end to end (research, script, voice, pictures, animation, filming), or wants to continue a series made this way, or any request to build a place, village, town, set or props in Blender.
---

# Make an explainer film (master steps)

You make one chapter at a time (about 3 to 5 minutes, ten "pages" of 15 to 35 seconds each).
Every picture lands on a spoken word: the narration is recorded first, its word times are measured,
and each page file asks for the time of a word (`kit.at('doubled')`) and makes something happen then.

**A concrete example.** In chapter 2 of the austerity explainer the narrator says "and prices climb"
at 66.98 seconds. Page 3's file asks for `kit.at('climb')` and at that moment a flip counter on a
card factory flips £1.25 → £1.60 → £2.00, coins stack beside it and a red label PRICES CLIMB points
at the counter. The whole film is built like that.

## Before you start (always)

1. **Set up the kit** in the project's working folder (once):
   `explainer-film-setup /path/to/work/film-kit` (installs three.js, Playwright and the Inter font
   with npm, checks for Python packages, ffmpeg, a Chromium browser, the Blender program and a virtual
   screen for 3D places, and a soundtrack, and writes what it found into the kit's
   `machine-settings.env`). Read its checks. The kit's own docs are in `film-kit/docs/` (start with
   `paper-look - 00 START HERE.md`).
2. **House rules** (read `${CLAUDE_PLUGIN_ROOT}/skills/make-explainer-film/house-rules.md`): confirm
   every paid step's estimated cost before spending; keep a project story, decisions (the person's
   exact words), status, lessons; name delivered files with a two-digit log number and plain words.
3. **Ask the person only about wants, risk or cost.** Make routine technical choices yourself.
4. **Read the tips guide** once before the first step, and the section for each stage as you reach it:
   `${CLAUDE_PLUGIN_ROOT}/kit/docs/LLM tips and tricks.md` (in the kit folder: `docs/LLM tips and tricks.md`).
   It holds the short rules this project learned over 35 logs, each with the tool that checks it, the numbers
   to know (with their units and whether they were measured, judged or invented), the traps that cost the
   most rounds, and the list of things only a critic can judge.
5. **If any part of the work builds a place, set or props in Blender** (also when the request names no surfaces, textures or
   wear), read `${CLAUDE_PLUGIN_ROOT}/skills/surfaces-wear-and-construction/SKILL.md` first and make the preflight stage
   `place` pass before any picture is drawn or painted. Do this without being asked.

## Compute, don't search: the preflight and the calculators

Nearly every number this project once found by trial (where a prop lands on the frame, how far back the
camera may stand, how long a slide may be, how loud the music sits, how long filming takes, what a painting
costs) is now worked out by a tool in the kit (`calculators/`, `narration-tools/`, `paper-film/tools/`,
`paper-film/blender/`), from the new film's own files. House numbers live in one table,
`film-settings.json`; change them only there. The calculators' guide is the kit's `calculators/README.md`.

**Run the preflight at each stage, read its whole report, and fix what it lists before you move on:**
```
explainer-film-preflight STAGE --project FILM_FOLDER [inputs]
```
(on the PATH once the plugin is installed, or `python3 calculators/preflight.py` in the kit). Name the film's
files once in `FILM_FOLDER/preflight-plan.json` (`explainer-film-preflight --example-plan` prints one);
`explainer-film-preflight --list` lists every stage's inputs and which tool makes each. Reports go to
`FILM_FOLDER/preflight-reports/`. Exit 0 passes (read the "look" items), 1 fails, 2 means an input is
missing (the report names the file and the tool that makes it). Only new failures block: a problem accepted
on purpose, with who and the date, is reported as known. Right before a paid or long step,
`explainer-film-preflight STAGE --gate` says whether the newest report passed and its inputs are unchanged.
It spends nothing and changes no project file.

| Stage | When | Step below |
|---|---|---|
| `script` | before recording (before paying for the voice) | 1-2 |
| `record` | after recording | 3 |
| `shots` | before building or drawing a place's views | 4a |
| `place` | after a place is built, before its views are drawn: the surface, wear and construction audit | 4a |
| `plates` | before paying for paintings | 4, 4a |
| `paint` | after each painting arrives | 4, 4a |
| `pages` | while building pages | 5 |
| `film` | before filming (it needs a critique, saved as JSON, newer than every page file, each finding fixed or accepted) | 6-7 |
| `finish` | after finishing | 7 |

Work like this: compute before you render; make one change, then measure again (camera first, then props,
then light); quote measured numbers in every report; never trust a single still. What no tool can judge
(history, what a detail reads as on a phone, newcomer understanding, story choices, the person's yes to
spend) goes to critics: section 19 of the tips guide lists it.

## The steps (each has its own skill; do them in order)

| Step | Skill | Hands on | Preflight |
|---|---|---|---|
| 1. Research, outlines, script | `research-and-script` | a research ledger (every fact with a source), 2-3 outlines for the person to choose, the script (`narration-script.json`) | `script` |
| 2. Fact check the script, and test it on newcomers | `check-facts` (workflows `verify-facts`, then `test-script-with-newcomers`) | fixes before recording; then read it to one or two real newcomers with the script's listener questions | `script` |
| 3. Record and time the voice | `record-narration` | recordings, word times, `timeline.json`, the mix | `record` |
| 4. Paintings, rooms with depth, cut-outs | `paint-and-cut` | `assets/reliefs/<chapter>/`, `paper-film/pieces/<chapter>/` | `plates`, `paint` |
| 4a. Or: places built in 3D and painted over (the look of chapter 2 for newcomers) | `build-and-paint-a-place` (and `make-3d-models`, and `surfaces-wear-and-construction` for every place or prop) | a Blender set per place, its place facts, planned and checked views, plates, lined-up paintings, `assets/models/<place>/` | `shots`, `place`, `plates`, `paint` |
| 5. Pages | `build-cinema-page` (workflow `build-pages` for many at once) | `paper-film/scenes/<chapter>/page-N.js` and `<chapter>.js` | `pages` |
| 6. Check and critique | `check-and-critique` (workflows `critique-film`, `verify-facts` again for on-screen words) | fixes before filming | `pages`, then `film` |
| 7. Film and finish | `film-and-finish` | the master film, a sendable copy under 28 MB, captions, cover, measurements | `film`, `finish` |

## Timings and costs to expect (chapter 2: 4 min 30 s, ten pages, 4 CPUs)

- Recording: about 1 ElevenLabs credit per letter (about 4,300 credits for 4,300 letters).
- Paintings: about 10 US cents per 2k painting, 2.5 cents per 1k, a fraction of a cent per depth
  map or mask; chapter 2 spent about US$1.06.
- Building ten pages: two pattern pages by hand, then eight in parallel (10-16 minutes each).
- Filming: about 1.4-2.4 s per frame; 8,110 frames took about 3.5 hours with two stretches at once.
- Built-and-painted places (chapter 2 for newcomers, October 2026): a plate repaint about 44 US cents
  (Flux 3 edit, 4.8 cents a megapixel counting the pictures sent; it was 2.4 the day before, so prices
  change between plan and purchase: read fal's live price before each paid batch); about 0.9 s a frame
  while the camera holds and 4.3 s while it slides (one worker). Before recording,
  `narration-tools/estimate_timeline.py` gives the chapter's length from the script (about 407 s for the
  16-page newcomer chapter).
- Work these out instead of guessing (from the kit folder):
  `python3 calculators/plan_budget.py cost PLAN.json --rate CENTS --rate-date DATE` prices the paid steps at today's rate (paintings by the
  megapixels returned AND sent, the narration's credits, a repaint and re-record reserve);
  `plan_budget.py ledger LEDGER.json --next-cost DOLLARS` says what is left of the person's allowance,
  counted from the day it began, and refuses a step larger than that (an allowance covers only the kind of
  spending it was given for, its `covers` list: a step of another kind needs a fresh yes; spending inside it is
  still reported each time; a helper's brief gets the true remaining figure, the ledger's line "For helper briefs:"); `plan_budget.py filming` plans the
  filming time and stretches from a short measured profile (skill `film-and-finish`). Do the free steps
  first, then ask once with the exact cost. A vague reply is not a yes.

## The rules that matter most

- Words on screen are short forms of what the narrator says at that moment; numbers are the ones
  she says (or plainly illustrative). Check every number against the research.
- An author's views are said and shown as theirs ("Mattei argues", credit line with the book).
- No drawn portraits of real people; invented figures are fine. No political party names, colours
  or logos when the film must be neutral. No real banknote designs.
- Every event is timed to a word; pages must draw the same picture for a moment whatever was drawn
  before (they are filmed in separate stretches).
- Leave room for phone buttons (rule 12): anything to read ends left of 0.90 across (972 px of 1080)
  and sits above 0.80 down; typed words go in the top band, 0.05 to 0.22 down.
- A place is not built until its surfaces, wear and construction pass the audit (stage `place`): a flat clean model that
  passes the model lint is not finished.
- Rented-card time is limited like painting money: make every change in one sweep, then look once; try a change as about 10 far-apart variations in ONE batch (`explainer-film-place variations`), at most one more batch;
  small quick pictures until the end, full-size pictures once at the very end; every helper has a card-time allowance and the ledger counts it (skill `surfaces-wear-and-construction`, file `batched-rounds-and-card-time.md`).
- Check pictures with your own eyes (contact sheets with the Read tool) before filming, and get an
  independent critique (subagents) before you call it done. The tools measure; the critics judge what they
  can't (section 19 of the tips guide).
- A view's kinds of shot (still life, crowd, overview, interior, dark subject) relax some composing rules
  on purpose, and a problem the project chose to keep goes in the check file's `accepted` list (rule,
  reason, who, date), so it is reported as known instead of failing every run.
