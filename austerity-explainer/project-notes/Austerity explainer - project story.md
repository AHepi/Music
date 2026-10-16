# Austerity explainer - project story

## The goal

A 15 to 20 minute narrated explainer for a tall phone screen, made of painted pictures moved like
paper (the paper pop-up look you chose in log 12; the old-scrapbook look came first), telling where
austerity came from and what it does, from Clara E. Mattei's book *The Capital Order* (2022), seen
through the eyes of economists who study how modern money works (never named in the film).
Easy to understand, yet thorough; conversational and a little urgent. Narrated by your voice Malina,
over your soundtrack "Tension and Gravity".

Because the whole film is big, it is being built one chapter at a time. Chapter 1 is a test:
about 3 and a half minutes on where austerity came from and why it was put in place.

## Where things stand

- **The plugin can now work out the settings we used to search for by hand** (log 35): calculators, one
  command per stage, 344 house numbers and 163 tips for AIs, version 1.3.0, about 780 checks passing.
- **Chapter 2's full redesign is being built** (log 34; rounds 5 and 6 below it): the Works (pages 3 to 5) built in 3D over four
  rounds, filmed with the plain 3D pictures standing in for paintings; round 5 is fixing the last critic's
  findings and starting the supermarket checkout (page 1). The people test is painted: painted men work,
  dark figures don't (log 34). About 85 US cents spent from the US$20; nothing recorded yet.
- **Chapter 2 rewritten for newcomers** (log 33): "33 Script - chapter 2 - what really causes inflation -
  for newcomers" and its narration file, ready to record. One idea, one picture (two factories), four
  real cases in time order, three guesses, every unfamiliar word explained; about 7 and a quarter
  minutes. Tested in two rounds by fresh helpers (imagined newcomers, facts, rules and voice, a skeptic)
  and fixed; not yet heard by a real newcomer, recorded or filmed.
