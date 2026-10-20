# Verifier copy of recipe/make_controls_table.py (layers path changed only), to regenerate controls.md here and diff it with recipe/controls.md.
# What this does (plain words): writes the one-page "controls" table (controls.md): every setting of every layer, what it does, its
# range and its default, read straight from the layer files (so the table can never disagree with the code). Run it again whenever a
# layer file changes its CONTROLS.
# Use:  blender -b --python make_controls_table.py     (writes controls.md next to this file)
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'layers')))
import layer_interface as li  # noqa: E402
import layout, colour_and_fade, damage, moss, outline_and_shadow, combine  # noqa: E402

SECTIONS = [('recipe', 'THE RECIPE ITSELF', None, 0), ('layout', 'LAYOUT', layout, None), ('colour_and_fade', 'COLOUR AND FADE', colour_and_fade, 11),
            ('damage', 'DAMAGE', damage, 21), ('moss', 'MOSS', moss, 31), ('outline_and_shadow', 'OUTLINE AND SHADOW', outline_and_shadow, 41),
            ('combine', 'COMBINE', combine, None)]
RECIPE_ROWS = [
    ('recipe.tiles_across', '(build)', '1', '1', '64', 'how many base tiles fit across the picture: 1 = one tile that repeats exactly; 2 = a 2 x 2 area of NEW content (bake 2 x 1254 dots). Whole numbers only.'),
    ('recipe.stack_order', '(build)', 'colour_and_fade,moss,damage,outline_and_shadow', '', '', 'which layer paints over which, bottom first (heights and roughness are plain sums, so the order only matters for colour)'),
]


def fmt(value):
    if isinstance(value, float):
        return f'{value:g}'
    return str(value)


SETTINGS = json.load(open(os.path.join(HERE, 'settings.json')))
lines = ['# Slate in layers - the controls (one page)', '',
         'Every setting is a flat name `layer.control` in `recipe/settings.json` (or passed as a parameter). Order of strength: the starting value written in the',
         'layer\'s own file < `settings.json` < the parameters given to the bake. **"default" below is the value the default tile uses** (the starting value with the',
         'tuned value from `settings.json` laid over it); where the tuned value differs from the layer file\'s starting value, the starting value is shown in brackets.',
         '"socket" controls are also knobs on the layer\'s box in the Shader editor; "build" controls change how many nodes a box has, so they are read when the recipe',
         'is built. Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile, 0.0064 = 8 dots). Every layer also has **seed** (its own random numbers)',
         'and **amount** (0 switches the layer off). This file is written by `recipe/make_controls_table.py` from the layer files and settings.json, so it can never',
         'disagree with the code.', '']
count = 0
for key, title, module, seed in SECTIONS:
    lines += [f'## {title}', '', '| setting | socket in Blender | default (starting value in the layer file, if different) | low | high | what it does |', '|---|---|---|---|---|---|']
    if key == 'recipe':
        rows = RECIPE_ROWS
    else:
        rows = [(r[0], r[1] if r[6] == 'socket' else '(build)', fmt(r[2]), fmt(r[3]) if r[3] is not None else '', fmt(r[4]) if r[4] is not None else '', r[5])
                for r in li.controls_table_rows(key, module.CONTROLS, with_common=(seed is not None and key not in ('layout', 'combine')), default_seed=seed or 0)]
    for r in rows:
        name, socket, start, low, high, text = r
        value = SETTINGS.get(name)
        shown = start if value is None or fmt(value) == start else f'**{fmt(value)}** ({start})'
        count += 1
        lines.append(f'| `{name}` | {socket} | {shown} | {low} | {high} | {text} |')
    if module is not None and getattr(module, 'DECLARED_LINKS', None):
        lines += ['', 'Declared links (inputs this layer reads from another layer): ' + '; '.join(f'`{l[0]}` from {l[4][0]}.{l[4][1]} ({l[3]})' for l in module.DECLARED_LINKS)]
    lines.append('')
lines.append(f'Total: {count} settings. {len(SETTINGS)} of them are written in `settings.json` (the tuned default tile); the rest keep the layer files\' starting values.')
with open(os.path.join(HERE, 'controls.md'), 'w') as handle:
    handle.write('\n'.join(lines) + '\n')
print('wrote controls.md', count, 'settings')
