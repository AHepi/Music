# What this does (plain words): counts lines of code of the wood trial, sorted into what was REUSED unchanged (the shared layers from the frozen
# snapshot), what is NEW in this folder (the wood turn, CRACKS, KNOTS, GRAIN), what was BORROWED unchanged from the earlier wood build (the grain
# streak box), what was COPIED from the brick trial (the height rule box, not used in the final settings), the recipe wiring, the settings and the
# tools. A line is counted when it is not blank and does not start with '#' (comment lines are not counted). Writes code_lines.json.
# Use: python3 -I count_code.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SNAPSHOT = os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers')


def code_lines(path):
    with open(path) as handle:
        return sum(1 for line in handle if line.strip() and not line.strip().startswith('#'))


groups = {
    'reused unchanged: shared layers (layer interface, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE)':
        [os.path.join(SNAPSHOT, n) for n in ('layer_interface.py', 'colour_and_fade.py', 'damage.py', 'moss.py', 'outline_and_shadow.py', 'combine.py')],
    'reused unchanged: shared slate LAYOUT': [os.path.join(SNAPSHOT, 'layout.py')],
    'new: WOOD TURN (the layout box that turns the bundle a quarter)': [os.path.join(HERE, 'wood_layout.py')],
    'new: CRACKS': [os.path.join(HERE, 'cracks.py')],
    'new: KNOTS': [os.path.join(HERE, 'knots.py')],
    'new: GRAIN (its own wrapper)': [os.path.join(HERE, 'grain.py')],
    'borrowed unchanged from the earlier wood build: Wood Grain Gain box': [os.path.join(PROC, 'recipes', 'wood', 'generator', 'wood_shaders.py')],
    'copied from the brick trial with one name changed: HEIGHT RULE box (built only if recipe.height_rule is wood; not in the final settings)': [os.path.join(HERE, 'height_rule.py')],
    'recipe wiring (a copy of the brick/slate recipe plus the wood layers)': [os.path.join(HERE, 'wood_recipe.py')],
    'tools and tests': [os.path.join(HERE, n) for n in ('run_views.py', 'final_bake.py', 'checks_run.py', 'checks_analyse.py', 'final_scores.py', 'score_pair.py', 'score_views.py',
                                                          'set_settings.py', 'make_look_sheet.py', 'measure_reference_once.py', 'make_pictures.py', 'count_code.py')],
}
result = {}
for name, files in groups.items():
    result[name] = {'lines': sum(code_lines(f) for f in files), 'files': [os.path.relpath(f, PROC) for f in files]}
with open(os.path.join(HERE, 'settings.json')) as handle:
    result['settings (lines of settings.json that hold a setting)'] = {'lines': sum(1 for line in handle if '": ' in line and not line.strip().startswith('"_'))}
shared = sum(v['lines'] for k, v in result.items() if k.startswith('reused'))
new = sum(v['lines'] for k, v in result.items() if k.startswith('new'))
result['_summary'] = {'reused_unchanged': shared, 'new_boxes': new, 'borrowed_unchanged': result[[k for k in result if k.startswith('borrowed')][0]]['lines'],
                      'share_reused_of_reused_plus_new': round(shared / (shared + new), 3)}
with open(os.path.join(HERE, 'code_lines.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
for name, value in result.items():
    print(f"{value['lines'] if isinstance(value, dict) and 'lines' in value else ''!s:>6}  {name}" if name != '_summary' else f'  summary: {value}')
