"""What this file does (plain words): puts the stage pictures side by side: for the plate's own view and the moved view, the film's dry painting against the new wet
painting (and the wet painting used as its own behind picture, and the colour map of what each surface wears). Writes JPEG files to pictures/.
Run: python3 -I tools/make_stage_sheets.py
"""
import cv2, numpy as np, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = lambda n: cv2.imread(os.path.join(HERE, 'stage/stills', n, 'still-6.00.jpg'))
def label(img, text):
    o = img.copy(); cv2.rectangle(o, (0, 0), (o.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(o, text, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA); return o
def row(items, scale=0.5, name=None):
    cells = [label(cv2.resize(i, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), t) for i, t in items]
    gap = np.full((cells[0].shape[0], 6, 3), 255, np.uint8)
    out = cells[0]
    for c in cells[1:]: out = np.hstack([out, gap, c])
    cv2.imwrite(os.path.join(HERE, 'pictures', name), out, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(name, out.shape)
row([(S('dry_projector'), 'PLATE VIEW, film dry painting'), (S('wet_projector'), 'PLATE VIEW, new wet painting')], 0.6, 'stage_plate_view_dry_and_wet.jpg')
row([(S('dry_moved'), 'MOVED VIEW, film dry painting'), (S('wet_moved'), 'MOVED VIEW, wet painting + film dry behind'),
     (S('wetwet_moved'), 'MOVED VIEW, wet painting + wet as behind'), (S('wet_weights'), 'MOVED VIEW, what each surface wears')], 0.42, 'stage_moved_view_four_ways.jpg')
# 100% crops of the moved view's road, dry against wet
d, w, ww = S('dry_moved'), S('wet_moved'), S('wetwet_moved')
box = (0, 1150, 1080, 1920)
row([(d[box[1]:box[3], box[0]:box[2]], 'MOVED, dry'), (w[box[1]:box[3], box[0]:box[2]], 'MOVED, wet + dry behind'), (ww[box[1]:box[3], box[0]:box[2]], 'MOVED, wet + wet behind')], 0.55, 'stage_moved_view_road_close.jpg')
