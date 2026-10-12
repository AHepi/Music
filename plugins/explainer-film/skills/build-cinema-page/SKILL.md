---
name: build-cinema-page
description: Build one page file of an explainer film in the cinema look (a 3D scene timed to the narrator's words, with documentary graphics on top), test it with stills and fix it; or build many pages at once with parallel helpers. Use after the narration timeline, painted rooms and cut-outs exist.
---

# Build a cinema page

Read the full guide first: `${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/guide.md` (what to read in
the kit, what a page file is, how to test, lessons, and the strict on-screen rules).

**Example.** Page 2 of chapter 2 ("Britain, 1915"): the camera creeps down a painted munitions hall
with sunlight and dust; on "Unemployment" munition women rise in the foreground and a panel of 100
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
4. Finish with a round of 8-12 stills covering every beat, including the page's first and last moments.

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
