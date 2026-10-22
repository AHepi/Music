# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SHEETS of the growth layer (plain Python): contact sheets for the person, every one a JPG under 400 KB.
#     before_after(work, baseline, out)     close views dry and wet and a spot of the gutter without and with the plants, and a crop of the main plate at 100 % without and with
#     dials_sheet(folder, out)              what each main dial does: the same close view with one dial changed at a time, labelled
#     pieces_sheet(gallery_folder, close_pair, out)   the piece library (dry and wet, at real size) above a real close view dry and wet
#     plate_crop(plate_with, out, mask)     the plate at 100 % around the densest group of plants
#     thin_rubbish(spot_pictures, out)      weeds through thin rubbish and none on the heaps
# Used by the work scripts; the pictures it writes are named "25 Growth - ..." by the caller.
import os

import cv2
import numpy as np

FONT = cv2.FONT_HERSHEY_SIMPLEX


def read(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    return im


def fit(im, width=None, height=None):
    h, w = im.shape[:2]
    if width:
        return cv2.resize(im, (width, int(round(h * width / w))), interpolation=cv2.INTER_AREA if width < w else cv2.INTER_CUBIC)
    return cv2.resize(im, (int(round(w * height / h)), height), interpolation=cv2.INTER_AREA if height < h else cv2.INTER_CUBIC)


def label(im, text, size=0.6, pad=26):
    band = np.full((pad, im.shape[1], 3), 28, np.uint8)
    cv2.putText(band, text, (8, pad - 8), FONT, size, (235, 235, 235), 1, cv2.LINE_AA)
    return np.concatenate([band, im], axis=0)


def hstack(images, gap=6):
    h = max(i.shape[0] for i in images)
    pad = [np.pad(i, ((0, h - i.shape[0]), (0, 0), (0, 0)), constant_values=28) for i in images]
    out = []
    for p in pad:
        out += [p, np.full((h, gap, 3), 28, np.uint8)]
    return np.concatenate(out[:-1], axis=1)


def vstack(images, gap=6):
    w = max(i.shape[1] for i in images)
    pad = [np.pad(i, ((0, 0), (0, w - i.shape[1]), (0, 0)), constant_values=28) for i in images]
    out = []
    for p in pad:
        out += [p, np.full((gap, w, 3), 28, np.uint8)]
    return np.concatenate(out[:-1], axis=0)


def title_band(width, lines, height=None):
    height = height or (22 * len(lines) + 12)
    band = np.full((height, width, 3), 20, np.uint8)
    for i, line in enumerate(lines):
        cv2.putText(band, line, (10, 24 + 22 * i), FONT, 0.55, (240, 240, 240), 1, cv2.LINE_AA)
    return band


def save_jpg(path, im, max_kb=385):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    quality, scale = 86, 1.0
    while True:
        cur = im if scale == 1.0 else cv2.resize(im, (int(im.shape[1] * scale), int(im.shape[0] * scale)), interpolation=cv2.INTER_AREA)
        cv2.imwrite(path, cur, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if os.path.getsize(path) <= max_kb * 1024:
            return os.path.getsize(path)
        if quality > 60:
            quality -= 6
        else:
            scale *= 0.9


def before_after(pairs, out, title_lines):
    """pairs: [(label_before, image_before, label_after, image_after)], all images already cropped; two columns."""
    rows = []
    for lb, ib, la, ia in pairs:
        w = 640
        rows.append(hstack([label(fit(ib, w), lb), label(fit(ia, w), la)]))
    sheet = vstack([title_band(rows[0].shape[1], title_lines)] + rows)
    return save_jpg(out, sheet)


def dials_sheet(items, out, title_lines, columns=3, cell=360):
    """items: [(label, image)]"""
    cells = [label(fit(im, cell), text, 0.5, 22) for text, im in items]
    rows = []
    for i in range(0, len(cells), columns):
        row = cells[i:i + columns]
        while len(row) < columns:
            row.append(np.full_like(cells[0], 28))
        rows.append(hstack(row, 4))
    sheet = vstack([title_band(rows[0].shape[1], title_lines)] + rows, 4)
    return save_jpg(out, sheet)


def plate_crop(plate_path, mask_path, out, size=(1000, 760), title=None, mask_channel=2):
    plate = read(plate_path)
    m = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
    mask = (m[..., mask_channel] > 127).astype(np.float32) if m.ndim == 3 else (m > 127).astype(np.float32)
    best, at = -1.0, (0, 0)
    h, w = mask.shape
    integral = cv2.integral(mask)
    ch, cw = size[1], size[0]
    for y in range(0, h - ch, 40):
        for x in range(0, w - cw if w > cw else 1, 40):
            s = integral[y + ch, x + cw] - integral[y, x + cw] - integral[y + ch, x] + integral[y, x]
            if s > best:
                best, at = s, (x, y)
    x, y = at
    crop = plate[y:y + ch, x:x + cw]
    if title:
        crop = label(crop, title)
    return save_jpg(out, crop), at
