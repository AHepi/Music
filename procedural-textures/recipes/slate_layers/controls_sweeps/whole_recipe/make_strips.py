# What this does (plain words): joins the whole-recipe sweep pictures (the finished recipe at its tuned default settings, baked at 768 dots with ONE
# setting changed) into one strip per setting: the same crop (a little over a third of the tile, about two rows of slates) of each value side by side,
# with the value written above it; the default value is marked "(default)". Also prints the colour group of each picture (same-kind score against the
# slate reference, a guide only), so the guide can say what a setting does to the score as well as to the look. Then it deletes the single pictures
# (they are big, and the strips show the same thing). Use (plain python): python3 -I make_strips.py
import json, os, subprocess
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..', '..'))
strips = json.load(open(os.path.join(HERE, 'strips.json')))
defaults = json.load(open(os.path.join(SL, 'recipe', 'settings.json')))
DEFAULTS_NOT_IN_SETTINGS = {}
scores = {}
for strip, (setting, values) in strips.items():
    cells = []
    scores[strip] = {}
    for index, value in enumerate(values):
        path = os.path.join(HERE, 'tiles', f'{strip}__{index}_colour.png')
        picture = cv2.imread(path)
        line = subprocess.run(['bash', os.path.join(SL, 'integration', 'score_colour.sh'), path], capture_output=True, text=True).stdout.split()
        group = float(line[2]) if len(line) > 2 else float('nan')
        scores[strip][str(value)] = group
        size = picture.shape[0]
        x, y, w = int(0.30 * size), int(0.36 * size), int(0.36 * size)
        crop = cv2.resize(picture[y:y + w, x:x + w], (420, 420), interpolation=cv2.INTER_CUBIC)
        is_default = defaults.get(setting) == value
        banner = np.full((34, 420, 3), 245, np.uint8)
        cv2.putText(banner, f'{setting.split(".")[1]} = {value}' + ('  (default)' if is_default else '') + f'   colour {group:.2f}', (6, 23),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
        cells.append(np.vstack([banner, crop]))
        cells.append(np.full((454, 6, 3), 255, np.uint8))
    row = np.hstack(cells[:-1])
    header = np.full((40, row.shape[1], 3), 255, np.uint8)
    cv2.putText(header, f'WHOLE RECIPE at the tuned defaults, one setting changed: {setting}', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(HERE, f'{strip}.jpg'), np.vstack([header, row]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(strip, scores[strip], flush=True)
json.dump(scores, open(os.path.join(HERE, 'colour_group_of_each_picture.json'), 'w'), indent=1)
for name in os.listdir(os.path.join(HERE, 'tiles')):
    os.remove(os.path.join(HERE, 'tiles', name))
os.rmdir(os.path.join(HERE, 'tiles'))
