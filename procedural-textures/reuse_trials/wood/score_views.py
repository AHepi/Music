# What this does (plain words): a ROUGH guide while tuning, not the like-for-like score. For each named view of a tuning round (made by
# run_views.py with Colour and Height), it copies the colour and 16-bit height into a scratch folder, makes the normal map from the height with
# recipes/slate_layers/integration/make_normal.py at the wood strength 8, and scores the set against the wood reference with lib/texture_compare.py
# (which enlarges a small picture to 1254 dots, so these numbers are NOT comparable with the 1254-dot bakes). Prints overall and the four groups,
# then deletes the scratch folder. Use: python3 -I score_views.py ROUND_FOLDER view_name [view_name ...]
# If a view has no height picture, the option --height-from FILE uses that height instead: then ONLY the colour group means anything.
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
arguments = sys.argv[1:]
stand_in = None
if '--height-from' in arguments:
    at = arguments.index('--height-from')
    stand_in = arguments[at + 1]
    del arguments[at:at + 2]
folder, names = arguments[0], arguments[1:]
for name in names:
    scratch = tempfile.mkdtemp(dir=HERE)
    try:
        shutil.copyfile(os.path.join(folder, name + '_colour.png'), os.path.join(scratch, 'colour.png'))
        height = os.path.join(folder, name + '_height.png')
        shutil.copyfile(height if os.path.exists(height) else stand_in, os.path.join(scratch, 'height.png'))
        subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(scratch, 'height.png'), os.path.join(scratch, 'normal.png'), '8'], check=True)
        report = json.loads(subprocess.run([sys.executable, '-I', COMPARE, 'wood', scratch], check=True, capture_output=True, text=True).stdout)
        groups = report['groups']
        facts = report['facts']['correlation_length_px_candidate']
        print(f"{name:28s} lengths {facts}  overall {report['overall']:.3f}  colour {groups['colour']:.3f}  height {groups['height']:.3f}  normal {groups['normal']:.3f}  tiling {groups['tiling']:.3f}")
    finally:
        shutil.rmtree(scratch)
