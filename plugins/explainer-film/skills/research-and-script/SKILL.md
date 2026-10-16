---
name: research-and-script
description: Research a chapter of an explainer film into a sourced research ledger, propose about three outlines, and write the narration script (page by page, timed to about 3-5 minutes) for the voice. Use at the start of every new chapter.
---

# Research, outlines and script

**Example.** For "what really causes inflation", four research helpers gathered 72 sourced facts in
four groups (history, real cases, the home country now, how inflation works); 43 claims they could
not confirm were listed and kept out. Three outlines were offered; the user chose one; the script
was written from it and checked before recording.

## 1. Research ledger (helpers in parallel)

- Split the topic into 3-5 angles. Give each research helper the angle, the audience, the date, and
  ask for facts as a table: Id | Claim (precise) | Plain version for narration | Source (URL, what it
  is) | Confidence | Simplified or contested. Ids by group (e.g. C2-H01, C2-C01, C2-N01, C2-M01).
- Helpers must prefer primary sources (statistics offices, central banks, laws, official histories,
  the author's own words), say what they opened versus saw only in search results, and list claims
  they could not confirm separately ("kept out").
- Merge into one Markdown ledger: `NN Research - <chapter> - <title>.md`, with a Traps section
  (figures that will change soon, contested points).

## 2. Outlines (about three)

- Each outline: a one-line idea, then ten pages, each with what is said (2-4 sentences), what is
  seen, and the ledger ids it uses; estimated length and paid costs (voice letters, paintings).
- Draft from different angles, then have each checked against the ledger and the project's rules,
  and revise. Recommend one. Stop and let the user choose before writing the script.

## 3. Script

- Pages of 15-35 seconds, one idea each. Plan the length at the voice's measured speed, not a
  guess: Malina read chapter 2 at 164 words a minute against the 140 planned, so plan at about 160.
  Better, once the narration script exists: `python3 -I narration-tools/estimate_timeline.py
  NARRATION_SCRIPT.json MEASURED_WORD_TIMES.json timeline-estimated.json` works out every word's time
  from the same narrator's measured word lengths and pauses (it predicted the old chapter 2's 251.7 s
  of speech as 252 s; chapter 2 for newcomers: 406.9 s). Build and check the pages on it before paying
  for the recording.
- Spoken style: short sentences, "..." for a pause; numbers written as said ("twenty twenty-one",
  "four point one percent"); explain each term the first time, in a plain sentence of its own
  ("Interest is the extra you pay back when you borrow."), never as an aside (see step 4).
- No capitals for emphasis (the voice shouts them). No delivery cues except the one accent line at
  the start of every page (e.g. `[in a warm, steady New Zealand accent]`).
- Names the voice gets wrong: write them in phonetic symbols in the text and map them back in
  `phonetic_names` (e.g. `"/məˈteɪi/": "Mattei"`, `"/rʊə/": "Ruhr"`).
- Opinions are said as someone's ("Mattei argues..., she says").
- Save the exact words as `narration-script.json`:
  ```json
  { "voice": "Malina", "voice_id": "...", "model": "eleven_v4",
    "accent_instruction": "[in a warm, steady New Zealand accent]",
    "phonetic_names": { "/məˈteɪi/": "Mattei" },
    "pages": [ { "page": 1, "name": "the question", "text": "[in a warm, steady New Zealand accent] So... won't ..." } ] }
  ```
  (the film kit's `examples/new-chapter-template/narration-script.json` is a blank copy).
- Also write a readable script file (`NN Script - <chapter>.md`) with each page's research ids.
- Then run the `check-facts` skill before recording.

## 4. Writing for newcomers (from rewriting chapter 2, log 33)

**Example.** Viewers got lost in chapter 2 as recorded: eight real cases in about 4 and a half
minutes, jumping back and forth in time, at 164 words a minute, with words like "unemployment" and
"central bank" explained only in quick asides. The newcomer version uses one imagined picture (two factories, each
standing for a whole country), four real cases in time order, each placed on the picture out loud,
three guesses, and the rule said twice in the same words. It came out about 7 minutes long.

- **One idea per chapter**, said in one sentence a viewer could repeat.
- **One picture first, then the real cases**: say what the picture stands for, say aloud where each
  case sits on it, and say where the picture stops working.
- **About four real cases, in at most three places, with time running one way.**
- **Every unfamiliar word explained the first time, in a few plain words, or left out.**
- **One name for each thing, both ways**: never two words for one thing, never one word for two
  things (e.g. "banks" for ordinary banks and the central bank).
- **"Before I tell you, guess" moments** at the end of a page, with about 4 seconds held in the film
  (a written "..." gives under a second). **Recaps in the same words each time.**
- **Numbers**: never two new numbers in one sentence, except a "from... to" pair or a date with one
  figure; give each a plain
  anchor ("about three in a hundred"; a hundred-dollar basket going to about a hundred and four).
- **Short sentences**, about 8 to 10 words, and never an aside between a subject and its verb.
- **A rule only as strong as its evidence** ("When new money is spent... and there are spare workers,
  materials and machines... it mostly gets more things made").
- **Listener questions**: end the script file with "Before recording", a few questions to ask a real
  newcomer after they hear it (the key one asks them to use the idea on a new case).
- **Test it**: run the workflow `test-script-with-newcomers` (args: `script`, `ledger`, `work`,
  `today`, and optionally `rules`, `older`, `viewer`, `voice`, `wordsPerMinute`). A viewer copy (if
  none is given), four fresh helpers (imagined newcomers who see only what a viewer sees, a fact
  checker, a rules-and-voice reader, a skeptic), a fixer that makes only confirmed fixes, a re-check of
  every changed sentence, and a last fixer if the re-check finds anything above minor.
  Then read the script to one or two real newcomers before recording: imagined viewers are only a
  first filter. Chapter 2's finished example: `austerity-explainer/chapter-2-inflation/33 Script -
  chapter 2 - what really causes inflation - for newcomers.md`.
