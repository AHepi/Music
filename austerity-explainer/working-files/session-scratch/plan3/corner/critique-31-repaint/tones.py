import cv2, numpy as np, sys
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/'
im=cv2.imread(F+'composed-end-4.png').astype(np.float32)/255
H,W=im.shape[:2]
b,g,r=im[...,0],im[...,1],im[...,2]
# linearize sRGB for luminance, then report in sRGB-ish value
L=0.2126*r+0.7152*g+0.0722*b   # display-referred luma
mx=im.max(2)
print('size',W,H,'mean luma',L.mean().round(3))
for t in (0.85,0.9,0.95,0.98):
    m=L>t; print(f'luma>{t}: {m.mean()*100:.2f}% of frame')
print('any channel>=0.98:', (mx>=0.98).mean()*100)
for t in (0.03,0.05,0.08,0.10):
    m=L<t; print(f'luma<{t}: {m.mean()*100:.2f}%')
# blobs of bright
ids=cv2.imread(F+'facts/ids.png')
def blobs(mask,name,minarea=30):
    n,lab,st,cen=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    order=np.argsort(-st[1:,4])+1
    print('--',name)
    for i in order[:12]:
        x,y,w,h,a=st[i]
        if a<minarea: break
        print(f'  area {a} px ({a/(W*H)*100:.3f}%) box across {x/W:.3f}-{(x+w)/W:.3f} down {y/H:.3f}-{(y+h)/H:.3f}')
blobs(L>0.9,'luma>0.9')
blobs(mx>=0.98,'a channel clipped')
blobs(L<0.05,'luma<0.05',200)
np.save('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/critique-31-repaint/L.npy',L)
