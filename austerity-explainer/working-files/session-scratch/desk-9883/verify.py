import bpy
from mathutils import Vector
out = {}
for label, path in (('old', '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/desk.orig.glb'),
                    ('new', '/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/desk-candidate.glb')):
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=path)
    s = bpy.context.scene
    lo, hi = Vector((1e9,)*3), Vector((-1e9,)*3)
    intrude = []
    for o in s.objects:
        if o.type != 'MESH': continue
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
            if abs(w.x) < 0.75 and abs(w.y) < 0.95 and w.z > 0.0005: intrude.append(o.name)
    out[label] = {
        'empties': {o.name: [round(c, 4) for c in o.matrix_world.translation] for o in s.objects if o.type == 'EMPTY'},
        'glow': sorted({o.name for o in s.objects if o.type == 'MESH' for m in o.data.materials if m and m.name.endswith('-glow')}),
        'glow_strength': [round(m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value, 2) for m in bpy.data.materials if m.name.endswith('-glow')],
        'materials': sorted(m.name for m in bpy.data.materials),
        'bounds': [[round(c, 3) for c in lo], [round(c, 3) for c in hi]],
        'clear_zone_intruders': sorted(set(intrude)),
        'meshes': len([o for o in s.objects if o.type == 'MESH']),
    }
old, new = out['old'], out['new']
out['missing_materials'] = sorted(set(old['materials']) - set(new['materials']))
out['added_materials'] = sorted(set(new['materials']) - set(old['materials']))
result = out
