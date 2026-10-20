# What this does: checks the palette tools. (1) A Color Ramp (Constant) filled with hex colours really gives back the same hex colours in the baked
# picture (the sRGB <-> linear trap). (2) What the Color Ramp offers in 5.2 (interpolation types, colour modes, hue interpolation) with pictures of smooth
# ramps between two colours. (3) Hue/Saturation/Value jitter per cell: how much colour spread a given setting adds (measured in the baked picture).
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
BASE = os.path.join(hp.OUT, 'pictures', 'c11_palette'); os.makedirs(BASE, exist_ok=True)
res = {}
hp.SAMPLES = 1
# 1 round trip
def bands():
    tree, w = hp.new_group('palette bands', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeSeparateXYZ', 'uv', x=0); w.link('in', 'Vector', 'uv', 'Vector')
    hp.palette_ramp(w, 'palette', [(h, 100.0 / 8) for h, _ in hp.BRICK_PALETTE], x=1, by_lightness=False)     # equal shares, palette order kept
    w.link('uv', 'X', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour'); return tree
path = os.path.join(BASE, 'bands.png')
hp.photograph_group(bands, 'Colour', path, 256)
a = hp.load(path)       # encoded values 0..1 straight from the file
errors = []
for i, (hex_text, _) in enumerate(hp.BRICK_PALETTE):
    x = int((i + 0.5) / 8 * 256)
    got = np.round(a[128, x] * 255).astype(int)
    want = np.array([int(hex_text[j:j + 2], 16) for j in (1, 3, 5)])
    errors.append(int(np.abs(got - want).max()))
res['hex_round_trip_max_error_per_colour_out_of_255'] = errors
print('round trip errors', errors)
# the trap: put the hex numbers into the ramp WITHOUT converting to linear
def bands_wrong():
    tree, w = hp.new_group('palette bands wrong', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeSeparateXYZ', 'uv', x=0); w.link('in', 'Vector', 'uv', 'Vector')
    node = w.add('ShaderNodeValToRGB', 'palette', x=1); ramp = node.color_ramp; ramp.interpolation = 'CONSTANT'
    while len(ramp.elements) < 8: ramp.elements.new(0.5)
    for i, (hex_text, _) in enumerate(hp.BRICK_PALETTE):
        ramp.elements[i].position = i / 8; ramp.elements[i].color = (*[int(hex_text[j:j + 2], 16) / 255 for j in (1, 3, 5)], 1.0)     # NOT converted
    w.link('uv', 'X', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour'); return tree
path2 = os.path.join(BASE, 'bands_wrong.png'); hp.photograph_group(bands_wrong, 'Colour', path2, 256)
b = hp.load(path2)
wrong = []
for i, (hex_text, _) in enumerate(hp.BRICK_PALETTE):
    x = int((i + 0.5) / 8 * 256); got = np.round(b[128, x] * 255).astype(int); want = np.array([int(hex_text[j:j + 2], 16) for j in (1, 3, 5)]); wrong.append(int(np.abs(got - want).max()))
res['hex_typed_in_without_conversion_max_error_per_colour'] = wrong
print('unconverted errors', wrong)
# 2 ramp options
tree = bpy.data.node_groups.new('probe', 'ShaderNodeTree'); node = tree.nodes.new('ShaderNodeValToRGB'); ramp = node.color_ramp
res['color_ramp_interpolation_options'] = [i.identifier for i in ramp.bl_rna.properties['interpolation'].enum_items]
res['color_ramp_color_mode_options'] = [i.identifier for i in ramp.bl_rna.properties['color_mode'].enum_items]
res['color_ramp_hue_interpolation_options'] = [i.identifier for i in ramp.bl_rna.properties['hue_interpolation'].enum_items]
print(res['color_ramp_interpolation_options'], res['color_ramp_color_mode_options'], res['color_ramp_hue_interpolation_options'])
hp.SAMPLES = 4
def ramp2(interp, mode, hue, name):
    def b():
        tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
        w.add('ShaderNodeSeparateXYZ', 'uv', x=0); w.link('in', 'Vector', 'uv', 'Vector')
        node = w.add('ShaderNodeValToRGB', 'ramp', x=1); r = node.color_ramp; r.interpolation = interp; r.color_mode = mode; r.hue_interpolation = hue
        r.elements[0].color = (*hp.srgb_hex_to_linear('#3a4045'), 1); r.elements[1].color = (*hp.srgb_hex_to_linear('#a34d2d'), 1)
        w.link('uv', 'X', 'ramp', 'Fac'); w.link('ramp', 'Color', 'out', 'Colour'); return tree
    return b
variants = [('LINEAR', 'RGB', 'NEAR'), ('LINEAR', 'HSV', 'NEAR'), ('LINEAR', 'HSV', 'FAR'), ('LINEAR', 'HSL', 'NEAR'), ('EASE', 'RGB', 'NEAR'), ('CONSTANT', 'RGB', 'NEAR')]
arrays = hp.sweep(lambda i: ramp2(*variants[i], name=f'r{i}')(), list(range(len(variants))), os.path.join(BASE, 'ramp_modes'), labels=[f'{a} {b} {c}' for a, b, c in variants], size=200, title='Color Ramp: slate blue-grey -> brick orange, interpolation / colour mode / hue path', cell=220)
# 3 hue / value jitter strength measured
def jitter(hue, val):
    tree, w = hp.new_group(f'jit_{hue}_{val}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=0, Scale=10.0); w.link('in', 'Vector', 'cells', 'Vector')
    hp.cell_random(w, 'rh', 'cells', 'Color', 11.0, x=1, y=-1); hp.cell_random(w, 'rv', 'cells', 'Color', 23.0, x=1, y=-2)
    w.math('hue', 'MULTIPLY_ADD', None, hue, 0.5 - hue / 2, x=2, y=-1); w.link('rh', 'Value', 'hue', 0)
    w.math('val', 'MULTIPLY_ADD', None, val, 1.0 - val / 2, x=2, y=-2); w.link('rv', 'Value', 'val', 0)
    w.add('ShaderNodeHueSaturation', 'hsv', x=3); w.nodes['hsv'].inputs['Color'].default_value = (*hp.srgb_hex_to_linear('#8b442d'), 1)
    w.link('hue', 0, 'hsv', 'Hue'); w.link('val', 0, 'hsv', 'Value'); w.link('hsv', 'Color', 'out', 'Colour'); return tree
rows = []
for hue, val in ((0.0, 0.0), (0.02, 0.0), (0.06, 0.0), (0.0, 0.2), (0.0, 0.5), (0.04, 0.35)):
    p = os.path.join(BASE, f'jitter_{hue}_{val}.png')
    hp.photograph_group(lambda: jitter(hue, val), 'Colour', p, 256)
    img = hp.load(p)
    import colorsys
    flat = img.reshape(-1, 3)
    hsv = np.array([colorsys.rgb_to_hsv(*c) for c in flat[::53]])
    rows.append({'hue_setting': hue, 'value_setting': val, 'hue_std_degrees': float(np.degrees(np.std(hsv[:, 0]) * 2 * np.pi)) , 'value_range_p5_p95': [float(np.percentile(hsv[:, 2], 5)), float(np.percentile(hsv[:, 2], 95))], 'lightness_std_encoded': float(img.mean(axis=2).std())})
res['jitter_measured'] = rows
for r in rows: print(r)
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c11_palette_checks.json'), 'w'), indent=1)
