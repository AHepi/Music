# What this does (plain words): like tests/bake_tools.py, but every dot looks at ONE exact point (the middle of the dot) instead of
# averaging four random points inside the dot. Random point positions differ from dot to dot, so a pattern slid by half a picture
# could differ by a few dots at hard edges for a reason that has nothing to do with tiling. With one exact point per dot, the half-tile
# test compares the pattern itself: a pattern that repeats exactly gives the same picture rolled by half (up to number rounding).
# Use (inside Blender):  blender -b --python point_bake.py -- RECIPE OUT_FOLDER SIZE 'JSON {view: params}' ['JSON base params'] ['Colour,Height']
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tests'))
import bake_tools as bt  # noqa: E402
bh = bt.bh


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    recipe_path, out_folder, size = arguments[0], arguments[1], int(arguments[2])
    views = json.loads(arguments[3])
    base = json.loads(arguments[4]) if len(arguments) > 4 else {}
    channels = tuple(arguments[5].split(',')) if len(arguments) > 5 else ('Colour', 'Height')
    os.makedirs(out_folder, exist_ok=True)
    recipe = bh.load_recipe(recipe_path)
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = 1
    scene.cycles.filter_width = 0.01
    for name, extra in views.items():
        parameters = dict(base)
        parameters.update(extra)
        group = recipe.build_node_group(parameters)
        bt.photograph(group, scene, tile, os.path.join(out_folder, name), channels)


if __name__ == '__main__':
    main()
