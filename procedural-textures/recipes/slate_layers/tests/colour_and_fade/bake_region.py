# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Runs INSIDE Blender. Bakes several pictures of one recipe, one picture per set of settings, but only a RECTANGLE of the tile (Cycles'
# "render border"), at the full dot density of a 1254-dot tile (or any size you give). That makes "what does this setting do" pictures
# cheap: a 627 x 300 dot corner takes a fraction of the time of the whole tile, and the streaks and drips are big enough to judge.
# Use (through tests/blender.sh):
#   blender.sh bake_region.py -- RECIPE.py OUT_FOLDER SIZE X0 Y0 X1 Y1 SAMPLES 'JSON {picture name: {settings...}}' ['JSON settings for every picture'] [Colour,Height]
# X0 Y0 X1 Y1 are shares of the tile measured from the TOP-LEFT corner (0..1). SIZE = dots across the whole tile (1254 = the real size).
# Writes OUT_FOLDER/<name>_colour.png (and _height.png, 16 bit, if asked for).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    recipe_path, out_folder, size = arguments[0], arguments[1], int(arguments[2])
    x0, y0, x1, y1 = (float(v) for v in arguments[3:7])
    samples = int(arguments[7])
    views = json.loads(arguments[8])
    base = json.loads(arguments[9]) if len(arguments) > 9 else {}
    channels = arguments[10].split(',') if len(arguments) > 10 else ['Colour']
    os.makedirs(out_folder, exist_ok=True)
    recipe = bh.load_recipe(recipe_path)
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = samples
    scene.render.use_border = True
    scene.render.use_crop_to_border = True
    scene.render.border_min_x, scene.render.border_max_x = x0, x1
    scene.render.border_min_y, scene.render.border_max_y = 1.0 - y1, 1.0 - y0        # Blender counts y from the bottom
    for name, extra in views.items():
        parameters = dict(base)
        parameters.update(extra)
        group = recipe.build_node_group(parameters)
        for channel in channels:
            material = bh.show_channel_material(group, channel)
            tile.data.materials.clear()
            tile.data.materials.append(material)
            suffix = {'Colour': '_colour', 'Height': '_height', 'Roughness': '_roughness'}[channel]
            bh.render_to(scene, os.path.join(out_folder, name + suffix + '.png'), channel != 'Colour', channel == 'Height')


if __name__ == '__main__':
    main()
