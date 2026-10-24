import numpy as np
from PIL import Image
S='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/composed-end-5.png'
S4='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/composed-end-4.png'
ID='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/next/next26/ids.png'
im=np.array(Image.open(S).convert('RGB')).astype(float)/255
im4=np.array(Image.open(S4).convert('RGB')).astype(float)/255
ids=np.array(Image.open(ID).convert('RGB')).astype(int)
H,W=im.shape[:2]
L=lambda a: 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
lum=L(im); lum4=L(im4)
cols={'notice':(230,25,75),'board':(60,180,75),'drum':(255,225,25),'chair':(0,130,200),'lantern':(245,130,48),'pail':(145,30,180),'lamp post':(70,240,240),'left lamp':(240,50,230),'handcart':(210,245,60),'sacks':(250,190,212),'dustbins':(220,190,255),'gates':(128,0,0),'winding':(170,110,40),'chimney':(255,250,200)}
def mask(name):
    c=np.array(cols[name]); return (np.abs(ids-c).max(-1)<=2)
def box(x0,y0,x1,y1): 
    m=np.zeros((H,W),bool); m[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]=True; return m
def rep(name,m,img=im):
    l=L(img)[m]; rgb=img[m].mean(0)
    mx=img[m].max(-1); mn=img[m].min(-1); sat=np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
    print(f'{name:28s} px={m.sum():6d} luma mean={l.mean():.3f} p5={np.percentile(l,5):.3f} p95={np.percentile(l,95):.3f} std={l.std():.3f} rgb=({rgb[0]*255:.0f},{rgb[1]*255:.0f},{rgb[2]*255:.0f}) sat={sat.mean():.2f} r-b={(img[m][:,0]-img[m][:,2]).mean():+.2f} clip255={(img[m].max(-1)>=0.999).mean()*100:.1f}%')
print('frame mean luma', lum.mean(), 'end4', lum4.mean())
for n in cols: 
    m=mask(n)
    if m.sum(): rep(n,m)
# drum mouth: drum mask rows 0.62-0.655
dm=mask('drum')
ys,xs=np.nonzero(dm); print('drum mask y range', ys.min()/H, ys.max()/H, 'x', xs.min()/W, xs.max()/W)
