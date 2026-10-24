import json, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-4k/sonnet_work'
x0,x1,y0,y1 = [float(v) for v in sys.argv[1:5]]; S=float(sys.argv[5]); outp=sys.argv[6]
d=json.load(open(W+'/objs.json')); insp=json.load(open(W+'/inspect.json'))
h=np.load(W+'/height.npz'); H,xs,ys=h['H'],h['xs'],h['ys']
w=int((x1-x0)*S); hh=int((y1-y0)*S)
def P(x,y): return ((x-x0)*S, (y1-y)*S)
# height shading
img=Image.new('RGB',(w,hh),(200,220,180))
px=img.load()
for j in range(hh):
    y=y1-j/S
    jj=int(round(y-ys[0]))
    if jj<0 or jj>=len(ys): continue
    for i in range(0,w):
        x=x0+i/S; ii=int(round(x-xs[0]))
        if ii<0 or ii>=len(xs): continue
        z=H[jj,ii]
        if np.isnan(z): continue
        c=int(np.clip(150+z*12,0,255)); px[i,j]=(c,c,int(c*0.8))
dr=ImageDraw.Draw(img)
def catmull(ctrl, per=40):
    P_=np.asarray(ctrl,float); P_=np.vstack([2*P_[0]-P_[1],P_,2*P_[-1]-P_[-2]]); out=[]
    t=np.linspace(0,1,per,endpoint=False)[:,None]
    for i in range(1,len(P_)-2):
        p0,p1,p2,p3=P_[i-1],P_[i],P_[i+1],P_[i+2]
        out.append(0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t**2+(-p0+3*p1-3*p2+p3)*t**3))
    out.append(P_[-2][None,:]); return np.vstack(out)
roads=[[(-135,-50),(-105,-40),(-82,-36),(-64,-27),(-50,-24),(-36,-22),(-22,-15),(-8,-12),(6,-6),(20,-5),(34,-1),(48,3),(60,10),(74,11),(92,17),(120,22),(150,30)],
[(6.5,-6.0),(4.5,1.5),(3.5,9.5),(6.0,17.5),(9.5,24.5),(13.0,30.5),(14.0,33.0)],[(48,3),(49,12),(52,21),(55.5,28),(58,32)]]
for r in roads:
    pts=catmull(r); dr.line([P(*p) for p in pts], fill=(150,110,70), width=max(1,int(4*S)))
pv=np.load(W+'/pudv.npy')
for v in pv[::3]:
    if x0<v[0]<x1 and y0<v[1]<y1: dr.point(P(v[0],v[1]), fill=(40,90,220))
for o in d['Undergrowth']:
    x,y=o['loc'][:2]
    if x0<x<x1 and y0<y<y1: dr.point(P(x,y), fill=(60,120,60))
for o in d['Trees']:
    x,y=o['loc'][:2]
    if not (x0-10<x<x1+10 and y0-10<y<y1+10): continue
    r=0.5*((o['mx'][0]-o['mn'][0])+(o['mx'][1]-o['mn'][1]))/2
    a=P(x-r,y+r); b=P(x+r,y-r)
    dr.ellipse([a,b], outline=(0,110,0))
    c=P(x,y); dr.ellipse([c[0]-2,c[1]-2,c[0]+2,c[1]+2], fill=(90,50,20))
objs=insp['objs']
for k,col in (('Buildings',(200,0,0)),('Props',(255,140,0)),('Fences',(120,80,40))):
    for o in objs[k]:
        n,t,loc,yaw,mn,mx=o
        if k=='Fences': continue
        dr.rectangle([P(mn[0],mx[1]),P(mx[0],mn[1])], outline=col)
        if k=='Buildings' or S>=8: dr.text(P(mn[0],mx[1]), n.replace('Cottage','C').replace('Stable_','S_'), fill=(0,0,0))
import math
for c in insp['cams']:
    x,y,z=c['loc']; rz=math.radians(c['rot'][2])
    fx,fy=-math.sin(rz),math.cos(rz)
    a=P(x,y); b=P(x+fx*8,y+fy*8)
    dr.line([a,b],fill=(255,0,255),width=2); dr.text(a,c['name'],fill=(255,0,255))
for extra in sys.argv[7:]:
    n,x,y,tx,ty=extra.split(',')
    x,y,tx,ty=map(float,(x,y,tx,ty))
    dr.line([P(x,y),P(tx,ty)],fill=(0,0,255),width=2); dr.text(P(x,y),n,fill=(0,0,255))
# grid
for gx in range(int(x0)//10*10, int(x1)+1, 10):
    dr.line([P(gx,y0),P(gx,y1)], fill=(230,230,230)); dr.text(P(gx,y0+1), str(gx), fill=(0,0,0))
for gy in range(int(y0)//10*10, int(y1)+1, 10):
    dr.line([P(x0,gy),P(x1,gy)], fill=(230,230,230)); dr.text(P(x0+0.5,gy), str(gy), fill=(0,0,0))
img.save(outp)
