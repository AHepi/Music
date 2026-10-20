# What this does (plain words): writes the one-page controls table of the OUTLINE AND SHADOW layer (every control: setting name, what it does,
# lowest and highest value, default) as a markdown table, straight from the CONTROLS list in layers/outline_and_shadow.py, so the table can never
# disagree with the code. Run it inside Blender (the layer file needs Blender's Python):
#   blender -b --disable-autoexec --python make_controls_table.py
# Output: outline_controls.md next to this file.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'layers'))
import layer_interface as li  # noqa: E402
import outline_and_shadow as layer  # noqa: E402

rows = li.controls_table_rows(layer.LAYER_KEY, layer.CONTROLS, with_common=True, default_seed=layer.DEFAULT_SEED)
lines = ['# OUTLINE AND SHADOW - the controls (generated from layers/outline_and_shadow.py; every control is also a setting named `outline_and_shadow.<name>`)', '',
         'Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.0064 = 8 dots). The "in dots" column shows the same size at 1254 dots per tile.', '',
         '| setting | socket in Blender | what it does | lowest | highest | default | default in dots (1254 per tile) |', '|---|---|---|---|---|---|---|']
for setting, label, default, low, high, text, how in rows:
    is_size = isinstance(default, float) and ('width' in setting or 'offset' in setting or 'drips' in setting or 'reach' in setting) and 'darkness' not in setting and 'scale' not in setting and 'roughness' not in setting and 'amount' not in setting
    dots = f'{default * 1254:.1f}' if is_size else ''
    lines.append(f'| `{setting}` | {label} | {text} | {low if low is not None else ""} | {high if high is not None else ""} | {default} | {dots} |')
with open(os.path.join(HERE, 'outline_controls.md'), 'w') as handle:
    handle.write('\n'.join(lines) + '\n')
print('wrote outline_controls.md with', len(rows), 'controls')
