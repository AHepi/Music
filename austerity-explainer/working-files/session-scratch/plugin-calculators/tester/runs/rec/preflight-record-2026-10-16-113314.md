Preflight record (after recording): PASS, with things to look at. 0 to fix, 14 to look at, 0 known and accepted, 0 input(s) missing; 1 check(s) in 0.1 s.
Paid step ready: using these recordings (re-recording any page listed is paid). It still needs the user's yes before anything is paid.

Made 2026-10-16 11:33:14 by preflight.py version d836d994; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec/preflight-record-2026-10-16-113314.

## To look at (they do not block; a person decides)

- LOOK page 1: "So..." leaves at most 0.96 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 1: "inflation..." leaves at most 0.96 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 2: "buy..." leaves at most 0.75 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 3: "arrives..." leaves at most 0.84 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 3: "factory..." leaves at most 0.96 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 4: "up..." leaves at most 0.45 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 5: "move..." leaves at most 0.49 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 5: "investments..." leaves at most 0.93 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 6: "protest..." leaves at most 0.91 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 6: "up..." leaves at most 0.64 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 7: "months..." leaves at most 0.69 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 7: "out..." leaves at most 0.53 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 8: "first..." leaves at most 0.80 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)
- LOOK page 9: "fall..." leaves at most 0.80 s from the word to the next (a thinking pause needs 1.0 s: hold the picture instead) (lint_script.py)

## Inputs not given (the stage runs without them, but checks less)

- --word-times WORD_TIMES: an earlier word-times file of the SAME voice (to estimate the timeline before paying); the word times of THIS recording (narration-tools/extract_word_times.py) let the voice gate find pages to record again.
  Make it: narration-tools/extract_word_times.py on an earlier recording; the kit ships examples/inflation-chapter-2/word-times.json

## Checks run

- WARN  the recordings against the script (lint_script.py after): 0 fail, 14 look, 0 known, 0 pass, 1 info; exit 0, 0.1 s; narration-tools/lint_script.py version 645b3b03
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/lint_script.py after /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-narration-script.json --transcripts /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-transcripts --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec/preflight-record-2026-10-16-113314/01-the-recordings-against-the-script-lint-script-py.json

## Inputs (sha1 when the run ended)

- 3b078efaed331e001eaacb270088a4a863471553  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-narration-script.json
- 0ab07185f935b2b688ff200c4d8fa8320bd6b3ae  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/script/old-chapter-2-transcripts

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/rec/preflight-record-2026-10-16-113314.json
