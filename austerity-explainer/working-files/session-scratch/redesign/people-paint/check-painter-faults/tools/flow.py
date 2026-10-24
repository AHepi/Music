import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def prep(a, s=0.5):
    g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
    g=cv2.resize(g,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    g=cv2.bilateralFilter(g,7,40,5)
    cl=cv2.createCLAHE(clipLimit=3.0,tileGridSize=(16,16))
    return cl.apply(g)
a=prep(I['plate']); b=prep(I['paint'])
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST)
dis=cv2.DISOpticalFlow_create(2)
dis.setUseSpatialPropagation(True)
f=dis.calc(a,b,None)  # flow from plate to painting
np.save(O+'/flow_plate_to_paint.npy',f)
mag=np.hypot(f[...,0],f[...,1])*2  # in full-res plate pixels
print('flow (full-res px): median',np.median(mag),'p90',np.percentile(mag,90),'p99',np.percentile(mag,99))
# film pixel = plate px * 1080/1536 * (film shows middle with narrower lens) -> report plate px
v=np.clip(mag/8.0,0,1)
col=cv2.applyColorMap((v*255).astype(np.uint8),cv2.COLORMAP_INFERNO)
base=cv2.cvtColor(cv2.resize(I['paint'],(a.shape[1],a.shape[0])),cv2.COLOR_RGB2BGR)
over=cv2.addWeighted(base,0.45,col,0.55,0)
cv2.imwrite(O+'/flow-mag.jpg',cv2.resize(over,None,fx=0.75,fy=0.75))
# grid summary
H,W=mag.shape
for gy in range(0,H,H//12):
    print(' '.join('%4.1f'%np.median(mag[gy:gy+H//12,gx:gx+W//8]) for gx in range(0,W,W//8)))
