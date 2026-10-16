# About these examples

What this folder is: chapter 2 of the austerity explainer, rewritten for newcomers (log 34), in the
built-and-painted look: its estimated timeline and the shot checker's check files for the Works, the first
built place (round 5 of the redesign, 16 October 2026).

- `timeline-estimated.json`: the chapter's timeline worked out from the narration script before anything
  was recorded (`narration-tools/estimate_timeline.py`, Malina's measured word lengths and pauses; 406.9 s).
  The chapter scene `paper-film/scenes/inflation-chapter-2-newcomers.js` reads it until the real
  `timeline.json` exists.
- `works-w1-shot-check.json`, `works-w1-working-shot-check.json`, `works-w2-shot-check.json`,
  `works-w2-slowed-shot-check.json`, `works-w3-shot-check.json`: check files for the Works' gate views (a
  crowd outside a shut gate, a factory working flat out), the second worked example of a check file after
  `examples/notice-corner/shot-check.json` (a still life). They use `story_reaches_down` (rule 7).

## Traps

- These views were accepted with problems still listed. Round 5's final reports list 13 (W1, layout) to 29
  (W3) problems per view, for example a crowd wider than rule 3's box and drums in the bottom-left quarter.
  The notice corner's rules were made for a still life; a crowd or an overview breaks some of them on
  purpose. Nothing in these files yet marks which problems were accepted, by whom or why, so do not read
  "it passed" into them: read each report and decide.
- Still to come from the austerity project once round 5 finishes: the W4 check file
  (`works-w4-shot-check.json`) and the checkout's (`checkout-c1-shot-check.json`), and the Blender scripts
  that build the Works and the checkout. See `kit-sync-notes.md` in the kit's top folder.
- The Works' pictures and models are not in the plugin; the page files in
  `paper-film/scenes/inflation-chapter-2-newcomers/` are patterns to read.
