import bpy, math
from mathutils import Vector
GLB = '/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/town-candidate.glb'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 24
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1080, 1920, 40
bpy.ops.import_scene.gltf(filepath=GLB)
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.25, 0.22, 0.2, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera = cam
cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(44); cam.data.clip_end = 200
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); s.collection.objects.link(sun)
sun.data.energy = 3.0; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = (math.radians(65), 0, math.radians(-40))
tris = 0
g = bpy.context.evaluated_depsgraph_get()
for o in s.objects:
    if o.type == 'MESH':
        m = o.evaluated_get(g).to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); o.evaluated_get(g).to_mesh_clear()
empties = sorted((o.name, tuple(round(c, 4) for c in o.matrix_world.translation)) for o in s.objects if o.type == 'EMPTY')
mats = sorted(m.name for m in bpy.data.materials)
result = {'tris': tris, 'meshes': sum(o.type == 'MESH' for o in s.objects), 'empties': empties, 'materials': mats}
