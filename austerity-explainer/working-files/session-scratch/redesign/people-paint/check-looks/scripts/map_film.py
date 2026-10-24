import numpy as np, cv2
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
paint=np.asarray(Image.open(P+'people-test-painting.png').convert('L')).astype(np.float32)
fr=np.asarray(Image.open(D+'pf/f031.png').convert('L')).astype(np.float32)
H,W=paint.shape
best=None
for z in np.arange(1.04,1.12,0.005):
    s=1080/1536*z
    M=np.array([[s,0,540-W/2*s],[0,s,960-H/2*s]],np.float32)
    w=cv2.warpAffine(paint,M,(1080,1920))
    # compare edges
    e1=cv2.Canny(w.astype(np.uint8),40,100).astype(np.float32); e2=cv2.Canny(fr.astype(np.uint8),40,100).astype(np.float32)
    e1=cv2.GaussianBlur(e1,(0,0),2); e2=cv2.GaussianBlur(e2,(0,0),2)
    c=(e1*e2).sum()/np.sqrt((e1*e1).sum()*(e2*e2).sum())
    if best is None or c>best[0]: best=(c,z)
print('best zoom',best)
