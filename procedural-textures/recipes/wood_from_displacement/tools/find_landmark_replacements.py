# What this does (plain words): for every LANDMARK of the uploaded wood maps (a place so recognisable that a person notices when it comes back: the knots, the zigzag
# cracks, the orange splinters, the dark hole, the big rust cloud ...) it looks for a clean piece of plain grain somewhere else in the map whose edge matches the landmark's
# surroundings best. The recipe (recipe/wood_from_maps_recipe.py, frame "4 LANDMARKS") then paints the landmark out of every window by default, by reading the
# map a second time at the shifted place (dx, dy) inside a ragged disc, and only shows the landmark in a board that draws a lucky number.
# This script is the one-off measuring step that found the (dx, dy) numbers now stored in recipe/settings.json under 'landmarks.list'. It reads only the two
# uploaded maps. The landmark places (x, y, radius) were chosen by eye from crops of the four usable rows (see the guide), helped by an automatic
# "which places have no look-alike elsewhere" search that was not decisive (all places of this painted map are about equally unlike each other).
# Rules for a replacement: it must lie in a usable row at about the same height in its row (within 30 percent of the row height), must not touch another landmark or an
# earlier replacement, must be plain (few very dark dots, low contrast), and its ring of dots next to the disc edge must match the original ring best (sum of squared
# differences of height and colour).
# Output: scores/landmarks_replacements.json and sheets/landmarks.jpg (left: the colour map with the landmarks circled and numbered; right: the same map with all
# landmarks painted out, drawn here with numpy to show what the recipe's nodes do).
# Use: python3 -I tools/find_landmark_replacements.py       (numpy and PIL only; about 3 minutes)
import json
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
T = 1254
# name, x, y (dots, y down), radius of the painted-out disc, kind (knot or mark)
LANDMARKS = [('knot K2', 350, 378, 88, 'knot'), ('knot K3', 170, 806, 85, 'knot'), ('knot K4', 832, 893, 72, 'knot'),
             ('zigzag crack R2', 742, 325, 55, 'mark'), ('hook splinter R2', 925, 410, 65, 'mark'), ('rust cloud R3', 600, 540, 100, 'mark'), ('hole R3', 1100, 578, 65, 'mark'),
             ('notch R3', 130, 592, 50, 'mark'), ('splinter R4', 620, 790, 70, 'mark'), ('splinter R5', 880, 1050, 75, 'mark'),
             ('stain cluster R5', 460, 1100, 85, 'mark'), ('rubble R5', 600, 1195, 50, 'mark')]
GAPS = [189, 470, 709, 980, 1254]


def correlate(a, b):
    return np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=a.shape)


