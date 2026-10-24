import sys, cv2, numpy as np, csv
v = sys.argv[1]; out = sys.argv[2]
cap = cv2.VideoCapture(v)
prev = None; i = 0
rows = []
while True:
    ok, fr = cap.read()
    if not ok: break
    small = cv2.resize(fr, (270, 480), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32)
    diff = float(np.mean(np.abs(g - prev))) if prev is not None else 0.0
    prev = g
    # edges for detail
    e = cv2.Canny(g.astype(np.uint8), 40, 120) > 0
    h = g.shape[0]
    thirds = [(0, h//3), (h//3, 2*h//3), (2*h//3, h)]
    r = [i, i/30.0, float(g.mean()), diff]
    for a,b in thirds:
        r += [float(g[a:b].mean()), float(g[a:b].std()), float(e[a:b].mean())]
    # top 20% and bottom 20%
    r += [float(g[:h//5].mean()), float(e[:h//5].mean()), float(g[4*h//5:].mean()), float(e[4*h//5:].mean())]
    rows.append(r)
    i += 1
with open(out, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['frame','t','luma','diff','top_luma','top_std','top_edge','mid_luma','mid_std','mid_edge','bot_luma','bot_std','bot_edge','top20_luma','top20_edge','bot20_luma','bot20_edge'])
    w.writerows(rows)
print(i)
