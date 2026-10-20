# What this file does (plain words): bakes the REAL recipe (all layers) at a small size for several named variants of the moss settings, and prints the general-character numbers
# of each picture (share of slate dots that look olive, how top-heavy they are, how patchy slate to slate, typical run lengths), next to the numbers measured once on the reference.
# This is for tuning BY HAND (look, change a setting, look again): it is not an optimiser. Use: python3 -I tune_real.py NAME SIZE 'JSON {variant: {settings}}'
import json, os, subprocess, sys, re
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.abspath(os.path.join(here, '..'))
name, size, variants = sys.argv[1], int(sys.argv[2]), json.loads(sys.argv[3])
out = os.path.join(work, 'dev', name)
keys = {l: f'v{i}' for i, l in enumerate(variants)}
views = {keys[l]: v for l, v in variants.items()}
subprocess.run([os.path.join(work, '..', 'tests', 'blender.sh'), os.path.join(work, '..', 'tests', 'bake_tools.py'), '--', os.path.join(work, '..', 'recipe', 'slate_recipe.py'), out, str(size), '4', json.dumps(views), '{}', 'Colour'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('REFERENCE (measured once): olive 7.5 % of slate dots; top tenth 11.6 %, bottom tenth 5.5 %; per-block std 4.5 %, blocks under 2 %: 19 %, over 15 %: 2 %; vertical run median 3, p90 18 (at 1254)')
for l in variants:
    path = f'{out}/{keys[l]}_colour.png'
    res = subprocess.run([sys.executable, '-I', os.path.join(here, 'measure_moss_in_picture.py'), path], capture_output=True, text=True).stdout
    share = re.search(r'share of slate dots: olive ([0-9.]+)', res).group(1)
    prof = re.search(r'olive share by tenth.*: \[(.*)\]', res).group(1).split(', ')
    blocks = re.search(r'std ([0-9.]+), share of blocks under 2%: ([0-9.]+), over 15%: ([0-9.]+)', res)
    runs = re.search(r'vertical run of olive: percentiles 50/75/90/99 = \[(.*?)\]', res).group(1)
    print(f'{l:40s} olive {float(share)*100:4.1f}%  top/bottom tenth {float(prof[0])*100:4.1f}/{float(prof[-1])*100:4.1f}  block std {float(blocks.group(1))*100:4.1f}% under2% {float(blocks.group(2))*100:3.0f}% over15% {float(blocks.group(3))*100:3.0f}%  v-run p50/75/90/99 {runs}')
cells = [cv2.imread(f'{out}/{keys[l]}_colour.png') for l in variants]
cv2.imwrite(f'{out}/contact.png', np.hstack(cells) if len(cells) <= 3 else np.vstack([np.hstack(cells[i:i + 2]) for i in range(0, len(cells), 2)]))
