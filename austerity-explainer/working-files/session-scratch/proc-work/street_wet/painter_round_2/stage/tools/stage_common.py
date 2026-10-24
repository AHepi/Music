"""What this file does (plain words): small helpers shared by this step's measuring scripts: cutting a plate-sized picture to the stage's narrower lens, reading Blender's surface masks (road, pavement, walls ...)
from the first painter test's folder (read only), and reading pictures as brightness 0..1. Not a film file."""
import json, os
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
W, H = 1080, 1920
TEST1 = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_test/'
FILM = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
k = np.tan(np.radians(20)) / np.tan(np.radians(22))     # the stage's lens (40 deg) sees the middle 90.1 % of the plate's (44 deg)


def central(img, interp=cv2.INTER_AREA):
    h, w = img.shape[:2]; ch, cw = int(round(h * k)), int(round(w * k)); y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=interp)


def central_mask(m):
    h, w = m.shape; ch, cw = int(round(h * k)), int(round(w * k)); y0, x0 = (h - ch) // 2, (w - cw) // 2
    return cv2.resize(m[y0:y0 + ch, x0:x0 + cw].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0


def masks(folder):
    f = json.load(open(folder + 'facts.json'))
    ids = cv2.cvtColor(cv2.imread(folder + 'ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: (np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24) for g, i in f['groups'].items()}


er = lambda m, n=4: cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0


def load01(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB).astype(np.float64) / 255


stage01 = load01
