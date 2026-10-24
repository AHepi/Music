import cv2, sys
sys.path.insert(0,'.')
from regions import R
P={'ref':'/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg',
 'old':'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/composed-end-2.png',
 'now':'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/composed-end-4.png'}
for k,p in P.items():
    im=cv2.imread(p); h,w=im.shape[:2]
    for i,(name,(x0,y0,x1,y1)) in enumerate(R[k].items()):
        cv2.rectangle(im,(int(x0*w),int(y0*h)),(int(x1*w),int(y1*h)),(0,255,0) if i%2 else (255,0,255),2)
        cv2.putText(im,str(i),(int(x0*w)+3,int(y0*h)+18),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)
    im=cv2.resize(im,(540,int(540*h/w)))
    cv2.imwrite(f'boxes_{k}.png',im)
