# What this does (plain words): bakes a quarter-size WINDOW of the recipe at 1254 dots per tile for several named sets of settings in ONE Blender run,
# measures each picture with profile_tools.py (the black core, the lip, the shadow band, the joints) and prints one short table next to the numbers
# of the reference picture. It is a GUIDE for hand tuning (look, change a setting, look again), not an optimiser.
# Use: python3 -I measure_sets.py LABEL '{"set name": {"outline_and_shadow.band_width": 0.0006}, "other": {}}' [window cx,cy,width]
# Output: previews/measure_LABEL/<set>_colour.png and a printed table; also measure_LABEL/table.md
import json, os, subprocess, sys
import cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)      # python3 -I does not look in the script's own folder
import profile_tools as pt
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
label, sets = sys.argv[1], json.loads(sys.argv[2])
window = sys.argv[3] if len(sys.argv) > 3 else '0.5,0.5,0.5'
width = float(window.split(',')[2])
pixels = int(round(1254 * width))
folder = os.path.join(HERE, 'previews', 'measure_' + label)
os.makedirs(folder, exist_ok=True)
jobs = {name.replace(' ', '_'): {'params': params} for name, params in sets.items()}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, folder, str(pixels), window, json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
reference = pt.measure(os.path.join(HERE, '..', '..', '..', 'reference', 'slate', 'colour.png'), 1254)
rows = [('reference', reference)]
for name in jobs:
    rows.append((name, pt.measure(os.path.join(folder, f'{name}_colour.png'), 1254)))
header = ['name', 'core len', 'lip@2', 'lip@4', 'lip@8', 'shadow@1', '@4', '@10', '@22', '@40', 'joint w', 'joint 10-90', 'dark share', 'dist1-2', 'dist2-4']
lines = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
for name, r in rows:
    a, s, d = r.get('above_core', {}), r.get('below_core', {}), r['brightness_by_distance_from_dark']
    lines.append('| ' + ' | '.join(str(x) for x in [name, r['core_length_median'], a.get(2), a.get(4), a.get(8), s.get(1), s.get(4), s.get(10), s.get(22), s.get(40),
                 r['vertical_joint_width_median'], r['vertical_joint_width_p10_p90'], r['share_dark_under_26'], d['1-2'], d['2-4']]) + ' |')
text = '\n'.join(lines)
print(text)
open(os.path.join(folder, 'table.md'), 'w').write(text + '\n')
