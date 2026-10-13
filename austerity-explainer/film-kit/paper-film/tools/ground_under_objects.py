"""What this does: finds the real ground under objects that were painted out of a painted room, so 3D
models can stand on it. For each object's mask it takes the painted ground in a ring just around and
below the object (from the ORIGINAL depth picture), turns it into 3D points the same way the cinema
stage does (near/far/fov), fits a flat ground to them (dropping outliers), and writes the ground into
layout.json as "ground": [a, b, c] (height y = a*x + b*z + c). Then it rewrites the clean depth
picture inside each mask so the painted room's floor there is that flat ground (instead of a smear
from whatever surrounded the object), so shadows land and camera moves reveal the right floor.
Use: python3 -I ground_under_objects.py ORIGINAL_DEPTH.png CLEAN_DEPTH.png MASK_FOLDER LAYOUT.json [near far fov]"""
import json, sys
import numpy as np
import cv2

original_depth, clean_depth, mask_folder, layout_path = sys.argv[1:5]
near, far, fov = (float(x) for x in (sys.argv[5:8] if len(sys.argv) > 7 else (6, 70, 40)))
layout = json.load(open(layout_path))
W, H = layout['painting_size']
tan_y = np.tan(np.radians(fov / 2)); tan_x = tan_y * W / H
depth = cv2.imread(original_depth, cv2.IMREAD_GRAYSCALE).astype(float) / 255
clean = cv2.imread(clean_depth, cv2.IMREAD_GRAYSCALE).astype(float) / 255
h, w = depth.shape
ys, xs = np.mgrid[0:h, 0:w]
u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
rx, ry = (2 * u - 1) * tan_x, (2 * v - 1) * tan_y
distance = 1 / (depth / near + (1 - depth) / far)
X, Y, Z = rx * distance, ry * distance, -distance

for obj in layout['objects']:
    if obj.get('keep_painted'):
        continue
    mask = cv2.resize(cv2.imread(f"{mask_folder}/{obj['mask']}", cv2.IMREAD_GRAYSCALE), (w, h), interpolation=cv2.INTER_NEAREST) > 128
    rows = np.where(mask.any(1))[0]; top, bottom = rows.min(), rows.max()
    wide = cv2.dilate(mask.astype(np.uint8), np.ones((21, 21), np.uint8)) > 0      # a narrow ring: the ground the object stands on
    close = cv2.dilate(mask.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    ring = wide & ~close & (ys > top + 0.6 * (bottom - top))                # around and below the lower part
    px, py, pz = X[ring], Y[ring], Z[ring]
    keep = np.ones(len(px), bool)
    for _ in range(6):                                                       # fit, drop the worst, fit again
        A = np.stack([px[keep], pz[keep], np.ones(keep.sum())], 1)
        plane, *_ = np.linalg.lstsq(A, py[keep], rcond=None)
        error = np.abs(px * plane[0] + pz * plane[1] + plane[2] - py)
        keep = error < max(0.05, np.percentile(error[keep], 70))
    if abs(plane[0]) > 0.15:                                                 # a steep sideways tilt means the ring caught a kerb: keep it level across
        A = np.stack([pz[keep], np.ones(keep.sum())], 1)
        (b0, c0), *_ = np.linalg.lstsq(A, py[keep], rcond=None)
        plane = np.array([0.0, b0, c0])
    a, b, c = (float(x) for x in plane)
    obj['ground'] = [round(a, 5), round(b, 5), round(c, 5)]
    # the floor inside the mask: where each pixel's line of sight meets that ground
    denominator = ry - a * rx + b                                          # the ray (rx d, ry d, -d) meets y = a x + b z + c where d = c / denominator
    with np.errstate(divide='ignore', invalid='ignore'):
        d = np.where(np.abs(denominator) > 1e-6, c / denominator, -1)
    ok = mask & (d > near) & (d < far)
    clean[ok] = np.clip((1 / d[ok] - 1 / far) / (1 / near - 1 / far), 0, 1)
    print(f"{obj['name']}: ground height {c:+.2f} under the camera, slope across {a:+.3f}, slope in depth {b:+.3f}, from {keep.sum()} ground points; floor set on {ok.sum()} depth pixels")
cv2.imwrite(clean_depth, np.round(clean * 255).astype(np.uint8))
json.dump(layout, open(layout_path, 'w'), indent=1)
