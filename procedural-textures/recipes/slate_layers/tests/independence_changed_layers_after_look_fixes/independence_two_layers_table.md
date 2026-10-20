# Independence re-test of the two layers whose files changed in the look fixes (MOSS and OUTLINE AND SHADOW), 512 dots, 20 October, after the look fixes

What this is (plain words): the same test as `tests/independence_full/independence_table.md`, but only for the two layers whose code changed in the look fixes
(`layers/moss.py` and `layers/outline_and_shadow.py` got six new controls). Each layer was switched off (Amount 0) and given a new seed (Seed + 1) in the whole
recipe with the NEW default settings, and every dot was compared with the unchanged recipe. A layer is independent when nothing changes OUTSIDE its own region
(every "outside" number must be 0.0). Baked at 512 dots by `look_fixes/independence_two_layers_bake.py` and counted by `look_fixes/independence_two_layers_analysis.py`
(both written by the tuner and run again unchanged by me, at 512 dots; the tuner's own run at 384 dots is in `look_fixes/round2/independence/`). The baked pictures were deleted
afterwards to save disk (about 10 MB); this table and the .json beside it are what is kept. The independence of colour and fade, damage and layout was NOT re-run (their files did not change).
Result: all outside numbers are 0.0, so both changed layers are still independent.

| layer changed | variant | own region share % | colour changed % | colour changed outside own region % | height changed % | height changed outside own region % | roughness changed % | roughness changed outside own region % |
|---|---|---|---|---|---|---|---|---|
| moss | Amount 0 | 17.66 | 16.536 | 0.0 | 17.271 | 0.0 | 17.174 | 0.0 |
| moss | Seed + 1 | 36.26 | 33.79 | 0.0 | 35.514 | 0.0 | 31.758 | 0.0 |
| outline_and_shadow | Amount 0 | 38.43 | 37.428 | 0.0 | 38.023 | 0.0 | 34.786 | 0.0 |
| outline_and_shadow | Seed + 1 | 40.76 | 30.731 | 0.0 | 39.346 | 0.0 | 11.509 | 0.0 |

Which other layers' own patterns (masks) changed (share of all dots; 'outside' = outside the changed layer's own region):

| layer changed | variant | slates (piece_id) | colour_and_fade mask | damage mask | moss mask | outline_and_shadow mask |
|---|---|---|---|---|---|---|
| moss | Amount 0 | 0.0 | 0.0 (outside 0.0) | 0.0 (outside 0.0) | (itself) 17.659 | 0.0 (outside 0.0) |
| moss | Seed + 1 | 0.0 | 0.0 (outside 0.0) | 0.0 (outside 0.0) | (itself) 35.797 | 0.0 (outside 0.0) |
| outline_and_shadow | Amount 0 | 0.0 | 0.0 (outside 0.0) | 0.0 (outside 0.0) | 0.0 (outside 0.0) | (itself) 38.408 |
| outline_and_shadow | Seed + 1 | 0.0 | 0.0 (outside 0.0) | 0.0 (outside 0.0) | 0.0 (outside 0.0) | (itself) 33.531 |
