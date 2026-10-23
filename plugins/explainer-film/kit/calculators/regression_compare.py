"""What this does: says whether a change to shared code (the stage, a scene kit, a tool) really changed the pictures, or
whether the difference is only the ordinary variation you get when the SAME code draws the same moment twice.

Why: one comparison is not a proof. In the project, eight comparison pictures matched dot for dot after a change, but the
ninth (the house sample at 20 s) differed by 7.7 percent of its dots (at most 7 levels of 255). Drawn ten times, the
unchanged old stage gave both results by itself, so the change had not caused it (measured, story logs 37 to 39). So:
draw each moment at least 3 times with the old code and 3 times with the new, and compare the old draws with each other
FIRST (the control), then old against new.

Use:
    python3 regression_compare.py --old OLD_FOLDER --new NEW_FOLDER
Each folder holds the draws of one version, named NAME-1.png, NAME-2.png, NAME-3.png ... (NAME is the moment, for
example house-sample-20s; .jpg and .webp are read too). Both folders must hold the same NAMEs, and at least 3 draws of
each NAME; the tool refuses fewer (exit 2).

What it prints, for each NAME:
  1. old against old: every pair of old draws, and the largest share of dots that changed between them (the spread);
  2. old against new: each new draw against the old draw nearest to it;
  3. the verdict: "real" only when EVERY new draw differs from its nearest old draw by more than the old-against-old
     spread; otherwise "within ordinary variation".
It always says how many pictures (NAMEs) and how many draws it compared.
A dot counts as changed when one of its colours differs by more than --dot-levels (default 0: any difference).
Exit: 0 when everything is within ordinary variation, 1 when a real difference was found, 2 when it refused.
Options: --names NAME ... (only these), --dot-levels N, --out FILE (the result as JSON), --json (print JSON).

"Real" with 3 draws can still be a rare outcome of the old code that none of the 3 old draws happened to show; when
the verdict matters, draw more of the old version (the house sample needed 10 to show both outcomes).
"""
import argparse
import itertools
import json
import os
import re
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from calculator_output import InputProblem, run_main  # noqa: E402

DRAWS_NEEDED = 3
PICTURE_NAME = re.compile(r'^(?P<name>.+)-(?P<draw>\d+)\.(?:png|jpg|jpeg|webp)$', re.IGNORECASE)


def find_draws(folder):
    """{NAME: {draw number: path}} for every NAME-K picture in a folder."""
    if not os.path.isdir(folder):
        raise InputProblem(f'{folder} is not a folder (it should hold NAME-1.png, NAME-2.png, NAME-3.png ...).')
    draws = {}
    for file_name in sorted(os.listdir(folder)):
        found = PICTURE_NAME.match(file_name)
        if found:
            draws.setdefault(found.group('name'), {})[int(found.group('draw'))] = os.path.join(folder, file_name)
    return draws


def read_picture(path):
    picture = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if picture is None:
        raise InputProblem(f'{path} cannot be read as a picture.')
    if picture.ndim == 2:
        picture = picture[:, :, None]
    return picture.astype(np.int32)


def difference(first, second, dot_levels):
    """Share of dots changed (one colour more than dot_levels apart), the largest difference and the mean difference."""
    if first.shape != second.shape:
        raise InputProblem(f'two draws differ in size or colour channels ({first.shape} against {second.shape}); draw them the same way.')
    per_dot = np.abs(first - second).max(axis=2)
    return {'changed_share': float((per_dot > dot_levels).mean()), 'largest_levels': int(per_dot.max()),
            'mean_levels': float(per_dot.mean())}


def compare_name(name, old_paths, new_paths, dot_levels):
    old = {k: read_picture(p) for k, p in sorted(old_paths.items())}
    new = {k: read_picture(p) for k, p in sorted(new_paths.items())}
    old_pairs = []
    for a, b in itertools.combinations(sorted(old), 2):
        old_pairs.append(dict(difference(old[a], old[b], dot_levels), old_draws=[a, b]))
    spread_share = max(p['changed_share'] for p in old_pairs)
    spread_largest = max(p['largest_levels'] for p in old_pairs)
    new_draws = []
    for k in sorted(new):
        against = [dict(difference(new[k], old[o], dot_levels), old_draw=o) for o in sorted(old)]
        nearest = min(against, key=lambda d: (d['changed_share'], d['largest_levels']))
        nearest['new_draw'] = k
        nearest['outside_the_spread'] = nearest['changed_share'] > spread_share
        new_draws.append(nearest)
    real = all(d['outside_the_spread'] for d in new_draws)
    return {'name': name, 'old_draws': len(old), 'new_draws': len(new), 'old_against_old': old_pairs,
            'spread_changed_share': spread_share, 'spread_largest_levels': spread_largest,
            'old_against_new': new_draws, 'draws_outside_the_spread': sum(d['outside_the_spread'] for d in new_draws),
            'verdict': 'real' if real else 'within ordinary variation'}


