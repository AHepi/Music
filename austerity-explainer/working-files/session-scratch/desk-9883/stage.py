import bpy, math, os
from mathutils import Vector
GLB = open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/desk-9883/glbpath.txt').read().strip()
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 24
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1080, 1920, 40
bpy.ops.import_scene.gltf(filepath=GLB)
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.03, 0.03, 0.035, 1)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera = cam
cam.data.lens = 35
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); s.collection.objects.link(sun)
sun.data.energy = 3.0; sun.data.color = (1.0, 0.86, 0.7); sun.rotation_euler = (math.radians(40), math.radians(-20), math.radians(-30))
area = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'AREA')); s.collection.objects.link(area)
area.data.energy = 200; area.data.size = 3; area.location = (-1.5, -2.5, 3); area.rotation_euler = (Vector((0,0,0)) - area.location).to_track_quat('-Z','Y').to_euler()
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in s.objects:
    if o.type == 'MESH':
        m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
empties = {o.name: [round(c, 4) for c in o.matrix_world.translation] for o in s.objects if o.type == 'EMPTY'}
result = {'tris': tris, 'meshes': len([o for o in s.objects if o.type == 'MESH']), 'empties': empties,
          'materials': sorted(m.name for m in bpy.data.materials), 'images': {i.name: list(i.size) for i in bpy.data.images}}
