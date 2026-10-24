# What this does: prints the scene settings a .blend keeps (colour, render engine, samples, size,
# world light), to compare two builds. Run: blender -b FILE.blend --python print_scene_settings.py
import bpy
scene = bpy.context.scene
view = scene.view_settings
print('SETTINGS', {'engine': scene.render.engine, 'samples': scene.eevee.taa_render_samples,
                   'size': (scene.render.resolution_x, scene.render.resolution_y),
                   'view_transform': view.view_transform, 'look': view.look, 'exposure': view.exposure, 'gamma': view.gamma,
                   'camera': scene.camera.name if scene.camera else None,
                   'world_strength': scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value if scene.world else None,
                   'objects': len(scene.objects), 'images': sorted(i.filepath for i in bpy.data.images)[:3]})
