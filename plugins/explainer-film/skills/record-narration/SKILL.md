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

1. **Check the script, then confirm the cost** with the user. First
   `python3 -I narration-tools/lint_script.py before narration-script.json --word-times EARLIER_WORD_TIMES.json --timeline-out timeline-estimated.json`
   (EARLIER_WORD_TIMES: any earlier recording of the same voice). Its errors stop the recording: a cue
   that is not the one accent line, capitals, a name not in its sound spelling, sentences over 20 words,
   more than 6 spoken figures a minute, the main rule not said twice word for word, no page marked
   `"key": true`, a key page faster than the median page. It fills the 4 s guess holds and prints the
   credits and dollars to quote (about 1 credit per letter, the cue included). Its LOOK lists are for a
   person: unfamiliar words, names, repeated words with their sentences, the first 30 seconds.
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
6. **Mix:** `bash narration-tools/mix_narration_over_music.sh MUSIC.mp3 narration.wav mix.wav mix.mp3 timeline.json`
   (music 11 dB down, dipping under the voice; whole mix -15 LUFS). With the timeline it stops on a FAIL
   line unless the mix is as long as the narration, the music sits 18 dB (+/- 1) under her voice while
   she speaks, and the mix lines up with the narration within 2 ms. A new soundtrack: find its level first
   with `python3 -I narration-tools/sound_gates.py duck MUSIC.mp3 narration.wav timeline.json` (then
   `MUSIC_LEVEL_DB=...`); "slightly louder" is `--louder 3`.
7. **Check the recordings** (by measurement; tell the user nobody listened unless they did):
   `python3 -I narration-tools/lint_script.py after narration-script.json --transcripts transcripts --recordings recordings`
   (a cue read aloud, words that differ, missing downloads; lists each "..." that left under 1 s of
   silence and words placed late after a pause) and
   `python3 -I narration-tools/sound_gates.py voice word-times.json --recordings-from recordings`
   (re-record a page whose typical pitch is more than 1.5 semitones from the chapter's median; the spread
   across pages passes up to 2.6 semitones: chapter 2's 2.2 was accepted, chapter 1's 3.0 was not;
   raised or loud words are listed for a person). Re-record only the pages named, with their cost.
8. Copy `timeline.json` and `word-times.json` to `film-kit/examples/<chapter>/` (the pages read them),
   and print the words with times for planning:
   `python3 -I narration-tools/print_word_times.py word-times.json`.

## Traps

- Re-recording one page moves every time after it: redo steps 4-6, and film again.
- Words with trailing "..." or punctuation are matched without it (`kit.at('arrives')`).
- A word said twice on a page: ask for the second with `kit.at('war', 2)`.
