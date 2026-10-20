# What this does (plain words): adds a new section called "look fixes (round 15)" to ../final_report.json with every number of the look-fix round and of the re-bake that followed
# (settings changed, new controls, the new default tile's scores next to the old ones, the ladder, variations, seed spread, 2 x 2 area, half-tile test, independence of the two
# changed layers, the 512 confirmation, node counts, Blender runs, folder size). It reads the numbers from the result files in this folder tree, so nothing is typed in by hand
# except the lists of things done and not done. It KEEPS every earlier entry of final_report.json (a copy of the file as it was is look_fixes/final_report_before_look_fixes.json).
# Use (plain python): python3 -I add_round15_to_final_report.py
import json, os, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
SL = os.path.abspath(os.path.join(HERE, '..'))
def load(*parts):
    return json.load(open(os.path.join(SL, *parts)))
report_path = os.path.join(SL, 'final_report.json')
backup = os.path.join(HERE, 'final_report_before_look_fixes.json')
if not os.path.exists(backup):
    shutil.copy(report_path, backup)
report = json.load(open(backup))             # always start from the saved old report, so running this twice gives the same file
round1, round2 = load('look_fixes', 'round_1_tuner_result.json'), load('look_fixes', 'round_2_tuner_result.json')
critic = load('verify_look_after_fixes', 'round_2', 'critic_result.json')
independence = load('tests', 'independence_changed_layers_after_look_fixes', 'independence_two_layers_results.json')
confirm = load('tests', 'confirm_512_after_look_fixes_differences.json')
nodes = load('recipe', 'node_counts_after_look_fixes.json')
size_bytes = int(subprocess.run(['du', '-sb', SL], capture_output=True, text=True).stdout.split()[0])
settings = load('recipe', 'settings.json')
section = {
    '_words': 'Look fixes (round 15, 20 October): a look checker listed 11 faults of the default tile, a tuner fixed them by hand in two rounds (settings 49 to 73, six new controls in two layer files), the look checker looked again, '
              'and a re-baker made again everything that depends on the default settings. Every number below is for the NEW default unless it says "before". The old numbers above in this file are the OLD default and are kept.',
    'settings file': {'entries now': len(settings), 'entries before': len(load('recipe', 'settings_before_look_fixes.json')),
                      'bytes now': os.path.getsize(os.path.join(SL, 'recipe', 'settings.json')), 'bytes before': os.path.getsize(os.path.join(SL, 'recipe', 'settings_before_look_fixes.json')),
                      'controls in recipe/controls.md now': 182, 'controls before': 176,
                      'note': 'the other 182 - 73 = 109 controls keep the layer files starting values; the whole description is about 6 KB (checked for the first 176 only)'},
    'new controls (the only code changes)': round2['code_changes'],
    'settings changes of the tuner (round 1 and 2, with old value, new value, kept or not, why)': round2['settings_changes'],
    'round 1 settings changes (as reported by the tuner)': round1['settings_changes'],
    'default tile now (outputs/default)': {'same-kind': load('outputs', 'default', 'score_same_kind.json'), 'dot-for-dot (transparency only)': load('outputs', 'default', 'score_pixel_for_transparency.json'), 'bake': load('outputs', 'default', 'bake.json')},
    'default tile before the look fixes (outputs/default_before_look_fixes)': {'same-kind': load('outputs', 'default_before_look_fixes', 'score_same_kind.json'), 'dot-for-dot (transparency only)': load('outputs', 'default_before_look_fixes', 'score_pixel_for_transparency.json')},
    'look measures (tuner script and copy of the look checker script): before / after round 1 / now / reference': round2['measures_table_markdown'],
    'look checker second look (round 2)': {'problems status': critic['problems_status'], 'new problems': critic['new_problems'], 'reads as same hand': critic['reads_as_same_hand'], 'overall': critic['overall'], 'should iterate': critic['should_iterate']},
    'ladder (1254 dots), now': load('ladder', 'ladder_scores.json'),
    'ladder before the look fixes': load('ladder', 'ladder_scores_before_look_fixes.json'),
    'variations (1254 dots, colour group), now': {'settings': {k: v for k, v in load('variations', 'variations.json').items() if k != 'before the look fixes'}, 'colour group': load('variations', 'same_kind_colour_scores.json')},
    'variations before the look fixes': {'settings': load('variations', 'variations_before_look_fixes.json'), 'colour group': load('variations', 'same_kind_colour_scores_before_look_fixes.json')},
    'variation test bakes at 512 dots (17 candidates, rounds 1 and 2)': {'round 1': load('variations', 'tuning_512', 'views_round_1.json'), 'round 2': load('variations', 'tuning_512', 'views_round_2.json')},
    'seed spread now (1254 dots, colour group)': load('variations', 'seed_spread', 'seed_spread.json'),
    'seed spread before the look fixes': load('variations', 'seed_spread', 'seed_spread_before_look_fixes.json'),
    'area 2 x 2 (2508 dots) now': {'measures': load('area', 'area_2x2', 'area_measures.json'), 'time': load('area', 'area_2x2', 'time.json')},
    'area 2 x 2 before the look fixes': {'measures': load('area', 'area_2x2', 'area_measures_before_look_fixes.json'), 'time': load('area', 'area_2x2', 'time_before_look_fixes.json')},
    'area 4 x 4': 'not baked again: the numbers in "area 4 x 4 (5016 dots, colour only)" above are of the OLD default',
    'half-tile test (512 dots) now': load('tests', 'half_tile_layers', 'half_tile_results.json'),
    'half-tile test before the look fixes': load('tests', 'half_tile_layers', 'half_tile_results_before_look_fixes.json'),
    'independence of the two changed layers (512 dots, new default settings)': independence,
    'one 512-dot bake against the 1254-dot default shrunk': confirm,
    'node counts after the look fixes (nodes per box)': {k: v['nodes'] for k, v in nodes.items()},
    'folder size at the end': {'bytes': size_bytes, 'megabytes (decimal)': round(size_bytes / 1e6, 1), 'mebibytes (what du -h prints)': round(size_bytes / 2 ** 20, 1), 'limit': '460 MB for this round'},
    'not made again (still the old default)': ['area/area_4x4', 'resolution/whole_recipe (links now point at outputs/default_before_look_fixes)', 'controls_sweeps (builders strips and whole-recipe strips)', 'reuse (brick)', 'links_and_order', 'tests/independence_full (the full table, old default)', 'the tiling and look of the variations beyond the contact sheet'],
    'corrections of earlier reporting (from verify/HONESTY_VERDICT.md), all made in the two guides': [
        'normal score attribution: the 0.671 / 0.705 numbers are for the strength-7 normal (integration/make_normal.py); the harness own fitted normal gave 0.604 / 0.695 for the old default',
        'mixed-method progress figure: 0.615 (harness normal) to 0.705 (strength-7 normal); like for like 0.615 to 0.695, normal group 0.608 to 0.604',
        'ladder: colour and fade adds the most to the colour group; the outline layer is the largest only in the height group, and adding a layer and removing a layer are different questions',
        'round 14 reasoning: the milder pair won on all three seed sets (+0.095, +0.011, +0.005); 0.068 is the spread between different seed sets, not the noise of a same-seed comparison; round 11 had the same feature-size cliff',
        '"identical" for damage_avoid colour pictures: they differ on 0.12 to 0.14 % of dots by up to 8 steps',
        'no sweep strips for the LAYOUT layer: now listed as a gap',
        'description size: the look depends on all controls (182 now), not only the settings file; the audit of all 176 was 6.0 KB',
        'height is 70 % paint brightness: now stated next to the height scores',
        'folder size: stated with units at the end',
        'half-tile explanation: the colour difference of 1 to 2 steps is Blender default dither, found by the point-sampled run of the honesty check',
        'resolution 1254 files are links: now stated, and re-pointed at the old default pictures',
        'minor: 49 entries included 2 build settings; the strips were made at the builders starting values; terms (SSIM, Delta E, Lab, log-normal, 4D noise, Smooth F1) are now explained in section 0'],
}
report['look fixes (round 15)'] = section
report = {'_note about round 15': 'READ THIS FIRST: every number outside the section "look fixes (round 15)" at the end of this file is for the OLD default tile (before the look fixes) and was kept as it was. The new numbers, with the old ones beside them, are in that last section.', **report}
with open(report_path, 'w') as handle:
    json.dump(report, handle, indent=1)
print('final_report.json now has', len(report), 'entries; new section has', len(section))
