# NOTE (plain words): my own re-measure of "the film's stage makes the wet painting darker than painted" (helper: road arrives at 0.75 of painted brightness for the wet painting, 0.92 for the dry one).
# Done differently: I cut the painting to the stage's narrower lens (same geometry the helper gives), then compare road brightness with a mask made from Blender's road picture (not the helper's colour-key masks), and also look at the dark-to-light curve with matched pixel pairs (blurred) in 5 brightness bins. Reads pictures only.
import cv2, numpy as np
B='proc-work/street_wet/painter_test'
W,H=1080,1920
def lum(im):
    b,g,r=[im[:,:,i].astype(np.float32)/255 for i in range(3)]; return 0.2126*r+0.7152*g+0.0722*b
k=np.tan(np.radians(20))/np.tan(np.radians(22))
def central(img,interp=cv2.INTER_AREA):
    h,w=img.shape[:2]; ch,cw=int(round(h*k)),int(round(w*k)); y0,x0=(h-ch)//2,(w-cw)//2
    return cv2.resize(img[y0:y0+ch,x0:x0+cw],(W,H),interpolation=interp)
road=cv2.imread(B+'/alignment/facts_surfaces/solo/road.png').max(axis=2)>100
roadc=(central(road.astype(np.uint8)*255,cv2.INTER_NEAREST)>128)
roadc=cv2.erode(roadc.astype(np.uint8),np.ones((7,7),np.uint8))>0
pw=cv2.resize(cv2.imread(B+'/pictures/wet_painting_lined_up.png'),(W,H),interpolation=cv2.INTER_AREA)
pd=cv2.resize(cv2.imread('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg'),(W,H),interpolation=cv2.INTER_AREA)
sw=cv2.imread(B+'/stage/stills/wet_projector/still-6.00.jpg'); sd=cv2.imread(B+'/stage/stills/dry_projector/still-6.00.jpg')
print('stage still size',sw.shape)
for name,p,s in (('dry',pd,sd),('wet',pw,sw)):
    a=lum(central(p)); b=lum(s)
    print(name,'road mean painted',round(float(a[roadc].mean()),3),'in stage',round(float(b[roadc].mean()),3),'ratio',round(float(b[roadc].mean()/a[roadc].mean()),3))
    # curve by bins of blurred painted brightness
    A=cv2.GaussianBlur(a,(0,0),4)[roadc]; Bb=cv2.GaussianBlur(b,(0,0),4)[roadc]
    edges=[0,0.1,0.2,0.3,0.45,1.01]
    row=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        m=(A>=lo)&(A<hi)
        row.append('%.2f-%.2f: n=%d painted %.3f stage %.3f'%(lo,hi,m.sum(),A[m].mean() if m.sum() else float('nan'),Bb[m].mean() if m.sum() else float('nan')))
    print('   '+'\n   '.join(row))
