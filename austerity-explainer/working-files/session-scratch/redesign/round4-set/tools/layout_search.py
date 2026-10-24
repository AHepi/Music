# What this does: a brute-force search for No. 1's gate group and queue layout that keeps, from W1 (composed and
# plate) and W3, the drums' words clear, the brazier showing, and every pair of neighbours either clearly overlapping
# (>= 15 px) or clearly apart (>= 18 px). Scratch tool for round 4.
import itertools, math
T = math.tan(math.radians(30.2)); PT = math.tan(math.radians(32.2)); A = 1080 / 1920; G = 0.155
cams = {'W1': ((-4.1, 10.2, 1.841), T), 'W1p': ((-4.1, 9.0, 1.841), PT), 'W3': ((0.0, -7.95, 5.74), T)}
def box(cam, tan, x, y, r, h):
    cx, cy, cz = cam; d = y - cy
    return (0.5 + 0.5 * (x - r - cx) / (d * tan * A), 0.5 - 0.5 * (G + h - cz) / (d * tan),
            0.5 + 0.5 * (x + r - cx) / (d * tan * A), 0.5 - 0.5 * (G - cz) / (d * tan), d)
def score(things, words):
    worst = 99; bad = []
    for cname, (cam, tan) in cams.items():
        boxes = {n: box(cam, tan, *v) for n, v in things.items()}
        names = list(boxes)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                A_, B_ = boxes[a], boxes[b]
                if min(A_[3], B_[3]) - max(A_[1], B_[1]) <= 0.005: continue
                gap = (max(A_[0], B_[0]) - min(A_[2], B_[2])) * 1080
                near, far = (a, b) if A_[4] < B_[4] else (b, a)
                # words: a nearer thing may not cover the middle 70% of a drum's width in W1
                if cname.startswith('W1') and far in words and gap < 0:
                    F = boxes[far]; N = boxes[near]
                    mid = (F[0] + 0.15 * (F[2] - F[0]), F[2] - 0.15 * (F[2] - F[0]))
                    if N[0] < mid[1] and N[2] > mid[0] and N[1] < F[3] - 0.25 * (F[3] - F[1]):
                        bad.append(f'{cname} {near} hides {far} word'); worst = min(worst, -50)
                if cname == 'W3' and far == 'brazier' and gap < -10:
                    bad.append(f'W3 {near} hides brazier'); worst = min(worst, -50)
                if -15 < gap < 18:
                    m = min(gap + 15, 18 - gap)
                    worst = min(worst, -m); bad.append(f'{cname} {a}/{b} {gap:.0f}')
    return worst, bad
best = None
men_y = [20.6, 19.5, 18.4, 17.3, 16.2]
for bx, px, dx, dy, xr, xl, x1 in itertools.product([-5.35, -5.2, -5.05], [-4.75, -4.6, -4.45], [-4.15, -4.0, -3.85], [21.0, 21.2],
                                                   [-3.0, -3.1], [-3.3, -3.4, -3.5], [-2.9, -3.0]):
    things = {'brazier': (bx, 21.55, 0.297, 0.856), 'man2': (bx - 0.35, 21.2, 0.3, 1.35), 'petrol': (px, 21.5, 0.304, 0.88),
              'diesel': (dx, dy, 0.304, 0.88), 'man1': (x1, 21.86, 0.3, 1.79)}
    for k, y in enumerate(men_y):
        things[f'man{k + 3}'] = ((xr if k % 2 == 0 else xl), y, 0.28, 1.74)
    s, bad = score(things, {'petrol', 'diesel'})
    if best is None or s > best[0] or (s == best[0] and len(bad) < len(best[2])):
        best = (s, (bx, px, dx, dy, xr, xl, x1), bad)
print(best[0], best[1]); print(len(best[2]), best[2][:30])
