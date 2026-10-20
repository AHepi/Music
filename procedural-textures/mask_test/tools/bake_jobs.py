# What this does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------
# It bakes several versions of the slate COPY (mask_test/slate_copy) one after the other inside ONE Blender run, writing for each version
# only the pictures asked for (colour, height, roughness). It uses the project's bake tool (lib/bake_harness.py) without changing it;
# the only difference is that it skips the normal map renders (the normal map is made afterwards from the height by a separate script),
# which saves about a third of the time.
# Use:  blender -b --disable-autoexec -t 2 --python bake_jobs.py -- JOBS.json
# JOBS.json = a list of {"name": ..., "out": folder, "size": 1254, "params": {...recipe settings...}, "channels": ["Colour", "Height", "Roughness"],
#                         "recipe": optional path of another recipe file (the original slate recipe, to prove the copy is unchanged)}
import json
import os
import sys
import time

sys.dont_write_bytecode = True          # never write .pyc files next to the recipes this reads (one of them belongs to another job)

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

RECIPE = os.path.join(PROC, 'mask_test', 'slate_copy', 'recipe', 'slate_recipe.py')
FILES = {'Colour': ('colour', False, False), 'Height': ('height', True, True), 'Roughness': ('roughness', True, False)}


def main():
    jobs = json.load(open(sys.argv[sys.argv.index('--') + 1]))
    for job in jobs:
        # the layer files are loaded by plain name, so forget them between jobs when a job uses a different recipe folder
        for name in ('layer_interface', 'layout', 'colour_and_fade', 'damage', 'moss', 'outline_and_shadow', 'combine', 'stamps'):
            sys.modules.pop(name, None)
        recipe = bh.load_recipe(job.get('recipe') or RECIPE)
        started = time.time()
        out = job['out']
        os.makedirs(out, exist_ok=True)
        scene, tile = bh.new_bake_scene(int(job.get('size', 1254)))
        group = recipe.build_node_group(dict(job.get('params') or {}))
        built = time.time()
        for channel in job.get('channels', ['Colour', 'Height', 'Roughness']):
            name, linear, sixteen = FILES[channel]
            material = bh.show_channel_material(group, channel)
            tile.data.materials.clear()
            tile.data.materials.append(material)
            bh.render_to(scene, os.path.join(out, name + '.png'), linear, sixteen)
        record = {'name': job['name'], 'size': job.get('size', 1254), 'params': job.get('params'), 'channels': job.get('channels'),
                  'build_seconds': round(built - started, 1), 'total_seconds': round(time.time() - started, 1)}
        json.dump(record, open(os.path.join(out, 'bake.json'), 'w'), indent=1)
        print('[job done]', json.dumps({k: record[k] for k in ('name', 'size', 'build_seconds', 'total_seconds')}), flush=True)


main()
