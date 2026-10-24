Preflight plates (before paying for paintings): FAIL. 1 to fix, 4 to look at, 0 known and accepted, 0 input(s) missing; 4 check(s) in 5.8 s.
Paid step BLOCKED: asking the painter for these paintings (about US$0.44: an estimate: 4.8 c a megapixel (read 2026-10-16) x the megapixels returned and sent). First fix the failures below (or accept them, with who and when), then run this stage again.

Made 2026-10-16 11:28:03 by preflight.py version d836d994; kit /home/user/Music/plugins/explainer-film/kit; every tool's own output is in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803.

## To fix (these block the next step)

- glow inside a hollow [pt]: brazier: 8.0% of the top is lit (limit 2%): the painter lifts a glowing hollow into a bright band (lesson 138). Darken the glow inside it in the plate first. (paint_request.py)
  Fix: Lower the coals' glow or hide it behind the front rim, then draw the plate again.

## To look at (they do not block; a person decides)

- figures against their surround [pt]: man hand on bar and man leaning are barely darker than what surrounds them in the plate (over 0.5 of its brightness); the painter lifts figures about three times toward their surround (people test 0.15 to 0.50), so these will read pale. (paint_request.py)
  Fix: Darken their cloth or stand them against a lighter background.
- figures casting long shadows [pt]: No helper plate (the plate drawn without the figures) given (--helper-plate). (paint_request.py)
- hidden figures [pt]: walker 6 do not show in the plate at all; the prompt does not count them. (paint_request.py)
- real people [pt]: No list of real people given (--real-names). (paint_request.py)

## Inputs not given (the stage runs without them, but checks less)

- --helper-plate HELPER_PLATE: the plate drawn without the figures (for the long-shadow check); without it the long-shadow check (lesson 135) cannot run.
  Make it: render the plate again with the figures hidden
- --spend-ledger SPEND_LEDGER: the spend ledger (allowances and every paid step so far); without it nothing checks the step against what is left of the allowance.
  Make it: write one entry per paid step ({"allowances": [...], "entries": [...]}; format in calculators/plan_budget.py's note)

## Cost and time

- painting pt: US$0.44 (an estimate: 4.8 c a megapixel (read 2026-10-16) x the megapixels returned and sent)
- this preflight: 5.8 s

## Checks run

- PASS  the plate rendered cleanly (plan_lights.py render-log) [pt]: 0 fail, 0 look, 0 known, 0 pass, 0 info; exit 0, 0.1 s; calculators/plan_lights.py version 4836ed1f
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/calculators/plan_lights.py render-log /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/empty.log --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803/01-the-plate-rendered-cleanly-plan-lights-py-render.json
- PASS  the shot checker's report: new problems only [pt]: 0 fail, 0 look, 0 known, 1 pass, 0 info; exit 0, 0.0 s; check_shot.py report version d836d994
  (inside the preflight)
- FAIL  the plate is ready to paint (paint_request.py preflight) [pt]: 1 fail, 4 look, 0 known, 7 pass, 0 info; exit 1, 5.4 s; calculators/paint_request.py version aef5911c
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/calculators/paint_request.py preflight --check /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/painting/people-test-paint-check.json --facts /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts --plate /home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/people-test-plate.jpg --work-folder /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803/paint-work --render-log /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/empty.log --shot-report /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/report.md --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803/03-the-plate-is-ready-to-paint-paint-request-py-pre.json
- PASS  the painting's price (paint_request.py price) [pt]: 0 fail, 0 look, 0 known, 0 pass, 0 info; exit 0, 0.3 s; calculators/paint_request.py version aef5911c
  /usr/bin/python3 -I -B /home/user/Music/plugins/explainer-film/kit/calculators/paint_request.py price --out /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803/04-the-painting-s-price-paint-request-py-price.json

## Inputs (sha1 when the run ended)

- 4b7693247f825d779a165259e2457c97019d8ae0  /home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/people-test-plate.jpg
- 6bef7584707c4b83a90a09e36a3be7e942fbab72  /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/painting/people-test-paint-check.json
- da39a3ee5e6b4b0d3255bfef95601890afd80709  /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/empty.log
- b68e7e49411648a3eec7a6e9c2b5c75ff0532f0c  /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/bad/report.md
- 8ccc610588650dc9b9917badcb80aee729c4a300  /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts

The same report as JSON: /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-calculators/tester/runs/plates2/preflight-plates-2026-10-16-112803.json
