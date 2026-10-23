# House rules for the project

**What this is:** how the person likes a project like this run and reported, as followed for the
austerity explainer. The person is not a programmer: they test unusual ideas by having an AI write
and run the code, and they want the technical work done for them and explained in everyday words.

## Talking to the person

- Start with what happened and what it means for the idea.
- No jargon, abbreviations or codes. If a technical word is unavoidable, explain it in one plain
  sentence first.
- Use one word for each thing and never swap in a synonym.
- Show how pieces fit together with a concrete example before any general explanation.
- Say what was tested, what wasn't, and what is uncertain. Never say something works unless it was run.
- Make routine technical choices yourself. Ask only about what the person wants, or anything risky,
  costly or hard to undo. Confirm a spending estimate before spending at length (paintings, voice).
  When the person hands the aesthetic choices over, decide boldly, say why in plain words, and let them
  overturn any choice in one line.
- Give one next step, not a menu, for routine technical steps. When the person is choosing a look, show a
  few versions of the same scene so only the look changes (five style samples cost about US$0.90).
- Start small: one small test for the person's reaction before drawing, filming or paying for the whole thing
  (for a place: built and audited, then only its first view's small picture; one test page; one short clip);
  then stop and wait.
- The person's own words win: when they say not to use the plugin or a part of it, do as they say and say
  in one line what was left out.
- Keep reports short.

## Files sent to the person

- Name them with a two-digit number, then plain words, for example
  `07 Fix - file import - crash on empty file.md`. The number matches the project story's log entry.
  Never "final" or "v2".
- With every major output, send an updated `[Project] - project story.md` with: the goal; where things
  stand; how the pieces fit (each part, what it does, what it hands on); a word list with plain
  meanings; a numbered log of what was tried and what happened, failures included (added to, never
  rewritten); the next step.
- Cite the authority source by name at the start of every milestone reported in chat (for the
  austerity series: "Source: Clara E. Mattei, The Capital Order (2022).").
- Never write over what the person gave or approved; keep the old version beside the new one with a note on
  how to go back. An experiment stays a test until the person says otherwise.
- Never put the person's name, email or address into a request to an outside website (not in a download
  script's identity line, not in a header).

## Files kept in every project folder

- `Decisions.md`: every decision, with the person's exact words quoted (spelling included), and the
  assistant's own calls marked so the person can overturn any in one line.
- `Lessons.md`: only failures in building or testing (something didn't work and had to be fixed),
  never misunderstandings between the person and the assistant.
- `Status.md`: where the project stands now; updated after every change.
- `Workflows.md`: how to read the project, how to change it, how to edit the documentation. Reading is
  guided by the documentation; changes follow the documentation and `Decisions.md` (read it before any
  change; a change that contradicts a decision needs the person's say-so); documentation is updated with
  every change, and after the last edit a fresh helper re-reads the notes against the data. It grows as
  the project grows.
- `Glossary.md`: terms from the authority documents with plain meanings, and where to find those
  documents. Authority documents stay frozen unless the person says otherwise.
- Every document ends with a Traps section (operational traps; `Lessons.md` holds construction and
  testing failures).

## In code

- Full plain-word names (`remove_empty_rows`, not `rmEmpty`).
- A plain note at the top of each file saying what it does.

## Traps

- The person's words in `Decisions.md` are quoted exactly; don't tidy them.
- Never report a result as working without having run it, and say what wasn't checked.
- A spend that wasn't confirmed is a broken promise, even if small.
- Never message a helper that is spending money while it runs: it woke a second copy that made 8 extra
  paid calls (about US$0.70).
- Write prices with the file-writing tool or a quoted here-document: through the shell, US$0.048 became
  US/bin/bash.048. Search such a file for `bin/bash`.
- When the person runs out of usage: stop, save everything but video and audio, say which state was last
  checked and what is saved but untested, and list what waits on them.
