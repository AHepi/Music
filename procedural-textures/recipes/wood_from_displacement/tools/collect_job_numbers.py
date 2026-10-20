# What this does (plain words): collects the node counts and the bake times of the final jobs from their job.json / bake.json files into
# scores/job_numbers.json (used by tools/fill_guides.py for the speed table). Also stores how many Blender runs were used (counted by hand, see the argument).
# Use: python3 -I tools/collect_job_numbers.py NUMBER_OF_BLENDER_RUNS
import json
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def job(path):
    with open(os.path.join(BASE, path, 'job.json')) as handle:
        return json.load(handle)


out = {'blender_runs': int(sys.argv[1]) if len(sys.argv) > 1 else 0}
tile = job('area/tile_repeated_2x2')
out['nodes_main'] = tile['nodes_in_group']
out['nodes_area'] = job('area/area_2x2')['nodes_in_group']
out['nodes_identity'] = job('tests/renders/source_unchanged')['nodes_in_group']
with open(os.path.join(BASE, 'outputs', 'main_seed1', 'bake.json')) as handle:
    full = json.load(handle)
s0 = job('tests/renders/shift_0')
a2, a4, cr, a8 = job('area/area_2x2'), job('area/area_4x4'), job('area/crop_a'), job('tests/renders/area8_small')
rows = [['default tile, 1254 dots, standard harness bake of ALL maps (colour, height, roughness, metallic, normal, normal cross-check)', full['seconds']],
        ['default tile, 1254 dots, colour only / height only (1 sample)', f"{s0['render_seconds']['Colour']} / {s0['render_seconds']['Height']}"],
        ['building the nodes (once per run)', s0['build_seconds']],
        ['2 x 2 area, 2508 dots, colour / height (1 sample)', f"{a2['render_seconds']['Colour']} / {a2['render_seconds']['Height']}"],
        ['4 x 4 area, 2508 dots, colour / height (4 samples)', f"{a4['render_seconds']['Colour']} / {a4['render_seconds']['Height']}"],
        ['full-size piece of the 4 x 4 area (window), 1254 dots, colour', cr['render_seconds']['Colour']],
        ['8 x 8 area, 512 dots, colour (8 samples)', a8['render_seconds']['Colour']]]
out['speed_rows'] = rows
with open(os.path.join(BASE, 'scores', 'job_numbers.json'), 'w') as handle:
    json.dump(out, handle, indent=1)
print(json.dumps(out, indent=1))
