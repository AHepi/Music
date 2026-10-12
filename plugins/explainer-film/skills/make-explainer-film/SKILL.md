---
name: make-explainer-film
description: Make a narrated, fact-checked explainer film for a phone screen (1080x1920) chapter by chapter, from research to a finished video with captions, in a cinematic look (painted rooms with depth, card models, paper cut-outs, film grain, documentary graphics) or the simpler paper pop-up look. Use when someone asks for an explainer video, a documentary-style chapter, or "the next chapter" of such a film.
when_to_use: The user wants a short documentary or explainer video made end to end (research, script, voice, pictures, animation, filming), or wants to continue a series made this way.
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
   with npm, and checks for Python packages, ffmpeg and a Chromium browser). The kit's own docs are
   in `film-kit/docs/`.
2. **House rules** (read `${CLAUDE_PLUGIN_ROOT}/skills/make-explainer-film/house-rules.md`): confirm
   every paid step's estimated cost before spending; keep a project story, decisions (the user's
   exact words), status, lessons; name delivered files with a two-digit log number and plain words.
3. **Ask the user only about wants, risk or cost.** Make routine technical choices yourself.

## The steps (each has its own skill; do them in order)

| Step | Skill | Hands on |
|---|---|---|
| 1. Research, outlines, script | `research-and-script` | a research ledger (every fact with a source), 2-3 outlines for the user to choose, the script (`narration-script.json`) |
| 2. Fact check the script | `check-facts` (workflow `verify-facts`) | fixes before recording |
| 3. Record and time the voice | `record-narration` | recordings, word times, `timeline.json`, the mix |
| 4. Paintings, rooms with depth, cut-outs | `paint-and-cut` | `assets/reliefs/<chapter>/`, `paper-film/pieces/<chapter>/` |
| 5. Pages | `build-cinema-page` (workflow `build-pages` for many at once) | `paper-film/scenes/<chapter>/page-N.js` and `<chapter>.js` |
| 6. Check and critique | `check-and-critique` (workflows `critique-film`, `verify-facts` again for on-screen words) | fixes before filming |
| 7. Film and finish | `film-and-finish` | the master film, a sendable copy under 28 MB, captions, cover, measurements |

## Timings and costs to expect (chapter 2: 4 min 30 s, ten pages, 4 CPUs)

- Recording: about 1 ElevenLabs credit per letter (about 4,300 credits for 4,300 letters).
- Paintings: about 10 US cents per 2k painting, 2.5 cents per 1k, a fraction of a cent per depth
  map or mask; chapter 2 spent about US$1.06.
- Building ten pages: two pattern pages by hand, then eight in parallel (10-16 minutes each).
- Filming: about 1.4-2.4 s per frame; 8,110 frames took about 3.5 hours with two stretches at once.

## The rules that matter most

- Words on screen are short forms of what the narrator says at that moment; numbers are the ones
  she says (or plainly illustrative). Check every number against the research.
- An author's views are said and shown as theirs ("Mattei argues", credit line with the book).
- No drawn portraits of real people; invented figures are fine. No political party names, colours
  or logos when the film must be neutral. No real banknote designs.
- Every event is timed to a word; pages must draw the same picture for a moment whatever was drawn
  before (they are filmed in separate stretches).
- Keep important words out of the bottom 380 px and right 140 px of the frame (phone buttons).
- Check pictures with your own eyes (contact sheets with the Read tool) before filming, and get an
  independent critique (subagents) before you call it done.
