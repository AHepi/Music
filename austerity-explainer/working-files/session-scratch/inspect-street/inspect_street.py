# Prints the dusk sky's strength, the gutter and kerb objects with their materials, and whether imported glass
# takes its see-through value from a picture.
import bpy, sys, os
w = bpy.context.scene.world
print('WORLD', w.name if w else None)
if w and w.node_tree:
    for n in w.node_tree.nodes:
        if n.type == 'BACKGROUND':
            print('WORLD BG', n.name, round(n.inputs['Strength'].default_value, 3), 'colour', [round(c, 3) for c in n.inputs['Color'].default_value][:3], 'linked', n.inputs['Color'].is_linked)
for o in bpy.data.objects:
    if any(k in o.name for k in ('channel', 'kerb', 'gutter')):
        print('OBJ', o.name, [s.material.name for s in o.material_slots if s.material][:4])
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/blender/pit-village')
from set_dressing import PROPS_FOLDER
for f in ('gas-lamp-post.glb', 'hurricane-lantern.glb'):
    before = set(bpy.data.materials)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PROPS_FOLDER, f))
    for m in set(bpy.data.materials) - before:
        if 'glass' in m.name and m.use_nodes:
            a = m.node_tree.nodes['Principled BSDF'].inputs['Alpha']
            print('GLASS', f, m.name, 'alpha linked', a.is_linked, 'method', getattr(m, 'surface_render_method', None))
