# What this does: experiment 3b. When a baked height PICTURE is used inside a material (Image Texture node feeding a Bump node), the node's "Extension"
# setting decides what happens at the picture's edge. Four settings (Repeat, Extend, Clip, Mirror) are tried on a height picture that tiles perfectly, and the
# seam of the resulting normal map is measured. A texture that tiles must use Repeat.
# Run: blender -b --disable-autoexec -t 2 --python exp3b_image_extension_seam.py   (needs out/displacement/4d_smooth_noise_16bit.png from exp4_displacement.py part 4d)
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
source = os.path.join(ec.OUT, 'displacement', '4d_smooth_noise_16bit.png')
folder = os.path.join(ec.OUT, 'normal')
scene, tile = bh.new_bake_scene(256)
scene.cycles.samples = 16
results = {}
for extension in ('REPEAT', 'EXTEND', 'CLIP', 'MIRROR'):
    tree, w = rt.make_group_tree('image height ' + extension, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    image = bpy.data.images.load(source, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    node = w.add('ShaderNodeTexImage', 'img', interpolation='Linear', extension=extension)
    node.image = image
    w.link('in', 'Vector', 'img', 'Vector')
    w.add('ShaderNodeRGBToBW', 'bw')
    w.link('img', 'Color', 'bw', 'Color')
    w.link('bw', 'Val', 'out', 'Height')
    tile.data.materials.clear()
    tile.data.materials.append(bh.show_channel_material(tree, 'NormalBump', normal_distance=0.2))
    path = os.path.join(folder, f'E_bump_extension_{extension}.png')
    bh.render_to(scene, path, True, True)
    picture = bh.load_png_as_array(path)
    red = picture[..., 0]
    inner = (np.abs(np.diff(red, axis=1)).mean() + np.abs(np.diff(red, axis=0)).mean()) / 2.0
    wrap = (np.abs(red[:, 0] - red[:, -1]).mean() + np.abs(red[0, :] - red[-1, :]).mean()) / 2.0
    results[extension] = {'seam_ratio_of_the_normal_maps_red_channel': round(float(wrap / inner), 2),
                          'worst_edge_pixel_difference_from_the_rest': round(float(max(np.abs(red[:, 0] - red[:, 1]).max(), np.abs(red[:, -1] - red[:, -2]).max())), 3)}
json.dump(results, open(os.path.join(folder, 'extension_seam.json'), 'w'), indent=1)
print(json.dumps(results, indent=1))
