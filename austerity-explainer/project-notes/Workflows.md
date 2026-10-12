# Workflows

What this file is: how to read, change and document this project. It grows as the project does.

## How to read the project

1. Start with `Status.md` (where things stand), then `Decisions.md` (what was decided, in your words).
2. For any fact in the film, open the chapter's research file in `research/` and find its id
   (for example C1-10). The id is written beside the scene that uses it in the scene plan.
3. For the drawing code, open the film folder's notes at the top of each file.

## How to change the project

1. Check `Decisions.md` first. A change that contradicts a decision needs your say-so.
2. A new fact needs a research entry (claim, plain version, source, confidence) before it goes into
   the script or onto the screen.
3. Script changes go into the chapter's script file; the scene plan is updated to match.
4. After any change to the drawing code, re-draw the affected scene and look at it before re-making
   the film.

## How a chapter is made (in order)

1. **Narration text** goes in `narration/chapter-N-narration.json` (exact words, delivery cues in
   square brackets, Mattei in phonetic symbols). Each page is recorded on its own in Malina.
2. **Download** each recording at once (ElevenLabs links stop working after 2 hours) into
   `downloads/malina/chapterN/`, and ask ElevenLabs for its transcript (free).
3. **Word times**: `tools/extract_word_times.py` turns the transcripts into
   `narration/chapter-N-word-times.json` (it refuses a transcript that does not match the script).
4. **Timeline and narration track**: `tools/assemble_chapter_narration.py` lays the pages end to end
   with the planned pauses, levels each page to -16 LUFS, and writes the narration track, the
   timeline, and the timing file the drawing code reads (`film/src/canvas-core/...Timing.ts`).
5. **Mix**: `tools/mix_chapter_narration_over_music.sh` lays the narration over the soundtrack.
6. **Pages**: the drawing code asks for words ("the second 'shells'") and gets their times, so the
   pictures follow the voice. Check every page at full size before rendering.
7. **Render** the silent film, join it with the mix, write the captions from the word times, and run
   the checks (the skill's gate, frame count, loudness, true peak).

Re-recording one page changes every time after it: redo steps 2 to 7 for the whole chapter.

## How a chapter is made in the paper pop-up look (the approved look)

1. **Plan the pages** from the narration: which word brings in which piece, and how (folds up, slides
   in, drops in, crashes down, folds away). Words on screen: few, plain, only to help memory.
   Chapter 1's plan: `plans/12 Plan - chapter 1 in paper pop-up.md`.
2. **Paint the pictures** with fal (Flux 3): one background per page (tall, nothing standing in it),
   and each figure or object on its own on plain grey, with the same style words every time. Big
   pictures cost about 10 US cents, small objects about 2.5 cents. Record each request in the
   folder's `00-requests.json`. Check every picture on a contact sheet for history mistakes, symbols
   and flags before cutting.
3. **Cut them out**: fal's background remover (BiRefNet, "General Use (Dynamic)", mask only) gives a
   mask; `paper-film/tools/download_fal_masks.py` saves the masks with plain names. Lay every cut-out
   over magenta to see missing or faint parts.
4. **Make the paper pieces**: list every background and piece in a cut list
   (`paper-film/scene-data/chapter-1-cut-list.json`: margin, colour nudge, size, and any repairs,
   printed labels, mouths or split shapes), then run
   `python3 -I paper-film/tools/prepare_paper_pieces.py <cut list> <project folder> [names]`.
   It writes `paper-film/pieces/chapter-1/` and `pieces.json`. Naming pieces at the end remakes only those.
5. **Mouths**: a speaking figure's jaw and mouth are outlines in the cut list (read off a gridded
   close-up); `paper-film/tools/make_mouth_track.py` turns Malina's loudness into how far the jaw opens
   on each frame (`paper-film/scene-data/chapter-1-page-N-mouth.json`).
6. **Page files**: `paper-film/scenes/chapter-1/page-N.js` names the page's sheets and says, in
   Malina's words, when each piece moves. The shared motions and the page kit are in
   `paper-film/scenes/paper-kit.js`; the chapter scene `paper-film/scenes/chapter-1.js` stacks the
   sheets, turns each page 0.3 s after its last word (pieces fold away first), and moves the camera.
7. **Look before filming**: `node paper-film/tools/render-paper-film.mjs chapter-1 <folder> --stills <times>`
   draws single moments. Check every entrance, word, mouth and page turn at full size, and look for
   pieces cut off at the frame edge. `paper-film/scratch/lamp-only-still.mjs` checks shadows.
8. **Film**: `bash paper-film/tools/film-chapter-1.sh` films one page-sized chunk at a time (about
   0.85 seconds a frame, about 95 minutes for chapter 1) and joins them into
   `paper-film/out/chapter-1-silent.mp4`. To re-film one page, delete its chunk and run it again.
9. **Finish**: join the chapter mix (`mix/chapter-1-mix-steady-accent.wav`) to the silent film, make
   captions with `python3 -I tools/make_captions.py <timeline> <output>`, take a cover frame, and
   check frame count, loudness, true peak and that sound and picture line up.

## How a chapter is made in the cinema look (chapter 2)

The cinema look keeps the paper pop-up book's page peel but makes every page a real 3D scene. The
code lives in `chapter-2-inflation/film-code/` (it sits on top of the film kit).

1. Research ledger, outlines, script, recording, word times, timeline and mix: as in the paper look.
   Before recording, fact checkers read the script against the ledger; after the pages are built,
   independent checkers try to prove every spoken and on-screen fact wrong from fresh sources.
