# About this example

**What this is:** chapter 1 of the austerity explainer, "Where austerity came from" (3 minutes 41
seconds, ten pages), with every file the paper film was made from. Source for the story: Clara E.
Mattei, *The Capital Order* (2022). The scene that uses these files is
`paper-film/scenes/austerity-chapter-1.js`.

| File | What it is | Made by |
|---|---|---|
| `narration-script.json` | the exact words of each page, with the accent instruction | written by hand |
| `recordings/page1.mp3` ... `page10.mp3` | Malina reading each page | ElevenLabs |
| `transcripts/page1-words.json` ... | the time of every word within each recording | ElevenLabs transcription |
| `word-times.json` | tidy word times per page (first words corrected) | `narration-tools/extract_word_times.py` |
| `timeline.json` | every word's time within the chapter; what the page files read | `narration-tools/assemble_chapter_narration.py --pauses 1.7,1.4,1.1,1.5,1.5,1.3,1.5,1.4,1.6` |
| `mouth-page-1.json`, `mouth-page-3.json` | how far the politician's and the miner's jaws open on each frame | `paper-film/tools/make_mouth_track.py` (2.3 to 9.0 s, and 67.5 to 70.0 s) |
| `cut-list.json` | every painting and piece, with its settings and repairs | written by hand |
| `plan.md` | the page-by-page plan: what appears on which words | written before painting |
| `style-research.md` | what makes cut-out and pop-up animation read as paper | research for the look |
| `captions.srt`, `captions.vtt` | the captions | `narration-tools/make_captions.py` |
| `cover.jpg` | the cover picture (99.6 s, page 5) | a frame of the master |
| `stills/` | eight moments drawn by the kit, to compare with your own first renders | `render-paper-film.mjs --stills` |

To rebuild the sound exactly as filmed (checked byte for byte when the kit was made):
```
python3 -I narration-tools/extract_word_times.py examples/austerity-chapter-1/transcripts examples/austerity-chapter-1/narration-script.json word-times.json examples/austerity-chapter-1/recordings
python3 -I narration-tools/assemble_chapter_narration.py word-times.json narration.wav timeline.json --pauses 1.7,1.4,1.1,1.5,1.5,1.3,1.5,1.4,1.6
bash narration-tools/mix_narration_over_music.sh "assets/soundtrack/Tension and Gravity.mp3" narration.wav mix.wav mix.mp3
```

The plan was followed with some changes made while building (for example the map of Italy printed on
a card, the stamp also crashing down on "takes charge", the ending turning to a plain dark page); the
page files are the final word on what happens.

## Traps

- The page files read `timeline.json` from this folder; if you re-record a page, rebuild the timeline
  and every time after that page moves.
- The stills were drawn from pieces made from the JPEG paintings in this kit; the delivered film used
  the PNG originals. The difference is too small to see.
