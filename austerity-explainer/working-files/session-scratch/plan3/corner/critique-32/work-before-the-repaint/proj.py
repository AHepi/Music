import math, numpy as np
yaw=math.radians(6.87)
fwd=np.array([-math.sin(yaw), math.cos(yaw), 0]); right=np.array([math.cos(yaw), math.sin(yaw),0]); up=np.array([0,0,1.0])
CAMS={'end':(np.array([3.10,17.85,3.1882]),60.4,1080,1920),'plate':(np.array([2.9931,16.3538,3.1882]),64.4,1536,2730),'start-film':(np.array([2.9931,16.3538,3.1882]),60.4,1080,1920)}
def proj(p,cam):
    c,fov,W,H=CAMS[cam]; d=np.array(p,float)-c
    z=d@fwd; f=(H/2)/math.tan(math.radians(fov/2))
    return 0.5+(d@right)/z*f/W, 0.5-(d@up)/z*f/H, z
if __name__=='__main__':
    for name,p in {'brazier_light':(2.78,22.0,2.93),'corner_lamp_light':(3.72,25.5,5.201),'left_lamp_light':(-2.75,45.0,6.546)}.items():
        print(name, [tuple(round(v,4) for v in proj(p,c)) for c in CAMS])
