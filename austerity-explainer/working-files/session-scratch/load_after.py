import bpy, math
from mathutils import Vector
GLB = '/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/props-candidate.glb'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 32
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1080, 1920, 40
bpy.ops.import_scene.gltf(filepath=GLB)
empties = {o.name: [round(c, 4) for c in o.matrix_world.translation] for o in s.objects if o.type == 'EMPTY'}
parents = {o.name: (o.parent.name if o.parent else None) for o in s.objects if o.type == 'EMPTY'}
mats = sorted(m.name for m in bpy.data.materials)
g = bpy.context.evaluated_depsgraph_get()
tris = {}
for o in s.objects:
    if o.type != 'MESH': continue
    top = o
    while top.parent and top.parent.name not in ('barrels', 'crates', 'lamp-post', 'cart'): top = top.parent
    key = top.parent.name if top.parent else o.name
    m = o.evaluated_get(g).to_mesh(); m.calc_loop_triangles()
    tris[key] = tris.get(key, 0) + len(m.loop_triangles); o.evaluated_get(g).to_mesh_clear()
# bounds per group
bounds = {}
for gname in ('barrels', 'crates', 'lamp-post', 'cart'):
    grp = bpy.data.objects.get(gname)
    if not grp: continue
    pts = []
    for o in grp.children_recursive:
        if o.type == 'MESH': pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    bounds[gname] = [[round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]]
# spread groups for viewing
spread = {'barrels': (-0.75, 0.2, 0), 'crates': (-0.15, 0.35, 0), 'cart': (0.55, -0.1, 0), 'lamp-post': (0.0, 0.75, 0)}
for k, v in spread.items():
    o = bpy.data.objects.get(k)
    if o: o.location = Vector(v)
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.03, 0.035, 0.045, 1)
fl = bpy.data.objects.new('floor', bpy.data.meshes.new('floor'))
import bmesh; bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4); bm.to_mesh(fl.data); bm.free()
fm = bpy.data.materials.new('floor-m'); fm.use_nodes = True; fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.085, 0.08, 1)
fl.data.materials.append(fm); s.collection.objects.link(fl)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); s.collection.objects.link(cam); s.camera = cam
cam.data.lens = 50
cam.location = (-0.9, -2.6, 1.2)
cam.rotation_euler = (Vector((0.0, 0.25, 0.4)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); s.collection.objects.link(sun)
sun.data.energy = 3.5; sun.data.color = (1.0, 0.82, 0.62); sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
area = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'AREA')); s.collection.objects.link(area)
area.data.energy = 60; area.data.size = 2; area.location = (1.5, -1.5, 2); area.rotation_euler = (Vector((0,0,0.3)) - area.location).to_track_quat('-Z','Y').to_euler()
result = {'empties': empties, 'parents': parents, 'materials': mats, 'tris': tris, 'total': sum(tris.values()), 'bounds': bounds,
          'objects': len([o for o in s.objects if o.type == 'MESH'])}
