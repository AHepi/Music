# measures one round: python3 mround.py FOLDER PLATE_NAME [--mask layer_mask_png] [--cam main]
import sys, os, json
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.path.insert(0, KIT + '/harness'); sys.dont_write_bytecode = True
import numpy as np
import measure_common as mc, measure_mush, measure_readable
settings = mc.load_set('pit_village_street')
BASE_PLATES = KIT + '/harness/baseline/plates/'
def mush(folder, plate, cam='main', size=(1536, 2730), base=None):
    base = base or BASE_PLATES + f'plate_{cam}_A_wet.png'
    Lk = mc.read_lum(os.path.join(folder, plate + '.png'))
    Lb = mc.read_lum(base)
    cmap = mc.read_class(os.path.join(folder, f'class_{cam}_{size[0]}x{size[1]}.png'))
    depth = mc.read_depth(os.path.join(folder, f'depth_{cam}_{size[0]}x{size[1]}.png'))
    return measure_mush.compare(Lk, Lb, cmap, depth, mc.classes(settings)), Lk, Lb, cmap, depth
def short(res, classes=('walls', 'trims', 'colliery', 'roofs', 'chimneys')):
    out = {'plate_ratio': res['plate_mean_ratio']}
    for c in classes:
        e = res['classes'].get(c)
        if not e: continue
        out[c] = dict(m1=e['m1_darkened_third'], m2=e['m2_under_010_rise'], m3=e['m3_mean_ratio'], m4=e['m4_spread_ratio'], m5=e['m5_band_ratios'], mean_base=e['base']['mean'], under010_base=e['base']['share_under_010'])
    out['failures'] = [f for f in res['failures'] if any(f.split(' ')[1].startswith(c) for c in classes)]
    return out
if __name__ == '__main__':
    folder, plate = sys.argv[1], sys.argv[2]
    res, Lk, Lb, cmap, depth = mush(folder, plate)
    print(json.dumps(short(res), indent=1))

def readable(folder, plate, mask_png, zone_class=None, max_m=None, cam='main', size=(1536, 2730), scale=0.45):
    plate_png = os.path.join(folder, plate + '.png')
    mask = mc.read_channel(mask_png, 0) > 0.5
    cmap = mc.read_class(os.path.join(folder, f'class_{cam}_{size[0]}x{size[1]}.png'))
    depth = mc.read_depth(os.path.join(folder, f'depth_{cam}_{size[0]}x{size[1]}.png'))
    if zone_class:
        mask &= mc.class_mask(cmap, mc.classes(settings)[zone_class])
    if max_m:
        mask &= depth <= max_m
    summ, rows = measure_readable.check_element(plate_png, mask, scale)
    return summ
