Preflight script (before recording the narration): FAIL. 1 to fix, 0 to look at, 0 known and accepted, 0 input(s) missing; 1 check(s) in 0.0 s.
Paid step BLOCKED: recording the narration with the voice service. First fix the failures below (or accept them, with who and when), then run this stage again.

Made 2026-10-16 11:24:42 by preflight.py version d836d994; kit /nonexistent/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/kit/preflight-script-2026-10-16-112442.

## To fix (these block the next step)

- ERROR the kit has no narration-tools/lint_script.py (kit: /nonexistent/kit) (lint_script.py)

## Inputs not given (the stage runs without them, but checks less)

- --word-times WORD_TIMES: an earlier word-times file of the SAME voice (to estimate the timeline before paying); without it no estimated timeline is made and the pages' speeds are not judged.
  Make it: narration-tools/extract_word_times.py on an earlier recording; the kit ships examples/inflation-chapter-2/word-times.json
- --spend-ledger SPEND_LEDGER: the spend ledger (allowances and every paid step so far); without it nothing checks the step against what is left of the allowance.
  Make it: write one entry per paid step ({"allowances": [...], "entries": [...]}; format in calculators/plan_budget.py's note)

## Checks run

- FAIL  script gate (lint_script.py before): 1 fail, 0 look, 0 known, 0 pass, 0 info; exit 2, 0.0 s; narration-tools/lint_script.py version missing
  /usr/bin/python3 -I -B /nonexistent/kit/narration-tools/lint_script.py before '/home/user/Music/austerity-explainer/chapter-2-inflation/33 Narration script - chapter 2 for newcomers.json' --timeline-out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/kit/preflight-script-2026-10-16-112442/estimated-timeline.json --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/kit/preflight-script-2026-10-16-112442/01-script-gate-lint-script-py-before.json

## Inputs (sha1 when the run ended)

- 090becd91fce74e521c0ce4c0638c3445eba7b83  /home/user/Music/austerity-explainer/chapter-2-inflation/33 Narration script - chapter 2 for newcomers.json

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/kit/preflight-script-2026-10-16-112442.json
