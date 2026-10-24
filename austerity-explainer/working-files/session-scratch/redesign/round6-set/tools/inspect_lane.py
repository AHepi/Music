# What this does: prints the Works lane's gutter (street_channels) material nodes and a few lights' settings (scratch, round 6)
import bpy
o = bpy.data.objects['street_channels']
print('channel verts', len(o.data.vertices), 'materials', [m.name for m in o.data.materials])
for m in o.data.materials:
    print('material', m.name, getattr(m, 'displacement_method', None))
    for n in m.node_tree.nodes:
        extra = ''
        if n.type == 'NORMAL_MAP':
            extra = f"strength={n.inputs['Strength'].default_value}"
        if n.type == 'BUMP':
            extra = f"strength={n.inputs['Strength'].default_value} dist={n.inputs['Distance'].default_value}"
        if n.type == 'DISPLACEMENT':
            extra = f"scale={n.inputs['Scale'].default_value}"
        print('  node', n.type, n.name, extra)
    out = [n for n in m.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    print('  displacement linked', out.inputs['Displacement'].is_linked)
L = bpy.data.lights.new('t', 'SPOT')
print('light props', [p for p in ('use_custom_distance', 'cutoff_distance') if hasattr(L, p)])
