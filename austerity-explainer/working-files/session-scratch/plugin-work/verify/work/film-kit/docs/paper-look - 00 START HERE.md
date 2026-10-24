# Start here

**What this is:** the film kit as the explainer-film plugin carries it: the tools, the step-by-step
instructions and the worked examples' timelines and check files for making films in the paper pop-up look
of "Where austerity came from" (chapter 1 of the austerity explainer), the cinema look of "What really
causes inflation" (chapter 2), and the built-and-painted look of chapter 2 for newcomers (log 34: each place
built in Blender, painted over, and the painting shone back onto the set). `explainer-film-setup` copies it
into your working folder; every path below starts at that folder.

The austerity project keeps the full kit in its repository as `austerity-explainer/film-kit/`, with every
painting, paper piece and model. This copy was brought up to date with it on 16 October 2026 (what was
copied, what waits and what only the plugin has: `kit-sync-notes.md` beside the `docs` folder).

## For you, in plain words

- **One folder, nothing to unzip.** (The very first kit was sent as three zip files; that is long past.)
- **What to tell the agent:** "Read `docs/paper-look - 00 START HERE.md` first, then follow
  `docs/paper-look - 01 How to make a film with this kit.md`."
- **What it can make:** a new series in any of the three looks: narration in your chosen voice, new
  paintings, pieces that pop up and turn like a book on the narrator's words, 3D scenes with models and
  lamp light, or places built in 3D and painted over, with the camera still or sliding.
- **What is not inside:** pictures, sound and models. The paintings, paper pieces, recordings, stills
  and Blender models of the example chapters stay in the austerity project (they are too big for a
  plugin); your soundtrack is never inside (copy it into `assets/soundtrack/` before mixing). The code,
  timelines and check files of every example are here, so you can read how each was made, and the
  Blender scripts rebuild the example places from free Poly Haven models and surfaces.

## For the agent: first steps

1. Work from inside the folder `explainer-film-setup` made (it ran `npm install` in `paper-film/`; if it
   could not, run it there yourself).
2. You also need Python 3 with numpy, opencv and Pillow, `ffmpeg`, a Chromium browser (Playwright's, or
   set `PAPER_FILM_BROWSER`), and for 3D places the Blender program with a virtual screen
   (`Xvfb :96 -screen 0 1920x1080x24 &`). `explainer-film-setup` checks each one and writes what it found
   into `machine-settings.env`, which the tools read.
3. Smoke test without any pictures: draw the 100-dot panel test page and look at it.
   ```
   node paper-film/tools/render-paper-film.mjs graphics-test paper-film/out/smoke --stills 3
   ```
   It writes `paper-film/out/smoke/still-3.00.jpg`: three panels of 100 dots on a dark background.
4. Before anything is recorded, make an estimated timeline from the narration script and build the pages
   on it (they ask for words, not seconds, so they retime themselves when the real timeline arrives):
   ```
   python3 -I narration-tools/estimate_timeline.py NARRATION_SCRIPT.json MEASURED_WORD_TIMES.json examples/<chapter>/timeline-estimated.json
   ```
   (MEASURED_WORD_TIMES is a word-times file recorded by the same narrator, for example
   `examples/inflation-chapter-2/word-times.json` for Malina.)
5. Read, in order: `01 How to make a film with this kit.md`, `02 The look - style rules.md`,
   `03 How a page file works.md`, `04 Painting prompts.md`, `05 Lessons and traps.md`,
   `06 House rules for the project.md`, `07 Composing a shot.md` (all in `docs/` with the
   `paper-look - ` prefix).

## What is where

| Folder or file | What it holds |
|---|---|
| `paper-film/stage/` | The paper stage, and the cinema stage (`cinema-stage.*`: 3D scenes with lens blur, glow and a film finish; held shots draw the painted set once and only the moving things each frame). |
| `paper-film/scenes/paper-kit.js`, `paper-chapter.js` | The paper look: motions and the page kit; a list of page files turned into one film. |
| `paper-film/scenes/cinema-*.js`, `graphics.js`, `effects.js`, `models.js`, `model-loader.js` | The cinema kit: still shots, painted rooms with depth, card models, Blender models, titles, labels, charts, the 100-dot panel, rule cards. `cinema-chapter.js` joins pages (peel, dissolve, dip, run-on) and can build a long chapter lazily. |
| `paper-film/scenes/projected-set.js`, `pit-village-effects.js` | Built-and-painted places: the painting shone back onto the 3D set, a "behind" painting for what near props hide, the painted sky on a far card (`skyCard`), flames, glows and contact shadows. |
| `paper-film/scenes/austerity-chapter-1*`, `inflation-chapter-2*` | The two finished chapters' page files (read them as patterns). |
| `paper-film/scenes/inflation-chapter-2-newcomers*`, `notice-corner.js`, `people-test.js`, `lockout-test.js`, `works-states-test.js`, `lazy-loading-test.js` | Built-and-painted worked examples: the Works pages 3 to 5, the notice corner, the people test, the lockout test, state changes on a held shot, lazy loading. |
| `paper-film/scenes/new-chapter-template*`, `cinema-chapter-template*` | Starting points for a new chapter. |
| `paper-film/blender/` | Blender scripts: chapter 2's models, the pit village (street, props library, set dressing, three shots), the people (`figures/`), chapter 2's newcomer props, `shot_facts.py` for the shot checker, and the checker's tests (`tests/`). |
| `paper-film/tools/` | Cutting paintings into pieces, filming, checking (contact sheets, the shot checker `check-shot.sh`, the camera audit, `find_jumps.py`), lining up paintings (`align_painting.py`, `keep_painted_shadows.py`, `make_state_picture.py`, `make_behind_picture.py`), music under a clip (`add_music_bed.sh`). |
| `narration-tools/` | Estimated timelines, word times, the narration track, the mix, captions, finishing, sound checks. |
| `examples/` | Narration scripts, word times and timelines of the chapters; check files (`shot-check.json`) and timelines of the built-and-painted examples. |

## Traps

- The folder `paper-film` must keep that name: the stage loads its libraries from `/paper-film/`.
- Run the commands from the kit's top folder; paths in the cut lists, check files and scenes start there.
- The example scenes that need pictures or models (most of them) will not draw until those are in
  `assets/` and `paper-film/pieces/`; read them as patterns, or copy the pictures over from the
  austerity project's film kit.
- A soundtrack belongs to its owner; use it only as they allow, and never add it to a public repository.
