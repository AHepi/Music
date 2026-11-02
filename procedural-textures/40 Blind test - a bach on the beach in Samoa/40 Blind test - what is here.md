# 40 Blind test: a bach on the beach in Samoa

What this file is: the record of the first blind test of the new plugin `painted-place` (2 November 2026, evening), the test the old plugin failed at 2.7 against 6.3 (logs 32 to 34). The owner's words for the place: "I batch on the beach in Samoa. Modern day." Read as "A bach on the beach in Samoa. Modern day." (a bach: a small, simple holiday house by the sea); the owner was told this reading and did not correct it.

## The answer in one paragraph

The plugin carried the look and did not sink the builder. All six blind judges chose the plugin's picture for the film ("it already belongs with the reference pictures"); on the look lens it scored 5.0 against 1.7 for the same model with Blender alone. It lost on the other two lenses (photograph 2.3 against 4.2, request 5.0 against 7.2): its shapes are weaker (toy props along the bottom edge, a sea you cannot see, fewer signs of Samoa today) after about an hour of building against the control's hour and thirty-five minutes. Overall the two are level (4.1 against 4.3). The old plugin's picture was chosen by nobody and sat four points below the unaided build; this one is chosen by everybody and sits level. The look transferred; the shapes are still the builder's own, which is what the plugin was built to leave alone.

## How the test was run

- Two builders, both Sonnet at high effort, started at the same time (16:11), both isolated (no other files, no internet, no rented cards, no image generation), both with the same words. Blender was the `bpy` module on this 2-processor machine; small pictures took 3 to 5 minutes while both drew at once.
- **The plugin builder** got the plugin folder and the words, nothing else. It built, dressed, lit and drew round 1 (15 minutes), made the judging packet and stopped. A fresh blind judge (Opus) answered the packet: verdict **no**, seven fixes. The builder was handed the verdict and did the one fix pass: round 2 (45 minutes). A second fresh blind judge: verdict **nearly**, six fixes, "the colours, the framing and the finish already match the references". The loop ended there, as the skill says. Round 2 was then drawn once at full size with the same dials (1080 x 1920, 64 samples, 17 minutes) for the judging.
- **The control builder** got the words and Blender alone, about two hours. It built, drew eleven test pictures and three review pictures, and one full-size final (1080 x 1920, 96 samples, 31 minutes). Work time about 1 hour 35 minutes.
- **Judging:** three fresh judges (Opus) got a folder with the two full-size pictures under shuffled letters, the five reference pictures, The look.md and a question sheet (0 to 10 on three lenses: could it be a photograph; does it deliver the request; could it be a film backdrop in the look), then a choice and one fix each. A third picture C was added afterwards (the control's own scene with the look stage dropped on it, see below) and three more fresh judges scored all three; the first three could not be asked again.

## The pictures

| Where | What |
|---|---|
| `plugin build/round-1.jpg` | The plugin's first picture, all dials at their defaults |
| `plugin build/round-2.jpg`, `round-2 full size 1080x1920.jpg` | After the one fix pass; the full-size one is what the judges saw as B |
| `plugin build/rounds 1 and 2 side by side.jpg` | The two together |
| `control build/final 1080x1920.jpg` | The control's final picture, what the judges saw as A |
| `control build/review picture v3 540x960.jpg` | Its last review picture before the final |
| `control scene with the look stage/defaults.jpg`, `one dial pass.jpg`, `second dial pass.jpg` | The control's scene with the look stage: defaults; a dial pass from the measures that overshot; a second that the judges saw as C |
| `judging/A, B and C side by side (...).jpg` | The three as the judges saw them, side by side |

## Scores

| Picture | Photograph | Request | Film backdrop in the look | Mean | Chosen for the film |
|---|---|---|---|---|---|
| A, the control (Blender alone), six judges | 4.2 | 7.2 | 1.7 | 4.3 | 0 of 6 |
| B, the plugin, six judges | 2.3 | 5.0 | 5.0 | 4.1 | 6 of 6 |
| C, the control scene with the look stage, three judges | 3.3 | 6.3 | 3.0 | 4.2 | 0 of 3 |

The judges' words, unedited: `judging/Judges round 1 - A and B.md` and `judging/Judges round 2 - A, B and C.md`. Every judge's fix for A was the same: turn the day into an evening lit from the house. Every judge's fix for B was the same: the toy fire and the foreground objects.

## What the test says

1. **The look transfers through the plugin.** A fresh builder with the plugin and six words made a picture six judges would put beside the references; the same model unaided made a bright pastel afternoon none would. The look stage, the materials by role and the judge-then-fix loop did that without naming any technique to the builder.
2. **The judge is the lesson carrier, and it works.** Round 1 to round 2 went from "no" to "nearly" on one pass. The judge's fixes were plain, pointed at places in the frame, and the builder could act on all but two (haze strength, and a fire brighter than the lamps: both now dials, see below).
3. **The look stage alone is not the plugin.** Dropped on the control's scene (C), it moved the look score from 1.7 to 3.0 and the judges still saw "orange glow from nowhere" and dark windows: that scene's windows do not glow, so the stage found only the string lights, and the warm off-frame light did the rest. The dressing and the judge are what carried B to 5.0.
4. **Shapes are still the weak half.** The plugin's picture lost on photograph and request. Its foreground props were toys (a ring, a starburst of rods, a crystal fire), its sea invisible, its modern cues few. The plugin does not build shapes and should not; but the judge could ask for them earlier (the request lens is not in the judge's rubric: it judges the look only).
5. **The measures are a coarse net.** Twice a judge said brightness "passes only because the dark sky balances the bright sand". A per-third measure (top, middle, bottom) would catch that.

## Plugin faults found and fixed during the test (painted-place 0.1.1)

- The judging rubric named `candidate.jpg` while the packet held a `.png`: the packet now always writes `candidate.jpg`.
- The reference picture of the coal mine carries balloon-shaped smoke, which the look page forbids: the page now says it is a reference for light, colour and air only.
- No haze dial: `--haze` added (thickness of the haze).
- One strength for every lamp and flame: fires, flames, embers and braziers now get their own low, wide light and their own dial, `--fire-light`.
- (Not fixed) the judge's rubric does not ask whether the request is delivered; the measures cannot see a bright bottom third under a dark sky; role words have traps (`step`, `window`, `fire` inside other names) that the builder had to read the code to avoid.

## Not done

- One place, one request, one builder model. No second request yet (an interior, a daylight place).
- The plugin's round-2 fixes that the builder could not make (haze, fire) were not re-drawn after the dials were added.
- No full-size picture of C; no judging of the plugin's round 1 beside the others.
- The old test's judges, lenses and places differ from this one's, so the 2.7-against-6.3 and 4.1-against-4.3 numbers are not the same scale; the pattern (chosen by nobody, then by everybody) is the comparison.

## Traps

- A judge who is told the scores of an earlier round, or the builder's report, is no longer blind. Every judge here saw only the folder.
- A builder handed its own verdict ("judge it yourself") is grading its own work; the plugin's loop needs a separate judge, and this harness lets the builder pause and resume for that.
- The control's two hours against the plugin builder's one hour is not equal time; the next test should give both the same clock.
- The request lens is judged by people who know the place only from six words; "Samoa today" meant surfboards and solar panels to the judges, and a fale to one of them.
