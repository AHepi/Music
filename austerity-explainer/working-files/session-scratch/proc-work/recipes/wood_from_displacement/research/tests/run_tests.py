# What this does: renders the research test pictures. It reads a list of jobs (a small JSON file), builds each test material
# with the functions in woodtests.py, and "photographs" it flat from above (the same way the project's bake harness does,
# one channel at a time, light-free, so every dot of the picture is exact data).
# Use:  blender -b --disable-autoexec -t 2 --python run_tests.py -- JOBS.json
# A job: {"name": "pieces_full", "builder": "build_pieces", "params": {...}, "channels": ["height","colour"], "area": 1, "size": 512, "samples": 8}
# Output: tests/renders/NAME_AREAxAREA_CHANNEL.png  (grey height or colour). Colour is stored like a normal picture (sRGB).
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
sys.path.insert(0, HERE)
sys.path.insert(0, PROC + 'lib')
import bake_harness as bh  # noqa: E402
import nodekit as nk  # noqa: E402
import woodtests as wt  # noqa: E402

RENDERS = os.path.join(HERE, 'renders')


def render_job(scene, tile, job):
    builder = getattr(wt, job['builder'])
    wt.INTERP[0] = 'Linear'                                              # every job starts with the normal picture reading mode
    area = float(job.get('area', 1))
    size = int(job.get('size', 512))
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.cycles.samples = int(job.get('samples', 8))
    scene.cycles.filter_width = float(job.get('filter_width', 1.0))     # 1.0 = the harness default; small = read each dot at its centre
    for channel in job.get('channels', ['height']):
        started = time.time()
        material = bpy.data.materials.new('test')
        material.use_nodes = True
        tree = material.node_tree
        tree.nodes.clear()
        kit = nk.Kit(tree)
        value = builder(kit, channel, area, **job.get('params', {}))
        if isinstance(value, tuple):
            kit.emit_rgb(*value)
        else:
            kit.emit_grey(value)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        label = job.get('label', job['name'])
        path = os.path.join(RENDERS, f"{label}_{int(area)}x{int(area)}_{channel}.png")
        bh.render_to(scene, path, linear_data=(channel == 'height'), sixteen_bit=False)
        print(f"[test] {label} {channel} area {area} size {size}: {len(tree.nodes)} nodes, {time.time() - started:.1f} s -> {path}", flush=True)
        bpy.data.materials.remove(material)


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    jobs = json.load(open(arguments[0]))
    os.makedirs(RENDERS, exist_ok=True)
    scene, tile = bh.new_bake_scene(512)
    for job in jobs:
        if 'builder' not in job:        # a plain note line at the top of a jobs file
            continue
        try:
            render_job(scene, tile, job)
        except Exception as error:      # one failed test must not stop the others; the failure is the result
            import traceback
            print(f"[test FAILED] {job.get('label', job['name'])}: {error}", flush=True)
            traceback.print_exc()


if __name__ == '__main__':
    main()
