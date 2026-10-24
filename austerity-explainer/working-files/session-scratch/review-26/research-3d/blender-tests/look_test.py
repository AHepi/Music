# Look tests (stills): warm dusk light, haze, ink lines, painterly filter. Uses the project's models read-only.
# Usage: blender -b --factory-startup --python look_test.py -- MODE OUT
import bpy, sys, time, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
mode, out = argv[0], argv[1]
MODELS = '/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
for name in ['town.glb', 'factory-a.glb']:
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name))
# camera: low, close street-level view of the works, tall frame
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 30
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam)
cam.location = Vector((1.6, -10.5, 0.9))
target = Vector((0.0, 0.0, 2.2))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam
# warm low sun (dusk) + cool sky
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; sun.color = (1.0, 0.62, 0.35); sun.angle = math.radians(4)
so = bpy.data.objects.new('sun', sun); scene.collection.objects.link(so)
so.rotation_euler = (math.radians(72), 0, math.radians(-38))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
nt = world.node_tree; bg = nt.nodes['Background']; bg.inputs[0].default_value = (0.20, 0.30, 0.42, 1); bg.inputs[1].default_value = 0.8
if 'fog' in mode:
    # haze in a big box around the set (a world-wide haze swallows the sky and turns it black)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 6)); box = bpy.context.active_object; box.scale = (60, 60, 12)
    mat = bpy.data.materials.new('haze'); mat.use_nodes = True; mnt = mat.node_tree
    for n in list(mnt.nodes):
        if n.type == 'BSDF_PRINCIPLED': mnt.nodes.remove(n)
    pv = mnt.nodes.new('ShaderNodeVolumePrincipled'); pv.inputs['Density'].default_value = 0.035
    pv.inputs['Anisotropy'].default_value = 0.55; pv.inputs['Color'].default_value = (0.75, 0.8, 0.9, 1)
    mnt.links.new(pv.outputs[0], mnt.nodes['Material Output'].inputs['Volume']); box.data.materials.append(mat)
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.image_settings.file_format = 'JPEG'; r.filepath = out
r.engine = 'BLENDER_EEVEE'; scene.eevee.taa_render_samples = 16
if 'fog' in mode:
    scene.eevee.volumetric_end = 60.0
if 'lines' in mode:
    r.use_freestyle = True; r.line_thickness_mode = 'ABSOLUTE'; r.line_thickness = 1.2
    vl = scene.view_layers[0]; vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets.new('ink') if len(fs.linesets) == 0 else fs.linesets[0]
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('ink')
    ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
    ls.linestyle.color = (0.08, 0.06, 0.05); ls.linestyle.thickness = 1.4
if 'kuwahara' in mode:
    tree = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); scene.compositing_node_group = tree
    rl = tree.nodes.new('CompositorNodeRLayers'); kw = tree.nodes.new('CompositorNodeKuwahara')
    outn = tree.nodes.new('NodeGroupOutput'); tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    kw.inputs['Size'].default_value = 9
    try: kw.inputs['Type'].default_value = 'Anisotropic'
    except Exception as e: print('type', e)
    tree.links.new(rl.outputs['Image'], kw.inputs['Image']); tree.links.new(kw.outputs['Image'], outn.inputs[0])
t = time.time(); bpy.ops.render.render(write_still=True)
print('LOOK_SECONDS', mode, round(time.time() - t, 1))
