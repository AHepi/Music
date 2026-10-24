### 7.3 Seeds and settings variations (**re-made on the new default**)

Eight tiles from eight settings variations, 1254 dots each, on top of the NEW default, contact sheet with each tile's settings written under it and its old score in brackets:
`variations/contact_sheet.png` (the old sheet is `variations/contact_sheet_before_look_fixes.jpg`; settings in `variations/variations.json`, where the entry "before the look fixes" keeps the old settings and scores;
`variations/variations_before_look_fixes.json` and `same_kind_colour_scores_before_look_fixes.json` are plain copies of the old files). Colour group of each against the reference:

| variation | what changed | colour group now | before |
|---|---|---|---|
| v1 new seeds | five new seeds, same settings (unchanged) | 0.811 | 0.765 |
| v2 more moss | **new settings**: moss coverage 0.62 (default 0.30), patchiness 0.5, lichen 0.3, softer rim (`rim_opacity` 0.7): a damp roof with moss on nearly every slate | 0.700 | 0.760 |
| v3 heavily damaged | unchanged settings: deep flakes on every lower edge, cracks, scratches, pits, bites, broken corners | 0.761 | 0.733 |
| v4 faded and sun-bleached | **new settings**: long fade, bigger and stronger bleached areas (`bleach_amount` 1.0, `bleach_cover` 0.55, `patch_size` 0.6), no damp stain, lighter (`tone_centre` 4.6) and greyer (`tint_amount` 0.5) slates, little moss | 0.694 | 0.554 |
| v5 fresh and clean | **new settings**: even tone (`tone_spread` 0.3, no outlier slates, less tint), slight paint streaks kept (`fade_amount` 0.6, `streak_contrast` 0.9), almost no damage, no moss | 0.534 | 0.463 |
| v6 dark and wet | **new settings**: darker slates (`tone_centre` 3.0), damp patches that stay lighter than the joints (`stain_amount` 0.6, `stain_cover` 0.4, `patch_size` 0.3), rougher, some moss | 0.693 | 0.550 |
| v7 pale and old | unchanged settings: pale warm-grey slates, flaked edges, lots of lichen | 0.591 | 0.544 |
| v8 big slates | unchanged settings: 6 rows of 4 slates instead of 8 of 6 | 0.732 | 0.746 |

![eight variations](variations/contact_sheet.png)

**How the four new variations were made (the look checker's advice, problem 10 of `verify_look/LOOK_VERDICT.md`, tried first and kept where it helped by eye).** I baked small colour-only tests at 512 dots (17 candidates, in
two rounds, `variations/tuning_512/`, sheets `sheet_*_round_*.jpg`; the advice and my other tries are in `views_round_1.json` and `views_round_2.json`), looked at them next to the new default, chose, and then baked the eight at 1254.
* **v6 dark and wet.** The checker's advice (stain 0.5, cover 0.3, tone centre 2.8) removed the burnt look, but a version with a slightly lighter tone centre 3.0 and bigger, gentler damp patches read best: every slate outline still reads and the joints stay darker than the damp patches. (v6 is one of the darkest tiles.)
* **v5 fresh and clean.** The advice (fade 0.5, streak contrast 0.8) kept some paint streaks. The brown-grey odd slates of the first try came from the default's stronger tint, so tint and outliers were turned down; the result is even but not flat vector fills.
* **v4 sun-bleached.** The advice (bleach patch size 0.35, stronger bleach) still read only as a lighter tile. Much bigger pale areas (patch size 0.6) with greyer, warmer slates read better. It is the weakest of the four: at thumbnail size it still reads mostly as a lighter roof.
* **v2 more moss.** The advice ("distinct once the default moss is reduced") was true only in part: the new default has moss coverage 0.30 and the old v2 only 0.34, so v2 needed coverage 0.5 to 0.62 to be told apart. 0.62 with softer rims was chosen; 0.5 was a middle step; 0.62 everywhere with see-through cores looked like green carpet.

The low scores of v4, v5, v6 and v7 are expected: they are meant to be DIFFERENT roofs from the reference. The colour scores moved with the settings AND with the new default, so a before/after comparison of one variation mixes both.

**Seed spread (re-made).** The default settings with five different sets of seeds (the default tile, v1, and three more baked now: `variations/seed_spread/seed_spread.json`, small pictures `seeds_b/c/d_colour_small.jpg`,
the old ones kept as `..._before_look_fixes`):

| | default seeds | v1 | seeds b | seeds c | seeds d | mean | spread (highest minus lowest) |
|---|---|---|---|---|---|---|---|
| colour group now | 0.822 | 0.811 | 0.824 | 0.802 | 0.792 | **0.810** | 0.032 |
| colour group before the look fixes | 0.701 | 0.765 | 0.769 | 0.753 | 0.710 | 0.740 | 0.068 |
| feature size now / before | 0.899 / 0.452 | 0.961 / 0.878 | 0.940 / 0.845 | 0.913 / 0.850 | 0.927 / 0.854 | | |

So the default seeds are no longer the unlucky draw (they are the second highest of five), and four of the five sets are at or above the brief's 0.8. The gain shows on every set, mostly as a gain of the feature-size measure (the cliff of section 7.1).
Corrected statement about noise: the 0.032 / 0.068 spread is how much the score differs between DIFFERENT seed sets; it is not the noise of a same-seed comparison, which is smaller. A fair rule is: do not adopt a setting because of a gain
on one seed set, and bake it on at least three.

