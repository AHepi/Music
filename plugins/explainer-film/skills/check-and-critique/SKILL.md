---
name: check-and-critique
description: Check a finished set of cinema-look pages before filming - first the automatic page checks (timing, words on screen, layout, camera, by calculation), then stills of every beat, the page turns from the whole chapter, and an independent critique by helper agents (pictures, on-screen content, history and period, code) aimed at what the tools cannot judge, whose findings a skeptic verifies and ranks; after filming, a fresh helper judges the clip in motion. Use when all pages are built, again after big fixes, and once the film is made.
---

# Check and critique before filming

**Example.** Chapter 2's own checks caught: 1920s-dressed men standing in a present-day street,
price tags showing as white slivers before they flipped up, a label running into a dial, a stray
mark beside every comma on a flip counter, banknotes looking like white bricks, and one page's words
showing on the next during page turns (only visible when frames are drawn one after another).

## 0. First let the tools find what they can (preflight `pages`)

Run `explainer-film-preflight pages` (or the three tools in skill `build-cinema-page`, "Check the pages by
calculation": `paper-film/tools/page_events.mjs`, then `calculators/plan_page_timing.py check` and
`paper-film/tools/check_page_layout.mjs` on its events, plus `paper-film/tools/camera_audit.py` per page). Fix
every failure it lists before spending critics' time: a label readable for under a second, an ambiguous word
lookup, a typed word or number the narrator doesn't say, words fading before a cut, a pop, a held shot with no
still key, a turn during a slide. Use the still times it prints for the sheets below, so every event and page
turn is covered.

## What the critics must still judge

The tools measure; they cannot judge these. Put this list in the critics' brief (the `notes` argument
below), so they spend their effort where no tool can (the full list with examples: the kit's
`docs/LLM tips and tricks.md`, section 19):
- what a detail reads as on a phone (a contour map, a bar chart, a tank), at about 300 px wide;
- history and story accuracy of every painted object and every word written on a prop, not only the spoken words: the
  workflow `critique-film` runs a history critic that asks of each "was this in that place and that year?" (the project's
  faults: wrong-era tanks, too much coal in a lockout, snow-like blotches on a May road, sacks shaped like clay jars, an
  oil-drum brazier more 1984 than 1926, a symbol like a hooked cross);
- whether a motion matches the meaning of its words (a needle falling on "raising");
- whether machines read as machines and props as what they are, and whether a hero prop has enough detail;
- whether a picture contradicts a card, or a colour or symbol carries political or commercial meaning;
- whether a newcomer would understand, and the 3 or 4 things a newcomer must see in each shot;
- whether a time cut where people vanish reads as time passing or as a glitch;
- the overall feel of the light, and which rule wins when two conflict;
- whether a flagged near-touch, thin part or small sign is worth fixing; if not, it goes in the `accepted`
  list with the reason, who and the date.

Have each critic compare the work with the best frame made so far, and a skeptic check their findings.

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
  brief: "the person's words about the look",
  pictureGroups: [ { label: "pages 1-3", stills: "OUT/p1/sheet.jpg, OUT/p2/sheet.jpg, OUT/p3/sheet.jpg, OUT/joins/sheet.jpg" },
                   { label: "pages 4-6", stills: "..." }, { label: "pages 7-10", stills: "..." } ],
  notes: "fixes already made since those sheets",
  propLettering: "/abs/path/prop-lettering.json",   // optional, for built places: python3 calculators/list_prop_lettering.py --out FILE
  period: "the place and the year the film shows",  // optional
  effort: "medium" } })
```
It returns `{ critics, verdict }`; one critic's area is `history`, and the `film` stage refuses a critique with no history area.
Without workflows: start the same critics as Agents (type `explainer-film:film-critic`), one per
area, all at once, then one more agent to verify and rank their findings.

Then run `check-facts` again with `onScreen` set to the page files, `pictures` set to the stills and paintings, and
`propLettering` set to the file `calculators/list_prop_lettering.py` writes, so every number shown, every picture's
period and every word on a prop is checked.

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
- Fix what it finds, run `explainer-film-preflight pages` again (fixes make new faults), look again, and
  record each fault and its fix in Lessons.md. Only then run `explainer-film-preflight film` and film.
- Before you say a fix left the other pages unchanged, draw each comparison still at least three times with the old
  and the new code and compare them with `python3 calculators/regression_compare.py --old OLD_FOLDER --new NEW_FOLDER`
  (some pictures come out two ways from run to run: the house sample at 20 s differed in 7.7 percent of its dots by at
  most 7 of 255 with nothing changed). Before you blame a change for a faint speckle, redraw the unchanged old version
  several times first (the control), and say how many pictures and draws you compared.
- Save the critique's findings as JSON and mark each `"status": "fixed"` or `"accepted"` (with `"who"` and
  `"date"`) once dealt with: the `film` stage (`--critique FILE`) refuses a critique, or a `pages` report,
  older than any page file, or with a finding still open.
- If filming has already started: a stretch only needs re-filming if its page changed after the
  stretch started (compare the stretch file's time with the page file's).

## 5. After filming: a fresh helper judges the clip in motion

Stills cannot show a shadow that fades in only when the move starts, a barrel that floats, a one-frame colour change,
or a pale outline that appears only once the camera moves (three separate rounds found faults only this way). After
filming, a fresh helper who did not make the clip (agent `explainer-film:film-critic` in its clip mode) looks at it in
motion: a contact sheet at about 2 frames a second, the frame-to-frame jump list (`paper-film/tools/find_jumps.py`),
and close-ups of the first second after each camera move starts. It saves its findings as the clip critique, a JSON
file shaped `{"film": PATH, "looked_at": [...], "findings": [{"time", "what", "severity", "status", "who", "date"}]}`;
mark each finding `"status": "fixed"` or `"accepted"` once dealt with. The finish stage needs it:
`explainer-film-preflight finish --clip-critique FILE` refuses one older than the film or with a "must fix" finding
still open.
