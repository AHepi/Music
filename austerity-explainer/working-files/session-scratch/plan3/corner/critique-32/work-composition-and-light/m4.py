from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
def halves(im,label):
    L=luma(im); H,W=L.shape; h=W//2
    g=cv2.GaussianBlur(L,(0,0),1.0)
    gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1); E=np.hypot(gx,gy)
    above=np.clip(L-L.mean(),0,None)
    # local contrast at phone scale: |L - blur(L, 2% width)|
    lc=np.abs(L-cv2.GaussianBlur(L,(0,0),W*0.02))
    def share(A): return A[:,:h].sum()/A.sum()*100
    print(f'{label}: left-half share  brightness {share(L):4.1f}%  edges {share(E):4.1f}%  above-average light {share(above):4.1f}%  local contrast {share(lc):4.1f}% | mean L left {L[:,:h].mean():.3f} right {L[:,h:].mean():.3f}')
    # thirds down
    for name,(a,b) in {'top third':(0,1/3),'middle':(1/3,2/3),'bottom':(2/3,1)}.items():
        s=slice(int(a*H),int(b*H))
        print(f'      {name:9s} L left {L[s,:h].mean():.3f} right {L[s,h:].mean():.3f}   edges left/right {E[s,:h].mean():.3f}/{E[s,h:].mean():.3f}')
for im,l in ((v4,'v4'),(v5,'v5'),(ref,'ref')): halves(im,l)
