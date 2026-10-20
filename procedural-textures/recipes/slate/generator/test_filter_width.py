# What this does (plain words): finds out how blurry Blender's own "Gaussian" pixel filter makes a picture for each filter width, by photographing the
# slate height at several widths and comparing with a numpy blur of the unblurred picture. (This is how the "blur 0.5 dots" in the maps recipe was set.)
# Use: blender -b --python test_filter_width.py -- DESCRIPTION.json OUT.json
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import slate_generator as sg
import slate_layers as layers
import bake_harness as bh

arguments = sys.argv[sys.argv.index('--') + 1:]
description = json.load(open(arguments[0]))
size = 512
scene, tile = bh.new_bake_scene(size)
bpy.data.objects.remove(tile)
mesh, count = sg.build_tile_mesh(layers.make_shape_list(description), description)
obj = bpy.data.objects.new('shapes', mesh)
scene.collection.objects.link(obj)
folder = os.path.join(HERE, '..', 'analysis', 'filter_test')
os.makedirs(folder, exist_ok=True)
sg.photograph(scene, obj, sg.channel_material('Height', description), os.path.join(folder, 'h_box.png'), True, True, 16, None)
sharp = bh.load_png_as_array(os.path.join(folder, 'h_box.png'))[..., 0]
results = {}
def blur(img, sigma):
    return sg.gaussian_blur_wrap(img, sigma)
candidates = {s: blur(sharp, s) for s in (0.3, 0.5, 0.7, 0.9, 1.1, 1.4, 1.8)}
for width in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0):
    path = os.path.join(folder, f'h_g{width}.png')
    sg.photograph(scene, obj, sg.channel_material('Height', description), path, True, True, 16, width)
    img = bh.load_png_as_array(path)[..., 0]
    errors = {s: float(np.abs(img - b).mean() * 255) for s, b in candidates.items()}
    best = min(errors, key=errors.get)
    results[width] = {'best_equivalent_sigma_dots': best, 'errors_levels': {str(k): round(v, 2) for k, v in errors.items()}}
    print(width, 'equivalent blur sigma ~', best, {k: round(v, 2) for k, v in errors.items()})
json.dump(results, open(arguments[1], 'w'), indent=1)
