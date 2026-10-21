# What this file does (plain words): makes the pictures for the person from the finished plate work: (1) chips and gutter, before and after (three 100 % crops); (2) the middle-distance joints, before and after;
# (3) the full-size wet plate and its props-free twin side by side at a quarter of full size. JPEG files, each under 400 KB, written into the "24 Wet street painting round 2 - pictures" folder.
import cv2, numpy as np, os
S = 'proc-work/'
OLD = S + 'street_wet/relief_and_rubbish/rubbish/work/plates02/'
NEW = S + 'street_wet/painter_round_2/plate/rubbish/work/plates04/'
OUT = S + '24 Wet street painting round 2 - pictures/'
FINAL = S + 'street_wet/painter_round_2/plate/'
def crop(path, x0, y0, w, h, scale=1.0):
    im = cv2.imread(path)[y0:y0 + h, x0:x0 + w]
    return cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA) if scale != 1 else im
def label(im, text):
    bar = np.full((26, im.shape[1], 3), 24, np.uint8)
    cv2.putText(bar, text, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (235, 235, 235), 1, cv2.LINE_AA)
    return np.vstack([bar, im])
def pair(a, b, ta, tb):
    gap = np.full((a.shape[0] + 26, 6, 3), 24, np.uint8)
    return np.hstack([label(a, ta), gap, label(b, tb)])
def save(im, name, q=84, limit=390 * 1024):
    path = OUT + name
    while True:
        cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, q])
        if os.path.getsize(path) <= limit or q <= 50:
            break
        q -= 4
    print(name, im.shape, os.path.getsize(path) // 1024, 'KB, quality', q)
# 1. chips and gutter
r1 = pair(crop(OLD + 'plate_lockout_B_dry_rubbish.jpg', 760, 1930, 700, 420), crop(NEW + 'plate_lockout_B_dry_rubbish.jpg', 760, 1930, 700, 420), 'chips by the sacks, dry lockout plate, 100 %: BEFORE (round 1)', 'AFTER (round 2 fixes)')
r2 = pair(crop(OLD + 'plate_main_A_wet_rubbish.jpg', 1000, 1640, 536, 440, 1.3), crop(NEW + 'plate_main_A_wet_rubbish.jpg', 1000, 1640, 536, 440, 1.3), 'right gutter and kerb, wet street plate, 130 %: BEFORE', 'AFTER')
w = max(r1.shape[1], r2.shape[1])
def padw(x):
    return np.hstack([x, np.full((x.shape[0], w - x.shape[1], 3), 24, np.uint8)]) if x.shape[1] < w else x
sheet = np.vstack([padw(r1), np.full((6, w, 3), 24, np.uint8), padw(r2)])
save(sheet, '24 plate - chips and gutter before and after.jpg')
# 2. joints in the middle distance and near
r1 = pair(crop(OLD + 'plate_main_A_wet_rubbish.jpg', 420, 1720, 330, 380, 2.0), crop(NEW + 'plate_main_A_wet_rubbish.jpg', 420, 1720, 330, 380, 2.0), 'middle distance of the wet street plate, 200 %: BEFORE', 'AFTER (no bright hooked ticks)')
r2 = pair(crop(OLD + 'plate_main_A_wet_rubbish.jpg', 300, 2300, 330, 380, 2.0), crop(NEW + 'plate_main_A_wet_rubbish.jpg', 300, 2300, 330, 380, 2.0), 'nearer, 200 %: BEFORE', 'AFTER (stones still stand up)')
save(np.vstack([r1, np.full((6, r1.shape[1], 3), 24, np.uint8), r2]), '24 plate - sett joints in the middle distance before and after.jpg')
# 3. the two full plates
a = cv2.imread(FINAL + 'lockout_plate_wet_round2.png'); b = cv2.imread(FINAL + 'lockout_plate_wet_round2_no_props.png')
f = 0.25
a, b = [cv2.resize(x, None, fx=f, fy=f, interpolation=cv2.INTER_AREA) for x in (a, b)]
save(pair(a, b, 'wet lockout plate (1536 x 2730), a quarter size', 'same view with the near props hidden'), '24 plate - full plate and props-free plate quarter size.jpg')
