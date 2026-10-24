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
c.curves[3].points[0].location = (0.0, 0.035)
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

bpy.data.lights['Village low sun'].energy = 24.0
# ground: less terracotta, a touch lighter
for m in bpy.data.materials:
    if m.name.startswith('mud'):
        nt2 = m.node_tree
        bsdf = nt2.nodes.get('Principled BSDF')
        ln = [l for l in nt2.links if l.to_socket == bsdf.inputs['Base Color']]
        if ln:
            src2 = ln[0].from_socket
            nt2.links.remove(ln[0])
            h2 = nt2.nodes.new('ShaderNodeHueSaturation')
            h2.inputs['Saturation'].default_value = 0.65
            h2.inputs['Value'].default_value = 1.25
            nt2.links.new(src2, h2.inputs['Color'])
            nt2.links.new(h2.outputs['Color'], bsdf.inputs['Base Color'])
nt = bpy.context.scene.world.node_tree
nt.nodes['Glow boost'].inputs[1].default_value = 2.2
# soft smoke: edges dissolve (alpha from facing ratio)
for m in bpy.data.materials:
    if m.name.startswith('Chimney smoke grey'):
        t = m.node_tree
        b = t.nodes['Principled BSDF']
        lw = t.nodes.new('ShaderNodeLayerWeight')
        lw.inputs['Blend'].default_value = 0.5
        mr = t.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.55
        mr.inputs['From Max'].default_value = 0.98
        mr.inputs['To Min'].default_value = 0.95
        mr.inputs['To Max'].default_value = 0.0
        t.links.new(lw.outputs['Facing'], mr.inputs['Value'])
        t.links.new(mr.outputs['Result'], b.inputs['Alpha'])
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
