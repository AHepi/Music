"""What this file does (plain words): makes the three pictures for the person from the round 2 front painting step, as JPEGs under 400 KB, into
"24 Wet street painting round 2 - pictures". (1) plate | painting as returned | painting with the free dark sky (final) | first test's painting, whole picture;
(2) 100 percent close-ups of the road, near and far: plate | final painting | first test's painting; (3) the sky: top half of plate | as returned | final, and 100 percent
close-ups of the roof line, the winding wheels and the rope before and after the free sky swap.
Run: python3 -I tools/make_pictures_for_the_person.py
"""
import cv2, numpy as np, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
ROOT = 'proc-work/'
OUT = ROOT + '24 Wet street painting round 2 - pictures/'
plate = cv2.imread(ROOT + 'street_wet/painter_round_2/plate/lockout_plate_wet_round2.png')
ret = cv2.imread(P('front_painting_lined_up.png'))
fin = cv2.imread(P('front_painting_final.png'))
t1 = cv2.imread(ROOT + 'street_wet/painter_test/pictures/wet_painting_lined_up.png')

def label(img, text):
    out = img.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(out, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out
def across(cells, gap=6):
    g = np.full((cells[0].shape[0], gap, 3), 255, np.uint8)
    row = cells[0]
    for c in cells[1:]:
        row = np.hstack([row, g, c])
    return row
def crop(img, box, scale=1.0):
    x0, y0, x1, y1 = box
    c = img[y0:y1, x0:x1]
    return cv2.resize(c, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC) if scale != 1 else c
def save(img, name, limit=390 * 1024):
    for q in (90, 85, 80, 75, 70, 65, 60):
        ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q])
        if len(buf) <= limit:
            break
    open(OUT + name, 'wb').write(buf.tobytes())
    print(name, img.shape[1], 'x', img.shape[0], len(buf) // 1024, 'KB at quality', q)

# 1 whole picture, four across
s = 0.30
full = across([label(crop(i, (0, 0, 1536, 2730), s), t) for i, t in ((plate, 'PLATE (3D picture)'), (ret, 'PAINTING AS RETURNED'), (fin, 'FINAL (free dark sky)'), (t1, 'FIRST TEST PAINTING'))])
save(full, '24 front painting - plate, painting, final and first test, whole picture.jpg')

# 2 road close-ups, near and far, 100 percent
near = across([label(crop(i, (500, 2300, 1100, 2730)), t) for i, t in ((plate, 'PLATE, road near'), (fin, 'PAINTING (final), road near'), (t1, 'FIRST TEST, road near'))])
far = across([label(crop(i, (400, 1700, 1000, 2100)), t) for i, t in ((plate, 'PLATE, road far'), (fin, 'PAINTING (final), road far'), (t1, 'FIRST TEST, road far'))])
w = max(near.shape[1], far.shape[1])
pad = lambda a: np.pad(a, ((0, 0), (0, w - a.shape[1]), (0, 0)), constant_values=255)
save(np.vstack([pad(near), np.full((6, w, 3), 255, np.uint8), pad(far)]), '24 front painting - road close-ups at 100 percent, near and far.jpg')

# 3 the sky
top = across([label(crop(i, (0, 0, 1536, 1300), 0.38), t) for i, t in ((plate, 'PLATE'), (ret, 'PAINTING AS RETURNED (pale clouds)'), (fin, 'FINAL (free dark plain sky)'))])
edge = across([label(crop(i, (200, 820, 700, 1120)), t) for i, t in ((ret, 'as returned, winding wheels'), (fin, 'final, same place at 100 percent'))] +
              [label(crop(i, (1100, 560, 1400, 860)), t) for i, t in ((fin, 'final, roof line at 100 percent'),)])
w = max(top.shape[1], edge.shape[1])
pad = lambda a: np.pad(a, ((0, 0), (0, w - a.shape[1]), (0, 0)), constant_values=255)
save(np.vstack([pad(top), np.full((6, w, 3), 255, np.uint8), pad(edge)]), '24 front painting - the sky as returned and the free dark sky.jpg')
