import bpy
# puddles: bright mirror
for m in bpy.data.materials:
    if m.name.startswith('Puddle water'):
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (0.80, 0.88, 0.92, 1.0)
        b.inputs['Metallic'].default_value = 1.0
        b.inputs['Roughness'].default_value = 0.05
        b.inputs['Alpha'].default_value = 1.0
# sky: slightly greener and less saturated, keep punch
nt = bpy.context.scene.world.node_tree
bg = nt.nodes['Sky strength']
link = [l for l in nt.links if l.to_socket == bg.inputs['Color']][0]
src = link.from_socket
nt.links.remove(link)
hs = nt.nodes.new('ShaderNodeHueSaturation')
hs.inputs['Hue'].default_value = 0.47
hs.inputs['Saturation'].default_value = 0.80
hs.inputs['Value'].default_value = 1.05
nt.links.new(src, hs.inputs['Color'])
nt.links.new(hs.outputs['Color'], bg.inputs['Color'])
# lifted blacks (painted look): raise the black point of the display curve
vs = bpy.context.scene.view_settings
vs.use_curve_mapping = True
c = vs.curve_mapping
c.curves[3].points[0].location = (0.0, 0.07)
c.update()
# lit windows much brighter and yellower
for m in bpy.data.materials:
    if m.name.startswith(('Window glow', 'Warm window glow')):
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Emission Strength'].default_value *= 5.0
        b.inputs['Emission Color'].default_value = (1.0, 0.55, 0.16, 1.0)
# coal: less mirror-like (white facets)
for m in bpy.data.materials:
    if m.name.startswith('Coal'):
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Roughness'].default_value = max(b.inputs['Roughness'].default_value, 0.6)
