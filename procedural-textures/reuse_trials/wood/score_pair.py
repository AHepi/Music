# What this does (plain words): scores ONE colour picture with ONE height picture against the wood reference, the same way as the final scores
# (normal map made from the height by recipes/slate_layers/integration/make_normal.py at the wood strength 8, then lib/texture_compare.py).
# Used while tuning to try a colour with different heights (the height picture can come from another view of the same settings).
# Both pictures must be 1254 dots for the score to be like for like. Prints overall, the four groups and every measure. Writes nothing but a
# scratch folder that it deletes again.
# Use: python3 -I score_pair.py COLOUR.png HEIGHT.png [label]
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
colour, height = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(colour)
scratch = tempfile.mkdtemp(dir=HERE)
try:
    shutil.copyfile(colour, os.path.join(scratch, 'colour.png'))
    shutil.copyfile(height, os.path.join(scratch, 'height.png'))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(scratch, 'height.png'), os.path.join(scratch, 'normal.png'), '8'], check=True)
    report = json.loads(subprocess.run([sys.executable, '-I', COMPARE, 'wood', scratch], check=True, capture_output=True, text=True).stdout)
    groups = report['groups']
    print(f"{label:34s} overall {report['overall']:.3f}  colour {groups['colour']:.3f}  height {groups['height']:.3f}  normal {groups['normal']:.3f}  tiling {groups['tiling']:.3f}  "
          f"lengths {report['facts']['correlation_length_px_candidate']}")
    print('   ' + '  '.join(f'{k.replace("colour_", "c_").replace("height_", "h_").replace("normal_", "n_")} {v:.2f}' for k, v in report['scores'].items()))
finally:
    shutil.rmtree(scratch)
