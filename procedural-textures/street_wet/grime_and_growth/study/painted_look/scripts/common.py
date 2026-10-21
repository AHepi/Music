"""Shared helpers of the painted-look study (plain: loading pairs, brightness, masks, band filters)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import *
import numpy as np, cv2

W, H = 1536, 2730

def load_rgb(path, size=(W, H)):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None: raise IOError(path)
    if (im.shape[1], im.shape[0]) != size:
        im = cv2.resize(im, size, interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

def lum(rgb):
    """picture brightness 0..1 (Rec.709 weights on the stored sRGB numbers, as the earlier tests did)."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]

def srgb_to_lin(v):
    v = np.asarray(v, dtype=np.float64)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

def lin_to_srgb(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)

SURF = SW + "/painter_test/alignment/facts_surfaces"
FACTS = SW + "/painter_test/alignment/facts"
def lockout_masks(size=(W, H)):
    """Blender-made VISIBLE-surface masks of the lockout camera (road, pavement, gutter, kerb, walls, roofs, props ...) at plate size, plus sky.
    (The earlier 'solo' pictures draw each group alone, so they include ground hidden behind props; the colour-coded ids.png does not.)"""
    facts = json.load(open(f"{SURF}/facts.json"))
    ids = cv2.cvtColor(cv2.imread(f"{SURF}/ids.png"), cv2.COLOR_BGR2RGB).astype(np.int32)
    out = {}
    for g, info in facts['groups'].items():
        m = (np.abs(ids - np.array(info['colour'])).sum(axis=2) < 24).astype(np.uint8)
        out[g] = cv2.resize(m, size, interpolation=cv2.INTER_NEAREST) > 0
    ids2 = cv2.cvtColor(cv2.imread(f"{FACTS}/ids.png"), cv2.COLOR_BGR2RGB)
    sky = (ids2.astype(np.int32).sum(axis=2) < 24).astype(np.uint8)
    out["sky"] = cv2.resize(sky, size, interpolation=cv2.INTER_NEAREST) > 0
    return out

def erode(m, n=5):
    return cv2.erode(m.astype(np.uint8), np.ones((n, n), np.uint8)) > 0

def gauss(a, s):
    return cv2.GaussianBlur(a, (0, 0), s, borderType=cv2.BORDER_REFLECT)

def dog(a, s):
    """band-pass: blur at s minus blur at 1.6 s (picks features about 2.4 s wide)."""
    return gauss(a, s) - gauss(a, 1.6 * s)
