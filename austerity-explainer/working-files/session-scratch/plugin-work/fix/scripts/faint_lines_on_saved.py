# What this does: runs the plugin's own comparison (compare.pair_differences, runner.flag_results and runner.faint_lines)
# on pictures already drawn in earlier runs, without drawing anything, and prints what a helper would read.
import json, os, sys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit.variations import compare, runner  # noqa: E402

for path in sys.argv[1:]:
    document = json.load(open(path))
    folder = os.path.dirname(os.path.abspath(path))
    results = document['results']
    for result in results:
        for picture in result.get('pictures', []):
            picture['path'] = os.path.join(folder, picture['path']) if picture.get('path') else None
    is_scout = bool(document.get('scout') is True)
    pairs = compare.pair_differences(results, scout=is_scout)
    lines = runner.flag_results(results, pairs)
    faint = runner.faint_lines(results, pairs)
    print('==', path, '(scout)' if is_scout else '(card or local batch)')
    print(f'  nearly the same: {len(pairs["nearly_same"])} pair(s); faint: {len(pairs["faint"])} pair(s); faint against the baseline: {pairs["faint_against_baseline"]}')
    for line in lines:
        print('  LOOK nearly the same:', line)
    for line in faint:
        print('  LOOK may not be visible:', line)
