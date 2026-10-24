import numpy as np
def lin(s):
    s=np.asarray(s,float)/255; return np.where(s<=0.04045,s/12.92,((s+0.055)/1.055)**2.4)
def srgb(c): return np.where(c<0.0031308,c*12.92,1.055*np.power(np.maximum(c,1e-9),1/2.4)-0.055)
def aces(x): return np.clip((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0,1)
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
def grade(rgb,exposure=1.0,contrast=1.05,saturation=1.0,shadow=(0.44,0.52,0.56),high=(0.56,0.5,0.42),tint=0.35,lift=0.015):
    c=lin(rgb)*exposure
    c=aces(c)
    luma=c@np.array([0.2126,0.7152,0.0722])
    c=luma+(c-luma)*saturation
    c=(c-0.5)*contrast+0.5
    t=np.array(shadow)+(np.array(high)-np.array(shadow))*smooth(0.05,0.75,luma)
    c=c+(c*t*2-c)*tint
    c=c+lift*(1-c)
    c=np.clip(c,0,1)
    return np.round(srgb(c)*255,1)
for p in [(46,39,32),(40,30,20),(60,45,30),(80,60,40),(35,25,18),(90,70,50)]:
    print(p, grade(p), grade(p,exposure=1.6), grade(p,contrast=1.04))
