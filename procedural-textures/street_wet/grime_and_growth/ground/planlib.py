import cv2, numpy as np, json, os
BOUNDS_Y=(-12.0,72.0); DOT=0.02
def load(path):
    im=cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.ndim==3: im=im[...,0]
    return im.astype(np.float32)/(65535.0 if im.dtype==np.uint16 else 255.0)
def rows(y0,y1,h=4200):
    return int((BOUNDS_Y[1]-y1)/DOT), int((BOUNDS_Y[1]-y0)/DOT)
def classes(folder):
    c=load(os.path.join(folder,'plan_class.png'))
    ids=np.round(c*64.0).astype(int)
    return ids
ROLE_IDS={'sett':1,'channel':2,'kerb':3,'flag':4}
def crop_view(folder, names, y0, y1, out, scale=0.5, labels=None, gamma=1.0):
    ims=[]
    for i,n in enumerate(names):
        a=load(os.path.join(folder,f'plan_{n}.png'))
        r0,r1=rows(y0,y1)
        a=a[r0:r1]**gamma
        im=(np.clip(a,0,1)*255).astype(np.uint8)
        im=cv2.resize(im,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        im=cv2.cvtColor(im,cv2.COLOR_GRAY2BGR)
        cv2.putText(im,(labels[i] if labels else n),(3,14),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1,cv2.LINE_AA)
        ims.append(im)
    sheet=np.hstack([cv2.copyMakeBorder(i,0,0,0,3,cv2.BORDER_CONSTANT,value=(40,40,40)) for i in ims])
    cv2.imwrite(out,sheet,[cv2.IMWRITE_JPEG_QUALITY,88])
