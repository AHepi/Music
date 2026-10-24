### 7.2 What each layer buys (the ladder, **re-made after the look fixes**)

`ladder/ladder_table.md` (new table first, the old one under "before the look fixes"), sheet `ladder/ladder_sheet.jpg` (the same crop of every rung next to the reference; the old
sheet is `ladder/ladder_sheet_before_look_fixes.jpg`). 1254 dots, same seeds, **new default settings**. The rungs are baked by `tests/bake_tools.py` with the stack order and Amount changes in `ladder/ladder_views.json`.

| rung | what is in the picture | colour group (before) | of which: feature size (before) | height group (before) | overall, harness-style normal (before) | overall, strength-7 normal |
|---|---|---|---|---|---|---|
| 0 | layout and joints, every slate one flat colour | 0.410 (0.322) | 0.065 (0.065) | 0.441 (0.371) | 0.459 (0.402) | 0.442 |
| 1 | + colour and fade | 0.728 (0.480) | 0.798 (0.000) | 0.691 (0.598) | 0.735 (0.570) | 0.718 |
| 2 | + moss | 0.792 (0.636) | 0.902 (0.369) | 0.737 (0.632) | 0.774 (0.656) | 0.770 |
| 3 | + damage (the default tile) | 0.822 (0.701) | 0.899 (0.452) | 0.735 (0.654) | 0.789 (0.695) | 0.778 |
| - | the default WITHOUT outline and shadow | 0.676 (0.567) | 0.649 (0.489) | 0.403 (0.367) | 0.601 (0.539) | 0.588 |

"Overall, harness-style normal" is the older way of the ladder (`integration/score_set.py`: the normal made from the height by a two-neighbour slope with a fitted strength). "Overall, strength-7 normal" is the
way of the default tile's own score file; rung 3 gives the same 0.778 as `outputs/default/score_same_kind.json`. (Corrected: the first version said rung 3 showed "0.695 instead of the harness's 0.705"; it is the strength-7 normal
that gave 0.705, and the harness-style normal that gave 0.695.)

What each layer adds, step by step, and what taking the outline out costs (corrected: the first version said "the drawing layer is worth most" for both groups; for the colour group it is not):

| step | colour group | height group | overall (harness-style normal) |
|---|---|---|---|
| rung 0 to 1: + colour and fade | +0.318 | +0.250 | +0.276 |
| rung 1 to 2: + moss | +0.064 | +0.046 | +0.039 |
| rung 2 to 3: + damage | +0.030 | -0.002 | +0.015 |
| the finished tile minus the same tile without outline and shadow (a cost of REMOVING, a different question) | +0.146 | +0.332 | +0.188 |

So colour and fade adds the most to the colour group (+0.318, the part-built picture without it is flat slates), and the drawing layer (outline and shadow) is the one whose removal costs the most
of the HEIGHT group (0.332), and overall (0.188 against 0.276 for adding colour and fade: adding colour and fade is still the larger step). The rung 0 scores rose because the look fixes also changed the layout and the joints
(rounder corners, uneven lower edges, no black drips, a lighter two-step shadow).

![the ladder](ladder/ladder_sheet.jpg)

