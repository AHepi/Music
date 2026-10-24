# What this does: opens the saved courtyard scene and lists material names and the base colours of the plank materials.
import bpy
bpy.ops.wm.open_mainfile(filepath=bpy.path.abspath('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work/out/test9.blend'))
for m in bpy.data.materials:
    b = m.node_tree.nodes.get('Principled BSDF') if m.use_nodes and m.node_tree else None
    print('MAT', m.name, [round(v, 3) for v in b.inputs['Base Color'].default_value[:3]] if b and not b.inputs['Base Color'].is_linked else '(linked)')
