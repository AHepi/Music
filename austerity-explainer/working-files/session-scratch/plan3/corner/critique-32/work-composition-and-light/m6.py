from common import *
v5=load(V5); v4=load(V4)
d=luma(v5)-luma(v4)
H,W=d.shape
ad=cv2.GaussianBlur(np.abs(d),(0,0),2)
m=(ad>0.04).astype(np.uint8)
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
order=np.argsort(-st[1:,4])+1
print('regions that changed by more than 0.04 brightness (v5 minus v4):')
for i in order[:25]:
    x,y,w,h,a=st[i]
    if a<30: continue
    sel=lab==i
    print(f'  {x/W:.3f}-{(x+w)/W:.3f} across, {y/H:.3f}-{(y+h)/H:.3f} down, area {a/(H*W)*100:.3f}%  change {d[sel].mean():+.3f}  v4 {luma(v4)[sel].mean():.3f} -> v5 {luma(v5)[sel].mean():.3f}')
# save a visual of differences
vis=np.clip(0.5+d*2,0,1)
cv2.imwrite('diff_v5_minus_v4.png',(vis*255).astype(np.uint8))
