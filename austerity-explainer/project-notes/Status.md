# Status

What this file is: where the austerity explainer stands right now. Updated after every change.

**As of 2026-10-12.**
Source for the story: Clara E. Mattei, *The Capital Order* (2022).

## Done

- Style, shape, length and sound agreed (see `Decisions.md`); the paper pop-up look approved
  ("This is great!") and the whole chapter approved ("Do it!").
- Chapter 1 research: 29 sourced facts (`research/02 Research - chapter 1 - where austerity came from.md`).
- Chapter 1 narration in Malina's steadier voice, all ten pages, with the time of every word
  (`narration/chapter-1-timeline-steady-accent.json`), mixed over "Tension and Gravity" with the music a
  little louder (`mix/chapter-1-mix-steady-accent.wav`).
- **Chapter 1 in the paper look, finished:**
  - Paintings: `downloads/fal/chapter-1-paper/` (47 pictures and their masks; ledger `00-requests.json`)
    plus page 3's in `downloads/fal/page3-paper-test/`.
  - Paper pieces: `paper-film/pieces/chapter-1/` (10 backgrounds, 55 pieces), made from the cut list
    `paper-film/scene-data/chapter-1-cut-list.json`.
  - Page files: `paper-film/scenes/chapter-1/page-1.js` to `page-10.js`; chapter scene
    `paper-film/scenes/chapter-1.js`; shared motions and page kit `paper-film/scenes/paper-kit.js`.
  - Film: `paper-film/out/chapter-1-silent.mp4` (pictures only, joined from one chunk per page in
    `paper-film/out/chapter-1-chunks/`) and the master with sound `paper-film/out/chapter-1-paper-master.mp4`
    (290 MB).
  - Sent: `deliver/13 Chapter 1 - where austerity came from - paper pop-up.mp4` (28.2 MB),
    `13 Captions - chapter 1.srt` / `.vtt`, `13 Cover - chapter 1 - the capital order.jpg`.

- **A reusable kit for new series** (log 14): `kit/paper-pop-up-film-kit/`, sent as three zip files
  (`deliver/14 Paper pop-up film kit - part 1 of 3 ...`, `part 2 of 3 ...`, `part 3 of 3 ...`; 20.8, 17.5
  and 24.8 MB). Tools made general for any series, with austerity chapter 1 as the worked example, a
  new-chapter template, and instructions for another agent (start page `00 START HERE.md`).

- **A one-page picture with origami props** (log 15): `deliver/15 One page - blank page with origami
  props in lamplight.png` (1080 x 1920). Scene `paper-film/scenes/one-page-origami.js`, drawn with
  `paper-film/tools/draw-one-page-still.mjs` and finished with `tools/finish_one_page_still.py`. No cost.
  You said "Yeah like that. But it's not aesthetically beautiful", which led to the next picture.
- **A one-page picture of an open pop-up book** (log 16): `deliver/16 One page - open pop-up book in
  lamplight.png` (1080 x 1920). Scene `paper-film/scenes/one-page-open-book.js`; drawn with
  `paper-film/tools/draw-one-page-still.mjs` (which also saves a distance picture) and finished with
  `python3 -I tools/finish_one_page_still.py DRAWN.png FINISHED.png --focus 790 1150`. No cost.
  Not yet approved.

## Checks run on the kit

- Unzipped all three parts into an empty folder, installed the engine, rebuilt the paper pieces from
  the kit's paintings and drew two moments: they match the kit's example stills (largest difference
  4 of 255 on a few pixels, which is drawing noise).
- The kit's sound tools rebuild chapter 1's word times, timeline, narration track, mix and captions
  byte for byte the same as this project's.
- The kit's film script read the page edges from the scene (the same as this project's), filmed the
  last page and joined all ten into 6,641 frames; the finishing script made a 26.5 MB copy with the
  sound lined up to 0.00 ms at every page.
- The kit drawing the example with this project's own pieces matches this project's stills (two
  identical, three differing by at most 5 of 255 on a few pixels).
- Not checked: the kit on another computer (other operating systems, other browser versions), and
  the new-chapter template running (it needs a new chapter's narration and paintings first).

## Checks run on chapter 1 (paper look)

- Picture: 1080 x 1920, 30 frames a second, 6,641 frames, 3 min 41.37 s (counted in the sent copy).
- Sound lines up with the pictures: 0.00 ms at the first word of every page (measured in the sent copy
  against the mix).
- Loudness of the sent copy: -15.1 LUFS; highest true peak -1.7 dB.
- Joins between the page chunks: the picture changes no more across a join than between the frames
  either side (measured at all nine joins).
- About 85 single moments checked at full size before filming; contact sheets of every page at one
  frame a second after filming; shadows checked with the lamp alone.
- Compression of the sent copy compared with the master on busy frames (crowd, tank, boards, page
  turn): fine detail a little softer, nothing broken.
- Not checked: watching at full speed (only single frames can be looked at here), and how it plays on
  a phone screen.

## Chapter 2: what really causes inflation (started 2026-10-12)

- Research ledger: `chapter-2-inflation/18 Research - chapter 2 - what really causes inflation.md`
  (72 sourced facts, ids C2-H, C2-C, C2-N, C2-M; 43 unconfirmed claims listed and kept out).
- Three outlines: `chapter-2-inflation/18 Outlines - chapter 2 - what really causes inflation.md`
  (A back to the shell factory, my pick; B what happened next; C five price tags). Each about 4 minutes,
  ten pages, about US$1.50-1.75 of new paintings and about 3,500 ElevenLabs credits.
- Nothing recorded, painted or spent.

## Waiting on you

- Your choice of outline for chapter 2.
- Nothing for chapter 1 (you said "This is fantastic."). The kit is ready to hand to the agent making
  the series on the enclosures.

## Not started

- Chapters 3 onward (where austerity was tested; Thatcher; social spending; New Zealand and
  Australia; what it did to people; bargaining power; why it is oppressive).

## Spend so far

About US$5 in all.
- fal, about US$4.25: chapter 1's paintings, about US$2.55 (17 large pictures at about 10 US cents,
  30 small ones at about 2.5 cents, 37 cut-out masks at about a fifth of a cent); the page 3 test,
  about 82 US cents; the five animated style samples, about 90 US cents.
- ElevenLabs: about 75 US cents counted by text length (about 4,200 credits); the reports for the
  later re-recordings show 0 credits charged. Transcripts were free.
- Filming and everything else: no cost.

## Traps

- Chapter 2's newest New Zealand figures (4.1% inflation in the year to June 2026) may be replaced
  on 22 October 2026; check before recording.
- Re-recording any page of chapter 1 moves every time after it: redo the timing, the mix and the
  filming for the whole chapter (see `Workflows.md`).
- Changing one page's file means filming that page's chunk again (delete it and run
  `paper-film/tools/film-chapter-1.sh`); changing the shared kit or the stage means filming all of it.
- ElevenLabs download links expire after 2 hours; download recordings as soon as they finish.
- The video's first frame is page 1's empty parliament; use the cover picture where an app lets you
  choose one.
- The sent copy is squeezed under 30 MB; the master is the one to upload anywhere that takes large files.
