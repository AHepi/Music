# What this does (plain words): collects every number of the slate-in-layers work into ONE file, final_report.json, in the folder above.
# It reads the numbers from the result files the tests wrote (it does not type them in by hand), so the report cannot disagree with them.
# Where a result file is missing, it writes "missing" instead of a number. Use (plain python): python3 -I make_final_report.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..', '..'))


def load(path):
    full = os.path.join(SL, path)
    if not os.path.exists(full):
        return 'missing'
    with open(full) as handle:
        return json.load(handle)


def table_rows(path):
    """reads a markdown table into a list of dicts (first table of the file)."""
    full = os.path.join(SL, path)
    if not os.path.exists(full):
        return 'missing'
    lines = [line.strip() for line in open(full) if line.strip().startswith('|')]
    header = [cell.strip() for cell in lines[0].strip('|').split('|')]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        if len(cells) == len(header) and not set(cells[0]) <= set('-'):
            rows.append(dict(zip(header, cells)))
        elif len(cells) != len(header):
            break
    return rows


same_kind = load('outputs/default/score_same_kind.json')
pixel = load('outputs/default/score_pixel_for_transparency.json')
settings = load('recipe/settings.json')
report = {
    '_words': 'Every number of the slate-in-layers work (layers inside one Blender recipe, pure procedural, not fitted). Same-kind = lib/texture_compare.py '
              'against the slate reference (a guide only); dot-for-dot = lib/pixel_compare.py, for transparency only. Written by '
              'integration/takeover/make_final_report.py from the result files.',
    'who': 'five layer builders; first integrator (tuning rounds 1-13, most bakes; cut off by a machine restart at about 03:15 on 20 October); '
           'second integrator (checked everything, re-ran what was cut off, wrote the guides and this report)',
    'recipe': {
        'entry point': 'recipe/slate_recipe.py (build_node_group(parameters) for lib/bake_harness.py)',
        'boxes and node counts': {k: v['nodes'] for k, v in load('integration/tools_used.json').items()},
        'settings file': {'path': 'recipe/settings.json', 'entries': len(settings), 'bytes': os.path.getsize(os.path.join(SL, 'recipe/settings.json'))},
        'settings audit (lib/description_audit.py --limit-kilobytes 8)': load('integration/takeover/settings_audit.json'),
        'controls in recipe/controls.md': sum(1 for line in open(os.path.join(SL, 'recipe/controls.md')) if line.startswith('| `')),
        'declared links': [{'reader': 'moss', 'socket': 'Damage Mask', 'from': 'damage Mask', 'settings': 'moss.damage_avoid 0.8, moss.damage_attract 0'}],
        'stack order': settings.get('recipe.stack_order'),
        'edits to layer files during integration': table_rows('integration/CHANGES_TO_LAYER_FILES.md'),
    },
    'default tile (outputs/default, 1254 dots)': {
        'same-kind': {'overall': same_kind['overall'], 'groups': same_kind['groups'], 'scores': same_kind['scores'],
                      'mean Lab reference / default': [same_kind['facts']['mean_lab_reference'], same_kind['facts']['mean_lab_candidate']],
                      'feature size along x, y in dots, reference / default': [same_kind['facts']['correlation_length_px_reference'],
                                                                               same_kind['facts']['correlation_length_px_candidate']]},
        'brief aim for the colour group': 0.8,
        'aim reached': same_kind['groups']['colour'] >= 0.8,
        'dot-for-dot (transparency only)': {k: pixel[k] for k in ('colour_mean_delta_e', 'colour_ssim', 'edge_skill_2px', 'height_mae_best_fit_levels',
                                                                   'normal_mean_angle_degrees', 'tier_reached')},
        'bake': load('outputs/default/bake.json'),
    },
    'first whole-stack bake before tuning (round 1)': {k: v for k, v in load('integration/bake_round1/score.json').items() if k in ('overall', 'groups')},
    'tuning rounds measured before their pictures were deleted': load('integration/takeover/measured_before_clean_up.json'),
    'tuning round 14 (second integrator; result: settings kept)': load('integration/r14_results.json'),
    'ladder (what each layer buys, 1254 dots)': load('ladder/ladder_scores.json'),
    'independence (384 dots)': load('tests/independence_full/independence_results.json'),
    'half-tile test (512 dots)': load('tests/half_tile_layers/half_tile_results.json'),
    'declared link measured (768 dots)': load('links_and_order/link_height/link_measures.json'),
    'variations (1254 dots, colour group)': {'settings': load('variations/variations.json'), 'colour group': load('variations/same_kind_colour_scores.json')},
    'seed spread of the default settings (1254 dots, colour group)': load('variations/seed_spread/seed_spread.json'),
    'area 2 x 2 (2508 dots)': {'measures': load('area/area_2x2/area_measures.json'), 'time': load('area/area_2x2/time.json')},
    'area 4 x 4 (5016 dots, colour only)': {'measures': load('area/area_4x4/area_measures.json'), 'time': load('area/area_4x4/time.json')},
    'resolution': {'times': load('resolution/whole_recipe/times.json'), 'differences': load('resolution/whole_recipe/resolution_differences.json')},
    'reuse on a brick layout': {
        'what had to change': 'a brick layout of about 40 nodes making the same eleven bundle numbers, and 53 settings (BRICK_SETTINGS); no line of any layer file',
        'same-kind against the BRICK reference (sanity check, never tuned against it)': {k: v for k, v in load('reuse/score_against_brick/score.json').items() if k in ('overall', 'groups')},
        'settings round 2 (colour only, 768 dots)': load('reuse/settings_round_2/scores.json'),
    },
    'whole-recipe strips': load('controls_sweeps/whole_recipe/strips.json'),
    're-run after the restart': [
        'resolution at 2508 dots (colour, height, roughness) and the resolution comparison',
        'reuse: the brick colour-and-fade-only view and the three mask views, the normal map, the sheet, the brick score, and a second brick settings round',
        'ladder rungs 2 (+ moss) and "without outline", the ladder scores and sheet',
        'declared-link and stack-order pictures, tone-blend height pictures, and the link measured in height and roughness',
        'whole-recipe strips of five settings',
        'three more seed sets of the default settings (seed spread)',
        'the 4 x 4 area (5016 dots)',
        'tuning round 14 (a lighter shadow and stronger streaks; checked on three seed sets; not adopted)',
        'the controls table regenerated (identical to the one on disk)',
    ],
    'kept from before the restart (checked, not re-run)': [
        'outputs/default (the default tile and its scores)', 'debug_views (every layer alone)', 'tests/independence_full', 'tests/half_tile_layers',
        'variations (eight tiles, contact sheet, scores)', 'area/area_2x2', 'resolution at 512 and 1254', 'reuse brick_all colour and height', 'layer builders\' strips',
    ],
}
with open(os.path.join(SL, 'final_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('written', os.path.join(SL, 'final_report.json'))
missing = [k for k, v in report.items() if v == 'missing'] + [f'{k} / {kk}' for k, v in report.items() if isinstance(v, dict) for kk, vv in v.items() if vv == 'missing']
print('missing:', missing)
