# Trial 22b: tries different seam settings of the skill on a copy of the door (UV only, no baking, no drawing), to see which gives a layout a bake can use.
# Run: blender -b --disable-autoexec street_copy/door_addwear.blend --python 32_uv_trials.py
import json
import sys
import time

import bpy

sys.dont_write_bytecode = True
SK = '/home/user/Music/.claude/skills'
sys.path.append(SK + '/scenario-blender-uv-baking/scripts')
import bx_uvbake as ub  # noqa: E402

high = bpy.data.objects['right_row_a_cottage_03_door']
rows = []
for label, angle, use_attr, method in (('sharp+30', 30.0, True, 'BEST'), ('angle30', 30.0, False, 'BEST'), ('angle60', 60.0, False, 'BEST'), ('angle80', 80.0, False, 'ANGLE_BASED'), ('angle60_conf', 60.0, False, 'CONFORMAL')):
    low = high.copy()
    low.data = high.data.copy()
    low.name = 'trial'
    bpy.context.scene.collection.objects.link(low)
    for p in low.data.polygons:
        pass
    uvl = low.data.uv_layers.new(name='bake_uv')
    low.data.uv_layers.active = uvl
    t = time.time()
    s = ub.seams_from_sharp(low, angle, use_sharp_attr=use_attr, mark_sharp=False, clear_first=True)
    u = ub.unwrap(low, method=method, uv_map='bake_uv')
    d = ub.normalize_texel_density(low, None, 512, uv_map='bake_uv')
    pk = ub.pack(low, tex_res=512, uv_map='bake_uv')
    q = ub.uv_qa(low, tex_res=512, uv_map='bake_uv')
    rows.append({'label': label, 'seams': s['seams_total'], 'islands': q['islands'], 'coverage': pk['coverage'], 'td_px_per_m': q['td_px_per_m'],
                 'flipped': q['flipped_faces'], 'zero_area': q['zero_area_faces'], 'min_gap_px': q['min_gap_px'], 'td_before': d['before_min_max'], 'target': d['target_px_per_m'],
                 'folding': len(u.get('folding_islands', [])), 'secs': round(time.time() - t, 1)})
    print('ROW', json.dumps(rows[-1]), flush=True)
    bpy.data.objects.remove(low)
# the door's mesh itself: how many faces have zero or near-zero 3D area?
import bmesh
bm = bmesh.new(); bm.from_mesh(high.data)
areas = sorted(f.calc_area() for f in bm.faces)
print('FACE_AREAS_m2 min/median/max', areas[0], areas[len(areas)//2], areas[-1], 'faces below 1e-9:', sum(a < 1e-9 for a in areas), 'total area', round(sum(areas), 2))
json.dump(rows, open('out/uv_trials.json', 'w'), indent=1)
