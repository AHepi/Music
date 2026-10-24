"""What this file does (plain words): looks for dry-looking patches and seams where the behind painting is worn, along the move. For each second asked, the frame of the wet clip is compared with the reference still
(the same moment drawn with the wet front painting as its own behind painting, so nothing can differ because of the behind painting). In the lower 55 percent of the frame (the ground): the share of dots whose
(slightly blurred) brightness differs by more than 0.04, how many of those are LIGHTER (a dry-looking behind painting is lighter and redder) and how many darker, and the average signed difference. The wet street test's
numbers for the same kind of measure (end of the move): wet behind painting 33 percent of road dots differ, 12.6 percent lighter, 20.2 percent darker, mean -0.006; old dry behind painting 61 percent differ, 59 percent lighter, mean +0.092.
Also makes a picture of the difference for each second (lighter in orange, darker in blue). Run: python3 -I measure_patches.py CLIP.mp4 OUT_FOLDER
"""
import json, os, subprocess, sys
import cv2, numpy as np
clip, out = sys.argv[1], sys.argv[2]
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(out, exist_ok=True)
def frame(t):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-vf', f'select=eq(n\\,{int(round(t * 30))})', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3)
def lum(im):
    b, g, r = [im[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
res = {}
for t in (3.0, 4.0, 5.0, 6.0, 7.0):
    ref = cv2.imread(os.path.join(W, 'stills', 'own', f'own_{t}', 'still-%.2f.jpg' % t))
    if ref is None: print('no reference for', t); continue
    a, b = lum(frame(t)), lum(ref)
    d = cv2.GaussianBlur(a - b, (0, 0), 2)
    ground = np.zeros(d.shape, bool); ground[int(0.45 * 1920):] = True
    diff = (np.abs(d) > 0.04) & ground
    res[str(t)] = {'ground_dots_that_differ_more_than_0.04': float(diff[ground].mean()), 'lighter': float(((d > 0.04) & ground)[ground].mean()), 'darker': float(((d < -0.04) & ground)[ground].mean()),
                   'mean_signed_difference_ground': float(d[ground].mean()), 'mean_absolute_difference_whole_frame': float(np.abs(a - b).mean())}
    vis = np.zeros((1920, 1080, 3), np.uint8) + 40
    vis[..., 2] = np.clip(128 + 1200 * np.clip(d, 0, None), 0, 255).astype(np.uint8)   # lighter: red/orange (BGR)
    vis[..., 0] = np.clip(128 + 1200 * np.clip(-d, 0, None), 0, 255).astype(np.uint8)  # darker: blue
    vis[..., 1] = 100
    cv2.imwrite(os.path.join(out, f'difference_{t}.jpg'), cv2.resize(vis, (540, 960), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(t, json.dumps(res[str(t)]))
json.dump(res, open(os.path.join(W, 'numbers', 'patches_wet_clip.json'), 'w'), indent=1)
