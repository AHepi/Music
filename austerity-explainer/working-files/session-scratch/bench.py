import bpy, time, sys, os
out = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def box(name, loc, size, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    m = o.modifiers.new("bev", "BEVEL"); m.width = bevel; m.segments = 3; m.limit_method = 'ANGLE'
    return o

mat = bpy.data.materials.new("brick"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.22, 0.15, 1)
# factory body + windows array + chimney
body = box("body", (0, 0, 1), (2, 1.2, 1)); body.data.materials.append(mat)
win = box("win", (-1.6, -1.22, 1.2), (0.25, 0.03, 0.35), 0.01)
a = win.modifiers.new("arr", "ARRAY"); a.count = 7; a.relative_offset_displace = (1.8, 0, 0)
roof = box("roof", (0, 0, 2.15), (2.1, 1.3, 0.12))
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.18, depth=2.5, location=(-1.2 + i * 1.2, 0.4, 3.3))
ground = box("ground", (0, 0, -0.05), (20, 20, 0.05))
bpy.ops.object.light_add(type='AREA', location=(3, -4, 6)); bpy.context.object.data.energy = 2000; bpy.context.object.data.size = 3
bpy.ops.object.light_add(type='POINT', location=(-3, -2, 2)); bpy.context.object.data.energy = 300
bpy.ops.object.camera_add(location=(0, -9, 2.5), rotation=(1.45, 0, 0)); sc.camera = bpy.context.object
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.05, 0.04, 0.03)

dg = bpy.context.evaluated_depsgraph_get()
tris = sum(len(o.evaluated_get(dg).to_mesh().loop_triangles) if (o.evaluated_get(dg).to_mesh().calc_loop_triangles() or True) else 0 for o in sc.objects if o.type == 'MESH')
print("TRIS", tris)

sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
for spp in (int(a) for a in sys.argv[sys.argv.index('--') + 1:] if a.isdigit()):
    sc.cycles.samples = spp; sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    sc.render.filepath = f"{out}/cyc_{spp}.png"
    t = time.time(); bpy.ops.render.render(write_still=True); print("CYCLES", spp, "spp", round(time.time() - t, 1), "s")

if '--eevee' in sys.argv:
    try:
        sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 16
        sc.render.filepath = f"{out}/eevee.png"
        t = time.time(); bpy.ops.render.render(write_still=True); print("EEVEE", round(time.time() - t, 1), "s")
    except Exception as e:
        print("EEVEE FAIL", e)

if '--bake' in sys.argv:
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 128
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier="bev")
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')
    img = bpy.data.images.new("ao", 1024, 1024)
    n = mat.node_tree.nodes.new("ShaderNodeTexImage"); n.image = img; mat.node_tree.nodes.active = n
    t = time.time(); bpy.ops.object.bake(type='AO', margin=8); print("BAKE AO 1024 128spp", round(time.time() - t, 1), "s")
    img.filepath_raw = f"{out}/ao.png"; img.file_format = 'PNG'; img.save()

bpy.ops.export_scene.gltf(filepath=f"{out}/test.glb", export_format='GLB', export_apply=True)
print("GLB bytes", os.path.getsize(f"{out}/test.glb"))
