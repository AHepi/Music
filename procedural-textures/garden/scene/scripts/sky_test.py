# What this does: tiny equirectangular render (256x128, 2 samples) of the scene's own sky with its sun disc switched on, plus a marker sphere where the SUN LAMP is,
#   to see whether the sky's sun and the lamp are in the same place. Works on a throw-away copy in memory; saves one small PNG; saves no .blend.
import bpy, math, sys
from mathutils import Vector
sc = bpy.context.scene
sun = bpy.data.objects['Golden hour sun']
travel = sun.matrix_world.to_3x3() @ Vector((0, 0, -1)); toward_sun = -travel.normalized()
print('SUN LAMP points from direction', [round(v, 3) for v in toward_sun], 'elevation', round(math.degrees(math.asin(toward_sun.z)), 1), 'azimuth (atan2 y,x)', round(math.degrees(math.atan2(toward_sun.y, toward_sun.x)), 1))
for o in list(bpy.data.objects):
    o.hide_render = True
w = sc.world
sky = next(n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeTexSky')
sky.sun_disc = True; sky.sun_size = math.radians(3)
# marker sphere at the lamp's direction
bpy.ops.mesh.primitive_uv_sphere_add(radius=4, location=tuple(toward_sun * 100))
sph = bpy.context.object
m = bpy.data.materials.new('mk'); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear(); e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (0, 1, 0, 1); e.inputs['Strength'].default_value = 5
o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0]); sph.data.materials.append(m)
# plain sky only (remove the script's banding so we see the raw sky): link sky colour straight to background
bg = next(n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground')
w.node_tree.links.new(sky.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = 0.0003
cd = bpy.data.cameras.new('pano'); cd.type = 'PANO'
try: cd.panorama_type = 'EQUIRECTANGULAR'
except Exception: cd.cycles.panorama_type = 'EQUIRECTANGULAR'
cam = bpy.data.objects.new('pano', cd); sc.collection.objects.link(cam); cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam   # looks along +Y
sc.render.engine = 'CYCLES'; sc.cycles.samples = 2; sc.cycles.use_denoising = False; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 256, 128, 100
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0
sc.render.filepath = sys.argv[sys.argv.index('--') + 1]
bpy.ops.render.render(write_still=True)
print('SKYTEST_DONE')
