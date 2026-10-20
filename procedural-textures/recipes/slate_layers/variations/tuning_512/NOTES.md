# What this folder is (20 October, after the look fixes)

Small test bakes (512 dots, colour only, each about 25 seconds) that I looked at before changing the four variations v2, v4, v5 and v6 on top of the NEW default tile.
The look checker's advice for the variations (problem 10 in `verify_look/LOOK_VERDICT.md`) was tried first (the candidates called `..._a_checker_advice`), then a few of my own.
`views_round_1.json` (12 candidates) and `views_round_2.json` (5 candidates) are the settings of each candidate (on top of `recipe/settings.json`); `bake_round_1.log` and `bake_round_2.log` are the Blender logs.
The pictures are JPEG copies (`..._colour.jpg`); `sheet_*.jpg` put four candidates and the new default side by side (made by `make_look_sheet.py`).
What was chosen, and why, is written in section 7.3 of `05 Recipe - slate in layers - how it is made.md`: v6 = `v6_b_less_dark_bigger_damp`, v5 = `v5_d_less_tint`, v4 = `v4_f_big_pale_areas_less_blue`, v2 = `v2_b_much_more_softer`.
Chosen by eye only (no score was used to choose); the chosen four were then baked at 1254 dots into `variations/`.
