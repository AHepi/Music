# What this does (plain words): scores all the finished default tiles of round 2 with the project's "same kind of surface" tool (lib/texture_compare.py, through
# tools/score_set.py) and with the dot-for-dot tool (lib/pixel_compare.py, for transparency only), and writes scores/final_scores_round2.json:
#   MAIN seeds 1-3 (colour map + height map), COMPARISON seeds 1-3 (colour made from the height), the earlier pure-node wood recipe's best new tile (seed 105, baked once
#   from its own description for round 1), and the round 1 numbers of this recipe for before / after.
# The COMPARISON folders only hold a colour picture (the height and normal are the same as MAIN's, so they are not stored twice to save disk space); this script makes a
# scratch folder of links (colour from the COMPARISON folder, height and normal from the MAIN folder of the same seed) and scores that.
# Two things the honesty checker asked to be said next to the numbers (they are also in the JSON):
#   * the new tile is built from the reference's own dots, so a high same-kind score is partly expected; the earlier recipe used nodes only, so the comparison is not like for like;
#   * "height_mae_best_fit_levels" collapses to a flat grey for every arrangement that is not in the reference's places (fit gain about 0), so it is the same number for
#     all pictures and says nothing; the plain height error "height_mae_levels" is the one to read.
# Use: python3 -I tools/score_all_round2.py
import json
import os
import tempfile
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import score_set  # noqa: E402


def main():
    out = {'what_this_is': 'Same-kind scores (0 = as different as another real surface, 1 = indistinguishable by those measures) of the round 2 default tiles against the uploaded wood, by lib/texture_compare.py, and the dot-for-dot numbers of lib/pixel_compare.py (for transparency only: the new boards are not where the reference boards are, so those numbers are low on purpose and say nothing about quality).',
           'caution_1': 'The new tile is made from the reference picture itself (its own dots, rearranged), the earlier recipe used nodes only: a higher score is partly expected and the comparison is not like for like.',
           'caution_2': 'height_mae_best_fit_levels is the error after the best brightness and contrast fit; for any picture whose boards are not in the reference places the fit collapses to a flat grey (gain about 0), so that number is the same for every picture and says nothing. Read height_mae_levels.'}
    scratch = tempfile.mkdtemp(prefix='wood_comparison_')
    for sd in (1, 2, 3):
        main_folder = os.path.join(BASE, 'outputs', f'main_seed{sd}')
        cmp_folder = os.path.join(BASE, 'outputs', f'comparison_seed{sd}')
        link_folder = os.path.join(scratch, f'comparison_seed{sd}')
        os.makedirs(link_folder, exist_ok=True)
        os.symlink(os.path.join(cmp_folder, 'colour.png'), os.path.join(link_folder, 'colour.png'))
        for name in ('height.png', 'normal.png'):
            os.symlink(os.path.join(main_folder, name), os.path.join(link_folder, name))
    jobs = [(f'main_seed{s}', f'outputs/main_seed{s}') for s in (1, 2, 3)] + [(f'comparison_seed{s}', os.path.join(scratch, f'comparison_seed{s}')) for s in (1, 2, 3)] + \
           [('earlier_wood_best_new_tile_seed105', 'tests/earlier_wood_seed105')]
    for key, folder in jobs:
        path = folder if os.path.isabs(folder) else os.path.join(BASE, folder)
        if not os.path.exists(os.path.join(path, 'colour.png')):
            print('missing', folder)
            continue
        res = score_set.score(path, pixel=True)
        res['folder'] = f'outputs/{key}' if key.startswith('comparison') else folder
        out[key] = res
        print(key, res['overall'], res['groups'], flush=True)
    r1 = os.path.join(BASE, 'scores', 'final_scores_round1.json')
    if os.path.exists(r1):
        with open(r1) as handle:
            old = json.load(handle)
        out['round1_for_before_and_after'] = {k: {'overall': v['overall'], 'groups': v['groups']} for k, v in old.items() if isinstance(v, dict) and 'overall' in v}
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'final_scores_round2.json'), 'w') as handle:
        json.dump(out, handle, indent=1)


if __name__ == '__main__':
    main()
