# verifier script: pixel differences between the builder's 8 baked variations, and against the reference
import sys, itertools, json
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/lib')
import numpy as np, cv2
import pixel_compare as pc
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/wood/'
ref = pc.load_bgr8('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reference/wood/colour.png')
def grey(a): return a @ np.array([0.114,0.587,0.299])
tiles={s:pc.load_bgr8(f'{W}variations/sample_{s}/colour.png') for s in range(101,109)}
gref=grey(ref)
print('variant vs reference: mean abs grey diff, ssim')
for s,t in tiles.items():
    g=grey(t); print(s, round(np.abs(g-gref).mean(),1), round(pc.ssim(g,gref),3), 'mean grey', round(g.mean(),1), 'ref', round(gref.mean(),1))
pairs=[]
for a,b in itertools.combinations(tiles,2):
    ga,gb=grey(tiles[a]),grey(tiles[b]); pairs.append((np.abs(ga-gb).mean(), pc.ssim(ga,gb)))
pairs=np.array(pairs); print('pairs',len(pairs),'mean abs diff',pairs[:,0].mean().round(1),'min',pairs[:,0].min().round(1),'ssim mean',pairs[:,1].mean().round(3),'max',pairs[:,1].max().round(3))
# is any variant a roll/shift of another or of the reference? maximum normalised cross-correlation over all wrap shifts (FFT)
def maxcorr(a,b):
    a=(a-a.mean())/a.std(); b=(b-b.mean())/b.std()
    c=np.fft.ifft2(np.fft.fft2(a)*np.conj(np.fft.fft2(b))).real/a.size
    return c.max()
print('max circular cross-correlation between variants (1.0 would be a shifted copy):')
mm=[]
for a,b in itertools.combinations(tiles,2):
    mm.append(maxcorr(grey(tiles[a]),grey(tiles[b])))
print(' variants pairs: max',round(max(mm),3),'mean',round(float(np.mean(mm)),3))
print(' variants vs reference:',[round(maxcorr(grey(t),gref),3) for t in tiles.values()])
# structure: gap rows
def rowprofile(g): return g.mean(axis=1)
for s,t in tiles.items():
    p=rowprofile(grey(t)); idx=np.argsort(p)[:1]; 
print('lowest-brightness rows per variant:',{s:int(np.argmin(rowprofile(grey(t)))) for s,t in tiles.items()}, 'ref', int(np.argmin(rowprofile(gref))))
