# What this does (plain words): makes the NEW "what does this setting do?" strips for the two tool guides
# ("06 Guide - pattern makers.md" and "06 Guide - shapers.md") for the settings that had no strip yet, and MEASURES the numbers
# that the guides quote about them (written to numbers.json next to this file). Each strip is a row of small 256-dot squares,
# each the same little node chain with ONE setting changed. The squares go into work/<strip name>/ and are joined into one
# labelled picture afterwards with lib/make_strip.py (see run_strips.sh).
# Strips made here: Wave Phase Offset; Noise Normalize on/off for three fractal types; Radial Tiling as faceted rivet heads;
# Math Compare line width; Clamp (Min Max and Range); Mix Factor; Mix blend modes for a stain; Separate / Combine; Color Ramp
# stop position against the share of the picture it covers (plus the hex-colour trap). Also numbers only: Float Curve "extend".
# Run (inside Blender 5.2.2):
#   blender -b --disable-autoexec -t 2 --python make_tool_guide_strips.py
import json
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'lib'))
sys.path.insert(0, LIB)
import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402
import sweep_tools as st  # noqa: E402

WORK = os.path.join(HERE, 'work')
SIZE = 256
NUMBERS = {}


# ------------------------------------------------------------------------------------------------ small helpers
def make_tree(name, body):
    """A node group with input 'Vector' (tile coordinate, u and v from 0 to 1) and outputs 'Colour' and 'Height'; body(w) fills it."""
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    body(w)
    return tree


def sweep(name, bodies, labels, channel):
    """One small square per body; bodies[i](w) builds square i."""
    folder = os.path.join(WORK, name)

    def build(index):
        return make_tree(f'{name}_{index}', bodies[index])
    st.render_sweep(build, list(range(len(bodies))), folder, channel=channel, size=SIZE, labels=labels)
    return folder


def measure(body, channel='Height', size=SIZE, samples=1):
    """Render one output as exact floating-point numbers (rows top to bottom). Colour comes back linear (h, w, 3)."""
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = samples
    group = make_tree('measure', body)
    material = bh.show_channel_material(group, channel)
    tile.data.materials.append(material)
    scene.view_settings.view_transform = 'Raw'
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.color_mode = 'RGB'
    path = os.path.join(WORK, '_measure.exr')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(image)
    return array[..., 0].copy() if channel != 'Colour' else array.copy()


def to_srgb_steps(linear):
    """Linear colour numbers -> ordinary screen numbers 0..255 (what a picture file and a colour picker show)."""
    linear = np.clip(linear, 0.0, 1.0)
    srgb = np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055)
    return srgb * 255.0


def summary(array):
    return {'min': round(float(array.min()), 4), 'max': round(float(array.max()), 4), 'mean': round(float(array.mean()), 4),
            'share_below_0': round(float((array < 0).mean()), 4), 'share_above_1': round(float((array > 1).mean()), 4)}


def noise(w, name, scale=5.0, detail=4.0, roughness=0.5, noise_type='FBM', normalize=True, dimensions='3D', vector=('in', 'Vector'), **extra):
    w.add('ShaderNodeTexNoise', name, noise_dimensions=dimensions, noise_type=noise_type, normalize=normalize,
          Scale=scale, Detail=detail, Roughness=roughness, **extra)
    w.link(vector[0], vector[1], name, 'Vector')
    return name


def stretch(w, name, source, socket=0, low=0.3, high=0.7, to_low=0.0, to_high=1.0, clamp=True):
    w.add('ShaderNodeMapRange', name, clamp=clamp, From__Min=low, From__Max=high, To__Min=to_low, To__Max=to_high)
    w.link(source, socket, name, 'Value')
    return name


def colour_ramp(w, name, stops, interpolation='CONSTANT'):
    """stops = [(position, linear colour (r, g, b, a)), ...]"""
    node = w.add('ShaderNodeValToRGB', name)
    ramp = node.color_ramp
    ramp.interpolation = interpolation
    ramp.elements[0].position = stops[0][0]
    ramp.elements[0].color = stops[0][1]
    ramp.elements[1].position = stops[1][0]
    ramp.elements[1].color = stops[1][1]
    for position, colour in stops[2:]:
        element = ramp.elements.new(position)
        element.color = colour
    return name


