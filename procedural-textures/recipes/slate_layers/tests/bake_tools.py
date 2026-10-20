# What this does: small helpers (used INSIDE Blender) to take many quick "pictures of one thing" from a recipe, without baking all the
# maps each time. bake_views() builds the recipe once per view, photographs the Colour output (what you see) and the Height output (exact
# 16-bit numbers) and writes <folder>/<view name>_colour.png and <view name>_height.png. Run through run_views.py.
# Also: set_samples() to raise Cycles' samples (the harness uses 4; 16 gives cleaner one-dot edges).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402


def photograph(group, scene, tile, path_without_extension, channels=('Colour', 'Height')):
    for channel in channels:
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        suffix = {'Colour': '_colour', 'Height': '_height', 'Roughness': '_roughness', 'Metallic': '_metallic'}[channel]
        bh.render_to(scene, path_without_extension + suffix + '.png', channel != 'Colour', channel == 'Height')


def bake_views(recipe_path, views, out_folder, size=512, samples=4, base_parameters=None, channels=('Colour', 'Height')):
    """views: dict name -> parameters (merged over base_parameters). Each is built and photographed."""
    os.makedirs(out_folder, exist_ok=True)
    recipe = bh.load_recipe(recipe_path)
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = samples
    for name, extra in views.items():
        parameters = dict(base_parameters or {})
        parameters.update(extra)
        group = recipe.build_node_group(parameters)
        photograph(group, scene, tile, os.path.join(out_folder, name), channels)
    return out_folder


def main():
    """blender -b --python bake_tools.py -- RECIPE OUT_FOLDER SIZE SAMPLES 'JSON {view: params}' ['JSON base params'] ['Colour,Height']"""
    arguments = sys.argv[sys.argv.index('--') + 1:]
    recipe_path, out_folder, size, samples = arguments[0], arguments[1], int(arguments[2]), int(arguments[3])
    views = json.loads(arguments[4])
    base = json.loads(arguments[5]) if len(arguments) > 5 else {}
    channels = tuple(arguments[6].split(',')) if len(arguments) > 6 else ('Colour', 'Height')
    bake_views(recipe_path, views, out_folder, size, samples, base, channels)


if __name__ == '__main__':
    main()
