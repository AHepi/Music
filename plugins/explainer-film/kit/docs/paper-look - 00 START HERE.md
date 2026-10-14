# Start here

**What this is:** everything needed to make more films in the paper pop-up look of "Where austerity
came from" (chapter 1 of the austerity explainer): the tools, step-by-step instructions, the whole
chapter as a worked example with every painting, and your soundtrack "Tension and Gravity".
Made on 12 October 2026.

## For you, in plain words

- **Three zip files, one folder.** A single file can't be bigger than 30 MB in a Claude chat, so the
  kit is split in three. Unzip all three into the same place: together they make one folder called
  `paper-pop-up-film-kit`.
  - part 1: the tools, the instructions, the example chapter's words, recordings and timings, the
    cut-out masks, and the soundtrack;
  - part 2: the background paintings;
  - part 3: the paintings of figures and objects.
- **What to tell the other agent:** "Read `00 START HERE.md` in the kit first, then follow
  `01 How to make a film with this kit.md`."
- **What it can make with this:** a new series (for example on the enclosures) in the same look:
  narration in Malina's voice, new paintings, pieces that pop up, crash in and turn like a book on
  the narrator's words, with no hands.
- **What is not inside:** the austerity project's research, script history and decisions (they
  belong to that project); the full-length sound files of chapter 1 (the kit can rebuild them from
  the page recordings that are inside); and the original PNG files of the paintings. The kit has
  high-quality JPEG copies instead, which look the same and are a quarter of the size.

## For the agent: first steps

1. Unzip all three parts into one folder. Work from inside `paper-pop-up-film-kit/`.
2. Install what the tools need (details in `01`, section "What you need"):
   ```
   cd paper-film && npm install && cd ..
   pip install numpy opencv-python-headless pillow      # add --break-system-packages if pip asks
   ```
   You also need `ffmpeg`, a Chromium browser (Playwright's, or set `PAPER_FILM_BROWSER`), and a bold
   font for printed labels (DejaVu Sans Bold, or set `PAPER_FILM_LABEL_FONT`).
3. Make the example's paper pieces from its paintings (about 2 minutes):
   ```
   python3 -I paper-film/tools/prepare_paper_pieces.py examples/austerity-chapter-1/cut-list.json .
   ```
4. Smoke test: draw two moments of the example and compare them with the ones in
   `examples/austerity-chapter-1/stills/` (they should look the same):
   ```
   node paper-film/tools/render-paper-film.mjs austerity-chapter-1 check --stills 66.1 99.6
   ```
   66.1 s is the tank landing on page 3; 99.6 s is the cover picture (page 5).
5. Read, in order: `01 How to make a film with this kit.md`, `02 The look - style rules.md`,
   `03 How a page file works.md`, `04 Painting prompts.md`, `05 Lessons and traps.md`,
   `06 House rules for the project.md`, `07 Composing a shot.md` (in this folder as `paper-look - 07 Composing a shot.md`).

## What is where

| Folder or file | What it holds |
|---|---|
| `paper-film/stage/` | The paper stage: the small 3D world with one lamp where every picture is a sheet of paper. |
| `paper-film/scenes/paper-kit.js` | Motions (fold up, drop in, slide in, hop, knock...) and the page kit each page file uses. |
| `paper-film/scenes/paper-chapter.js` | Turns a list of page files into one film: stacks the sheets, turns pages, moves the camera. |
| `paper-film/scenes/austerity-chapter-1.js` and `austerity-chapter-1/` | The worked example: ten page files. |
| `paper-film/scenes/new-chapter-template.js` and `new-chapter-template/` | The starting point for a new chapter. |
| `paper-film/tools/` | Cutting paintings into paper pieces, mouth tracks, filming, checking (contact sheets, shadows). |
| `narration-tools/` | Word times, the narration track, the mix over music, captions, finishing, sound checks. |
| `examples/austerity-chapter-1/` | The example's narration script, recordings, transcripts, word times, timeline, mouth tracks, cut list, plan, captions, cover and stills. |
| `examples/new-chapter-template/` | Empty narration script and cut list to copy. |
| `assets/paintings/austerity-chapter-1/` | 53 paintings, 43 cut-out masks, and `paintings.json` with the exact prompt of each. |
| `assets/soundtrack/` | "Tension and Gravity" (the user's own track). |

## Traps

- Unzip all three parts into the same folder, or the example's paintings will be missing.
- The folder `paper-film` must keep that name: the stage loads its libraries from `/paper-film/`.
- Run the commands from inside `paper-pop-up-film-kit/`; paths in the cut lists and scenes start there.
- The soundtrack belongs to the user; use it for the user's own films only.