# ------------------------------------------------------------------------------------------------ A. Wave Phase Offset
def wave_body(phase, distortion=0.0):
    def body(w):
        w.add('ShaderNodeTexWave', 'wave', wave_type='BANDS', bands_direction='X', wave_profile='SIN',
              Scale=5 * math.pi / 10, Distortion=distortion, Phase__Offset=phase)
        w.link('in', 'Vector', 'wave', 'Vector')
        w.link('wave', 1, 'out', 'Height')
    return body


phases = [0.0, math.pi / 2, math.pi, 3 * math.pi / 2, 2 * math.pi]
sweep('wave_phase_offset', [wave_body(p) for p in phases],
      ['phase 0', 'phase 1.571 (1/4 turn)', 'phase 3.142 (1/2 turn)', 'phase 4.712 (3/4 turn)', 'phase 6.283 (full turn)'], 'Height')
p0 = measure(wave_body(0.0))
pq = measure(wave_body(math.pi / 2))
ph = measure(wave_body(math.pi))
pf = measure(wave_body(2 * math.pi))
row0, rowq = p0.mean(axis=0), pq.mean(axis=0)
errors = [float(np.abs(np.roll(row0, s) - rowq).mean()) for s in range(-SIZE // 2, SIZE // 2)]
best_shift = int(np.argmin(errors)) - SIZE // 2
NUMBERS['wave_phase_offset'] = {
    'setup': 'Wave Bands, direction X, Sine, Scale 5 x pi/10 = 1.5708 (5 whole bands across the tile), Distortion 0, 256 dots',
    'mean_difference_phase_0_vs_full_turn': round(float(np.abs(p0 - pf).mean()), 5),
    'mean_difference_half_turn_vs_inverted_phase_0': round(float(np.abs(ph - (1.0 - p0)).mean()), 5),
    'shift_in_dots_for_quarter_turn (positive = bands moved right)': best_shift,
    'band_period_in_dots': SIZE / 5.0,
}
# does Phase Offset also move bands that Distortion has bent?
d0 = measure(wave_body(0.0, 3.0))
dq = measure(wave_body(math.pi / 2, 3.0))
NUMBERS['wave_phase_offset']['with_distortion_3_mean_difference_quarter_turn'] = round(float(np.abs(d0 - dq).mean()), 4)


# ------------------------------------------------------------------------------------------------ B. Noise Normalize trap
def normalize_body(noise_type, normalize):
    def body(w):
        noise(w, 'n', scale=5.0, detail=2.0, noise_type=noise_type, normalize=normalize)
        w.link('n', 0, 'out', 'Height')
    return body


normal_cases = [('FBM', True), ('FBM', False), ('RIDGED_MULTIFRACTAL', True), ('RIDGED_MULTIFRACTAL', False),
                ('MULTIFRACTAL', True), ('MULTIFRACTAL', False)]
sweep('noise_normalize', [normalize_body(t, n) for t, n in normal_cases],
      ['fBM, Normalize on', 'fBM, Normalize off', 'Ridged, Normalize on', 'Ridged, Normalize off', 'Multifractal, on', 'Multifractal, off'],
      'Height')
NUMBERS['noise_normalize'] = {'setup': 'Noise 3D, Scale 5, Detail 2, Roughness 0.5, Lacunarity 2, Offset 0 (default); numbers are the true values'}
for t, n in normal_cases:
    NUMBERS['noise_normalize'][f'{t} normalize {"on" if n else "off"}'] = summary(measure(normalize_body(t, n)))


# ------------------------------------------------------------------------------------------------ C. Radial Tiling as faceted rivet heads
def rivet_body(sides, roundness=0.0, show='shade', light=0.785):
    def body(w):
        w.vector_math('centred', 'SUBTRACT')
        w.link('in', 'Vector', 'centred', 0)
        w.nodes['centred'].inputs[1].default_value = (0.5, 0.5, 0.0)
        w.add('ShaderNodeRadialTiling', 'radial', Sides=sides, Roundness=roundness)
        w.link('centred', 0, 'radial', 'Vector')
        w.math('turned', 'SUBTRACT', None, light)                       # light direction (0.785 = 45 degrees, the upper right of the disc)
        w.link('radial', 'Segment Rotation', 'turned', 0)
        w.math('facing', 'COSINE')
        w.link('turned', 0, 'facing', 0)
        stretch(w, 'shade', 'facing', 0, -1.0, 1.0, 0.25, 0.9)
        w.vector_math('distance', 'LENGTH')
        w.link('centred', 0, 'distance', 0)
        w.math('disc', 'LESS_THAN', None, 0.38)
        w.link('distance', 'Value', 'disc', 0)
        w.add('ShaderNodeMix', 'cut', data_type='FLOAT', A=0.08)
        w.link('disc', 0, 'cut', 'Factor')
        w.link('shade', 0, 'cut', 'B')
        if show == 'rotation':
            w.link('radial', 'Segment Rotation', 'out', 'Height')
        else:
            w.link('cut', 0, 'out', 'Height')
    return body


rivet_cases = [(4, 0.0), (6, 0.0), (8, 0.0), (12, 0.0), (8, 1.0)]
sweep('radial_tiling_facets', [rivet_body(s, r) for s, r in rivet_cases],
      ['Sides 4', 'Sides 6', 'Sides 8', 'Sides 12', 'Sides 8, Roundness 1'], 'Height')
NUMBERS['radial_tiling_facets'] = {'setup': 'centred tile coordinate -> Radial Tiling -> Segment Rotation - 0.785 -> Cosine -> Map Range -1..1 to 0.25..0.9; '
                                            'inside a disc of radius 0.38 (Vector Math Length, Less Than); 256 dots'}
yy, xx = np.mgrid[0:SIZE, 0:SIZE]
inside = np.hypot((xx + 0.5) / SIZE - 0.5, 0.5 - (yy + 0.5) / SIZE) < 0.33
for s, r in rivet_cases:
    shade = measure(rivet_body(s, r))
    rotation = measure(rivet_body(s, r, show='rotation'))
    levels, counts = np.unique(np.round(shade[inside], 2), return_counts=True)
    big_levels = int((counts > 0.005 * inside.sum()).sum())
    NUMBERS['radial_tiling_facets'][f'sides {s} roundness {r}'] = {
        'flat shade levels inside the disc (each covering over 0.5 per cent)': big_levels,
        'segment rotation distinct values (rounded to 0.01)': int(len(np.unique(np.round(rotation[inside], 2)))),
        'segment rotation min / max': [round(float(rotation[inside].min()), 3), round(float(rotation[inside].max()), 3)]}


# the same 8 sides with the light turned to 0.6 instead of 0.785 (is the pairing of shades a property of the light angle?)
shade = measure(rivet_body(8, 0.0, light=0.6))
levels, counts = np.unique(np.round(shade[inside], 2), return_counts=True)
NUMBERS['radial_tiling_facets']['sides 8, light angle 0.6 instead of 0.785'] = {
    'flat shade levels inside the disc (each covering over 0.5 per cent)': int((counts > 0.005 * inside.sum()).sum())}


# ------------------------------------------------------------------------------------------------ D. Math Compare: line width
def compare_body(epsilon):
    def body(w):
        noise(w, 'n', 5.0, 4.0)
        stretch(w, 's', 'n')
        w.math('compare', 'COMPARE', None, 0.5, epsilon)
        w.link('s', 0, 'compare', 0)
        w.link('compare', 0, 'out', 'Height')
    return body


epsilons = [0.005, 0.01, 0.03, 0.06, 0.12]
sweep('math_compare_width', [compare_body(e) for e in epsilons], [f'Epsilon {e}' for e in epsilons], 'Height')
NUMBERS['math_compare_width'] = {'setup': 'Noise 3D Scale 5 Detail 4 -> Map Range 0.3..0.7 to 0..1 -> Math Compare (B = 0.5, Epsilon varied); share of the tile that is white'}
for e in epsilons:
    NUMBERS['math_compare_width'][f'epsilon {e}'] = round(float((measure(compare_body(e)) > 0.5).mean()), 4)


# ------------------------------------------------------------------------------------------------ E. Clamp
def clamp_body(case):
    def body(w):
        noise(w, 'n', 5.0, 4.0)
        stretch(w, 's', 'n')
        if case is None:
            w.link('s', 0, 'out', 'Height')
        elif case == 'map':
            stretch(w, 'm', 's', 0, 0.45, 0.55)
            w.link('m', 0, 'out', 'Height')
        else:
            kind, low, high = case
            w.add('ShaderNodeClamp', 'clamp', clamp_type=kind, Min=low, Max=high)
            w.link('s', 0, 'clamp', 'Value')
            w.link('clamp', 0, 'out', 'Height')
    return body


clamp_cases = [None, ('MINMAX', 0.3, 0.7), ('MINMAX', 0.45, 0.55), ('MINMAX', 0.7, 0.3), ('RANGE', 0.7, 0.3), 'map']
clamp_labels = ['source (noise 0..1)', 'Min Max 0.3..0.7', 'Min Max 0.45..0.55', 'Min Max, Min 0.7 > Max 0.3', 'Range, Min 0.7 > Max 0.3',
                'Map Range 0.45..0.55 (to compare)']
sweep('clamp', [clamp_body(c) for c in clamp_cases], clamp_labels, 'Height')
NUMBERS['clamp'] = {'setup': 'Noise 3D Scale 5 Detail 4 -> Map Range 0.3..0.7 to 0..1 (clamped) -> Clamp node'}
for case, label in zip(clamp_cases, clamp_labels):
    values = measure(clamp_body(case))
    entry = summary(values)
    entry['share_at_its_lowest'] = round(float((values <= values.min() + 1e-4).mean()), 4)
    entry['share_at_its_highest'] = round(float((values >= values.max() - 1e-4).mean()), 4)
    NUMBERS['clamp'][label] = entry


# ------------------------------------------------------------------------------------------------ F. Mix: Factor and blend modes for a stain
BRICK = [(0.0, rt.srgb_hex_to_linear('#7a3426')), (0.4, rt.srgb_hex_to_linear('#9c4a35')), (0.7, rt.srgb_hex_to_linear('#b8664a'))]
SOOT = rt.srgb_hex_to_linear('#3a2d27')


def stain_body(amount, mode='MULTIPLY', show='colour'):
    def body(w):
        noise(w, 'base noise', 4.0, 3.0)
        stretch(w, 'base stretch', 'base noise')
        colour_ramp(w, 'brick colours', BRICK)
        w.link('base stretch', 0, 'brick colours', 'Fac')
        noise(w, 'stain noise', 2.5, 5.0, dimensions='4D', W=7.3)
        stretch(w, 'stain mask', 'stain noise', 0, 0.5, 0.56)
        w.math('factor', 'MULTIPLY', None, amount)
        w.link('stain mask', 0, 'factor', 0)
        w.add('ShaderNodeMix', 'stain', data_type='RGBA', blend_type=mode, B=SOOT)
        w.link('factor', 0, 'stain', 'Factor')
        w.link('brick colours', 'Color', 'stain', 'A')
        if show == 'mask':
            w.link('stain mask', 0, 'out', 'Height')
        else:
            w.link('stain', 'Result', 'out', 'Colour')
    return body


amounts = [0.0, 0.25, 0.5, 0.75, 1.0]
sweep('mix_factor', [stain_body(a) for a in amounts], [f'Factor = mask x {a}' for a in amounts], 'Colour')
modes = ['MIX', 'MULTIPLY', 'DARKEN', 'OVERLAY', 'SOFT_LIGHT', 'VALUE']
sweep('mix_stain_modes', [stain_body(1.0, m) for m in modes], [m.replace('_', ' ').title() for m in modes], 'Colour')
mask = measure(stain_body(1.0, show='mask'))
in_stain, out_stain = mask > 0.999, mask < 0.001
NUMBERS['mix'] = {'setup': 'A = brick reds (Color Ramp Constant on noise), B = soot #3a2d27, Factor = stain mask (noise Map Range 0.5..0.56) x amount; '
                           'numbers = mean screen colour (0..255) inside the stain and outside it',
                  'share_of_tile_in_stain': round(float(in_stain.mean()), 4)}
for a in amounts:
    colour = to_srgb_steps(measure(stain_body(a), 'Colour'))
    NUMBERS['mix'][f'MULTIPLY factor x {a}'] = {'inside': [round(float(c), 1) for c in colour[in_stain].mean(axis=0)],
                                               'outside': [round(float(c), 1) for c in colour[out_stain].mean(axis=0)]}
for m in modes:
    colour = to_srgb_steps(measure(stain_body(1.0, m), 'Colour'))
    NUMBERS['mix'][f'{m} factor 1'] = {'inside': [round(float(c), 1) for c in colour[in_stain].mean(axis=0)]}


# ------------------------------------------------------------------------------------------------ G. Separate / Combine
def separate_body(case):
    def body(w):
        if case == 'u':
            w.add('ShaderNodeSeparateXYZ', 'split')
            w.link('in', 'Vector', 'split', 'Vector')
            w.link('split', 'X', 'out', 'Height')
            return
        if case == 'combine':
            w.add('ShaderNodeSeparateXYZ', 'split')
            w.link('in', 'Vector', 'split', 'Vector')
            w.math('u times 6', 'MULTIPLY', None, 6.0)
            w.link('split', 'X', 'u times 6', 0)
            w.add('ShaderNodeCombineXYZ', 'squeezed')
            w.link('u times 6', 0, 'squeezed', 'X')
            w.link('split', 'Y', 'squeezed', 'Y')
            noise(w, 'n', 5.0, 4.0, vector=('squeezed', 'Vector'))
            stretch(w, 's', 'n')
            w.link('s', 0, 'out', 'Height')
            return
        noise(w, 'n', 5.0, 4.0)
        if case == 'factor':
            stretch(w, 's', 'n', 0)
        else:
            w.add('ShaderNodeSeparateColor', 'channels', mode='RGB')
            w.link('n', 'Color', 'channels', 'Color')
            stretch(w, 's', 'channels', case)
        w.link('s', 0, 'out', 'Height')
    return body


separate_cases = ['factor', 'Red', 'Green', 'Blue', 'u', 'combine']
sweep('separate_combine', [separate_body(c) for c in separate_cases],
      ['Noise Factor', 'Noise Color: red', 'Noise Color: green', 'Noise Color: blue', 'Separate XYZ: X (= u)', 'Combine XYZ(u x 6, v) -> Noise'],
      'Height')


def raw_channel(case):
    def body(w):
        noise(w, 'n', 5.0, 4.0)
        if case == 'factor':
            w.link('n', 0, 'out', 'Height')
        else:
            w.add('ShaderNodeSeparateColor', 'channels', mode='RGB')
            w.link('n', 'Color', 'channels', 'Color')
            w.link('channels', case, 'out', 'Height')
    return body


raw = {c: measure(raw_channel(c)).ravel() for c in ['factor', 'Red', 'Green', 'Blue']}
corr = lambda a, b: round(float(np.corrcoef(raw[a], raw[b])[0, 1]), 3)
NUMBERS['separate_combine'] = {'setup': 'Noise 3D Scale 5 Detail 4, Color output split with Separate Color (RGB), true values, 256 x 256 dots',
                               'correlation factor-red': corr('factor', 'Red'), 'correlation factor-green': corr('factor', 'Green'),
                               'correlation factor-blue': corr('factor', 'Blue'), 'correlation green-blue': corr('Green', 'Blue'),
                               'ranges': {c: [round(float(v.min()), 3), round(float(v.max()), 3)] for c, v in raw.items()}}


# ------------------------------------------------------------------------------------------------ H. Color Ramp: stop position against share covered; hex trap
STEEL_HEX, RUST_HEX = '#4b5052', '#8a4a26'


def ramp_body(position, typed_wrong=False):
    def body(w):
        noise(w, 'n', 5.0, 4.0)
        if typed_wrong:
            steel = tuple(int(STEEL_HEX[i:i + 2], 16) / 255.0 for i in (1, 3, 5)) + (1.0,)
            rust = tuple(int(RUST_HEX[i:i + 2], 16) / 255.0 for i in (1, 3, 5)) + (1.0,)
        else:
            steel, rust = rt.srgb_hex_to_linear(STEEL_HEX), rt.srgb_hex_to_linear(RUST_HEX)
        colour_ramp(w, 'ramp', [(0.0, steel), (position, rust)])
        w.link('n', 0, 'ramp', 'Fac')
        w.link('ramp', 'Color', 'out', 'Colour')
    return body


positions = [0.45, 0.5, 0.55, 0.6, 0.65]
sweep('ramp_threshold_share', [ramp_body(p) for p in positions] + [ramp_body(0.55, True)],
      [f'rust stop at {p}' for p in positions] + ['0.55, hex typed as /255 (wrong)'], 'Colour')
raw_noise = measure(lambda w: (noise(w, 'n', 5.0, 4.0), w.link('n', 0, 'out', 'Height')))
NUMBERS['ramp_threshold_share'] = {'setup': 'raw Noise 3D Scale 5 Detail 4 (not stretched) -> Color Ramp Constant: steel #4b5052 from 0, rust #8a4a26 from the stop',
                                   'noise_range': [round(float(raw_noise.min()), 3), round(float(raw_noise.max()), 3)],
                                   'noise_middle_90_percent': [round(float(np.percentile(raw_noise, 5)), 3), round(float(np.percentile(raw_noise, 95)), 3)]}
for p in positions:
    NUMBERS['ramp_threshold_share'][f'rust share, stop at {p}'] = round(float((raw_noise >= p).mean()), 4)
right = to_srgb_steps(measure(ramp_body(0.55), 'Colour'))
wrong = to_srgb_steps(measure(ramp_body(0.55, True), 'Colour'))
steel_area = raw_noise < 0.5
NUMBERS['ramp_threshold_share']['steel colour baked, hex converted to linear'] = [round(float(c), 1) for c in right[steel_area].mean(axis=0)]
NUMBERS['ramp_threshold_share']['steel colour baked, hex typed as /255'] = [round(float(c), 1) for c in wrong[steel_area].mean(axis=0)]
NUMBERS['ramp_threshold_share']['steel colour wanted'] = [int(STEEL_HEX[i:i + 2], 16) for i in (1, 3, 5)]


# ------------------------------------------------------------------------------------------------ I. Float Curve "extend" (numbers only)
def curve_body(extend):
    def body(w):
        w.add('ShaderNodeSeparateXYZ', 'split')
        w.link('in', 'Vector', 'split', 'Vector')
        w.math('input', 'MULTIPLY_ADD', None, 2.0, -0.5)           # u from 0..1 becomes -0.5..1.5
        w.link('split', 'X', 'input', 0)
        node = w.add('ShaderNodeFloatCurve', 'curve')
        curve = node.mapping.curves[0]
        curve.points.new(0.35, 0.1)
        curve.points.new(0.65, 0.9)
        node.mapping.extend = extend
        node.mapping.update()
        w.link('input', 0, 'curve', 'Value')
        w.link('curve', 0, 'out', 'Height')
    return body


NUMBERS['float_curve_extend'] = {'setup': 'S-curve through (0,0) (0.35,0.1) (0.65,0.9) (1,1); input runs -0.5..1.5 across the tile; value read at the dot nearest each input'}
wanted_inputs = [-0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
for extend in ('EXTRAPOLATED', 'HORIZONTAL'):
    row = measure(curve_body(extend), size=SIZE)[SIZE // 2]
    table = {}
    for x in wanted_inputs:
        column = int(min(SIZE - 1, max(0, round((x + 0.5) / 2.0 * SIZE - 0.5))))
        actual = (column + 0.5) / SIZE * 2.0 - 0.5
        table[f'input {actual:.3f}'] = round(float(row[column]), 3)
    NUMBERS['float_curve_extend'][extend] = table

with open(os.path.join(HERE, 'numbers.json'), 'w') as handle:
    json.dump(NUMBERS, handle, indent=1)
print('done: numbers.json written')
