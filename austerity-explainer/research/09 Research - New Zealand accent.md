# 09 Research - New Zealand accent

**What this is:** the sounds that make standard New Zealand English sound like New Zealand, what
ElevenLabs offers for controlling an accent, and how this project uses both. Written after you asked
for Malina to keep a steady New Zealand accent (log 09).

## What ElevenLabs offers (checked 11 October 2026)

- **No "accent rules" for a voice that I could find.** ElevenLabs' help page says the accent "comes
  from the voice you're using". Source: [How do I select the language and accent?](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-i-select-the-language-and-accent)
- **Pronunciation rules (dictionaries):** each rule fixes how one word is said (by its sounds, or by
  swapping in other words). They are set up in ElevenLabs Studio projects or sent with a request
  through ElevenLabs' programming interface; the connection this project uses cannot attach them. They fix
  words one at a time, so they cannot set a whole accent. Source: [Pronunciation best practices](https://elevenlabs.io/docs/best-practices/prompting/pronunciation)
- **An accent instruction inside the script** (in square brackets), which the v4 model follows.
  ElevenLabs says v4 "no longer drifts back toward its source accent over the course of a
  generation", and calls accent instructions experimental, "less consistent across different
  voices". Sources: [Eleven v4 announcement](https://elevenlabs.io/blog/eleven-v4); [Pronunciation best practices](https://elevenlabs.io/docs/best-practices/prompting/pronunciation)
- **Capital letters increase emphasis** in v4 ("VERY long day"). Same source.
- Malina is a designed voice labelled only "English", with no accent label.

## The sounds of standard New Zealand English

Source: [New Zealand English phonology (Wikipedia)](https://en.wikipedia.org/wiki/New_Zealand_English_phonology).
Each row is a vowel group named after an example word, the sound in New Zealand, and what to listen for.

| Group | NZ sound | Listen for |
|---|---|---|
| KIT (sit, fish) | /ə/, centralised | "fish and chips" sounds like "fush and chups"; the clearest NZ marker, and the main difference from Australian |
| DRESS (dress, bed) | /e/, raised | "bed" edges toward "bid" |
| TRAP (trap, cat) | /ɛ/, raised | "cat" edges toward "ket" |
| FACE (face, day) | /æɪ/ | starts lower and further forward than in British English |
| PRICE (price, my) | /aɪ/, onset pulled back | "my" starts toward "ah" |
| GOAT (goat, no) | /aʉ/ | starts open, ends with a forward "oo" |
| GOOSE (goose, you) | /ʉː/ | a very forward "oo" |
| NEAR / SQUARE | /iə/, /eə/, merging | "beer" and "bear" sound alike |
| START (start, car) | /aː/ | long open "ah"; no R |
| NURSE (nurse, word) | /øː/ | rounded, a little like "noohs" |

Other features: no R after vowels (non-rhotic), with linking R; a dark L, often vocalised at the end
of syllables; T between vowels often flapped ("butter" toward "budder"); "str" sometimes "shtr".

## How the project uses this

- The script now opens every page with the same accent instruction, "[in a warm, steady New Zealand
  accent]", and has no other delivery cues. The old mixed cues ([urgent], [wry], [serious]) moved the
  voice up and down between pages.
- The table is what to listen for when judging a take; it is not sent to ElevenLabs. Writing these
  sounds into the script for every word would mean spelling most words in phonetic symbols, which
  makes the model stumble (phonetic spellings were one likely cause of the accent jumping).
- If a particular word keeps coming out un-New-Zealand, a single pronunciation rule for that word is
  the right fix. That would need ElevenLabs Studio or a fuller connection to ElevenLabs.

## Traps

- If a feature called "accent rules" exists in your ElevenLabs screen, it did not show up in
  ElevenLabs' public documentation on 11 October 2026; check where it lives before relying on it.
- An accent instruction is followed, not guaranteed: always listen to a take before building on it.
- Do not put capitals in the script for emphasis; they make Malina push.
