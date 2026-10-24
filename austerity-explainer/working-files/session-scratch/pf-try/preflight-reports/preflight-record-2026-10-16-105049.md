Preflight record (after recording): FAIL. 1 to fix, 10 to look at, 0 known and accepted, 0 input(s) missing; 2 check(s) in 23.0 s.
Paid step BLOCKED: using these recordings (re-recording any page listed is paid). First fix the failures below (or accept them, with who and when), then run this stage again.

Made 2026-10-16 10:50:49 by preflight.py version 8d91e989; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-record-2026-10-16-105049.

## To fix (these block the next step)

- exit code: it exited 2 (a refusal or a failure): usage: lint_script.py [-h] {before,after} ... | lint_script.py: error: unrecognized arguments: --word-times /home/user/Music/austerity-explainer/chapter-2-inflation/narration/word-times.json (lint_script.py)

## To look at (they do not block; a person decides)

- look: LOOK page 1: listen to "won't" +8.1, "inflation?" +9.0, "You've" +6.9, "felt" +8.8, "same" +6.9, "see" +9.3 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 2: listen to "Unemployment," +7.8, "war" +7.1, "partly" +6.4, "more" +8.6, "end" +10.1, "prices" +6.0 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 3: listen to "Now" +10.0, "picture" +10.9, "two" +6.2, "first," +8.3, "machines" +5.0, "in," +7.6, "second," +9.9, "every" +5.0 ... (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 4: listen to "Homes" +8.7, "1915," +9.3, "pushed" +5.2, "quarter." +5.2, "twenty" +8.1, "Homes" +6.8 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 5: listen to "central" +9.4, "sets" +7.4, "double" +5.5, "new" +10.1, "own" +6.2, "soar." +5.2, "eight" +8.9, "After" +11.1 ... (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 6: listen to "Prices" +6.4, "Then" +6.1, "French" +6.6, "government" +10.2, "keeps" +6.5, "paying" +7.7, "November," +7.4, "new" +6.8 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 7: listen to "Prices" +6.8, "everything" +6.0, "latest" +9.6, "prices" +6.1 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 8: listen to "new" +8.9, "or" +8.3, "on" +6.1, "twenty" +10.2, "our" +5.5, "House" +7.0, "independent" +5.8, "support" +7.3 ... (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 9: listen to "usual" +9.1, "Bank" +8.3, "Loans" +5.0, "Within" +6.9, "Prices" +9.3, "Mattei" +8.9, "fewer" +9.3 (higher or louder than the page; a person decides) (sound_gates.py)
- look: LOOK page 10: listen to "our" +7.2, "pushed" +7.9, "quarter" +6.4, "end" +8.1, "two" +5.8, "ask" +9.1, "Spent" +7.4, "pays" +7.3 ... (higher or louder than the page; a person decides) (sound_gates.py)

## Checks run

- FAIL  the recordings against the script (lint_script.py after): 1 fail, 0 look, 0 known, 0 pass, 0 info; exit 2, 0.1 s; narration-tools/lint_script.py version 87bdda5e
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/lint_script.py after /home/user/Music/austerity-explainer/chapter-2-inflation/narration/chapter-2-narration.json --transcripts /home/user/Music/austerity-explainer/chapter-2-inflation/narration/transcripts --recordings /home/user/Music/austerity-explainer/chapter-2-inflation/narration/recordings --word-times /home/user/Music/austerity-explainer/chapter-2-inflation/narration/word-times.json --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-record-2026-10-16-105049/01-the-recordings-against-the-script-lint-script-py.json
- WARN  voice steadiness (sound_gates.py voice): 0 fail, 10 look, 0 known, 0 pass, 0 info; exit 0, 22.9 s; narration-tools/sound_gates.py version deb50241
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/narration-tools/sound_gates.py voice /home/user/Music/austerity-explainer/chapter-2-inflation/narration/word-times.json --recordings-from /home/user/Music/austerity-explainer/chapter-2-inflation/narration/recordings --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-record-2026-10-16-105049/02-voice-steadiness-sound-gates-py-voice.json

## Inputs (sha1 when the run ended)

- 3b078efaed331e001eaacb270088a4a863471553  /home/user/Music/austerity-explainer/chapter-2-inflation/narration/chapter-2-narration.json
- d2146a67855a6c4adb70a082bd39c1663de0ffc9  /home/user/Music/austerity-explainer/chapter-2-inflation/narration/recordings
- 0ab07185f935b2b688ff200c4d8fa8320bd6b3ae  /home/user/Music/austerity-explainer/chapter-2-inflation/narration/transcripts
- eed4faf4a948b7cd4cf82f3d258b5f322bfe7667  /home/user/Music/austerity-explainer/chapter-2-inflation/narration/word-times.json

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/pf-try/preflight-reports/preflight-record-2026-10-16-105049.json
