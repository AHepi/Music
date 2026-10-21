# What this file does (plain words): writes results/picture_info.json and results/sheet_config.json (the labels, notes and crop places of the sheets) from the measured numbers, so that the sheets say what the numbers say.
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.abspath(os.path.join(HERE, '..', 'results'))
m = {}
for f in ('main', 'lockout', 'close_views'):
    m.update(json.load(open(f'{R}/pair_measurements_{f}.json')))
info = {}
for n in m:
    info[n] = '64 samples, ray tracing, shadow rays 4 / steps 16' if n.endswith('_eevee') else '512 samples (adaptive), OptiX denoiser, RTX 4090'
for n in ('brick_wet_eevee', 'brick_wet_cycles'):
    info[n] = info.get(n, '')
json.dump(info, open(R + '/picture_info.json', 'w'), indent=1)

def line(a, b):
    ea, ec = m[a], m[b]
    return (f"Brightness (mean): EEVEE {ea['mean_L']:.3f}, Cycles {ec['mean_L']:.3f}.   Blown out (over 0.97): {100 * ea['blown']:.2f} % / {100 * ec['blown']:.2f} %.   "
            f"Crushed (under 0.02): {100 * ea['crushed']:.1f} % / {100 * ec['crushed']:.1f} %.")

def joint(a, b):
    ea, ec = m[a], m[b]
    if 'joint' not in ea:
        return None
    def c(e):
        j = e['joint']
        return f"near {j['near']['contrast']:.2f}, middle {j['middle']['contrast']:.2f}"
    return f"Sett joint contrast (study measure): EEVEE {c(ea)};  Cycles {c(ec)}."

cfg = {}
cfg['notes_main_wet'] = [line('main_wet_eevee', 'main_wet_cycles'), joint('main_wet_eevee', 'main_wet_cycles'),
                         f"Road brightness: EEVEE {m['main_wet_eevee']['road_L']:.3f}, Cycles {m['main_wet_cycles']['road_L']:.3f}. Puddles: {m['main_wet_eevee']['puddle_L']:.3f} / {m['main_wet_cycles']['puddle_L']:.3f}."]
cfg['notes_main_dry'] = [line('main_dry_eevee', 'main_dry_cycles'), joint('main_dry_eevee', 'main_dry_cycles'),
                         f"Road brightness: EEVEE {m['main_dry_eevee']['road_L']:.3f}, Cycles {m['main_dry_cycles']['road_L']:.3f}."]
cfg['notes_main_today'] = [line('main_today_eevee', 'main_today_cycles'), joint('main_today_eevee', 'main_today_cycles')]
cfg['notes_lockout'] = [line('lockout_wet_eevee', 'lockout_wet_cycles'), joint('lockout_wet_eevee', 'lockout_wet_cycles'),
                        f"Grid visible (second measure, line / stone grain): EEVEE near {m['lockout_wet_eevee']['grid']['near']['line']}, Cycles near {m['lockout_wet_cycles']['grid']['near']['line']}; both pass the joint pass line."]
cfg['notes_cottage'] = [line('cottage_wet_eevee', 'cottage_wet_cycles')]
cfg['notes_brick'] = [line('brick_wet_eevee', 'brick_wet_cycles')]
for k in cfg:
    cfg[k] = [x for x in cfg[k] if x]
# 100 % crops: (label, eevee picture, cycles picture, (x0, y0) of a 380 x 250 crop)
cfg['crops'] = [
    ['Brick wall (brick cottage)', 'brick_wet_eevee', 'brick_wet_cycles', [960, 230]],
    ['Stone wall under the sill (stone cottage)', 'cottage_wet_eevee', 'cottage_wet_cycles', [840, 540]],
    ['Door, brick and knocker (brick cottage)', 'brick_wet_eevee', 'brick_wet_cycles', [300, 280]],
    ['Door, stone, window (stone cottage)', 'cottage_wet_eevee', 'cottage_wet_cycles', [640, 380]],
    ['Setts in the glare (lockout plate)', 'lockout_wet_eevee', 'lockout_wet_cycles', [760, 2400]],
    ['Gutter, puddle, rubbish (stone cottage)', 'cottage_wet_eevee', 'cottage_wet_cycles', [250, 820]],
]
json.dump(cfg, open(R + '/sheet_config.json', 'w'), indent=1)
print(json.dumps(cfg, indent=1)[:1500])
