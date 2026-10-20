# What this does (plain words): writes the controls table of the DAMAGE layer only (every setting, its default, its range, what it does and which
# sweep strip shows it), read straight from layers/damage.py so the table can never disagree with the code. The shared table of ALL layers is
# recipe/controls.md (made by recipe/make_controls_table.py); this one is kept next to the damage work so it can be read on its own.
# Use:  blender -b --python make_damage_controls_table.py     (writes damage_controls.md next to this file)
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'layers')))
import layer_interface as li  # noqa: E402
import damage  # noqa: E402

STRIP_OF = {
    'chip_amount': 'strip_1', 'chip_depth': 'strip_1', 'chip_frequency': 'strip_1', 'chip_breakup': 'strip_1', 'chip_clustering': 'strip_1',
    'crack_amount': 'strip_2', 'crack_length': 'strip_2', 'crack_width': 'strip_2', 'crack_across_share': 'strip_2', 'scratch_amount': 'strip_2', 'pit_amount': 'strip_2',
    'corner_break_amount': 'strip_3', 'notch_amount': 'strip_3', 'amount': 'strip_3', 'break_colour': 'strip_3', 'break_colour_light': 'strip_3', 'break_colour_dark': 'strip_3',
}
STRIP_OF.update({'side_share': 'strip_4', 'corner_gain': 'strip_4', 'slate_variation': 'strip_4', 'pit_size': 'strip_4'})
STRIP_FILES = {'strip_4': 'strip_4_where_and_how_big.png', 'strip_1': 'strip_1_edge_flakes.png', 'strip_2': 'strip_2_cracks_scratches_pits.png', 'strip_3': 'strip_3_corners_notches_colours_amount.png'}


def fmt(value):
    return f'{value:g}' if isinstance(value, float) else str(value)


rows = li.controls_table_rows('damage', damage.CONTROLS, with_common=True, default_seed=damage.DEFAULT_SEED)
lines = ['# DAMAGE - the controls (one page)', '',
         'Each control is a setting named `damage.<control>` (in `recipe/settings.json` or passed as a parameter) and a knob on the DAMAGE box in the Shader editor.',
         'Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.0064 = 8 dots). "build" controls change how many nodes the box has, so they are read',
         'when the recipe is built. The last column names the picture strip (in `controls_sweeps/damage/`) that shows what the control does. Written by',
         '`damage_work/make_damage_controls_table.py` from `layers/damage.py`.', '',
         '| setting | socket in Blender | default | low | high | what it does | strip |', '|---|---|---|---|---|---|---|']
for setting, label, default, low, high, text, kind in rows:
    key = setting.split('.', 1)[1]
    strip = STRIP_FILES.get(STRIP_OF.get(key, ''), '')
    lines.append(f"| `{setting}` | {label if kind == 'socket' else '(build)'} | {fmt(default)} | {fmt(low) if low is not None else ''} | {fmt(high) if high is not None else ''} | {text} | {strip} |")
lines += ['', 'Declared links: DAMAGE reads no other layer. MOSS reads DAMAGE\'s `Mask` through its declared link `Damage Mask` (moss may keep away from fresh damage or gather beside it).', '']
open(os.path.join(HERE, 'damage_controls.md'), 'w').write('\n'.join(lines))
print('wrote damage_controls.md', len(rows), 'controls')
