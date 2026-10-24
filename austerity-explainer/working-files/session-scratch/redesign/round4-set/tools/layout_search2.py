# What this does: like layout_search.py, with W1's camera spot across the pavement as a choice too, the house
# corner's sightline (things left of it are hidden from W1), and the queue as a diagonal with a small zigzag.
# Scratch tool for round 4.
import itertools, math
T = math.tan(math.radians(30.2)); PT = math.tan(math.radians(32.2)); A = 1080 / 1920; G = 0.155
def box(cam, tan, x, y, r, h):
    cx, cy, cz = cam; d = y - cy
    return (0.5 + 0.5 * (x - r - cx) / (d * tan * A), 0.5 - 0.5 * (G + h - cz) / (d * tan),
            0.5 + 0.5 * (x + r - cx) / (d * tan * A), 0.5 - 0.5 * (G - cz) / (d * tan), d)
def corner_ok(cam, x, y, r):
    cx, cy, _ = cam
    limit = cx + (-5.2 - cx) * (y - cy) / (18.0 - cy)      # the terrace's end hides what is left of this
    return x - r > limit + 0.02
def evaluate(camx, things, words, verbose=False):
    cams = {'W1': ((camx, 10.2, 1.841), T), 'W1p': ((camx, 9.0, 1.841), PT), 'W3': ((0.0, -7.95, 5.74), T)}
    worst = 99; bad = []
    for cname, (cam, tan) in cams.items():
        boxes = {n: box(cam, tan, *v) for n, v in things.items()}
        if cname.startswith('W1'):
            for w in words:
                if not corner_ok(cam, things[w][0], things[w][1], things[w][2]):
                    bad.append(f'{cname} {w} behind corner'); worst = min(worst, -60)
            for n, v in things.items():
                if n.startswith('man') and n not in ('man1', 'man2') and abs(v[1] - cam[1]) < 5.95:
                    bad.append(f'{cname} {n} too near'); worst = min(worst, -60)
            for n in things:
                b = boxes[n]
                if n not in ('man2',) and b[2] > 0.95:
                    bad.append(f'{cname} {n} past 0.95'); worst = min(worst, -30)
        names = list(boxes)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                A_, B_ = boxes[a], boxes[b]
                if min(A_[3], B_[3]) - max(A_[1], B_[1]) <= 0.005: continue
                gap = (max(A_[0], B_[0]) - min(A_[2], B_[2])) * 1080
                near, far = (a, b) if A_[4] < B_[4] else (b, a)
                if cname.startswith('W1') and far in words and gap < 0:
                    F = boxes[far]; N = boxes[near]
                    mid = (F[0] + 0.15 * (F[2] - F[0]), F[2] - 0.15 * (F[2] - F[0]))
                    if N[0] < mid[1] and N[2] > mid[0] and N[1] < F[3] - 0.25 * (F[3] - F[1]):
                        bad.append(f'{cname} {near} hides {far} word'); worst = min(worst, -50)
                if far == 'brazier' and gap < -12 and near != 'man2':
                    F = boxes[far]; N = boxes[near]
                    if N[1] < F[1] + 0.3 * (F[3] - F[1]):
                        bad.append(f'{cname} {near} hides brazier'); worst = min(worst, -50)
                if -15 < gap < 18:
                    m = min(gap + 15, 18 - gap)
                    worst = min(worst, -m); bad.append(f'{cname} {a}/{b} {gap:.0f}')
    return worst, bad
if __name__ == '__main__':
    best = None
    men_y = [20.6, 19.5, 18.4, 17.3, 16.2]
    for camx, bx, px, dx, dy, x3, x7, zig, x1 in itertools.product([-3.9, -3.8, -3.7], [-5.6, -5.45, -5.3], [-4.95, -4.8, -4.65], [-4.35, -4.2, -4.05],
                                                                   [21.0, 21.25], [-3.3, -3.2, -3.1], [-2.9, -2.8, -2.7], [0.0, 0.12, 0.2], [-2.75, -2.9]):
        things = {'brazier': (bx, 21.55, 0.297, 0.856), 'man2': (bx + 0.49, 21.06, 0.3, 1.35), 'petrol': (px, 21.5, 0.304, 0.88),
                  'diesel': (dx, dy, 0.304, 0.88), 'man1': (x1, 21.86, 0.3, 1.79)}
        for k, y in enumerate(men_y):
            x = x3 + (x7 - x3) * k / 4 + (zig if k % 2 else -zig) * (1 if k not in (0,) else 0.5)
            things[f'man{k + 3}'] = (x, y, 0.28, 1.74)
        s, bad = evaluate(camx, things, {'petrol', 'diesel'})
        key = (s, -len(bad))
        if best is None or key > best[0]:
            best = (key, (camx, bx, px, dx, dy, x3, x7, zig, x1), bad)
    print(best[0], best[1]); print(len(best[2]), best[2])
