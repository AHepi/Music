# What this does: lists what is in a .blend (lights, world, render settings, how the road and wall materials are wired) so the study can say how the street is lit.
# Changes nothing, saves nothing. Run: blender -b --disable-autoexec -t 2 FILE.blend --python 02_inspect_street_blend.py
import bpy
scene = bpy.context.scene
print('ENGINE', scene.render.engine, 'view', scene.view_settings.view_transform, scene.view_settings.look, 'exposure', scene.view_settings.exposure)
try:
    print('EEVEE samples', scene.eevee.taa_render_samples, 'raytracing', scene.eevee.use_raytracing, 'shadows', scene.eevee.use_shadows)
except Exception as e:
    print('eevee attrs', e)
print('WORLD', scene.world.name if scene.world else None)
if scene.world and scene.world.node_tree:
    for n in scene.world.node_tree.nodes:
        if n.type == 'BACKGROUND':
            print('  background', tuple(n.inputs['Color'].default_value), n.inputs['Strength'].default_value)
lights = [o for o in bpy.data.objects if o.type == 'LIGHT']
print('LIGHTS', len(lights))
for o in lights:
    d = o.data
    print('  ', o.name, d.type, 'energy', round(d.energy, 2), 'colour', tuple(round(c, 2) for c in d.color), 'loc', tuple(round(v, 1) for v in o.location))
print('OBJECTS', len(bpy.data.objects), 'MATERIALS', len(bpy.data.materials))
for name in ('street_setts', 'pavement_flags', 'cottage_brick', 'roof_slate', 'channel_stones'):
    m = bpy.data.materials[name]
    print('MATERIAL', name)
    for n in m.node_tree.nodes:
        extra = ''
        if n.type == 'TEX_IMAGE':
            extra = f' image={n.image.name} {tuple(n.image.size)} {n.image.colorspace_settings.name} interp={n.interpolation}'
        if n.type == 'BSDF_PRINCIPLED':
            extra = f' roughness={n.inputs["Roughness"].default_value} spec={n.inputs["Specular IOR Level"].default_value} coat={n.inputs["Coat Weight"].default_value}'
        print('   ', n.type, n.name, extra)
    for l in m.node_tree.links:
        print('      link', l.from_node.name, '.', l.from_socket.name, '->', l.to_node.name, '.', l.to_socket.name)
road = bpy.data.objects.get('street_setts')
if road:
    me = road.data
    print('ROAD verts', len(me.vertices), 'faces', len(me.polygons), 'uv layers', [u.name for u in me.uv_layers])
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    print('  x', min(xs), max(xs), 'y', min(ys), max(ys), 'z', min(zs), max(zs))
    uv = me.uv_layers[0].data
    us = [d.uv[0] for d in uv]; vs = [d.uv[1] for d in uv]
    print('  uv u', min(us), max(us), 'v', min(vs), max(vs))
