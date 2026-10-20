# What this does (plain words): bakes several pictures of the wood recipe in ONE Blender run (starting Blender is slow, so a list of
# jobs is done in one go). It uses the project's own bake harness (lib/bake_harness.py, not changed) to make the flat photographing
# scene and the "show one channel as plain light" material, so every picture is exact data, exactly as the normal harness command makes it.
# The only difference from the normal harness command: you choose which channels to photograph (the harness always makes all of them plus
# a Blender-node normal map, which costs time and disk).
#
# Use:  blender -b --disable-autoexec -t 2 --python tools/run_jobs.py -- JOBS.json [first_job_number last_job_number]
# JOBS.json is a list. A line without "out" is a plain note. A job:
#   {"out": "FOLDER", "size": 1254, "params": {...recipe settings...}, "channels": ["Colour", "Height", "Roughness"]}
# With "full": true the job is the complete standard harness bake (all channels and normal.png), the same as the harness command line.
# Channels: Colour (8-bit sRGB), Height (16-bit data), Roughness (8-bit data), Metallic. One file per channel in FOLDER:
# colour.png, height.png, roughness.png, metallic.png. A job log line (seconds, node count) is printed and written to FOLDER/job.json.
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

BASE = os.path.abspath(os.path.join(HERE, '..'))          # the recipe's own folder: a relative 'out' in a jobs file is relative to this, wherever Blender was started
RECIPE = os.path.join(HERE, '..', 'recipe', 'wood_from_maps_recipe.py')
FILES = {'Colour': 'colour.png', 'Height': 'height.png', 'Roughness': 'roughness.png', 'Metallic': 'metallic.png'}


def run_full_job(recipe, job):
    """The whole standard bake (colour, height 16-bit, roughness, metallic, normal.png from the height at strength 8) exactly as the harness command line does it."""
    started = time.time()
    out = os.path.join(BASE, job['out'])
    result = bh.bake_recipe(recipe, dict(job.get('params', {})), out, size=int(job.get('size', 1254)), quiet=True)
    bump = os.path.join(out, 'normal_bumpnode.png')
    if os.path.exists(bump):
        os.remove(bump)                       # the Blender-node normal is only a cross-check and costs 3 MB; not kept
    result['total_seconds'] = round(time.time() - started, 1)
    with open(os.path.join(out, 'job.json'), 'w') as handle:
        json.dump(result, handle, indent=1)
    print('[job]', out, json.dumps({k: v for k, v in result.items() if k != 'parameters'}), flush=True)


def run_job(recipe, job):
    if job.get('full'):
        return run_full_job(recipe, job)
    started = time.time()
    out = os.path.join(BASE, job['out'])
    os.makedirs(out, exist_ok=True)
    size = int(job.get('size', 1254))
    scene, tile = bh.new_bake_scene(size)
    group = recipe.build_node_group(dict(job.get('params', {})))
    build_seconds = time.time() - started
    seconds = {}
    for channel in job.get('channels', ['Colour', 'Height']):
        t0 = time.time()
        material = bh.show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        bh.render_to(scene, os.path.join(out, FILES[channel]), linear_data=(channel != 'Colour'), sixteen_bit=(channel == 'Height'))
        seconds[channel] = round(time.time() - t0, 1)
    info = {'size': size, 'params': job.get('params', {}), 'nodes_in_group': len(group.nodes), 'build_seconds': round(build_seconds, 1),
            'render_seconds': seconds, 'samples': scene.cycles.samples, 'filter_width': scene.cycles.filter_width,
            'total_seconds': round(time.time() - started, 1)}
    with open(os.path.join(out, 'job.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    print('[job]', out, json.dumps({k: v for k, v in info.items() if k != 'params'}), flush=True)


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    jobs = [j for j in json.load(open(arguments[0])) if 'out' in j]
    first = int(arguments[1]) if len(arguments) > 1 else 0
    last = int(arguments[2]) if len(arguments) > 2 else len(jobs) - 1
    recipe = bh.load_recipe(os.path.abspath(RECIPE))
    for number, job in enumerate(jobs):
        if number < first or number > last:
            continue
        try:
            run_job(recipe, job)
        except Exception as error:       # one failed job must not stop the others; the failure is a result
            import traceback
            print(f"[job FAILED] {job['out']}: {error}", flush=True)
            traceback.print_exc()
            sys.stdout.flush()


if __name__ == '__main__':
    main()
