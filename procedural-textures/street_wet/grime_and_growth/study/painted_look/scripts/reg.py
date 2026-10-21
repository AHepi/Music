"""Line up a painting on its plate locally (the film's own tool only fixes stretch and shift for the whole picture)."""
from common import *
def edge_map(x):
    g = gauss(x, 1.2); gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    m = np.sqrt(gx * gx + gy * gy); return (m / (gauss(m, 40) + 1e-3)).astype(np.float32)

def shift_field(A, B, T=256, step=128):
    EA, EB = edge_map(A), edge_map(B)
    h, w = A.shape
    ys = list(range(0, h - T + 1, step)); xs = list(range(0, w - T + 1, step))
    win = cv2.createHanningWindow((T, T), cv2.CV_32F)
    dx = np.full((len(ys), len(xs)), np.nan, np.float32); dy = dx.copy(); rr = dx.copy()
    for i, y in enumerate(ys):
        for j, x in enumerate(xs):
            (sx, sy), r = cv2.phaseCorrelate(EA[y:y+T, x:x+T], EB[y:y+T, x:x+T], win)
            rr[i, j] = r
            if r > 0.06 and abs(sx) < 12 and abs(sy) < 12: dx[i, j] = sx; dy[i, j] = sy
    gx, gy = np.nanmedian(dx), np.nanmedian(dy)
    dx = np.where(np.isnan(dx), gx, dx); dy = np.where(np.isnan(dy), gy, dy)
    dx = cv2.GaussianBlur(dx, (0, 0), 1.0); dy = cv2.GaussianBlur(dy, (0, 0), 1.0)
    cxs = np.array(xs) + T / 2; cys = np.array(ys) + T / 2
    # bilinear expand to full size
    fx = cv2.resize(dx, (w, h), interpolation=cv2.INTER_LINEAR); fy = cv2.resize(dy, (w, h), interpolation=cv2.INTER_LINEAR)
    # resize maps tile grid to whole picture (small edge error, fine for a +-1 px job)
    return fx, fy, (float(gx), float(gy))

def warp_back(img, fx, fy):
    """phaseCorrelate(A,B) returns the shift of B relative to A; sample B at x+shift to line it up on A."""
    h, w = fx.shape
    xx, yy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    return cv2.remap(img, xx + fx, yy + fy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def register_pair(A_rgb, B_rgb):
    A, B = lum(A_rgb), lum(B_rgb)
    fx, fy, g = shift_field(A, B)
    Bw = np.stack([warp_back(B_rgb[..., i], fx, fy) for i in range(3)], -1)
    return Bw, (fx, fy, g)
