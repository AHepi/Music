# What this does (plain words): the "what does each layer buy" ladder. It takes the ladder bakes (the whole recipe at 1254 dots with layers added one at a
# time: layout and joints with flat slates; + colour and fade; + moss; + damage = the default tile; and the default WITHOUT the outline), scores each one
# against the slate reference with the project's "same kind" tool (colour group from the colour picture; height and normal groups from the height picture,
# the normal being made the way the harness makes it), and draws one sheet with the same crop of every rung next to the reference.
# Use (plain python): python3 -I make_ladder_table.py
import json, os, subprocess
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(SL, '..', '..'))
RUNGS = [('0', 'layout and joints, flat slates', 'ladder0_layout_joints_flat_slates'),
         ('1', '+ colour and fade', 'ladder1_plus_colour_and_fade'),
         ('2', '+ moss', 'ladder2_plus_moss'),
         ('3', '+ damage (= the default tile)', None),
         ('-', 'the default WITHOUT the outline and shadow', 'ladder4_without_outline')]


def files(stem):
    if stem is None:
        return os.path.join(SL, 'outputs', 'default', 'colour.png'), os.path.join(SL, 'outputs', 'default', 'height.png')
    return os.path.join(HERE, stem + '_colour.png'), os.path.join(HERE, stem + '_height.png')


rows = []
for number, words, stem in RUNGS:
    colour, height = files(stem)
    colour_line = subprocess.run(['bash', os.path.join(SL, 'integration', 'score_colour.sh'), colour], capture_output=True, text=True).stdout
    colour_group = float(colour_line.split()[2])
    scale = float(colour_line.split("'colour_scale': ")[1].split(',')[0])
    set_line = subprocess.run(['python3', '-I', os.path.join(SL, 'integration', 'score_set.py'), colour, height], capture_output=True, text=True).stdout
    groups = json.loads(set_line.split('groups ')[1].split(' sobel')[0].replace("'", '"'))
    overall = float(set_line.split()[1])
    rows.append({'rung': number, 'what': words, 'colour group': colour_group, 'colour_scale measure': scale, 'height group': groups['height'],
                 'overall (normal made like the harness)': overall})
    print(rows[-1], flush=True)
json.dump(rows, open(os.path.join(HERE, 'ladder_scores.json'), 'w'), indent=1)
with open(os.path.join(HERE, 'ladder_table.md'), 'w') as handle:
    handle.write('| rung | what is in the picture | same-kind colour group | of which: feature size (colour_scale) | same-kind height group | overall |\n|---|---|---|---|---|---|\n')
    for r in rows:
        handle.write(f"| {r['rung']} | {r['what']} | {r['colour group']:.3f} | {r['colour_scale measure']:.3f} | {r['height group']:.3f} | {r['overall (normal made like the harness)']:.3f} |\n")
# the sheet: the same 420 x 420 crop of every rung and of the reference, enlarged 1.2 x
x, y, w = 300, 300, 420
panels = []
reference = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'colour.png'))
for words, picture in [('reference (a guide only)', reference)] + [(f'{n}: {t}', cv2.imread(files(s)[0])) for n, t, s in RUNGS]:
    piece = cv2.resize(picture[y:y + w, x:x + w], (504, 504), interpolation=cv2.INTER_AREA)
    cv2.rectangle(piece, (0, 0), (504, 30), (255, 255, 255), -1)
    cv2.putText(piece, words[:46], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
    panels.append(piece)
cv2.imwrite(os.path.join(HERE, 'ladder_sheet.jpg'), np.vstack([np.hstack(panels[0:3]), np.hstack(panels[3:6])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
