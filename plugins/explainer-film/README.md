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
| `skills/research-and-script` | Research ledger with sources, about three outlines, the script for the voice. |
| `skills/check-facts` | Skeptical fact checking of spoken and on-screen claims (workflow `verify-facts`). |
| `skills/record-narration` | ElevenLabs recording page by page, word times, timeline, mix, voice checks. |
| `skills/paint-and-cut` | fal paintings, depth maps to make rooms with depth, cut-out pieces. |
| `skills/build-cinema-page` | Building a page file; `guide.md` is the full guide; parallel helpers via workflow `build-pages`. |
| `skills/check-and-critique` | Stills, page turns, and an independent critique (workflow `critique-film`). |
| `skills/film-and-finish` | Filming in parallel stretches, sound, sendable copy, captions, cover, measurements. |
| `agents/` | `page-builder`, `fact-checker`, `film-critic` (all at medium effort). |
| `workflows/` | `verify-facts`, `critique-film`, `check-fixes`, `build-pages` (run as `/explainer-film:NAME`, or with the Workflow tool). |
| `bin/explainer-film-setup` | Sets up the kit in a working folder (on the PATH once installed). |
| `kit/` | The film kit: `paper-film/` (stage, scenes, tools, templates), `narration-tools/`, `examples/` (word timelines of chapters 1 and 2), `docs/` (the paper look's full how-to). |

The kit holds code and timelines, not pictures or sound: a chapter's paintings, cut-outs and
recordings stay in its own project (the austerity explainer keeps chapter 2's in
`austerity-explainer/chapter-2-inflation/`).

## A concrete example

In chapter 2 the narrator says "and prices climb" at 66.98 seconds. Page 3's file asks for
`kit.at('climb')` and at that moment a flip counter on a card factory flips £1.25 → £1.60 → £2.00,
coins stack beside it, and a red label PRICES CLIMB points at the counter. The whole film is timed
to spoken words like that.
