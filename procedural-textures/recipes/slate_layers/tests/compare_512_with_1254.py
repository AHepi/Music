# What this does (plain words): checks that the finished default tile looks the same when it is baked small. It takes the 512-dot bake in
# confirm_512_after_look_fixes/ (made with the same settings as outputs/default) and the 1254-dot default shrunk to 512 dots, and measures how far apart they are
# (mean difference in steps of 255, and the share of dots more than 40 steps apart) for the colour, the height and the roughness; it also writes a picture with the
# two side by side and one crop at full size. Same rule as resolution/run_resolution.py. Use (plain python): python3 -I compare_512_with_1254.py
import json, os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..'))
small = os.path.join(HERE, 'confirm_512_after_look_fixes')
big = os.path.join(SL, 'outputs', 'default')
def read(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    a = a / (65535.0 if a.max() > 255 else 255.0) * 255.0
    return a
result = []
for name in ('colour', 'height', 'roughness'):
    a = read(os.path.join(small, name + '.png'))
    b = cv2.resize(read(os.path.join(big, name + '.png')), (512, 512), interpolation=cv2.INTER_AREA)
    d = np.abs(a - b)
    d = d.max(axis=2) if d.ndim == 3 else d
    result.append({'picture': name, 'mean difference (of 255)': round(float(d.mean()), 2), 'share of dots over 40 steps %': round(float(100 * (d > 40).mean()), 3)})
    print(result[-1])
json.dump({'what': '1254-dot default (outputs/default) shrunk to 512 compared with a 512-dot bake of the same settings', 'results': result}, open(os.path.join(HERE, 'confirm_512_after_look_fixes_differences.json'), 'w'), indent=1)
colour_small = cv2.imread(os.path.join(small, 'colour.png'))
colour_big = cv2.resize(cv2.imread(os.path.join(big, 'colour.png')), (512, 512), interpolation=cv2.INTER_AREA)
for picture, text in ((colour_small, '512-dot bake'), (colour_big, '1254-dot default shrunk to 512')):
    cv2.rectangle(picture, (0, 0), (512, 22), (255, 255, 255), -1)
    cv2.putText(picture, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
cv2.imwrite(os.path.join(HERE, 'confirm_512_after_look_fixes_side_by_side.jpg'), np.hstack([colour_small, colour_big]), [cv2.IMWRITE_JPEG_QUALITY, 90])