def main():
    h = np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'height_as_uploaded.png')).convert('L'), dtype=np.float64) / 255
    c = np.asarray(Image.open(os.path.join(PROC, 'reference', 'wood', 'colour.png')).convert('RGB'), dtype=np.float64) / 255
    feat = np.concatenate([h[..., None], c], -1)
    yy, xx = np.mgrid[0:T, 0:T]
    occupied = np.zeros((T, T), bool)
    for _, x0, y0, r, _ in LANDMARKS:
        occupied |= ((xx - x0) ** 2 + (yy - y0) ** 2) <= (1.2 * r) ** 2

    def row_of(y):
        return next(i for i in range(4) if GAPS[i] <= y < GAPS[i + 1])

    result = []
    for name, x0, y0, r, kind in LANDMARKS:
        d = np.sqrt((xx - x0) ** 2 + (yy - y0) ** 2)
        ring = ((d >= r - 8) & (d <= r + 8)).astype(np.float64)
        tm = np.roll(np.roll(ring, -y0, 0), -x0, 1)
        ssd = np.zeros((T, T))
        for ch in range(4):
            ft = np.roll(np.roll(feat[..., ch] * ring, -y0, 0), -x0, 1)
            fa = feat[..., ch]
            ssd += correlate(fa * fa, tm) - 2 * correlate(fa, ft) + (ft ** 2).sum()
        score = ssd / (ring.sum() * 4)
        integral = np.pad(occupied.astype(np.float64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
        rr = int(r)
        y_lo, y_hi, x_lo, x_hi = np.clip(yy - rr, 0, T), np.clip(yy + rr + 1, 0, T), np.clip(xx - rr, 0, T), np.clip(xx + rr + 1, 0, T)
        busy = integral[y_hi, x_hi] - integral[y_lo, x_hi] - integral[y_hi, x_lo] + integral[y_lo, x_lo]
        row = row_of(y0)
        rel = (y0 - GAPS[row]) / (GAPS[row + 1] - GAPS[row])
        usable = np.zeros((T, T), bool)
        for cr in range(4):
            a, b = GAPS[cr], GAPS[cr + 1]
            lo, hi = max(a + r + 10, a + (b - a) * (rel - 0.3)), min(b - r - 10, a + (b - a) * (rel + 0.3))
            if hi > lo:
                usable[int(lo):int(hi) + 1, :] = True
        valid = usable & (busy == 0) & (((xx - x0) ** 2 + (yy - y0) ** 2) > (2.3 * r) ** 2)
        valid[:, :rr + 8] = False
        valid[:, -rr - 8:] = False
        ranked = np.argsort(np.where(valid, score, 1e9).ravel())[:3000]
        best = None
        for i in ranked:
            cy, cx = divmod(int(i), T)
            inside = feat[cy - rr:cy + rr + 1, cx - rr:cx + rr + 1, 0]
            dist = np.sqrt((np.mgrid[-rr:rr + 1, -rr:rr + 1] ** 2).sum(0))
            inside = inside[dist <= rr]
            if (inside < 0.12).mean() > 0.05 or inside.std() > 0.30:
                continue
            best = (cx, cy, float(score.ravel()[i]), float(inside.std()))
            break
        occupied |= ((xx - best[0]) ** 2 + (yy - best[1]) ** 2) <= (1.3 * r) ** 2
        result.append({'name': name, 'kind': kind, 'x': x0, 'y': y0, 'r': r, 'dx': best[0] - x0, 'dy': best[1] - y0, 'replacement_centre': [best[0], best[1]],
                       'ring_mean_squared_difference': round(best[2], 5), 'replacement_height_spread': round(best[3], 3)})
        print(result[-1], flush=True)
    os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
    with open(os.path.join(BASE, 'scores', 'landmarks_replacements.json'), 'w') as handle:
        json.dump({'what_this_is': 'The landmarks of the uploaded wood maps and the clean replacement place for each, found by tools/find_landmark_replacements.py. These numbers are stored in recipe/settings.json (landmarks.list).', 'landmarks': result}, handle, indent=1)
    # picture: circled, and painted out (ragged edge made with smooth random noise; the recipe uses its own noise nodes)
    rng = np.random.default_rng(1)
    noise = np.asarray(Image.fromarray((rng.random((T // 20 + 3, T // 20 + 3)) * 255).astype(np.uint8)).resize((T, T), Image.BICUBIC), dtype=np.float64) / 255
    out = c.copy()
    for e in result:
        d = np.sqrt((xx - e['x']) ** 2 + (yy - e['y']) ** 2) + (noise - 0.5) * 0.3 * e['r']
        m = np.clip((e['r'] - d) / 2.5 + 0.5, 0, 1)
        xs, ys = np.clip(xx + e['dx'], 0, T - 1), np.clip(yy + e['dy'], 0, T - 1)
        for ch in range(3):
            out[..., ch] = out[..., ch] * (1 - m) + c[ys, xs, ch] * m
    left = Image.fromarray((c * 255).astype(np.uint8))
    draw = ImageDraw.Draw(left)
    for i, e in enumerate(result):
        draw.ellipse((e['x'] - e['r'], e['y'] - e['r'], e['x'] + e['r'], e['y'] + e['r']), outline=(255, 255, 0), width=3)
        draw.text((e['x'] - 5, e['y'] - 6), str(i + 1), fill=(255, 255, 0))
    right = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    sheet = Image.new('RGB', (T * 2 + 20, T), (255, 255, 255))
    sheet.paste(left, (0, 0))
    sheet.paste(right, (T + 20, 0))
    os.makedirs(os.path.join(BASE, 'sheets'), exist_ok=True)
    sheet.resize((1800, int(1800 * T / (2 * T + 20)))).save(os.path.join(BASE, 'sheets', 'landmarks.jpg'), quality=90)


if __name__ == '__main__':
    main()
