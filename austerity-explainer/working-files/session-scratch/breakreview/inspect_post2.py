import bpy, os, sys
from mathutils import Vector
P = '/home/user/work/paper-pop-up-film-kit/assets/models/pit-village/props/'
for f in ('gas-lamp-post.glb', 'kitchen-chair.glb', 'wooden-pail.glb', 'notice-on-board.glb', 'hurricane-lantern.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=P + f)
    print('==', f)
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        for index, material in enumerate(o.data.materials):
            pts = [o.matrix_world @ o.data.vertices[v].co for p in o.data.polygons if p.material_index == index for v in p.vertices]
            if pts:
                print('  ', o.name, material.name if material else None, 'x', round(min(p.x for p in pts), 3), round(max(p.x for p in pts), 3), 'y', round(min(p.y for p in pts), 3), round(max(p.y for p in pts), 3), 'z', round(min(p.z for p in pts), 3), round(max(p.z for p in pts), 3))
                m = material
                if m and m.use_nodes:
                    b = m.node_tree.nodes.get('Principled BSDF')
                    if b:
                        c = b.inputs['Base Color']
                        tex = [l.from_node.type for l in c.links]
                        print('      base', [round(v, 2) for v in c.default_value[:3]], 'linked', tex)
