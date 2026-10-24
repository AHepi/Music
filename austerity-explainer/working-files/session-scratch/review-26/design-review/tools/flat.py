import sys, glob, os, cv2, numpy as np, json
# per-second frames; 9x16 grid of 120px blocks; a block is "flat" when it has little texture
files = sorted(glob.glob(sys.argv[1] + '/s*.jpg'))
out = {}
for p in files:
    t = int(os.path.basename(p)[1:4])
    g = cv2.imread(p, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    g = cv2.resize(g, (540, 960), interpolation=cv2.INTER_AREA)
    lap = np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3))
    B = 60
    flat = np.zeros((16, 9), bool); dark = np.zeros((16, 9), bool)
    for r in range(16):
        for c in range(9):
            blk = g[r*B:(r+1)*B, c*B:(c+1)*B]; L = lap[r*B:(r+1)*B, c*B:(c+1)*B]
            flat[r, c] = (blk.std() < 10 and L.mean() < 4.0)
            dark[r, c] = blk.mean() < 28
    out[t] = {'flat': flat.astype(int).tolist(), 'dark': dark.astype(int).tolist(),
              'top25_flat': float(flat[:4].mean()), 'bot25_flat': float(flat[12:].mean()),
              'mid_flat': float(flat[4:12].mean()), 'top25_dark': float(dark[:4].mean()), 'bot25_dark': float(dark[12:].mean()),
              'all_flat': float(flat.mean())}
json.dump(out, open(sys.argv[2], 'w'))
for t in sorted(out):
    o = out[t]
    print(f"{t:3d}s  top25 flat {o['top25_flat']:.2f} dark {o['top25_dark']:.2f} | mid flat {o['mid_flat']:.2f} | bot25 flat {o['bot25_flat']:.2f} dark {o['bot25_dark']:.2f} | all {o['all_flat']:.2f}")
