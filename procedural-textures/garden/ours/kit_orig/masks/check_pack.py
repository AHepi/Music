# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CHECKS ON A FINISHED PACK that need the pictures rather than the geometry (plain Python: numpy, OpenCV):
#   shade_side(set, scene)   when the set DECLARES a sun direction (shade.mode 'declared' or a mix with it), the wall fronts that face away from it must read at least 0.2 shadier than the
#                            fronts that face it (mean of the coarse wall-sheet shade picture over each wall sheet; the sheet's front direction is rotated into the world by its matrix)
#     python3 -I masks/check_pack.py SET_ID SCENE_ID [--out result.json]
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import settings as settings_module  # noqa: E402
from masks import pack as pack_module  # noqa: E402


def shade_side(set_id, scene_id):
    settings = settings_module.load_set(set_id)
    shade = settings.get('shade') or {}
    manifest = pack_module.load_manifest(KIT_ROOT, set_id, scene_id)
    sheets = manifest['frames']['sheets']
    if not shade.get('toward_sun') or not sheets or 'shade' not in manifest['masks'].get('WF', {}):
        return dict(passed=None, note='the set declares no sun direction or the scene has no wall sheets: nothing to compare')
    sun = np.array(shade['toward_sun'], float)
    entry = manifest['masks']['WF']['shade']
    atlas = manifest['frames']['atlases'][entry['picture']]
    img = pack_module.read_png(os.path.join(manifest['_dir'], atlas['file']))
    chan = 'RGBA'.index(entry['channel'])
    facing, away = [], []
    for sheet in sheets:
        rect = atlas['rects'][str(sheet['id'])]
        coarse = atlas.get('coarse')
        # coarse atlas rects are in coarse dots already (pack.build writes them per atlas)
        sub = img[rect['y']:rect['y'] + rect['h'], :rect['w'], chan]
        m3 = np.array(sheet['matrix_world'], float)[:3, :3]
        local = np.zeros(3)
        local[sheet['front_axis']] = sheet['front_sign']
        normal = m3 @ local
        normal /= max(1e-9, np.linalg.norm(normal))
        (away if float(normal @ sun) < 0 else facing).append((sheet['object'], float(sub.mean())))
    if not facing or not away:
        return dict(passed=None, note='all wall sheets face the same way relative to the declared sun')
    a, f = np.mean([v for _, v in away]), np.mean([v for _, v in facing])
    return dict(passed=bool(a - f >= 0.2), shaded_fronts_mean=round(float(a), 3), lit_fronts_mean=round(float(f), 3), difference=round(float(a - f), 3), wanted='at least 0.2',
                shaded_sheets=[n for n, _ in away], lit_sheets=[n for n, _ in facing])


def _c(passed, value, wanted, note=''):
    return dict(passed=passed, value=value, wanted=wanted, note=note)


