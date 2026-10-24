import cv2, numpy as np, sys
REF='/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg'
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/'
NOW=B+'final/composed-end-4.png'; OLD=B+'composed-end-2.png'
def crop(p, x0,y0,x1,y1, scale=1.0):
    im=cv2.imread(p); h,w=im.shape[:2]
    c=im[int(y0*h):int(y1*h), int(x0*w):int(x1*w)]
    return cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC)
# right-hand story group, top of lamp to pail
for name,(p,box) in {'ref':(REF,(0.55,0.08,1.0,1.0)),'now':(NOW,(0.40,0.08,1.0,1.0)),'old':(OLD,(0.45,0.08,1.0,1.0))}.items():
    c=crop(p,*box); s=900/c.shape[0]; c=cv2.resize(c,None,fx=s,fy=s,interpolation=cv2.INTER_AREA); cv2.imwrite(f'group_{name}.png',c)
# lamp head
for name,(p,box) in {'ref':(REF,(0.70,0.10,0.88,0.26)),'now':(NOW,(0.78,0.10,0.96,0.25))}.items():
    c=crop(p,*box); s=500/c.shape[0]; cv2.imwrite(f'lamp_{name}.png',cv2.resize(c,None,fx=s,fy=s))
# drum top + chair seat
for name,(p,box) in {'ref':(REF,(0.48,0.62,0.97,0.80)),'now':(NOW,(0.42,0.61,0.90,0.78))}.items():
    c=crop(p,*box); s=500/c.shape[0]; cv2.imwrite(f'drumseat_{name}.png',cv2.resize(c,None,fx=s,fy=s))
# notice
for name,(p,box) in {'ref':(REF,(0.72,0.44,0.94,0.68)),'now':(NOW,(0.69,0.49,0.90,0.66))}.items():
    c=crop(p,*box); s=600/c.shape[0]; cv2.imwrite(f'notice_{name}.png',cv2.resize(c,None,fx=s,fy=s))
