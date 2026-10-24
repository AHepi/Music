Preflight script (before recording the narration): FAIL. 1 to fix, 11 to look at, 0 known and accepted, 0 input(s) missing; 2 check(s) in 0.3 s.
Paid step BLOCKED: recording the narration with the voice service (about US$1.10: the narration (voice service) US$1.10). First fix the failures below (or accept them, with who and when), then run this stage again.
Time: the chapter, as estimated from the script: about 6.7 min.

Made 2026-10-16 10:49:22 by preflight.py version 6bd2e370; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922.

## To fix (these block the next step)

- key page: no page is marked "key": true (the page carrying the main idea; it gets a card hold and must not be faster than the median page) (lint_script.py)

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

## Cost and time

- the narration (voice service): US$1.10 (6,287 credits: one per letter sent, the cue included)
- the chapter, as estimated from the script: about 6.7 min (saved as /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922/estimated-timeline.json)
- this preflight: 0.3 s

## Checks run

- FAIL  script gate (lint_script.py before): 1 fail, 11 look, 0 known, 0 pass, 4 info; exit 1, 0.2 s; narration-tools/lint_script.py version 87bdda5e
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/lint_script.py before '/home/user/Music/austerity-explainer/chapter-2-inflation/33 Narration script - chapter 2 for newcomers.json' --word-times /home/user/Music/plugins/explainer-film/kit/examples/inflation-chapter-2/word-times.json --timeline-out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922/estimated-timeline.json --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922/01-script-gate-lint-script-py-before.json
- PASS  the allowance left (plan_budget.py ledger): 0 fail, 0 look, 0 known, 0 pass, 0 info; exit 0, 0.1 s; calculators/plan_budget.py version bdcb5933
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/calculators/plan_budget.py ledger /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/budget/spend-ledger-logs-10-to-34.json --next-cost 1.10 --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922/02-the-allowance-left-plan-budget-py-ledger.json

## Inputs (sha1 when the run ended)

- 090becd91fce74e521c0ce4c0638c3445eba7b83  /home/user/Music/austerity-explainer/chapter-2-inflation/33 Narration script - chapter 2 for newcomers.json
- 359c110a8ee7b928c0949aade1a5af6fcd82d7bf  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/budget/spend-ledger-logs-10-to-34.json
- eed4faf4a948b7cd4cf82f3d258b5f322bfe7667  /home/user/Music/plugins/explainer-film/kit/examples/inflation-chapter-2/word-times.json

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-script-2026-10-16-104922.json
