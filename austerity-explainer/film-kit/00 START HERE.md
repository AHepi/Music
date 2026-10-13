# Start here

**What this is:** everything needed to make more films in the paper pop-up look of "Where austerity
came from" (chapter 1 of the austerity explainer) and the cinema look of "What really causes
inflation" (chapter 2): the tools, step-by-step instructions, and both chapters as worked examples
with every painting, paper piece and model. First made on 12 October 2026 as three zip files; since
13 October 2026 it lives in the repository as this folder, `austerity-explainer/film-kit/`.

## For you, in plain words

- **One folder, nothing to unzip.** This folder is the kit. (The first version was sent as three zip
  files called "14 Paper pop-up film kit", because a single file can't be bigger than 30 MB in a
  Claude chat.)
- **What to tell the other agent:** "Read `00 START HERE.md` in the kit first, then follow
  `01 How to make a film with this kit.md`."
- **What it can make with this:** a new series (for example on the enclosures) in either look:
  narration in Malina's voice, new paintings, pieces that pop up, crash in and turn like a book on
  the narrator's words, or 3D scenes with models, lamp light and a still camera.
- **What is not inside:** your soundtrack "Tension and Gravity" (the repository is public, so the
  track is kept out; copy it into `assets/soundtrack/` before mixing); the austerity project's
  research, script history and decisions (they are elsewhere in the repository); the full-length
  sound files of chapter 1 (the kit can rebuild them from the page recordings that are inside); and
  the original PNG files of chapter 1's paintings, which are high-quality JPEG copies here (they look
  the same and are a quarter of the size). Chapter 2's paintings are the original PNG files.

## For the agent: first steps

1. Work from inside this folder (`austerity-explainer/film-kit/` in the repository).
2. Install what the tools need (details in `01`, section "What you need"):
   ```
   cd paper-film && npm install && cd ..
   pip install numpy opencv-python-headless pillow      # add --break-system-packages if pip asks
   ```
   You also need `ffmpeg`, a Chromium browser (Playwright's, or set `PAPER_FILM_BROWSER`), and a bold
   font for printed labels (DejaVu Sans Bold, or set `PAPER_FILM_LABEL_FONT`).
3. The paper pieces of both chapters are already made and kept in `paper-film/pieces/`. To rebuild
   chapter 1's from its paintings (about 2 minutes):
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
   `06 House rules for the project.md`.

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
| `assets/soundtrack/` | Where the user's soundtrack "Tension and Gravity" goes; not stored, because the repository is public. |
| `paper-film/pieces/` | The paper pieces of both chapters, already made (`austerity-chapter-1/`, `inflation-chapter-2/`). |
| `paper-film/stage/cinema-stage.*` | The cinema stage used by chapter 2: 3D scenes with lens blur, glow and a film finish. |
| `paper-film/scenes/cinema-*.js`, `graphics.js`, `effects.js`, `models.js`, `model-loader.js` | The cinema kit: still shots, painted rooms with depth, card models, Blender models, titles, labels and charts. |
| `paper-film/scenes/inflation-chapter-2.js` and `inflation-chapter-2/` | Chapter 2's ten page files and the shared two-factories set. |
| `paper-film/blender/` | Scripts that build chapter 2's models in Blender (works, town, props, desk), and the Blender MCP client. |
| `examples/inflation-chapter-2/` | Chapter 2's word times and timeline. |
| `assets/paintings/inflation-chapter-2/` | Chapter 2's 11 first paintings (PNG), masks and `paintings.json`; the round-20 repaint of the bank street (406b) is kept as a painted room in `assets/reliefs/`. |
| `assets/reliefs/inflation-chapter-2/` | Painted rooms with depth (each painting with its distance picture). |
| `assets/models/inflation-chapter-2/` | The Blender models (.glb): two works, the town, the props, the reviewer's desk. |

## Traps

- Anyone given the old zip files must unzip all three parts into the same folder, or the example's
  paintings will be missing.
- The folder `paper-film` must keep that name: the stage loads its libraries from `/paper-film/`.
- Run the commands from inside this folder (called `paper-pop-up-film-kit/` in the old zips); paths in
  the cut lists and scenes start there.
- The soundtrack belongs to the user; use it for the user's own films only, and never add it to the
  public repository.
