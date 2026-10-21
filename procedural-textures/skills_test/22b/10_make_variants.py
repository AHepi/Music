# Trial 22b, step 1 (runs on this computer, draws nothing): makes the BEFORE and AFTER files of the door test.
# Run: PYTHONDONTWRITEBYTECODE=1 blender -b --disable-autoexec street_copy/street.blend --python 10_make_variants.py -- VARIANT
#   VARIANT before    : the street exactly as it is, plus a close camera on one door  -> street_copy/door_before.blend
#   VARIANT addwear   : the door's paint material copied, then M.add_wear() put on it -> street_copy/door_addwear.blend
# The door chosen: right_row_a_cottage_03_door (navy paint, next to the first gas lamp). Only this door gets the new material;
# the other 10 navy doors keep the original material, because the new one is a COPY (paint_navy.copy()).
import json
import os
import sys

import bpy

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = '/home/user/Music/.claude/skills'
sys.path.append(os.path.join(SKILLS, 'scenario-blender-texturing-shading', 'scripts'))
sys.path.insert(0, 'proc-work/street_wet/tools')
import bx_materials as M  # noqa: E402
import apply_wetness_to_set as aw  # noqa: E402

variant = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
door = bpy.data.objects['right_row_a_cottage_03_door']

# a close camera, standing in the road, looking at the whole door (door face at x 4.22, y 9.15..10.05, z 1.19..3.77)
cam = aw.make_camera('door_close', (1.0, 9.6, 2.35), look_at=(4.22, 9.6, 2.45), fov_vertical=46.0)
scene.camera = cam
# round 2: the street at dusk is too dark to judge paint wear on a navy door, so ONE extra soft light (100 W; 60, 150 and 300 W were tried, 700 W washed the door out; same in every variant) is added in front of the door,
# a little to the side so that it rakes across the door (the skill's advice: grazing light shows relief)
ld = bpy.data.lights.new('lookdev_key', 'AREA')
ld.energy, ld.size = 100.0, 1.0
lo = bpy.data.objects.new('lookdev_key', ld)
lo.location = (2.2, 8.0, 3.2)
lo.rotation_euler = (__import__('mathutils').Vector((4.22, 9.6, 2.5)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(lo)

report = {'variant': variant}
if variant == 'addwear':
    base = bpy.data.materials['paint_navy']
    mat = base.copy()
    mat.name = 'door_navy_wear'
    report['audit_before'] = M.audit_material(base, door)
    # the call the skill's step 4 gives: wear that follows form (edges), dirt in cavities, grunge spots, small colour variation
    # round 1 used the skill's example values (wear_amount 0.5, radius 0.02): every panel edge came out as a brown outline, so round 2 uses a fifth of the amount
    groups = M.add_wear(mat, edge_color=(0.35, 0.26, 0.17), edge_roughness=0.75, edge_metallic=None,
                        dirt_color=(0.010, 0.012, 0.020), dirt_roughness=0.9, dirt_amount=0.55, grunge_amount=0.3,
                        variation=0.08, coords='OBJECT', radius=0.012, wear_amount=0.22, cavity_dirt=0.35, noise_scale=14.0, grunge_scale=4.0)
    door.material_slots[0].material = mat
    # the black trim of the same door gets the same treatment (its own copy)
    base2 = bpy.data.materials['paint_black']
    mat2 = base2.copy()
    mat2.name = 'door_black_wear'
    M.add_wear(mat2, edge_color=(0.35, 0.26, 0.17), edge_roughness=0.75, dirt_color=(0.01, 0.01, 0.01), dirt_roughness=0.9,
               dirt_amount=0.5, grunge_amount=0.3, variation=0.05, coords='OBJECT', radius=0.012, wear_amount=0.22, cavity_dirt=0.35)
    door.material_slots[2].material = mat2
    report['audit_after'] = M.audit_material(mat, door)
    report['nodes_added'] = sorted({n.bl_idname + ('/' + n.node_tree.name if n.bl_idname == 'ShaderNodeGroup' else '') for n in mat.node_tree.nodes})
    report['node_count_before'] = len(base.node_tree.nodes)
    report['node_count_after'] = len(mat.node_tree.nodes)
if variant.startswith('curv'):
    # the skill's EEVEE-friendly route: a curvature number stored on every vertex (no Bevel node), read back with an Attribute node
    import bpy as _b
    door.data = door.data.copy()
    cur = M.curvature_attribute(door, 'col_curvature', smooth=2, contrast=4.0)
    report['curvature_vertex_stats'] = {'min': float(cur.min()), 'max': float(cur.max()), 'share_above_0.6': float((cur > 0.6).mean()), 'share_above_0.75': float((cur > 0.75).mean()), 'vertices': len(cur)}
    base = bpy.data.materials['paint_navy']
    mat = base.copy()
    mat.name = 'door_navy_' + variant
    lo_t, hi_t = (0.58, 0.8) if variant == 'curv' else (0.80, 0.92)   # curv2: a second try with a much higher threshold
    nt = mat.node_tree
    p = M.principled(mat)
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'col_curvature'
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 40.0
    nz.inputs['Detail'].default_value = 4.0
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    _, convex = M._maprange(nt, at.outputs['Fac'], lo_t, hi_t)
    _, nbr = M._maprange(nt, nz.outputs['Fac'], 0.35, 0.6)
    _, wear = M._math(nt, 'MULTIPLY', convex, nbr)
    bc = M._source(nt, p.inputs['Base Color'], (-300, 300))
    _, col = M._mix(nt, 'RGBA', 'MIX', wear, bc, (0.35, 0.26, 0.17))
    _, rough = M._mix(nt, 'FLOAT', fac=wear, a=0.45, b=0.75)
    nt.links.new(col, p.inputs['Base Color'])
    nt.links.new(rough, p.inputs['Roughness'])
    door.material_slots[0].material = mat
out = os.path.join(HERE, 'street_copy', f'door_{variant}.blend')
bpy.ops.wm.save_as_mainfile(filepath=out, copy=True)
print('SAVED', out)
print('REPORT', json.dumps(report, default=str))
json.dump(report, open(os.path.join(HERE, 'out', f'variants_{variant}.json'), 'w'), indent=1, default=str)
