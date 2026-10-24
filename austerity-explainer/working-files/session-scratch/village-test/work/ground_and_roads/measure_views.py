import sys, json, os
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/calculators')
import numpy as np
import picture_measures as pm
from PIL import Image
def run(path, mask_path=None):
    rgb = pm.load_picture(path)
    lum = pm.luminance(rgb)
    res = {'file': os.path.basename(path), 'size': rgb.shape[:2]}
    res['percentiles'] = {k: round(v, 3) for k, v in pm.percentiles_of(lum).items()}
    clip = float(((rgb >= 0.995).any(axis=2)).mean())
    res['clipped_share'] = round(clip, 5)
    res['mean_saturation'] = round(float(pm.saturation(rgb).mean()), 3)
    res['flat_windows_auto_sky'] = pm.flat_windows(lum, 96, 48, 0.01)
    if mask_path:
        m = np.asarray(Image.open(mask_path).convert('RGBA'))[..., 3] > 250
        rows, cols = lum.shape
        flat = tot = near = 0
        spreads = []
        for y in range(0, rows - 96 + 1, 48):
            for x in range(0, cols - 96 + 1, 48):
                if m[y:y + 96, x:x + 96].mean() > 0.98:
                    tot += 1
                    sd = float(lum[y:y + 96, x:x + 96].std()); spreads.append(sd)
                    flat += sd < 0.01; near += sd < 0.014
        res['backdrop_windows'] = {'windows': tot, 'flat': flat, 'under_0.014': near, 'min_spread': round(min(spreads), 4) if spreads else None}
    return res
if __name__ == '__main__':
    print(json.dumps(run(*sys.argv[1:3]), indent=1))
