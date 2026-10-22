# numbers for the report: value study, shadow tone on the wall, roof band, screens vs sky; original vs real vs painted (hero view) from a run folder
import sys, json, numpy as np
from PIL import Image
G='proc-work/garden/light/'
R=sys.argv[1]
def load(p): return np.asarray(Image.open(p).convert('RGB').resize((960,640))).astype(float)/255
def Y(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
ims={'original':load(G+'work/orig_960.jpg'),'real':load(R+'/hero_real.png'),'painted':load(R+'/hero_painted.png')}
out={}
for k,a in ims.items():
    y=Y(a); H,W=y.shape
    bh,bw=int(H*.12),int(W*.12); m=np.zeros(y.shape,bool); m[:bh]=m[-bh:]=1; m[:,:bw]=m[:,-bw:]=1
    cen=y[H//4:3*H//4,W//4:3*W//4]
    sc=y[240:300,430:570].mean(); sky=y[0:60].mean()
    roof=y[112:160,340:600]
    ws=a[250:285,600:690].reshape(-1,3).mean(0); wl=a[250:285,800:900].reshape(-1,3).mean(0)
    out[k]=dict(mean=round(float(y.mean()),3),p5=round(float(np.percentile(y,5)),3),p95=round(float(np.percentile(y,95)),3),edge_over_centre=round(float(y[m].mean()/cen.mean()),3),
        screens=round(float(sc),3),sky_band=round(float(sky),3),screens_over_sky=round(float(sc/sky),2),roof_mean=round(float(roof.mean()),3),roof_near_black_pct=round(100*float((roof<0.04).mean()),1),
        wall_shade_BoverR=round(float(ws[2]/ws[0]),2),wall_sun_BoverR=round(float(wl[2]/wl[0]),2),wall_shade_luma=round(float(0.2126*ws[0]+0.7152*ws[1]+0.0722*ws[2]),3))
print(json.dumps(out,indent=1))
json.dump(out,open(G+'out/hero_numbers.json','w'),indent=1)
