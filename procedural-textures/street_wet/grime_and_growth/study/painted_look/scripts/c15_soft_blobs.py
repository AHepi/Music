"""Soft pale and dark blobs (stains) on the notice corner pavement flags: plate vs painting at two blob sizes (difference-of-blurs), the 8 strongest pale and 6 darkest."""
import sys; sys.path.insert(0,'scripts')
from common import *
p,q=PAIRS['corner_dry']
A=lum(load_rgb(p)); B=lum(load_rgb(WORK+"/corner_dry_painting_registered.png"))
yy,xx=np.mgrid[0:H,0:W]
flags=(xx>=900)&(xx<=1480)&(yy>=2150)&(yy<=2690)&~((xx<1220)&(yy<2260))
allr=[];darkr=[]
for sg in (6,10):
    da=dog(A,sg); db=dog(B,sg)
    m=cv2.dilate(da,np.ones((41,41),np.uint8)); pk=(da>=m)&flags&(da>0.012)
    ys,xs=np.nonzero(pk); order=np.argsort(-da[ys,xs])[:8]
    print("sigma",sg,"pale blobs: plate / painting / ratio")
    for o in order:
        y,x=ys[o],xs[o]; pb=db[max(0,y-6):y+7,max(0,x-6):x+7].max(); allr.append(pb/da[y,x]); print("  (%d,%d) %.3f %.3f %.1f"%(x,y,da[y,x],pb,pb/da[y,x]))
    m2=cv2.dilate(-da,np.ones((41,41),np.uint8)); pk2=((-da)>=m2)&flags&(-da>0.012)
    ys,xs=np.nonzero(pk2); order=np.argsort(da[ys,xs])[:6]
    print("sigma",sg,"dark blobs")
    for o in order:
        y,x=ys[o],xs[o]; pb=db[max(0,y-6):y+7,max(0,x-6):x+7].min(); darkr.append(pb/da[y,x]); print("  (%d,%d) %.3f %.3f %.1f"%(x,y,da[y,x],pb,pb/da[y,x]))
print("pale: ratio range %.1f-%.1f median %.2f ; dark: range %.1f-%.1f median %.2f"%(min(allr),max(allr),np.median(allr),min(darkr),max(darkr),np.median(darkr)))
