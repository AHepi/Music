import numpy as np, sys
def islands(co, cell=0.35):
    keys = np.floor(co[:, :2] / cell).astype(int)
    cells = {}
    for i, k in enumerate(map(tuple, keys)):
        cells.setdefault(k, []).append(i)
    seen, out = set(), []
    for k in cells:
        if k in seen: continue
        stack, comp = [k], []
        seen.add(k)
        while stack:
            c = stack.pop(); comp.extend(cells[c])
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (c[0] + dx, c[1] + dy)
                    if n in cells and n not in seen:
                        seen.add(n); stack.append(n)
        p = co[comp]
        out.append((p[:, 0].mean(), p[:, 1].mean(), p[:, 2].mean(), np.ptp(p[:, 0]), np.ptp(p[:, 1])))
    return out
r = {}
for ps in (1, 2):
    d = np.load('pud_p%d.npz' % ps)
    r[ps] = {}
    for k in d.files:
        if k.startswith('puddles_') or k == 'yard_901_water':
            r[ps][k] = islands(d[k])
            print(ps, k, len(r[ps][k]))
# match pass-1 islands to pass-2 islands within the clearing
for k in r[1]:
    print('==', k)
    for a in sorted(r[1][k], key=lambda t: t[0]):
        if abs(a[0]) > 55 or abs(a[1] - 6) > 60: continue
        best = min(r[2].get(k, []), key=lambda b: (a[0]-b[0])**2 + (a[1]-b[1])**2) if r[2].get(k) else None
        dist = ((a[0]-best[0])**2 + (a[1]-best[1])**2) ** 0.5 if best else 99
        print('  p1 (%.1f,%.1f) z%.2f size %.1fx%.1f | nearest p2 (%.1f,%.1f) size %.1fx%.1f d=%.2f' % (a[0], a[1], a[2], a[3], a[4], best[0], best[1], best[3], best[4], dist))
