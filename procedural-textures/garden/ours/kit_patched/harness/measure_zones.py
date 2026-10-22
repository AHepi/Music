# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P6 (no weeds or moss on the crown or the traffic lanes: zero). Four tests, each with its own number:
#   fields   the habitat fields (moss_site, weed_site, lichen_site, and algae_site off keep-clear places) are exactly 0.0 wherever footfall >= 0.6, crown >= 0.7 or keepclear >= 0.5
#            (read from the scene's mask pack, plain Python; the same test the reader makes when it builds the pack)
#   pieces   no 3D piece (from a pieces list [{x, y, z, kind}]) stands in those zones, within 1 m of a fire (points given), or on a doorstep strip (step_foot >= 0.5)
#   marks    painted marks of the named layers (look.green_layers: layer pictures layer_<key>_<label>_<state>) cover at most 0.2 % of the zone dots in each camera's zones_ picture
#   litter   at most 3 % of the weed pieces stand within 5 cm of a rubbish piece (rubbish pieces list)
# Use:   python3 -I measure_zones.py SET_ID SCENE_ID [--folder PICTURES] [--pieces pieces.json] [--rubbish rubbish_pieces.json] [--fire x,y;x,y] [--look sooty_1926] [--out result.json]
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402
from masks import pack as pack_module  # noqa: E402

ZONES = {'footfall': 0.6, 'crown': 0.7, 'keepclear': 0.5}


def read_gp(set_id, scene_id):
    """{mask name: 2D array (row 0 = low y)} for the ground-frame masks of a scene's pack, plus the manifest."""
    manifest = pack_module.load_manifest(mc.KIT_ROOT, set_id, scene_id)
    cache, out = {}, {}
    for name, entry in manifest['masks']['GP'].items():
        picture = manifest['pictures'][entry['picture']]
        if picture.get('grid') != 'normal':
            continue
        path = os.path.join(manifest['_dir'], picture['file'])
        if path not in cache:
            cache[path] = pack_module.read_png(path)
        out[name] = cache[path][..., 'RGBA'.index(entry['channel'])]
    return out, manifest


def zone_masks(gp):
    zones = {name: gp[name] >= limit for name, limit in ZONES.items() if name in gp}
    if 'step_foot' in gp:
        zones['doorstep'] = gp['step_foot'] >= 0.5
    return zones


def fields_test(gp):
    """Exactly zero inside the zones. Returns dict(ok, worst per field)."""
    zones = {k: v for k, v in zone_masks(gp).items() if k in ZONES}
    out, ok = {}, True
    for field in ('moss_site', 'weed_site', 'lichen_site', 'algae_site'):
        if field not in gp:
            continue
        use = {k: v for k, v in zones.items() if field != 'algae_site' or k == 'keepclear'}
        worst = max((float(gp[field][z].max()) for z in use.values() if z.any()), default=0.0)
        out[field] = worst
        ok &= worst == 0.0
    return dict(ok=ok, worst=out)


def to_cell(manifest, x, y):
    g = manifest['ground']
    return int((x - g['x'][0]) / g['dot_m']), int((y - g['y'][0]) / g['dot_m'])


def pieces_test(gp, manifest, pieces, fire_points=(), rubbish=()):
    zones = zone_masks(gp)
    h, w = next(iter(gp.values())).shape
    counts = {k: 0 for k in zones}
    counts['fire_1m'] = 0
    where = []
    for p in pieces:
        ix, iy = to_cell(manifest, p['x'], p['y'])
        if not (0 <= ix < w and 0 <= iy < h):
            continue
        for name, z in zones.items():
            if z[iy, ix]:
                counts[name] += 1
                where.append((name, p))
        if any((p['x'] - fx) ** 2 + (p['y'] - fy) ** 2 <= 1.0 for fx, fy in fire_points):
            counts['fire_1m'] += 1
    weeds = [p for p in pieces if str(p.get('kind', '')).startswith('weed') or p.get('kind') in ('tuft', 'weed', 'dandelion')]
    near = 0
    if weeds and rubbish:
        rx = np.array([[r['x'], r['y']] for r in rubbish])
        for p in weeds:
            if np.min(np.hypot(rx[:, 0] - p['x'], rx[:, 1] - p['y'])) <= 0.05:
                near += 1
    return dict(ok=sum(counts.values()) == 0 and (not weeds or near / len(weeds) <= 0.03), counts=counts, weeds=len(weeds), weeds_near_rubbish=near, pieces=len(pieces))


def marks_test(settings, folder, look):
    """Painted marks of the look's green layers inside the zones, per camera."""
    out, ok = {}, True
    layers = look.get('green_layers', [])
    for label, light, state, scene_id in mc.t22_list(settings):
        if state != 'wet':
            continue
        w, h = mc.size_of(settings, label)
        zp = mc.pic(folder, f'zones_{mc.camera_of(settings, label)}_{w}x{h}')
        if zp is None:
            continue
        z = mc.read_rgb(zp)
        zone = (z[..., 0] >= 0.6) | (z[..., 1] >= 0.7) | (z[..., 2] >= 0.5)
        cp = mc.pic(folder, f'class_{mc.camera_of(settings, label)}_{w}x{h}')
        if cp is not None:                                    # the ground masks are looked up by world x and y, so they also read on a wall above the spot: ground dots only
            ids = sorted({mc.role_table(settings)[r] for r in settings.expand_roles(settings.geometry['ground']['roles']) if r in mc.role_table(settings)})
            zone &= mc.class_mask(mc.read_class(cp), ids)
        if zone.sum() < 200:
            continue
        for key in layers:
            mp = mc.pic(folder, f'layer_{key}_{label}_{state}')
            if mp is None:
                continue
            share = float((mc.read_channel(mp, 0)[zone] > 0.5).mean())
            out[f'{key}@{label}'] = round(share, 5)
            ok &= share <= 0.002
    return dict(ok=ok, shares=out, layers=layers)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    settings = mc.load_set(args[0])
    gp, manifest = read_gp(args[0], args[1])
    result = {'fields': fields_test(gp)}
    if '--pieces' in opts:
        fire = [tuple(float(v) for v in pt.split(',')) for pt in opts.get('--fire', '').split(';') if pt]
        result['pieces'] = pieces_test(gp, manifest, json.load(open(opts['--pieces'])), fire, json.load(open(opts['--rubbish'])) if '--rubbish' in opts else ())
    if '--folder' in opts:
        look = json.load(open(os.path.join(mc.KIT_ROOT, 'presets', opts.get('--look', 'sooty_1926') + '.json')))
        result['marks'] = marks_test(settings, opts['--folder'], look)
    if '--out' in opts:
        mc.jdump(result, opts['--out'])
    print(json.dumps(result, indent=1))
