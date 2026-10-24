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
c.curves[3].points[0].location = (0.0, 0.02)
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
            h2.inputs['Value'].default_value = 1.15
            nt2.links.new(src2, h2.inputs['Color'])
            nt2.links.new(h2.outputs['Color'], bsdf.inputs['Base Color'])
nt = bpy.context.scene.world.node_tree
nt.nodes['Glow boost'].inputs[1].default_value = 2.2

# smoke: noise-varied tone + silhouettes dissolve toward sky colour
for m in bpy.data.materials:
    if m.name.startswith('Chimney smoke grey'):
        tr = m.node_tree
        b = tr.nodes['Principled BSDF']
        base = tuple(b.inputs['Base Color'].default_value)[:3]
        tc = tr.nodes.new('ShaderNodeTexCoord')
        nz = tr.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.55; nz.inputs['Detail'].default_value = 5.0
        tr.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = tr.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.55; mr.inputs['To Max'].default_value = 1.5
        mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 0.65
        tr.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        mul = tr.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        mul.inputs['A'].default_value = (*base, 1.0)
        tr.links.new(mr.outputs['Result'], mul.inputs['B'])
        lw = tr.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
        rim = tr.nodes.new('ShaderNodeMix'); rim.data_type = 'RGBA'; rim.blend_type = 'MIX'
        rim.inputs['B'].default_value = (0.16, 0.25, 0.27, 1.0)
        tr.links.new(lw.outputs['Facing'], rim.inputs['Factor'])
        tr.links.new(mul.outputs['Result'], rim.inputs['A'])
        tr.links.new(rim.outputs['Result'], b.inputs['Base Color'])
# haze: a big scattering box around the whole yard (aerial perspective)
import bmesh
mesh = bpy.data.meshes.new('Critic haze box')
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(mesh); bm.free()
haze = bpy.data.objects.new('Critic haze box', mesh)
bpy.context.scene.collection.objects.link(haze)
haze.scale = (600.0, 600.0, 60.0); haze.location = (0.0, 150.0, 30.0)
hm = bpy.data.materials.new('Critic haze'); hm.use_nodes = True
ht = hm.node_tree
for n in list(ht.nodes): ht.nodes.remove(n)
out = ht.nodes.new('ShaderNodeOutputMaterial')
vsn = ht.nodes.new('ShaderNodeVolumeScatter')
vsn.inputs['Color'].default_value = (0.70, 0.82, 0.88, 1.0)
vsn.inputs['Density'].default_value = 0.0045
vsn.inputs['Anisotropy'].default_value = 0.45
ht.links.new(vsn.outputs['Volume'], out.inputs['Volume'])
mesh.materials.append(hm)
haze.visible_shadow = False