def acceptance(set_id, scene_id):
    """The acceptance checks of the plan's mask table that can be made from the finished pack alone (ground masks; wall-sheet sheltered). Returns {check name: {passed, value, wanted}}.
    Checks that need positions the pack does not keep (door positions, kerb top edges, window reveals) are not here: masks/NOT_DONE.md lists them."""
    import cv2
    sys.path.insert(0, os.path.join(KIT_ROOT, 'harness'))
    from measure_zones import read_gp
    gp, manifest = read_gp(set_id, scene_id)
    settings = settings_module.load_set(set_id)
    out = {}
    has = gp['ground_height'] > -1e9
    crown_mid = gp['crown'] >= 0.9
    exp = settings.get('expect') or {}
    foot = (gp['wall_dist'] < 0.04) & (gp['dampness'] >= 0)
    if foot.any() and 'dampness_feet_min' in exp:
        out['dampness_wall_feet'] = _c(bool(np.median(gp['dampness'][foot]) > exp['dampness_feet_min']), round(float(np.median(gp['dampness'][foot])), 3), 'median above the set\'s expected minimum', f'{int(foot.sum())} dots touching a wall')
    pipes = gp['vertical_foot'] >= 0.9
    if pipes.any() and 'dampness_feet_min' in exp:
        out['dampness_pipe_feet'] = _c(bool(np.median(gp['dampness'][pipes]) > exp['dampness_feet_min']), round(float(np.median(gp['dampness'][pipes])), 3), 'median above the set\'s expected minimum', f'{int(pipes.sum())} dots')
    if crown_mid.any() and 'dampness_road_middle_max' in exp:
        out['dampness_road_middle'] = _c(bool(np.percentile(gp['dampness'][crown_mid], 95) < exp['dampness_road_middle_max']), round(float(np.percentile(gp['dampness'][crown_mid], 95)), 3), '95th percentile below 0.2', f'{int(crown_mid.sum())} dots on the crown')
    if crown_mid.any():
        out['footfall_crown'] = _c(bool(np.percentile(gp['footfall'][crown_mid], 10) >= 0.8), round(float(np.percentile(gp['footfall'][crown_mid], 10)), 3), '10th percentile at least 0.8', 'crown dots')
        out['keepclear_road_middle'] = _c(bool(np.percentile(gp['keepclear'][crown_mid], 10) >= 0.5), round(float(np.percentile(gp['keepclear'][crown_mid], 10)), 3), '10th percentile at least 0.5', 'crown dots')
    # sheltered under the sills and on their tops (first sheet that has ledge sources of the sample object)
    sample = (settings.get('expect') or {}).get('ledges_sample') or {}
    sills = sample.get('sills_m')
    if sills and 'sheltered' in manifest['masks'].get('WF', {}):
        entry = manifest['masks']['WF']['sheltered']
        atlas = manifest['frames']['atlases'][entry['picture']]
        img = pack_module.read_png(os.path.join(manifest['_dir'], atlas['file']))[..., 'RGBA'.index(entry['channel'])]
        sheet = next((sh for sh in manifest['frames']['sheets'] if sample.get('object') in sh.get('objects', [sh['object']]) or sh['object'] == sample.get('object')), manifest['frames']['sheets'][0])
        rect = atlas['rects'][str(sheet['id'])]
        sub = img[rect['y']:rect['y'] + rect['h'], :rect['w']]
        v0, dpm = sheet['v_range'][0], sheet['dots_per_m']
        ledges = [s for s in sheet['sources'] if s['kind'] == 'ledge' and any(abs(s['z'] - z) <= 0.05 for z in sills)]
        under, tops = [], []
        for s in ledges:
            u_mid = 0.5 * (s['u'][0] + s['u'][1])
            col = int(round((u_mid - sheet['u_range'][0]) * dpm))
            rows_under = [int(round((s['z'] - d - v0) * dpm)) for d in (0.03, 0.06, 0.09, 0.12, 0.15)]
            row_top = int(round((s['z'] + 0.03 - v0) * dpm))
            if 0 <= col < sub.shape[1] and all(0 <= r < sub.shape[0] for r in rows_under) and 0 <= row_top < sub.shape[0]:
                under.append(float(np.median([sub[r, col] for r in rows_under])))
                tops.append(float(sub[row_top, col]))
        if under:
            out['sheltered_under_sills'] = _c(bool(min(under) >= 0.8), round(min(under), 3), 'every sill: median of the band 3 to 15 cm below it is 0.8 or more', f'{len(under)} sill sources')
            out['sheltered_on_sill_tops'] = _c(bool(max(tops) <= 0.1), round(max(tops), 3), 'every sill top (3 cm above): 0.1 or less', f'{len(tops)} sill sources; the window above shelters the top within the 1.2 m reach')
    # the doors: a trodden line to the kerb, a keep-clear doorstep strip, one entry number per door
    doors = (manifest.get('stats') or {}).get('entrance_points') or []
    if doors:
        g = manifest['ground']
        h_, w_ = gp['footfall'].shape
        worst_foot, worst_clear, worst_spread = 1.0, 1.0, 0.0
        for x, y in doors:
            ix, iy = int((x - g['x'][0]) / g['dot_m']), int((y - g['y'][0]) / g['dot_m'])
            r = int(1.0 / g['dot_m'])
            win = (slice(max(0, iy - r), min(h_, iy + r + 1)), slice(max(0, ix - r), min(w_, ix + r + 1)))
            worst_foot = min(worst_foot, float(gp['footfall'][win].max()))
            r2 = int(0.6 / g['dot_m'])
            win2 = (slice(max(0, iy - r2), min(h_, iy + r2 + 1)), slice(max(0, ix - r2), min(w_, ix + r2 + 1)))
            worst_clear = min(worst_clear, float(gp['keepclear'][win2].max()))
            near = gp['entry_rand'][win2]
            worst_spread = max(worst_spread, float(near.max() - near.min()))
        out['footfall_every_door'] = _c(bool(worst_foot >= 0.7), round(worst_foot, 3), f'all {len(doors)} doors: footfall 0.7 or more within 1 m')
        out['keepclear_every_doorstep'] = _c(bool(worst_clear >= 0.5), round(worst_clear, 3), f'all {len(doors)} doors: keepclear 0.5 or more within 0.6 m')
        out['entry_rand_one_value_per_door'] = _c(bool(worst_spread <= 0.05), round(worst_spread, 3), 'spread of the entry number within 0.6 m of a door at most 0.05')
    # existing growth patches (settings.existing_growth names objects)
    if settings.get('existing_growth') and gp['existing_growth'].max() > 0.5:
        n, _ = cv2.connectedComponents((gp['existing_growth'] >= 0.5).astype(np.uint8))
        want = exp.get('existing_growth_patches', 1)
        out['existing_growth_patches'] = _c(n - 1 >= want, int(n - 1), f'at least the {want} patches the set names', 'separate patches at 0.5 or more (a patch may split in two, never vanish)')
    # water edge: the ground crosses the water level where water_dist is 0
    water = settings.geometry.get('water')
    if water and float(gp['water_dist'].min()) < 1.0:
        level = water.get('level_z')
        z0, z1 = manifest['ground']['z_range']
        height = gp['ground_height'] * (z1 - z0) + z0 if gp['ground_height'].max() <= 1.0 + 1e-6 else gp['ground_height']
        below = has & (height < level - 0.03)
        above = has & (height > level + 0.05)
        out['water_below_level_zero_distance'] = _c(bool(np.percentile(gp['water_dist'][below], 99) <= 0.02) if below.any() else None, round(float(np.percentile(gp['water_dist'][below], 99)), 3) if below.any() else None, '99 % of dots below the level at distance 0')
        out['water_above_level_positive'] = _c(bool(np.percentile(gp['water_dist'][above], 1) > 0.0) if above.any() else None, round(float(np.percentile(gp['water_dist'][above], 1)), 3) if above.any() else None, 'dots above the level have a positive distance')
    return out


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_path = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
    if out_path in args:
        args.remove(out_path)
    result = dict(shade_side=shade_side(args[0], args[1]), acceptance=acceptance(args[0], args[1]))
    print(json.dumps(result, indent=1))
    if out_path:
        json.dump(result, open(out_path, 'w'), indent=1)
