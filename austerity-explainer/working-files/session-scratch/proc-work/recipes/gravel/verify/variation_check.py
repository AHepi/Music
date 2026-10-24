# Verifier script: independent check of the 8 builder variations (and my own S_v4 bake): pairwise pixel difference, difference to the reference,
# stone share / big-stone share / soil share, their spread across variations vs the claimed window spread, and a look at whether they are copies.
import glob, itertools, json, os, sys
import cv2, numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/gravel'
sys.path.insert(0, os.path.join(G, 'generator'))
import preview_tools as pt
ref = cv2.imread('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reference/gravel/colour.png')
files = sorted(glob.glob(G + '/variations/out/sample_*/colour.png'))
imgs = {os.path.basename(os.path.dirname(f)): cv2.imread(f) for f in files}
imgs['S_v4_myBake'] = cv2.imread(G + '/verify/S_v4/colour.png')
imgs['S_v4_builder'] = cv2.imread(G + '/outputs/S_v4/colour.png')
d = lambda a, b: float(np.abs(a.astype(float) - b.astype(float)).mean())
print('mean abs difference my S_v4 bake vs builder S_v4 bake:', d(imgs['S_v4_myBake'], imgs['S_v4_builder']), 'identical bytes:', bool((imgs['S_v4_myBake'] == imgs['S_v4_builder']).all()))
print('reference vs variations (mean abs diff over all dots):', {k: round(d(ref, v), 1) for k, v in imgs.items() if k.startswith('sample')})
vs = [k for k in imgs if k.startswith('sample')]
pairs = [d(imgs[a], imgs[b]) for a, b in itertools.combinations(vs, 2)]
print('pair differences min/mean/max', round(min(pairs), 2), round(float(np.mean(pairs)), 2), round(max(pairs), 2))
# best-shift correlation between variants (is one a shifted copy of another?)
def ncc_peak(a, b):
    a = (a - a.mean()) / (a.std() + 1e-9); b = (b - b.mean()) / (b.std() + 1e-9)
    return float((np.fft.ifft2(np.fft.fft2(a) * np.conj(np.fft.fft2(b))).real / a.size).max())
g = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
print('max best-shift correlation between variants', round(max(ncc_peak(g(imgs[a]), g(imgs[b])) for a, b in itertools.combinations(vs, 2)), 3), ' variant vs reference', round(max(ncc_peak(g(imgs[a]), g(ref)) for a in vs), 3))
# stone share and granulometry
m_ref = pt.measure(ref)
rows = {}
for k, v in imgs.items():
    m = pt.measure(v)
    rows[k] = m
print('stone share: reference %.3f' % m_ref['stone_share'])
sh = [rows[k]['stone_share'] for k in vs]
print('variant stone shares', [round(x, 3) for x in sh], 'mean %.3f relative spread %.3f' % (np.mean(sh), np.std(sh) / np.mean(sh)))
print('S_v4 mine stone share %.3f' % rows['S_v4_myBake']['stone_share'])
big = lambda m: m['stone_gran'][8]            # stone surviving opening radius 12 (index: 0 share, then RADII)
print('stone surviving opening radius 12: reference %.3f variants %s' % (m_ref['stone_gran'][8], [round(big(rows[k]), 3) for k in vs]), 'S_v4', round(big(rows['S_v4_myBake']), 3))
print('stone granulometry ref', np.round(m_ref['stone_gran'], 3).tolist())
print('stone granulometry var01', np.round(rows['sample_01']['stone_gran'], 3).tolist())
print('soil share ref %.3f' % m_ref['soil_gran'][0], 'variants', [round(rows[k]['soil_gran'][0], 3) for k in vs])
print('mean RGB ref', ref.reshape(-1, 3).mean(0)[::-1].round(1).tolist(), 'S_v4', imgs['S_v4_myBake'].reshape(-1, 3).mean(0)[::-1].round(1).tolist(), 'var', [imgs[k].reshape(-1, 3).mean(0)[::-1].round(0).tolist() for k in vs[:3]])
print('mean lightness ref', float(cv2.cvtColor(ref, cv2.COLOR_BGR2Lab)[..., 0].mean() * 100 / 255), 'S_v4', float(cv2.cvtColor(imgs['S_v4_myBake'], cv2.COLOR_BGR2Lab)[..., 0].mean() * 100 / 255))
# different seeds in the descriptions?
ds = [json.load(open(G + f'/variations/descriptions/{k}.json')) for k in vs]
print('seeds', [(x['stones']['seed'], x['soil']['seed']) for x in ds])
print('class counts', [[c['count'] for c in x['stones']['classes']] for x in ds])
