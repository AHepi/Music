Preflight script (before recording the narration): INPUTS MISSING OR UNUSABLE. 0 to fix, 11 to look at, 1 known and accepted, 1 input(s) missing; 1 check(s) in 0.2 s.
Paid step BLOCKED: recording the narration with the voice service (about US$1.10: 6,287 credits: one per letter sent, the cue included). First make (or mend) the inputs listed below, then run this stage again.
Time: the chapter, as estimated from the script: about 6.7 min.

Made 2026-10-16 11:56:20 by preflight.py version 2dd7bb91; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/r/preflight-reports/preflight-script-2026-10-16-115620.

## Inputs missing or unusable (the stage cannot pass without them; exit 2)

- --accepted ACCEPTED: the problems accepted on purpose (a JSON list of entries, each with "stage", a "check" or "text", "reason", "who" and "date" YYYY-MM-DD). Needed by the accepted problems. Given but it cannot be used: acc-broad.json: the entry {stage 'script', check 'speed'} matches 5 findings (at most 3, film-settings.json preflight.accepted_entry_most_findings): name the "check" exactly and add "page", "view" or a longer "text", or write one entry per finding.
  Make it: write it by hand (see --example-plan's "accepted")

## To look at (they do not block; a person decides)

- main rule: no main_rule named; these sentences are said word for word on more than one page: "when new money is spent and there are spare workers materials and machines it mostly gets more things made" (pages 5, 16); "when nothing is spare it mostly pushes prices up" (pages 5, 16). Name the rule with main_rule. (lint_script.py)
- speed [page 2]: 179 words a minute (over 170): fewer words, or shorter sentences (lint_script.py)
- speed [page 4]: 173 words a minute (over 170): fewer words, or shorter sentences (lint_script.py)
- speed [page 13]: 174 words a minute (over 170): fewer words, or shorter sentences (lint_script.py)
- speed [page 14]: 173 words a minute (over 170): fewer words, or shorter sentences (lint_script.py)
- speed [page 15]: 177 words a minute (over 170): fewer words, or shorter sentences (lint_script.py)
- stakes: the first 30 s say: "p. Is that always true? It matters... because when prices go up too fast, the usual cure makes many loans cost more. And that can put people out of work. Who can create new money? Here in New Zealand,"; words about what is at stake: cost, costs, cure, loan, loans, money, out of work, price, prices, work (a person judges whether the stakes are said this early) (lint_script.py)
- unfamiliar words: 7 words a newcomer may not know (no common-words list given: words of 9 letters or more are listed): inflation, economists, submarines, Landlords, America's, unfortunate, economist. Each needs an explanation within two sentences, or cut it. (lint_script.py)
- names: names and places (is each introduced? will the voice say it right?): New, Zealand, Reserve, Bank, First, World, War, Glasgow, November, Britain's, Parliament, Covid, Mattei, June (lint_script.py)
- one word, one meaning: repeated words, to read with their sentences (each should mean one thing): price x19, money x17, worker x13, factory x13, machine x9, work x8, material x8, cost x7, cure x7, bank x7, spent x7, spare x7, people x6, reserve x6, fewer x6 (lint_script.py)
- guess holds [page 9]: ends on a question without a guess phrase ("Are there spare workers, materials and machines to make what"): if the viewer should think, end with "Have a guess." or mark "guess": true (lint_script.py)

## Known and accepted (kept on purpose; they do not block)

- key page: no page is marked "key": true (the page carrying the main idea; it gets a card hold and must not be faster than the median page) (lint_script.py)
  Accepted: test (the tester, 2026-10-15; acc-broad.json)

## Inputs not given (the stage runs without them, but checks less)

- --spend-ledger SPEND_LEDGER: the spend ledger (allowances and every paid step so far); without it nothing checks the step against what is left of the allowance.
  Make it: write one entry per paid step ({"allowances": [...], "entries": [...]}; format in calculators/plan_budget.py's note)

## Cost and time

- the narration (voice service): US$1.10 (6,287 credits: one per letter sent, the cue included)
- the chapter, as estimated from the script: about 6.7 min (saved as /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/r/preflight-reports/preflight-script-2026-10-16-115620/estimated-timeline.json)
- this preflight: 0.2 s

## Notes

- Accepted entry {stage 'script', check 'speed'} (acc-broad.json, the tester, 2026-10-15): matched 5 finding(s)
- Accepted entry {stage 'script', check 'key page'} (acc-broad.json, the tester, 2026-10-15): matched 1 finding(s)

## Checks run

- WARN  script gate (lint_script.py before): 0 fail, 11 look, 1 known, 0 pass, 4 info; exit 1, 0.1 s; narration-tools/lint_script.py version 645b3b03
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/lint_script.py before /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/newcomer-narration-script.json --word-times /home/user/Music/plugins/explainer-film/kit/examples/inflation-chapter-2/word-times.json --timeline-out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/r/preflight-reports/preflight-script-2026-10-16-115620/estimated-timeline.json --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/r/preflight-reports/preflight-script-2026-10-16-115620/01-script-gate-lint-script-py-before.json

## Inputs (sha1 when the run ended)

- 090becd91fce74e521c0ce4c0638c3445eba7b83  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/newcomer-narration-script.json
- eed4faf4a948b7cd4cf82f3d258b5f322bfe7667  /home/user/Music/plugins/explainer-film/kit/examples/inflation-chapter-2/word-times.json
- 6db76b4cce7e8a2b6fdead7d83c7219f24b8180e  /home/user/Music/plugins/explainer-film/kit/film-settings.json
- 88025f5118f323547aab85966d1a2cd6695aed00  /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/acc-broad.json

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/fixer/r/preflight-reports/preflight-script-2026-10-16-115620.json
