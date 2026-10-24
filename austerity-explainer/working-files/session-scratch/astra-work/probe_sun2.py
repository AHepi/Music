# What this does: for four sun rotations, renders a tiny empty sky looking toward +y and prints how orange it is.
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 8; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = 96, 54
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; t = w.node_tree; t.nodes.clear()
sky = t.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'; sky.sun_elevation = math.radians(5); sky.sun_disc = True
bg = t.nodes.new('ShaderNodeBackground'); out = t.nodes.new('ShaderNodeOutputWorld')
t.links.new(sky.outputs['Color'], bg.inputs['Color']); t.links.new(bg.outputs['Background'], out.inputs['Surface'])
cd = bpy.data.cameras.new('c'); cd.lens = 30; cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_euler = (math.radians(90), 0, 0)          # looks toward +y
import numpy as np
for deg in (0, 90, 180, 270):
    sky.sun_rotation = math.radians(deg)
    sc.render.filepath = f'/tmp/sunprobe_{deg}.png'; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(f'/tmp/sunprobe_{deg}.png'); px = np.array(im.pixels[:]).reshape(-1, 4)
    low = px.reshape(54, 96, 4)[20:30]; print('SUNROT', deg, 'mean RGB near horizon', [round(float(v), 3) for v in low.reshape(-1, 4)[:, :3].mean(axis=0)])
