# Checker's own semantic test of normal maps: integrate each map to a height field (FFT) and compare with something independent.
# blender -b --python nm_sem.py -- BLEND OUT.json
import bpy, sys, json, numpy as np
BLEND = sys.argv[sys.argv.index('--') + 1]; OUT = sys.argv[sys.argv.index('--') + 2]
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/'
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(BLEND, link=False) as (src, dst):
    dst.images = list(src.images)
def px(im):
    w, h = im.size; n = w * h * im.channels
    a = np.empty(n, dtype=np.float32); im.pixels.foreach_get(a)
    return a.reshape(h, w, im.channels)
def integrate(nrm):
    # OpenGL tangent normal: n = (-dh/dx, -dh/dy, 1) normalised; rows go +V (bottom to top in Blender pixel order)
    nx = nrm[..., 0] * 2 - 1; ny = nrm[..., 1] * 2 - 1; nz = np.maximum(nrm[..., 2] * 2 - 1, 0.2)
    gx = -nx / nz; gy = -ny / nz
    H, W = gx.shape
    fx = np.fft.fftfreq(W)[None, :] * 2j * np.pi; fy = np.fft.fftfreq(H)[:, None] * 2j * np.pi
    GX = np.fft.fft2(gx); GY = np.fft.fft2(gy)
    den = (fx * np.conj(fx) + fy * np.conj(fy)); den[0, 0] = 1
    Hf = (np.conj(fx) * GX + np.conj(fy) * GY) / den; Hf[0, 0] = 0
    return np.real(np.fft.ifft2(Hf))
def corr(a, b):
    a = a - a.mean(); b = b - b.mean(); d = np.sqrt((a * a).sum() * (b * b).sum()); return float((a * b).sum() / d) if d > 0 else 0.0
res = {}
for im in bpy.data.images:
    if im.size[0] < 256 or im.channels < 3 or im.name.endswith('.exr'): continue
    a = px(im)
    m = a[..., :3].reshape(-1, 3).mean(axis=0)
    if not (abs(m[0] - .5) < .05 and abs(m[1] - .5) < .05 and m[2] > .8): continue   # only normal maps
    h = integrate(a[..., :3])
    d = {'size': list(im.size), 'h_std': float(h.std()), 'h_skew': float(((h - h.mean()) ** 3).mean() / (h.std() ** 3 + 1e-9))}
    res[im.name] = d
# plank grain map vs the cavity (groove) picture the wood stage uses for darkening grooves
cav = bpy.data.images.load(G + 'fix/wood/maps/plank_top_cavity.png')
cav.colorspace_settings.name = 'Non-Color'
c = px(cav)[..., 0]
for name, d in res.items():
    if 'plank' in name.lower() and 'normal' in name.lower() and tuple(d['size']) == tuple(cav.size):
        h = integrate(px(bpy.data.images[name])[..., :3])
        d['corr_integrated_height_with_cavity'] = corr(h, c)
        d['corr_flipped_green_control'] = None
res['_cavity_size'] = list(cav.size)
json.dump(res, open(OUT, 'w'), indent=1)
print('NM SEM DONE', len(res))
for k, v in res.items(): print(k, v)
