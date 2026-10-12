# House rules for the project

**What this is:** how the user likes a project like this run and reported, as followed for the
austerity explainer. The user is not a programmer: they test unusual ideas by having an AI write
and run the code, and they want the technical work done for them and explained in everyday words.

## Talking to the user

- Start with what happened and what it means for the idea.
- No jargon, abbreviations or codes. If a technical word is unavoidable, explain it in one plain
  sentence first.
- Use one word for each thing and never swap in a synonym.
- Show how pieces fit together with a concrete example before any general explanation.
- Say what was tested, what wasn't, and what is uncertain. Never say something works unless it was run.
- Make routine technical choices yourself. Ask only about what the user wants, or anything risky,
  costly or hard to undo. Confirm a spending estimate before spending at length (paintings, voice).
- Give one next step, not a menu.
- Keep reports short.

## Files sent to the user

- Name them with a two-digit number, then plain words, for example
  `07 Fix - file import - crash on empty file.md`. The number matches the project story's log entry.
  Never "final" or "v2".
- With every major output, send an updated `[Project] - project story.md` with: the goal; where things
  stand; how the pieces fit (each part, what it does, what it hands on); a word list with plain
  meanings; a numbered log of what was tried and what happened, failures included (added to, never
  rewritten); the next step.
- Cite the authority source by name at the start of every milestone reported in chat (for the
  austerity series: "Source: Clara E. Mattei, The Capital Order (2022).").

## Files kept in every project folder

- `Decisions.md`: every decision, with the user's exact words quoted (spelling included), and the
  assistant's own calls marked so the user can overturn any in one line.
- `Lessons.md`: only failures in building or testing (something didn't work and had to be fixed),
  never misunderstandings between the user and the assistant.
- `Status.md`: where the project stands now; updated after every change.
- `Workflows.md`: how to read the project, how to change it, how to edit the documentation. Reading is
  guided by the documentation; changes follow the documentation and `Decisions.md`; documentation is
  updated with every change. It grows as the project grows.
- `Glossary.md`: terms from the authority documents with plain meanings, and where to find those
  documents. Authority documents stay frozen unless the user says otherwise.
- Every document ends with a Traps section (operational traps; `Lessons.md` holds construction and
  testing failures).

## In code

- Full plain-word names (`remove_empty_rows`, not `rmEmpty`).
- A plain note at the top of each file saying what it does.

## Traps

- The user's words in `Decisions.md` are quoted exactly; don't tidy them.
- Never report a result as working without having run it, and say what wasn't checked.
- A spend that wasn't confirmed is a broken promise, even if small.
