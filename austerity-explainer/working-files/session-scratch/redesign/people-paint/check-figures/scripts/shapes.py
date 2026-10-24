import numpy as np, json, cv2
from PIL import Image
A='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/'
pt=np.array(Image.open(A+'people-test-painting.png').convert('RGB')).astype(float)
bh=np.array(Image.open(A+'people-test-painting-behind.jpg').convert('RGB')).astype(float)
pl=np.array(Image.open(A+'people-test-plate.jpg').convert('RGB')).astype(float)
hp=np.array(Image.open(A+'people-test-helper-plate.jpg').convert('RGB')).astype(float)
H,W=pt.shape[:2]
def figmask(a,b,th):
    d=np.abs(a-b).mean(2)
    m=(cv2.GaussianBlur(d,(0,0),1.5)>th).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    return m,d
mp,dp=figmask(pt,bh,22)   # people in painting
mq,dq=figmask(pl,hp,12)   # people in plate (plate vs helper plate)
Image.fromarray(mp*255).save(O+'masks/painting-people-diff.png')
Image.fromarray(mq*255).save(O+'masks/plate-people-diff.png')
names=['man facing','man arms folded','man stooped','man hand on bar','man leaning']+['walker %d'%i for i in range(1,7)]
vis={}
for n in names:
    vis[n]=np.array(Image.open(O+'masks/'+n.replace(' ','-')+'-visible.png'))>127
# label map of visible plate figures, then assign each pixel to nearest figure (within 25 px)
lab=np.zeros((H,W),np.int32)
for i,n in enumerate(names): lab[vis[n]]=i+1
dist,idx=None,None
inv=(lab==0).astype(np.uint8)
d,(iy,ix)=None,(None,None)
D=np.stack([cv2.distanceTransform((~vis[n]).astype(np.uint8),cv2.DIST_L2,5) if vis[n].sum()>0 else np.full((H,W),1e9,np.float32) for n in names])
near=D.argmin(0)+1
near[D.min(0)>30]=0
out={}
def stats(m):
    ys,xs=np.nonzero(m)
    if len(ys)==0: return None
    return dict(area=int(m.sum()),box=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],cx=round(float(xs.mean()),1),cy=round(float(ys.mean()),1),h=int(ys.max()-ys.min()+1),w=int(xs.max()-xs.min()+1))
for i,n in enumerate(names):
    region=(near==i+1)
    a=vis[n]; b=(mp>0)&region; c=(mq>0)&region
    r={'plate_visible':stats(a),'painting_people_pixels':stats(b),'plate_people_pixels':stats(c)}
    if a.sum()>0:
        inter=(a&b).sum(); uni=(a|b).sum()
        r['iou_plate_mask_vs_painting']=round(inter/uni,3)
        r['painting_covers_plate_figure']=round(inter/a.sum(),3)
        r['painting_outside_plate_figure_px']=int((b&~a).sum())
        # iou plate-diff vs painting-diff
        inter2=(c&b).sum(); uni2=(c|b).sum()
        r['iou_platediff_vs_paintingdiff']=round(inter2/max(uni2,1),3)
    out[n]=r
    sv=r['plate_visible']; sp=r['painting_people_pixels']
    if sv and sp:
        print(f"{n:16s} plate h={sv['h']:4d} w={sv['w']:4d} c=({sv['cx']},{sv['cy']}) | painting h={sp['h']:4d} w={sp['w']:4d} c=({sp['cx']},{sp['cy']}) | IoU={r['iou_plate_mask_vs_painting']} covers={r['painting_covers_plate_figure']} outside={r['painting_outside_plate_figure_px']} | IoU(plate-diff)={r['iou_platediff_vs_paintingdiff']}")
    else:
        print(n, 'plate visible:',sv is not None,'painting:',sp)
json.dump(out,open(O+'shape-match.json','w'),indent=1)
# overlay picture
ov=pt.copy()*0.5
ov[...,0]+= (np.any([vis[n] for n in names],axis=0))*120
ov[...,1]+= (mp>0)*120
Image.fromarray(np.clip(ov,0,255).astype(np.uint8)).crop((150,1180,1260,1900)).save(O+'outline-overlay.jpg',quality=90)
