# What this file does (plain words): makes every "what does this setting do" strip of the MOSS layer (one picture per control group), by calling strip.py once per strip.
# The strips are written to ../controls_sweeps/moss/ (one level up from the work folder). Run:  python3 -I run_all_sweeps.py [SIZE] [only-this-strip-name ...]
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.abspath(os.path.join(here, '..'))
out_dir = os.path.abspath(os.path.join(work, '..', 'controls_sweeps', 'moss'))
size = sys.argv[1] if len(sys.argv) > 1 else '512'
only = sys.argv[2:]

def v(setting, value, label=None):
    return (label or f'{setting.split(".")[-1].replace("_", " ")} {value}', {setting: value})

def variants(*items):
    d = {}
    for label, settings in items:
        d[label] = settings
    return d

def many(setting, values, name=None):
    name = name or setting.split('.')[-1].replace('_', ' ')
    return variants(*[(f'{name} {x}', {setting: x}) for x in values])

STRIPS = [
    ('01_coverage', 'Coverage: how much of the slate is moss (the share of slate dots covered is printed)', many('moss.coverage', [0.05, 0.1, 0.2, 0.35, 0.6]), ['--share'], 5),
    ('02_patchiness_and_slate_variation', 'Patchiness (top row) and Slate Variation (bottom row)',
        variants(*[(f'patchiness {x}', {'moss.patchiness': x, 'moss.coverage': 0.3}) for x in (0.0, 0.5, 1.0)], *[(f'slate variation {x}', {'moss.slate_variation': x, 'moss.coverage': 0.3, 'moss.patchiness': 0.0}) for x in (0.0, 0.5, 1.0)]), ['--share'], 3),
    ('03_patch_size', 'Patch Size: the size of the big mossy and clean areas (tile units; Patchiness 1)', variants(*[(f'patch size {x}', {'moss.patch_size': x, 'moss.patchiness': 1.0, 'moss.slate_variation': 0.0, 'moss.coverage': 0.3}) for x in (0.15, 0.25, 0.4, 0.7, 1.0)]), [], 5),
    ('04_drip_length', 'Drip Length: how far a drip runs down from the upper edge (tile units)', variants(*[(f'drip length {x}', {'moss.drip_length': x, 'moss.clump_strength': 0.6, 'moss.coverage': 0.3}) for x in (0.02, 0.05, 0.1, 0.16, 0.25)]), [], 5),
    ('05_drip_width_and_stretch', 'Drip Width (top row) and Drip Stretch (bottom row)',
        variants(*[(f'drip width {x}', {'moss.drip_width': x, 'moss.clump_strength': 0.6, 'moss.coverage': 0.3}) for x in (0.02, 0.05, 0.1)], *[(f'drip stretch {x}', {'moss.drip_stretch': x, 'moss.coverage': 0.3}) for x in (1.0, 1.8, 3.5)]), [], 3),
    ('06_cluster_size', 'Cluster Size: the width of a moss clump (tile units)', variants(*[(f'cluster size {x}', {'moss.cluster_size': x, 'moss.coverage': 0.3}) for x in (0.02, 0.035, 0.05, 0.08, 0.12)]), [], 5),
    ('07_clump_strength', 'Clump Strength: 0 = only the rules (a band under the upper edge), 3 = free blobs', variants(*[(f'clump strength {x}', {'moss.clump_strength': x, 'moss.coverage': 0.3}) for x in (0.0, 0.7, 1.5, 2.2, 3.0)]), [], 5),
    ('08_where_it_gathers', 'Where it gathers: all preferences 0, then ONE of them at 1.2 (Coverage 0.45, Clump Strength 0.8)',
        variants(('all preferences 0', {}), ('drip preference 1.2', {'moss.drip_preference': 1.2}), ('joint preference 1.2', {'moss.joint_preference': 1.2}),
                 ('lower preference 1.2', {'moss.lower_preference': 1.2}), ('damp preference 1.2', {'moss.damp_preference': 1.2})),
        ['--base', json.dumps({'moss.coverage': 0.45, 'moss.clump_strength': 0.8, 'moss.drip_preference': 0.0, 'moss.joint_preference': 0.0, 'moss.lower_preference': 0.0, 'moss.damp_preference': 0.0, 'moss.patchiness': 0.0, 'moss.slate_variation': 0.0, 'moss.lichen_amount': 0.0})], 5),
    ('09_flow_wobble_and_fringe', 'Flow Wobble (top row) and Fringe Amount (bottom row)',
        variants(*[(f'flow wobble {x}', {'moss.flow_wobble': x, 'moss.coverage': 0.3}) for x in (0.0, 0.012, 0.04)], *[(f'fringe amount {x}', {'moss.fringe_amount': x, 'moss.coverage': 0.3}) for x in (0.0, 0.25, 1.0)]), [], 3),
    ('10_edge_raggedness', 'Edge Raggedness: smooth outline to very ragged', variants(*[(f'edge raggedness {x}', {'moss.edge_raggedness': x, 'moss.coverage': 0.3}) for x in (0.0, 0.3, 0.6, 1.0, 1.5)]), [], 5),
    ('11_tone_centre', 'Moss Tone Centre: which olive tone is typical (0 = darkest, 1 = lightest)', variants(*[(f'tone centre {x}', {'moss.tone_centre': x, 'moss.coverage': 0.3}) for x in (0.0, 0.3, 0.6, 0.85, 1.0)]), [], 5),
    ('12_tone_spread_rim_and_shade', 'Moss Tone Spread (top row), Rim Lightening and Top Shading (bottom row, 0 and 1)',
        variants(*[(f'tone spread {x}', {'moss.tone_spread': x, 'moss.coverage': 0.3}) for x in (0.0, 0.4, 1.0)], ('rim lightening 0', {'moss.rim_lightening': 0.0, 'moss.coverage': 0.3}), ('rim lightening 1', {'moss.rim_lightening': 1.0, 'moss.coverage': 0.3}),
                 ('top shading 1', {'moss.top_shading': 1.0, 'moss.coverage': 0.3})), [], 3),
    ('13_lichen_amount', 'Lichen Amount (Coverage 0.2): the discs and rings', variants(*[(f'lichen amount {x}', {'moss.lichen_amount': x}) for x in (0.0, 0.2, 0.5, 0.8, 1.0)]), [], 5),
    ('14_lichen_size_and_clustering', 'Lichen Size (top row) and Lichen Clustering (bottom row), Lichen Amount 0.8',
        variants(*[(f'lichen size {x}', {'moss.lichen_size': x, 'moss.lichen_amount': 0.8}) for x in (0.002, 0.0042, 0.008)], *[(f'lichen clustering {x}', {'moss.lichen_clustering': x, 'moss.lichen_amount': 0.8}) for x in (0.0, 0.5, 1.0)]), [], 3),
    ('15_seed', 'Seed: the same settings, five different seeds (same slates, new moss)', variants(*[(f'seed {x}', {'moss.seed': x}) for x in (31, 32, 33, 34, 35)]), [], 5),
    ('16_amount', 'Amount: 0 = layer off, then growing (Amount scales Coverage and Lichen Amount)', variants(*[(f'amount {x}', {'moss.amount': x, 'moss.coverage': 0.4}) for x in (0.0, 0.25, 0.5, 0.75, 1.0)]), [], 5),
    ('17_damage_avoid', 'Damage Avoid: moss painted OVER damage, heavy flaking and lots of moss low on the slates; Damage Avoid 0, 0.5, 1 keeps the moss off the flakes',
        variants(*[(f'damage avoid {x}', {'moss.damage_avoid': x, 'moss.damage_attract': 0.0, 'order': 'moss_on_top'}) for x in (0.0, 0.5, 1.0)]),
        ['--paint', '--damage', '--base', json.dumps({'damage.chip_amount': 1.0, 'damage.chip_depth': 0.04, 'moss.coverage': 0.55, 'moss.lower_preference': 1.5, 'moss.drip_preference': 0.2, 'moss.patchiness': 0.0, 'moss.slate_variation': 0.0, 'moss.lichen_amount': 0.0})], 3),
    ('17b_damage_attract', 'Damage Attract: moss painted OVER damage, little moss (Coverage 0.08); Damage Attract 0, 0.5, 1 lets moss grow on the flakes',
        variants(*[(f'damage attract {x}', {'moss.damage_attract': x, 'moss.damage_avoid': 0.0, 'order': 'moss_on_top'}) for x in (0.0, 0.5, 1.0)]),
        ['--paint', '--damage', '--base', json.dumps({'damage.chip_amount': 1.0, 'damage.chip_depth': 0.04, 'moss.coverage': 0.08, 'moss.patchiness': 0.0, 'moss.slate_variation': 0.0, 'moss.lichen_amount': 0.0})], 3),
    ('18_height', 'Raise: the moss height (0.5 grey = no change, moss shown 5 times as strong), Raise 0, 0.5, 1, 2', variants(*[(f'raise {x}', {'moss.raise': x, 'view': 'height', 'moss.coverage': 0.3}) for x in (0.0, 0.5, 1.0, 2.0)]), [], 4),
    ('19_roughness', 'Roughness Gain: how much rougher moss is (0.5 grey = no change), gain 0, 1, 3', variants(*[(f'roughness gain {x}', {'moss.roughness_gain': x, 'view': 'roughness', 'moss.coverage': 0.3}) for x in (0.0, 1.0, 3.0)]), [], 3),
]
WHOLE = ('01_coverage', '02_patchiness_and_slate_variation', '03_patch_size', '15_seed', '16_amount')       # these show the whole tile; the others are zoomed on a mossy part
ZOOM = ['--crop', '0.4', '0.38', '1.0', '0.78', '--cell', '460']
os.makedirs(out_dir, exist_ok=True)
for name, title, vs, extra, columns in STRIPS:
    if only and name not in only:
        continue
    bake_size = size if name in WHOLE else str(int(int(size) * 1.5))
    cmd = ['python3', '-I', os.path.join(here, 'strip.py'), os.path.join(out_dir, name + '.png'), title, bake_size, json.dumps(vs), '--columns', str(columns)] + extra + ([] if name in WHOLE else ZOOM)
    print('making', name, flush=True)
    subprocess.run(cmd, check=False)
