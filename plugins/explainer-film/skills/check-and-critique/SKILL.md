---
name: check-and-critique
description: Check a finished set of cinema-look pages before filming - stills of every beat, the page turns from the whole chapter, and an independent critique by helper agents (pictures, on-screen content, code) whose findings a skeptic verifies and ranks. Use when all pages are built, and again after big fixes.
---

# Check and critique before filming

**Example.** Chapter 2's own checks caught: 1920s-dressed men standing in a present-day street,
price tags showing as white slivers before they flipped up, a label running into a dial, a stray
mark beside every comma on a flip counter, banknotes looking like white bricks, and one page's words
showing on the next during page turns (only visible when frames are drawn one after another).

## 1. Every page, every beat

For each page, stills at every beat (the page's first and last moments too), as a contact sheet,
looked at with the Read tool (single stills at full size when a detail matters):
`PAPER_FILM_CHAPTER=<chapter> PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages OUT/pN --stills ...`
then `python3 -I paper-film/tools/contact_sheet.py OUT/pN/sheet.jpg 4 OUT/pN`.

## 2. The whole chapter and its page turns

- `node paper-film/tools/render-paper-film.mjs <chapter> --info` must load all pages and print the
  page edges.
- Draw the page turns IN ONE RUN (state leaks only show when frames follow each other): one still at
  each page's last word + 0.7 s, plus the first and last moments:
  `node paper-film/tools/render-paper-film.mjs <chapter> OUT/joins --stills 0.5 20.03 42.55 ...`
  Each page's words must stay on its own page; the new page under the curl must be clean.

## 3. Independent critique (helpers)

```
Workflow({ name: "explainer-film:critique-film", args: {
  kit: "/abs/path/film-kit", chapter: "<chapter>",
  script: "/abs/path/NN Script.md", wordTimes: "/abs/path/film-kit/examples/<chapter>/timeline.json",
  guide: "${CLAUDE_PLUGIN_ROOT}/skills/build-cinema-page/guide.md",
  ledger: "/abs/path/NN Research.md",
  brief: "the user's words about the look",
  pictureGroups: [ { label: "pages 1-3", stills: "OUT/p1/sheet.jpg, OUT/p2/sheet.jpg, OUT/p3/sheet.jpg, OUT/joins/sheet.jpg" },
                   { label: "pages 4-6", stills: "..." }, { label: "pages 7-10", stills: "..." } ],
  notes: "fixes already made since those sheets",
  effort: "medium" } })
```
Without workflows: start the same critics as Agents (type `explainer-film:film-critic`), one per
area, all at once, then one more agent to verify and rank their findings.

Then run `check-facts` again with `onScreen` set to the page files, so every number shown is checked.

## 4. Fix, then check the fixes independently

- Write each page's confirmed findings to its own file and give one fixing helper per page (agent
  type `explainer-film:page-builder`, all at once) its file; each edits only its page and draws stills.
  Shared changes (a new option in graphics.js, a recoloured piece, a shared model set) you make first.
- Then an independent check (checkers who did not make the fixes), comparing every finding with the
  new stills AND the code, and looking for new problems the fixes caused (in chapter 2 they found
  four: a camera change that pushed another label off screen, a needle now falling on the word
  "raising", coins landing where the camera could not see them, a stray line moved rather than removed):
  ```
  Workflow({ name: "explainer-film:check-fixes", args: { kit, chapter, guide, wordTimes,
    groups: [ { label: "pages 1-3", pages: [1,2,3], findings: "/abs/fixes/page-1.md ... page-3.md", stills: "new sheets ..." }, ... ],
    joins: "/abs/joins/sheet.jpg", changes: "what shared things changed", effort: "medium" } })
  ```
- Fix what it finds, look again, and record each fault and its fix in Lessons.md. Only then film.
- If filming has already started: a stretch only needs re-filming if its page changed after the
  stretch started (compare the stretch file's time with the page file's).
