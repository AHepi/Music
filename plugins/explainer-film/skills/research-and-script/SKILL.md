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

- Pages of 15-35 seconds, one idea each; about 150 spoken words a minute.
- Spoken style: short sentences, "..." for a pause; numbers written as said ("twenty twenty-one",
  "four point one percent"); explain each term in a few words the first time ("unemployment, the
  share of workers without a job").
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
