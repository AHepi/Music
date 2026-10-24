# What this does (plain words): per-slate facts for the reference, BEFORE and AFTER: the lightest and darkest slates (with where they are),
# how many slates are far from the typical slate, and how bright the lower rim (the pale lip / chips along each slate's lower edge) is
# compared with the slate face. Also the colour of the moss dots (hue, saturation, brightness) and how much the moss stands out from its slate.
import cv2
import numpy as np
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
S = {'reference': P + 'reference/slate/colour.png', 'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png', 'after': P + 'recipes/slate_layers/outputs/default/colour.png'}
for name, path in S.items():
    bgr = cv2.imread(path)
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(float)
    mask = cv2.erode((grey > 30).astype(np.uint8), np.ones((3, 3), np.uint8))
    count, labels, stats, cent = cv2.connectedComponentsWithStats(mask, connectivity=4)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 5000]
    rows = []
    rim_contrast, rim_p90, rim_pale_share = [], [], []
    for i in keep:
        sub = labels == i
        face = cv2.erode(sub.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
        if face.sum() < 2000:
            continue
        x, y, w, h = stats[i, :4]
        rows.append((grey[face].mean(), grey[face].std(), x, y, w, h))
        # lower rim strip: for each column the 9 dots above the lowest slate dot in that column
        if x > 2 and y > 2 and x + w < 1252 and y + h < 1252 and w > 80:
            strip = np.zeros_like(sub)
            for c in range(x + 6, x + w - 6):
                col = np.where(sub[:, c])[0]
                if len(col):
                    b = col.max()
                    strip[max(0, b - 9):b - 1, c] = True
            if strip.sum() > 300:
                faceval = np.median(grey[face])
                v = grey[strip]
                rim_contrast.append(np.percentile(v, 90) - faceval)
                rim_pale_share.append((v > faceval + 22).mean() * 100)
    rows = np.array(rows)
    means = rows[:, 0]
    typ = np.median(means)
    print('=== %s: %d slates; face mean grey median %.1f, std %.1f, min %.1f, max %.1f' % (name, len(means), typ, means.std(), means.min(), means.max()))
    order = np.argsort(-means)[:4]
    print('  lightest slates (mean, inner std, x, y):', [(round(rows[j, 0], 1), round(rows[j, 1], 1), int(rows[j, 2]), int(rows[j, 3])) for j in order])
    order = np.argsort(means)[:3]
    print('  darkest slates  (mean, inner std, x, y):', [(round(rows[j, 0], 1), round(rows[j, 1], 1), int(rows[j, 2]), int(rows[j, 3])) for j in order])
    print('  slates more than 12 grey levels from the middle slate: %d of %d' % ((np.abs(means - typ) > 12).sum(), len(means)))
    print('  slates with inner spread below 8 (flat, plain): %d of %d' % ((rows[:, 1] < 8).sum(), len(means)))
    print('  lower rim: 90th percentile above the slate face median: mean %.1f; share of rim dots 22+ levels above the face: mean %.1f%% (%d slates)' % (np.mean(rim_contrast), np.mean(rim_pale_share), len(rim_contrast)))
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h_, s_, v_ = [hsv[..., k].astype(int) for k in range(3)]
    moss = (h_ >= 22) & (h_ <= 45) & (s_ >= 45) & (v_ >= 40) & (v_ <= 150)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(float)
    L, A, B = lab[..., 0] * 100 / 255, lab[..., 1] - 128, lab[..., 2] - 128
    big = cv2.dilate(moss.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~moss & (grey > 30)
    print('  moss dots: Lab mean %.1f %.1f %.1f; spread L %.1f, b* %.1f; saturation mean %.0f (std %.0f); ring around moss: L %.1f, b* %.1f -> moss is %.1f L darker/lighter, %.1f b* yellower than its surroundings' % (
        L[moss].mean(), A[moss].mean(), B[moss].mean(), L[moss].std(), B[moss].std(), s_[moss].mean(), s_[moss].std(), L[big].mean(), B[big].mean(), L[moss].mean() - L[big].mean(), B[moss].mean() - B[big].mean()))
