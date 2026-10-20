# What this does (plain words): one round of SETTINGS-ONLY changes to the brick reuse test (no layer file touched): b0 = the first brick settings,
# b1 = redder bricks and light mortar (palette and joint colours only), b2 = b1 + no up-down fade on the bricks (fade_direction 0) + big dark "soot"
# patches (the damp-stain setting). Draws the three next to the brick reference (whole tile shrunk and a 2 x enlarged crop) and scores each picture's
# COLOUR group against the BRICK reference (a sanity check only: the brick reference shows what a brick wall can look like; nothing is fitted).
# Use (plain python): python3 -I make_sheet_and_scores.py
import json, os, shutil, subprocess, tempfile
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
names = ['b0_first_brick_settings', 'b1_redder_bricks_light_mortar', 'b2_plus_no_up_down_fade_and_soot']
scores = {}
for name in names:
    folder = tempfile.mkdtemp(dir=HERE)
    picture = cv2.imread(os.path.join(HERE, name + '_colour.png'))
    cv2.imwrite(os.path.join(folder, 'colour.png'), cv2.resize(picture, (1254, 1254), interpolation=cv2.INTER_CUBIC))
    shutil.copy(os.path.join(HERE, '..', 'baked', 'brick_all_height.png'), os.path.join(folder, 'height.png'))
    shutil.copy(os.path.join(HERE, '..', 'baked', 'brick_all_normal.png'), os.path.join(folder, 'normal.png'))
    subprocess.run(['python3', '-I', os.path.join(PROC, 'lib', 'texture_compare.py'), 'brick', folder, '--json', os.path.join(folder, 'score.json')], capture_output=True)
    result = json.load(open(os.path.join(folder, 'score.json')))
    scores[name] = {'colour group against the brick reference': result['groups']['colour'], 'colour scores': {k: v for k, v in result['scores'].items() if k.startswith('colour')}}
    shutil.rmtree(folder)
    print(name, scores[name]['colour group against the brick reference'])
json.dump(scores, open(os.path.join(HERE, 'scores.json'), 'w'), indent=1)
reference = cv2.imread(os.path.join(PROC, 'reference', 'brick', 'colour.png'))
panels, crops = [], []
for text, picture in [('brick reference (a guide only)', reference)] + [(n, cv2.imread(os.path.join(HERE, n + '_colour.png'))) for n in names]:
    whole = cv2.resize(picture, (500, 500), interpolation=cv2.INTER_AREA)
    s = picture.shape[0] / 1254.0
    crop = cv2.resize(picture[int(300 * s):int(550 * s), int(300 * s):int(550 * s)], (500, 500), interpolation=cv2.INTER_AREA)
    for image in (whole, crop):
        cv2.rectangle(image, (0, 0), (500, 28), (255, 255, 255), -1)
        cv2.putText(image, text[:44], (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    panels.append(whole)
    crops.append(crop)
cv2.imwrite(os.path.join(HERE, 'brick_settings_round_2.jpg'), np.vstack([np.hstack(panels), np.hstack(crops)]), [cv2.IMWRITE_JPEG_QUALITY, 90])
