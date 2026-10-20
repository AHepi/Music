# What this does (plain words): collects the node counts and the bake times of the round 2 jobs from their job.json / bake.json files into scores/job_numbers_round2.json
# (used by tools/fill_guides_round2.py for the speed table). Also stores how many Blender runs were used (counted by hand, see the argument).
# Use: python3 -I tools/collect_job_numbers_round2.py NUMBER_OF_BLENDER_RUNS
import json
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def job(path):
    with open(os.path.join(BASE, path, 'job.json')) as handle:
        return json.load(handle)


out = {'what_this_is': 'Node counts and bake times of the round 2 jobs (tools/collect_job_numbers_round2.py). Times are seconds on a machine shared with two other helpers (load 4 to 9 on 4 cores), 2 threads.',
       'blender_runs': int(sys.argv[1]) if len(sys.argv) > 1 else 0}
tile = job('area/tile_repeated_2x2')
out['nodes_main'] = tile['nodes_in_group']
out['nodes_area'] = job('area/area_2x2')['nodes_in_group']
out['nodes_identity'] = job('tests/renders/source_unchanged')['nodes_in_group']
out['nodes_comparison'] = job('outputs/comparison_seed1')['nodes_in_group']
with open(os.path.join(BASE, 'outputs', 'main_seed1', 'bake.json')) as handle:
    full = json.load(handle)
s0 = job('tests/renders/shift_half')
a2, a4, cr, rp = job('area/area_2x2'), job('area/area_4x4'), job('area/crop_a'), job('area/tile_repeated_2x2')
dbg = job('area/debug_source_x')
rows = [['default tile, 1254 dots, standard harness bake of ALL maps (colour, height, roughness, metallic, normal, normal cross-check)', full['seconds']],
        ['default tile, 1254 dots, colour only / height only (1 sample)', f"{s0['render_seconds']['Colour']} / {s0['render_seconds']['Height']}"],
        ['building the nodes (once per job)', s0['build_seconds']],
        ['2 x 2 area, 1254 dots across (2 dots per picture dot, 4 samples), colour / height', f"{a2['render_seconds']['Colour']} / {a2['render_seconds']['Height']}"],
        ['4 x 4 area, 2508 dots across (2 dots per picture dot, 4 samples), colour / height', f"{a4['render_seconds']['Colour']} / {a4['render_seconds']['Height']}"],
        ['4 x 4 area, exact "which source dot" picture, 1254 dots across (1 sample)', dbg['render_seconds']['Height']],
        ['full-size piece of the 4 x 4 area (window), 1254 dots, colour', cr['render_seconds']['Colour']]]
out['speed_rows'] = rows
os.makedirs(os.path.join(BASE, 'scores'), exist_ok=True)
with open(os.path.join(BASE, 'scores', 'job_numbers_round2.json'), 'w') as handle:
    json.dump(out, handle, indent=1)
print(json.dumps(out, indent=1))
