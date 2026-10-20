# What this does (plain words): counts the lines of CODE (comment-only lines and empty lines are not counted) of the files that make up the mud trial,
# split into: reused unchanged from the shared snapshot, borrowed unchanged from lib/contrib, new boxes written for mud, recipe wiring, settings, and tools.
# Use: python3 -I count_lines.py   (writes line_counts.json next to this file and prints a table)
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SNAP = os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers')


def code_lines(path):
    count = 0
    with open(path) as handle:
        for line in handle:
            text = line.strip()
            if text and not text.startswith('#'):
                count += 1
    return count


groups = {
    'reused unchanged: the four paint layers, COMBINE and the layer interface (shared snapshot)': [os.path.join(SNAP, f) for f in
        ('colour_and_fade.py', 'damage.py', 'moss.py', 'outline_and_shadow.py', 'combine.py', 'layer_interface.py')],
    'reused unchanged but NOT used: the slate LAYOUT (imported for the "slate" option only)': [os.path.join(SNAP, 'layout.py')],
    "borrowed unchanged: the project's stone maker (lib/contrib/stone_tools.py, whole file; STONES calls polygon_stones)": [os.path.join(PROC, 'lib', 'contrib', 'stone_tools.py')],
    'new boxes written for mud': [os.path.join(HERE, f) for f in ('mud_layout.py', 'ruts.py', 'stones.py', 'mud_height_rule.py')],
    'recipe wiring (a copy of the slate recipe wiring, through the brick trial)': [os.path.join(HERE, 'mud_recipe.py')],
    'tools and tests (bake driver, views, checks, scoring, sheets, measuring)': [os.path.join(HERE, f) for f in
        ('run_views.py', 'final_bake.py', 'window_render.py', 'checks_run.py', 'checks_analyse.py', 'final_scores.py', 'make_mud_sheet.py', 'seed_sets_sheet.py',
         'look_sheet.py', 'look_numbers.py', 'measure_reference_once.py', 'set_values.py', 'count_lines.py')],
}
result = {}
for name, files in groups.items():
    per_file = {os.path.basename(f): code_lines(f) for f in files if os.path.exists(f)}
    result[name] = {'total': sum(per_file.values()), 'files': per_file}
settings = os.path.join(HERE, 'settings.json')
with open(settings) as handle:
    result['settings (settings.json lines)'] = {'total': sum(1 for line in handle if line.strip() not in ('{', '}')), 'files': {'settings.json': 0}}
with open(os.path.join(HERE, 'line_counts.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
for name, row in result.items():
    print(f"{row['total']:6d}  {name}   {row['files']}")
