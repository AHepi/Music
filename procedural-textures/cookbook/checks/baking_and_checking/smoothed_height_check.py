# What this does: checks which reference height lib/texture_compare.py compares against. It scores two copies of the brick reference slid by
# (311, 517) dots that differ ONLY in their height picture: tests/selftest_brick_rolled2 holds the 8-bit uploaded height, tests/selftest_brick_rolled
# holds the 16-bit lightly smoothed height. If the tool reads the 8-bit upload for the reference, the 8-bit copy's height group is (about) 1.0 and the
# smoothed copy's is lower. Writes smoothed_height_check.json. Plain Python: python3 -I smoothed_height_check.py
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import texture_compare
result = {}
for label, folder in (('8-bit uploaded height (selftest_brick_rolled2)', 'selftest_brick_rolled2'), ('16-bit smoothed height (selftest_brick_rolled)', 'selftest_brick_rolled')):
    report = texture_compare.score_set('brick', os.path.join(PROC, 'tests', folder))
    result[label] = {'overall': report['overall'], 'groups': report['groups'],
                     'height_scores': {k: v for k, v in report['scores'].items() if k.startswith('height')},
                     'normal_scores': {k: v for k, v in report['scores'].items() if k.startswith('normal')}}
    print(label, json.dumps(result[label]))
json.dump(result, open(os.path.join(HERE, 'smoothed_height_check.json'), 'w'), indent=1)
