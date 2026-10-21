# What this does (plain words): lists the lights, cameras, props and render settings of the film's lockout shot file (opened read-only, nothing is saved),
# so the lighting test set can be written against what is really in the shot.
# Run: blender -b --disable-autoexec -t 2 .../lockout.blend --python a02_dump_lockout_file.py
import bpy
scene = bpy.context.scene
print('FILE', bpy.data.filepath)
print('RENDER', scene.render.engine, scene.render.resolution_x, scene.render.resolution_y, scene.eevee.taa_render_samples, 'rt', scene.eevee.use_raytracing, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure)
print('CAMERA', scene.camera.name, tuple(round(v, 3) for v in scene.camera.location), scene.camera.data.angle_y)
lights = [o for o in scene.objects if o.type == 'LIGHT']
print('LIGHT COUNT', len(lights))
for o in lights:
    if o.data.energy > 100 or o.data.type != 'POINT' or 'brazier' in o.name.lower() or 'fire' in o.name.lower():
        print('  LIGHT', o.name, o.data.type, round(o.data.energy, 1), tuple(round(v, 2) for v in o.location), tuple(round(c, 2) for c in o.data.color), getattr(o.data, 'shadow_soft_size', None))
print('MESH OBJECTS (non-street):')
for o in scene.objects:
    if o.type == 'MESH' and not (o.name.startswith('right_row') or o.name.startswith('left_row') or o.name.startswith('gas_lamp')):
        mats = [s.material.name for s in o.material_slots if s.material]
        print('  ', o.name, tuple(round(v, 2) for v in o.location), mats[:3])
w = scene.world
bg = w.node_tree.nodes.get('Background')
print('WORLD', tuple(bg.inputs['Color'].default_value), bg.inputs['Strength'].default_value, [n.type for n in w.node_tree.nodes])
print('EEVEE', {k: getattr(scene.eevee, k) for k in ('shadow_ray_count', 'shadow_step_count', 'shadow_pool_size', 'shadow_resolution_scale', 'use_shadows', 'use_volumetric_shadows', 'fast_gi_method') if hasattr(scene.eevee, k)})
road = bpy.data.objects.get('street_setts')
print('ROAD OBJ', road, road.pass_index if road else None)
print('MATS setts', bpy.data.materials['street_setts'].node_tree.nodes.keys())
