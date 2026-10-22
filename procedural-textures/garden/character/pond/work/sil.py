# offline silhouette tools (numpy only): project points with the garden's cameras and rasterise leaf discs / tubes
import numpy as np, json
D = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond/work/"
CAMS = json.load(open(D + "cams.json"))

def project(P, cam='photo', W=600):
    c = CAMS[cam]; M = np.array(c['R']); loc = np.array(c['loc'])
    H = int(round(W * c['res'][1] / c['res'][0]))
    pc = (np.asarray(P, dtype=np.float64) - loc) @ M          # world -> camera (M columns are camera axes)
    f = c['lens'] / c['sensor']
    z = -pc[:, 2]
    u = W * (0.5 + pc[:, 0] / z * f)
    v = H * 0.5 - pc[:, 1] / z * f * W
    return u, v, z, W, H, f

def disc_mask(P, r_world, cam='photo', W=600, vis=None):
    u, v, z, W, H, f = project(P, cam, W)
    m = np.zeros((H, W), bool)
    rp = np.maximum(r_world * f * W / np.maximum(z, 0.1), 0.6)
    ok = z > 0.2
    for k in (1, 2, 3, 4, 6, 9, 14):
        sel = ok & (rp <= k + 0.0) & (rp > (k_prev if (k_prev := {1:0,2:1,3:2,4:3,6:4,9:6,14:9}[k]) else 0))
        if not sel.any():
            continue
        r = int(np.ceil(k))
        uu, vv = np.round(u[sel]).astype(int), np.round(v[sel]).astype(int)
        yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
        inside = (xx ** 2 + yy ** 2) <= (k ** 2 if k > 1 else 1)
        for dy, dx in zip(yy[inside], xx[inside]):
            y2, x2 = vv + dy, uu + dx
            g = (y2 >= 0) & (y2 < H) & (x2 >= 0) & (x2 < W)
            m[y2[g], x2[g]] = True
    return m

def tube_mask(path, radii, cam='photo', W=600):
    path = np.asarray(path, float)
    pts, rr = [], []
    for i in range(len(path) - 1):
        n = max(2, int(np.linalg.norm(path[i + 1] - path[i]) / 0.03))
        t = np.linspace(0, 1, n)[:, None]
        pts.append(path[i] * (1 - t) + path[i + 1] * t); rr.append(radii[i] * (1 - t[:, 0]) + radii[i + 1] * t[:, 0])
    pts = np.vstack(pts); rr = np.concatenate(rr)
    u, v, z, W, H, f = project(pts, cam, W)
    m = np.zeros((H, W), bool)
    rp = np.maximum(rr * f * W / np.maximum(z, 0.1), 0.8)
    for r_ in np.unique(np.ceil(rp).astype(int)):
        sel = np.ceil(rp).astype(int) == r_
        yy, xx = np.mgrid[-r_:r_ + 1, -r_:r_ + 1]; inside = (xx ** 2 + yy ** 2) <= r_ ** 2
        uu, vv = np.round(u[sel]).astype(int), np.round(v[sel]).astype(int)
        for dy, dx in zip(yy[inside], xx[inside]):
            y2, x2 = vv + dy, uu + dx
            g = (y2 >= 0) & (y2 < H) & (x2 >= 0) & (x2 < W); m[y2[g], x2[g]] = True
    return m

def iou(a, b):
    return float((a & b).sum() / max(1, (a | b).sum()))
