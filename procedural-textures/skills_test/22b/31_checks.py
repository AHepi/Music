# Trial 22b, step 2 (runs on the rented machine): the skill's own checks on the door's worn paint, plus the "render each mask as emission" gate.
#   a. M.audit_material (static), M.value_report (renders albedo / roughness / metallic as pictures and measures them), M.preview (EEVEE and Cycles, studio and roughness rigs, on a sphere and a cube)
#   b. the Wear and Dirt masks of add_wear shown as emission, drawn in EEVEE and in Cycles on the door, with the share of door pixels that are "worn" in each
# Run: blender -b --disable-autoexec street_copy/door_addwear.blend --python 31_checks.py -- OUTDIR
import json
import os
import sys

import bpy
import numpy as np

sys.dont_write_bytecode = True
SK = '/home/user/Music/.claude/skills'
sys.path.append(SK + '/scenario-blender-texturing-shading/scripts')
import bx_materials as M  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
door = bpy.data.objects['right_row_a_cottage_03_door']
mat = bpy.data.materials['door_navy_wear']
rep = {}
rep['audit'] = M.audit_material(mat, door)
try:
    rep['value_report_cycles'] = M.value_report([door], res=256, views=('front',), engine='CYCLES', out_dir=os.path.join(out, 'vr'))
except Exception as exc:
    rep['value_report_cycles'] = 'ERROR ' + repr(exc)
try:
    rep['value_report_eevee'] = M.value_report([door], res=256, views=('front',), engine='BLENDER_EEVEE', out_dir=os.path.join(out, 'vr'))
except Exception as exc:
    rep['value_report_eevee'] = 'ERROR ' + repr(exc)
print('VALUE_REPORT_CYCLES', json.dumps(rep['value_report_cycles'], default=str)[:1200])
print('VALUE_REPORT_EEVEE', json.dumps(rep['value_report_eevee'], default=str)[:1200])
try:
    rep['preview_sheet'] = M.preview(mat, os.path.join(out, 'preview'), engines=('BLENDER_EEVEE', 'CYCLES'), rigs=('studio', 'roughness'), res=256, samples=16, tag='navy_wear')
except Exception as exc:
    rep['preview_sheet'] = 'ERROR ' + repr(exc)
print('PREVIEW', rep['preview_sheet'])

# ---- masks as emission on the real door (the door's own camera and street)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 270, 480
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0
sc.cycles.samples = 16
sc.cycles.use_denoising = False
sc.eevee.taa_render_samples = 16
nt = mat.node_tree
ew = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree.name == 'BX Edge Wear')
outn = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
em = nt.nodes.new('ShaderNodeEmission')
nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
w = bpy.data.worlds.new('mask_world')
sc.world = w
w.color = (0, 0, 0)
for ln in sc.view_layers:
    pass
for o in sc.objects:
    if o.type == 'LIGHT':
        o.hide_render = True
res = {}
for chan in ('Wear', 'Edges', 'Dirt'):
    for l in list(em.inputs['Color'].links):
        nt.links.remove(l)
    nt.links.new(ew.outputs[chan], em.inputs['Color'])
    for eng in ('BLENDER_EEVEE', 'CYCLES'):
        sc.render.engine = eng
        fn = os.path.join(out, f'mask_{chan}_{eng}.png')
        sc.render.filepath = fn
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(fn, check_existing=False)
        a = np.array(img.pixels[:]).reshape(480, 270, 4)[..., 0]
        bpy.data.images.remove(img)
        # the door leaf is the middle of the picture (x 0.28..0.78, y 0.12..0.78 of the frame); the street around it is a different material
        door_px = a[int(480 * 0.20):int(480 * 0.80), int(270 * 0.27):int(270 * 0.73)]
        res[f'{chan}_{eng}'] = {'mean': round(float(door_px.mean()), 4), 'share_above_0.5': round(float((door_px > 0.5).mean()), 4), 'max': round(float(door_px.max()), 3)}
rep['mask_numbers'] = res
print('MASKS', json.dumps(res))
json.dump(rep, open(os.path.join(out, 'checks.json'), 'w'), indent=1, default=str)
print('DONE')
