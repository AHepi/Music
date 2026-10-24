import sys, numpy as np
from PIL import Image
def stats(p, boxes):
    im = Image.open(p).convert('RGB'); W,H = im.size
    a = np.asarray(im).astype(np.float32)/255
    R,G,B = a[...,0],a[...,1],a[...,2]
    L = 0.2126*R+0.7152*G+0.0722*B
    s = np.asarray(im.convert('HSV')).astype(np.float32)[...,1]/255
    warmbright = (R > B+0.15) & (s>0.35) & (L>0.45)
    print(p.split('/')[-1], W,H, 'mean L', round(float(L.mean()),3), 'bright-warm % of picture', round(float(warmbright.mean()*100),2))
    tot = warmbright.sum()
    print('  bright-warm by thirds across L/M/R %', [round(float(warmbright[:, int(i*W/3):int((i+1)*W/3)].sum()/tot*100),1) for i in range(3)])
    print('  L>0.6 % by thirds across', [round(float((L[:, int(i*W/3):int((i+1)*W/3)]>0.6).mean()*100),2) for i in range(3)])
    print('  3x3 mean L rows:', [[round(float(L[int(r*H/3):int((r+1)*H/3), int(c*W/3):int((c+1)*W/3)].mean()),3) for c in range(3)] for r in range(3)])
    for k,(x0,y0,x1,y1) in boxes.items():
        X0,Y0,X1,Y1 = int(x0*W),int(y0*H),int(x1*W),int(y1*H)
        inner = L[Y0:Y1,X0:X1]; pad=int(0.5*max(X1-X0,Y1-Y0))
        oy0,oy1,ox0,ox1 = max(0,Y0-pad),min(H,Y1+pad),max(0,X0-pad),min(W,X1+pad)
        ring = L[oy0:oy1,ox0:ox1].copy(); m=np.ones_like(ring,bool); m[Y0-oy0:Y1-oy0,X0-ox0:X1-ox0]=False
        print(f'  {k:14s} area% {(X1-X0)*(Y1-Y0)/(W*H)*100:5.2f}  L {inner.mean():.3f}  ring {ring[m].mean():.3f}  contrast {(inner.mean()+.05)/(ring[m].mean()+.05):.2f}')
stats(sys.argv[1], {'notice paper':(850/1080,1080/1920,970/1080,1245/1920),'fire':(700/1080,1310/1920,830/1080,1375/1920),'sacks':(105/1080,1560/1920,660/1080,1830/1920)})
stats(sys.argv[2], {'notice paper':(830/1116,905/2000,1020/1116,1290/2000),'fire':(590/1116,1260/2000,740/1116,1335/2000),'lit cobbles':(300/1116,1390/2000,520/1116,1570/2000)})
