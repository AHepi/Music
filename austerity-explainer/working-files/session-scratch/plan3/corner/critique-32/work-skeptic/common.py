import numpy as np
from PIL import Image
F = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/'
S5 = F + 'composed-end-5.png'; S4 = F + 'composed-end-4.png'
REF = '/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg'
PLATE = F + 'notice-corner-plate-2.png'
IDS = F + 'facts5/ids.png'
def load(p, size=None):
    im = Image.open(p).convert('RGB')
    if size: im = im.resize(size, Image.LANCZOS)
    return np.asarray(im).astype(float) / 255
def luma(a): return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
def box(a, x0, y0, x1, y1):
    h, w = a.shape[:2]
    return a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
import json
FACTS = json.load(open(F + 'facts5/facts.json'))
def mask(name, ids_path=IDS, tol=3):
    ids = np.asarray(Image.open(ids_path).convert('RGB')).astype(int)
    c = np.array(FACTS['groups'][name]['colour'])
    return (np.abs(ids - c).max(-1) <= tol)
def hsv_sat(a):
    mx, mn = a.max(-1), a.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
