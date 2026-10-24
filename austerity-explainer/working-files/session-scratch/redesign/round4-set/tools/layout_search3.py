# What this does: the layout search with the stooped man on the brazier's corner side. Scratch tool for round 4.
import itertools, sys
sys.path.insert(0, sys.argv[1])
from layout_search2 import evaluate
best = []
men_y = [20.6, 19.5, 18.4, 17.3, 16.2]
for camx, bx, px, dx, dy, x3, x7, zig, x1 in itertools.product([-3.9, -3.8, -3.7], [-5.5, -5.35, -5.2], [-4.75, -4.6, -4.45, -4.3], [-4.15, -4.0, -3.85, -3.7],
                                                               [20.9, 21.1, 21.3], [-3.3, -3.2, -3.1], [-2.9, -2.8, -2.7], [0.0, 0.12, 0.2], [-2.5, -2.7, -2.9]):
    things = {'brazier': (bx, 21.55, 0.297, 0.856), 'man2': (bx - 0.5, 21.35, 0.3, 1.35), 'petrol': (px, 21.5, 0.304, 0.88),
              'diesel': (dx, dy, 0.304, 0.88), 'man1': (x1, 21.86, 0.3, 1.79)}
    for k, y in enumerate(men_y):
        x = x3 + (x7 - x3) * k / 4 + (zig if k % 2 else -zig) * (1 if k else 0.5)
        things[f'man{k + 3}'] = (x, y, 0.28, 1.74)
    s, bad = evaluate(camx, things, {'petrol', 'diesel'})
    bad = [b for b in bad if not b.startswith('W1 man2') and not b.startswith('W1p man2')]   # he is half behind the corner
    best.append(((s, -len(bad)), (camx, bx, px, dx, dy, x3, x7, zig, x1), bad))
best.sort(key=lambda b: b[0], reverse=True)
for b in best[:5]:
    print(b[0], b[1]); print('   ', len(b[2]), b[2])
