# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Small helpers (plain Python with OpenCV and numpy) that put pictures side by side with a caption above each, for looking: used to make the sheets and the quick comparisons.
# Use: import sheet_tools as st; st.save('out.jpg', st.row([('caption', 'path or array'), ...], height=700), quality=90)
import cv2
import numpy as np

BG = (22, 22, 24)
FONT = cv2.FONT_HERSHEY_SIMPLEX


def load(item):
    return cv2.imread(item) if isinstance(item, str) else item


def caption(img, text, height=34, scale=0.62, colour=(215, 225, 245), sub=None):
    h, w = img.shape[:2]
    bar = np.full((height + (22 if sub else 0), w, 3), BG, np.uint8)
    cv2.putText(bar, text, (8, 24), FONT, scale, colour, 1, cv2.LINE_AA)
    if sub:
        cv2.putText(bar, sub, (8, 44), FONT, 0.46, (150, 160, 175), 1, cv2.LINE_AA)
    return np.vstack([bar, img])


def fit(img, height=None, width=None):
    h, w = img.shape[:2]
    if height:
        return cv2.resize(img, (int(round(w * height / h)), height), interpolation=cv2.INTER_AREA if height < h else cv2.INTER_CUBIC)
    return cv2.resize(img, (width, int(round(h * width / w))), interpolation=cv2.INTER_AREA if width < w else cv2.INTER_CUBIC)


def row(items, height=700, gap=8, crop=None):
    """items: [(caption, picture), ...] or [(caption, picture, sub caption)]; every picture scaled to the same height; crop = (x0, y0, x1, y1) in fractions of the picture."""
    tiles = []
    for item in items:
        text, pic = item[0], load(item[1])
        sub = item[2] if len(item) > 2 else None
        if crop:
            h, w = pic.shape[:2]
            pic = pic[int(crop[1] * h):int(crop[3] * h), int(crop[0] * w):int(crop[2] * w)]
        tiles.append(caption(fit(pic, height=height), text, sub=sub))
    heights = max(t.shape[0] for t in tiles)
    padded = []
    for i, t in enumerate(tiles):
        pad = np.full((heights - t.shape[0], t.shape[1], 3), BG, np.uint8)
        padded.append(np.vstack([t, pad]))
        if i < len(tiles) - 1:
            padded.append(np.full((heights, gap, 3), BG, np.uint8))
    return np.hstack(padded)


def stack(rows, gap=8, title=None):
    width = max(r.shape[1] for r in rows)
    out = []
    if title:
        bar = np.full((40, width, 3), BG, np.uint8)
        cv2.putText(bar, title, (8, 28), FONT, 0.8, (240, 230, 190), 2, cv2.LINE_AA)
        out.append(bar)
    for r in rows:
        if r.shape[1] < width:
            r = np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), BG, np.uint8)])
        out.append(r)
        out.append(np.full((gap, width, 3), BG, np.uint8))
    return np.vstack(out)


def save(path, img, quality=90, max_width=None):
    if max_width and img.shape[1] > max_width:
        img = fit(img, width=max_width)
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
