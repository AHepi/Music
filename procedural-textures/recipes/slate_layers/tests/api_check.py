# What this does: a quick look at which Blender 5.2 node settings exist (so the layout recipe uses names that are really there).
import bpy
t = bpy.data.node_groups.new('x', 'ShaderNodeTree')
m = t.nodes.new('ShaderNodeMath')
print('MATH OPS', [i.identifier for i in m.bl_rna.properties['operation'].enum_items])
w = t.nodes.new('ShaderNodeTexWhiteNoise')
print('WHITE dims', [i.identifier for i in w.bl_rna.properties['noise_dimensions'].enum_items], [(s.name, s.type) for s in w.inputs], [s.name for s in w.outputs])
x = t.nodes.new('ShaderNodeMix')
print('MIX', [(s.name, s.type, s.enabled) for s in x.inputs], [s.name for s in x.outputs])
mr = t.nodes.new('ShaderNodeMapRange')
print('MAPRANGE interp', [i.identifier for i in mr.bl_rna.properties['interpolation_type'].enum_items], [s.name for s in mr.inputs if s.enabled])
print(bpy.app.version_string)
s = t.interface.new_socket('a', in_out='INPUT', socket_type='NodeSocketFloat')
print([p for p in dir(s) if not p.startswith('_')][:60])