2. Paintings (fal): one painted room per setting (9:16, no words in the picture), plus cut-out pieces.
   For each room a distance picture is made (fal, Depth Anything v2), then
   `film-code/tools/prepare_relief.py PAINTING DEPTH FOLDER NAME --blur 3` makes the painted room
   with depth.
3. Pages: each page is `film-code/scenes/inflation-chapter-2/page-N.js`, built from the kit in
   `cinema-kit.js` (lamp, painted rooms, cut-outs, words, camera paths), card models in
   `models.js`, effects in `effects.js` and flat graphics in `graphics.js`. Every event is timed
   to a word with `kit.at('word')`. `19 Guide - building a cinema page.md` is the full how-to.
   Since round 20 the camera follows your rule ("stay still unless it's essential ... 3 movements per
   frame, max"): each shot is a `kit.stillShot` (still, with at most three named moves: zoom in or
   out, pan left, right, up or down, move up or down); more moves means a cut to a new shot.
   `20 Guide - camera rule, filling the frame, no clipping.md` is the how-to.
3a. Models: detailed buildings, the town, the desk and props are built in Blender by script
   (`film-code/blender/build_*.py`, run with Blender's Python module) and saved as `.glb` files in
   `pictures/models/`; pages load them with `model-loader.js`. To look at one model alone:
   `PAPER_FILM_QUERY="model=/assets/models/inflation-chapter-2/NAME.glb&cam=X,Y,Z&look=X,Y,Z&fov=42" node paper-film/tools/render-paper-film.mjs model-preview FOLDER --stills 1`.
3b. Frame a shot with numbers before rendering: `python3 -I film-code/tools/frame_check.py CAMERA TARGET FOV name=x,y,z ...`
   says where each thing lands in the tall frame.
4. Check stills often:
   `PAPER_FILM_PAGES=N node paper-film/tools/render-paper-film.mjs cinema-test-pages FOLDER --stills T1 T2 ...`
   (times separated by spaces), then a contact sheet, and look at every beat.
4a. Check the camera rule by measurement (about 10 seconds for the whole film):
   `node paper-film/tools/render-paper-film.mjs inflation-chapter-2 --camera CAMERA.json 3` then
   `python3 -I film-code/tools/camera_audit.py CAMERA.json` (must end "0 problem(s)").
4b. Check nothing passes through anything: `room.clearance(thing)` (how far in front of the painted
   room; negative = poking through) and `boxesOverlap(a, b)`, at the moments things land or move.
5. Check the page turns from the whole chapter (`... inflation-chapter-2 FOLDER --stills` at each
   last word plus 0.7 s): each page's words must stay on its own page.
6. Film: `bash paper-film/tools/film-chapter-parallel.sh inflation-chapter-2 2 240` (35 chunks, two at
   a time, about 3.5 hours; run it again to carry on after a stop).
7. Finish: `narration-tools/finish_film.sh` with the mix, then captions (`make_captions.py`), the
   sound alignment check and the loudness check, as in the paper look.

## The reusable kit

`kit/paper-pop-up-film-kit/` is a general copy of the paper film tools for other series (made for a
series on the enclosures), with this chapter as its worked example. It is a separate copy: changes
here do not change it. To refresh it after a fix here, copy the fixed file across, adjust paths, run
the kit's smoke test (`00 START HERE.md`, step 4) and pack the zips again.

## A one-page picture (still) with folded paper props

1. The props are built in a scene file from folded shapes (`paper-film/scenes/one-page-origami.js`):
   each prop is a list of flat triangles, so every fold catches the light differently. The scene
   switches off the stage's own lamp and brings its own lights.
2. Draw it at twice the size: `node paper-film/tools/draw-one-page-still.mjs one-page-origami OUT.png`
   (about 5 seconds).
3. Finish it: `python3 -I tools/finish_one_page_still.py OUT.png FINISHED.png` shrinks it to
   1080 x 1920, darkens the corners softly and adds a fine grain.
4. Look at it whole and in close-ups (props, fold edges, shadows) before sending.
5. The open-book picture (`paper-film/scenes/one-page-open-book.js`) is built the same way, but its
   pieces are cut-paper sheets drawn in code (holes cut where the paper is removed), and it also saves
   a distance picture. Give the finishing tool the point to keep sharp: `--focus 790 1150` (the
   cottage). Check the fine detail at full size after finishing: the blur must not soften it.

## How to edit the documentation

1. Every change to the project updates `Status.md`, and the project story log gets a new numbered
   entry (the log is added to, never rewritten).
2. A new decision goes at the bottom of `Decisions.md` with your exact words.
3. A failure while building or testing goes into `Lessons.md`.
4. New terms from the authority source go into `Glossary.md`.

## Traps

- Files sent to you start with the log number they belong to. Never reuse a number for a new log entry.
- Never write "final" or "v2" in a file name.
- A word that is spoken twice on a page must be asked for by which time it is spoken ("shells", 2),
  or the mark lands on the first one.
- The drawing code's timing file is made by a tool; never edit it by hand.
- Paper pieces need to cast shadows from both faces, or a piece facing the lamp casts none.
- The hidden browser cannot do the smoothest kind of soft shadow (it lacks a needed graphics
  feature); the paper stage uses the plain kind with softened edges instead.
- Dust and smoke must be made through the page kit (`kit.effect(...)`), or they are not put away
  with their page.
- Filming two chunks at once is no faster on a 2-processor machine; on 4 processors (chapter 2) two at
  once is about 17% faster, and three is not worth it.
- In a one-page picture, folded props must not push their shadows along the face (Lessons 36), or
  they go dark.