- **The notice corner, painted and filmed** (log 32): "32 Test - notice corner slide" (13 seconds, music only).
  The picture you liked, rebuilt in our street with our props, fixed after three rounds of critics, painted
  in the series' style and filmed as one slow slide toward the notice without turning. Checked in motion by
  helpers; the one fault they found (the fire's shadows fading off the pavement) is fixed. The shot checker
  passes 32 of 38 checks on the finished still, and on the film's own end frame the notice is lit from below
  and the frame is balanced. You kept it ("Yes keep it", decision 38).
- **The picture you liked, rebuilt in our street, and a tool that checks a shot** (log 31): the notice
  corner rebuilt with our own props and sharp notice, the camera matched to the picture you liked, then
  relit after four critics ("31 Notice corner - rebuilt and lit"; side by side in "31 Notice corner - before
  and after"). The new shot checker measures a 3D shot against the composing rules and says what is wrong
  and what to change, in metres ("31 Notice corner - checked by the tool" and its report). Tested on eleven
  faults planted on purpose (each named first) and by five independent helpers. The rebuilt frame passes 30
  of its 36 checks. Painted and filmed in log 32 (above).
- **Why a shot looks arranged, worked out** (log 30, the composition test): fal's picture- and
  video-making programs were given our empty street and our props to arrange. Nano Banana Pro, choosing
  its own camera, made the picture you liked ("30 Test - composed by Nano Banana - own camera"). Measured
  and checked by critics, it works because every strong thing in it (where the street's lines meet, the
  brightest parts, the biggest near props, the warm light, the touching group of props) points at the
  notice corner; in our clip they point at three different places. Seedance's 10-second video showed a
  better kind of move (one approach up the street, barely turning, with a long slowdown) but can't be
  used as it is. None of the programs' pictures can go on screen: the notices are garbled. A main rule
  and twelve more for future shots are in the film kit ("07 Composing a shot"). Recommended next: rebuild
  that picture in our own 3D street.
- **A 12-second test of plan 3** ("29 Test - pit village lockout", log 29): a 1926 pit village street
  built in 3D in Blender, repainted by Flux in the series' style, with the painting shone back onto the
  3D street so the camera can move up it, then a cut to a sharp, readable lock-out notice and LOCKED
  OUT / FROM 1 MAY 1926. Music only. Your view: the props look great, the arrangement and the camera
  move don't (log 30).
- **Chapter 2, "what really causes inflation", is remade with your round-20 changes**: "20 Chapter
  2 - what really causes inflation.mp4" (4 minutes 30 seconds, 27.6 MB), with captions ("20 Captions
  - chapter 2", .srt and .vtt) and a new cover ("20 Cover"). The camera now holds still except for
  your named moves (at most three a shot); the factories, the town and the reviewer's desk are
  detailed models made in Blender; the six picture problems from your screenshots are fixed. It
  replaces "19 Chapter 2", which is kept for the record. Each page is a 3D scene timed to Malina's
  words, with documentary titles, figures and charts on top, joined by page turns.
- **A plugin, "explainer-film"**, holds the whole method (skills, workflows, helper definitions, the
  film engine and tools) so another model can make the next chapter. It is in your repository under
  `plugins/explainer-film` and installs with `/plugin marketplace add AHepi/Music` then
  `/plugin install explainer-film@ahepi-music`.
- **Chapter 1 is finished in the paper look**: "13 Chapter 1 - where austerity came from - paper
  pop-up.mp4" (3 minutes 41 seconds), with captions ("13 Captions") and a cover picture ("13 Cover").
  All ten pages pop up, crash in and turn like a book on Malina's words; no hands.
- **The film kit is in your repository** at `austerity-explainer/film-kit/`, complete for both
  chapters: every painting, the paper pieces, painted rooms, Blender models, the stage, page files,
  tools, chapter 1's recordings, and both chapters as worked examples, with step-by-step instructions
  for the agent starting a series on the enclosures. Only your soundtrack is left out, because the
  repository is public. (Its first version was three zip files, "14 Paper pop-up film kit".)
- **A test of 3D models lifted out of a painting** ("22 Snapshot - SAM 3D petrol station", log 22): the
  petrol station's red car and pumps rebuilt as 3D models that wear the painting. Close to the
  painting from its own view and solid on a short push; the painted background still tears on moves.
  Waiting for your view.
- **A first test of the petrol station itself as 3D** ("24 Test - 3D petrol station", log 24): the
  canopy posts, canopy, kiosk and pump island are simple 3D shapes that wear the painting, with the
  painting's own light kept. From the painting's view it matches the painting; on a push in, the
  posts and canopy stay straight where today's painted room bends them. A sideways step still shows a
  rough smear behind the station, and the forecourt and road are not 3D yet.
- **The working files are being saved to your repository** (log 25), all but videos and audio:
  chapter 2's 2,300 check pictures and its models are in `austerity-explainer/working-files/`. The
  rest (notes, scripts, logs, this session's working folder) was stopped by the safety check and waits
  for your decision.
- **A 37-second sample of "the house"** ("27 Sample - the house", log 27): Britain in the 1920s as one
  cut-away building at night, from the cuts of 1922 to the miners' lockout of 1926, with music and no
  narration. Built free from chapter 1's paintings and cut-outs. Waiting for your view.
- **A review of chapter 2's look, research on fully 3D scenes, and four plans for chapter 3 on**
  (log 26, in `experiments/`). Recommended: "the house", each chapter staged in one cut-away
  building of society, decisions at the top and work and homes at the bottom. Waiting for your
  choice; its first test costs nothing.
- **A one-page picture with origami props** ("15 One page"): a blank page at an angle on a dark desk,
  with a folded cottage, trees, crane and fence, lit by one low warm lamp. You liked the idea but not
  the beauty, so it led to the next one.
- **An open pop-up book** ("16 One page"): an open book floating in the dark, seen from the reader's
  chair, with a pop-up countryside cut from one ivory paper, lit by a reading lamp, moonlight and the
  cottage's glowing windows. Waiting for your view.
- **The narration is the steadier voice**, with the music a little louder ("10 Narration").
- The earlier scrapbook film (08), the five animated samples (10) and the page 3 test (11) are kept
  for the record; the new film replaces them.
- Spent so far: about US$10.60 in all (log 32: about 20 to 45 US cents for two paintings; log 31 spent nothing): about US$2.80 for the composition test (log 30), about 50 US
  cents for plan 3's paint-overs (log 29), about 12 US cents for the SAM 3D test (log 22), about US$5 for
  chapter 1 and earlier (ElevenLabs about 75 US cents; fal about US$4.25), and about US$1.91 for chapter 2
  (US$1.16 on fal for 12 paintings, depth maps and 3 masks, and about 4,300 ElevenLabs credits, about 75
  US cents).

## How the pieces fit

**A concrete example first.** On page 3 Malina says "union membership doubles, to eight million."
That sentence comes from the script, which took the fact from research entry C1-08 (4.1 million
in 1914, 8.3 million in 1920). ElevenLabs recorded the page and reported that she starts saying
"doubles" 56.48 seconds into the chapter (with the steadier voice). Page 3's file asks for "doubles",
gets 56.48 seconds, and folds the second, bigger crowd up from flat 0.1 seconds before it, so the
crowd doubles as she says it. Your soundtrack plays underneath, dipping while she talks.

**The pieces, in order:** (these are chapter 1's original working-folder names; in the repository the
same tools and files are in `austerity-explainer/film-kit/`, under `narration-tools/`, `paper-film/`
and `examples/austerity-chapter-1/`)

1. **Research ledger** (`research/02 ...`): every fact, its source, how sure we are. Hands facts
   to the script.
2. **Narration text** (`narration/chapter-1-narration.json`): exactly what Malina reads on each
   page, with delivery cues. Hands it to ElevenLabs.
3. **Recording** (ElevenLabs, voice Malina): one recording per page, plus a transcript giving the
   time of every word. Hands both to the timing tools.
4. **Timing tools** (`tools/extract_word_times.py`, `tools/assemble_chapter_narration.py`): put the
   pages end to end with short pauses, level the voice, and write the chapter timeline. Hand the
   narration track to the mix and the word times to the drawing code.
5. **Mix** (`tools/mix_chapter_narration_over_music.sh`): lays Malina over your soundtrack, turns the
   music down under her voice, sets the loudness for phones. Hands the sound to the final film.
6. **Drawing code** (the anidoodle skill, scrapbook style): draws every page on its words (cards laid
   down, words typed, cut-out letters, engravings cut line by line, red pen, stamps), turns the pages,
   and makes a silent picture-only film. Hands it to the final film.
7. **Final film**: the pictures and the mixed sound joined into one video file, plus a captions file
   made from the same word times, and a cover picture.

**The paper look (now used for the whole chapter), in order:**

8. **Paintings** (fal, Flux 3): one background per page, and each figure or object painted on its own
   on plain grey, checked on contact sheets. Hands the pictures to the cutting step.
9. **Cutting** (fal's background remover, then `paper-film/tools/prepare_paper_pieces.py` reading the
   cut list `paper-film/scene-data/chapter-1-cut-list.json`): cuts each figure out with a paper margin,
   matches its colours to the backgrounds, repairs what the remover missed, prints labels (the book's
   title, TAX, ROYAL COMMISSION), splits speaking figures into face, jaw and mouth. Hands paper pieces
   to the stage.
10. **Paper stage** (`paper-film/stage/`): a small 3D world with one lamp, where every picture is a
    sheet of paper standing a little in front of its page; it also makes words, printed cards,
    posters, dust and smoke. Hands finished frames to the filming tool.
11. **Page files and chapter scene** (`paper-film/scenes/chapter-1/page-1.js` to `page-10.js`, with
    `paper-kit.js` and `chapter-1.js`): each page file says, from Malina's word times, when each piece
    folds up, slides, drops, crashes or folds away; the chapter scene stacks the sheets, turns each
    page just after its last word and moves the camera. Example: on "tanks" (65.96 seconds into the
    chapter) the tank lands, the camera shakes and dust bursts out.
12. **Filming** (`paper-film/tools/film-chapter-1.sh`, using `render-paper-film.mjs`): films one page
    at a time and joins the pages into a silent film. Hands it to the finishing step.
13. **Finishing** (`tools/finish_chapter_1_paper_film.sh`, `tools/make_captions.py`,
    `tools/check_sound_alignment.py`): joins the mix, makes the copy small enough to send, writes the
    captions, and measures that sound and pictures line up.

**Chapter 2, so far (the same pieces as chapter 1, one step earlier):**

14. **Research ledger for chapter 2** (`chapter-2-inflation/18 Research - chapter 2 - what really
    causes inflation.md`): 72 facts in four parts (C2-H the history after chapter 1, C2-C real cases,
    C2-N New Zealand now, C2-M how inflation works), each with its source and how sure it is. Written
    from the research results (`chapter-2-inflation/research-and-outlines-raw.json`) by
    `tools/write_research_ledger.py`. Hands facts to the outlines.
15. **Outlines** (`chapter-2-inflation/18 Outlines - chapter 2 - what really causes inflation.md`):
    three ways to tell the chapter, page by page, each fact tied to a ledger id. The one you choose
    becomes the script, which then follows the same path as chapter 1 (recording, timing, mix,
    paintings, paper pieces, page files, filming, finishing).

**Chapter 2 in the cinema look (a concrete example first).** On page 3 Malina says "and prices climb"
at 66.98 seconds. Page 3's file asks for "climb", and at that moment the flip counter on the second
card factory flips from £1.25 to £1.60 to £2.00 while coins stack up beside it and a red label
PRICES CLIMB draws its line to the counter; the camera is already close on the counter, with the
factory behind it softly out of focus. Every moving thing in the film is timed like that, to a word.

16. **Script** (`chapter-2-inflation/19 Script - chapter 2 - what really causes inflation.md`): the
    words Malina recorded, each page with the research ids its facts come from. Hands the words to
    the recording.
17. **Recording and sound** (`chapter-2-inflation/narration/`, `mix/chapter-2-mix.mp3`): ten
    recordings, their transcripts (the time of every word), the chapter timeline and the mix over
    your soundtrack. Hands the word times to the pages and the mix to the finishing step.
18. **Painted rooms with depth** (`chapter-2-inflation/pictures/`): 11 new paintings plus four from
    chapter 1, each with a distance picture, turned into rooms the camera can move a little way into;
    and 29 cut-out pieces. Hands them to the pages.
19. **Cinema stage and page files** (`chapter-2-inflation/film-code/`): the stage draws each page as a
    3D scene with lens blur, glow and a film finish, with flat documentary graphics on top, and joins
    pages with a page peel. The ten page files say what happens on each word. Hands pictures to the
    filming.
20. **Filming and finishing** (`film-code/tools/film-chapter-parallel.sh`, then the kit's
    `finish_film.sh`, `make_captions.py` and `check_sound_alignment.py`): films the chapter in 35
    short stretches, two at a time, joins them, adds the mix, squeezes a sendable copy, writes the
    captions and checks the sound lines up.
21. **Fact recheck** (`chapter-2-inflation/fact-recheck-2026-10-12.json`, summarised at the end of the
    research ledger): every spoken and on-screen fact checked again from fresh sources after
    recording. Hands any changes to the page files.
22. **Independent critique and fix check** (workflows `critique-film` and `check-fixes`): critics look at
    the pictures, the words on screen and the code; a skeptic confirms each finding; after the fixes,
    fresh checkers confirm each one and look for new problems. Hands fixes to the page files.
23. **The plugin** (`plugins/explainer-film`): all of the above as instructions, workflows, helper
    definitions and tools, so another model can make the next chapter. Hands the method on.
24. **Blender models** (`film-code/blender/`, models in `pictures/models/`):
    scripts that build the two brick works, the model town, the near-corner props and the reviewer's
    desk in Blender, bake their corner shading, and save each as one model file (.glb). The Blender
    MCP server was used to inspect and improve them. Hands finished models to the cinema stage, which
    lights and films them.
25. **Camera and frame checks** (`film-code/tools/camera_audit.py`, `frame_check.py`): the first
    measures every shot of the film against your camera rule (still unless a move is needed, at most
    three moves a shot); the second says where each object lands in the tall frame for a camera
    position, before anything is drawn. Hands problems back to the page files.
26. **3D stand-ins in a painting** (test only; `film-kit/paper-film/tools/fit_station_proxies.py`,
    `station_plates.py`, scene `station-proxies-test.js`, shared code `painted-projection.js`): fits
    simple boxes to the edges of near, upright things in a painting (posts, a canopy, a kiosk), paints
    those things out of the background picture, and dresses each box in the painting shone onto it
    from where it was painted. Hands the boxes and the cleaned background to the cinema stage.
27. **A built place, painted over (plan 3)** (`film-kit/paper-film/blender/pit-village/`, models in
    `film-kit/assets/models/pit-village/`). A concrete example: the lock-out notice is a real 3D board
    with a printed paper on it, its lettering drawn by script ("PITS WILL BE CLOSED from SATURDAY, 1st
    MAY, 1926"). Blender draws the whole street once from the main camera (the plate); Flux repaints
    that picture in the series' style; the film shines the painting back onto the same street, so the
    camera can move up it. The notice keeps its own sharp lettering, so the close shot can read it.
    - `build_street.py` builds the street, cottages, lamps and colliery; `props/` builds or converts
      the 46 props; `assemble_lockout.py` places the props for the shot, draws the plate and exports
      the set and the camera. Hands the plate to Flux and the set to the film.
    - Flux 3 edit (fal) repaints the plate, and then paints the near props out of the painting.
      Hands two paintings to the film.
    - `projected-set.js` shines the paintings onto the set: the painting where the camera saw a
      surface, the props-removed painting where a near prop hid it, the painted sky alone on a far
      card, and the sign's own surfaces. Hands a moving, painted street to the cinema stage, which
      films it like the other pages.

28. **The shot checker** (`film-kit/paper-film/tools/check-shot.sh`; explained in "07 Composing a shot").
    A concrete example: given our first camera for the notice corner, its report's first fix was "Lower the
    camera about 0.42 m; move it about 0.29 m to the left; turn it about 1.0 degrees left".
    - `paper-film/blender/shot_facts.py` runs in Blender after the scene script: it draws every prop in its
      own flat colour (as the camera sees it, and alone) and writes the camera, where the street's lines
      meet, the lights, and each prop's distance, size and what it stands on. Hands these to the checker.
    - `paper-film/tools/check_shot.py` checks every composing rule it can (and the reference picture, if the
      check file names one) and writes `report.md` (problems worst first, each with a fix in metres) and
      `marked.jpg`. Hands the fixes to whoever changes the scene script; then it is run again.
    - `paper-film/blender/tests/run-checker-tests.sh` breaks the notice corner on purpose in eleven ways and
      checks that each report's first fix names the planted fault.

## Word list

| Word | Plain meaning |
|---|---|
| Austerity | Government cutting public spending, making borrowing dearer and holding wages down. |
| The capital order | Mattei's name for a world where a few own the land, factories and mines, and everyone else must work for a wage to live. |
| Research ledger | The list of every fact used, each with its source. |
| Page | One page of the film: one stretch of narration (about 10 to 30 seconds) with its own pictures. Chapter 1 has ten. |
| Delivery cue | A word in square brackets, like [urgent], that tells the voice how to say the next line. It is not spoken. |
| Ducking | Turning the music down automatically while the voice speaks, and back up in the pauses. |
| LUFS | A measure of how loud something sounds to people. About -15 is usual for phone video; more negative is quieter. |
| Credits | ElevenLabs' units of payment; about 1 credit per letter of script with this voice. |
| Transcript | ElevenLabs' written-out version of a recording, with the time each word starts and ends. |
| Page turn | The move from one page to the next. In the paper look the bottom-right corner lifts, rolls over showing the plain back of the paper, and uncovers the next sheet (log 11 calls it the page peel). In the scrapbook film the next page slid in from the right. |
| Rest | A moment where nothing new is drawn while Malina keeps talking. Planned, never longer than 1.7 seconds (2.5 on the end card). |
| Engraving | A picture made only of fine lines, like an old printed plate; here it is cut line by line on screen. |
| Captions file | A small text file (.srt) holding the words and when they are spoken; apps show them as subtitles. |
| Quality gate | The drawing skill's own checklist: the same picture every time, nothing forbidden in the code, and something visibly moving every second. |
| Style sample | A 6-second animated clip showing one possible look for the film. All five show the same scene so only the look differs. |
| fal | An online service that runs picture- and video-making programs; you pay per second of video made. |
| Video model | A program that makes a short video from a written description. It invents details, so every clip has to be checked. |
| Paper piece | A painted figure, object or word cut out like paper, with a narrow off-white margin, standing a little in front of its page. |
| Pop up | A piece folding up from lying flat to standing, hinged on its bottom edge, like a pop-up book. |
| Paper mouth | A figure's jaw cut out as its own piece, sliding down and up with the loudness of Malina's voice. |
| Lamp | The one light in the paper world, upper left; it gives every piece a soft shadow on the page behind. |
| Cut-out mask | A black-and-white picture marking which part of a painting is the figure; made by fal's background remover. |
| True peak | The loudest instant in the sound. Kept under -1 dB so phones don't distort it. |
| Sheet | One painted background printed on a sheet of paper, the page's backdrop. Most pages have one; pages 3 and 8 have two (one turns over to show the next), and the film ends on a plain dark one. |
| Cut list | The file that lists every painting and paper piece, with its paper margin, colour nudge, size and any repairs or printed words. The cutting tool works from it. |
| Chunk | One page's stretch of the film, filmed on its own and then joined to the others, so one page can be filmed again without the rest. |
| Master | The full-quality film with sound (about 290 MB for chapter 1, about 800 MB for chapter 2): too big to send here or to keep in the repository; it can be filmed again from the film kit. |
| Sendable copy | The film squeezed under the 30 MB limit for sending files here, in the most common video format so any phone or computer plays it. |
| Kit | The reusable copy of the tools, paintings and instructions for making other films in the paper look. |
| Folded prop | A paper object built as a real folded shape with flat faces (not a painted cut-out), so each fold is lit differently. |
| Distance picture | A grey picture of how far every point is from the camera (near dark, far light), drawn alongside a still so the finishing tool knows what to blur. |
| Background blur | Softening what is nearer or farther than the point in focus, the way a camera lens does close up; it makes a model look photographed. |
| Inflation | Prices in general going up over time, usually measured over a year: the whole shopping basket, not one price tag. |
| New money | Money a government or its central bank creates, rather than collects in tax or borrows from savers. |
| Central bank | The bank that issues a country's money and sets its main interest rate. New Zealand's is the Reserve Bank. |
| Interest rate | The price of borrowing. Raising it is the usual cure for inflation: loans cost more, people spend less. |
| Flat out | Every worker and machine already busy, so new money can't make more things, only push prices up. |
| Honest edge | The part of the chapter that admits creating money does push prices up when it's spent where nothing more can be made. |
| Outline | A page-by-page plan of a chapter: what Malina says and what appears, before any script is written. |
| Verdict card | In outline C, a paper card stamped with what caused each price rise: the money, a shortage, or where it was spent. |
| Cinema look | Chapter 2's look: each page is a real 3D scene with a camera that moves like a film camera, light, depth and film grain, with documentary graphics on top, still joined by page peels. |
| Painted room with depth | A painting pushed back into 3D using its distance picture, so the camera can move a little way into it and near things shift against far ones. |
| Card model | A simple 3D object built in code from flat card surfaces (factory, house, price tag, flip counter, dial), lit by the lamp like a real model. |
| Flip counter | A board of little flaps that flip to show a new price or number, like an old station departures board. |
| Hook | A few big words on screen, a short form of what Malina is saying. |
| Callout | A short label with a thin line pointing at something in the picture. |
| Dip to black | A very quick fade to black and back, used to hide a cut from one place to another within a page. |
| Page helper | A helper agent that builds one page file from the written guide, checks its stills and reports back. |
| Fact recheck | A second check of every fact, by checkers told to try to prove each one wrong from fresh sources. |
| Still shot | A stretch of a page where the camera holds still, except for at most three named camera moves. The engine refuses a fourth. |
| Camera move | One of the moves from your camera rule: zoom in or out, pan left, right, up or down, move up or down. |
| Blender | A free program for making 3D models. Here it builds the factories, town, props and desk by script; the cinema stage films them. |
| MCP server | A small program that lets me drive another program through a set of named tools. Blender's official one also gives building advice and searches Blender's manual. |
| Triangle | The small flat pieces a 3D model's surface is made of. More triangles means finer shapes, but slower drawing. |
| Baked shading | Soft shadows in corners and creases worked out once in Blender and painted onto the model, so the stage doesn't have to work them out every frame. |
| Camera check | The tool that measures every shot's camera against your rule and lists any that break it. |
| Frame check | The tool that says where each object will land in the tall frame for a camera position, before any picture is drawn. |
| Near corners | The bottom corners of the frame, closest to the camera. Filled with soft barrels, crates and a cart so the bottom third isn't empty. |
| Button zone | The strip down the right side and along the bottom of a phone video where apps put their like and share buttons; words are kept out of it. |
| SAM 3D | A tool on fal (by Meta) that turns things in one picture into separate 3D models, one per thing, each with its own painted surface and its place in the picture. |
| Clean plate | A copy of a painting with some things painted out, so 3D models of those things can stand in their place. |
| Projection | Shining the painting onto a 3D model from where it was painted, like a slide projector, so the model wears the painting's own brushwork wherever the painting showed it. |
| Stand-in | A simple 3D shape (here a box) put where something in a painting stands, dressed in the painting, so it looks the same from the painting's view and stays solid when the camera moves. |
| Push | The camera moving straight forward into the picture. "A 1.25 times push" makes things ahead look a quarter bigger. |
| Safety check | An automatic guard on the machine I work on that stops anything that could leak data out of it. It can stop a step even when you asked for it; then you decide. |
| Set | A real 3D place built from shapes and models, which the camera can move through without tearing. |
| Paint-over | Flux repainting a plain picture of a set in the series' painted style, keeping the shapes where they are. |
| Splat world | A 3D place made of millions of soft coloured dots, made by a paid service from one picture. |
| Background still | The unchanging part of a still shot, drawn once and reused behind everything that moves. |
| Cut-away | A building shown with its front taken off, like a doll's house, so every room can be seen at once. |
| Plate | The one picture Blender draws of a set from the main camera; Flux repaints it, and the painting is shone back onto the set from the same spot. |
| Projector | The camera the plate was drawn from, used in the film to shine the painting back onto the set. |
| Behind painting | A copy of the painting with the near props painted out, worn by the road and walls those props hid, so moving past them uncovers painted street. |
| Weights view | A check picture of a projected set: orange where it wears the painting, green the behind painting, blue its own surface. Blue at a frame edge means the camera left the painting. |
| Own surface | A 3D object's own pictures and colours, not the painting; signs keep theirs so their lettering stays sharp. |
| Ghost outline | A prop's painted outline left lying on the road behind it once the camera moves, because the painting can't tell the prop's edge from the road. |
| Composition | How the things in a picture are arranged: where each stands, how big and how bright it is, and so where the eye goes. |
| Where the lines meet | The spot where a street's straight lines (kerbs, gutters, roof edges) run together in the distance. It moves only when the camera turns, not when it slides. |
| Brightest parts | The brightest 3 per cent of a picture after a slight blur: where the eye tends to land first. |
| Weight | How strongly each part of a picture pulls the eye, from its size, brightness and detail. |
| Nano Banana Pro | Google's picture-making program on fal; it can combine up to 14 pictures into one new picture. |
| Seedance | A video-making program on fal (by ByteDance) that makes a short video from a description and several reference pictures (this test sent 11). |
| Flux 3 | Black Forest Labs' picture-making program on fal; it repaints our plain pictures in the series' style and takes at most ten pictures at once. |
| Seedance draft | Seedance's quick, small, cheaper first version of a video (480 pixels wide); it can be finished at full size within 7 days without being made again. |
| Shot checker | Our tool that measures a 3D shot against the composing rules and says what is wrong and what to change, in metres. |
| Flat-colour picture | A picture of the scene with each prop painted in one plain colour, so a program can tell exactly where each prop is on screen and what hides what. |
| Reference | The picture a shot is meant to match (here, the one you liked). |
| Camera match | Finding the camera that lines up the reference's landmarks (wheel hubs, chimney top, gate, roofline, kerbs) with our street's. |
| Near-touch | Two edges at different distances that just meet on screen, which makes near and far things look stuck together (rule 4). |
| Render log | The notes Blender writes while drawing a picture; "Shadow buffer full" in it means some shadows came out wrong. |
| Light linking | Blender's way of choosing which objects a light reaches: the warm light aimed at the notice reaches only the notice and its board. |
| Lining up a painting | Undoing the small stretch and shift a painter adds, so the painting's edges land exactly on the 3D props when it is shone back. |
| Music bed | A stretch of music laid under a clip that has no narration, faded in and out. |
| Newcomer | A viewer who hasn't seen chapter 1 and doesn't know the subject. |
| The quiet factory and the flat-out factory | Chapter 2's picture: two factories, each standing for a whole country. In the quiet one, workers wait at the gate; in the flat-out one, everyone is already working as hard as they can. |
| Guess | A question at the end of a page ("Have a guess"), with about 4 seconds held in the film so the viewer can think. |
| Recap | The main rule said again in exactly the same words, so the second time feels familiar. |
| Listener questions | A few questions to ask a real newcomer after they hear the script, to see if the idea landed; in the script file under "Before recording". |
| Workflow | A set of helpers that run in a fixed order, each doing one job (for example four testers, then a fixer, then a re-checker). |
| Words a minute | How fast Malina reads. Measured on chapter 2: 164 (planned: 140). |

## Log (added to, never rewritten)

01. **Style chosen.** Drew three style samples. You chose the old scrapbook, a tall phone screen,
    15 to 20 minutes, and a narrator with quiet music. You asked if it was too big; we agreed to
    build a 2 to 3 minute test chapter first.
02. **Researched chapter 1.** 29 facts, each with a source. Some websites refused automated
    reading; facts only they could confirm were left out.
03. **First script.** Written in a formal voice. Not sent; replaced by 05 after you said it
    sounded like a lecture.
04. **Voices and sound.** Recorded three stock narrators reading the opening (about 12 US cents of
    credits) before you chose Malina; those are not used. Recorded the formal opening in Malina and
    mixed it over your soundtrack. Two problems fixed on the way: the mix came out 3 seconds short
    (a sample-rate change inside the loudness step), and the music dipped 31 dB under the voice,
    nearly vanishing; it now sits about 18 dB under while she speaks. Replaced by 05.
05. **Conversational rewrite.** Rewrote the script using your Pinker toolkit (start from what the
    listener knows, one plain name for each thing, a concrete case before each idea) and a more
    urgent tone. Recorded the new opening in Malina with delivery cues, with Mattei said the
    Italian way (mat-TEH-ee). Checked: the cues were not read aloud, and the word timings match
    the real pauses in the recording. New sound check made.

06. **Test picture.** Drew page 5 (the capital order) as a real page of the film: cut-out title,
    an engraved temple with two columns, two typed cards naming what each column stands for, red-pen
    arrows, a red-pen crack and "COULD FALL?". Close-ups at double size found three engraving faults
    (shadows ruled like graph paper, a doorway like chain-link fence, flat columns with a spiky top);
    all three fixed and re-checked. The page keeps its words clear of where phone apps put their
    buttons and captions, which leaves the bottom of the page quiet on purpose.

07. **Narration recorded and timed.** You said "Do it." Recorded pages 2 to 10 in Malina, one page
    at a time (about 2,950 credits, by the length of the text), downloaded them straight away, and
    got a transcript of each (free) for the time of every word. Checked: no delivery cue was read
    aloud (each lasts under a fifth of a second and sits in a pause), and the word times match the
    real pauses in the recordings. Laid the pages end to end with pauses of 1.1 to 1.7 seconds,
    levelled each page to the same loudness, and mixed them over your soundtrack: the music sits about
    18 to 21 dB under her voice while she speaks and about 12 dB under in the pauses (measured page by
    page). One problem fixed: levelling pushed the voice's peaks past full scale; the final limiter now
    holds them at -1.6 dB. Sent "07 Narration preview". Wrote "07 Script - chapter 1 - as recorded".

08. **Chapter 1 drawn and made into a film.** Drew pages 1 to 4 and 6 to 10 and re-timed page 5, so
    every card, typed word, cut-out letter, engraving line, red-pen mark and stamp lands on the word
    it belongs to. Three new engravings: five 1915 field-gun shells, an Italian factory (a red flag
    goes up at "take over their factories"), and three gold bars (the red pen draws a padlock at "a
    limit they chose"). Pages turn by laying the next one over the last. Close-ups found and fixed:
    marks tied to the wrong word where a word is spoken twice on a page; a cut-out T that read as I
    ("THREE PARIS"); a stamp covering the last letter of MATTEI; a candle poking into the header; two
    cut-out rows colliding; a flag too small to read; shells and gold bars small and off-centre.
    Rendered the 6,524 frames (19 minutes) and joined them with the mix. Found the sound 5 milliseconds
    late (the limiter's look-ahead) and corrected it: now 0.00 ms at every page. Loudness -15.0 LUFS,
    true peak -1.5 dB after encoding. The skill's quality gate: 13 of 14 checks pass. A typing pause it
    took for a freeze is now declared as a rest. The one check still failing flags 18 stretches of
    about a second where the only movement is a thin red-pen line or small typing beside a planned rest;
    the check looks at the picture at a quarter of its size, where those marks hardly show. Not fixed,
    because the marks are deliberate and making them bigger would change the look. Made a captions file
    from the word times and a cover picture (page 5). The first film file (37 MB) was too big to send
    here (30 MB limit), so the sent copy is compressed to 25 MB; side by side with the original, the
    engraving lines look the same. Re-checked the sent copy: sound lines up (0.00 ms), -15.1 LUFS,
    true peak -1.8 dB, all 6,524 frames.

09. **Voice fix, tested on pages 1 to 4.** You heard the accent switch early in the film, and
    shouting, and suggested New Zealand accent rules in ElevenLabs. I looked: ElevenLabs' documentation
    has no accent rules for a voice (only pronunciation rules that fix one word at a time, which this
    connection can't attach) but its newest model follows an accent instruction written into the script.
    Measured the old recordings: pages sat at very different voice heights (page 3 about 5 semitones above
    page 4), matching the mixed mood cues ([urgent], [serious] and so on); capitals added pushed emphasis.
    Rewrote the narration: the same New Zealand accent instruction opens every page, no other cues, no
    capitals, Mattei said in English sounds. Researched the sounds of standard New Zealand English as a
    listening guide ("09 Research - New Zealand accent"). Re-recorded pages 1 to 4: the gap in voice height
    between pages fell from 5.3 to 1.8 semitones. Not settled by measuring: whether it sounds New Zealand,
    and whether every push is gone; the voice still rises on some words (as it did before), which may be
    ordinary emphasis. Sent "09 Voice test". Fixed on the way: the timing tool read the words inside the
    long accent instruction as spoken words; it now treats everything in brackets as the instruction.

10. **Whole chapter re-recorded; louder music; five looks.** You said the voice "sounds a bit
    Australian. It'll do for now", asked for the music "slightly" up, and asked for five 2D animation
    styles from fal that bring out discontent and conflict, with few colours but not simple drawing.
    Recorded pages 5 to 10 like the test, got their word times (free), and fixed an old problem on the
    way: ElevenLabs placed each page's first word up to 0.32 seconds late; the timing tool now moves it
    to where the voice really starts (nine pages corrected). Raised the music 3 dB: measured about 18 dB
    under Malina while she speaks (was about 21). Sent "10 Narration". Made five 6-second samples of
    the same scene (Glasgow, 1919) with fal's MiniMax video model, about 90 US cents: revolutionary
    poster (red, black, cream), charcoal lithograph (soot black, sepia), linocut print (black, off-white,
    rust), painted gouache (slate blue, grey, ochre), graphic-novel night (blue-grey with red). Removed
    their own sound (one had a made-up shouted line). Checked frame by frame and found faults the real
    film must avoid: all five drew Second World War tanks and had a tank face the crowd (the research
    says troops and tanks came after the clash); the linocut put a symbol like a hooked cross on a
    placard; the night sample added a real movement's red-and-black flag. Not yet remade: the film
    itself, which waits on your choice of look.

11. **Paper pop-up test, page 3.** You showed four pictures from a history channel and asked for
    still painted images moved like paper or card on a surface, with no hands: pop-ups, book page
    turns, a paper mouth, things crashing in (a tank crashing into a cheering crowd), and few plain
    words that only help memory. Looked up what makes cut-out and pop-up animation read as paper
    ("11 Research - paper pop-up style"). Painted eight pictures with fal (Glasgow square, two crowds,
    soldiers, a First World War tank, a pithead, a miner, a report), about 82 US cents with the
    cut-outs; checked each one (the tank came out the right shape this time; a small pale fin on its
    roof that could read as a flag was cut away). Built a paper stage: every picture is a sheet in a
    small 3D world with one lamp, filmed by a hidden browser. Problems found and fixed on the way: no
    shadows at all (flat sheets lit from the front cast none until set to cast from both faces); the
    smoothest soft shadows do not work in the hidden browser, so softened plain ones are used; shadows
    too small to see, then word shadows so big they read as a second word; a page turn that swung like
    a door and left white strips (now a corner peel, with pieces folding away first); a mouth like a
    black bar (now a narrower jaw that opens on louder syllables); dust hidden behind the crowd.
    Filmed the test (23 seconds, about 12 minutes of computer time) on Malina's page 3 words with the
    new mix: -15.0 LUFS, 19 MB.

12. **Look approved; chapter planned.** You said "This is great!" about the page 3 test. Planned all ten
    pages in the paper look: what flips up, slides, drops or folds away on which word, and the few
    words on screen ("12 Plan - chapter 1 in paper pop-up"). About 70 pictures to paint, about US$5
    (up to US$8 with re-paints). Nothing painted yet.

13. **Chapter 1 made and filmed in the paper look.** You said "Do it!". Painted 47 pictures with fal
    (8 page backgrounds, 8 big figures, 30 objects, 1 re-paint), about US$2.55 with the cut-outs, and
    checked every one on contact sheets. Two failed: the shells looked like rifle cartridges
    (re-painted as artillery shells and cut into seven separate shells) and a new tank came out an odd
    shape (page 3 keeps the approved one). Laying every cut-out over magenta showed what the background
    remover had dropped: the politician's lectern (put back), Sardinia on the map of Italy (the map is
    now printed on a small paper card) and part of a coal heap (kept with a lower threshold). Rebuilt
    the cutting tool to work from one cut list for the whole chapter (page 3's pieces came out
    identical to the approved test, checked pixel by pixel). Wrote one file per page and a chapter
    scene that stacks the sheets like a book, turns each page 0.3 seconds after its last word (pieces
    fold away first) and moves the camera. Checked about 85 single moments at full size before filming
    and fixed: three words spoken twice looked up by their first time ("war", "get", "prices"); dust
    that lingered after its page; knocked-down pieces showing as pale blobs; pieces cut off at the frame
    edge; a falling word washed out by dust and a ghost shadow; a division by zero in a walk. Filmed
    6,641 frames one page at a time (about 80 minutes; two at once was no faster). After filming, a
    close look found the worker's cap peeking over the slammed door on page 6: made the door taller and
    filmed page 6 again (10 minutes). The joins between pages run smoothly (measured frame to frame).
    Sent copy: 3 minutes 41 seconds, 1080 x 1920, 6,641 frames, 28.2 MB, -15.1 LUFS, true peak -1.7 dB;
    sound lines up to 0.00 ms at the first word of every page (measured against the mix). The full-
    quality master (290 MB) stays in the project. New captions from the steady-accent word times (121
    lines, none longer than 42 letters; "Clara E. Mattei" is no longer split at the "E."). Cover: page 5.
    Not checked: how it feels to watch at full speed on a phone (I can only look at single frames), and
    whether every entrance lands where you would want it.

14. **A kit for new series.** You said "This is fantastic." and asked for the assets and reusable tools in a
    zip with clear instructions, for another agent to start a series on the enclosures. Made
    `kit/paper-pop-up-film-kit/`: the paper film tools made general for any series (page turns, camera
    and filming work from any list of page files; the film script finds where pages end by itself; the
    browser and label font are found on any computer; the narration tools take their pauses and folders
    as settings), this chapter as the worked example, a template for a new chapter, the 53 paintings as
    high-quality JPEG with their 43 masks and the exact prompt of each (recovered from fal's request
    history), your soundtrack, and seven instruction files (a plain start page for you; the full path
    from script to film for the agent; the look in your own words; how a page file works; painting
    prompts; lessons; your rules for running a project). Packed as three zips under the 30 MB limit
    (20.8, 17.5 and 24.8 MB). Tested: unzipped into an empty folder, installed, rebuilt the pieces and
    drew two moments, which match the example; the sound tools rebuild this chapter's sound byte for
    byte; the film script filmed and joined a page; the finishing script made a 26.5 MB copy with the
    sound lined up. Two mistakes in the kit's papers were caught on re-reading and fixed (the shells
    filed as a figure; a wrong word count). Not tested: another computer or operating system; the
    new-chapter template (it can only run once a new chapter has its recordings and paintings).

15. **A one-page picture with origami props.** You asked for "a blank page on and angle with the props
    like origami" and "some mood lighting to cast a shadow". Built it in the paper stage at no cost: an
    A4-shaped blank page turned at an angle on a dark wooden desk, its corner curling up; a folded
    cottage, three trees, a paper crane and a zig-zag fence standing on it; one low warm lamp from the
    front left making a pool of light and long shadows, with a faint cool light from behind. Took nine
    test pictures. Two things failed on the way: the trees came out almost black because they were
    shading themselves (fixed by changing how shadows are kept off a surface), and the crane did not
    read as a crane from above (turned side-on with wings raised, camera lowered). Checked the whole
    picture and close-ups. Not checked: how it looks on your phone screen.

16. **An open pop-up book.** You said "Yeah like that. But it's not aesthetically beautiful", and asked
    for an open book seen as if reading it at a desk (no desk), with intricate pop-ups whose shading
    sells the drama, leaving the look to me. Built it in the paper stage at no cost: a red cloth book
    with curved pages, small printed type and page numbers; rising from it, all in one ivory paper,
    three layers of hedged hills with a church, a paper moon with hanging stars, cypresses, a three-layer
    lacy oak, a cottage with scalloped shingles, cut windows and a smoke curl, a picket fence with roses,
    sheep and a grass strip. Warm reading lamp, cool moonlight, and a warm light inside the cottage
    glowing through its windows and open door. Finished like a photograph (window glow, very slight lens
    blur, soft corners, grain). Took 14 test pictures. Failures on the way, all fixed: the oak's leaves
    cut off by its sheet edge; the pages reading as upright walls; rings and criss-crossing shadows; a
    too-coarse distance picture and a blur that ate the detail; light leaking out of the back windows.
    Checked the whole picture and close-ups of the oak, moon, hills, cottage and sheep. Not checked: how
    it looks on your phone. Unsure: the sheep are still the weakest part (white on white; their shadows
    read more clearly than they do).

17. **Chapter 1 packed for handing over.** The research, notes, decisions, tools and rules behind
    chapter 1 were packed into one zip ("17 Chapter 1 - research notes, decisions, tools and rules").
    (Recorded here from the zip you uploaded; the session that made it isn't available, so this entry
    has no more detail.)

18. **Chapter 2 researched; three outlines.** You asked for part two on inflation, explained within
    the first video, with about three outlines before anything is made, up to US$10 on fal for
    paintings and ElevenLabs only for speech, and every helper at medium effort. Set the project up
    in your repository (chapter 1's notes, research, scripts and rules, copied from the zip). Four
    research helpers gathered 72 sourced facts (the history after chapter 1, real cases, New Zealand
    now, how inflation works); 43 more claims they could not confirm were left out. Three outlines
    were drafted from three angles (back to the shell factory; what happened next; five price tags)
    and each was checked against the facts, your rules and chapter 1, then fixed. The checks caught,
    among others: a line saying today's price rise is "mostly fuel" (wrong: without fuel it's still
    2.9%); "too strong for too long" put on the wrong report; Britain's money creation shown beside a
    0% inflation figure that really came from falling fuel and food prices; and Germany in 1923 said
    to "stop" making coal and steel (the sources say only that output fell). Ten helpers in all, about
    17 minutes. No cost. Not checked: Mattei's book itself; official Reserve Bank and Statistics New
    Zealand pages, which refused automated reading (their figures come from bank and news reports and
    your deficits report). A pull request couldn't be opened, because the repository has only this one
    branch.

19. **Chapter 2 made, in a new cinema look.** You said "Definitely A. But I want you to elevate the
    visuals. Mix 2d with 3d with compelling animation and motion graphics. I'll leave the aesthetic
    choices to you. It has to be cinematic, yet still carry the informational quality." Later you
    added "Oh and do the research to ensure your facts are correct".
    - **Script:** written from outline A ("Back to the shell factory"), then checked by four fact
      checkers and a rules reader before recording. They found, among others, wrong starting points
      for some figures, "Britain at war was the second factory" (now "close to the second factory"),
      and a Mattei line not marked as hers; all fixed. 21 new sourced facts were added to the ledger
      (C2-X).
    - **Voice:** Malina recorded each page once (no retakes). Measured, not heard: pitch spread 2.2
      semitones across pages (chapter 1: 3.0), no word much louder than the rest. ElevenLabs' own
      transcript heard "Ruhr" and "Mattei" as those words. Mixed at -15 LUFS over your soundtrack;
      4 minutes 30 seconds.
    - **Paintings:** 11 new paintings with fal (a checkout, a dusk skyline of chimneys, Glasgow
      tenements, a noodle shop, the Bank of England, the Ruhr works, a 1973 petrol station, a New
      Zealand street, and pieces), plus distance pictures and three cut-out masks: about US$1.06 of the
      US$10 allowed. Four chapter 1 paintings were reused (parliament, munitions hall, town street,
      factory gate).
    - **The cinema look:** a new stage where each page is a real 3D scene. Paintings become rooms
      with depth the camera can move a little way into; card models (factories, houses, brass
      shells, gold coins, banknote bundles, price tags, flip counters, dials, an oil barrel, paper
      boats) and chapter 1-style cut-outs stand in them, lit by a warm lamp with soft shadows, beams
      of light, drifting dust and smoke; the camera cranes, pushes and drifts like a film camera,
      with focus falling off; a film finish (teal shadows, warm highlights, glow, grain, soft dark
      corners). On top, documentary graphics: place-and-year titles, counting figures, labels with
      pointer lines, bars and charts that draw themselves, a panel of a hundred dots. Pages still
      turn with a page peel.
    - **How it was built:** I built the stage and pages 2 and 3 myself as patterns, wrote a guide,
      and eight page helpers (medium effort) built pages 1 and 4 to 10 in parallel in about 10 to
      16 minutes each. I then checked every page's stills and fixed what was weak: 1920s-dressed
      out-of-work men standing in today's New Zealand street (now the hundred-dot panel, 3 then 6
      empty, echoing page 2's 1915 panel), price tags showing as white slivers before they flipped
      up, a label running into a dial, a stray mark beside every comma on the flip counter, banknotes
      that looked like white bricks, and a bug where one page's words showed on the next during a
      page turn.
    - **Facts checked again** (your request): seven checkers each tried to prove one group of claims
      wrong from fresh, mostly primary sources (Bank of England data, the Federal Reserve's history,
      Bank of Japan speeches, legislation, news reports of Stats NZ and Reserve Bank releases), and a
      final reviewer settled disagreements. Nothing was wrong and nothing needed re-recording. Five
      on-screen changes were made: UP TO +25% (Glasgow rents rose by as much as a quarter, not all
      by a quarter); LOWEST SINCE 1986 (the survey behind "since records began" started in 1986);
      the last of the hundred dots nearly empty (1915 was 0.95%); and two kept as they were with a
      reason: ×4 for oil ($2.90 to $11.65 is 4.02 times) and "about ½% a year" for Japan (the Bank of
      Japan's own figure; with the 2014 tax rise counted it is about 0.6%).
    - **Independent critique** (you asked: "You need to use subagents to double check your work and
      critique it."): seven critics (pictures of three page groups, the words and numbers on screen
      of two page groups, the code) and a skeptic who checked every finding. 4 must-fix and about 20
      should-fix findings were confirmed; 14 were rejected as taste, already fixed or too risky.
      The worst: on the two factories page the price boards were cut off at the right edge and the
      labels were pale on pale walls; page 4's change to "Homes can't be built" looked broken; page
      10's 5.6% never held still and the rate dial slid down as if rates were cut; a party-coloured
      tie; a top-hatted caricature; banknotes and a pay packet landing face-down. Filming was stopped
      (pages 1 to 4 had been filmed), nine fixing helpers repaired every page, then three independent
      checkers confirmed each fix and found four new problems the fixes had caused (a label pushed off
      screen by a camera change, a needle falling on the word "raising", coins landing where the camera
      could not see them, a stray line moved rather than removed). I fixed those and looked again.
    - **The house** (you said: "that 3d house is sparse in detail. It doesn't stand out as visually
      complete."): rebuilt as a detailed card villa (weatherboards, hipped iron roof, chimney with pots,
      bay window under a gable with fretwork, tall sash windows, a verandah with brackets and a railing,
      a panelled door) on a small lawn with a picket fence; two critics (model maker, film director)
      reviewed it and their best points went in. In the street it is turned to show its depth; on the
      model table its tag climbs in arrows rather than pounds.
    - **A plugin** (you asked to "save your workflow and Dev a plugin ... so that other smaller models
      can use the plugin"): "explainer-film", in your repository under `plugins/explainer-film`, with
      a catalogue file so it installs with `/plugin marketplace add AHepi/Music` then
      `/plugin install explainer-film@ahepi-music`. Seven skills (the master steps, research and
      script, fact checking, recording, paintings and cut-outs, building pages, checking, filming and
      finishing), three helper definitions (page builder, fact checker, critic), four workflows
      (verify-facts, critique-film, check-fixes, build-pages), a setup command, and the film kit (engine,
      a commented page template, tools, chapters 1 and 2 as worked examples). It passed the official
      validation, and a fresh setup drew a picture end to end.
    - **Filming:** 35 short stretches, two at a time: 8,110 frames, 4 minutes 30 seconds. The cloud machine
      restarted at about 5pm and silently stopped filming for about 90 minutes, until you asked "Done
      yet?"; it carried on from the 20 finished stretches. Sound lines up to 0.00 ms at every page;
      loudness -15.0 LUFS, highest peak -1.6 dB, the same as chapter 1. The sendable copy is 27 MB: a
      little softer than the full-quality master, with every word and number still crisp. I looked
      at one frame every 3 seconds of the finished film.
    - Not checked: the voice by ear; the film at full speed (only single frames can be looked at
      here); how it plays on a phone; the plugin installed by another person or a smaller model. Cost this round: about US$1.06 on fal and about 4,300
      ElevenLabs credits for the recording (about 75 US cents by the same count as chapter 1).

20. **Round 20: your phone screenshots, the camera rule, Blender.** You sent seven screenshots ("I love
    the fact theirs depth in these. Just a few issues.") and a camera rule ("stay still unless it's
    essential to land an important point ... 3 movements per frame, max"), then added "Oh use
    blender MCP as well".
    - **The camera rule is now part of the engine.** A "still shot" holds still and allows only your
      moves (zoom in or out, pan left, right, up or down, move up or down), at most three per shot;
      a fourth stops the page loading. A checker measures every shot of the film in about ten
      seconds. Before: 9 shots broke the rule (page 1 crept for 20 seconds; pages 3 and 8 never held
      still). After: 21 shots, 0 problems.
    - **Picture 1, the politician's face:** it was about 1.7 times as colourful as the other painted
      people; all three layers (face, jaw, mouth) were calmed to match (pages 1 and 10).
    - **Pictures 2 and 3, the checkout:** the price tags now float in clear air in front of the
      shelves (measured: none within 15 units of the painting, none touching each other); the basket
      stands on the belt (0.05 clear) and fades as it folds away instead of hovering.
    - **Picture 4, the factories:** rebuilt in Blender by script: two detailed brick works (about
      22,000 triangles each, against about 2,000 before) in a model industrial town (terraced streets,
      far works and chimneys, a gasholder, a viaduct, gas lamps), with soft barrels, crates and a cart
      in the near corners. Research on filling a tall frame (miniature and vertical-video
      cinematography) led to low, close cameras, subjects stacked in depth, and chimneys and sky in
      the top third. Pages 3 and 8 were reframed shot by shot with a new tool that says where each
      thing lands in the frame before any picture is drawn.
    - **Picture 5, page 9:** the book is much bigger and stands at the back as the authority; the
      start is wider; the envelope stands clear of the workers and the ground.
    - **Picture 6, page 5:** the bank street was repainted with a dry pavement (about 10 US cents);
      coins now land on the pavement or the towers and stay there; their shadows show only once landed.
    - **Picture 7, the review:** the report now lands on a detailed reviewer's desk made in Blender
      (a leather blotter, a banker's lamp with its own warm light, folders, typed papers, an ink pad
      for the stamp, a pen, glasses, tea, bookshelves); a soft dark band keeps the words readable.
    - **The Blender MCP:** Blender Lab's official server was installed and run without a screen on
      this machine (Blender 5.2.2, checksum checked), and registered with Claude Code for later
      sessions; in this session its tools were used through a small client. Its own guidance and its
      bundled manual found two faults in the first models (bevelled edges shading as hard facets, cut
      walls with razor corners), and helpers improved each model through it. The works went from about 22,000 to about 34,000
      triangles each (bevelled edges now shade smoothly, brick openings have soft corners, 232 parts
      joined into 19), the town to about 63,000 with more street detail, the props to about 5,600,
      and the desk got smoother wood, a softer lamp shade and pale glasses. A before-and-after judge
      looked at each in the real film frame and caught three details that read as something else on
      a phone (stone blocks by the gutters that looked like little cameras, figured wood that looked
      like a contour map, dark lenses that made the reading glasses look like sunglasses); all three
      were fixed.
    - **Checking:** seven page helpers, an independent reviewer (which failed three pages), seven more
      helpers, a fresh reviewer (one page left, fixed), then a last check of the fixes. It found three more, all fixed and measured: page 2's SUPPLY
      SHIPS SUNK label sat where phone apps put their buttons (moved in); works B's door looked
      different on pages 3 and 8 (the look now lives in the shared set, so both pages match); and a
      $$$ tag sat in the same button zone (moved in).
    - **Filming:** 35 stretches, two at a time: 8,110 frames, 4 minutes 30 seconds, about 7 hours from
      start to finish (the pages with detailed models drew at 12 to 16 seconds a picture, the others
      at about 3). It was stopped twice: by the 2-hour limit on background jobs, and by the cloud
      machine restarting at 02:53, which lost about 30 minutes of page 3. The filming tool now keeps
      every 60 frames as soon as they are drawn, so the next stop lost nothing; the joins between kept
      pieces measure as smooth as any two frames in a row. Sound lines up to 0.00 ms at every page;
      loudness -15.0 LUFS, highest peak -1.6 dB, the same as before. The sendable copy is 27.6 MB. I
      looked at one frame every 3 seconds of the finished film; the only black moments are the planned
      quick dips between shots (one is new: page 6 is now two shots, to stay within three moves).
      New cover: page 3's brick works at dusk.
    - Not checked: the film at full speed and on a phone; whether Blender's MCP would add more with a
      screen (its screenshot tools need one). Cost this round: about 10 US cents on fal; nothing else.

21. **Everything pushed to your repository.** You said "That's fantastic. Not perfect, but good enough.
    Can you push all assets and scripts to repo."
    - **What went in:** the whole film kit as one folder, `austerity-explainer/film-kit/`, laid out
      exactly like the working kit so it works straight from a copy: chapter 1's 53 paintings and 43
      masks, chapter 2's paintings, both chapters' paper pieces already made, the painted rooms, the
      five Blender models and their build scripts, the stage, all page files, every tool, chapter 1's
      page recordings and transcripts, and both chapters as worked examples. Also chapter 2's raw
      depth pictures from fal, contact sheets, the painting prompts, and the mix and narration as
      lossless sound files. Git keeps one copy of any file that was already there, so it added about
      115 MB.
    - **Checked:** a helper made a fresh copy of the repository and drew six moments from it (two of
      chapter 1, four of chapter 2, including the Blender factories and desk); all six were identical
      to the working kit's, pixel for pixel, with no missing files. The sound check read the new
      lossless mix and found the sound lined up to 0.00 ms on every page. Two more helpers checked
      the notes for wrong paths (16 found, all fixed: most still said the kit was in zip files; a fresh
      recheck then found 8 smaller ones, also fixed) and
      looked for anything still missing (nothing that matters).
    - **A fault found and fixed in the plugin:** its test pictures always showed chapter 2's pages,
      whatever chapter was named, because the chapter setting never reached the page. Fixed in every
      copy and tested (a named chapter now loads that chapter's pages); plugin version 1.1.1.
    - **Left out on purpose:** your soundtrack (the repository is public, so the track would be
      downloadable on its own); the full-quality films (about 800 MB each, over GitHub's 100 MB limit);
      the review screenshots (1.3 GB) and old video pieces, which are checking by-products.
    - **Held back for your decision:** chapter 2's working files from this session (session scripts,
      fix briefs, speed tests, round-20 working pictures, drafts, helper results, the painting
      service's job numbers). Claude Code's safety check blocked saving them twice, the second time as
      possible leaking of a password or key. A search found none (only job numbers and this session's
      folder paths), but I stopped rather than force them through. They are kept aside on the working
      machine, which is cleared when this session ends.
    - Not checked: installing the plugin from the repository on another computer. No cost.

22. **WorldSculpt, then a SAM 3D test on a painting.** You asked "Would this help with videos?" about
    WorldSculpt, then said "Hmm. Try SAM 3D in the painted style, compile a scene, then show me a
    snapshot."
    - **WorldSculpt** (checked by two helpers, nothing installed): it turns many posed views of a 3D
      scene, with every object outlined and boxed, into separate 3D models. Not usable here: it needs
      a large NVIDIA graphics card, it isn't offered on fal, and your films start from single
      paintings. A fal tool, SAM 3D, does a similar job from one picture.
    - **The test:** the 1973 petrol station painting (page 7). SAM 3D turned the red car, the teal car
      and the three pumps into 3D models in one run (2 US cents). I worked out how its layout maps onto
      the painting, painted the objects out of the background with Flux 3 (about 10 US cents, used
      only inside their outlines), fitted the real ground under each one, and stood the models on it in
      the film stage. Each model wears the painting itself, projected from where it was painted, on
      every surface the painting showed; only hidden sides use SAM's own surface.
    - **Checked by three helpers over two rounds**, and fixed between them: the teal car was misplaced,
      floating and pink-trimmed (now left painted); one colour over each whole model had turned chrome
      and headlights cyan (now they glow as painted); models floated about half a unit above the
      ground (now 0.01 to 0.03); my colour check was circular (replaced); the models first drew as
      black blocks (their files carry no surface directions, now worked out on loading); my colour
      handling was wrong twice (now the stage's own). Measured at the end: the car's colour within a
      few levels of the painting; the pumps about 10% darker.
    - **Result** ("22 Snapshot - SAM 3D petrol station"): from the painting's own view the scene is very
      close to the painting, with real 3D objects in it. On a short push in, the car and pumps hold up
      as solid painted objects. Still wrong: ghost edges on two pumps and one pump's display head left
      on the background; the car's rear wheels look lifted when the camera moves; the headlight pool
      under the bumper is broken; and the painted background still tears (canopy posts, kiosk).
    - **What it means:** it works for a few solid things in the foreground on short moves. The
      background is now the limit, not the objects: the canopy and kiosk would need their own layers.
    - Not checked: a moving shot (only single pictures). Cost: about 12 US cents on fal.


23. **How to make the station and road 3D, with the light kept.** You said "the petrol station
    itself, the road its on need to also be 3d objects. The rest of the cars and everything else
    remains part of the background. Hmm. How would you do this because lighting is important here."
    - Three helpers each designed one way: a film backdrop approach (simple shapes that wear the
      painting, real lights only where paint can't be right), a full Blender rebuild lit to match the
      painting, and splitting the painting's light into separate layers with AI edits. Two judges, one
      for look and light and one for what this machine can build, both chose the backdrop approach
      (8.5 and 8 out of 10, against 6 to 6.5), with the best ideas of the others grafted on (wet-ground
      glints, a contact shadow under the car, headlight pools from the original painting, a wireframe
      check before any drawing).
    - The plan: "23 Plan - 3D petrol station with painted light" (in `experiments/`). Not built yet. No
      cost.


24. **First test of the 3D petrol station (plan 23).** You said "Go".
    - **What I built** (no cost): the petrol station in page 7's painting as simple 3D shapes
      (stand-ins). The two canopy posts, the canopy, the kiosk and the pump island are boxes fitted to
      their edges in the painting, and each wears the painting shone onto it from where it was
      painted. The red car and the three pumps are the 3D models from log 22. The station was painted
      out of the background picture, so it isn't shown twice.
    - **Light:** the painting's own light is kept exactly; no stage lamp shines on the background or the
      stand-ins. The car and pumps take a small share of the lamp, mainly to shape their hidden sides,
      and their shadows fall on a see-through ground that shows only shadows.
    - **Went wrong on the way, and fixed:** the canopy wouldn't fit as a true rectangle, because the
      painting's perspective isn't consistent (AI paintings rarely are), so it is fitted to its four
      painted corners instead. Ghosts of a post and the kiosk showed in the background until the
      painted-out areas were made wider. The stand-ins came out brighter than the background until
      both were set to show the painting with no lamp. A grey block stood in front of the kiosk until
      the painted-out part of the background was pushed further back. The canopy's underside drew
      dark until surfaces seen almost edge-on were allowed to wear the painting.
    - **Result** ("24 Test - 3D petrol station"): from the painting's own view it matches the
      painting closely: on average about 4 levels out of 255 off, and 6.4% of the picture off by more
      than 12. The posts, canopy and kiosk match best; the pump island least, because of edges around
      the 3D pumps. On a push in, where the film's painted room today bends the posts and makes the
      canopy edge wavy, the 3D posts and canopy stay straight and the posts slide in front of the
      kiosk. Both of the test's pass marks are met.
    - **Checked by two independent helpers.** Both agree the push passes and the sheet is honest. They
      also found: the bollard (the U-shaped rail at the island's end) lies flat and reads as a bench on
      the push; when the camera also steps sideways, the rough smear left where the station was
      painted out shows behind the rear post (a blue, see-through-looking patch with a faint ghost of
      a post in it); the left pump has no display head (from log 22); the 3D car's outline differs a
      little from the painted one; there is a faint strip beside the rear post under the canopy. I
      corrected one caption (it now says the car and pumps are 3D too) and four notes in the code
      that claimed more than the code does, and checked the tidied code draws the same picture.
    - **Not done:** the forecourt and road are still the painted background, not 3D (the plan put the
      forecourt in this test; it didn't bend on this push, so I left it); the queued cars are not yet
      upright cut-outs; no real lamps yet; the shapes' edges were checked against the painting by
      eye, not measured to the plan's 3 pixels; only still pictures, no moving shot.
    - **What it means:** the idea fixes what was breaking: the near, upright parts of the station now
      stay solid on a push. The limit now is what's behind them: the painted-out background is a
      rough smear, and any sideways move shows it. Cost: none.
    - Saved: the code, boxes and cleaned background in the film kit; the method in the plugin's 3D
      models instructions (plugin version 1.1.2).

25. **Saving everything but videos and audio.** You said "That's ok. Just keep saving assets to repo.
    Everything but the videos and audio. Everything else goes to repo."
    - I listed every file made so far that wasn't in the repository: about 3,500 files (1.5 GB) once
      videos, audio, installed software and files already saved were set aside.
    - **Checked by three independent helpers before copying.** No passwords, keys or personal details
      anywhere (every text file was read in full). They found other people's work that must stay out
      of a public repository (a book chapter, central bank papers, pages of Blender's manual, and a
      copy of another author's animation engine), and about 30 MB of Blender renders and textures I
      had missed. One of my own sorting rules wrongly counted some program files as video (the same
      ending is used for both); those files turned out to be the other author's engine anyway.
    - **Saved:** chapter 2's check pictures and models, 2,323 files (1.3 GB), uploaded in four batches
      so each stays under GitHub's limit; also 25 filming and setup pictures. A note in the folder,
      "25 Working files - what is here", lists what is there and what isn't.
    - **Stopped by the safety check** (which guards against data leaking out of this machine): the
      notes, scripts and logs, and anything from this session's own working folder. It stopped three
      tries; I didn't try to get around it. Waiting for your decision.
    - The repository is now about 1.6 GB, more than GitHub's suggested 1 GB, so downloading all of it
      takes longer. Cost: none.

26. **A review of the look, research on 3D scenes, and plans.** You said "That's fine." about the
    files the safety check stopped (left as they are), then asked what's next ("Britain and Italy in
    the 1920s", chapter 3), then: "I need you to set two Opus 5.5 agents on max effort to do the
    following jobs" (a design review of chapter 2, and a search for free tools to make fully 3D
    scenes, including platforms like Tripo, plus cheap effects), "When those two are done, one more max
    Opus 5.5 agent to synthesize the results and put forward alternative plans".
    - **Design review** ("26 Review - design of chapter 2 and a direction"): the paintings, the
      numbers arriving on their words and the returning objects work. The three biggest problems: the
      film looks like a collage of five kinds of image (plain code-built props such as the banknote
      bundles look like soap); the story sits in a middle band and the bottom of the frame is empty
      floor (in about 70% of frames the bottom fifth is more than 30% darker than the middle); people
      are props (copied strips, cut-off heads, empty streets while unemployment is spoken).
    - **Research** ("26 Research - fully 3D scenes and cheap effects"): Blender's fast drawing mode can
      run here with a pretend screen, about 20 seconds a picture (too slow for every frame, fine for
      one background per shot). Object makers (SAM 3D, TRELLIS, 2 US cents a model; Tripo through
      fal, 20 to 40 cents) make single objects, not scenes. Never use Tripo's free plan: its terms
      give Tripo rights to what free users make. Whole-world makers (World Labs) cost about US$1.26 a
      world with a US$5 minimum, need an account and uploads of your paintings. Most effects (rain,
      snow, haze, dust, smoke, flicker) cost almost nothing to draw here.
    - **Plans** ("26 Plans - the look from chapter 3 on"): four plans, checked against the film and
      the tools' own pages: 1. painted places, refilled (cheapest, not 3D); 2. the house (each
      chapter in one cut-away building of society: decisions at the top, public services in the
      middle, work and homes at the bottom, the street in front); 3. built places, painted over
      (Blender sets painted by Flux and shone back); 4. generated worlds (World Labs, about US$10 a
      chapter). Recommended: plan 2, with a free first test.
    - **Found on the way:** the petrol station tear in chapter 2 came from the camera rising during a
      "pan down"; pure turns and pure zooms never tear a painted room. The painting prompts' rule
      "the lower quarter of the picture is the empty floor" is where the empty bottom comes from.
    - **Corrected:** I told the helpers about US$3 was left for pictures. Your "upto $10 in Fal" was
      given when chapter 2 started, and about US$1.28 has been spent since, so about US$8.70 is left.
      Every plan was costed to fit US$3 anyway.
    - Not checked: any paid step; the house itself (nobody has built it yet); filming times for plans
      2 to 4 are estimates. The helpers' test pictures stay in this session's working folder. Cost:
      none.

27. **A sample of the house.** You said "Ok do a sample video of the house and how it would work."
    - **What I built** (no cost): 37 seconds, music only (your soundtrack), with the words on screen
      telling the story. One tall British building at night, cut open at the front: the Treasury and
      the Bank's vault on the top floor, a council-house building site and a school in the middle, a
      factory floor and a kitchen on the ground floor, the mine in the cellar, and a pavement in
      front. The rooms are real 3D boxes; their back walls wear crops of chapter 1's paintings (the
      boardroom, the munitions hall, the kitchen, a town street); the people and objects are chapter
      1's cut-outs. Each room has its own light, so lights go out on a beat.
    - **What happens:** 1922: the floors light up from the top down and are named. THE CUTS: scissors
      appear on the committee's table, then land in the building site; the scaffolding falls and the
      floor goes dark; the school keeps some light. The camera moves in to the vault: BACK ON GOLD, AT
      THE PRE-WAR PRICE, and a padlock lands on the gold. It moves down through the house, dust falling
      from the lit rooms' ceilings, to the mine: COAL OWNERS WANT LOWER PAY, LONGER HOURS, the ceiling
      comes down, the miners bow, their wages packet shrinks. It pulls back: 1926, THE GENERAL STRIKE,
      the factory and mine go dark, the chimneys stop, a crowd fills the street. LOCKED OUT, THE MINERS
      HELD OUT TILL NOVEMBER, THEN LOST, in falling snow. The end: everything dims except the committee
      room (DECIDES) and the miners outside (PAYS): ONE HOUSE, WHO DECIDES, WHO PAYS, with a note that
      it is a sample after Clara E. Mattei's argument and its history is not yet researched. One shot
      with three camera moves, so your camera rule holds.
    - **Checked before filming by two independent helpers**, then fixed: the strike crowd and the
      miners looked as if they stood inside the factory (now a lit pavement and a smaller crowd further
      forward); the scissors fell through the vault (now they start on the committee's table); gold
      dropping into an empty vault wrongly said Britain gained gold (now the gold is there all along and
      a padlock locks it); the shrinking pay was the kitchen's, but the pay cut sought was the miners'
      (moved to the mine); "held out for months" read as a win (now "locked out ... then lost"); the
      "who decides, who pays" idea is Mattei's argument (now named in the note); dark rooms kept glowing
      paper outlines; the miners' lamps glared over their faces; the dust billowed upward; snow fell
      inside the rooms; a flickering slab edge. The facts on screen were confirmed for Britain (the
      1922 cuts, gold at the pre-war rate in April 1925, the owners' demands, the General Strike of May
      1926, the lockout until November).
    - **Checked again after filming, in motion, by a third helper**, which found what still pictures
      can't show: the strike crowd rose out of a pale flat card and later sank through the floor, the
      street miners popped up from flat shapes, the scissors jumped from the table to the building site
      in one frame, the padlock appeared in mid-air with a glow that switched on in one frame, and the
      kitchen ceiling changed colour in one frame. That last one was two surfaces sharing a plane (each
      room's ceiling sat exactly on the slab above it), which flickers as the camera moves. Fixed: the
      surfaces now sit a hair apart; people fade in and out standing up; one pair of scissors travels
      from the table, past the floor below, to the site; the padlock fades in as it drops and its glow
      builds over a few frames; the pavement is wider, so the crowd and the miners stand clearly outside.
      Then filmed again. A frame-to-frame scan of the new film found one more jump: the crowd vanished
      half way through fading out (a cut-out first drawn solid stays solid, then vanishes at half
      opacity); fixed for every fading piece, and the four stretches with fades filmed again. A second
      motion check then found the strike crowd showing as a hard-edged rectangle (the picture is cut
      straight along its bottom and sides), crossfades that overlapped like a double exposure, music
      that came in at once instead of fading in, and the 1925 title lingering through the move down.
      Fixed (soft edges with the crowd's bottom behind the kerb, fades one after another, a 2-second
      music fade-in, the title clears as the camera moves) and the last three stretches filmed again.
    - **Filming:** 1,110 frames in about 33 minutes (about 1.8 seconds a frame, filmed two at a time),
      filmed in full twice and in parts three more times as the checks found faults. The final film
      has no single-frame jumps (checked frame by frame) and the music sits at -17 LUFS with no
      clipping. Sent as "27 Sample - the house" (about 20 MB). As your rule says, the video and music are not in the repository;
      the code, the timing file and a sheet of one frame a second are.
    - **Not done:** new wall paintings (the rooms reuse old ones, so some walls don't quite match their
      rooms, and the vault and mine walls are plain painted surfaces); narration; Italy; checking which
      trades struck first in 1926 (the factory dims to a quarter rather than going dark, until that is
      researched). Cost: none.


28. **The house rejected.** You said "It doesn't. It looks terrible.  The 3d looks fantastic though.
    What were the other options". So the doll's-house idea is dropped, but real 3D stays. The other
    options from log 26 were put back to you: plan 1 (today's paintings, filled better, not 3D), plan 3
    (real 3D places built in Blender, then painted over by Flux so they look painted), plan 4 (3D worlds
    made by World Labs from each painting), and the review's two other looks (the money machine, the
    pop-up book). Recommended: plan 3, the one that keeps the real 3D. No cost.


29. **Plan 3: a pit village built in 3D, painted over (a 12-second test).** You said "Do plan 3. And a
    short clip. Use props as well that are higher quality instead of plain. Don't worry about budget
    because they are reusable. Just no more books and signs with no details."
    - **The place:** Britain, 1 May 1926, the first day of the miners' lockout. A street of 28 stone
      and brick cottages climbing to a colliery, with a steel pithead, two winding houses, a tall
      chimney, gas lamps and a cobbled road, built by script in Blender. 46 props: Poly Haven models
      (free for any use) and props built by script with real lettering: a coal tub on rails, a
      handcart, coal sacks stencilled "J. HARTWELL COAL MERCHANT", the colliery's name board
      "ABBOTSCLOUGH COLLIERY", and a printed lock-out notice. All the names are invented.
    - **How it is made:** Blender draws the street once from the main camera (the plate). Flux repaints
      the plate in the series' painted style. The film shines the painting back onto the same 3D
      street, so the camera can move up it while everything stays painted. A second painting with the
      near props painted out covers the road they hid; the painted sky lands on a far card; the notice
      board keeps its own sharp surfaces so it can be read close up.
    - **The clip:** BRITAIN 1926 over the street at dusk; the camera moves up the street past coal
      sacks and a burning brazier; a cut to the notice ("Owing to the cessation of the Government
      Subsidy, the present Contracts of Service will terminate on FRIDAY, 30th APRIL, 1926, and these
      PITS WILL BE CLOSED from SATURDAY, 1st MAY, 1926, until the Workmen are prepared to accept the
      NEW TERMS"); LOCKED OUT / FROM 1 MAY 1926; fade out. Music only (your soundtrack). One camera
      move a shot, so your camera rule holds.
    - **What went wrong and was fixed along the way:**
      - The notice board floated in mid-air (its posts landed on top of it and at the street's
        start); the brazier's flames rendered as white paper cones (lit by the fire's own lamp).
      - The first repaint garbled the notice's small print, so the notice now keeps its own lettering.
      - The painted clouds had nowhere to land; then the strip of sky behind the pithead showed as a
        pale double edge once the camera moved. Fixed with a sky card wearing the painted sky alone.
      - Turning the camera too far showed a strip of unpainted houses at the frame's edge: the plate is
        only a little wider than the film's frame. The push in is now mostly a lens zoom.
      - Moving the camera uncovered the road behind the sacks and the cart as pale, jagged copies of
        their outlines, then (after a first fix) as dark ink lines: the painter's outlines round the
        props lie on the road. Fixed with the props-removed painting, handed over round the props as
        soon as the camera moves, and soft 3D shadows under the sacks to replace the painted ones.
        Finding why the handover didn't work took three tries: it waited for too much camera movement,
        and a helper step was silently half thrown away by leftover depth in a working picture.
      - A rust stain from a tack hid the A of ABBOTSCLOUGH, and another tack punched a hole in the E of
        NOTICE; both tacks moved.
    - **Checked by two rounds of three independent helpers** (looks, history, faults). The first found
      the ghost outlines, the paper-crown flame, snow-like blotches on a May road (the painter added
      them), sacks shaped like clay jars, too much coal for a lockout (coal was scarce), the colliery
      sign cut to stray letters, and a move that never reached the notice. The second confirmed most
      were fixed and found the remaining ink ghosts, a see-through flame, the cut letters still there,
      a weak end to the move, a pin hole in NOTICE, and gaps of light between the board's planks; all
      were fixed. The history helper checked every line of the notice (30 April 1926 was a Friday,
      1 May a Saturday, 16 April a Friday; the wording matches a real 1926 letter from a colliery,
      National Coal Mining Museum) and suggested the subsidy line, the austerity link: the
      government's subsidy to miners' wages ended on 30 April 1926.
    - **Checked in motion by a fourth helper**, frame by frame, after filming: the switch to the
      props-removed painting is invisible, the cut is clean, the notice's small print holds steady, and
      a frame-to-frame scan finds no jumps except the planned cut at 7.3 seconds. It found the barrel's
      painted scorch ring fading away at 3.4 seconds (the barrel then seemed to float), flames that
      read as a neat row of cartoon teardrops, smoke rising as a stiff sheet, and a small opening title.
      Fixed (a soft shadow under the barrel, flames of three ragged shapes in different sizes and
      leans, drifting smoke, a larger title) and the clip filmed again.
    - **Kept as it is, on purpose:** the two winding ropes run in opposite directions to two winding
      houses either side of the pithead; both houses are hidden behind the cottages from this street,
      so the ropes seem to end at the roofs. A helper flagged it; the 3D is right, the view hides it.
    - **The result:** "29 Test - pit village lockout" (12 seconds, 8.8 MB, music at -17.7 LUFS with no
      clipping). Filmed four times in all (twice stopped part way when checks found faults); the last
      filming took about 40 minutes for 360 frames. A frame-by-frame scan of the final film finds no
      jumps except the planned cut. As your rule says, the video and music are not in the repository;
      the scripts, models, paintings and a sheet of two frames a second are.
    - **Not checked, or unsure:** I have not seen it on a phone. The fourth helper's points were fixed
      and the final film was scanned and spot-checked by me, not by a fresh helper. The notice board's
      wood looks more like a 3D model than a painting in the close shot; the coal sacks are smooth
      pillows rather than lumpy sacks; faint lines from the painted board posts may show beside the
      real posts for the last two seconds of the street move. Filming is slow (about 12 seconds a frame,
      two at once), so a full chapter in this look would take many hours of filming.
    - **Cost:** about 50 US cents on fal (five Flux repaints: four of the street and one with the props
      painted out). About US$8.20 of the picture allowance is left.


30. **The composition test: letting fal arrange the props and move the camera, and why the best
    picture works.** You said "It looks ok. The props look great. But there's no sense aesthetics with
    regards to their composition. The camera movement is a little odd too. Hmm. Try fal. Feed a top
    quality image generator with an image of the background set and images of the props and see how it
    organises everything. Or alternatively, use seedance this way, and see how it composes everything and
    moves the camera" (decision 35).
    - **What was sent:** the same pictures to every program (Flux takes only ten, so it got all but the
      pail): the empty painted street (the props-removed painting from log 29) and ten of our 3D props,
      each drawn alone on grey (handcart, coal sacks, the drum (an oil drum used for a fire), the notice on
      its board, two dustbins, a barrel, a coal tub on rails, a wooden pail, a white kitchen chair, a
      hurricane lantern). Each was asked to dress the street like a film's designer (which props, where,
      near and far layers, one clear subject, the notice easy to find, the drum's fire lit, no people);
      two of the four were also asked to choose the camera. The exact words are in "30 Composition test -
      the four requests".
    - **The four results** (all in `experiments/`, except the video):
      - Nano Banana Pro, keeping our camera ("30 Test - composed by Nano Banana - same view"): all ten
        props, each with a reason (bins by doors, barrels by walls), but spread evenly like a catalogue;
        the handcart blocks the middle of the road; it swapped our drum for a wire basket.
      - Nano Banana Pro, choosing its own camera ("30 Test - composed by Nano Banana - own camera"): stood on
        the right-hand pavement at standing height and built one group at the notice: the drum burning in
        front, the chair against the board with the lantern on its seat and the pail at its foot, a street
        lamp above; the handcart and sacks small on the far left; the road clear up to the pit apart from a
        small coal tub on a loose length of rail. The critics' clear winner (7 to 8 of 10) and yours: "this
        image is good". But it redrew the street, gave the board a roof, and garbled the notice (dated
        1756, "FRIDAY, 50H, APRIL").
      - Flux 3, keeping our camera ("30 Test - composed by Flux - same view"): kept the street almost pixel
        for pixel, but jammed most props into one tight group on the right (with the cart, barrel and a bin
        in a second clump on the left), lit the fire on the ground beside a cold drum and made the lantern
        nearly as tall as the chair. Lowest of the four in every round (3.5 to 5 of 10).
      - Seedance 2.5, a 10-second video ("30 Test - composed by Seedance - 10-second draft", sent; not in the
        repository): one continuous move, no cut, starting low among the props, travelling up the street,
        barely turning, and slowing down for a long time onto the notice, which ends big. But its props look
        like 3D objects rather than paintings, several stand alone in the road, the drum steams with no
        flame, the notice appears from nowhere at 2.7 seconds, the camera is at hip height and moves at
        jogging pace, and the notice's dates are garbled ("PRIDAY", "1828"). It is a draft, 480 pixels
        wide; it could be finished at full size within 7 days.
    - **Checked by three critics** (composition, camera, usefulness) and a skeptic who re-checked 35 of
      their claims against the pictures and rejected 11 (for example, "Seedance ends at an angle to the
      notice": it ends nearly square-on).
    - **What it means:** copy the composition and the kind of move, not the pictures. Nano Banana Pro and
      Seedance garbled the notice, and Flux's looks wrong too (too small to read for sure); only our own 3D
      notice reads correctly ("FRIDAY, 30th APRIL, 1926"). Nano Banana Pro and Seedance also redraw the
      street, and every program redraws the props, so their pictures can't be cut together with ours. I
      recommend (yours to decide) rebuilding the own-camera picture in our 3D street with our props and
      notice.
    - **Why the own-camera picture works** (decision 36; you said "this image is good. I'm not sure why ...
      It's genuinely hard to vary"). I measured it with a new measuring tool (now in the film kit): where
      its street lines meet, its brightest parts, its warm light, and where its weight sits (how strongly
      each part pulls the eye, from its size, brightness and detail). Then five critics gave reasons that a
      skeptic checked against the picture and against our clip. The answer: **every strong thing in the
      picture points at the same corner, the notice corner.** The street's lines all meet right beside the
      notice; the notice is the biggest bright shape (about half to two thirds of the brightest parts fall
      on it; in our clip about a fifth, the rest scattered over the sky, the fire's glow on the road and the
      lamps); the biggest near props (the drum, the chair) stand there; the warm light is there; and the
      props there touch and overlap, so they read as one group. Because everything agrees, almost any change
      either takes one strong thing away or makes a second place to look, which is why it is hard to vary.
      The balance you feel is that agreement, not an even weight: our clip is just as even left and right
      (46 to 54 per cent against 43 to 57). In our clip the lines meet at the colliery door, the brightest
      parts are scattered, and the biggest near prop is the coal sacks: three different places. The
      picture "30 Why it works - do the strongest things agree" shows this side by side.
    - **Your two observations hold, and help the composition too:** the chair by the fire and the lantern
      on the seat say "someone sat here and has just stepped away", so a street with no people feels lived
      in; the pale seat also repeats the notice's pale tone just below it, so the eye moves between them.
    - **Why our camera move felt odd** (both rounds of critics agree): it turned while it moved. Where the
      lines meet depends only on which way the camera faces, so the turn slid where the lines meet toward
      the colliery door at the frame's edge and slid the pithead out of frame; then a cut jumped to a
      close-up of the notice seen straight on, with no street or fire. A move that slides straight toward
      the subject without turning keeps everything pointing at it.
    - **Rules for future shots:** a main rule and twelve more, each with a check, are in the film kit as
      "07 Composing a shot" (and in the plugin). The checked reasons, a worked plan for rebuilding this
      picture in our street, and the measurements are in `experiments/` ("30 Why it works - ...").
    - **Reasons thrown out** (true of almost any picture, or not supported by the measurements): "things
      sit on the lines that divide the picture into thirds", "the cool blue makes the orange strong", "the
      subject is on the right because we read left to right" (the mirror image still works), "the three
      flames make a triangle".
    - **The picture's own faults, to fix in the rebuild:** the notice's right edge, the chair and the pail
      crowd the right edge, where phone apps put their buttons; three pairs of edges just touch (the street
      lamp and a winding wheel, the drum and the board's corner, the lantern and the board's bottom); the
      chair is spotless white in a sooty street; the chimney pours smoke although the pit is closed.
    - **Not checked, or unsure:** one run of each program only; another run could arrange things
      differently. The rebuild plan's positions come from a helper's calculation, not a picture drawn in
      Blender, and the two rounds of critics disagree on the camera's height (about 1.5 m or about
      1.85 m); a test picture drawn in Blender settles it. Flux's price may count the pictures sent as well
      as the one made; I've assumed it does.
    - **Cost:** about US$2.80 on fal (Nano Banana Pro 30 US cents for two pictures; Flux up to about 43 US
      cents; the Seedance draft about US$2.06). About US$5.40 of the picture allowance is left.

31. **Rebuilding the picture you liked in our street, and a tool that finds what is wrong with a shot**
    (decision 37). You said: "Yup redo with your props. See if new understanding of camera movement can
    help." Then: "The camera angle is wrong as well. The lines don't converge the same way." Pointing at the
    yellow lines in "30 Why it works": "You were right here." And: "Can you develop a tool that can calculate
    these things automatically and pinpoint what exactly is wrong."
    - **The rebuild.** The picture you liked was rebuilt in our 3D street with our own props and our sharp
      notice: the notice on its board on two posts, the drum with a burnt-down fire, the chair with its back
      to the board and the lantern on its seat, the pail at the chair's feet, a gas lamp behind the board,
      the handcart and sacks small on the road, the colliery gates shut.
    - **The camera.** You were right: the street's lines ran together differently. The camera was then
      matched to the picture you liked by lining up its landmarks (the winding wheels' hubs, the chimney's
      top, the colliery gate, the left roofline, both kerbs) with ours. Ours stood 0.42 m too high and was
      turned 1 degree too little; matched, the street's lines meet at 0.684 across, 0.440 down, against
      0.706, 0.424 in the picture you liked (the lines in a painting never meet at one exact point).
    - **The shot checker** ("07 Composing a shot", section "Checking a shot automatically"). Blender measures
      the 3D scene itself: it draws every prop in its own flat colour (once as the camera sees it, once
      alone), and writes down the camera, where the street's lines meet, the lights, and for every prop how
      far away it is, how big, and what it stands on. A second program checks every composing rule it can
      and writes a report: the problems worst first, each with a fix in metres, then what passed and what
      it can't check; and a copy of the frame with each problem boxed and numbered. It takes about a minute.
      For example, given our first camera, its first fix was "Lower the camera about 0.42 m; move it about
      0.29 m to the left (across the street); turn it about 1.0 degrees left", which puts it exactly where
      matching the landmarks had put it.
    - **How it was tested.** I broke the scene on purpose eleven ways and checked each one: a camera too
      high, a camera tipped up, a pail lifted 5 m into the air, a chair pushed away from its lantern, a pail
      pushed out of the frame, a lantern dropped on the pavement, a drum moved so its edge just meets the
      chair's, props sunk into the pavement, a lamp post standing right along the board's edge, a drum
      moved behind the board, and a lamp post across the notice's words. Each report's first fix named the
      planted fault, and the sizes were close: the pail pushed 0.25 m right got "move pail about 0.25 m to
      the left"; the drum sunk 0.30 m got "raise drum by 0.30 m".
    - **Checked by helpers.** Five independent helpers then tried to break the tool: one did exactly what its
      reports said and checked again, one planted new faults, one read its code, one read its reports as you
      would, and a skeptic checked their 50 findings. Faults they found, now fixed: putting the lantern back
      on its chair would have dropped it to the pavement; it missed a post standing along the board's edge
      and a post across the notice; it told you to move every prop when the camera stood too far back; it
      offered a camera turn that its own camera check then undid; its numbers sat on top of each other on the
      marked picture; the camera's lean had the wrong sign; and some words had two names. Every report now
      says which version of the tool made it.
    - **What the critics found in the rebuilt frame, and what was done** (four critics and a skeptic):
      - the chair faced the wrong way (its back to the fire, hiding the lantern): turned round;
      - a hard black wedge across the road: not the lighting but a fault of the render (Blender ran out of
        shadow memory, "Shadow buffer full" in its log); the checker now reads the render's log;
      - everything near white (the notice, the board, the chair's seat, the drum's top): the fire's light
        cut from 900 to 160 W and raised, the lantern's from 60 to 5 W, the board's timber darkened by half,
        a narrow warm light from just over the coals aimed at the notice's lower part, so it is lit from
        below;
      - the notice in the strip where phone apps put their buttons: the camera slid 0.14 m to the right
        without turning, so where the lines meet stays put (the checker's own fix; the critics worked out
        0.12 m by hand);
      - a far street lamp touching the board's post right where the lines meet: removed; the posts cut
        level with the board; the corner lamp's glass made amber and dimmer; the pail's thin wire handle
        removed (the painter would smear it);
      - the left half a black, empty mass: a soft cool light on the left-hand houses (now about 0.6 of the
        sky's brightness, as in the picture you liked), the sacks and dustbins moved into view, one dim lit
        window, and the handcart moved to where the picture you liked has it.
    - **Where the rebuilt frame stands** ("31 Notice corner - rebuilt and lit"): the shot checker passes 30 of its 36 checks on the
      finished still: the camera (within 0.02 m of the camera that best matches the picture you liked), where
      the lines meet (right at the board's edge), no two edges just touching, the story props one group in
      front of the board, the notice clear of the phone buttons, the notice the brightest thing (3.1 times the
      frame's average, 60% of the brightest parts), warm light on 2.9% of the frame and nearly all of it round
      the story props, no big dark shape where the eye enters, a dim sky, and every strong thing within 0.11 of
      the frame's width of the others (the main rule). Six remain: the quiet left half holds 34% of the
      weight (aim 40); the notice is only 0.07 warmer at its bottom than its top (needs 0.10; the picture you
      liked: 0.17); and four places that differ from the picture you liked on purpose (our notice is
      shorter, which would mean laying it out again; the pail is a little shorter; the lamp post and lantern
      sit a little further left, to keep clear edges and the phone buttons). By eye, the corner lamp's glass
      still looks nearly white rather than amber, and the drum's inside rim pale pink. Two new critics and a
      skeptic are checking the still now.
    - **Not checked, or unsure:** the checker measures only what shows on screen and each prop's outline
      box, so a prop poking into another in 3D is not caught; rule 7 (columns), most of rule 9 and rule 11
      (whether the camera turns during a move) are not checked. Which light lights a warm patch is worked
      out from distance alone, ignoring anything that shades it. The plate for painting (the bigger picture
      the painter repaints) has not been drawn with the new lighting yet, and nothing has been painted or
      filmed this round.
    - **Cost:** nothing (all of it in Blender). About US$5.40 of the picture allowance is left.

32. **Fixing what three rounds of critics found in the notice corner, sharpening the shot checker, and
    painting it** (continues log 31; decision 37). No new words from you; this follows log 31's next step.
    - **The second critics' fixes, and one that went wrong.** The skeptic of the second round asked for a sooty
      lining inside the drum 0.365 m across its radius. The drum is only 0.296 m, so the lining stuck out as a
      flat orange band and brought the drum's edge to 9 pixels from the notice. The shot checker caught the
      near-touch; a measurement of the drum model found why. The lining now fits inside the wall (lesson 116).
    - **Light linking.** Blender can choose which objects a light reaches. The warm light aimed at the notice's
      bottom edge now reaches only the notice and its board (it had lit the chair's top rail as bright as the
      notice); the lantern's light skips the lantern itself (it lit the brass frame and made the glass look
      milky); the fire's light skips the drum and the chair (from 0.4 m over the rim it turned the rim and the
      chair's back as bright as the notice). The film's live flames light the drum instead.
    - **The third critics** (composition and light; what the painter will garble; 1926 and the story) **and a
      skeptic** found, and these were fixed:
      - the drum's mouth an even orange disc that would be painted as orange soup or a lid: its glow now fades
        up from the coals, dark under the rim;
      - the shut colliery gates lost in a pure-black doorway, so the gate read as open: dim shut doors behind
        them;
      - the gas lamps and the lantern flat amber cards: the "see-through" setting had been ignored, because the
        imported glass takes that value from its picture; unhooked, the mantles and the flame show;
      - the extra lit window landed off the frame: moving the camera never refreshed the scene, so the window
        picker used the old camera; two windows now light on the left side of the frame;
      - the whole frame a third darker than the picture you liked: a brighter dusk sky (1.4 to 1.96);
      - the chair so dark its legs were darker than the pavement: lighter paint (0.25), still darker than the
        notice;
      - the gutter still like steps: a plain stone colour (the first try was a pale stripe, the second joined
        the drum's shadow into one dark pool where the eye enters; the third sits just under the road);
      - the drum's side running 2 pixels in front of the board's left post for 113 pixels: the post moved 4.5 cm.
      - Left as they are: the oil-drum brazier (more 1984 than 1926, but the composition depends on it), the
        board across the pavement, the pail in the band where apps put captions.
    - **What the shot checker learnt** (each tested; the 11 faults planted on purpose still come first):
      - edges by colour as well as brightness: a rusty drum against a blue-grey road is about as bright as the
        road, so it took a correct picture for an out-of-date one;
      - a picture is out of date only when a prop lines up clearly better once slid a little (a moved prop
        does; one with faint edges doesn't). It caught all four old pictures, passed every new one, and later
        found the painter's 3-pixel shift;
      - the longest stretch where two edges touch, so a deep overlap higher up no longer excuses a post running
        along the drum's side lower down;
      - background props in the check (the far lamp, handcart, sacks, dustbins): it found the handcart only
        just overlapping the dustbins and the new lamp's post meeting their edge;
      - which lights reach which props (light linking), and that a lit lantern's small flame may outshine the
        notice while its glass may not (a flame lights about 6% of the lantern that bright; a glowing glass 18
        to 22%).
    - **Where the frame stands** ("32 Notice corner - relit and checked"): the checker passes 32 of 38 checks.
      Open: the quiet left half holds 38% of the weight (aim 40; the picture you liked 42%); the notice's
      bottom is 0.08 warmer than its top (needs 0.10), but in the film the notice is its own surface, lit by
      the film page, which now has a copy of the warm light under it; and four places that differ from the
      picture you liked on purpose.
    - **The paint-over** ("32 Notice corner - plate and painting"): Flux 3 repainted the plate (the bigger
      picture drawn from where the slide starts) in the series' style, with the critics' instructions: keep
      every shape and the light and dark; a dull rust drum with a dark sooty mouth; shut gates against grey
      doors; and never add flames, smoke, glows or new shadows round the near props, because those would
      slide or blink out once the camera moves. It did all of that, and added nothing. The notice and the
      colliery sign went to blurred marks, as expected: the film keeps its own sharp copies of both.
    - **Lining the painting up.** The shot checker's new test showed every prop in the painting lining up
      better once slid about 4 pixels: the painter had stretched the picture by 0.65% and shifted it 3
      pixels. A new tool (`align_painting.py`) finds that stretch and shift from the props' outlines and undoes
      it: 96% of the outlines then sit on the painting's edges, against 70% before. A second painting with the
      near props painted out (what the film shows behind them as the camera moves) was lined up against the
      first ("32 Notice corner - painting with and without the near props").
    - **The film page's own end frame**, checked by the shot checker: the notice is 0.23 warmer at its bottom
      than its top (needs 0.10; the picture you liked measures 0.17), now that the page has a copy of the warm
      light under it; and the quiet left half holds 46% of the weight (aim 40 to 48). New there, from the
      painting: a dark painted gutter leading in from the bottom (2.1% of the frame, limit 1%), the lamps and lit
      windows spreading the warm light (43% of it round the story props), and pale painted dustbins. Kept as
      they are: the gutter is a narrow lead-in line, not a dark mass.
    - **The film** ("32 Test - notice corner slide", 13 seconds, music only): BRITAIN 1926 over the dim sky,
      one slow slide of 1.5 m toward the notice without turning, the drum's live fire and smoke, the lantern's
      flicker, then LOCKED OUT / FROM 1 MAY 1926 over the held frame, and a fade. The music is a quiet stretch
      of your soundtrack (from 3 minutes 36 seconds), faded in and out.
    - **Checked in motion by two helpers and a skeptic.** Clean: the camera never turns (everything spreads
      out from one fixed spot), the move is smooth and stops by 8.4 seconds, no blinks, no painted outlines left
      on the road, no smearing at the frame's edges, the notice's print steady and its dates right. One fault a
      viewer would see: 2 seconds in, the long shadows the fire throws from the pail and the chair faded off
      the pavement. The painting with the near props painted out had lost them, and the film switches to it
      round the props as soon as the camera moves. Fixed by keeping the main painting everywhere except inside
      the props' own outlines (`keep_painted_shadows.py`), then filmed again. Also changed: the fire glow's
      size pulse calmed (its rim slid on the road), a soft dark band behind the first title (the amber 1926 was
      faint against the sky), the two chimney smokes dropped (both chimneys are out of the frame), and the
      music raised from -17.7 to -14 LUFS (a helper found it faint on a phone speaker).
    - **Filmed again** (about 41 minutes, two halves at once): the patch of pavement right of the pail now stayed at
      70 to 71 (on a 0 to 255 scale) through the switch, where the first filming rose to 89 as the shadow faded.
      A fresh helper checked the changes and found one new fault the fix had made: a pale outline 10 to 15
      pixels wide round the pail from 1.8 seconds to the end. The narrow gap kept round each prop (so the
      painter's ink lines don't stay on the road) still had no shadow. Fixed by carrying the shadows' darkening
      into the gap and under the props (measured outside them and spread inward), checked on single frames,
      and filmed a third time. The helper found the title band smooth, the fire glow steady (1.2% swing against
      2.8%), nothing else changed, and the music at -13.7 LUFS with clean starts and ends.
    - **The third filming** has no pale outline round the pail (checked side by side at 10 seconds), no jumps, and
      the same clean shadows, title band and glow. It is the one sent ("32 Test - notice corner slide", 8.5 MB).
    - **Left for later** (minor, or a bigger change): the notice's key lines are only just readable on a phone
      (PITS WILL BE CLOSED 11 pixels tall; about 18 would read easily); the flames look like flat cut-outs and
      the sparks rise in tidy strings; the notice paper's edges show a faint 1-pixel saw-tooth zoomed in; the
      end titles arrive at 8.9 seconds with a small pop; and nothing personal is left on the chair to say
      someone kept watch there (a cap or jacket would).
    - **Not checked, or unsure:** I haven't seen it on a phone; the helpers judged from frames and measurements
      and could not listen. The music's stretch was chosen by its loudness, not by ear. The checker measures only
      what shows on screen, so props poking into each other in 3D are not caught. The paintings' price is a
      range because fal didn't show the exact charge.
    - **Computer time:** about 3 hours of drawing and filming in all (each filming about 41 minutes).
    - **Cost:** about 20 to 45 US cents on fal for the two paintings; everything else ran here. About US$5.00 of the
      picture allowance is left (between US$4.95 and US$5.20).

33. **Rewriting chapter 2 for newcomers** (decisions 38 and 39). You kept the notice corner ("Yes keep
    it") and asked: "could you rewrite a script to be more introduction friendly. I've had a few people get
    lost trying to understand the last video because it moves to quickly and uses terms that your average
    person isn't familiar with. Keep the writing in the voice of Naomi Klein. See if this attachment helps
    with pedagogy and prose" (the attachment: your Steven Pinker Teaching and Writing Toolkit).
    - **My reading of the request** (Decisions, item 39): "the last video" is chapter 2, "what really causes
      inflation". "The voice of Naomi Klein" means her spirit, as in decision 8: urgency, direct questions,
      the stakes first, who gains and who pays; never her words, titles or coined phrases. Facts come only
      from chapter 2's checked research ledger. The toolkit (teach for understanding, write for readers, a
      clarity workflow) guided every step. It stays out of the repository, as before.
    - **Why people got lost, measured on the recording** ("01 Newcomer audit of the recorded chapter 2"):
      - Malina read it at 164 words a minute, against the 140 planned. The three fastest pages carried the
        most new things or the main idea.
      - It began with "So..." and, by the end of the first page, sent the viewer "back to the shell
        factory" from chapter 1.
      - The rule the chapter teaches came only once, 3 minutes in, as one 28-word sentence.
      - Eight real cases in about 4 and a half minutes, changing direction in time 8 times.
      - 48 words a newcomer might not know, and "price" used for six different things.
      - Each "..." pause gave under a second: no time to think.
    - **Seven places where the recorded script says a little more than the ledger allows** ("04 Fact
      choice", section 6). The two that matter: page 8 drops the review's "with the benefit of hindsight" (it should say "looking back") and
      puts the review next to house prices, which it didn't discuss; page 10's "is raising its interest
      rate again" should be dated, in the past tense. The other five are small, or on screen only. The
      film already sent is unchanged.
    - **How the rewrite was made** (three rounds, 22 helpers, about 3 hours 20 minutes; every step is in
      "33 Chapter 2 for newcomers - working files"):
      - Round 1: the audit, a teaching plan, a voice brief, a choice of facts, then three drafts from
        different angles (one picture first; the viewer's own question; people first).
      - Round 2: three judges (will a newcomer follow it; voice and sound; truth and rules). "One picture
        first" scored best for newcomers (7.5 of 10) and was combined with the best parts of the others.
        Three fresh testers (imagined newcomers, facts, rules and voice) then found 6 must-fixes, for
        example the rule said that new money gets things made, where the research speaks of money that
        is spent. A reviser fixed them.
      - Round 3: four fresh testers. The newcomer tester saw only what a viewer hears and sees, and a
        skeptic (called "the people who got lost" in working files 11 and 12) compared the script with
        the recorded script's words. They found 4 must-fixes: "Spent on what?" was
        never tied to its test; "building new homes" was heard as a building boom; the script gave our
        Reserve Bank's view with no source (the ledger has America's); and Mattei's view was said more
        strongly than her own words. A fixer made the confirmed fixes, a re-checker read all 45 changed
        sentences (no factual errors), and a last fixer made two more.
      - Then I made three small wording changes the last fixer had left open, re-read Powell's speech on
        the Federal Reserve's page and a news site's copy of Stats NZ's June 2022 release (Stats NZ's own
        page could not be found), and added their exact words to the ledger (C2-M17, C2-N02).
    - **What the new script does** ("33 Script - chapter 2 - what really causes inflation - for
      newcomers"):
      - Example: pages 3 and 4 ask the viewer to picture two factories, each standing for a whole country. In
        the quiet factory, workers wait at the gate; new money is spent, the workers go in, "More
        money... and more things to buy. So prices barely move." In the flat-out factory everyone is
        already busy; the same money arrives: "What happens to prices? Have a guess." Britain at war,
        Glasgow's homes, Japan and New Zealand are then each placed on that picture out loud.
      - One idea: whether new money pushes prices up depends on whether it's spent, and on what.
      - Four real cases in time order, three guesses held about 4 seconds, the rule said twice in the same
        words, every unfamiliar word explained or left out, about 28 spoken figures instead of 37,
        sentences of about 9 words.
      - The stakes in the first 30 seconds; the usual cure and who pays for it ("many people with
        loans... and people put out of work"); America's central bank's view in one fair line, then
        Mattei's, marked as hers.
      - Left for later chapters: Germany 1923, the Bank of England after 2008, oil in 1973, Britain 1920,
        New Zealand house prices.
      - About 7 and a quarter minutes at Malina's measured speed (the recording: about 4 and a half).
        Ready cuts of 32 words are listed.
      - The pictures are planned from the paintings and pieces already made: no new paintings.
    - **The narration file** ("33 Narration script - chapter 2 for newcomers.json") is ready to record, in the
      same form as before. Not recorded.
    - **A last check of the finished files** by two fresh helpers: the narration has no rule breaks and the
      file's numbers are right, but they found 37 smaller problems in the notes around it. For example:
      picture notes that would put years or example prices on screen that Malina never says; a line
      saying I had opened Stats NZ's own page, when it was a news site's copy; the main rule quoted in
      older words in the rules file and the plugin; and a word ("stand-in") used for two things. All were
      fixed ("14 Check of the finished files" in the working files).
    - **Added for later chapters:** a newcomer section in the writing rules (section 4); in the film plugin
      (version 1.2.0), a new workflow (a set of helpers that run in a fixed order),
      `test-script-with-newcomers`, and a newcomer section in its scriptwriting guide. The new workflow
      was tried only in a practice run with pretend helpers that do no real work (it starts each helper
      in the right order and refuses to start without the files it needs), not yet on a real script.
    - **Not checked, or unsure:**
      - No real newcomer has heard it. The testers' listeners were imagined by helpers.
      - Malina hasn't read it, so the length is an estimate.
      - Whether ElevenLabs lets Malina's speed be set lower: not checked.
      - The picture notes are plans; nothing is drawn or filmed, and 16 pages means new page files.
      - Three sources are still to open: Glasgow's builders gone to the war, why petrol and diesel went
        up in 2026, and any New Zealand Reserve Bank statement on job losses.
    - **Cost:** nothing on fal or ElevenLabs. About 3 hours 20 minutes from start to finish.

34. **The full redesign of chapter 2, in the look you kept** (decision 40; in progress). You said: "Better.
    Now's the real test. The full redesign. New budget starting from now is $20. Go!"
    - **My reading** (Decisions, item 40): the whole newcomer script (log 33) made in the notice corner's look:
      real places built in 3D in Blender, painted over, composed by the rules in "07 Composing a shot", the
      camera sliding without ever turning. The US$20 covers the narration (about US$1.10) and the paintings.
    - **The paid steps were refused by this session's automatic safety check** on 15 October, at the first
      call to ElevenLabs, despite the budget. I didn't try to get round it. The recording and the paintings
      wait for your yes; everything free is done first.
    - **The plan** ("34 Plan - chapter 2 full redesign - places, shots and order of work"): six places (the
      Works, a supermarket checkout, a Japanese corner shop, a building site, a kitchen, Glasgow in 1915), 11
      views, 13 plates (the plain 3D pictures), 20 paintings (about US$7), 16 pages. For example, "workers
      wait at the gate" is the chapter's central picture: dark figures seen from behind, never nearer than
      about 6 metres, so the painter has no faces to paint.
    - **Groundwork, all free:**
      - **An estimated timeline** made from the script alone, with word lengths and pauses measured on
        Malina's real recording. Tested on the old recording, it gives 252 seconds against the real 251.7.
        On it, the new chapter runs about 6 minutes 47 seconds.
      - **Held shots filmed about 5 times faster:** the still set is drawn once and reused, so a held frame
        takes 1.1 to 1.3 seconds.
      - **Chapters that load only the pages a piece of film needs**, so 16 heavy pages no longer run the
        computer out of memory.
      - **Changes on a held shot** (the men gone, the windows lit) by swapping only the area that changes.
    - **The Works, built in four rounds.** Each round, helpers build; then a fresh critic who hasn't seen the
      work judges it against the notice corner, and the next round fixes what they found.
      - **Round 1:** the street and prop scripts reused, each writing to its own folder (the notice corner
        proven unchanged, pixel for pixel); chapter 2's 13 props; 11 figure shapes. Found: names that broke
        loading, a jacket that read as a headless man, heads that looked bald.
      - **Round 2:** the two factories at true size. No. 1 is dark red brick with one round chimney; No. 2 is
        pale stone with two square chimneys and a tank, so they're told apart at a glance. Figures fixed
        (coats too red, a toy-like look).
      - **Round 3:** the Works put together with four views (W3 from an upstairs window, W1 at No. 1's gate,
        W2 at No. 2's gate, W4 inside No. 2's yard), the plates drawn, and pages 3 to 5 written and filmed
        (76 seconds), with the plates standing in for the paintings. Found: striped brick (a one-line bug),
        doorways that looked like bar charts, a gasholder that read as a tank on No. 1's side, drums whose
        words couldn't be read.
      - **Round 4:** all of those fixed (no striped parts left; machines in the doorways; lit mill windows;
        the gasholder gone; PETROL and DIESEL readable; words end exactly on each cut; the slight dimming on
        each page turn's first frame gone). Filmed again: the only jumps are the planned ones, the camera
        never turns, every word on screen matches the narration, 1.4 seconds a frame. The fresh critic
        still found 15 problems, 4 of them must-fix: nobody is ever seen working; the men stand in single
        file, so from the camera they stack into one dark column; the story sits small and high, with bare
        paving filling the bottom third; and the smoke looks like a fault (pale rings).
    - **The computer restarted overnight** during round 4's filming. The finished work was already on disk
      and saved; only the filming was lost, and it was done again.
    - **The FOUNDRY painterly library you sent** (a set of ready-made Blender surfaces) was tried on its own
      sample scenes and on two views of the Works. Brick came out sootier and wood got grain, but nothing
      looked painted, the wet-stone road came out white and icy, and drawing was about 7 times slower (223
      seconds against 33 for two views). Not used: the paintings stay the way to the painted look.
    - **Round 5 (running):** the round 4 critic's fixes (people seen working inside the lit doorways; the
      waiting men as a loose crowd across the gate; the cameras about 3 metres nearer; the gate lit as the
      brightest thing; smoke blown across the view); W4 fixed; and the next place started, the supermarket
      checkout for page 1.
    - **Not checked, or unsure:**
      - Nothing is painted yet, so every picture so far is the plain 3D plate.
      - Whether painted figures work at all is untested (the people test needs your yes).
      - The narration isn't recorded, so all timing is estimated.
    - **Cost:** nothing spent from the US$20.
    - **The people test, painted** (you said "Yeah do it", 16 October). The pit village street with five men
      round a brazier and six small walkers was painted by Flux in the series' style, then painted again with
      the people taken out. Both paintings were lined up with the 3D set (the second within one pixel) and
      filmed two ways: the painted men leaving on a cut, and dark figures standing over the painting
      ("34 People test - plate and paintings", "34 People test - painted men leaving, and dark figures").
      Four fresh helpers checked it:
      - **Painted men work.** All four agreed. Same number, places and poses as the 3D picture (within 1 to 3
        pixels), no faces, and they look part of the painting, not like dummies or toys.
      - **Dark figures don't.** They came out flat black and read as shadow puppets. Dropped.
      - **The cut reads as the men blinking out**, not as time passing: nothing else changes, and the fire
        even looks bigger once they've gone. For the Works, something else will change with them (the men are
        seen inside the factory, the fire burns lower).
      - **The painter left the men's long shadows** when asked to remove them, so dark streaks stay on the road
        after the cut. For the Works, the plates will be drawn with the figures casting no long shadows.
      - Smaller things: the drum's top painted as a bright orange band; the men painted paler than in the 3D
        picture; the fire's warm pool on the road half the notice corner's; the steps look like wooden blocks.
      - **Cost:** the price had doubled since the plan (4.8 US cents a megapixel), so about 85 US cents for
        the two paintings, worked out from fal's price list (fal doesn't show the exact charge).

    - **Round 5** (the Works, W4 and the checkout): people now work inside both lit doorways; the waiting men
      stand as a crowd you can count across No. 1's gate; the cameras moved 1.2 metres nearer, and the shot
      checker now also tests that the story reaches 0.70 down the frame; PETROL, DIESEL and THIS WAY UP read
      whole; the smoke blows as trails; MACHINES is readable for 0.83 seconds; W4 was relit, with a modelled
      jacket, cap and WAGES envelope. The supermarket checkout (C1, page 1) was built, composed and tested in
      the stage, and its newspaper name, THE EVENING LAMP, was checked against 1,617 New Zealand titles.
      Pages 3 to 5 were filmed again: only planned jumps, no camera turn. Two fresh critics still found:
      page 5's closing picture contradicts its rule ("more things made" points at No. 1's cold chimney, with
      the men still waiting); both price arrows run through the "No." boards; the bottom of the frame is still
      plain paving; the checkout's top 40% is nearly black and its brightest area is the empty belt.
    - **Round 6 was stopped partway** when you asked to wrap up (16 October). Its helpers had changed
      assemble_works.py and the page files (the price arrows, the "made" picture, the busy burst, the fire
      after "go", the people test's lessons), but no plates were redrawn and nothing was filmed or checked.
      Those changes are saved and their code loads, but they are untested. The last fully checked state is
      round 5 (commit cdca253).

35. **The plugin learns the numbers** (16 October). You asked: "All the runs and adjustments you've made, can
    you make them into automatic calculations the plugin makes automatically so they don't have to be
    exhaustively searched for every time a new video is made. Along with tips and tricks for LLMs to follow."
    - **What was found:** five helpers read everything (lessons, logs 1 to 34, every round's findings, the
      tools) and listed 423 settings or fixes found by trial. For example: people never nearer than 6 metres;
      a crowd across the camera's line of sight, never along it; music 18 dB under the voice; a word said twice
      on a page needs "which time".
    - **What was built** (the plugin's version 1.3.0, `plugins/explainer-film`):
      - **Calculators** that work these out from a new film's own files before anything is drawn or paid
        for: where to put the camera and the people, letter and head sizes in each view, which way smoke
        should blow, the lights to start from, the painter's instructions and price, the checks when a
        painting arrives, which "before and after" pictures a change needs, how long every word on screen
        stays readable, the script's checks before recording, loudness and timing checks, and money,
        filming hours and disk.
      - **One command per stage of making a film** (explainer-film-preflight: script, record, shots,
        plates, paint, pages, film, finish) that runs the right calculators and writes one report.
      - **One table of 344 house numbers**, each marked measured, judged or invented, with its source.
      - **"LLM tips and tricks"**: 163 short tips for a model making the next film, each naming the tool
        that checks it, or "ask a critic" where nothing can.
      - The plugin's copy of the film kit was brought up to date (92 files), with a new skill,
        build-and-paint-a-place.
    - **Tested:** 23 test files, about 780 checks, each against a number recorded in the project (for example:
      the W1 camera numbers, the head size at 6 metres, both smoke winds). A skeptic first corrected several
      pass marks that would have rejected work you had accepted.
    - **Not done:** the planned adversarial tester and the "fresh model" trial (a model that has never seen the
      project planning the Japanese corner shop with only the plugin) were stopped before they ran, so nobody
      outside the build has used it yet. A few tools are still to come (a light-tuning loop, a camera solver
      inside Blender). The Works and checkout files were not copied into the plugin because round 6 was
      changing them.
    - **Cost:** nothing.

36. **The films so far, joined** (16 October). You asked: "Can you stich together videos that are rendered thus
    far?" One silent film, 1 minute 48 seconds, 10.7 MB ("34 Redesign so far - films joined"): a title card, then
    the notice corner (the standard you kept), the painted people test (the men leave at the cut), and pages 3 to 5
    of the Works from round 5 (plain 3D pictures, words on an estimated timing), each after a plain title card.
    Left out: the dark-figure version of the people test (dropped), the checkout (only stills exist so far), round 6
    (nothing filmed) and the older finished chapter 2 film (round 20), which is a different version. Checked by
    looking at seven frames across the join. Like every film, it stays out of the repository. Cost: nothing.

## Next step

When you have usage again, say "carry on from the project story". The first job is to finish round 6:
redraw the Works plates, film pages 3 to 5 and have fresh critics check them. Then I'll ask your yes for the
Works' first three paintings (about US$1.30).

## Traps

- The latest New Zealand inflation figure (4.1%, year to June 2026) may be replaced on 22 October 2026:
  check it on the day chapter 2 is recorded.
- Mattei's interpretations stay marked as hers ("Mattei says", "her answer"), however urgent the
  wording gets.
- Your soundtrack is loud and dense (about -13 LUFS); it must always be turned down under Malina.
- ElevenLabs download links expire after 2 hours: recordings are downloaded straight away.
- Re-recording one page moves every time after it, so the whole chapter's timing, mix and film are
  made again (about 25 minutes of computer time, no extra cost beyond the recording).
- The film's first frame is page 1's empty parliament, before the politician folds up. Where an app
  lets you pick a cover, use "13 Cover".
- The sent film is squeezed to fit under 30 MB. For uploading to a video site, the full-quality master
  (`paper-film/out/chapter-1-paper-master.mp4`, 290 MB) looks sharper, but it was on an earlier
  session's machine and is not in the repository; it can be filmed again from the film kit.
- The newcomer script (log 33): after 22 October, check that page 1's "costs more than it did a year
  ago" still holds, and decide whether page 15's dated basket (June 2025 to June 2026) should switch to
  the new figures; after 4 November, check page 13's "nearly six in a hundred" out of work.
- Chapter 2's newest figures go out of date soon: prices (4.1%, year to June 2026) on 22 October,
  the Reserve Bank's rate decision on 28 October, unemployment (5.6%) on 4 November. The recorded chapter 2's page 7 says
  "the latest figures" and its page 10 says "this year ... is raising"; recheck before publishing late.
- Chapter 2's full-quality master (808 MB, round 20) is not in the repository (GitHub refuses files over
  100 MB). It can be made again from `austerity-explainer/film-kit/` with the mix and timeline in
  `chapter-2-inflation/`, in about 6 hours of filming. The 27.6 MB copy and captions are kept.
- The repository is public: never add the soundtrack, recordings of anyone but Malina, or anything
  with a password or key in it.
- A cloud machine can restart and silently end long jobs: watch for a job stopping, not only for it
  finishing (lesson 56).
