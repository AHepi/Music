from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
names=['notice','board','drum','chair','lantern','pail','lamp post','left lamp','handcart','dustbins','sacks','winding wheels','chimney','gates']
M={k:idm(k) for k in names}
def bright_share(im,label,masks=M):
    L=cv2.GaussianBlur(luma(im),(0,0),3)
    thr=np.percentile(L,97); top=L>=thr
    print(f'{label}: brightest 3% threshold L={thr:.3f}')
    tot=top.sum(); acc=0
    for k,m in masks.items():
        s=(top&m).sum()
        if s>0: print(f'   {k:15s} {s/tot*100:5.1f}%'); acc+=s
    print(f'   {"(no prop)":15s} {(tot-acc)/tot*100:5.1f}%')
    # connected blobs of the top 3%
    n,lab,st,cen=cv2.connectedComponentsWithStats(top.astype(np.uint8))
    order=np.argsort(-st[1:,4])[:8]+1
    H,W=L.shape
    for i in order:
        x,y,w,h,a=st[i]
        print(f'   blob {a/(H*W)*100:5.2f}% of frame at {x/W:.2f}-{(x+w)/W:.2f} across, {y/H:.2f}-{(y+h)/H:.2f} down, mean L {L[lab==i].mean():.3f}')
bright_share(v4,'v4 (ids masks of v5: lamp post mask off for v4)')
bright_share(v5,'v5')
bright_share(ref,'ref',{
 'notice':boxm(ref.shape,0.745,0.455,0.915,0.66),
 'chair':boxm(ref.shape,0.70,0.60,0.97,0.84),
 'lamp head':boxm(ref.shape,0.72,0.10,0.86,0.25),
 'drum':boxm(ref.shape,0.50,0.62,0.69,0.82),
 'left lamp':boxm(ref.shape,0.19,0.34,0.27,0.42)})
