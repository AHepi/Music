# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# TEXTURE-SPACE PICTURES: masks that live in a material's own picture coordinates, made from the photo pictures the set's materials already use (settings texture_maps).
# One RGB picture per photo material (the shader reads it with the same texture coordinates as the photo, repeating):
#   R tx_cavity   the hollows of the photo's own relief (mortar lines, stone gaps): a blurred copy of the height picture minus the height, stretched to 0..1
#   G tx_joint    the joint centre-lines (thin dark lines between setts, flags or bricks), soft edges
#   B tx_cell     a random number 0..1 per sett, flag or brick (each cell one number)
# How the joints are found: for a set with a ready joint picture (a 'legacy:' file, the earlier sett joint picture) that picture is reused; otherwise from the photo itself: dark
# thin lines kept only where long straight runs exist (morphological opening along rows and columns), or, for bricks and stone, the low parts of the height picture.
# Cells are the connected pieces between joints, found on a 3 x 3 tiled copy so a flag cut by the picture's edge keeps one number across the seam.
# Needs OpenCV and numpy (no Blender).
import hashlib
import os

import numpy as np


def _hash(label):
    return int.from_bytes(hashlib.md5(f'cell{label}'.encode()).digest()[:8], 'big') / float(1 << 64)


def read_gray(path):
    import cv2
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(path)
    if im.ndim == 3:
        im = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
    if im.dtype == np.uint16:
        return im.astype(np.float32) / 65535.0
    return im.astype(np.float32) / 255.0


def cavity_from_height(height, px_per_m, sigma_m=0.015):
    import cv2
    sigma = max(1.0, sigma_m * px_per_m)
    k = int(sigma * 6) | 1
    wrapped = cv2.copyMakeBorder(height, 64, 64, 64, 64, cv2.BORDER_WRAP)
    blur = cv2.GaussianBlur(wrapped, (k, k), sigma)[64:-64, 64:-64]
    cav = np.maximum(blur - height, 0.0)
    top = np.percentile(cav, 97.0)
    return np.clip(cav / max(top, 1e-6), 0.0, 1.0).astype(np.float32)


def joints_from_lines(colour_gray, px_per_m, line_m=0.35):
    """Thin dark lines kept only where they run straight for at least line_m (flags, tiles)."""
    import cv2
    sigma = max(2.0, 0.04 * px_per_m)
    k = int(sigma * 6) | 1
    wrapped = cv2.copyMakeBorder(colour_gray, 96, 96, 96, 96, cv2.BORDER_WRAP)
    local = cv2.GaussianBlur(wrapped, (k, k), sigma)
    dark = ((local - wrapped) > 0.04).astype(np.uint8)
    length = max(9, int(line_m * px_per_m))
    horizontal = cv2.morphologyEx(dark, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (length, 1)))
    vertical = cv2.morphologyEx(dark, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, length)))
    joint = (horizontal | vertical)
    joint = cv2.dilate(joint, np.ones((3, 3), np.uint8))
    return joint[96:-96, 96:-96].astype(np.uint8)


def joints_from_height(height, low_percentile=22.0):
    import cv2
    t = np.percentile(height, low_percentile)
    return (height < t).astype(np.uint8)


def label_cells(joint_mask, min_pixels=600):
    """A random number per connected piece between joints (3 x 3 tiled so pieces cross the picture's seams); returns float32 0..1."""
    import cv2
    h, w = joint_mask.shape
    solid = (1 - cv2.dilate(joint_mask, np.ones((3, 3), np.uint8))).astype(np.uint8)
    tiled = np.tile(solid, (3, 3))
    count, labels = cv2.connectedComponents(tiled, connectivity=4)
    middle = labels[h:2 * h, w:2 * w]
    out = np.full((h, w), 0.5, np.float32)
    sizes = np.bincount(labels.ravel(), minlength=count)
    lut = np.array([_hash(i) for i in range(count)], np.float32)
    lut[0] = 0.5
    out = lut[middle]
    small = sizes[middle] < min_pixels
    out[small] = 0.5
    return out


def make_material(spec, root, kit_root, size=1024):
    """The three pictures for one photo material. Returns (rgb uint8 (size, size, 3), stats dict). spec: one entry of settings.texture_maps."""
    import cv2
    height = read_gray(os.path.join(root, spec['height']))
    period = float(spec.get('period_m', 1.5))
    px_per_m = height.shape[0] / period
    cavity = cavity_from_height(height, px_per_m)
    joint_picture = spec.get('joint_picture', '')
    kind = spec.get('cells', 'mortar')
    source = 'height'
    if joint_picture.startswith('legacy:'):
        path = os.path.join(kit_root, 'integrate', 'legacy_pinned', 'earlier', 'relief_and_rubbish', joint_picture[len('legacy:'):])
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        red = im[..., 2].astype(np.float32) / (65535.0 if im.dtype == np.uint16 else 255.0)         # OpenCV reads BGR: index 2 is red = joint cavity
        joint_soft = cv2.resize(red, (height.shape[1], height.shape[0]), interpolation=cv2.INTER_AREA)
        joint_mask = (joint_soft > 0.5).astype(np.uint8)
        source = 'earlier joint picture'
    elif kind in ('flags', 'setts'):
        colour = read_gray(os.path.join(root, spec['colour']))
        colour = cv2.resize(colour, (height.shape[1], height.shape[0]), interpolation=cv2.INTER_AREA)
        joint_mask = joints_from_lines(colour, px_per_m)
        joint_soft = cv2.GaussianBlur(joint_mask.astype(np.float32), (5, 5), 1.0)
        source = 'dark straight lines of the colour photo'
    else:
        joint_mask = cv2.morphologyEx((cavity > 0.3).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        joint_soft = cv2.GaussianBlur(joint_mask.astype(np.float32), (5, 5), 1.0)
        source = 'hollows of the height picture (cavity above 0.3, closed)'
    cells = label_cells(joint_mask)
    rgb = np.stack([cavity, np.clip(joint_soft, 0, 1), cells], axis=-1)
    if rgb.shape[0] != size:
        rgb = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)
    n_cells = int(len(np.unique(np.round(cells, 4))))
    stats = dict(period_m=period, joint_share=float(joint_mask.mean()), cells=n_cells, joint_source=source, size=size)
    return (np.clip(rgb, 0, 1) * 255.0 + 0.5).astype(np.uint8), stats
