Preflight record (after recording): FAIL. 10 to fix, 0 to look at, 0 known and accepted, 0 input(s) missing; 1 check(s) in 0.1 s.
Paid step BLOCKED: using these recordings (re-recording any page listed is paid) (about US$0.75: 4,297 credits). First fix the failures below (or accept them, with who and when), then run this stage again.

Made 2026-10-16 11:33:14 by preflight.py version d836d994; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec2/preflight-record-2026-10-16-113314.

## To fix (these block the next step)

- RE-RECORD page 1: no transcript (lint_script.py)
- RE-RECORD page 2: no transcript (lint_script.py)
- RE-RECORD page 3: no transcript (lint_script.py)
- RE-RECORD page 4: no transcript (lint_script.py)
- RE-RECORD page 5: no transcript (lint_script.py)
- RE-RECORD page 6: no transcript (lint_script.py)
- RE-RECORD page 7: no transcript (lint_script.py)
- RE-RECORD page 8: no transcript (lint_script.py)
- RE-RECORD page 9: no transcript (lint_script.py)
- RE-RECORD page 10: no transcript (lint_script.py)

## Inputs not given (the stage runs without them, but checks less)

- --word-times WORD_TIMES: an earlier word-times file of the SAME voice (to estimate the timeline before paying); the word times of THIS recording (narration-tools/extract_word_times.py) let the voice gate find pages to record again.
  Make it: narration-tools/extract_word_times.py on an earlier recording; the kit ships examples/inflation-chapter-2/word-times.json

## Cost and time

- re-recording page 1, page 2, page 3, page 4, page 5, page 6, page 7, page 8, page 9, page 10: US$0.75 (4,297 credits)
- this preflight: 0.1 s

## Checks run

- FAIL  the recordings against the script (lint_script.py after): 10 fail, 0 look, 0 known, 0 pass, 1 info; exit 1, 0.1 s; narration-tools/lint_script.py version 645b3b03
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/lint_script.py after /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-narration-script.json --transcripts /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/emptytr --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec2/preflight-record-2026-10-16-113314/01-the-recordings-against-the-script-lint-script-py.json

## Inputs (sha1 when the run ended)

- 3b078efaed331e001eaacb270088a4a863471553  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-narration-script.json
- da39a3ee5e6b4b0d3255bfef95601890afd80709  /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/emptytr

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec2/preflight-record-2026-10-16-113314.json
