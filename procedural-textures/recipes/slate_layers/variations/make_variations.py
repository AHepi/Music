# What this does (plain words): bakes the colour picture of EIGHT variations of the slate recipe (each is the default settings with a few
# settings changed, listed in variations.json) at 1254 dots, then makes a contact sheet (contact_sheet.png) with every tile's name, its one-line
# description and the settings it changed written under it, and scores each tile with the project's "same kind of surface" tool (colour group).
# Use (plain python): python3 -I make_variations.py [bake|sheet|score|all]
# Changed after the look fixes (round 15): variations.json now also holds an entry called "before the look fixes" (the old settings and scores); this script skips it.
# The contact sheet says "same-kind colour" for the score of each tile and now also the score it had before the look fixes.
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
SPEC = {k: v for k, v in json.load(open(os.path.join(HERE, 'variations.json'))).items() if k != 'before the look fixes'}
step = sys.argv[1] if len(sys.argv) > 1 else 'all'


def settings_of(name):
    return {k: v for k, v in SPEC[name].items() if not k.startswith('_')}


if step in ('bake', 'all'):
    views = {name: settings_of(name) for name in SPEC if not os.environ.get('ONLY') or name == os.environ['ONLY']}
    subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'), HERE, '1254', '4',
                              json.dumps(views), '{}', 'Colour'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
if step in ('score', 'all'):
    scores = {}
    for name in SPEC:
        scores[name] = float(subprocess.run(['bash', os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'score_colour.sh'), os.path.join(HERE, name + '_colour.png')],
                                            capture_output=True, text=True).stdout.split()[2])
    json.dump(scores, open(os.path.join(HERE, 'same_kind_colour_scores.json'), 'w'), indent=1)
    print(scores)
if step in ('sheet', 'all'):
    scores = json.load(open(os.path.join(HERE, 'same_kind_colour_scores.json'))) if os.path.exists(os.path.join(HERE, 'same_kind_colour_scores.json')) else {}
    cell, text_h, columns = 560, 150, 4
    tiles = []
    for name in SPEC:
        picture = cv2.resize(cv2.imread(os.path.join(HERE, name + '_colour.png')), (cell, cell), interpolation=cv2.INTER_AREA)
        card = np.full((cell + text_h, cell, 3), 245, np.uint8)
        card[:cell] = picture
        old_scores = json.load(open(os.path.join(HERE, 'same_kind_colour_scores_before_look_fixes.json'))) if os.path.exists(os.path.join(HERE, 'same_kind_colour_scores_before_look_fixes.json')) else {}
        cv2.putText(card, name + (f'   same-kind colour {scores[name]:.2f}' if name in scores else '') + (f' (before the look fixes {old_scores[name]:.2f})' if name in old_scores else ''), (8, cell + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
        words = SPEC[name]['_words']
        line, y = '', cell + 40
        for word in words.split():
            if len(line) + len(word) > 70:
                cv2.putText(card, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (60, 60, 60), 1); y += 15; line = ''
            line += word + ' '
        cv2.putText(card, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (60, 60, 60), 1); y += 18
        changed = '  '.join(f'{k.replace("colour_and_fade", "cf").replace("outline_and_shadow", "os")}={v}' for k, v in settings_of(name).items())
        line = ''
        for word in changed.split('  '):
            if len(line) + len(word) > 78:
                cv2.putText(card, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (120, 0, 0), 1); y += 13; line = ''
            line += word + '  '
        cv2.putText(card, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (120, 0, 0), 1)
        tiles.append(card)
    rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
    cv2.imwrite(os.path.join(HERE, 'contact_sheet.png'), np.vstack(rows))
