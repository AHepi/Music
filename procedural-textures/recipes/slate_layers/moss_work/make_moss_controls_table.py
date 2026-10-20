# What this does (plain words): writes the one-page controls table of the MOSS layer (moss_controls.md): every setting, what it does, its range and its default,
# read straight from layers/moss.py (so the table can never disagree with the code). Run it again whenever the CONTROLS of moss.py change.
# Use:  blender -b --python make_moss_controls_table.py     (writes moss_controls.md next to this file)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'layers')))
import layer_interface as li  # noqa: E402
import moss  # noqa: E402

GROUPS = [
    ('How much, and where in the big picture', ['coverage', 'patchiness', 'patch_size', 'slate_variation', 'seed', 'amount']),
    ('Where it likes to grow (each is a preference; 0 = does not care)', ['drip_preference', 'drip_length', 'drip_width', 'joint_preference', 'lower_preference', 'damp_preference', 'damage_avoid', 'damage_attract']),
    ('The shape of the clumps', ['cluster_size', 'clump_strength', 'drip_stretch', 'flow_wobble', 'edge_raggedness', 'fringe_amount', 'fringe_width']),
    ('The olive colours and how they are used', ['tone_1', 'tone_2', 'tone_3', 'tone_4', 'tone_5', 'tone_centre', 'tone_spread', 'rim_lightening', 'top_shading', 'tone_patch_size']),
    ('Lichen (small round discs and rings)', ['lichen_amount', 'lichen_clustering', 'lichen_size', 'lichen_colour', 'lichen_light', 'lichen_dark']),
    ('Relief and roughness', ['raise', 'roughness_gain']),
]


def fmt(value):
    if isinstance(value, float):
        return f'{value:g}'
    return str(value)


rows = {r[0].split('.', 1)[1]: r for r in li.controls_table_rows('moss', moss.CONTROLS, with_common=True, default_seed=moss.DEFAULT_SEED)}
lines = ['# MOSS layer - the controls (one page)', '',
         'Every control is a setting named `moss.<name>` (in `recipe/settings.json` or passed to the bake, for example `--params \'{"moss.coverage": 0.5}\'`) and also a knob',
         'on the MOSS box in the Shader editor (its "socket" name is in the second column). Order of strength: the default below (written in `layers/moss.py`)',
         '< settings.json < the parameters given to the bake. Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile, 0.0064 = 8 dots).',
         '`moss.amount` is the layer\'s off-switch and an overall dimmer: 0 = nothing at all (mask, height and roughness exactly 0); between 0 and 1 it scales **coverage and lichen amount**',
         '(so the paint stays crisp, only the amount of moss changes). This file is written by `moss_work/make_moss_controls_table.py` from `layers/moss.py`.', '']
for title, keys in GROUPS:
    lines += [f'## {title}', '', '| setting | socket in Blender | default | range | what it does |', '|---|---|---|---|---|']
    for key in keys:
        r = rows.pop(key)
        low, high = ('', '') if r[3] is None else (fmt(r[3]), fmt(r[4]))
        rng = f'{low} to {high}' if low != '' else '(a colour)'
        lines.append(f'| `{r[0]}` | {r[1]} | {fmt(r[2])} | {rng} | {r[5]} |')
    lines.append('')
assert not rows, f'controls not in any group: {list(rows)}'
lines += ['## The declared link (an input MOSS reads from another layer)', '',
          '| socket | comes from | what it means |', '|---|---|---|']
for link in moss.DECLARED_LINKS:
    lines.append(f'| `{link[0]}` | {link[4][0]} layer, output `{link[4][1]}` | {link[3]} |')
lines.append('')
with open(os.path.join(HERE, 'moss_controls.md'), 'w') as handle:
    handle.write('\n'.join(lines))
print('wrote moss_controls.md with', sum(len(k) for _, k in GROUPS), 'controls')
