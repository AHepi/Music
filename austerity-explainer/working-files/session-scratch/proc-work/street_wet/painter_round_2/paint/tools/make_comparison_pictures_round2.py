"""What this file does (plain words): makes the look-by-eye comparison pictures for the round 2 front painting: the NEW PLATE | the ROUND 2 PAINTING (final) | the FIRST TEST's
painting, side by side; the whole picture and 100 percent close-ups of the same places as the first test, plus the lamps and the sky. All at the plate's size (1536 x 2730), so one box cuts
the same place from each. Writes JPEG files to pictures_look/ (working copies; the ones worth showing are copied to the person's folder).
Run: python3 -I tools/make_comparison_pictures_round2.py
"""
import cv2, numpy as np, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
plate = cv2.imread(ROOT + 'painter_round_2/plate/lockout_plate_wet_round2.png')
new = cv2.imread(P('front_painting_final.png'))
ret = cv2.imread(P('front_painting_lined_up.png'))
t1 = cv2.imread(ROOT + 'painter_test/pictures/wet_painting_lined_up.png')
assert plate.shape == new.shape == t1.shape == ret.shape
names = ['PLATE (round 2)', 'ROUND 2 PAINTING (final)', 'FIRST TEST PAINTING']
os.makedirs(P('pictures_look'), exist_ok=True)

def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(out, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out

def sheet(box, out_name, scale=1.0, quality=88, imgs=None, labels=None):
    imgs = imgs or (plate, new, t1); labels = labels or names
    x0, y0, x1, y1 = box
    cells = []
    for img, n in zip(imgs, labels):
        c = img[y0:y1, x0:x1]
        if scale != 1.0:
            c = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        cells.append(label(c, n))
    gap = np.full((cells[0].shape[0], 6, 3), 255, np.uint8)
    row = cells[0]
    for c in cells[1:]:
        row = np.hstack([row, gap, c])
    cv2.imwrite(P('pictures_look', out_name), row, [cv2.IMWRITE_JPEG_QUALITY, quality])
    print(out_name, row.shape, os.path.getsize(P('pictures_look', out_name)) // 1024, 'KB')

sheet((0, 0, 1536, 2730), 'full_picture_three_across.jpg', scale=0.33)
sheet((500, 2300, 1100, 2730), 'crop_road_near_100pct.jpg')
sheet((400, 1700, 1000, 2100), 'crop_road_far_100pct.jpg')
sheet((900, 1800, 1536, 2250), 'crop_right_gutter_100pct.jpg')
sheet((700, 1560, 1300, 2000), 'crop_wall_foot_100pct.jpg')
sheet((850, 1800, 1450, 2400), 'crop_brazier_area_100pct.jpg')
sheet((0, 2050, 600, 2550), 'crop_left_gutter_and_cart_100pct.jpg')
sheet((0, 1150, 450, 1800), 'crop_left_lamp_ladder_100pct.jpg')
sheet((1200, 1850, 1536, 2450), 'crop_right_edge_dustbin_pail_100pct.jpg')
sheet((380, 1350, 980, 1800), 'crop_colliery_gates_100pct.jpg')
sheet((0, 0, 1536, 1300), 'sky_top_half_quarter.jpg', scale=0.4, imgs=(plate, ret, new), labels=['PLATE', 'PAINTING AS RETURNED', 'FINAL (free dark sky)'])
sheet((100, 1550, 500, 1750), 'crop_lamp_left_head_100pct.jpg', scale=2.0)
sheet((300, 2150, 900, 2650), 'crop_sacks_100pct.jpg')
