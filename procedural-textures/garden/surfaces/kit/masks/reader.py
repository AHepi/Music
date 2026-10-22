# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GEOMETRY READER: run once per scene, it asks the real 3D shapes "where" and writes the where-pictures (the pack, see pack.py) from ANY set's settings file.
#     blender -b --disable-autoexec SCENE.blend --python masks/reader.py -- SET_ID SCENE_ID PACK_DIR [RAW_DIR] [--no-sheets] [--no-shade]
# It never saves the scene and changes nothing in it. Stages (timed): roles -> ground height, slope, lowness, crown -> wall, prop, feet, corner, cover distances, seams, water
# -> fine pictures (steps, sharp edges, stone gaps) -> sky openness and sun shade (16 cm) and the sheltered ground -> footfall, keep-clear, entry numbers, existing growth ->
# ground drip lines -> wall sheets (one per wall mesh) -> raw arrays saved -> pack (pictures, manifest, habitat fields, texture space, checks).
# Nothing here names an object of a set: roles, shapes and numbers come from sets/<set>.json.
import json
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import kit as kit_module  # noqa: E402
from masks import checks as checks_module, footfall, geom, ground_plan, ledges, pack, shade, wall_sheets  # noqa: E402
from masks.geom import Grid  # noqa: E402


def run(set_ref, scene_id, pack_dir, raw_dir=None, sheets=True, with_shade=True, rubbish_heap=None):
    import cv2
    timer = geom.Timer()
    started = time.time()
    k = kit_module.Kit.load(set_ref, scene_id=scene_id, strict=False)   # GARDEN PATCH 5: was strict=True
    settings = k.settings
    print(k.validation, flush=True)
    role_map = k.role_map
    geo = geom.RoleGeometry(role_map)
    timer.mark('scene geometry gathered')
    grid, arrays, stats = ground_plan.make(geo, settings, timer)
    arrays['_role_names'] = stats['role_names']
    entrance_list = ground_plan.entrances(geo, settings)
    fine_grid, fine, fine_stats = ground_plan.fine_pictures(geo, settings, grid, arrays, entrance_list, timer)
    arrays['_step_top_coarse'] = (cv2.resize(fine['step_top'], (grid.width, grid.height), interpolation=cv2.INTER_AREA) > 0.3).astype(np.uint8)
    # ---- shade on the 16 cm ground grid
    grid16 = Grid.from_settings(settings, 'coarse_dot_m')
    h16 = cv2.resize(arrays['ground_height'], (grid16.width, grid16.height), interpolation=cv2.INTER_AREA)
    has16 = cv2.resize(arrays['has_ground'].astype(np.uint8), (grid16.width, grid16.height), interpolation=cv2.INTER_NEAREST) > 0
    shade_stats = {}
    if with_shade:
        shade_arrays, shade_stats = shade.make_ground(geo, settings, grid16, h16, has16, timer)
        arrays.update(shade_arrays)
        arrays['sheltered'] = shade.sheltered_ground(geo, settings, grid16, h16, has16)
        timer.mark('sheltered ground')
    else:
        for key in ('openness', 'sun_shade', 'shade', 'sheltered'):
            arrays[key] = np.full(grid16.shape(), 0.5 if key != 'sheltered' else 0.0, np.float32)
    # ---- who walks where, and the rest
    arrays.update(footfall.make(geo, settings, grid, arrays, entrance_list, timer))
    arrays['drip'], arrays['drip_dist'] = ledges.ground_drip(geo, settings, grid, arrays)
    arrays['drip_kind'] = np.zeros(grid.shape(), np.float32)
    timer.mark('ground drip lines')
    # ---- wall sheets
    sheet_list, frame_of, sheet_errors = [], {}, {}
    if sheets:
        sheet_list, frame_of = wall_sheets.find_frames(geo, settings, role_map)
        done, sheet_errors = [], {}
        for sh in sheet_list:
            try:
                wall_sheets.build_sheet(sh, geo, settings, role_map, arrays, grid, timer)
                done.append(sh)
            except Exception as error:                      # one wall that cannot be read must not stop the rest; it is listed in NOT_DONE
                sheet_errors[sh.name] = repr(error)
                print('[reader] SHEET FAILED', sh.name, repr(error), flush=True)
        sheet_list = done
        frame_of = {k: v for k, v in frame_of.items() if v in {s.id for s in done}}
    meta = dict(stats=dict(ground=stats, fine=fine_stats, shade=shade_stats, entrances=len(entrance_list), entrance_points=[[round(float(e[0]), 3), round(float(e[1]), 3)] for e in entrance_list], role_counts=role_map.counts(),
                           unassigned=len(role_map.unassigned), sheets=len(sheet_list), sheet_errors=sheet_errors),
                seconds=round(time.time() - started, 1))
    raw_dir = raw_dir or os.path.join(pack_dir, '_raw')
    pack.save_raw(raw_dir, grid, fine_grid, arrays, fine, sheet_list, frame_of, meta)
    timer.mark('raw arrays saved')
    # ---- checks against the set's `expect` block (made while the geometry is in memory) and the pack
    checks = checks_module.run_geometry_checks(settings, role_map, geo, grid, arrays, fine, fine_grid, sheet_list, entrance_list)
    timer.mark('checks')
    json.dump(dict(checks=checks, timings=timer.marks), open(os.path.join(raw_dir, 'checks_geometry.json'), 'w'), indent=1, default=str)
    manifest, gp = pack.build(settings, KIT_ROOT, scene_id, raw_dir, pack_dir, rubbish_heap=rubbish_heap, checks=checks, timings=timer.marks)
    manifest['stats'] = meta['stats']
    checks_module.resolve_stone_pieces(manifest)
    json.dump(manifest, open(os.path.join(pack_dir, 'manifest.json'), 'w'), indent=1)
    timer.mark('pack written')
    print('PACK DONE', os.path.abspath(pack_dir), manifest['bytes'], 'bytes in', round(time.time() - started, 1), 's', flush=True)
    return manifest


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    flags = [a for a in args if a.startswith('--')]
    pos = [a for a in args if not a.startswith('--')]
    run(pos[0], pos[1], pos[2], pos[3] if len(pos) > 3 else None, sheets='--no-sheets' not in flags, with_shade='--no-shade' not in flags)
