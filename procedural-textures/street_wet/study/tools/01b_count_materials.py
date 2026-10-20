# What this does: reads the false-colour picture made by 01_material_map.py and works out what share of the frame each material covers.
# Plain Python (run with python3 -I). Writes NAME_shares.json beside the picture and prints the biggest shares.
# Run:  python3 -I 01b_count_materials.py OUT_FOLDER NAME
import json
import sys

import numpy as np
from PIL import Image

folder, name = sys.argv[1], sys.argv[2]
numbers = json.load(open(f'{folder}/{name}_numbers.json'))
picture = np.array(Image.open(f'{folder}/{name}_ids.png'))[..., 0]
counts = np.bincount(picture.ravel(), minlength=256)
total = picture.size
result = {'frame': numbers['frame'], 'camera': numbers['camera'], 'nothing_black': counts[0] / total, 'materials': {}}
for material, number in numbers['numbers'].items():
    result['materials'][material] = {'number': number, 'share': round(float(counts[number] / total), 5), 'objects_wearing_it': numbers['objects_wearing_it'][material]}
json.dump(result, open(f'{folder}/{name}_shares.json', 'w'), indent=1)
for material, info in sorted(result['materials'].items(), key=lambda kv: -kv[1]['share'])[:30]:
    print(f"{info['share'] * 100:6.2f} %  {material}")
print('nothing (black):', round(result['nothing_black'] * 100, 2), '%')
