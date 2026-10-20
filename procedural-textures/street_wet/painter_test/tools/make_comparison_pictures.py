"""What this file does (plain words): makes the pictures that compare, side by side, the wet plate | the new wet painting | the existing dry
lockout painting: the whole picture and several 100% close-ups (road near, road far, the gutter, a wall foot, the brazier area).
All three are at the plate's size (1536 x 2730), so one close-up box cuts the same place from each. Writes JPEG files to pictures/.
Run: python3 -I tools/make_comparison_pictures.py
"""
import cv2, numpy as np, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
plate = cv2.imread('proc-work/street_wet/work/r35/main_wet_plate.png')
wet = cv2.imread(P('pictures/wet_painting_lined_up.png'))
dry = cv2.imread('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg')
assert plate.shape == wet.shape == dry.shape, (plate.shape, wet.shape, dry.shape)
names = ['WET PLATE (3D picture)', 'NEW WET PAINTING', 'EXISTING DRY PAINTING']

def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(out, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out

def sheet(box, out_name, scale=1.0):
    x0, y0, x1, y1 = box
    cells = []
    for img, n in zip((plate, wet, dry), names):
        c = img[y0:y1, x0:x1]
        if scale != 1.0:
            c = cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        cells.append(label(c, n))
    gap = np.full((cells[0].shape[0], 6, 3), 255, np.uint8)
    row = np.hstack([cells[0], gap, cells[1], gap, cells[2]])
    cv2.imwrite(P('pictures', out_name), row, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(out_name, row.shape)

sheet((0, 0, 1536, 2730), 'compare_full_picture_three_across.jpg', scale=0.33)
sheet((500, 2300, 1100, 2730), 'compare_crop_road_near_100pct.jpg')
sheet((400, 1700, 1000, 2100), 'compare_crop_road_far_100pct.jpg')
sheet((900, 1800, 1536, 2250), 'compare_crop_right_gutter_100pct.jpg')
sheet((700, 1560, 1300, 2000), 'compare_crop_wall_foot_100pct.jpg')
sheet((850, 1800, 1450, 2400), 'compare_crop_brazier_area_100pct.jpg')
sheet((0, 2050, 600, 2550), 'compare_crop_left_gutter_and_cart_100pct.jpg')
sheet((0, 1150, 450, 1800), 'compare_crop_left_lamp_ladder_100pct.jpg')
sheet((1200, 1850, 1536, 2450), 'compare_crop_right_edge_dustbin_pail_100pct.jpg')
sheet((380, 1350, 980, 1800), 'compare_crop_colliery_gates_100pct.jpg')
