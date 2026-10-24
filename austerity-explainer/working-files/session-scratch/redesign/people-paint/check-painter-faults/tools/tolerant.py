import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
def tol_diff(A,B,r=2,blur=1.0):
    la=cv2.cvtColor(A,cv2.COLOR_RGB2LAB).astype(np.float32); lb=cv2.cvtColor(B,cv2.COLOR_RGB2LAB).astype(np.float32)
    la=cv2.GaussianBlur(la,(0,0),blur); lb=cv2.GaussianBlur(lb,(0,0),blur)
    best=np.full(la.shape[:2],1e9,np.float32)
    H,W=best.shape
    pad=cv2.copyMakeBorder(lb,r,r,r,r,cv2.BORDER_REFLECT)
    for dy in range(-r,r+1):
        for dx in range(-r,r+1):
            sh=pad[r+dy:r+dy+H, r+dx:r+dx+W]
            d=np.sqrt(((la-sh)**2).sum(-1))
            best=np.minimum(best,d)
    return best
if __name__=='__main__':
    I=imgs()
    d=tol_diff(I['paint'],I['behind'])
    db=cv2.GaussianBlur(d,(0,0),4)
    np.save(O+'/tol_paint_behind.npy',db)
    people=np.load(O+'/people_mask.npy')
    # people zone: people + generous dilation for shadows near the feet
    pz=cv2.dilate(people.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41)))>0
    print('shift-tolerant (2 px) difference painting vs people-out: whole mean %.1f, in people(+20px) %.1f, elsewhere %.1f'%(d.mean(),d[pz].mean(),d[~pz].mean()))
    for t in [8,12,16,24]:
        m=db>t
        print('  >%d: %.2f%% of frame; outside people(+20px): %.2f%% of frame'%(t,100*m.mean(),100*(m&~pz).mean()))
    m=((db>12)&~pz).astype(np.uint8)
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    idx=sorted([i for i in range(1,n) if st[i,4]>300],key=lambda i:-st[i,4])
    print('blobs >12 outside people zone (>300 px):',len(idx))
    for i in idx[:30]:
        x,y,w,h,ar=st[i]; print('   (%.3f,%.3f)-(%.3f,%.3f) %d px mean %.1f'%(x/1536,y/2730,(x+w)/1536,(y+h)/2730,ar,db[lab==i].mean()))
    v=np.clip(db/30,0,1)
    base=cv2.cvtColor(I['behind'],cv2.COLOR_RGB2GRAY).astype(np.float32)/255*0.55
    rgb=np.stack([base+v*0.9,base+v*0.35,base],-1)
    e=cv2.Canny(pz.astype(np.uint8)*255,50,100)>0; rgb[e]=[0.2,0.7,1.0]
    Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).resize((768,1365)).save(O+'/diff-tolerant-paint-vs-behind.jpg',quality=90)
