# What this does (plain words): bakes several settings variants of the slate recipe in ONE Blender run (to save start-up time and keep to one
# Blender process), each at a small size, and only the maps asked for. It uses the bake harness's own scene, camera and channel pictures
# (lib/bake_harness.py), so a picture made here is the same as the harness's picture of that map. Settings given here are laid over
# recipe/settings.json, exactly like the harness's --params.
# Use: blender -b --disable-autoexec -t 2 --python bake_variants.py -- OUT_FOLDER SIZE 'JSON {variant: {"params": {...}, "maps": ["Colour", "Height", "Roughness"]}}'
# A variant may also name its own "size" (round 2 addition, for small check bakes); otherwise SIZE is used.
# Writes OUT_FOLDER/<variant>/colour.png, height.png (16 bit), roughness.png and prints the time of each.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    out_folder, size, variants = arguments[0], int(arguments[1]), json.loads(arguments[2])
    recipe = bh.load_recipe(RECIPE)
    scene, tile = bh.new_bake_scene(size)
    for name, job in variants.items():
        started = time.time()
        folder = os.path.join(out_folder, name)
        os.makedirs(folder, exist_ok=True)
        size_here = int(job.get('size', size))
        scene.render.resolution_x = scene.render.resolution_y = size_here
        group = recipe.build_node_group(dict(job.get('params', {})))
        for channel in job.get('maps', ['Colour', 'Height']):
            material = bh.show_channel_material(group, channel)
            tile.data.materials.clear()
            tile.data.materials.append(material)
            bh.render_to(scene, os.path.join(folder, channel.lower().replace('colour', 'colour') + '.png'), channel != 'Colour', channel == 'Height')
        with open(os.path.join(folder, 'variant.json'), 'w') as handle:
            json.dump({'size': size_here, 'params': job.get('params', {}), 'maps': job.get('maps'), 'seconds': round(time.time() - started, 1)}, handle, indent=1)
        print(f'[variant] {name} done in {time.time() - started:.0f} s', flush=True)


if __name__ == '__main__':
    main()
