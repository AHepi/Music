## 6. THE LIGHTING TEST SET (every later helper must draw this, and pass it)

**Why it exists.** "The geometry should still be visible under all conditions" is only true if somebody looks under all conditions. Today a helper tunes the road in the dusk lamps, sees good joints, and the first brazier glare or heavy rain ruins them. This set is a fixed list of pictures, a command that draws them, and a number that says PASS or FAIL.

**Example first.** Run the quick set on the road as it is today: [[QUICK_BASE_RESULT]] Run it on the road with the joint picture: [[QUICK_MILD1_RESULT]] That is the whole use.

### 6.1 The five lightings (letters A to E), how each is made, and how to switch

Every lighting is made by `set_lighting(letter)` in `tools/b02_lighting_and_variants.py` (a function inside Blender; it puts everything back first, so lightings never pile up). The suns and lights used are listed here so that anybody can rebuild them.

| letter | name | what it is | dry road brightness, main camera | why it is in the set |
|---|---|---|---|---|
| **A** | dusk lamps | the street exactly as the film lights it: five gas lamps (260 W each), the lit windows (45 W each), the two dim sky suns (0.3 and 0.2) | [[A_dry_main]] | the film's own light: the plate lighting |
| **B** | brazier glare | the lockout shot file as the film lights it, with the brazier's light (900 W, orange) and its glare on the wet road. It is the same as A in the lockout file; B only names the picture | [[B_dry_lockout]] (lockout camera) | the lockout plate: the glare is the worst case in the real film |
| **C** | low side light | all lamps off (the two sky suns stay); one low sun, 10 degrees above the horizon, from the right of the street and slightly from the camera side (strength 1.0, warm). **The houses' shadows are switched off for this one** (otherwise the houses block the low sun and the road is simply dark), so C is an artificial test of how the relief looks under raking light, not a picture of a real evening | [[C_dry_main]] | a light that comes from the side, so the relief picture has its best chance. If the joints do not show here, they do not show |
| **D** | flat overhead light | all lamps off; one sun almost straight up (88 degrees, strength 0.4, slightly warm) | [[D_dry_main]] | the opposite: almost no side light, so a relief picture has nothing to work with and only the joints' own darkness counts |
| **E** | light from behind into the glare | A as it is, plus one strong low light (30,000 W, orange, 0.35 m across) at the far end of the street (x 0, y 66, z 5.9, which is 1.2 m above the road there), shining toward the camera | [[E_dry_main]] | a bright source low in front of the camera: every shiny surface reflects it. The worst case for "light washes out the joints" |

The sun strengths of C and D were chosen so that the DRY road is about as bright as in A (0.12 to 0.16, `work/cal`), so that a change in how well the joints show comes from the kind of light, not from how much. The first try of the back light (E) stood at z = 1.8, under the road (the street climbs 4 degrees), and did nothing; the first try of C was six times too strong. Both are recorded in section 9.

### 6.2 Cameras, sizes, states

| camera | file | size | samples | what it shows |
|---|---|---|---|---|
| **main** | the street copy `set_copy/street.blend` | 540 x 960 | 16 | the film's street camera |
| **lockout** | the film's lockout shot file (opened read-only, never saved), the lockout plate camera | 540 x 960 | 16 | the plate of the lockout shot, with the props |
| **close** | `set_copy/street.blend` | 640 x 480 | 24 | a low view down the road from (0.5, 6.0, 1.0): more joint dots |

States: **dry** (Wetness 0, Puddles 0), **wet** (0.85 / 0.5), **heavy** (1.0 / 0.8). Plate settings are the round 2 ones (EEVEE, ray tracing on, shadow rays 4, steps 16).

**The two sets** (`tools/b09_lighting_test_set.py`, `FULL` and `QUICK`):
* **quick, 9 pictures, about 20 minutes:** main A wet, A heavy, C wet, D wet, E wet; close A wet, E wet; lockout B wet, E wet. These are the conditions the baseline fails most.
* **full, 22 pictures, about 40 minutes:** main A dry / wet / heavy, C dry / wet, D dry / wet, E dry / wet / heavy; close A dry / wet / heavy, C wet, D wet, E wet; lockout B dry / wet / heavy, C wet, D wet, E wet.

**The command** (one, from any folder; it never saves a Blender file and never touches the film project):

