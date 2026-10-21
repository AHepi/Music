# What this does (plain words): prints how the road material (street_setts) is built in the street copy (before the wetness layer is put on),
# the road mesh, its texture coordinates, and the same for pavement_flags / channel_stones / kerb_stone. It changes and saves nothing.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python a01_dump_setts_material.py
import bpy
for name in ('street_setts', 'pavement_flags', 'channel_stones', 'kerb_stone', 'colliery_yard'):
    m = bpy.data.materials[name]
    print('MATERIAL', name, 'users', m.users)
    for n in m.node_tree.nodes:
        extra = ''
        if n.type == 'TEX_IMAGE':
            extra = f' image={n.image.name if n.image else None} {tuple(n.image.size) if n.image else None} cs={n.image.colorspace_settings.name if n.image else None} interp={n.interpolation}'
        elif n.type == 'NORMAL_MAP':
            extra = f' strength={n.inputs["Strength"].default_value} uv={n.uv_map!r} space={n.space}'
        elif n.type == 'MAPPING':
            extra = f' scale={tuple(n.inputs["Scale"].default_value)} loc={tuple(n.inputs["Location"].default_value)} rot={tuple(n.inputs["Rotation"].default_value)}'
        elif n.type == 'BSDF_PRINCIPLED':
            extra = ' ' + ', '.join(f'{i.name}={getattr(i, "default_value", None) if not hasattr(getattr(i,"default_value",None), "__len__") else tuple(round(v,3) for v in i.default_value)}' for i in n.inputs if i.name in ('Base Color','Roughness','Metallic','Specular IOR Level','Coat Weight','Normal','IOR') )
        elif n.type == 'BUMP':
            extra = f' strength={n.inputs["Strength"].default_value} dist={n.inputs["Distance"].default_value}'
        print('  NODE', n.name, n.type, extra)
    for l in m.node_tree.links:
        print('  LINK', l.from_node.name, l.from_socket.name, '->', l.to_node.name, l.to_socket.name)
for obj in bpy.data.objects:
    if obj.name in ('street_setts', 'street_pavements', 'street_channels', 'street_kerbs', 'ground'):
        me = obj.data
        print('OBJ', obj.name, 'verts', len(me.vertices), 'faces', len(me.polygons), 'uv', [u.name for u in me.uv_layers], 'dims', tuple(round(v, 2) for v in obj.dimensions), 'loc', tuple(round(v, 2) for v in obj.location), 'mods', [m.type for m in obj.modifiers])
        xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
        print('   bbox x', min(xs), max(xs), 'y', min(ys), max(ys), 'z', min(zs), max(zs))
        for uv in me.uv_layers:
            us = [d.uv[0] for d in uv.data]; vs = [d.uv[1] for d in uv.data]
            print('   UV', uv.name, 'u', min(us), max(us), 'v', min(vs), max(vs))
scene = bpy.context.scene
print('RENDER', scene.render.engine, scene.eevee.taa_render_samples, 'rt', scene.eevee.use_raytracing, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure)
print('LIGHTS')
for o in scene.objects:
    if o.type == 'LIGHT':
        print('  ', o.name, o.data.type, round(o.data.energy, 1), tuple(round(v, 2) for v in o.location), 'color', tuple(round(c, 2) for c in o.data.color), 'size', getattr(o.data, 'shadow_soft_size', None))
w = scene.world
print('WORLD', w.name, [(n.type, n.name) for n in w.node_tree.nodes])
