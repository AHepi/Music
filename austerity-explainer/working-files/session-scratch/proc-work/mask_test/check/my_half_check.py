# plain note: my own half-tile (slide) test on pictures I baked myself (512 dots, slide 0.125 across and 0.875 up). Reads pictures, prints numbers.
import cv2, numpy as np, json
H = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/mask_test/check/half/'
N = 512
def rd(p, mask):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if mask:
        a = a[..., 0] if a.ndim == 3 else a
        return a.astype(np.float64) / 65535.0
    return a.astype(np.float64) / 255.0
res = {}
for label, b, s, mask in [('finished colour (moss+chip stamps)', 'colour_0', 'colour_shift', False), ('moss stamp mask', 'mossmask_0', 'mossmask_shift', True)]:
    base = rd(H + b + ('/height.png' if mask else '/colour.png'), mask)
    sh = rd(H + s + ('/height.png' if mask else '/colour.png'), mask)
    cols, rows = 64, 448
    out = {}
    for name, (dc, dr) in {'roll left 64, down 448': (-cols, rows), 'roll right 64, up 448': (cols, -rows)}.items():
        pred = np.roll(np.roll(base, dc, axis=1), dr, axis=0)
        d = np.abs(sh - pred)
        if d.ndim == 3: d = d.max(axis=2)
        blur = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), 1.5)
        bl = np.abs(blur(sh) - blur(pred))
        if bl.ndim == 3: bl = bl.max(axis=2)
        lim = 0.06 if mask else 0.03
        # old tile edge in the shifted picture
        ecol = (N - dc * -1) % N if False else None
        out[name] = {'mean_diff': round(float(d.mean()), 5), 'blurred_max': round(float(bl.max()), 4), 'blurred_dots_over_limit': int((bl > lim).sum()), 'limit': lim}
    res[label] = out
    # tile edge location: the unshifted tile edge column 0 appears at column (0 + 64) or (0 - 64) in the shifted picture
    print(label, json.dumps(out, indent=1))
    # also: how much stamp stuff touches the unshifted tile edge (so the test is not empty)
    if mask:
        bm = (base > 0.5)
        print('  mask dots within 30 dots of the tile edge:', int(bm[:30].sum() + bm[-30:].sum() + bm[:, :30].sum() + bm[:, -30:].sum()), ' of total mask dots', int(bm.sum()))
json.dump(res, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/mask_test/check/my_half_results.json', 'w'), indent=1)
