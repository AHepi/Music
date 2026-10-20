# What this does (plain words): takes quick, zoomed-in pictures of ONE WINDOW of the slate recipe (for example a 0.32 x 0.32 share of the
# tile) instead of the whole tile, for many sets of settings in one Blender run. It is used for the "what does this setting do" strips and
# the before/after pictures of the DAMAGE layer: because only a small window is drawn, a picture costs a sixth of a full 1254 dot bake,
# and the window shows the lower edges of several slates at about 1000 dots per tile.
# Use (inside Blender):
#   blender -b --disable-autoexec -t 2 --python window_render.py -- RECIPE OUT_FOLDER PIXELS 'cx,cy,width' 'JSON {job: {"params": {...}, "channel": "Colour"}}'
#   cx, cy = window centre in tile units (cy counts from the BOTTOM of the tile, like the Vector); width = window size in tile units.
#   channel: Colour, Height (exact 16 bit), Roughness. Writes OUT_FOLDER/<job>_<channel>.png
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    recipe_path, out_folder, pixels = arguments[0], arguments[1], int(arguments[2])
    centre_x, centre_y, window = [float(v) for v in arguments[3].split(',')]
    jobs = json.loads(arguments[4])
    os.makedirs(out_folder, exist_ok=True)
    recipe = bh.load_recipe(recipe_path)
    scene, tile = bh.new_bake_scene(pixels)
    camera = scene.camera
    camera.location = (centre_x, centre_y, 5.0)
    camera.data.ortho_scale = window
    for name, job in jobs.items():
        group = recipe.build_node_group(dict(job.get('params', {})))
        channel = job.get('channel', 'Colour')
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        bh.render_to(scene, os.path.join(out_folder, f'{name}_{channel.lower()}.png'), channel != 'Colour', channel == 'Height')


if __name__ == '__main__':
    main()
