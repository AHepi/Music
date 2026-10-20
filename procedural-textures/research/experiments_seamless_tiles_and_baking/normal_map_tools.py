# What this does: small plain-Python helpers (numpy + cv2, run with `python3 -I`) for reading and judging normal maps and height maps.
# The two jobs a non-programmer cares about:
#   * "Is this normal map OpenGL (Blender) or DirectX?"  -> convention_from_the_map_alone() and convention_from_height()
#   * "How strong is this normal map, expressed as the strength a Sobel filter would need?"  -> sobel_strength_that_matches()
# Picture rows run top to bottom. OpenGL normal map: red points right, green points UP the picture, blue points out. DirectX: green points DOWN.
import cv2
import numpy as np


def load_unit_picture(path):
    """Any PNG as float 0..1 (RGB order for colour pictures, one channel for grey), and its bit depth (8 or 16)."""
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(path)
    bits = 16 if image.dtype == np.uint16 else 8
    image = image.astype(np.float64) / (65535.0 if bits == 16 else 255.0)
    if image.ndim == 3:
        image = image[..., :3][..., ::-1] if image.shape[2] >= 3 else image[..., 0]
    return image, bits


def decode_normal(picture):
    """Picture values 0..1 -> unit-ish vectors -1..1 (x right, y up the picture if OpenGL, z out)."""
    return picture * 2.0 - 1.0


def central_differences(grey):
    """Per-pixel slope of a grey picture with wrap-around: (change per pixel going right, change per pixel going down the picture)."""
    dx = (np.roll(grey, -1, axis=1) - np.roll(grey, 1, axis=1)) / 2.0
    dy_down = (np.roll(grey, -1, axis=0) - np.roll(grey, 1, axis=0)) / 2.0
    return dx, dy_down


def convention_from_the_map_alone(normal_picture):
    """OpenGL or DirectX from the normal map only (no height needed).
    Idea: slopes of a real surface obey  d(slope_x)/d(row) = d(slope_y)/d(column)  up to a sign that depends on the green convention.
    Returns (verdict, score): score near -1 = OpenGL, near +1 = DirectX, near 0 = cannot tell (flat or noisy map).
    This sees only whether green is flipped RELATIVE to red; a map with both red and green flipped (or a raised-versus-sunken height swap)
    looks the same to it."""
    n = decode_normal(normal_picture)
    nz = np.maximum(n[..., 2], 0.05)
    p, q = n[..., 0] / nz, n[..., 1] / nz
    dp_drow = (np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)) / 2.0
    dq_dcol = (np.roll(q, -1, axis=1) - np.roll(q, 1, axis=1)) / 2.0
    a, b = dp_drow.ravel(), dq_dcol.ravel()
    if a.std() < 1e-6 or b.std() < 1e-6:
        return 'cannot tell (map is flat)', 0.0
    score = float(np.corrcoef(a, b)[0, 1])
    if score < -0.25:
        return 'OpenGL (green points up the picture; Blender)', score
    if score > 0.25:
        return 'DirectX (green points down the picture)', score
    return 'cannot tell', score


def convention_from_height(normal_picture, height_grey):
    """OpenGL or DirectX when the matching height map is known: compare the green channel with the height's slope down the picture.
    Returns (verdict, correlation_of_green_with_slope_down, correlation_of_red_with_slope_right)."""
    n = decode_normal(normal_picture)
    dx, dy_down = central_differences(height_grey)
    green = float(np.corrcoef(n[..., 1].ravel(), dy_down.ravel())[0, 1])
    red = float(np.corrcoef(n[..., 0].ravel(), dx.ravel())[0, 1])
    # for a height that rises going down the picture, an OpenGL normal tilts UP the picture, i.e. toward +green: positive correlation
    if green > 0.2:
        verdict = 'OpenGL'
    elif green < -0.2:
        verdict = 'DirectX'
    else:
        verdict = 'cannot tell'
    if red > 0.2:
        verdict += ' (but RED is flipped too: the height may be inverted)'
    return verdict, green, red


def sobel_strength_that_matches(normal_picture, height_grey, opengl=True):
    """Least-squares strength s so that the normal map is about  normalize(-s*dh/dx, +s*dh/dy_down, 1)  with the per-pixel central differences of the height.
    Returns (s_from_red, s_from_green, correlation_red, correlation_green)."""
    n = decode_normal(normal_picture)
    nz = np.maximum(n[..., 2], 0.05)
    p, q = n[..., 0] / nz, n[..., 1] / nz
    dx, dy_down = central_differences(height_grey)
    if not opengl:
        q = -q
    s_red = float(-(p * dx).sum() / max((dx * dx).sum(), 1e-12))
    s_green = float((q * dy_down).sum() / max((dy_down * dy_down).sum(), 1e-12))
    return s_red, s_green, float(np.corrcoef(p.ravel(), dx.ravel())[0, 1]), float(np.corrcoef(q.ravel(), dy_down.ravel())[0, 1])


def sobel_normal(height, strength):
    """Normal map picture 0..1 (OpenGL) from a height picture 0..1 with per-pixel central differences and wrap-around (the same maths as lib/bake_harness.py)."""
    dx, dy_down = central_differences(height)
    nx, ny, nz = -strength * dx, strength * dy_down, np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5


def flip_green(normal_picture):
    flipped = normal_picture.copy()
    flipped[..., 1] = 1.0 - flipped[..., 1]
    return flipped
