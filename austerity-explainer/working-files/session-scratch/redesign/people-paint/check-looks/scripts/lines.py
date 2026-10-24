import numpy as np, cv2, json
from PIL import Image
def skeletonize(b):
    # local maxima of the distance map as a stand-in skeleton
    dt=cv2.distanceTransform(b.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    mx=cv2.dilate(dt,np.ones((3,3),np.uint8))
    return (dt>0)&(dt>=mx)
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
NC='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def L(p): 
    a=np.asarray(Image.open(p).convert('RGB')).astype(np.float32); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
allmen=np.load(D+'allmen.npy')
def lines(Lm, region=None, name=''):
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21))
    bh=cv2.morphologyEx(Lm,cv2.MORPH_BLACKHAT,k)
    ink=(bh>18)&(Lm<45)
    ink=cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8)).astype(bool)
    dt=cv2.distanceTransform(ink.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    sk=skeletonize(ink)
    if region is not None: sel=sk&region; inks=ink&region
    else: sel=sk; inks=ink
    w=2*dt[sel]
    return inks.mean()*100, np.mean(w), np.percentile(w,75), Lm[inks].mean()
pt=L(P+'people-test-painting.png'); nc=L(NC+'notice-corner-painted.jpg'); bh=L(P+'people-test-painting-behind.jpg')
band=np.zeros_like(allmen); 
dil=cv2.dilate(allmen.astype(np.uint8),np.ones((9,9),np.uint8)).astype(bool)
for name,Lm,reg in [('people painting, whole',pt,None),('people painting, on/around the men',pt,dil),('people painting, away from men',pt,~dil),('painting without people, whole',bh,None),('notice corner painting, whole',nc,None)]:
    cover,med,p75,dark=lines(Lm,reg,name)
    print(f'{name:40s} ink lines cover {cover:4.1f}% of area; line width mean {med:.1f} px, 75th pct {p75:.1f} px; ink darkness L {dark:.0f}')
