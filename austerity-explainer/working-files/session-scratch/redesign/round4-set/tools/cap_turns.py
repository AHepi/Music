# What this does: renders the jacket-and-cap prop square on, with the cap turned on its nail by several angles, to
# choose the one that reads as a cap from W4 (scratch, round 4).
import bpy, math, sys, os
from mathutils import Matrix, Vector
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/props/jacket-and-cap-on-nail.glb')
cap = bpy.data.objects['cap']; nail = bpy.data.objects['cap-nail']
scene = bpy.context.scene
bpy.context.view_layer.update()
pts = [nail.matrix_world @ Vector(c) for c in nail.bound_box]
pivot = Vector((sum(p.x for p in pts) / 8, sum(p.y for p in pts) / 8, max(p.z for p in pts)))
rest = cap.matrix_world.copy()
wall = bpy.data.objects.new('wall', bpy.data.meshes.new('wall'))
import bmesh
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(wall.data)
wall.scale = (3, 0.02, 3); wall.location = (0, 0.03, 0.5)
scene.collection.objects.link(wall)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam)
cam.location = (0.25, -6.0, 0.5 + 0.7); cam.rotation_euler = (math.radians(90 - math.degrees(math.atan2(0.7, 6.0))), 0, 0)
cam.data.angle_y = math.radians(9); scene.camera = cam
light = bpy.data.objects.new('l', bpy.data.lights.new('l', 'POINT')); light.data.energy = 300; light.location = (1.5, -4, 2.0); scene.collection.objects.link(light)
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.4
scene.render.engine = 'BLENDER_EEVEE'; scene.eevee.taa_render_samples = 16
scene.render.resolution_x = scene.render.resolution_y = 300
for angle in (0, -25, -45, 25, 60):
    cap.matrix_world = (Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(angle), 4, 'Z') @ Matrix.Translation(-pivot)) @ rest
    scene.render.filepath = os.path.join(out, f'cap-{angle}.png')
    bpy.ops.render.render(write_still=True)
print('pivot', pivot)
