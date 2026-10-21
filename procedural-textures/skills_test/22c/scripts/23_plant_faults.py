# What this does (plain words)
# Trial 22c, part 1d: plants faults in the wet plate (as pictures only, no Blender scene needed) to see whether the lighting skill's verdict notices them:
#   F1 everything four stops brighter (blown highlights), F2 flattened to a low-contrast grey (muddy), F3 a bright white disc in the top-left corner of the frame
#   (a competing focal point, the "bright window" mistake), judged with the headframe as the subject. Pictures go to out/faults. No render, no GPU.
import json, os, sys
import numpy as np
import bpy
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-lighting-rendering/scripts')
import bx_light as BL
out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
src = os.path.join(out, '..', 'light', 'main_wet.png')
rgb = BL.load_rgba(src)[..., :3]
mask = np.load(os.path.join(out, '..', 'light', 'mask_colliery_wet.npy')) / 255.0
H, W = rgb.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
variants = {}
variants['F0_untouched'] = rgb
variants['F1_blown_four_stops_up'] = np.clip(rgb * 16.0 ** 0.5 * 2.0 ** 0.0, 0, 1)    # display values x4 (about two stops in display terms)
mean = rgb.mean()
variants['F2_flattened_muddy'] = rgb * 0.15 + mean * 0.85
disc = (xx - 60) ** 2 + (yy - 70) ** 2 < 45 ** 2
f3 = rgb.copy()
f3[disc] = 1.0
variants['F3_bright_disc_top_left'] = f3
res = {}
for name, im in variants.items():
    p = os.path.join(out, name + '.png')
    BL.save_png(im, p)
    rep = BL.analyse(p, mask)
    res[name] = {'verdict': BL.verdict(rep), 'clip_pct': rep['clip_pct'], 'value_range': rep['value_range'], 'focus': rep['focus'], 'subject_minus_ring': rep['subject']['minus_ring'], 'squint_on_subject': rep['squint'].get('max_on_subject')}
json.dump(res, open(os.path.join(out, 'faults.json'), 'w'), indent=1)
for k, v in res.items():
    print('FAULT', k, json.dumps(v))
