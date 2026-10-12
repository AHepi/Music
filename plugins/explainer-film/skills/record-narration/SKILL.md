---
name: record-narration
description: Record a chapter's narration page by page with ElevenLabs, get every word's time from the free transcripts, assemble the chapter timeline and narration track, mix it over music, and check the voice is steady. Use after the script is fact-checked.
---

# Record and time the narration

Kit folder below = the folder made by `explainer-film-setup` (it holds `narration-tools/`).
Full detail for each step: `film-kit/docs/paper-look - 01 How to make a film with this kit.md`,
steps 2-5 (the same for both looks).

**Example.** Chapter 2: ten pages, one take each, about 4,300 credits; pitch spread across pages
2.2 semitones (steady); mixed at -15 LUFS; 270.33 s long.

## Steps

1. **Confirm the cost** (about 1 credit per letter of the script file's text) with the user.
2. **Record each page on its own** with the ElevenLabs connector, all on one flow
   (`creative_create_flow` first, then `creative_generate_speech` per page with the page's full text,
   the voice id, model `eleven_v4`, and `generations_count: 1` unless the user wants takes to choose
   from). Poll `creative_get_flow_run_status`; **download each recording at once** (links expire
   after 2 hours) as `recordings/pageN.mp3`.
3. **Transcribe** each recording (`creative_transcribe_audio`, model `eleven_scribe_v1`, free) and save
   the word list as `transcripts/pageN-words.json` (a top-level `"words"` list with `text`, `type`,
   `start`, `end`).
4. **Word times:** `python3 -I narration-tools/extract_word_times.py TRANSCRIPTS_FOLDER narration-script.json word-times.json RECORDINGS_FOLDER`
5. **Timeline and narration track:** `python3 -I narration-tools/assemble_chapter_narration.py word-times.json narration.wav timeline.json --pauses 1.6,1.5,...`
   (one pause per gap between pages, 1.4-1.7 s; the first word lands at 1.08 s; run it from the
   folder the recording paths in word-times.json start from).
6. **Mix:** `bash narration-tools/mix_narration_over_music.sh MUSIC.mp3 narration.wav mix.wav mix.mp3`
   (music 11 dB down, dipping under the voice; whole mix -15 LUFS).
7. **Check the voice** (by measurement; tell the user nobody listened unless they did):
   `python3 -I narration-tools/compare_voice_steadiness.py page1=recordings/page1.mp3 page2=recordings/page2.mp3 ...`
   (pitch spread across pages; under about 3 semitones is steady),
   `python3 -I narration-tools/find_raised_voice.py word-times.json` and
   `python3 -I narration-tools/find_loud_words.py word-times.json` (words that jump up; run from the
   folder the recording paths start from). Re-record a page only if it clearly drifts or shouts.
8. Copy `timeline.json` and `word-times.json` to `film-kit/examples/<chapter>/` (the pages read them),
   and print the words with times for planning:
   `python3 -I narration-tools/print_word_times.py word-times.json`.

## Traps

- Re-recording one page moves every time after it: redo steps 4-6, and film again.
- Words with trailing "..." or punctuation are matched without it (`kit.at('arrives')`).
- A word said twice on a page: ask for the second with `kit.at('war', 2)`.
