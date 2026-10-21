import sys; sys.path.insert(0,'scripts')
from common import *
from PIL import Image
def pair_crop(name, box, scale=1, out=None, label=True):
    p,q=PAIRS[name]
    a=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB); b=cv2.cvtColor(cv2.imread(WORK+f"/{name}_painting_registered.png"),cv2.COLOR_BGR2RGB)
    x0,y0,x1,y1=box
    ca=a[y0:y1,x0:x1]; cb=b[y0:y1,x0:x1]
    if scale!=1:
        ca=cv2.resize(ca,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST); cb=cv2.resize(cb,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    sheet=np.concatenate([ca,np.full((ca.shape[0],6,3),255,np.uint8),cb],1)
    Image.fromarray(sheet).save(out,quality=90)
if __name__=='__main__':
    C=WORK
    pair_crop('corner_dry',(700,2000,1300,2500),1,C+"/c_corner_flags.jpg")
    pair_crop('corner_dry',(0,1700,600,2200),1,C+"/c_corner_setts_left.jpg")
    pair_crop('lockout_dry',(850,1800,1450,2300),1,C+"/c_lockout_drum_ground.jpg")
    pair_crop('lockout_dry',(900,1100,1500,1600),1,C+"/c_lockout_wall_right.jpg")
