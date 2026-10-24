import sys, math
from PIL import Image
F='/home/user/work/paper-pop-up-film-kit/assets/reliefs/inflation-chapter-2/109-bg-factory-gate'
paint=Image.open(F+'.jpg'); depth=Image.open(F+'-depth.png').convert('L')
near,far,fov=6,70,40
ty=math.tan(math.radians(fov/2)); tx=ty*paint.width/paint.height
W,H=depth.size; px=depth.load()
def dist(u,v):
    x=min(W-1,max(0,round(u*(W-1)))); y=min(H-1,max(0,round((1-v)*(H-1))))
    w=px[x,y]/255; return 1/(w/near+(1-w)/far)
def point(u,v):
    d=dist(u,v); return ((u*2-1)*tx*d,(v*2-1)*ty*d,-d)
def card_clear(base,width,height,yaw,n=24):
    least=1e9;where=None
    for i in range(n+1):
        for j in range(n+1):
            lx=(i/n-0.5)*width; ly=j/n*height
            x=base[0]+lx*math.cos(yaw); z=base[2]-lx*math.sin(yaw); y=base[1]+ly
            d=-z; u=(x/d/tx+1)/2; v=(y/d/ty+1)/2
            if not(0<=u<=1 and 0<=v<=1): continue
            c=dist(u,v)-d
            if c<least: least=c;where=(round(lx,2),round(ly,2))
    return least,where
if __name__=='__main__':
    aspect=940/662
    for u in [0.55,0.6,0.64,0.68,0.72]:
      for v in [0.24,0.26,0.28,0.3]:
        b=point(u,v)
        for yaw in [-0.3,-0.15,0]:
          for w in [2.1,2.4]:
            c,wh=card_clear(b,w,w*aspect,yaw)
            if c>0.05: print(f'u{u} v{v} yaw{yaw} w{w} base x{b[0]:.2f} y{b[1]:.2f} z{b[2]:.2f} clear {c:.3f}')

def lift_needed(base,width,height,yaw,need=0.05):
    lo,hi=0.0,1.5
    if card_clear(base,width,height,yaw,30)[0]>=need: return 0.0
    for _ in range(14):
        m=(lo+hi)/2
        if card_clear((base[0],base[1]+m,base[2]),width,height,yaw,30)[0]>=need: hi=m
        else: lo=m
    return hi
