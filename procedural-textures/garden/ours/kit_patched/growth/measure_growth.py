# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GROWTH LAYER'S MEASURES (plain Python, no Blender): reads the pictures and pieces.json files the runner brought back and works out the plan's pass lines for the growth layer
#     P3  readable at the painter's size (the kit's measure_readable on the growth layer's own mask picture of each plate; 0.45 and 0.40)
#     P4  weed cover, gutter-side tufts, wall-foot plants, moss cushion cover, the species mix and sizes against the period rules; hue of the plants (no bright green)
#     P6  zones: no plant in footfall >= 0.6, crown >= 0.7, keepclear >= 0.5, doorstep strips, within 1 m of a fire; weeds within 5 cm of litter; counted per plate
#     P7  drawing time: best of three plates without and with the plants, time per 1,000 plants
#     P8  amount 0: the picture against the plain one (and the plain one against itself: the renderer's own noise)
#     P2  wet look: the kit's wet measure on the pictures, the plants' own wet over dry brightness
#     P5  not one dark mush: the plates against the frozen baseline plates
# Use:   python3 -I growth/measure_growth.py SET_ID WORK_FOLDER [--out growth_measures.json]
#        WORK_FOLDER holds full_<scene id>/ (the 'full' job set of each scene file), times_<first scene id>/, stress_<first scene id>/, zero_<first scene id>/ as the runner wrote them.
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.path.insert(0, os.path.join(KIT_ROOT, 'harness'))
sys.dont_write_bytecode = True

import cv2  # noqa: E402

import measure_common as mc  # noqa: E402
import measure_readable  # noqa: E402
import measure_zones as mz  # noqa: E402
from masks import pack as pack_module  # noqa: E402
from growth import local_masks  # noqa: E402


