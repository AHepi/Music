"""What this file does (plain words): makes the two pictures for the person, in "24 Wet street painting round 2 - pictures/":
  1. the film's stage after the camera has moved, with the film's old DRY behind painting (left) and the new WET behind painting (right), the same front painting in both;
  2. the new front painting, the plate with the near props hidden that the behind painting was painted from, and the new behind painting, side by side.
Both are JPEGs under 400 KB. Run: python3 -I tools/make_pictures_for_the_person.py"""
import os
import cv2
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
OUT = 'proc-work/24 Wet street painting round 2 - pictures/'
os.makedirs(OUT, exist_ok=True)

def titled(img, text, h=34):
    bar = np.full((h, img.shape[1], 3), 24, np.uint8)
    cv2.putText(bar, text, (8, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (235, 235, 235), 1, cv2.LINE_AA)
    return np.vstack([bar, img])

def save_under(path, img, limit=395000):
    for q in (86, 82, 78, 74, 70, 66, 60):
        cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, q])
        if os.path.getsize(path) < limit:
            break
    print(os.path.basename(path), os.path.getsize(path), 'bytes, quality', q, img.shape)

a = cv2.imread(P('stage/stills/r2_moved_drybehind/still-6.00.jpg'))
b = cv2.imread(P('stage/stills/r2_moved_wetbehind/still-6.00.jpg'))
s = [cv2.resize(i, (560, 996), interpolation=cv2.INTER_AREA) for i in (a, b)]
img = np.hstack([titled(s[0], "Film's old DRY behind painting (pale, dry ground)"), titled(s[1], 'New WET behind painting (wet, same colours)')])
save_under(OUT + '24 behind painting - old dry vs new wet behind painting in the moved view.jpg', img)

F = cv2.imread(P('../paint/front_painting_final.png')); N = cv2.imread(P('../plate/lockout_plate_wet_round2_no_props.png')); B = cv2.imread(P('../paint/behind_painting_final.png'))
s = [cv2.resize(i, (500, 889), interpolation=cv2.INTER_AREA) for i in (F, N, B)]
img = np.hstack([titled(s[0], 'Front painting (with props)'), titled(s[1], 'Plate, near props hidden'), titled(s[2], 'New wet behind painting')])
save_under(OUT + '24 behind painting - front painting, plate without props and behind painting.jpg', img)
