# What this does: photographs ONE small brick recipe (research/.../test_recipes/bricks_and_wave_recipe.py) eight times at 256 x 256 dots with the
# project's overhead camera, changing only Blender's "view transform" (Render Properties > Color Management > View Transform), to show the AgX trap:
#   row 1 = the colour picture under Standard (right for colour), AgX (what a brand-new Blender scene uses), Filmic, Raw;
#   row 2 = the height picture under Raw (right for data), Standard, AgX, Filmic.
# It also measures each picture's average value and writes the numbers to view_transform_numbers.json, and the squares plus a sweep.json
# (the file format lib/make_strip.py reads) to the folder view_transform_tiles/.
# Run (inside Blender):  blender -b --disable-autoexec -t 2 --python view_transform_strip.py
# Then (plain Python):   python3 -I ../../../lib/make_strip.py view_transform_tiles OUT.png --columns 4 --title "..."
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as harness  # noqa: E402

RECIPE_FILE = os.path.join(PROC, 'research', 'experiments_seamless_tiles_and_baking', 'test_recipes', 'bricks_and_wave_recipe.py')
OUT_FOLDER = os.path.join(HERE, 'view_transform_tiles')
SIZE = 256
CASES = [  # (channel shown, view transform, label under the square)
    ('Colour', 'Standard', 'colour, Standard (right)'),
    ('Colour', 'AgX', 'colour, AgX (new-scene default)'),
    ('Colour', 'Filmic', 'colour, Filmic'),
    ('Colour', 'Raw', 'colour, Raw'),
    ('Height', 'Raw', 'height, Raw (right)'),
    ('Height', 'Standard', 'height, Standard'),
    ('Height', 'AgX', 'height, AgX'),
    ('Height', 'Filmic', 'height, Filmic'),
]


def photograph(scene, path, view_transform):
    """Render the square from above with the given view transform, 8-bit PNG (the harness's render_to always picks Standard or Raw itself)."""
    scene.view_settings.view_transform = view_transform
    scene.view_settings.look = 'None'
    settings = scene.render.image_settings
    settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'RGB', '8'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    os.makedirs(OUT_FOLDER, exist_ok=True)
    recipe = harness.load_recipe(RECIPE_FILE)
    scene, tile = harness.new_bake_scene(SIZE)
    group = recipe.build_node_group({})
    files, labels, numbers = [], [], {}
    for index, (channel, view_transform, label) in enumerate(CASES):
        material = harness.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        path = os.path.join(OUT_FOLDER, f'tile_{index:02d}.png')
        photograph(scene, path, view_transform)
        values = harness.load_png_as_array(path)          # 0..1 as stored in the file
        numbers[label] = {'average_value_in_file': round(float(values.mean()), 4),
                          'average_red_green_blue': [round(float(v), 4) for v in values.reshape(-1, 3).mean(axis=0)]}
        files.append(os.path.basename(path))
        labels.append(label)
    with open(os.path.join(OUT_FOLDER, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels}, handle, indent=1)
    # how far each wrong choice is from the right one, as an average over the picture
    right_colour = numbers['colour, Standard (right)']['average_value_in_file']
    right_height = numbers['height, Raw (right)']['average_value_in_file']
    for label, row in numbers.items():
        right = right_colour if label.startswith('colour') else right_height
        row['average_value_minus_the_right_one'] = round(row['average_value_in_file'] - right, 4)
    numbers['about'] = ('bricks_and_wave_recipe.py photographed at 256 dots with lib/bake_harness.new_bake_scene (Cycles, 4 samples, Box 1.0 filter), '
                        'only the view transform changed; 8-bit PNG; values 0..1 as stored in the file')
    numbers['blender_version'] = bpy.app.version_string
    with open(os.path.join(HERE, 'view_transform_numbers.json'), 'w') as handle:
        json.dump(numbers, handle, indent=1)
    print('[view transform strip]', json.dumps(numbers))


main()
