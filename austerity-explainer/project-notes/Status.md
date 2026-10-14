# Status

What this file is: where the austerity explainer stands right now. Updated after every change.

**As of 2026-10-14, evening.**
Source for the story: Clara E. Mattei, *The Capital Order* (2022).

## Done

- Style, shape, length and sound agreed (see `Decisions.md`); the paper pop-up look approved
  ("This is great!") and the whole chapter approved ("Do it!").
- Chapter 1 research: 29 sourced facts (`research/02 Research - chapter 1 - where austerity came from.md`).
- Chapter 1 narration in Malina's steadier voice, all ten pages, with the time of every word
  (`narration/chapter-1-timeline-steady-accent.json` in chapter 1's original working folder; in the
  repository `film-kit/examples/austerity-chapter-1/timeline.json`), mixed over "Tension and Gravity"
  with the music a little louder (`mix/chapter-1-mix-steady-accent.wav`, not in the repository; the kit
  rebuilds it from the page recordings and the soundtrack).
- **Chapter 1 in the paper look, finished.** The paths below are chapter 1's original working folder
  (an earlier session's machine). In the repository: paintings and masks in
  `film-kit/assets/paintings/austerity-chapter-1/`, pieces in `film-kit/paper-film/pieces/austerity-chapter-1/`,
  cut list, recordings, word times and timeline in `film-kit/examples/austerity-chapter-1/`, pages in
  `film-kit/paper-film/scenes/austerity-chapter-1/`, filming script `film-kit/paper-film/tools/film-chapter.sh`.
  Chapter 1's film files, its mix as a .wav, and the one-page pictures (logs 15 and 16) and their
  scripts are not in the repository.
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

- **The film kit is in the repository** (2026-10-13): `austerity-explainer/film-kit/`, complete for both
  chapters: every painting (chapter 1 as JPEG copies, chapter 2 as PNG), the paper pieces already
  made, painted rooms with depth, the Blender models and their build scripts, the stage and page
  files, all tools, chapter 1's page recordings, and both chapters as worked examples. Rebuilt from a
  clean copy, six test pictures (two of chapter 1, four of chapter 2) matched the originals exactly.
  Left out on purpose: the soundtrack (the repository is public). Chapter 2's raw depth pictures from
  fal are in `chapter-2-inflation/pictures/depth-from-fal/`; its mix and narration as lossless .flac in
  `mix/` and `narration/` (the mix matches the original sample for sample; the narration is 24-bit,
  within -138 dB of the 32-bit original).
- **A reusable kit for new series** (log 14, first version): `kit/paper-pop-up-film-kit/` on that
  session's machine, sent as three zip files
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

## Chapter 2: what really causes inflation (finished 2026-10-12)

- Sent: `chapter-2-inflation/deliver/19 Chapter 2 - what really causes inflation.mp4` (4 min 30 s,
  27 MB), `19 Captions - chapter 2.srt` / `.vtt`, `19 Cover - chapter 2 - what really causes inflation.jpg`.
- Script with research ids: `chapter-2-inflation/19 Script - chapter 2 - what really causes inflation.md`;
  research ledger (72 facts, 21 more from the script check, and a second fact check of 31 claims):
  `18 Research - chapter 2 - what really causes inflation.md`; raw recheck `fact-recheck-2026-10-12.json`.
- Sound: `chapter-2-inflation/narration/` (ten recordings, transcripts, word times, timeline) and
  `mix/chapter-2-mix.mp3`.
- Pictures: `chapter-2-inflation/pictures/` (11 paintings and masks, 12 painted rooms with depth, 29
  cut-out pieces; the politician's original blue tie kept as `politician-face-blue-tie-original.png`).
- Film code: `chapter-2-inflation/film-code/` (cinema stage, kit, models, effects, graphics, the ten
  pages, tools); the page guide `19 Guide - building a cinema page.md`.
- Checks: 8,110 frames, 30 a second; sound 0.00 ms off at every page; -15.0 LUFS, peak -1.6 dB;
  every page's stills checked before filming; independent critique (7 critics and a skeptic), fixes,
  and an independent check of the fixes; page turns checked in one run; the finished film looked at
  every 3 seconds. Not checked: the voice by ear, full-speed playback, a phone screen.
- The round-19 full-quality master (902 MB) is not kept (too big for the repository).

## Chapter 2, round 20 (finished 2026-10-13)

- Sent: `chapter-2-inflation/deliver/20 Chapter 2 - what really causes inflation.mp4` (4 min 30 s,
  27.6 MB), `20 Captions - chapter 2.srt` / `.vtt` (the same narration as round 19),
  `20 Cover - chapter 2 - what really causes inflation.jpg`. Round 19's files are kept for the record.
- What changed (your seven screenshots and camera rule): the camera holds still except for at most
  three named moves a shot (21 shots, 0 problems on the camera check); detailed Blender models of the
  two works, the town, near-corner props and the reviewer's desk (`chapter-2-inflation/pictures/models/`,
  built by `film-code/blender/`, improved through the Blender MCP server); the politician's face calmed;
  price tags and basket clear of everything; page 9's book bigger and further back; page 5's street
  repainted dry, with coins that land and stay; the review on a detailed desk.
- Guides: `20 Guide - camera rule, filling the frame, no clipping.md`, `20 Blender MCP notes - detailed models.md`.
- Checks: 8,110 frames, 30 a second; sound 0.00 ms off at every page; -15.0 LUFS, peak -1.6 dB;
  seven page helpers, an independent reviewer, fixing helpers, a fresh reviewer, a last fix check;
  the finished film looked at every 3 seconds; the only black moments are planned dips between shots.
  Not checked: full-speed playback, a phone screen.
- The full-quality master (808 MB) is not kept in the repository (too big for GitHub); it can be filmed
  again from `austerity-explainer/film-kit/` (stage, pages, pieces, models, tools) with the mix and
  timeline in `chapter-2-inflation/` (about 6 hours; the filming tool keeps every 60 frames, so stops
  lose little).

## The plugin (2026-10-12)

- `plugins/explainer-film` (version 1.1.2: the 3D models skill now covers stand-ins, log 24) with `.claude-plugin/marketplace.json` at the repository root. Nine skills,
  four workflows (verify-facts, critique-film, check-fixes, build-pages), three helper definitions,
  the setup command `explainer-film-setup`, and the film kit. Passed `claude plugin validate`; a fresh
  setup drew a picture end to end. Not tested: installation by another person or a smaller model.

## SAM 3D test (log 22, 2026-10-13)

- Snapshot: `experiments/22 Snapshot - SAM 3D petrol station.jpg`. Scene:
  `film-kit/paper-film/scenes/sam-3d-petrol-station-test.js`; models and layout in
  `film-kit/assets/models/sam-3d-test/`; clean background and masks in `film-kit/assets/reliefs/sam-3d-test/`;
  tools `sam3d_fit_layout.py`, `sam3d_make_clean_plate.py`, `composite_fill.py`, `ground_under_objects.py`.
- Works from the painting's view and on a short push; still wrong: ghost edges on two pumps, a pump
  head left on the background, lifted rear wheels when moving, the headlight pool under the bumper,
  and the painted background tearing. Not tried in a moving shot.

## 3D petrol station, first test (log 24, 2026-10-13)

- Comparison sheet: `experiments/24 Test - 3D petrol station.jpg`. Plan: `experiments/23 Plan - 3D
  petrol station with painted light.md`. Scene: `film-kit/paper-film/scenes/station-proxies-test.js`
  (views painting, push, push-side, original, original-push), shared code `painted-projection.js` (also
  in the plugin's kit); tools `fit_station_proxies.py`, `station_plates.py`; boxes in
  `film-kit/assets/models/station-test/proxies.json`; cleaned background in
  `film-kit/assets/reliefs/station-test/`.
- Passed both pass marks: matches the painting from its own view (mean 4.08 levels, 6.4% of pixels
  off by more than 12); on a 1.25 times push the posts and canopy stay straight and slide in front of
  the kiosk. Checked by two independent helpers.
- Still wrong: the smear behind the station shows on a sideways step; the bollard lies flat; the left
  pump has no display head; small edge rims around the 3D car and pumps; a faint strip beside the rear
  post. Not done: forecourt and road as 3D, queued cars as upright cut-outs, real lamps, a moving shot.
  No cost.

## Working files (log 25, 2026-10-13)

- Rule from you: save everything to the repository except videos and audio.
- Saved in `working-files/`: chapter 2's check pictures and models (2,323 files, 1.3 GB) and 25
  filming and setup pictures. Index: `working-files/25 Working files - what is here.md`.
- Stopped by the safety check, waiting on you: notes, scripts, logs and this session's working folder.
- Left out on purpose: other people's publications and code, installed software.

## The look from chapter 3 on (log 26, 2026-10-13)

- Reports in `experiments/`: "26 Review - design of chapter 2 and a direction", "26 Research - fully
  3D scenes and cheap effects", "26 Plans - the look from chapter 3 on". Recommended: plan 2, the
  house. Nothing built yet; no cost.

## The house sample (log 27, 2026-10-13)

- 37 seconds, music only, sent as "27 Sample - the house" (not in the repository: video). Frame sheet:
  `experiments/27 Sample - the house - one frame a second.jpg`. Scene: `film-kit/paper-film/scenes/
  house-sample.js` with `house-sample/page-1.js` and `house-set.js`; timing `film-kit/examples/
  house-sample/timeline.json`. Checked by two helpers before filming and one after. No cost.

## Plan 3 test clip: the pit village (log 29, 2026-10-14)

- A pit village street at dusk in May 1926 built in Blender: 28 cottages, a colliery with a steel
  headframe, two winding houses, gas lamps, and 46 props (Poly Haven CC0 models and props built by
  script with real lettering). Scripts: `film-kit/paper-film/blender/pit-village/`; models:
  `film-kit/assets/models/pit-village/` (the street, the lockout set, the props, the paintings).
- Drawn once from the main camera, repainted by Flux 3 edit (four repaints and one props-removed copy
  in all, about 50 US cents), and the paintings shone back onto the set
  (`film-kit/paper-film/scenes/projected-set.js`): the painting, a second painting with the near props
  painted out for what they hid, the painted sky alone on a far card, and the notice board's own sharp
  surfaces. Clip scene: `film-kit/paper-film/scenes/lockout-test.js`, timing
  `film-kit/examples/lockout-test/timeline.json`.
- 12 seconds, music only: BRITAIN 1926, a move up the street, a cut to the lock-out notice, LOCKED OUT /
  FROM 1 MAY 1926. Two rounds of three independent critics (looks, history, faults) and a motion check
  of the filmed clip; filmed, scanned frame by frame and sent as "29 Test - pit village lockout" (not in
  the repository: video). Frame sheet: `experiments/29 Test - pit village lockout - two frames a second.jpg`.

## Composition test and why it works (log 30, 2026-10-14)

- Our empty street and ten prop pictures given to Nano Banana Pro (twice: our camera, its own camera),
  Flux 3 (our camera) and Seedance 2.5 (a 10-second draft video). Results in `experiments/` ("30 Test -
  composed by ..."); the exact requests in "30 Composition test - the four requests"; the pictures sent
  in "30 Composition test - pictures given to the models". The Seedance video was sent, not saved to
  the repository (video).
- Judged by three critics and a skeptic: Nano Banana Pro's own-camera picture is composed best (the user
  agrees); Seedance's way of moving is best; nothing the programs made can go on screen (their notices
  are garbled).
- Why the own-camera picture works: measured with the new `film-kit/paper-film/tools/measure_composition.py`
  and checked by five critics and a skeptic. Every strong thing points at the notice corner. Checked
  reasons, the measurements and a rebuild plan (worked out by calculation, not yet drawn in Blender):
  `experiments/30 Why it works - ...`.
- A main rule and twelve more, each with a check, for placing props and the camera:
  `film-kit/07 Composing a shot.md` (also in the plugin's kit documents).

## The picture you liked, rebuilt, and the shot checker (log 31, 2026-10-14)

- The notice corner rebuilt in the 3D street with our props (`film-kit/paper-film/blender/pit-village/
  assemble_notice_corner.py`, shared helpers in `set_dressing.py`), the camera matched to the picture you
  liked, then relit after four critics. Pictures: `experiments/31 Notice corner - ...`.
- The shot checker: `film-kit/paper-film/tools/check-shot.sh` (with `check_shot.py` and
  `paper-film/blender/shot_facts.py`), explained in `film-kit/07 Composing a shot.md`; also in the plugin.
  Its tests: `paper-film/blender/tests/run-checker-tests.sh` (eleven planted faults, each named first).
- The rebuilt frame passes 30 of 36 checks; open: the quiet side's weight (34%, aim 40) and the notice's
  warmth from below (0.07, need 0.10). Two critics and a skeptic are checking it before the repaint.
- Painted and filmed in log 32 (below).

## The notice corner, painted and filmed (log 32, 2026-10-14)

- Three rounds of critics' fixes made in 3D (`assemble_notice_corner.py`, `set_dressing.py`), then the
  final still ("32 Notice corner - relit and checked", 32 of 38 checks pass) and the plate drawn.
- Painted by Flux 3 with the critics' painter words, plus a copy with the near props painted out; both lined
  up with the plate by the new `paper-film/tools/align_painting.py` (`film-kit/assets/models/pit-village/
  notice-corner-painted.jpg`, `notice-corner-behind.jpg`, their record in `notice-corner-paintings.json`).
- Filmed: "32 Test - notice corner slide" (13 seconds, music only, a section of your soundtrack at
  -17.7 LUFS; not in the repository, like every video). Frames: "32 Notice corner - the film, two frames a
  second". New tools: `add_music_bed.sh`, `find_jumps.py`.
- The shot checker learnt five things this round (colour edges, out-of-date pictures, touching stretches,
  background props, lights in props); its 11 planted-fault tests still pass.
- Spent this round: about 20 to 45 US cents on fal (two paintings).

## Waiting on you

- Your view of the notice corner slide ("32 Test - notice corner slide").



- Your view of chapter 2 (round 20) on your phone.
- Before publishing: whether page 10's "is raising" still holds after 28 October.
- Nothing for chapter 1 (you said "This is fantastic."). The kit is ready to hand to the agent making
  the series on the enclosures.
- The working files the safety check stopped (log 25): notes, scripts and logs from chapter 2's
  working folder and the film kit, and everything in this session's working folder (including the
  chapter 2 files held back earlier). All checked: no passwords, keys or personal details. They exist
  only on this machine and are lost when the session ends.

## Not started

- Chapters 3 onward (where austerity was tested; Thatcher; social spending; New Zealand and
  Australia; what it did to people; bargaining power; why it is oppressive).

## Spend so far

Picture allowance: about US$5.40 left of the "upto $10 in Fal" given when chapter 2 started (about
US$4.58 spent since). About US$10.30 in all (composition test, log 30: about US$2.80, of which Seedance's
draft about US$2.06, Nano Banana Pro 30 US cents, Flux up to about 43 US cents; plan 3 test, log 29:
about 50 US cents for five Flux repaints;
SAM 3D test, log 22: about 12 US cents; chapter 2: about US$1.16 on fal, of which about 10 US cents in round 20 for the dry
bank street, and about 4,300 ElevenLabs credits, about 75 US cents).
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
  `bash paper-film/tools/film-chapter.sh austerity-chapter-1` from inside `austerity-explainer/film-kit/`);
  changing the shared kit or the stage means filming all of it.
- ElevenLabs download links expire after 2 hours; download recordings as soon as they finish.
- The video's first frame is page 1's empty parliament; use the cover picture where an app lets you
  choose one.
- The sent copy is squeezed under 30 MB; the master is the one to upload anywhere that takes large files.
