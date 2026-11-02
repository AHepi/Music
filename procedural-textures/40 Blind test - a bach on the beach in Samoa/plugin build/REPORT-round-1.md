# Round 1 report: a bach on the beach in Samoa, modern day

(Written by the plugin builder, a Sonnet helper at high effort, and returned as text; saved to disk by the coordinating session unchanged except for this note.)

Work folder: /home/claude/blind-test/plugin-build
Packet for the blind judge: /home/claude/blind-test/plugin-build/judge-1 (made with look/judge.py; no verdict written, no fix pass done)

## What I read and followed
Only the plugin folder: README.md, skills/make-a-painted-place/SKILL.md, look/The look.md, materials/Roles.md, the material inventory, the `--help` of each script, the example lane build script and its notes, and the top of stage/look_stage.py and materials/apply_by_role.py (to see how names turn into roles). Nothing outside the plugin and my work folder. No internet, no image generation, no rented machine, control-build not opened.

## What I built (build_bach.py -> bach.blend)
One script, plain shapes only, 78 objects (77 meshes, 12,640 faces, 1 camera). Laid along Y (the beach), ground at Z = 0, metres. The bach is turned 30 degrees about the vertical so the camera sees its front and its long left wall. Nothing is textured or lit in the build.

- The bach: 3.6 x 7 m house on timber piles; lapped weatherboard walls (one mesh per wall, boards cut around openings, a dark core behind for the shadow lines); front verandah with columns, handrails, three stairs; gable-end triangle of boards; corrugated iron roof as two real ribbed sheets, apex flashing, fascia, gutter and down pipe; a door; louvre windows (frames, slats, a pane behind: 2 lit, 2 dim, 5 dark); two LED lamps (over the door, under the verandah beam); two chairs; a leaning surfboard.
- Modern-day things: corrugated iron roof, rain tank on a stand, a solar panel on a post, a power pole with its wire to the bach, LED lamps, chairs, surfboard.
- Place: sand strip, a lawn behind the beach, the sea as two big flat boxes (a water film over a dark bed, 800 m wide so the look stage treats them as backdrop), a broken reef line, a headland at the far end, a fale (open Samoan house: posts, stone foundation, domed thatch, lantern) in the distance, a beached outrigger canoe (paopao), a fire pit (stone ring, two logs, a flame), driftwood, shore boulders, 8 coconut palms (curved ringed trunks, 15 notched drooping fronds each), 5 fern clumps.
- Camera: standing person, eye 1.65 m, 32 mm, tall frame 1080 x 1920, looking down the beach with the bach left of centre and the sea a wedge on the right. Set in the build; I did not use --person-camera.

### How I named things
Role words in every name; no `place_role` properties and no roles file. Pattern: `bach left wall board timber`, `bach front louvre lit window 0`, `bach left corrugated rust sheet`, `palm 3 frond grass`, `palm 3 trunk wood`, `beach sand ground`, `sea water`, `sea bed shadow`, `village lawn grass`, `headland moss`, `fale thatch leaf`, `fale lantern lamp glass`, `fire flame`, `hearth ring stone`, `shore boulder stone`, `rain tank steel`, `solar panel glass`, `power pole timber`.
I changed three name patterns before building because the plugin's word list (read in apply_by_role.py, not found by running it) would have given the wrong role: `step` (pavement) became `stair`; `window frame` (dark window) became `casing frame`; `fire pit` / `fire log` (flame) became `hearth`. The roof sheets are named `rust sheet`, not `roof`, because `roof` gives soot-dark slate and a Samoan iron roof is rust.

## Dressing report (dressing.json)
- 77 objects dressed, `unassigned` empty. Dressing took about 1 second. No setts laid (no flat road or pavement in the place).
- By role: wood 34, weed 14 (palm fronds, ferns, lawn), window dark 5, wall 4 (boulders, reef, fale foundation, headland-free), iron 4, lamp glass 3, window lit 2, window dim 2, rust 2 (roof sheets), recess 2 (wall core, sea bed), earth 1 (sand), water 1 (sea), moss 1 (headland), flame 1, leaf 1 (thatch).
- Honest note: the plugin has no sand, sea, palm leaf, thatch, plastic, painted weatherboard or solar glass. Sand got `earth` (damp grit), the sea got `water` (puddle film), palm fronds got `weed` (rain olive), thatch got `leaf` (ochre fallen leaf), walls and chairs got `wood` (peeling dark painted wood), the headland got `moss`, the solar panel got dark window glass, the tank got soot-black iron. Every object got a role, but several are a nearest match, not a true one.
- UVs: I gave box-projected UVs to the gable triangle only. Other custom meshes (palm trunks, fronds, roof sheets, canoe, headland) have none. I did not check whether their materials needed them.

