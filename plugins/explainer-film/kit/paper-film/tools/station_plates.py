"""What this does: makes the "behind" pictures for the station test of painting 409 (log 23), from
the station proxies (fit_station_proxies.py) and the SAM 3D clean plate (log 22, car and pumps
already painted out):
  - plate P: the clean plate with the two posts also painted out. The kiosk, canopy and island
    wear this picture, so what the camera newly sees behind a post, a pump or the car is wall, not a
    smeared copy of the post.
  - plate Q: plate P with the kiosk and canopy painted out too, and its depth picture with the whole
    station flattened back to what is behind it: the far background (painted room) that stands behind
    every 3D piece, with nothing near and upright left in it to tear.
Painting out here is OpenCV's fill (free): rough, but only thin slivers of it show on short moves.
Use: python3 -I station_plates.py PROXIES.json CLEAN_PLATE.jpg CLEAN_DEPTH.png OUT_FOLDER"""
import json, sys, os
import numpy as np
import cv2

proxies_path, clean_path, depth_path, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)
W, H = 1536, 2736
TAN_Y = np.tan(np.radians(20)); TAN_X = TAN_Y * W / H
def project(p):
    d = -p[2]
    return ((p[0] / d / TAN_X) + 1) / 2 * W, (1 - (p[1] / d / TAN_Y)) / 2 * H
boxes = json.load(open(proxies_path))['boxes']
def silhouette(names, grow):
    mask = np.zeros((H, W), np.uint8)
    for name in names:
        pts = np.array([project(np.array(c)) for c in boxes[name]], np.float32)
        cv2.fillPoly(mask, [cv2.convexHull(pts).astype(np.int32)], 255)
    return cv2.dilate(mask, np.ones((grow, grow), np.uint8))
posts = silhouette(['post_front', 'post_rear'], 23)                     # wide enough to take the posts' soft painted edges
station = silhouette(['post_front', 'post_rear', 'kiosk', 'canopy'], 31)
clean = cv2.imread(clean_path)
plate_p = cv2.inpaint(clean, posts, 9, cv2.INPAINT_TELEA)
cv2.imwrite(f'{out}/409-station-plate-p.jpg', plate_p, [cv2.IMWRITE_JPEG_QUALITY, 93])
plate_q = cv2.inpaint(plate_p, station, 15, cv2.INPAINT_TELEA)
cv2.imwrite(f'{out}/409-station-backdrop.jpg', plate_q, [cv2.IMWRITE_JPEG_QUALITY, 93])
depth = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
small = cv2.resize(station, (depth.shape[1], depth.shape[0]), interpolation=cv2.INTER_NEAREST)
small = cv2.dilate(small, np.ones((15, 15), np.uint8))                   # past the depth picture's blurred edges (about 45 painting pixels)
filled = cv2.inpaint(depth, small, 9, cv2.INPAINT_TELEA)
# behind the station is far away: push the painted-out area back past the kiosk (about 32 units, near 6
# / far 70), or the fill borrows the near forecourt's depth and the painted room comes out in front of
# the 3D kiosk
far_enough = int(round((1 / 32 - 1 / 70) / (1 / 6 - 1 / 70) * 255))
filled[small > 0] = np.minimum(filled[small > 0], far_enough)
cv2.imwrite(f'{out}/409-station-backdrop-depth.png', filled)
cv2.imwrite(f'{out}/mask-posts.png', posts); cv2.imwrite(f'{out}/mask-station.png', station)
sheet = np.concatenate([cv2.resize(x, (W // 3, H // 3)) for x in (plate_p, plate_q, cv2.cvtColor(cv2.resize(cv2.imread(f'{out}/409-station-backdrop-depth.png', 0), (W, H)), cv2.COLOR_GRAY2BGR))], 1)
cv2.imwrite(f'{out}/check-plates.jpg', sheet)
print('posts', int((posts > 0).sum()), 'station', int((station > 0).sum()), 'pixels painted out')
