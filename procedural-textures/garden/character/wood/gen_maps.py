"""gen_maps.py - makes the normal maps of the wood builder into maps/ (numpy + PIL, no Blender). Run: python3 gen_maps.py [outdir]"""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wood_maps as wm
from normal_tools import height_to_normal, to_rgb
from PIL import Image

def save_rgb(path, rgb):
    Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)

def make_all(out=None, seed=1):
    out = out or os.path.join(HERE, 'maps')
    os.makedirs(out, exist_ok=True)
    stats = {}
    h = wm.plank_top_height(2048, 512, seed=3 + seed)
    hc = wm.calibrate_height(h, 30.0)
    n = height_to_normal(hc, strength=1.0, tile=True)
    save_rgb(os.path.join(out, 'plank_top_normal.png'), to_rgb(n))
    cav = wm.plank_cavity(h)
    save_rgb(os.path.join(out, 'plank_top_cavity.png'), np.stack([cav] * 3, -1))
    np.save(os.path.join(out, '_h_plank_top.npy'), hc.astype(np.float16))
    stats['plank_top'] = n
    h = wm.end_grain_height(1024, seed=5 + seed)
    hc = wm.calibrate_height(h, 28.0)
    n = height_to_normal(hc, strength=1.0, tile=True)
    save_rgb(os.path.join(out, 'end_grain_normal.png'), to_rgb(n)); np.save(os.path.join(out, '_h_end_grain.npy'), hc.astype(np.float16))
    stats['end_grain'] = n
    h = wm.post_timber_height(1024, 2048, seed=9 + seed)
    hc = wm.calibrate_height(h, 30.0)
    n = height_to_normal(hc, strength=1.0, tile=True)
    save_rgb(os.path.join(out, 'post_timber_normal.png'), to_rgb(n)); np.save(os.path.join(out, '_h_post_timber.npy'), hc.astype(np.float16))
    stats['post_timber'] = n
    # stone: from rock_08_disp_1k.jpg when present
    src = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps/rock_08_disp_1k.jpg'
    if os.path.exists(src):
        d = np.asarray(Image.open(src).convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255.0
        h = wm.stone_height_from(d, blur_px=11.0)
    else:
        h = wm.soft_stone_height(1024)
    hc = wm.calibrate_height(h, 26.0)
    n = height_to_normal(hc, strength=1.0, tile=True)
    save_rgb(os.path.join(out, 'footing_stone_normal.png'), to_rgb(n)); np.save(os.path.join(out, '_h_footing_stone.npy'), hc.astype(np.float16))
    stats['footing_stone'] = n
    for k, n in stats.items():
        rgb = to_rgb(n)
        print("MAP %-14s size %s mean RGB %.3f %.3f %.3f  (blue>=0.85 %s)  p99 tilt %.1f deg" % (k, n.shape[:2][::-1], rgb[..., 0].mean(), rgb[..., 1].mean(), rgb[..., 2].mean(), rgb[..., 2].mean() >= 0.85,
              np.degrees(np.arccos(np.clip(np.percentile(n[..., 2], 1), -1, 1)))))
    return stats

if __name__ == '__main__':
    make_all(sys.argv[1] if len(sys.argv) > 1 else None)
