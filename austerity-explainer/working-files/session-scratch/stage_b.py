import bpy, math
from mathutils import Vector
GLB = '/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/factory-b.glb'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 24
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1080, 1920, 40
bpy.ops.import_scene.gltf(filepath=GLB)
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.12, 0.1, 0.09, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera = cam
cam.data.lens = 40
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); s.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = (math.radians(60), 0, math.radians(-50))
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in s.objects:
    if o.type == 'MESH':
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
result = {'objects': len(s.objects), 'meshes': sum(o.type=='MESH' for o in s.objects), 'tris': tris,
          'empties': {o.name: [round(c, 4) for c in o.matrix_world.translation] for o in s.objects if o.type == 'EMPTY'},
          'materials': sorted(m.name for m in bpy.data.materials)}
