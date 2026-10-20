# What this does (plain words): the "what does each layer buy" ladder. It takes the ladder bakes (the whole recipe at 1254 dots with layers added one at a
# time: layout and joints with flat slates; + colour and fade; + moss; + damage = the default tile; and the default WITHOUT the outline), scores each one
# against the slate reference with the project's "same kind" tool (colour group from the colour picture; height and normal groups from the height picture,
# the normal being made the way the harness makes it), and draws one sheet with the same crop of every rung next to the reference.
# Use (plain python): python3 -I make_ladder_table.py
# Changed after the look fixes (round 15): (1) each rung is also scored with the normal map made the way the reference's own normal map was made (3 x 3 slope,
# strength 7, integration/make_normal.py), which is the normal that outputs/default/score_same_kind.json uses, so rung 3 gives the same overall as the default's stored
# score; the older column (the harness's own fitted normal) is kept next to it. (2) The table is written together with the old table under the heading
# "before the look fixes" (read from ladder_table_before_look_fixes.md). (3) It also writes what each layer adds and what taking out the outline costs.
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


def score_strength_7(colour, height_path):
    """overall score and group scores when the normal map is made with the reference's own rule (3 x 3 slope, strength 7)."""
    import shutil, sys, tempfile
    sys.path.insert(0, os.path.join(SL, 'integration'))
    import make_normal
    folder = tempfile.mkdtemp(dir=os.path.join(SL, 'integration'))
    shutil.copy(colour, os.path.join(folder, 'colour.png'))
    shutil.copy(height_path, os.path.join(folder, 'height.png'))
    h = cv2.imread(height_path, cv2.IMREAD_UNCHANGED)
    h = h[..., 0] if h.ndim == 3 else h
    n = make_normal.sobel_normal_from_height(h, 7.0)
    cv2.imwrite(os.path.join(folder, 'normal.png'), ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])
    subprocess.run(['python3', '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), 'slate', folder, '--json', os.path.join(folder, 'score.json')], capture_output=True)
    result = json.load(open(os.path.join(folder, 'score.json')))
    shutil.rmtree(folder)
    return result['overall'], result['groups']


rows = []
for number, words, stem in RUNGS:
    colour, height = files(stem)
    colour_line = subprocess.run(['bash', os.path.join(SL, 'integration', 'score_colour.sh'), colour], capture_output=True, text=True).stdout
    colour_group = float(colour_line.split()[2])
    scale = float(colour_line.split("'colour_scale': ")[1].split(',')[0])
    set_line = subprocess.run(['python3', '-I', os.path.join(SL, 'integration', 'score_set.py'), colour, height], capture_output=True, text=True).stdout
    groups = json.loads(set_line.split('groups ')[1].split(' sobel')[0].replace("'", '"'))
    overall = float(set_line.split()[1])
    overall7, groups7 = score_strength_7(colour, height)
    rows.append({'rung': number, 'what': words, 'colour group': colour_group, 'colour_scale measure': scale, 'height group': groups['height'],
                 'overall (normal made like the harness)': overall, 'overall (strength-7 normal, as the default tile score)': overall7,
                 'normal group (strength-7 normal)': groups7['normal'], 'height group (strength-7 run)': groups7['height']})
    print(rows[-1], flush=True)
json.dump(rows, open(os.path.join(HERE, 'ladder_scores.json'), 'w'), indent=1)
before = open(os.path.join(HERE, 'ladder_table_before_look_fixes.md')).read().strip()
with open(os.path.join(HERE, 'ladder_table.md'), 'w') as handle:
    handle.write('# The ladder: what each layer buys (1254 dots, scored against the slate reference with the "same kind" tool)\n\n')
    handle.write('## after the look fixes (round 15; new default settings; 20 October)\n\n')
    handle.write('| rung | what is in the picture | same-kind colour group | of which: feature size (colour_scale) | same-kind height group | overall, normal made like the harness | overall, strength-7 normal (the default tile score) |\n|---|---|---|---|---|---|---|\n')
    for r in rows:
        handle.write(f"| {r['rung']} | {r['what']} | {r['colour group']:.3f} | {r['colour_scale measure']:.3f} | {r['height group']:.3f} | {r['overall (normal made like the harness)']:.3f} | {r['overall (strength-7 normal, as the default tile score)']:.3f} |\n")
    handle.write('\nWhat each layer adds, step by step (added to the part-built picture before it), and what taking the outline out of the finished tile costs:\n\n')
    handle.write('| step | colour group | height group | overall (harness normal) |\n|---|---|---|---|\n')
    for a, b in ((0, 1), (1, 2), (2, 3)):
        handle.write(f"| rung {rows[a]['rung']} to rung {rows[b]['rung']}: {rows[b]['what']} | {rows[b]['colour group'] - rows[a]['colour group']:+.3f} | {rows[b]['height group'] - rows[a]['height group']:+.3f} | {rows[b]['overall (normal made like the harness)'] - rows[a]['overall (normal made like the harness)']:+.3f} |\n")
    handle.write(f"| the default tile minus the same tile WITHOUT outline and shadow (a cost, not an addition) | {rows[3]['colour group'] - rows[4]['colour group']:+.3f} | {rows[3]['height group'] - rows[4]['height group']:+.3f} | {rows[3]['overall (normal made like the harness)'] - rows[4]['overall (normal made like the harness)']:+.3f} |\n")
    handle.write('\n(The "added" steps and the "cost of removing" step are different questions: the first adds a layer to a partly built picture, the second takes one out of the finished picture. The earlier guides compared the two, which was wrong for the colour group.)\n\n')
    handle.write('## before the look fixes (the old table, kept as it was; same measuring, old default settings)\n\n')
    handle.write(before + '\n')
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
