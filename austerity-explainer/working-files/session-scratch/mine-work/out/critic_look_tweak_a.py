import math
# --- 1. puddles: painter's mirror puddles (bright sky-coloured)
for m in bpy.data.materials:
    if m.name.startswith('Puddle water'):
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.80, 0.88, 0.92, 1.0)
        b.inputs['Metallic'].default_value = 1.0
        b.inputs['Roughness'].default_value = 0.05
        b.inputs['Alpha'].default_value = 1.0
# --- 2. sky: slightly desaturated, lighter, warmer glow
w = bpy.context.scene.world
nt = w.node_tree
bg = nt.nodes['Sky strength']
link = [l for l in nt.links if l.to_socket == bg.inputs['Color']][0]
src = link.from_socket
nt.links.remove(link)
hs = nt.nodes.new('ShaderNodeHueSaturation')
hs.inputs['Saturation'].default_value = 0.72
hs.inputs['Value'].default_value = 1.15
nt.links.new(src, hs.inputs['Color'])
nt.links.new(hs.outputs['Color'], bg.inputs['Color'])
nt.nodes['Glow boost'].inputs[1].default_value = 3.0
# --- 3. colour management
vs = bpy.context.scene.view_settings
try:
    vs.look = 'AgX - Base Contrast'
except Exception as e:
    print('look fail', e)
vs.exposure = 0.6
# --- 4. lights
bpy.data.lights['Village low sun'].energy = 12.0
