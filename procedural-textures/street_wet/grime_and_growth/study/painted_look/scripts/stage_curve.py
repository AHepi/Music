"""The film stage's finishing step, written out from film-kit/paper-film/stage/cinema-stage.js (read-only copy of its maths):
sRGB painting -> linear -> x exposure -> ACES filmic -> saturation -> contrast -> tint -> lift -> sRGB -> dark edges (vignette).
Used to say what a painted brightness arrives as in the film."""
import numpy as np
def srgb_to_lin(v):
    v=np.asarray(v,float); return np.where(v<=0.04045,v/12.92,((v+0.055)/1.055)**2.4)
def lin_to_srgb(c):
    c=np.asarray(c,float); return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.maximum(c,0),1/2.4)-0.055)
def aces(x):
    return np.clip((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0,1)
def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
LOOK_LOCKOUT=dict(exposure=1.0,contrast=1.04,saturation=1.0,tintAmount=0.35,lift=0.015,vignette=0.3,
                  shadowTint=(0.44,0.52,0.56),highlightTint=(0.56,0.5,0.42))
def stage_rgb(rgb, look=LOOK_LOCKOUT, edge=1.0):
    """rgb: painting sRGB 0..1, shape (...,3). edge=1 centre of picture, <1 towards corners (vignette). Returns film sRGB (no grain)."""
    c=srgb_to_lin(rgb)*look['exposure']
    c=aces(c)
    luma=c@np.array([0.2126,0.7152,0.0722])
    c=luma[...,None]+(c-luma[...,None])*look['saturation']
    c=(c-0.5)*look['contrast']+0.5
    t=smoothstep(0.05,0.75,luma)[...,None]
    tint=np.array(look['shadowTint'])*(1-t)+np.array(look['highlightTint'])*t
    c=c*(1-look['tintAmount'])+c*tint*2*look['tintAmount']
    c=c+look['lift']*(1-c)
    c=np.clip(c,0,1)
    out=lin_to_srgb(c)
    out=out*(1-look['vignette']*(1-edge))
    return np.clip(out,0,1)
def stage_grey(v, look=LOOK_LOCKOUT, edge=1.0):
    """a neutral grey painted at brightness v (0..1) -> film brightness (Rec.709 weights of the output)."""
    v=np.asarray(v,float); rgb=np.stack([v,v,v],-1)
    o=stage_rgb(rgb,look,edge); return o@np.array([0.2126,0.7152,0.0722])
if __name__=='__main__':
    for v in [0.02,0.05,0.08,0.10,0.13,0.17,0.20,0.24,0.30,0.4,0.5,0.7,0.9]:
        print(v, round(float(stage_grey(v)),3))
