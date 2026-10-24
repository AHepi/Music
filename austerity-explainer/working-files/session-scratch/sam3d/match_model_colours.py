"""What this does: makes 3D models match the painting they came from. It compares, object by object,
the average colour of the painted object (in a still of the original painted room) with the average
colour of its 3D model (in a still of the test scene from the same view), inside that object's mask,
and multiplies the model's tint in layout.json by the difference. Run it, redraw, and run it again
(two rounds get within a few percent).
Use: python3 -I match_model_colours.py ORIGINAL_STILL.jpg MODELS_STILL.jpg MASK_FOLDER LAYOUT.json"""
import glob, json, sys
import numpy as np
from PIL import Image, ImageFilter

original_still, models_still, mask_folder, layout_path = sys.argv[1:5]
a = np.asarray(Image.open(original_still).convert('RGB'), dtype=float)
b = np.asarray(Image.open(models_still).convert('RGB'), dtype=float)
layout = json.load(open(layout_path))
masks = sorted(glob.glob(f'{mask_folder}/mask-[0-9]*.png'))
for k, (path, obj) in enumerate(zip(masks, layout['objects'])):
    m = Image.open(path).resize((a.shape[1], a.shape[0])).filter(ImageFilter.MinFilter(21))   # stay inside the edges
    inside = np.asarray(m) > 128
    ma, mb = a[inside].mean(0), b[inside].mean(0)
    change = np.clip(ma / np.maximum(mb, 1), 0.3, 2.0)
    obj['tint'] = [round(float(t * c), 4) for t, c in zip(obj.get('tint', [1, 1, 1]), change)]
    print(f'{obj["name"]}: painted {ma.round(0)}, model {mb.round(0)}, tint now {obj["tint"]}')
json.dump(layout, open(layout_path, 'w'), indent=1)
