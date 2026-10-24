"""Checker's own re-measurement: how bright the road arrives in the stage compared with the painting (plate view, first frame).
Own code, own road mask read from the first test's surface masks (read only). Uses cv2 and numpy only."""
import json, cv2, numpy as np
R='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
k=np.tan(np.radians(20))/np.tan(np.radians(22))
def central(img, interp=cv2.INTER_AREA):
    h,w=img.shape[:2]; ch,cw=int(round(h*k)),int(round(w*k)); y0,x0=(h-ch)//2,(w-cw)//2
    return cv2.resize(img[y0:y0+ch,x0:x0+cw],(1080,1920),interpolation=interp)
f=json.load(open(R+'painter_test/alignment/facts_surfaces/facts.json'))
ids=cv2.cvtColor(cv2.imread(R+'painter_test/alignment/facts_surfaces/ids.png'),cv2.COLOR_BGR2RGB).astype(int)
road=np.abs(ids-np.array(f['groups']['road']['colour'])).sum(axis=2)<24
h,w=road.shape; ch,cw=int(round(h*k)),int(round(w*k)); y0,x0=(h-ch)//2,(w-cw)//2
roadc=cv2.resize(road[y0:y0+ch,x0:x0+cw].astype(np.uint8),(1080,1920),interpolation=cv2.INTER_NEAREST)
roadc=cv2.erode(roadc,np.ones((4,4),np.uint8))>0
def lum(rgb): return 0.2126*rgb[...,0]+0.7152*rgb[...,1]+0.0722*rgb[...,2]
def rd(p): return cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB).astype(np.float32)/255
paint=lum(central(rd(R+'painter_round_2/paint/front_painting_final.png')))
base=R+'painter_round_2/stage/stills/'
for tag in ('before','after'):
    s=lum(rd(base+tag+'/wet_projector/still-6.00.jpg'))
    dark=roadc&(paint>0.08)&(paint<0.22)
    crushed=roadc&(paint>0.08)&(s<0.03)
    print(tag,'road stage/painting %.3f'%(s[roadc].mean()/paint[roadc].mean()),
          'dark parts %.3f'%(s[dark].mean()/paint[dark].mean()),
          'crushed share %.4f'%(crushed.sum()/roadc.sum()))
# first test painting for reference through the real stage? (first test stage still)
print('my road px',roadc.sum(),'painting road mean %.3f'%paint[roadc].mean())
for tag in ('before','after'):
    s=lum(rd(base+tag+'/wet_projector/still-6.00.jpg')); print(tag,'stage road mean %.3f'%s[roadc].mean())
