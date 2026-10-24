import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
g=cv2.cvtColor(I['plate'],cv2.COLOR_RGB2GRAY)
# brighten plate for edge finding
g2=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(g)
g2=cv2.GaussianBlur(g2,(0,0),1.2)
E=cv2.Canny(g2,30,80)
np.save(O+'/plate_edges.npy',E)
for name in ['paint','behind']:
    p=cv2.cvtColor(I[name],cv2.COLOR_RGB2GRAY)
    base=np.stack([p]*3,-1).astype(np.float32)*0.6+40
    base[E>0]=[255,40,40]
    Image.fromarray(base.clip(0,255).astype(np.uint8)).save(O+'/overlay-plate-edges-on-%s.png'%name)
print('ok')
