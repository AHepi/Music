import cv2, numpy as np, json
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final'
im = cv2.imread(F+'/composed-end-4.png')[..., ::-1].astype(np.float64)/255
H, Wd = im.shape[:2]
L = 0.2126*im[...,0]+0.7152*im[...,1]+0.0722*im[...,2]
RB = im[...,0]-im[...,2]
hsv = cv2.cvtColor((im*255).astype(np.uint8)[..., ::-1], cv2.COLOR_BGR2HSV)
S = hsv[...,1]/255.0
ids = cv2.imread(F+'/facts/ids.png')[..., ::-1].astype(int)
f = json.load(open(F+'/facts/facts.json'))
def mask(name, tol=3):
    c = np.array(f['groups'][name]['colour'])
    return (np.abs(ids - c).max(-1) <= tol)
yy, xx = np.mgrid[0:H, 0:Wd]
fx, fy = (xx+0.5)/Wd, (yy+0.5)/H
def box(x0,x1,y0,y1): return (fx>=x0)&(fx<x1)&(fy>=y0)&(fy<y1)
def stat(m, label):
    n = m.sum()
    if n == 0: print(label, 'empty'); return
    c = (im[m].mean(0)*255).round().astype(int)
    print('%-38s n=%6d (%.3f%%) L mean %.3f med %.3f p95 %.3f max %.3f | RGB %s | R-B %+.3f | sat %.2f | clip %.1f%%' % (label, n, n/H/Wd*100, L[m].mean(), np.median(L[m]), np.percentile(L[m],95), L[m].max(), tuple(c), RB[m].mean(), S[m].mean(), (im[m].max(-1)>=0.998).mean()*100))
