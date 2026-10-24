import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
Lp,Lq=L(I['plate']),L(I['paint'])
def feature(Lx,xc,y,half=30,rows=9):
    prof=Lx[y-rows//2:y+rows//2+1,xc-half:xc+half+1].mean(0)
    bg=np.median(np.r_[prof[:6],prof[-6:]])
    # feature = biggest contiguous run differing from bg near the centre
    c=half; dif=prof-bg
    # pick polarity by centre region
    pol=np.sign(dif[c-4:c+5].mean()) or 1
    d=dif*pol
    i=c-4+int(np.argmax(d[c-4:c+5])); peak=d[i]; lvl=peak/2
    a=i; b=i
    while a>0 and d[a]>lvl: a-=1
    while b<len(d)-1 and d[b]>lvl: b+=1
    return xc-half+(a+b)/2, b-a-1, pol, peak
def track(name, xf, yfs, half=30):
    out=[]
    for yf in yfs:
        y=int(yf*2730); xc=int(xf*1536)
        cp,wp,pp,kp=feature(Lp,xc,y,half)
        # recentre painting search on plate centre
        cq,wq,pq,kq=feature(Lq,int(round(cp)),y,half)
        out.append((yf,cp,wp,cq,wq))
    wp=np.median([o[2] for o in out]); wq=np.median([o[4] for o in out]); dx=np.median([o[3]-o[1] for o in out])
    print('%-34s plate width %4.1f px, painting %4.1f px (x%.2f); centre moved %+.1f px   rows: %s'%(name,wp,wq,wq/max(wp,0.1),dx,' '.join('%.0f/%.0f'%(o[2],o[4]) for o in out)))
track('near lamp post (shaft)',0.652,[0.36,0.38,0.40,0.42,0.44])
track('right wall downpipe (upper)',0.791,[0.06,0.10,0.14,0.18,0.22])
track('right wall downpipe (lower)',0.791,[0.30,0.34,0.38,0.42,0.46,0.52])
track('left terrace downpipe A',0.217,[0.33,0.36,0.40,0.43])
track('left terrace downpipe B',0.280,[0.34,0.37,0.40,0.43])
track('left front house pipe',0.013,[0.28,0.32,0.36,0.40,0.44])
track('chimney (whole width)',0.4305,[0.15,0.20,0.25,0.30],half=60)
