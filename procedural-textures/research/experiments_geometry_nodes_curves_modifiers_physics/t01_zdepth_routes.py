# What this does: tests the "draw height with an overhead camera" idea on a made-up staircase whose true heights we know:
# four flat steps (heights 0.00, 0.02, 0.05, 0.10) and a ramp. It draws the height three ways and compares each with the truth:
#   A. emission of Geometry > Position Z, saved as an 8-bit PNG
#   B. the same, saved as a 16-bit PNG
#   C. Camera Data > View Z Depth into the emission, 16-bit PNG
#   D. Cycles' own Z (depth) pass saved as a 32-bit float OpenEXR and read back
# Also checks: how many grey levels survive in 8 bit vs 16 bit; what happens at the edge of a step (anti-aliasing).
# Run:  blender -b --disable-autoexec -t 2 --python t01_zdepth_routes.py
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gn_tools as gt  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import bake_harness as bh  # noqa: E402

OUT = os.path.join(HERE, 'out', 't01_zdepth')
os.makedirs(OUT, exist_ok=True)
SIZE = 256

scene = gt.new_scene(SIZE)
# staircase: four columns each 0.25 wide, heights known; plus a ramp in the lower half of the last column
mesh = bpy.data.meshes.new('stairs')
verts, faces = [], []
def box(x0, x1, y0, y1, z):
    base = len(verts)
    verts.extend([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
    faces.extend([(base + 0, base + 3, base + 2, base + 1), (base + 4, base + 5, base + 6, base + 7), (base + 0, base + 1, base + 5, base + 4),
                  (base + 1, base + 2, base + 6, base + 5), (base + 2, base + 3, base + 7, base + 6), (base + 3, base + 0, base + 4, base + 7)])
heights = [0.0001, 0.02, 0.05, 0.10]
for i, z in enumerate(heights):
    box(i * 0.25, (i + 1) * 0.25, 0.0, 1.0, z)
mesh.from_pydata(verts, [], faces)
obj = bpy.data.objects.new('stairs', mesh)
scene.collection.objects.link(obj)
low, high, count = gt.z_range(obj)
print('height range', low, high)

truth = np.zeros((SIZE, SIZE))
for i, z in enumerate(heights):
    truth[:, int(i * SIZE / 4):int((i + 1) * SIZE / 4)] = (z - low) / (high - low)

results = {}
# A and B: position route, 8 and 16 bit
for label, sixteen in (('A_position_8bit', False), ('B_position_16bit', True)):
    gt.render_with(scene, obj, gt.height_material(low, high, 'position'), os.path.join(OUT, label + '.png'), True, sixteen)
    picture = bh.load_png_as_array(os.path.join(OUT, label + '.png'))[..., 0]
    results[label] = {'max_error': float(np.abs(picture - truth).max()), 'mean_error_ignoring_step_edges': float(np.abs(picture - truth)[:, 8:-8].mean()),
                      'distinct_levels': int(len(np.unique(np.round(picture * 65535)))) }
# C: camera route
gt.render_with(scene, obj, gt.height_material(low, high, 'camera'), os.path.join(OUT, 'C_camera_depth.png'), True, True)
picture = bh.load_png_as_array(os.path.join(OUT, 'C_camera_depth.png'))[..., 0]
results['C_camera_depth_16bit'] = {'max_error': float(np.abs(picture - truth).max()), 'mean_error': float(np.abs(picture - truth).mean())}
# D: Z pass and Position pass in a 32-bit float multilayer OpenEXR (Blender 5.2: set media_type = MULTI_LAYER_IMAGE first, then file_format = OPEN_EXR_MULTILAYER)
view_layer = scene.view_layers[0]
view_layer.use_pass_z = True
view_layer.use_pass_position = True
view_layer.use_pass_normal = True
obj.data.materials.clear()
obj.data.materials.append(gt.height_material(low, high, 'position'))
settings = scene.render.image_settings
settings.media_type = 'MULTI_LAYER_IMAGE'
settings.file_format = 'OPEN_EXR_MULTILAYER'
settings.color_depth = '32'
scene.view_settings.view_transform = 'Raw'
scene.render.filepath = os.path.join(OUT, 'D_passes.exr')
bpy.ops.render.render(write_still=True)
try:
    import OpenImageIO as oiio
    image_input = oiio.ImageInput.open(os.path.join(OUT, 'D_passes.exr'))
    # a Blender 5 multilayer EXR can be "multipart": every pass is its own sub-picture, so read them all
    channel_names, planes = [], []
    index = 0
    while True:
        spec = image_input.spec()
        data = image_input.read_image('float')
        if data.ndim == 2:
            data = data[..., None]
        for k, name in enumerate(spec.channelnames):
            channel_names.append(name if '.' in name and name.startswith('ViewLayer') else f'part{index}:{spec.getattribute("name") or ""}.{name}')
            planes.append(data[..., k])
        index += 1
        if not image_input.seek_subimage(index, 0):
            break
    image_input.close()
    results['D_parts'] = index
    results['D_channels'] = channel_names
    pixels = np.stack(planes, axis=-1)
    def channel(name):
        return pixels[..., channel_names.index(name)]
    depth_name = [n for n in channel_names if n.endswith('.Z') or n.endswith('Depth.V') or n.endswith('Depth.Z')]
    if depth_name:
        depth = channel(depth_name[0])
        norm = ((5.0 - depth) - low) / (high - low)
        results['D_zpass'] = {'channel': depth_name[0], 'max_error': float(np.abs(norm - truth).max()),
                              'mean_error': float(np.abs(norm - truth).mean()), 'raw_min': float(depth.min()), 'raw_max': float(depth.max())}
    position_z = [n for n in channel_names if 'Position' in n and n.endswith('.Z')]
    if position_z:
        height_world = channel(position_z[0])
        norm = (height_world - low) / (high - low)
        results['E_position_pass'] = {'channel': position_z[0], 'max_error': float(np.abs(norm - truth).max()), 'mean_error': float(np.abs(norm - truth).mean())}
    normal_z = [n for n in channel_names if 'Normal' in n and n.endswith('.Z')]
    if normal_z:
        results['F_normal_pass_z_min_max'] = [float(channel(normal_z[0]).min()), float(channel(normal_z[0]).max())]
    # the emission-of-Z picture saved in the same float file ('Combined' pass) - exact floats, no 8/16 bit rounding
    combined = [n for n in channel_names if 'Combined' in n and n.endswith('.R')]
    if combined:
        picture = channel(combined[0])
        results['G_emission_float_exr'] = {'max_error': float(np.abs(picture - truth).max()), 'mean_error': float(np.abs(picture - truth).mean())}
except Exception as error:
    import traceback
    results['D_error'] = traceback.format_exc()

# edge behaviour: take one image row across the first step edge (A_16bit) and list the values around the jump
row = bh.load_png_as_array(os.path.join(OUT, 'B_position_16bit.png'))[128, :, 0]
results['edge_values_around_first_jump'] = [round(float(v), 4) for v in row[60:68]]
with open(os.path.join(OUT, 'results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
