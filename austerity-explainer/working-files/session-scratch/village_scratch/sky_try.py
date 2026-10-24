# scratch: paint the sky outside Blender, show a flat map and the standard-camera view of it
import sys, time, math
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work/modules')
import numpy as np
from PIL import Image
import village_and_sky as vs
t=time.time()
pic = vs.paint_sky()
print('paint secs', time.time()-t, pic.shape, pic.min(), pic.max())
img8 = (np.clip(pic,0,1)*255).astype(np.uint8)
Image.fromarray(img8).resize((2048,1024), Image.LANCZOS).save('sky_flat.png')
# camera view
def camera_view(pic, cam_az=24.5, pitch=8.5, W=540, H=960, lens=28.0, sensor=36.0, gamma_srgb=False):
    h,w,_=pic.shape
    t=(sensor/2)/lens
    i,j=np.meshgrid(np.arange(W),np.arange(H))
    nx=(2*(i+0.5)/W-1)*(W/H)*t if W<H else (2*(i+0.5)/W-1)*t
    ny=(1-2*(j+0.5)/H)*t if W<H else (1-2*(j+0.5)/H)*t*(H/W)
    az=math.radians(cam_az); pt=math.radians(pitch)
    f=np.array([math.sin(az)*math.cos(pt), math.cos(az)*math.cos(pt), math.sin(pt)])
    r=np.cross(f,[0,0,1]); r/=np.linalg.norm(r); u=np.cross(r,f)
    d=nx[...,None]*r+ny[...,None]*u+f
    d/=np.linalg.norm(d,axis=-1,keepdims=True)
    A=np.degrees(np.arctan2(d[...,0],d[...,1])); e=np.degrees(np.arcsin(d[...,2]))
    uu=np.mod(0.25+A/360.0,1.0)*w-0.5; vv=(90-e)/180*h-0.5
    x0=np.floor(uu).astype(int); y0=np.clip(np.floor(vv).astype(int),0,h-2); fx=(uu-x0)[...,None]; fy=(vv-y0)[...,None]
    x0m=x0%w; x1=(x0+1)%w
    out=(pic[y0,x0m]*(1-fx)+pic[y0,x1]*fx)*(1-fy)+(pic[y0+1,x0m]*(1-fx)+pic[y0+1,x1]*fx)*fy
    return out
view=camera_view(pic)
Image.fromarray((np.clip(view,0,1)*255).astype(np.uint8)).save('sky_cam.png')
np.save('sky_pic.npy', pic.astype(np.float16))
