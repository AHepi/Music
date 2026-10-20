# What this does: checks whether the two scoring tools can score a surface they have never seen. It copies lib/texture_compare.py,
# lib/pixel_compare.py, lib/texture_compare_anchors.json and the brick reference into a throw-away folder, gives the brick copy a NEW name
# ("tiles_new"), and runs both tools on it. Nothing in the real lib/ or reference/ is touched; the throw-away folder is deleted at the end.
# Writes new_reference_name_test.json next to this script.  Usage: python3 -I new_reference_name_test.py
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
work = tempfile.mkdtemp(prefix='new_reference_test_')
try:
    os.makedirs(os.path.join(work, 'lib'))
    os.makedirs(os.path.join(work, 'reference'))
    for name in ('texture_compare.py', 'pixel_compare.py', 'texture_compare_anchors.json'):
        shutil.copy(os.path.join(PROJECT, 'lib', name), os.path.join(work, 'lib', name))
    shutil.copytree(os.path.join(PROJECT, 'reference', 'brick'), os.path.join(work, 'reference', 'brick'))
    shutil.copytree(os.path.join(PROJECT, 'reference', 'brick'), os.path.join(work, 'reference', 'tiles_new'))
    candidate = os.path.join(work, 'reference', 'brick')          # any folder with colour.png, height.png, normal.png will do
    result = {}
    for tool in ('texture_compare.py', 'pixel_compare.py'):
        run = subprocess.run([sys.executable, '-I', os.path.join(work, 'lib', tool), 'tiles_new', candidate],
                             capture_output=True, text=True, timeout=600, cwd=work)
        last_error_line = [line for line in run.stderr.strip().splitlines() if line.strip()][-1:] or ['']
        result[tool] = {'exit_code': run.returncode, 'worked': run.returncode == 0 and ('"tier_reached"' in run.stdout or '"overall"' in run.stdout),
                        'last_error_line': last_error_line[0]}
    result['anchor_names_in_the_real_file'] = sorted(json.load(open(os.path.join(PROJECT, 'lib', 'texture_compare_anchors.json'))).keys())
    with open(os.path.join(HERE, 'new_reference_name_test.json'), 'w') as handle:
        json.dump(result, handle, indent=1)
    print(json.dumps(result, indent=1))
finally:
    shutil.rmtree(work, ignore_errors=True)
