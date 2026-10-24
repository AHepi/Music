import json, os, sys
import cv2, numpy as np
def make(facts_path, out):
    facts = json.load(open(facts_path))
    w, h = facts['size']
    os.makedirs(os.path.join(out, 'solo'), exist_ok=True)
    ids = np.zeros((h, w, 3), np.uint8)
    for name, g in sorted(facts['groups'].items(), key=lambda kv: -kv[1]['distance']):
        l, t, r, b = g['screen_box_unclipped']
        box = (int(round(l * w)), int(round(t * h)), int(round(r * w)) - 1, int(round(b * h)) - 1)
        r_, g_, b_ = g['colour']
        cv2.rectangle(ids, box[:2], box[2:], (b_, g_, r_), -1)
        solo = np.zeros((h, w, 3), np.uint8)
        cv2.rectangle(solo, box[:2], box[2:], (255, 255, 255), -1)
        cv2.imwrite(os.path.join(out, 'solo', f'{name}.png'), solo)
    cv2.imwrite(os.path.join(out, 'ids.png'), ids)
    json.dump(facts, open(os.path.join(out, 'facts.json'), 'w'), indent=1)
make(sys.argv[1], sys.argv[2])
