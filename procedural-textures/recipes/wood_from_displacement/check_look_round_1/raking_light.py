"""
Plain note: the look checker's own low "raking" light picture maker (numpy, not Blender).
Raking light means light that skims across the surface at a low angle, so every bump throws a shadow.
It lights a colour picture using a height picture only: the slope of the height gives the surface direction,
a simple matte lighting rule gives the brightness. The same strength and the same light are used for the
uploaded reference and for the new wood, so the two can be compared fairly. It is not a Blender render.
"""
import sys
import numpy as np
import cv2


def read_height(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a.ndim == 3:
        a = a[:, :, 0]
    a = a.astype(np.float64)
    a /= 65535.0 if a.max() > 255 else 255.0
    return a


def read_colour(path):
    a = cv2.imread(path, cv2.IMREAD_COLOR)[:, :, ::-1].astype(np.float64) / 255.0
    return a


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def light(colour, height, azimuth_deg, elevation_deg, strength=10.0, ambient=0.18):
    # slope with two neighbours (as the project's normal rule does), wrapping at the edges
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
    n = np.stack([-dx * strength * 255 / 4, +dy * strength * 255 / 4, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)
    L = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)])
    lam = np.clip((n * L).sum(-1), 0, 1)
    lam = lam / np.sin(el)       # so flat ground has brightness 1.0
    lin = srgb_to_lin(colour)
    out = lin * (ambient + (1 - ambient) * lam[..., None] * 0.9)
    return lin_to_srgb(out * 1.6)


if __name__ == '__main__':
    colour_path, height_path, out_path, az, el = sys.argv[1:6]
    strength = float(sys.argv[6]) if len(sys.argv) > 6 else 10.0
    c = read_colour(colour_path)
    h = read_height(height_path)
    if h.shape != c.shape[:2]:
        h = cv2.resize(h, (c.shape[1], c.shape[0]), interpolation=cv2.INTER_AREA)
    img = light(c, h, float(az), float(el), strength)
    cv2.imwrite(out_path, (img[:, :, ::-1] * 255 + 0.5).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])
