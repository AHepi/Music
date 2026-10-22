import sys, json
import numpy as np
from PIL import Image
def luma(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def stats(p):
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float32)/255.0
    Y = luma(a); H, W = Y.shape
    bh, bw = int(H*0.12), int(W*0.12)
    mask = np.zeros_like(Y, bool); mask[:bh,:]=1; mask[-bh:,:]=1; mask[:,:bw]=1; mask[:,-bw:]=1
    cen = Y[int(H*.25):int(H*.75), int(W*.25):int(W*.75)]
    sat = (a.max(-1)-a.min(-1))/(a.max(-1)+1e-6)
    top = Y[:int(H*0.14)]
    r = dict(file=p.split('/')[-1], mean=round(float(Y.mean()),3), p5=round(float(np.percentile(Y,5)),3), p50=round(float(np.percentile(Y,50)),3), p95=round(float(np.percentile(Y,95)),3),
             edge_over_centre=round(float(Y[mask].mean()/cen.mean()),3), sky_band_luma=round(float(top.mean()),3), mean_sat=round(float(sat.mean()),3))
    # roof band: central-left region rows 22%-34%
    roof = Y[int(H*0.18):int(H*0.34), int(W*0.05):int(W*0.70)]
    r['roof_band_p5'] = round(float(np.percentile(roof,5)),3); r['roof_band_mean']=round(float(roof.mean()),3)
    r['frac_near_black'] = round(float((Y<0.04).mean()),4)
    return r
for p in sys.argv[1:]: print(json.dumps(stats(p)))
