# Trial 22b, step 3 (runs on the rented machine, Cycles needed for baking): a small TEST BAKE of the door's worn paint with the skill scenario-blender-uv-baking.
# What it does, in order (every step prints what it measured):
#   1. opens street_copy/door_addwear.blend (the door with M.add_wear on its paint), makes a COPY of the door called door_low (own mesh, own plain material);
#      the real door stays as the "high" (it carries the worn material, which is what we want baked)
#   2. gives the copy a NEW UV map "bake_uv" (the door's own UV map is a tiling one, 0 to 3, so it cannot hold a bake): seams from the sharp edges, unwrap,
#      equal texel density, pack, then the skill's UV checks
#   3. bakes DIFFUSE (colour), ROUGHNESS and NORMAL at RES x RES with bx_uvbake.bake_high_to_low
#   4. builds a plain material from the three baked pictures (no Bevel, no AO, no noise: EEVEE can read it), copies the new UV map onto the real door,
#      puts the baked material on the door's paint and trim slots, saves street_copy/door_baked_RES.blend
# Run: blender -b --disable-autoexec street_copy/door_addwear.blend --python 30_bake_door.py -- RES OUTDIR
import json
import os
import sys
import time

import bpy
import numpy as np

sys.dont_write_bytecode = True
SK = '/home/user/Music/.claude/skills'
sys.path.append(SK + '/scenario-blender-uv-baking/scripts')
sys.path.append(SK + '/scenario-blender-texturing-shading/scripts')
import bx_uvbake as ub  # noqa: E402

_a = sys.argv[sys.argv.index('--') + 1:]
res = int(_a[0])
outdir = _a[1]
seam_angle = float(_a[2]) if len(_a) > 2 else 30.0
use_sharp_attr = (_a[3] == '1') if len(_a) > 3 else True
os.makedirs(outdir, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
report = {'res': res, 'seam_angle': seam_angle, 'use_sharp_attr': use_sharp_attr}
t0 = time.time()


def lap(name):
    report.setdefault('seconds', {})[name] = round(time.time() - t0, 1)
    print('LAP', name, report['seconds'][name], flush=True)


high = bpy.data.objects['right_row_a_cottage_03_door']
low = high.copy()
low.data = high.data.copy()
low.name = 'door_low'
low.data.name = 'door_low_mesh'
for c in high.users_collection:
    c.objects.link(low)
# the copy gets ONE plain material (the bake adds its image node to every material of the low, and the real materials must not be touched)
plain = bpy.data.materials.new('door_low_plain')
low.data.materials.clear()
low.data.materials.append(plain)
for p in low.data.polygons:
    p.material_index = 0

# ---- 2. UVs
uvl = low.data.uv_layers.new(name='bake_uv')
low.data.uv_layers.active = uvl
report['seams'] = ub.seams_from_sharp(low, seam_angle, use_sharp_attr=use_sharp_attr, mark_sharp=False, clear_first=True)
lap('seams')
try:
    u = ub.unwrap(low, method='BEST', uv_map='bake_uv')
    report['unwrap'] = {k: u[k] for k in u if k in ('unsolved_faces', 'folding_islands', 'method', 'chosen', 'islands')}
    print('UNWRAP', json.dumps({k: (v if not hasattr(v, 'tolist') else v.tolist()) for k, v in u.items()}, default=str)[:900])
except Exception as exc:
    report['unwrap_error'] = repr(exc)
    raise
lap('unwrap')
report['density'] = ub.normalize_texel_density(low, None, res, uv_map='bake_uv')
report['pack'] = ub.pack(low, tex_res=res, uv_map='bake_uv')
lap('pack')
qa = ub.uv_qa(low, tex_res=res, uv_map='bake_uv')
report['uv_qa'] = {k: v for k, v in qa.items() if not isinstance(v, (list, dict)) or len(str(v)) < 300}
try:
    report['uv_verdict'] = ub.uv_verdict(qa, 'game')
except Exception as exc:
    report['uv_verdict'] = repr(exc)
print('UV_QA', json.dumps(report['uv_qa'], default=str))
print('UV_VERDICT', json.dumps(report['uv_verdict'], default=str)[:600])
ub.uv_layout_image(low, os.path.join(outdir, f'door_uv_layout_{res}.png'), res=512, uv_map='bake_uv')
report['prepare'] = ub.prepare_low(low)
lap('uv_done')

# ---- 3. bake
bk = ub.bake_high_to_low(low, [high], outdir, res=res, maps=('DIFFUSE', 'ROUGHNESS', 'NORMAL'), uv_map='bake_uv', prefix='door', adaptive=False)
report['bake_paths'] = bk['paths']
report['bake_sanity'] = bk['sanity']
report['bake_settings'] = bk['settings']
report['bake_projection'] = bk.get('projection')
report['bake_warnings'] = bk['warnings']
print('BAKE', json.dumps({k: bk[k] for k in ('paths', 'settings', 'warnings')}, default=str)[:1500])
print('SANITY', json.dumps(bk['sanity'], default=str)[:1500])
lap('bake')

# ---- 4. rebuild from the maps
mat = bpy.data.materials.new('door_baked_paint')
nt = mat.node_tree
p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
uvn = nt.nodes.new('ShaderNodeUVMap')
uvn.uv_map = 'bake_uv'
for key, ch, cs in (('DIFFUSE', 'Base Color', 'sRGB'), ('ROUGHNESS', 'Roughness', 'Non-Color')):
    img = bpy.data.images.load(bk['paths'][key], check_existing=False)
    img.colorspace_settings.name = cs
    tn = nt.nodes.new('ShaderNodeTexImage')
    tn.image = img
    nt.links.new(uvn.outputs['UV'], tn.inputs['Vector'])
    nt.links.new(tn.outputs['Color'], p.inputs[ch])
# the other pieces of the real door: same UV copy, baked material on the paint slot and the trim slot, brass stays live
src = low.data.uv_layers['bake_uv']
buf = np.zeros(len(src.data) * 2, dtype=np.float64)
src.data.foreach_get('uv', buf)
dst = high.data.uv_layers.new(name='bake_uv')
dst.data.foreach_set('uv', buf)
# hook the baked normal map into the baked material with the skill's own function: give the (now unused) low only this material
low.data.materials.clear()
low.data.materials.append(mat)
normal_ok = not bk['sanity']['NORMAL']['problems']
report['normal_used'] = normal_ok
report['hookup'] = ub.hookup_maps(low, normal=bk['paths']['NORMAL'] if normal_ok else None, uv_map='bake_uv')
high.material_slots[0].material = mat
high.material_slots[2].material = mat
bpy.data.objects.remove(low)
# keep the worn (live) door for the side-by-side: this file is the BAKED variant only
out_blend = os.path.join(HERE, 'street_copy', f'door_baked_{res}{os.environ.get("BAKE_TAG", "")}.blend')
bpy.ops.wm.save_as_mainfile(filepath=out_blend, copy=True, relative_remap=True)
report['saved'] = out_blend
lap('rebuilt')
json.dump(report, open(os.path.join(outdir, f'bake_report_{res}.json'), 'w'), indent=1, default=str)
print('DONE', out_blend)
