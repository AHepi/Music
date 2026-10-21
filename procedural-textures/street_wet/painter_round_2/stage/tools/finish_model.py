"""What this file does (plain words): a small copy, in Python, of what the film's stage does to a painting after it has been shone onto the 3D set, so the cause of the darkening can be shown with numbers.
The stage's last step (cinema-stage.js, the "finish", about lines 138 to 185 of the film's file) takes the painting's light values (the painting is read as light, not as picture values), then in this order:
  exposure (x 1.0), a filmic curve called ACES (the function aces()), colour saturation (1.0), contrast (1.04 in the lockout scene, 1.05 by default, pivot at 0.5), a cool tint in the shadows and a warm one in the lights
  (tintAmount 0.35), a lift (0.015, adds a little to everything), then it turns the values back into picture values (sRGB), darkens the frame's edges (vignette 0.3) and adds a fine grain (0.035).
This script does the same sums on a painting, so that (1) it can be checked against the picture the stage really drew (does the copy explain the stage?), and (2) each step can be switched off one at a time to see how much of the
darkening it causes. It does not do the soft focus blur, the glow round very bright lights (only values above 0.9 in light terms) or the tiny colour fringe at the edges; they hardly change brightness.
Used by tools/diagnose_darkening.py. Not a film file.
"""
import numpy as np, cv2

W, H = 1080, 1920


def srgb_to_lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# the lockout scene's finishing look (lockout-test.js pose(): exposure 1.0, contrast 1.04, vignette 0.3, glow 0.6) over the stage's defaults (DEFAULT_LOOK)
LOCKOUT_LOOK = dict(exposure=1.0, contrast=1.04, saturation=1.0, shadowTint=(0.44, 0.52, 0.56), highlightTint=(0.56, 0.5, 0.42), tintAmount=0.35,
                    vignette=0.3, grain=0.035, lift=0.015, filmic=1.0, toe=0.0)
# filmic = how much of the filmic curve is used at all (1 = the film's, 0 = none); toe = 0 the film's curve, 1 = the curve may lift but never crush (the larger of the curve's value and the plain value)


def vignette_factor(h=H, w=W, vignette=0.3):
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (xx + 0.5) / w - 0.5, (yy + 0.5) / h - 0.5
    edge = smoothstep(0.85, 0.2, np.sqrt((cx * 0.9) ** 2 + cy ** 2) * 1.25)
    return (1 - vignette) + vignette * edge


def finish(painting_srgb01, look=None, grain_seed=0, with_grain=True):
    """painting_srgb01: H x W x 3 picture values 0..1 (the painting as the stage sees it, already cut to the stage's lens). Returns the predicted stage picture values 0..1 (RGB order)."""
    L = dict(LOCKOUT_LOOK)
    if look: L.update(look)
    c = srgb_to_lin(painting_srgb01) * L['exposure']
    a = aces(c)
    a = (1 - L['toe']) * a + L['toe'] * np.maximum(a, c)
    c = (1 - L['filmic']) * c + L['filmic'] * a
    luma = c @ np.array([0.2126, 0.7152, 0.0722])
    c = luma[..., None] + (c - luma[..., None]) * L['saturation']
    c = (c - 0.5) * L['contrast'] + 0.5
    t = L['shadowTint'] + (np.array(L['highlightTint']) - np.array(L['shadowTint'])) * smoothstep(0.05, 0.75, luma)[..., None]
    c = (1 - L['tintAmount']) * c + L['tintAmount'] * (c * t * 2.0)
    c = c + L['lift'] * (1.0 - c)
    c = np.clip(c, 0, 1)
    out = lin_to_srgb(c)
    out = out * vignette_factor(painting_srgb01.shape[0], painting_srgb01.shape[1], L['vignette'])[..., None]
    if with_grain:
        n = np.random.RandomState(grain_seed).rand(*out.shape[:2]) - 0.5
        out = out + (n * L['grain'])[..., None] * (1 - 0.6 * out)
    return np.clip(out, 0, 1)


def lum(img):
    return img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
