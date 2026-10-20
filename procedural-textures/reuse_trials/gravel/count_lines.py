# What this does (plain words): counts lines of code (not blank lines, not comment lines) in the files the gravel trial uses, split into
#   shared and reused UNCHANGED (the frozen snapshot's layer files the recipe imports), NEW boxes written for gravel, the recipe WIRING
#   (mostly a copy of the slate recipe's wiring), SETTINGS (settings.json) and TOOLS AND TESTS (scripts that bake, score, check and draw).
# A line inside a multi-line text string (the plain-words notes at the top of functions) counts as a comment line.
# Use: python3 -I count_lines.py   (prints a table and writes checks/line_counts.json)
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.abspath(os.path.join(HERE, '..', 'shared_layers_snapshot', 'layers'))
GROUPS = {
    'shared, reused unchanged (in the final stack)': [os.path.join(SNAPSHOT, name) for name in
                                                      ('layer_interface.py', 'colour_and_fade.py', 'damage.py', 'outline_and_shadow.py', 'combine.py')],
    'shared, tried but out of the final stack (MOSS)': [os.path.join(SNAPSHOT, 'moss.py')],
    'new boxes': [os.path.join(HERE, name) for name in ('gravel_layout.py', 'soil.py', 'facets.py', 'gravel_height_rule.py')],
    'recipe wiring': [os.path.join(HERE, 'gravel_recipe.py')],
    'settings': [os.path.join(HERE, 'settings.json')],
    'tools and tests': [os.path.join(HERE, name) for name in ('run_views.py', 'final_bake.py', 'final_scores.py', 'checks_run.py', 'checks_analyse.py',
                                                              'make_gravel_sheet.py', 'seed_sets_sheet.py', 'baseline_scores.py', 'count_lines.py', 'count_node_share.py',
                                                              'score_height_blends.py', 'score_probe.sh', 'score_ladder.py', 'make_maps_sheet.py', 'compare_details.py', 'seam_location_check.py',
                                                              'contact_sheet.py', 'measure_stones.py', 'measure_colours.py')],
}


def code_lines(path):
    count, in_text = 0, False
    with open(path) as handle:
        for raw in handle:
            line = raw.strip()
            if path.endswith('.json'):
                count += bool(line) and not line.startswith('"_')
                continue
            quotes = line.count('"""')
            if in_text:
                in_text = quotes % 2 == 0
                continue
            if line.startswith('"""'):
                in_text = quotes == 1
                continue
            if line and not line.startswith('#'):
                count += 1
    return count


table = {}
for group, paths in GROUPS.items():
    files = {os.path.basename(p): code_lines(p) for p in paths if os.path.exists(p)}
    table[group] = {'files': files, 'total': sum(files.values())}
    print(f"{group:28s} {table[group]['total']:5d}   {files}")
os.makedirs(os.path.join(HERE, 'checks'), exist_ok=True)
with open(os.path.join(HERE, 'checks', 'line_counts.json'), 'w') as handle:
    json.dump(table, handle, indent=1)
