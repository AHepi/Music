# What this does (plain words): measures the "wear statistics" of a colour picture: how much of it is steel, rust, pale chips and dark stains (each dot
# is put in the nearest of the 16 palette colours of the reference), how far a patch of each kind reaches across and up (autocorrelation length), and how
# unevenly the rust is spread (the spread of the rust share between 96-dot windows). Used to tune the procedural wear so it behaves like the reference.
# Use:  python3 -I wear_stats.py PICTURE.png [OTHER.png ...]     or as a module: stats(rgb)
import json, os, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
PAL=np.array(json.load(open(HERE+'/palette_k16.json'))['rgb'],np.float32)
PAL_LAB=cv2.cvtColor(PAL.reshape(1,-1,3)/255.0,cv2.COLOR_RGB2LAB).reshape(-1,3)
def cls_of(c):
    r,g,b=c
    if r-b>=25: return 'rust'
    if r-b>=10 and r>70: return 'light'
    if (r+g+b)/3>=85: return 'chip'
    if (r+g+b)/3<32 or (r<50 and r-b>=15): return 'dark'
    return 'steel'
NAMES=[cls_of(c) for c in PAL]
def acf_len(m,axis):
    f=m.astype(np.float32)-m.mean(); F=np.fft.fft(f,axis=axis); ac=np.fft.ifft(np.abs(F)**2,axis=axis).real.mean(axis=1-axis); ac/=max(ac[0],1e-9)
    for k in range(1,len(ac)//2):
        if ac[k]<0.37: return k
    return len(ac)//2
def stats(rgb):
    if rgb.shape[0]!=1254: rgb=cv2.resize(rgb,(1254,1254),interpolation=cv2.INTER_AREA)
    lab=cv2.cvtColor(rgb.astype(np.float32)/255.0,cv2.COLOR_RGB2LAB).reshape(-1,3)
    idx=np.zeros(len(lab),np.int32)
    for i in range(0,len(lab),300000): idx[i:i+300000]=((lab[i:i+300000,None,:]-PAL_LAB[None,:,:])**2).sum(-1).argmin(1)
    idx=idx.reshape(1254,1254)
    out={}
    for n in ('steel','rust','light','chip','dark'):
        m=np.isin(idx,[i for i,x in enumerate(NAMES) if x==n])
        win=m[:1254//96*96,:1254//96*96].reshape(13,96,13,96).mean(axis=(1,3))
        out[n]={'share':round(float(m.mean()),3),'len_x':acf_len(m,1),'len_y':acf_len(m,0),'window_std':round(float(win.std()),3)}
    L=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(np.float32)
    out['grey_mean_std']=[round(float(L.mean()),1),round(float(L.std()),1)]
    hp=L-cv2.GaussianBlur(L,(0,0),3); out['highpass_std']=round(float(hp.std()),2)
    return out
def show(name,s):
    print(name.ljust(14),' '.join(f"{n}:{s[n]['share']:.3f}/x{s[n]['len_x']}y{s[n]['len_y']}/w{s[n]['window_std']:.2f}" for n in ('steel','rust','light','chip','dark')),'grey',s['grey_mean_std'],'hp',s['highpass_std'])
if __name__=='__main__':
    show('REFERENCE',stats(cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]))
    for p in sys.argv[1:]: show(os.path.basename(os.path.dirname(p)) or p,stats(cv2.imread(p)[...,::-1]))
