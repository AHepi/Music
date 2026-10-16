# Explainer film (a Claude Code plugin)

What this is: everything an agent needs to make a narrated, fact-checked explainer film for a phone
screen (1080 x 1920), one chapter at a time, in the cinematic look of "What really causes
inflation" (chapter 2 of the austerity explainer) or the simpler paper pop-up look of chapter 1.
Written so that smaller models can follow it step by step.

## Install

```
/plugin marketplace add AHepi/Music
/plugin install explainer-film@ahepi-music
```
Then, in the project's working folder: `explainer-film-setup /path/to/work/film-kit`
(copies the kit and installs its drawing engine; needs Node.js 18+, Python 3.9+ with numpy, Pillow
and opencv, ffmpeg, and a Chromium browser). Paid steps use the ElevenLabs (voice) and fal
(paintings) connectors, and always ask the user before spending.

## What is inside

| Part | What it does |
|---|---|
| `skills/make-explainer-film` | The master steps, costs and rules; start here. `house-rules.md`: how to talk to the user, money, notes, file names. |
| `skills/research-and-script` | Research ledger with sources, about three outlines, the script for the voice, and how to write it for newcomers. |
| `skills/check-facts` | Skeptical fact checking of spoken and on-screen claims (workflow `verify-facts`). |
| `skills/record-narration` | ElevenLabs recording page by page, word times, timeline, mix, voice checks. |
| `skills/paint-and-cut` | fal paintings, depth maps to make rooms with depth, cut-out pieces. |
| `skills/build-cinema-page` | Building a page file; `guide.md` is the full guide; `camera-and-framing.md` the strict camera rule (still, at most 3 named moves per shot), filling a tall frame and no clipping; parallel helpers via workflow `build-pages`. |
| `skills/make-3d-models` | Detailed models (buildings, a town, a desk, props) built in Blender by script, with the official Blender MCP server (set-up, client, and the modelling notes learned through it); EEVEE under a virtual screen. |
| `skills/build-and-paint-a-place` | A whole place built in Blender by script (Poly Haven models and surfaces, lettered props, people), each view composed with the shot checker, the plate painted over and lined up, and shone back onto the set in a page that holds or slides. |
| `skills/check-and-critique` | Stills, page turns, and an independent critique (workflow `critique-film`). |
| `skills/film-and-finish` | Filming in parallel stretches, sound, sendable copy, captions, cover, measurements. |
| `agents/` | `page-builder`, `fact-checker`, `film-critic` (all at medium effort). |
| `workflows/` | `verify-facts`, `test-script-with-newcomers`, `critique-film`, `check-fixes`, `build-pages` (run as `/explainer-film:NAME`, or with the Workflow tool). |
| `bin/explainer-film-setup` | Sets up the kit in a working folder (on the PATH once installed); checks the browser, Blender and its virtual screen, the soundtrack and every kit file the skills name, and writes `machine-settings.env`. |
| Checking tools | `paper-film/tools/camera_audit.py` (measures every camera move per shot), `frame_check.py` (where things land in the frame for a camera, before rendering), `check-shot.sh` (the shot checker: measures a Blender shot against the composing rules and says what to change, in metres), `find_jumps.py` (sudden jumps in a finished film), `tone_piece.py` (calms an over-coloured cut-out), `room.clearance()` and `boxesOverlap()` in the engine (nothing passing through anything). |
| `kit/` | The film kit: `paper-film/` (stage, scenes, tools, templates, Blender scripts), `narration-tools/`, `examples/` (word timelines of chapters 1 and 2, the estimated timeline of chapter 2 for newcomers, check files of the built places), `docs/` (the full how-to; start with `paper-look - 00 START HERE.md`). `kit-sync-notes.md` says when it was last brought up to date with the austerity project's film kit and what waits. |

The kit holds code and timelines, not pictures, sound or models: a chapter's paintings, cut-outs,
recordings and Blender models stay in its own project (the austerity explainer keeps them in
`austerity-explainer/film-kit/` and `austerity-explainer/chapter-2-inflation/`).

## A concrete example

In chapter 2 the narrator says "and prices climb" at 66.98 seconds. Page 3's file asks for
`kit.at('climb')` and at that moment a flip counter on a card factory flips £1.25 → £1.60 → £2.00,
coins stack beside it, and a red label PRICES CLIMB points at the counter. The whole film is timed
to spoken words like that.