def percent(share):
    return f'{share * 100:.3f}%'


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Compares several draws of the old and new version of the same moments: the old-against-old spread first, '
                    'then old against new; a difference is "real" only when it is bigger than the spread in every draw.')
    parser.add_argument('--old', required=True, help='folder of the old version\'s draws: NAME-1.png, NAME-2.png, NAME-3.png ...')
    parser.add_argument('--new', required=True, help='folder of the new version\'s draws, named the same way')
    parser.add_argument('--names', nargs='*', help='compare only these NAMEs')
    parser.add_argument('--dot-levels', type=int, default=0,
                        help='a dot counts as changed when one colour differs by more than this many levels of 255 (default 0)')
    parser.add_argument('--out', help='also write the result as JSON to this file')
    parser.add_argument('--json', action='store_true', help='print the result as JSON instead of plain lines')
    args = parser.parse_args(argv)

    old, new = find_draws(args.old), find_draws(args.new)
    names = sorted(set(old) | set(new))
    if args.names:
        names = [n for n in names if n in args.names]
        unknown = sorted(set(args.names) - set(old) - set(new))
        if unknown:
            raise InputProblem(f'no draws named {", ".join(unknown)} in either folder.')
    if not names:
        raise InputProblem(f'no pictures named NAME-1.png, NAME-2.png ... in {args.old} or {args.new}.')
    problems = []
    for name in names:
        for version, draws in (('old', old), ('new', new)):
            count = len(draws.get(name, {}))
            if count < DRAWS_NEEDED:
                problems.append(f'{name}: {count} draw(s) of the {version} version (at least {DRAWS_NEEDED} are needed)')
    if problems:
        print('regression_compare: refused. One draw cannot tell a real change from the ordinary variation between two draws '
              'of the same code; draw each moment at least 3 times with each version.', file=sys.stderr)
        for line in problems:
            print('  ' + line, file=sys.stderr)
        return 2

    results = [compare_name(name, old[name], new[name], args.dot_levels) for name in names]
    picture_files = sum(r['old_draws'] + r['new_draws'] for r in results)
    real = [r['name'] for r in results if r['verdict'] == 'real']
    summary = {'old_folder': os.path.abspath(args.old), 'new_folder': os.path.abspath(args.new), 'pictures_compared': len(results),
               'picture_files_read': picture_files, 'dot_levels': args.dot_levels, 'pictures': results,
               'real_differences': real, 'verdict': 'real difference' if real else 'within ordinary variation'}
    lines = [f'regression_compare: {args.old} (old) against {args.new} (new)',
             f'Compared {len(results)} picture(s): ' + ', '.join(f'{r["name"]} ({r["old_draws"]} old draws, {r["new_draws"]} new draws)' for r in results)
             + f'; {picture_files} picture files in all.',
             f'A dot counts as changed when one of its colours differs by more than {args.dot_levels} level(s) of 255.', '']
    for r in results:
        lines.append(r['name'])
        lines.append(f'  1. old against old (the ordinary variation, {len(r["old_against_old"])} pairs): at most '
                     f'{percent(r["spread_changed_share"])} of dots changed, largest difference {r["spread_largest_levels"]} levels')
        for pair in r['old_against_old']:
            lines.append(f'       old {pair["old_draws"][0]} against old {pair["old_draws"][1]}: {percent(pair["changed_share"])} of dots, '
                         f'largest {pair["largest_levels"]} levels')
        lines.append('  2. old against new (each new draw against the old draw nearest to it):')
        for d in r['old_against_new']:
            lines.append(f'       new {d["new_draw"]} against old {d["old_draw"]}: {percent(d["changed_share"])} of dots, largest '
                         f'{d["largest_levels"]} levels: ' + ('bigger than the spread' if d['outside_the_spread'] else 'within the spread'))
        if r['verdict'] == 'real':
            lines.append(f'  3. REAL: every new draw ({r["draws_outside_the_spread"]} of {r["new_draws"]}) differs from the old draws by more than '
                         'the old draws differ among themselves. (A rare outcome of the old code could still look like this: '
                         'draw more of the old version if the verdict matters.)')
        else:
            lines.append(f'  3. within ordinary variation: {r["new_draws"] - r["draws_outside_the_spread"]} of {r["new_draws"]} new draw(s) '
                         'differ from an old draw by no more than the old draws differ among themselves.')
        lines.append('')
    lines.append(f'Overall: {"REAL difference in " + ", ".join(real) if real else "within ordinary variation"} '
                 f'({len(results)} picture(s), {picture_files} draws compared).')
    print(json.dumps(summary, indent=1) if args.json else '\n'.join(lines))
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, 'w') as handle:
            json.dump(summary, handle, indent=1)
    return 1 if real else 0


if __name__ == '__main__':
    sys.exit(run_main(main, 'regression_compare'))
