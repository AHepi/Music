# What was deleted after the restart, and why (second integrator, 20 October)

The folder was 436 MB, over the brief's limit of 400 MB, before the last bakes. These pictures were deleted; every one was an in-between picture
whose numbers are kept (in a .json next to where it was, or in `measured_before_clean_up.json` in this folder). Nothing the guides show was deleted.

| what | size | why it could go |
|---|---|---|
| `integration/bake_round1/*.png` | 20 MB | the first whole-stack bake before tuning; its scores stay in `score.json`. `score_colour.sh` used its height and normal only to let the scorer run; it now borrows them from `outputs/default` (the colour group does not depend on them). |
| `outputs/moss_default/*.png` | 13 MB | the moss builder's bake of the whole stack at the moss builder's own settings, before integration; superseded by `outputs/default`. |
| `tests/colour_and_fade/full_stack_1254/*.png` | 16 MB | the colour builder's bake of the part-built stack (moss and outline still empty); its scores stay in its `score.json`. |
| `integration/looks/r11/*.png`, `integration/looks/r13h/*.png` | 17 MB | tuning-round pictures; their scores and differences were measured first and are in `measured_before_clean_up.json`. |
| `damage_work/previews/*.png` | 17 MB | the damage builder's quick looks while building the layer. |
| `integration/sbs_*.png`, `tests/comparison/two_by_two.png` | 20 MB | kept, but as JPEG pictures (`.jpg`, quality 88): they are for looking at, not for measuring. |
| `resolution/whole_recipe/at_1254/*.png` | 7 MB | identical, dot for dot, to `outputs/default` (checked: largest difference 0 in colour, height and roughness, so baking twice gives the same picture); replaced by links to those files |
| `links_and_order/tone_blend_*_height.png`, `links_and_order/link_height/*.png` | 8 MB | after the sheet `tone_blend_sheet.jpg` and the numbers `link_height/link_measures.json` were made from them |
| `outputs/default/sheet_same_kind.png` and five big "look" sheets of the outline and damage builders in `tests/` | 22 MB | kept as JPEG (quality 90): they are for looking at |
| `controls_sweeps/whole_recipe/tiles/` | 16 MB | the single pictures of the whole-recipe strips, deleted by `make_strips.py` after it joined them into the strips |
| `area/area_*/new_area_against_copied_tile.png` | 9 MB | kept as JPEG (for looking at) |
| `debug_views/colour_and_fade/*_768.png` | 5 MB | the colour builder's single debug pictures at its own starting settings; its sheet `colour_and_fade_debug_views.png` stays, and `debug_views/` holds the same views at the tuned settings |