## The look stage's dials (round-1 - dials.json): all defaults
width 540, height 960, samples 32, exposure 0.5, window light 1.0, lamp light 1.0, sky light 1.0, amber reflection 1.0, max glow lights 48, painterly 0.28, no rain, no --person-camera, haze on, own sky replaced.
Look stage reported: bounds x -51 to 48, y -16 to 96, z -3.2 to 12.4; 8 glowing patches found (2 lit windows, 2 dim, 3 lamp glass, 1 flame); 12 lights added; 0 scene lights to mute.

## Measures of round 1 (measure.py; saved in measures-round-1.json)
| Measure | Round 1 | Band | Verdict |
|---|---|---|---|
| Brightness | 0.31 | 0.14 to 0.35 | inside |
| Warm share | 61 % | 15 to 35 % | high |
| Cool share | 33 % | 30 to 60 % | inside |
| Warm light coverage | 15.0 % | 0.4 to 3.0 % | high |

measure.py's own advice: window light down or fewer lit windows; exposure down. I did not act on it (no fix pass).

## How long it took
Round 1 (540 x 960, 32 samples, Cycles, 2-processor machine): 219.7 s as the script measured it. Dressing about 1 s, building about 1 s. Whole first part about 15 minutes by the machine clock.
I also drew one throwaway check, `sketch.png` (270 x 480, 8 samples, default dials, 22 s), before round 1, only to see that the scene was not broken. I changed nothing in the scene after it. It is not a round.

## Packet
`/home/claude/blind-test/plugin-build/judge-1/` holds Judge this packet.md, The look.md, candidate.png (= round-1.png), measures.json, reference/ (five pictures). I did not judge it.

## What I tested
- Ran, in order: build_bach.py, apply_by_role.py (with --report), render_small.py (sketch and round 1), measure.py, judge.py. All finished without error. (My first attempt at timing round 1 with /usr/bin/time failed because that program is not installed; the render was redone with the shell's `time`.)
- Looked at both pictures once to check the scene was not broken. That is a check, not a judgment.

## What I did not test or do
- No blind judge, no fix pass, no round 2, no full-size picture.
- Did not run the plugin's test suite (tests/run_tests.sh).
- Did not try `--person-camera`, `--rain`, `--keep-world`, or a daylight picture. The plugin says it has no daylight variant; the request says only "modern day", so I used the blue hour the plugin provides.
- Did not check how any custom mesh looks close up.

## What I am unsure of (my own eye on round 1, not a verdict)
- The sand fills the lower third as a big pale, smooth, reflective surface with the fire's glow on it; it may read as a wet floor, not sand. The sea on the right is nearly invisible against the dark sky; I cannot make out the horizon.
- Warm share and warm light coverage are both far above the bands; the sand and the pale weatherboards pick up the amber and carry it.
- The fire (a cone of flame, nine faceted stones) looks like a toy and is the brightest thing in the frame.
- The wood role came out pale grey-tan on the walls, not dark peeling paint; the palm fronds are near-black flat silhouettes; the headland shows as a dark blob at right.
- Whether a blue-hour, amber-lit Samoan beach is what the owner meant by "modern day" is open; the plugin only makes a blue hour.
- Whether `rust sheet` for the roof and `sea water` for the sea were the best words to pick the nearest material, I cannot tell from one round.
- The scene bounds are large (lawn and headland widen them) and the look stage scales its sky lights from them; I do not know whether that hurt.

## Traps (operational)
- A name with `step`, `window` or `fire` anywhere in it takes that role before the role word you meant; read the dressing report, not the intention.
- The sea and the sky are both dark in this look; without a visible horizon the sea can vanish.
- Drawing while another builder is drawing makes the picture slower than 220 s.
- Correction: in the "By role" list, the `wall` count of 4 is the shore boulders, the reef, the fale foundation and the boulder-like stone objects; the headland is under `moss`.
