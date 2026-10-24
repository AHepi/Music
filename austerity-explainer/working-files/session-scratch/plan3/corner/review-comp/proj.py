import math, numpy as np
R=math.tan(math.radians(4))
W,H=1080,1920
def cam(x=2.96,y=17.85,eye=1.81,yaw=6.87,fov=60.4):
    return (x,y,y*R+0.13+eye,yaw,fov)
def project(c,p):
    x,y,z,yaw,fov=c; yw=math.radians(yaw)
    a=np.array([-math.sin(yw),math.cos(yw),0]); r=np.array([math.cos(yw),math.sin(yw),0]); u=np.array([0,0,1.])
    v=np.array(p)-np.array([x,y,z]); d=v@a
    f=(H/2)/math.tan(math.radians(fov)/2)
    return np.array([W/2+f*(v@r)/d, H/2-f*(v@u)/d]), d
def line_img(c,lx,hz,y0,y1):
    a,_=project(c,(lx,y0,y0*R+hz)); b,_=project(c,(lx,y1,y1*R+hz)); return a,b
MEET=np.array([0.7064,0.4241]); STARTS={'left roofline':(0.0,0.1806),'left kerb':(0.0,0.6014),'right kerb':(0.5794,0.6177)}
def liked_y_at(name,xf):
    s=np.array(STARTS[name]); t=(xf-s[0])/(MEET[0]-s[0]); return s[1]+t*(MEET[1]-s[1])
def our_line(c,name):
    spec={'left roofline':(-4.3,6.44),'left kerb':(-2.5,0.13),'right kerb':(2.5,0.13)}[name]
    a,b=line_img(c,spec[0],spec[1],c[1]+6,c[1]+300)
    return a/np.array([W,H]), b/np.array([W,H])
if __name__=='__main__':
    c=cam()
    vp,_=project(c,(2.96-1000*math.sin(0),17.85+1e5,1e5*R)); print('VP',vp/np.array([W,H]))
    for n in STARTS:
        a,b=our_line(c,n)
        # y at x = start x and at x = 0.3 / 0.5
        for xf in ([0.0,0.2,0.4] if n!='right kerb' else [0.58,0.62,0.66]):
            t=(xf-a[0])/(b[0]-a[0]); yo=a[1]+t*(b[1]-a[1])
            print(f'{n:14s} x={xf:.2f}  ours y={yo:.4f}  liked y={liked_y_at(n,xf):.4f}  diff px={ (yo-liked_y_at(n,xf))*H:6.1f}')
        ang_o=math.degrees(math.atan2((b[1]-a[1])*H,(b[0]-a[0])*W)); s=np.array(STARTS[n]); ang_l=math.degrees(math.atan2((MEET[1]-s[1])*H,(MEET[0]-s[0])*W))
        print(f'   angle ours {ang_o:.1f}  liked {ang_l:.1f}')
