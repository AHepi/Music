# What this does (plain words): writes transfer/deck_boards_score.json: the plain-words summary of the transfer test (what was changed, how long it took, the numbers), read from the
# bake and score files, so the guide quotes it. Plain Python (python3 -I).
import json, os
WOOD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
T = os.path.join(WOOD, 'transfer')
bake = json.load(open(os.path.join(T, 'deck_boards_seed1', 'bake.json')))
score = json.load(open(os.path.join(T, 'deck_boards_seed1', 'score.json')))
half_path = os.path.join(WOOD, 'scores', 'half_tile', 'deck_boards.json')
half = json.load(open(half_path)) if os.path.exists(half_path) else None
size = os.path.getsize(os.path.join(T, 'deck_boards_seed1.json'))
changed = ('the palette (16 silver-grey and warm-brown colours instead of the wood\'s), the board tone, the paint model numbers (zone colour mean and spread, strip colour spreads, strips 1.4 times longer for their thickness), '
           'the sampler options (6 planks, no knots, 8 % of the rust splatter, 35 % of the cracks, strip count x1.1, zone spread 0.9, strip spread 0.8, finer and weaker grain: 30 x 520 features, light gain 1.35), '
           'the gap lines (6 EQUAL planks with STRAIGHT 4.2-dot gaps instead of wavy ones), two short hand-written lists (6 butt joints as thin dark ribbons: 3 points each, and 176 small round blobs as nail heads and their highlights), and the pebbles layer was removed. '
           'No line of generator code was changed.')
detail = (f'Surface: sun-bleached silver deck boards (6 equal boards, narrow straight dark gaps, butt joints where two boards meet end to end at staggered places, rows of nail heads, a few long straight cracks, a little rust, no knots). '
          f'Made by `transfer/make_deck_boards.py` (about 70 lines; written in one sitting, about 10 minutes of work including looking at the first picture) which calls the SAME sampler and generator and changes only the description: {changed} '
          f'The description is {size} bytes. One bake at 1254 dots took {bake["total_s"]} seconds (colour render {bake["colour_render_s"]} s; {bake["shapes"]} shapes). The first picture was used as it came out (no second iteration). '
          f'There is no deck-boards reference, so the only checks are by eye and by the seamless test' + (f': half-tile shift test mean difference {half["half_tile_roll"]["mean_difference_levels"]} steps, {half["half_tile_roll"]["share_over_40_levels"] * 100:.2f} % of dots over 40 (wrong-roll control {half["wrong_roll_control"]["share_over_40_levels"] * 100:.1f} %)' if half else '') +
          f'. (Scored against the WOOD reference it gets the same-kind score {score["texture_compare_overall"]} and a colour difference of {score["colour_mean_delta_e"]}, which only confirms that it is a different surface.) '
          'What I had to change was numbers and two lists; what I did NOT have to change was code. What did not transfer by numbers alone: butt joints and nails (straight vertical ribbons and round blobs) had to be written by hand as lists; a generator option for "joints and nails along rows" would make them numbers too.')
summary = (f'sun-bleached silver deck boards made by changing only the description (palette, paint numbers, straight equal gaps, two short hand-written lists for butt joints and nails); no generator code changed; about 10 minutes of work; bake {bake["total_s"]} s at 1254 dots.')
json.dump({'summary': summary, 'detail': detail, 'bake_seconds': bake['total_s'], 'description_bytes': size, 'texture_compare_vs_wood': score['texture_compare_overall'], 'half_tile': half}, open(os.path.join(T, 'deck_boards_score.json'), 'w'), indent=1)
print(summary)
