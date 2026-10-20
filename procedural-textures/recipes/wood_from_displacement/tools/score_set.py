# What this does (plain words): scores one baked folder (colour.png, height.png, normal.png; the normal is made from the height if missing) against the
# reference wood with the project's own "same kind of surface" tool (lib/texture_compare.py): 0 = as different as another real surface,
# 1 = indistinguishable by those measures. It also reports (for transparency only) the dot-for-dot numbers of lib/pixel_compare.py: our boards are
# NOT in the same places as the reference's, so those numbers are low on purpose and must not be read as quality.
# Use: python3 -I score_set.py FOLDER [--json OUT.json] [--pixel]
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, HERE)
import texture_compare as tc  # noqa: E402
import make_normal_from_height as mn  # noqa: E402


def score(folder, pixel=False):
    if not os.path.exists(os.path.join(folder, 'normal.png')):
        mn.write_normal(os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'))
    report = tc.score_set('wood', folder)
    out = {'folder': folder, 'overall': report['overall'], 'groups': report['groups'], 'scores': report['scores'], 'facts': report['facts']}
    if pixel:
        import pixel_compare as pc
        try:
            out['pixel'] = pc.pixel_report('wood', folder)
        except Exception as error:
            out['pixel'] = {'error': str(error)}
    return out


if __name__ == '__main__':
    argv = sys.argv[1:]
    json_path = argv[argv.index('--json') + 1] if '--json' in argv else None
    folder = argv[0]
    result = score(folder, pixel='--pixel' in argv)
    if json_path:
        with open(json_path, 'w') as handle:
            json.dump(result, handle, indent=1)
    print(json.dumps({'overall': result['overall'], 'groups': result['groups'], 'facts': result['facts']}))
