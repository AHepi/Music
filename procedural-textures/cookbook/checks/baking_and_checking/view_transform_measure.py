# What this does: plain-Python follow-up to view_transform_strip.py. For every square in view_transform_tiles/ it measures how far it is from the
# right square (colour: Standard; height: Raw) dot by dot: the average difference in steps of 255, the average colour difference (Delta E, using the
# same colour maths as lib/texture_compare.py) and the average colour strength (Lab chroma). Adds the result to view_transform_numbers.json, then
# joins the squares into one labelled strip with lib/make_strip.py and saves a small JPEG copy for the cookbook.
# Use: python3 -I view_transform_measure.py
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import texture_compare  # noqa: E402

TILES = os.path.join(HERE, 'view_transform_tiles')
info = json.load(open(os.path.join(TILES, 'sweep.json')))
pictures = {label: cv2.imread(os.path.join(TILES, name))[..., ::-1].astype(np.float64) / 255.0 for name, label in zip(info['files'], info['labels'])}
right_colour, right_height = pictures['colour, Standard (right)'], pictures['height, Raw (right)']
numbers_path = os.path.join(HERE, 'view_transform_numbers.json')
numbers = json.load(open(numbers_path))
for label, picture in pictures.items():
    right = right_colour if label.startswith('colour') else right_height
    lab, lab_right = texture_compare.srgb_to_lab(picture), texture_compare.srgb_to_lab(right)
    numbers[label]['average_difference_steps_of_255'] = round(float(np.abs(picture - right).mean() * 255.0), 1)
    numbers[label]['average_colour_difference_delta_e'] = round(float(np.sqrt(((lab - lab_right) ** 2).sum(axis=-1)).mean()), 2)
    numbers[label]['average_colour_strength_chroma'] = round(float(np.hypot(lab[..., 1], lab[..., 2]).mean()), 2)
with open(numbers_path, 'w') as handle:
    json.dump(numbers, handle, indent=1)
strip_png = os.path.join(HERE, 'view_transform_strip.png')
subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'make_strip.py'), TILES, strip_png, '--columns', '4', '--cell', '256',
                '--title', 'One brick recipe, only the View Transform changed (top: colour, bottom: height)'], check=True)
strip = cv2.imread(strip_png)
cv2.imwrite(os.path.join(PROC, 'cookbook', 'pictures', 'baking-strip-view-transform.jpg'), strip, [cv2.IMWRITE_JPEG_QUALITY, 85])
os.remove(strip_png)
print(json.dumps({k: v for k, v in numbers.items() if isinstance(v, dict)}, indent=1))