```
bash tools/run_lighting_test_set.sh quick OUT_FOLDER
bash tools/run_lighting_test_set.sh full  OUT_FOLDER --variant NAME --args '{"...": ...}'
bash tools/run_lighting_test_set.sh quick OUT_FOLDER --after-apply my_solution.py
```
`--variant` names a change of the road material in `tools/b02_lighting_and_variants.py` (the study's solutions are there: `joint_picture`, `geometry`, `combo`); `--after-apply` is a Python file that is run once inside Blender after the wetness layer is on, for a new solution of your own. It stops if the free disk space is below 1.25 GB, skips pictures already drawn, and prints the PASS / FAIL table (`report.txt`). The measuring is `tools/b04_measure_joints.py`; the masks are drawn by the same run.

### 6.3 The pass line ("visible under all conditions", in numbers)

For every picture of the set, in the **near** and **middle** bands of the road (section 2 defines contrast, delta and seen):

| camera | band | contrast at least | delta at least | seen at least |
|---|---|---|---|---|
| main | near | 0.18 | 0.020 | 0.65 |
| main | middle | 0.12 | 0.015 | 0.30 |
| lockout | near | 0.15 | 0.020 | 0.50 |
| lockout | middle | 0.07 | 0.015 | 0.12 |
| close | near | 0.25 | 0.030 | 0.70 |
| close | middle | 0.20 | 0.025 | 0.60 |

and the other fault: **contrast at most 0.75 (main, lockout) or 0.80 (close)**, so that the cure is not a harsh black grid.

**How I chose it (by looking, then writing the numbers down).** I looked at today's DRY road in the film's own lights (A and D, the lockout B) and at the close view: those pictures show the setts clearly, and the person's own verdict on the street so far was that it "works really well". So the line is set just under what today's dry road has in every one of those pictures: they all pass it (section 6.4, baseline table: six of six). Then I looked at every wet and heavy picture of round 2: the joints are gone, and every one of them fails by a wide margin (near contrast 0.01 to 0.12; "seen" 9 to 41 %). The upper limit comes from the first try of the cure, which made the joints black and ragged (contrast 0.85 to 0.96, section 5): 0.75 is just under the strongest look I would keep. The delta column is there because the stage's brightness curve crushes dark values (painter test): a contrast on a very dark road means nothing if the brightness difference is under about 0.02.

*The line is a first line.* It was chosen by one person (me) looking at about 60 pictures; the person who owns the film should look at `pictures/solution_main_all_lights.jpg` and say if it is too lenient or too strict. If a later helper finds a picture that fails the line but looks fine, or passes and looks wrong, the line is what to change, not the picture.

### 6.4 What the set says: the road as it is today, and the road with the joint picture

**How to read the reports below.** `pud` is the share of the road that was left out because it lies under a puddle (the puddle plus a 2-dot margin; it is calibrated for the main camera, so it is a little higher than the shares in section 3b); `near` and `middle` give contrast, delta and seen; the last column is the output of `report` (PASS, or FAIL with the first three reasons). The nine pictures of the quick set are among the 22.

**The road as it is today (round 2), the full set** (`work/r01/measurements_nopuddle.json`, the pictures of `work/r01`):

[[REPORT_BASELINE]]

**The road with the joint picture "mild1"** (colour x0.85 in the joints, roughness 0.9, specular x0.65, coat x0.55, the "closed" joint picture; section 5), the full set (`work/r07`):

[[REPORT_MILD1]]

**What fails, and why I think so.** Two pictures, both in the lockout shot's middle band: *B wet* (middle contrast 0.04 against the line's 0.07) and *B heavy* (middle contrast -0.09: there the joints are LIGHTER than the stones). The lockout camera's middle band (rows 712 to 836 of the 960) is the part of the road behind the sacks and beside the drum: the sacks' big shadow, the brazier's glare and, in heavy rain, 58 % puddle (42 % of the whole lockout road at the heavy dial) fill it, and what is left are few joint dots next to a mirror-like puddle that reflects dark houses, so a dull joint can come out lighter than a stone that mirrors something dark. By eye the joints in that band of the wet picture are visible where the road is lit (`pictures/solution_lockout_all_lights.jpg`), so I do not think the picture is wrong; I think the band is badly placed for this shot and the line is too strict for it. **I left the line as it is, and the two failures stand as an open item** (a later helper can move the lockout bands to the unoccluded road, or draw a plate without the sacks' shadow, and re-run). The near band, where the plate's foreground road is, passes in all six lockout pictures (0.18 to 0.40).

**The self-test of the one command** (`bash tools/run_lighting_test_set.sh quick work/r13 --variant joint_picture --args '{"colour_mult":0.85,"rough_to":0.9,"spec_keep":0.65,"coat_keep":0.55,"picture":"joint_cavity_closed.png"}'`, exactly as a later helper would type it). It took 1,119 seconds (18.7 minutes) and printed:

[[REPORT_QUICK_SELFTEST]]

Its numbers agree with the full set's for the same pictures to within 0.009 in contrast (the pictures were drawn a second time, independently): so the measure is repeatable at the 0.01 level, and a change of 0.03 or more in a later helper's report is a real change.
