# What this does: reads the reference colour pictures (for ANALYSIS only - they are never used inside a recipe) and prints the main colours
# of each surface (k-means in sRGB, sorted dark to light) plus how bright the height map is where the colour is dark vs light.
# Run: python3 -I analyse_reference_palettes.py
import cv2, numpy as np, json, os
ref = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reference'
out = {}
for name in ['brick','slate','wood','metal','mud','gravel']:
    img = cv2.imread(f'{ref}/{name}/colour.png')[..., ::-1]
    small = cv2.resize(img, (256,256), interpolation=cv2.INTER_AREA).reshape(-1,3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, labels, centres = cv2.kmeans(small, 8, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=8) / len(labels)
    order = np.argsort(centres.mean(axis=1))
    out[name] = [{'srgb': [int(v) for v in centres[i]], 'share': round(float(counts[i]),3)} for i in order]
    h = cv2.imread(f'{ref}/{name}/height.png', cv2.IMREAD_UNCHANGED).astype(np.float64)
    h = h[...,0] if h.ndim==3 else h
    h = h/ (65535.0 if h.max()>255 else 255.0)
    out[name+'_height'] = {'mean': round(float(h.mean()),3), 'std': round(float(h.std()),3), 'p5': round(float(np.percentile(h,5)),3), 'p95': round(float(np.percentile(h,95)),3)}
json.dump(out, open('reference_palettes.json','w'), indent=1)
for k,v in out.items(): print(k, v if k.endswith('height') else [ (c['srgb'], c['share']) for c in v])