def _load_pieces(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name.startswith('pieces_') and name.endswith('.json'):
            d = json.load(open(os.path.join(folder, name)))
            if isinstance(d.get('pieces'), list):            # (the runner's own picture json also has a 'pieces' number: that one is not a list)
                out[name[len('pieces_'):-5]] = d
    return out


def _rubbish(folder, name):
    path = os.path.join(folder, f'rubbish_{name}.json')
    return json.load(open(path)) if os.path.exists(path) else []


def pack_arrays(set_id, scene_id, section):
    """Plain-Python copy of the arrays the layer works from (ground-plan masks, role ids, the private strips)."""
    manifest = pack_module.load_manifest(KIT_ROOT, set_id, scene_id)
    gp, _ = mz.read_gp(set_id, scene_id)
    height = pack_module.read_png(os.path.join(manifest['_dir'], 'gp_height.png'))
    z_lo, z_hi = manifest['ground']['z_range']
    ground_z = z_lo + height[..., 0] * (z_hi - z_lo)
    has = height[..., 1] > 0.5
    role_id = np.round(height[..., 2] * 65.0).astype(int)
    role_names = manifest['stats']['ground']['role_names']
    settings = mc.load_set(set_id)
    sites = local_masks.make_sites(gp, has, role_id, role_names, manifest['ground'], section, float(settings.geometry.get('wall_reach_m', 1.275)))
    return dict(gp=gp, manifest=manifest, ground_z=ground_z, has=has, sites=sites, grid=manifest['ground'])


def camera_pose(settings, camera):
    for spec in settings.get('cameras', []):
        if spec['name'] == camera and spec.get('location') and spec.get('quaternion_wxyz'):
            w, x, y, z = spec['quaternion_wxyz']
            # forward = rotation of (0, 0, -1)
            fx = -2.0 * (x * z + w * y)
            fy = -2.0 * (y * z - w * x)
            fz = -(1.0 - 2.0 * (x * x + y * y))
            return tuple(spec['location']), (fx, fy, fz), float(spec.get('fov_v', 40.0))
    return None


def section_of(settings):
    from growth import growth_names
    return growth_names.growth_section(settings)


# ---------------------------------------------------------------------------------------------------------------------------------------------- P3
def p3(settings, look, folders, scale=0.45):
    rows = [r for r in look.get('readable', []) if r['layer'] == 'growth']
    out = {}
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        res = measure_readable.run(settings, folder, dict(look, readable=rows), scale)
        for tag, entry in res['elements'].items():
            if 'skipped' not in entry or tag not in out:
                out[tag] = entry
    done = {t: e for t, e in out.items() if 'skipped' not in e}
    return dict(scale=scale, elements=out, passed=all(e.get('passed') for e in done.values()) and bool(done))


# ---------------------------------------------------------------------------------------------------------------------------------------------- P6 and P4
def window_stats_for(arrays, section, camera_pose_, distance, cone_cos):
    window = local_masks.window_mask(arrays['grid'], arrays['ground_z'], arrays['has'], camera_pose_[0], distance, camera_pose_[1], cone_cos)
    stats = local_masks.window_stats(arrays['gp'], arrays['sites'], arrays['grid'], arrays['ground_z'], window)
    return window, stats


def p4_p6(settings, folder, name, arrays, section, species, rubbish_folder=None):
    data = json.load(open(os.path.join(folder, f'pieces_{name}.json')))
    rows = data['pieces']
    camera = data.get('camera')
    pose = camera_pose(settings, camera) or (None, None, 40.0)
    rub = _rubbish(folder, name)
    fire = [tuple(p) for p in data.get('fire_points', [])]
    zones = mz.pieces_test(arrays['gp'], arrays['manifest'], rows, fire, rub)
    out = dict(plate=name, camera=camera, plants=len(rows), zone_counts=zones['counts'], weeds=zones['weeds'], weeds_near_litter=zones['weeds_near_rubbish'], rubbish_pieces=len(rub))
    out['p6_passed'] = zones['ok']
    kinds = {}
    for r in rows:
        kinds.setdefault(r['species'], []).append(r['size_m'])
    out['by_species'] = {k: dict(count=len(v), size_cm_p5_p95=[round(float(np.percentile(v, 5)) * 100, 1), round(float(np.percentile(v, 95)) * 100, 1)]) for k, v in kinds.items()}
    if pose[0] is not None:
        distance = float(data.get('calibration', {}).get('distance', 18.0)) if False else 18.0
        import math
        plate = (settings.get('plate') or {}).get('size')
        dot = 2.0 * math.tan(math.radians(pose[2]) / 2.0) / plate[1]
        cone = math.cos(min(math.radians(75.0), math.atan(dot * plate[1] / 2.0) + math.radians(12.0)))
        window, stats = window_stats_for(arrays, section, pose, distance, cone)
        weeds = [r for r in rows if r['kind'].startswith('weed')]
        moss = [r for r in rows if r['kind'] == 'moss_cushion']
        footprint = lambda rs: float(sum(np.pi / 4.0 * r['size_m'] ** 2 for r in rs))   # noqa: E731
        # only plants inside the same window (distance and cone) count
        g = arrays['grid']

        def inside(r):
            ix, iy = int((r['x'] - g['x'][0]) / g['dot_m']), int((r['y'] - g['y'][0]) / g['dot_m'])
            return 0 <= iy < window.shape[0] and 0 <= ix < window.shape[1] and bool(window[iy, ix])
        w_in, m_in = [r for r in weeds if inside(r)], [r for r in moss if inside(r)]
        gut = arrays['sites']['gutter_strip']
        wall = arrays['sites']['wall_strip']

        def in_strip(r, strip):
            ix, iy = int((r['x'] - g['x'][0]) / g['dot_m']), int((r['y'] - g['y'][0]) / g['dot_m'])
            return 0 <= iy < strip.shape[0] and 0 <= ix < strip.shape[1] and strip[iy, ix] > 0.5
        gut_w = sum(r['size_m'] for r in w_in if in_strip(r, gut))
        wall_w = sum(r['size_m'] for r in w_in if in_strip(r, wall))
        out['window'] = dict(area_m2=round(stats['area_m2'], 1), gutter_side_m=round(stats['gutter_side_m'], 1), wall_foot_m=round(stats['wall_foot_m'], 1), distance=distance, cone_cos=round(cone, 3))
        out['weed_cover_visible_ground'] = round(footprint(w_in) / max(stats['area_m2'], 1e-6), 5)
        disc = local_masks.window_mask(arrays['grid'], arrays['ground_z'], arrays['has'], pose[0], distance)
        out['weed_cover_disc_18m'] = round(footprint([r for r in weeds if r['distance'] < distance]) / max(float(disc.sum() * g['dot_m'] ** 2), 1e-6), 5)
        out['moss_cover_visible_ground'] = round(footprint(m_in) / max(stats['area_m2'], 1e-6), 5)
        out['gutter_side_tuft_share'] = round(gut_w / max(stats['gutter_side_m'], 1e-6), 4)
        out['wall_foot_plant_share'] = round(wall_w / max(stats['wall_foot_m'], 1e-6), 4) if stats['wall_foot_m'] > 0 else None
        out['weeds_in_window'], out['moss_in_window'] = len(w_in), len(m_in)
        out['first_15m'] = dict(weeds=sum(1 for r in weeds if r['distance'] <= 15.0), moss=sum(1 for r in moss if r['distance'] <= 15.0))
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------- P7
def p7(folders_base, folders_growth, pieces_by_name):
    """Best of the runs: plates without and with the plants. folders: {tag: folder}."""
    def read(folder):
        out = {}
        for f in os.listdir(folder):
            if f.startswith('plate_') and f.endswith('.json') and 'seconds' in open(os.path.join(folder, f)).read():
                d = json.load(open(os.path.join(folder, f)))
                if 'seconds' in d:
                    out[d['name']] = d
        return out
    result = {}
    for label, folder in folders_growth.items():
        runs = read(folder)
        by_camera = {}
        for name, d in runs.items():
            cam = d['camera']
            tag = name.split('_wet_')[1] if '_wet_' in name else name
            kind = 'base' if tag.startswith('base') else tag.split('_r')[0]
            by_camera.setdefault(cam, {}).setdefault(kind, []).append(d['seconds'])
        rows = {}
        for cam, kinds in by_camera.items():
            base = min(kinds.get('base', [np.nan]))
            row = dict(base_best=base)
            for kind, vals in kinds.items():
                if kind == 'base':
                    continue
                pj = pieces_by_name.get(label, {}).get(f'plate_{cam}_A_wet_{kind}') or pieces_by_name.get(label, {}).get(f'plate_{cam}_A_wet_{kind}_r1')
                count = pj['count'] if pj else None
                best = min(vals)
                row[kind] = dict(best=best, pieces=count, extra_s=round(best - base, 3), extra_share=round((best - base) / base, 4), s_per_1000=(round((best - base) / count * 1000, 3) if count else None))
            rows[cam] = row
        result[label] = rows
    return result


# ---------------------------------------------------------------------------------------------------------------------------------------------- P8
def p8(folder):
    def read(n):
        return cv2.imread(os.path.join(folder, n + '.png'), cv2.IMREAD_UNCHANGED).astype(np.int32)
    base = read('zero_base')
    out = {}
    for n in ('zero_base_again', 'zero_growth_amount0', 'zero_growth_weeds0_cushions0', 'zero_after_layer_off'):
        if not os.path.exists(os.path.join(folder, n + '.png')):
            continue
        d = np.abs(read(n) - base).max(axis=2)
        out[n] = dict(max_step=int(d.max()), dots_differ=int((d > 0).sum()), share_differ=round(float((d > 0).mean()), 5), dots_over_one_step=int((d > 1).sum()), dots=int(d.size))
    noise = out.get('zero_base_again', {})
    out['passed'] = all(v['max_step'] <= max(2, noise.get('max_step', 2)) and v['dots_over_one_step'] <= max(50, 3 * noise.get('dots_over_one_step', 0)) for k, v in out.items() if k != 'zero_base_again')
    out['note'] = 'the plain picture drawn twice differs from itself by the same amount (the renderer\'s own noise), so that is the floor'
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------- P2 and P5
def p2(settings, folders, base_numbers):
    import measure_wet
    result = measure_wet.run(settings, folders, base_numbers)
    ok, fails = measure_wet.judge(result, base_numbers) if base_numbers else (None, [])
    return dict(element_wet_dry=result['element_wet_dry'], failures=fails, passed=ok, wet_to_dry_sample={k: v for k, v in list(result['wet_to_dry'].items())[:3]})


def p5(settings, folder, plate_names):
    import measure_mush
    base_dir = os.path.join(KIT_ROOT, 'harness', 'baseline')
    out = {}
    for name in plate_names:
        try:
            kit_stats, (Lk, cmap, depth) = measure_mush.plate_stats_from_folder(settings, folder, name, os.path.join(base_dir, 'maps'))
            Lb = mc.read_lum(os.path.join(base_dir, 'plates', name + '.png'))
            if Lb.shape != Lk.shape:
                out[name] = dict(skipped='shape differs')
                continue
            res = measure_mush.compare(Lk, Lb, cmap, depth, mc.classes(settings))
            out[name] = dict(ok=res['ok'], failures=res['failures'], plate_mean_ratio=res['plate_mean_ratio'], class_mean_ratio={c: e['m3_mean_ratio'] for c, e in res['classes'].items()})
        except Exception as exc:     # noqa: BLE001
            out[name] = dict(error=repr(exc))
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------------- colours
def colours(folder, label='main', scale=0.45):
    """Hue, saturation and value of the plants' own dots in the plate (the layer's mask), and the bright-green share the period check counts."""
    mask_path = os.path.join(folder, f'layer_growth_plate_{label}.png')
    plate = os.path.join(folder, f'plate_{label}_A_wet.png')
    if not (os.path.exists(mask_path) and os.path.exists(plate)):
        return {}
    m = cv2.imread(mask_path, cv2.IMREAD_UNCHANGED)
    mask = (m[..., 2] > 127) if m.ndim == 3 else (m > 127)
    im = cv2.cvtColor(cv2.imread(plate).astype(np.float32) / 255.0, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0][mask], hsv[..., 1][mask], hsv[..., 2][mask]
    lum = measure_readable.pdc.lum(im)
    ring = (cv2.dilate(mask.astype(np.uint8), np.ones((11, 11), np.uint8)) > 0) & ~mask
    green = (s >= 0.6) & (v >= 0.6) & (h >= 75) & (h <= 160)
    return dict(dots=int(mask.sum()), hue_median=round(float(np.median(h)), 1), hue_p10_p90=[round(float(np.percentile(h, 10)), 1), round(float(np.percentile(h, 90)), 1)], sat_median=round(float(np.median(s)), 3),
                value_median=round(float(np.median(v)), 3), brightness_in_plants=round(float(lum[mask].mean()), 3), brightness_round_plants=round(float(lum[ring].mean()), 3),
                bright_green_dots=int(green.sum()), bright_green_share=round(float(green.mean()), 5))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    opts = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith('--')}
    for v in opts.values():
        if v in args:
            args.remove(v)
    set_id, work = args[0], args[1]
    out_path = opts.get('--out', os.path.join(work, 'growth_measures.json'))
    settings = mc.load_set(set_id)
    look = json.load(open(os.path.join(KIT_ROOT, 'presets', settings.default_look() + '.json')))
    section = section_of(settings)
    scenes = [s['id'] for s in settings.scenes]
    folders = {sid: os.path.join(work, f'full_{sid}') for sid in scenes}
    first = scenes[0]
    result = {}
    base_numbers = json.load(open(os.path.join(KIT_ROOT, 'harness', 'baseline', 'numbers.json'))).get('wet')
    result['P3_045'] = p3(settings, look, list(folders.values()), 0.45)
    result['P3_040'] = p3(settings, look, list(folders.values()), 0.40)
    arrays = {sid: pack_arrays(set_id, sid, section) for sid in scenes if os.path.isdir(folders[sid])}
    result['P4_P6'] = {}
    for sid, folder in folders.items():
        if not os.path.isdir(folder):
            continue
        for name in sorted(_load_pieces(folder)):
            result['P4_P6'][f'{sid}:{name}'] = p4_p6(settings, folder, name, arrays[sid], section, None)
    result['P6_all_plates_zero'] = all(sum(v['zone_counts'].values()) == 0 for v in result['P4_P6'].values())
    result['P6_litter_share_max'] = max((v['weeds_near_litter'] / v['weeds'] if v['weeds'] else 0.0) for v in result['P4_P6'].values()) if result['P4_P6'] else None
    t_pieces = {}
    for prefix in ('times', 'stress'):
        folder = os.path.join(work, f'{prefix}_{first}')
        if os.path.isdir(folder):
            t_pieces[f'{prefix}_{first}'] = _load_pieces(folder)
    result['P7'] = p7(None, {k: os.path.join(work, k) for k in t_pieces}, t_pieces)
    zero_folder = os.path.join(work, f'zero_{first}')
    if os.path.exists(os.path.join(zero_folder, 'zero_base.png')):
        result['P8_pictures'] = p8(zero_folder)
        json.dump(result['P8_pictures'], open(os.path.join(work, 'measures_p8.json'), 'w'), indent=1)
    elif os.path.exists(os.path.join(work, 'measures_p8.json')):
        result['P8_pictures'] = json.load(open(os.path.join(work, 'measures_p8.json')))      # the big pictures were deleted after the first measure (disk)
    result['P2'] = {sid: p2(settings, [folder], base_numbers) for sid, folder in folders.items() if os.path.isdir(folder)}
    plates = [f'plate_{c}_{l}_{st}' for c, l, st in (settings.get('test_set') or {}).get('plates', []) if (settings.get('test_set') or {}).get('scene_of', {}).get(c, first) == first]
    result['P5'] = p5(settings, folders[first], plates)
    result['colours'] = colours(folders[first], (settings.get('test_set') or {}).get('plates', [['main']])[0][0])
    json.dump(result, open(out_path, 'w'), indent=1, default=str)
    print(json.dumps({k: (v if k in ('P6_all_plates_zero', 'P6_litter_share_max') else '...') for k, v in result.items()}, indent=1))


if __name__ == '__main__':
    main()
