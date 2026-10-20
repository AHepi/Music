# What this does: makes "what does this setting do?" pictures. You give it a function that builds a small shader node group for one value
# of a setting, and a list of values; it renders each one as a small square picture. Then make_strip.py (plain Python, run outside Blender)
# joins the squares into one labelled strip or grid. Use these to show, for example, how Noise "Detail" 0, 2, 4, 8, 16 looks.
# Use (inside Blender):
#   import sweep_tools as st
#   st.render_sweep(build_group, values=[1, 2, 4, 8], out_folder='out/noise_detail', channel='Colour', size=256, labels=['detail 1', ...])
#   build_group(value) must return a shader node group with input 'Vector' and an output called like the channel ('Colour' or 'Height').
# Then:  python3 -I lib/make_strip.py out/noise_detail out/noise_detail_strip.png [--columns 5] [--title "Noise Texture: Detail"]
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bake_harness as bh  # noqa: E402


def render_sweep(build_group, values, out_folder, channel='Colour', size=256, labels=None, linear_data=None):
    os.makedirs(out_folder, exist_ok=True)
    linear = (channel != 'Colour') if linear_data is None else linear_data
    scene, tile = bh.new_bake_scene(size)
    files = []
    for index, value in enumerate(values):
        group = build_group(value)
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        path = os.path.join(out_folder, f'tile_{index:02d}.png')
        bh.render_to(scene, path, linear, False)
        files.append(os.path.basename(path))
    with open(os.path.join(out_folder, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels or [str(v) for v in values]}, handle, indent=1)
    return files
