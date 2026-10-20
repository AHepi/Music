# What this does (plain words): the honesty checker re-uses the builder's near-copy test (the look checker's test, function checker_score in my copy of the builder's script) but with NEW random draws of pieces
# (seeds 21, 22, 23), on the new 4 x 4 area and on the round 1 area, to see that the claim "2 % and 0 % of pieces have a twin over 0.7 (round 1: 14 % and 18 %)" is not an accident of the two draws the builder used.
# Use: nice python3 -I twin_test_new_seeds.py
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_repeats_rerun as m
B = m.BASE
new = m.load_grey(os.path.join(B, 'area', 'area_4x4'), 'height')
old = m.load_grey(os.path.join(B, 'round1', 'area_4x4'), 'height')
out = {'what_this_is': 'Look checker twin test (200 x 380 dots pieces, all four ways round, 50 pieces) with new draws (seeds 21, 22, 23) on the round 2 and round 1 4 x 4 height areas.'}
for s in (21, 22, 23):
    out[f'round2_seed{s}'] = m.checker_score(new, 4, 50, s)
    out[f'round1_seed{s}'] = m.checker_score(old, 4, 50, s)
    print(s, out[f'round2_seed{s}'], out[f'round1_seed{s}'], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'twin_test_new_seeds.json'), 'w'), indent=1)
