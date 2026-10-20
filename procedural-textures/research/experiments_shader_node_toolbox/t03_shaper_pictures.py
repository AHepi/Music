# What this does: renders the "shaper" pictures for the guide: Color Ramp modes, Map Range, Math operations, Float Curve, Mix blend modes,
# Hue/Saturation, Brightness/Contrast, Gamma, Invert, Mapping, Vector Math warping.
# Run: blender -b --disable-autoexec -t 2 --python t03_shaper_pictures.py -- [only_name ...]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import probe_tools as pt
from sweeps import sweep
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def want(n): return not only or n in only
D = 'ShaderNodeTex'

def noise_src(w, name='src', scale=4.0, detail=4.0, lo=0.3, hi=0.7, vec=None):
    """normalised fBM noise stretched from the usual 0.3..0.7 to 0..1; the result is node `name` output 0"""
    n = w.add(D + 'Noise', name + '_n', x=-3, Scale=scale, Detail=detail, Roughness=0.55)
    w.link(vec or 'in', 'Vector' if not vec else 0, name + '_n', 'Vector')
    m = w.add('ShaderNodeMapRange', name, x=-2)
    m.inputs[1].default_value = lo; m.inputs[2].default_value = hi
    w.link(name + '_n', 'Fac', name, 0)
    return m

# ---- color ramp ------------------------------------------------------------------------------------------------
if want('s01_color_ramp_interpolation'):
    modes = ['CONSTANT', 'LINEAR', 'EASE', 'CARDINAL', 'B_SPLINE']
    def body(w, mode):
        w.add('ShaderNodeSeparateXYZ', 'sx', x=-1); w.link('in', 'Vector', 'sx', 'Vector')
        r = w.add('ShaderNodeValToRGB', 'r', x=0)
        cr = r.color_ramp
        cr.interpolation = mode
        cr.elements[0].color = (0.05, 0.05, 0.05, 1); cr.elements[1].color = (0.95, 0.95, 0.95, 1)
        cr.elements[1].position = 0.9
        e = cr.elements.new(0.3); e.color = (0.85, 0.15, 0.05, 1)
        e = cr.elements.new(0.6); e.color = (0.1, 0.35, 0.8, 1)
        w.link('sx', 'X', 'r', 'Fac'); w.link('r', 'Color', 'out', 'Colour')
    sweep('s01_color_ramp_interpolation', body, modes, ['Constant', 'Linear', 'Ease', 'Cardinal', 'B-Spline'], channel='Colour', columns=5, size=160, title='Color Ramp: Interpolation (4 stops)')
if want('s01b_color_ramp_hue'):
    cases = [('RGB', 'NEAR'), ('HSV', 'NEAR'), ('HSV', 'FAR'), ('HSV', 'CW'), ('HSV', 'CCW'), ('HSL', 'NEAR')]
    def body(w, c):
        w.add('ShaderNodeSeparateXYZ', 'sx', x=-1); w.link('in', 'Vector', 'sx', 'Vector')
        r = w.add('ShaderNodeValToRGB', 'r', x=0)
        cr = r.color_ramp
        cr.color_mode = c[0]; cr.hue_interpolation = c[1]
        cr.elements[0].color = (1.0, 0.1, 0.05, 1); cr.elements[1].color = (0.1, 0.3, 1.0, 1)
        w.link('sx', 'X', 'r', 'Fac'); w.link('r', 'Color', 'out', 'Colour')
    sweep('s01b_color_ramp_hue', body, cases, [f'{a} / {b}' for a, b in cases], channel='Colour', columns=6, size=128, title='Color Ramp: colour mode and hue path (red to blue)')

# ---- map range --------------------------------------------------------------------------------------------------
if want('s02_map_range'):
    cases = [('LINEAR', True, 4), ('SMOOTHSTEP', True, 4), ('SMOOTHERSTEP', True, 4), ('STEPPED', True, 4), ('STEPPED', True, 2), ('STEPPED', True, 8)]
    def body(w, c):
        interp, clamp, steps = c
        n = noise_src(w, 'src', lo=0.0, hi=1.0)
        m = w.add('ShaderNodeMapRange', 'mr', x=0, interpolation_type=interp, clamp=clamp)
        m.inputs[1].default_value = 0.4; m.inputs[2].default_value = 0.6; m.inputs[3].default_value = 0.0; m.inputs[4].default_value = 1.0; m.inputs[5].default_value = steps
        w.link('src', 0, 'mr', 0); w.link('mr', 0, 'out', 'Height')
    # src uses Map Range with lo=0, hi=1 -> raw noise. Then From 0.4..0.6 -> 0..1
    sweep('s02_map_range', body, cases, ['Linear', 'Smooth Step', 'Smoother Step', 'Stepped, 4 steps', 'Stepped, 2 steps', 'Stepped, 8 steps'], columns=3, size=192, title='Map Range on noise (From 0.4..0.6 to 0..1)')
if want('s02b_map_range_window'):
    cases = [(0.0, 1.0), (0.3, 0.7), (0.45, 0.55), (0.49, 0.51)]
    def body(w, c):
        n = noise_src(w, 'src', lo=0.0, hi=1.0)
        m = w.add('ShaderNodeMapRange', 'mr', x=0)
        m.inputs[1].default_value = c[0]; m.inputs[2].default_value = c[1]
        w.link('src', 0, 'mr', 0); w.link('mr', 0, 'out', 'Height')
    sweep('s02b_map_range_window', body, cases, ['From 0 to 1 (none)', 'From 0.3 to 0.7', 'From 0.45 to 0.55', 'From 0.49 to 0.51'], columns=4, size=192, title='Map Range: narrowing the From window = contrast')

# ---- math -------------------------------------------------------------------------------------------------------
if want('s03_math_operations'):
    ops = [('ADD', 0.25, None, True), ('MULTIPLY', 2.0, None, True), ('POWER', 3.0, None, False), ('GREATER_THAN', 0.5, None, False),
           ('COMPARE', 0.5, 0.03, False), ('ABSOLUTE*', 0.5, None, False), ('FRACT*', 4.0, None, False), ('PINGPONG', 0.3, None, False),
           ('SNAP', 0.25, None, False), ('SMOOTH_MIN', 0.5, 0.2, False), ('WRAP', 0.3, 0.7, False), ('SINE*', 6.0, None, False)]
    def body(w, c):
        op, a, b, clamp = c
        src = noise_src(w, 'src')
        label = op
        if op == 'ABSOLUTE*':       # |noise - 0.5| * 2
            w.math('sub', 'SUBTRACT', None, 0.5, x=0); w.link('src', 0, 'sub', 0)
            w.math('abs', 'ABSOLUTE', x=1); w.link('sub', 0, 'abs', 0)
            w.math('x2', 'MULTIPLY', None, 2.0, x=2); w.link('abs', 0, 'x2', 0); last = 'x2'
        elif op == 'FRACT*':        # fract(noise * 4)
            w.math('mul', 'MULTIPLY', None, a, x=0); w.link('src', 0, 'mul', 0)
            w.math('fr', 'FRACT', x=1); w.link('mul', 0, 'fr', 0); last = 'fr'
        elif op == 'SINE*':         # 0.5 + 0.5*sin(noise*6)
            w.math('mul', 'MULTIPLY', None, a, x=0); w.link('src', 0, 'mul', 0)
            w.math('sin', 'SINE', x=1); w.link('mul', 0, 'sin', 0)
            w.math('half', 'MULTIPLY_ADD', None, 0.5, 0.5, x=2); w.link('sin', 0, 'half', 0); last = 'half'
        elif op == 'PINGPONG':      # pingpong(noise*3, 1)
            w.math('mul', 'MULTIPLY', None, 3.0, x=0); w.link('src', 0, 'mul', 0)
            w.math('pp', 'PINGPONG', None, 1.0, x=1); w.link('mul', 0, 'pp', 0); last = 'pp'
        else:
            nd = w.math('op', op, None, a, b, clamp=clamp, x=0); w.link('src', 0, 'op', 0); last = 'op'
        w.link(last, 0, 'out', 'Height')
    labels = ['Add 0.25 (clamp)', 'Multiply 2 (clamp)', 'Power 3', 'Greater Than 0.5', 'Compare 0.5 +-0.03', '|x-0.5| * 2', 'Fraction(x * 4)', 'Ping-Pong(x*3, 1)', 'Snap 0.25', 'Smooth Min 0.5, 0.2', 'Wrap 0.3..0.7', '0.5+0.5*Sine(x*6)']
    sweep('s03_math_operations', body, ops, labels, columns=4, size=160, title='Math node on the same noise (0..1)')

# ---- float curve -------------------------------------------------------------------------------------------------
if want('s04_float_curve'):
    shapes = {'identity (2 points)': [], 'S-curve': [(0.35, 0.1), (0.65, 0.9)], 'hump (peaks at 0.5)': [(0.5, 1.0)], 'steps': [(0.33, 0.0), (0.34, 0.5), (0.66, 0.5), (0.67, 1.0)]}
    def body(w, name):
        src = noise_src(w, 'src')
        c = w.add('ShaderNodeFloatCurve', 'fc', x=0)
        cur = c.mapping.curves[0]
        pts = shapes[name]
        if name == 'hump (peaks at 0.5)':
            cur.points[0].location = (0.0, 0.0); cur.points[1].location = (1.0, 0.0)
        for (x, y) in pts:
            cur.points.new(x, y)
        if name == 'S-curve':
            for p in cur.points: p.handle_type = 'AUTO'
        c.mapping.update()
        w.link('src', 0, 'fc', 'Value'); w.link('fc', 0, 'out', 'Height')
    sweep('s04_float_curve', body, list(shapes.keys()), list(shapes.keys()), columns=4, size=160, title='Float Curve applied to noise')

# ---- mix blend modes ----------------------------------------------------------------------------------------------
if want('s05_mix_blend_modes'):
    modes = ['MIX', 'DARKEN', 'MULTIPLY', 'BURN', 'LIGHTEN', 'SCREEN', 'DODGE', 'ADD', 'OVERLAY', 'SOFT_LIGHT', 'LINEAR_LIGHT', 'DIFFERENCE', 'EXCLUSION', 'SUBTRACT', 'DIVIDE', 'HUE', 'SATURATION', 'COLOR', 'VALUE']
    def body(w, mode):
        w.add('ShaderNodeSeparateXYZ', 'sx', x=-1); w.link('in', 'Vector', 'sx', 'Vector')
        # A: a coloured pattern (brick)  B: a grey-blue to yellow noise
        b = w.add(D + 'Brick', 'b', x=0); b.inputs['Scale'].default_value = 2.0
        b.inputs['Color1'].default_value = (0.65, 0.2, 0.1, 1); b.inputs['Color2'].default_value = (0.4, 0.12, 0.08, 1); b.inputs['Mortar'].default_value = (0.55, 0.5, 0.4, 1)
        w.link('in', 'Vector', 'b', 'Vector')
        n = w.add(D + 'Noise', 'n', x=0, Scale=4.0, Detail=3.0)
        w.link('in', 'Vector', 'n', 'Vector')
        r = w.add('ShaderNodeValToRGB', 'r', x=1)
        r.color_ramp.elements[0].color = (0.1, 0.2, 0.7, 1); r.color_ramp.elements[1].color = (0.95, 0.85, 0.3, 1)
        r.color_ramp.elements[0].position = 0.3; r.color_ramp.elements[1].position = 0.7
        w.link('n', 'Fac', 'r', 'Fac')
        m = w.add('ShaderNodeMix', 'm', x=2, data_type='RGBA', blend_type=mode, clamp_result=False)
        m.inputs[0].default_value = 1.0
        w.link('b', 'Color', 'm', 'A'); w.link('r', 'Color', 'm', 'B')
        w.link('m', 'Result', 'out', 'Colour')
    sweep('s05_mix_blend_modes', body, modes, [mo.replace('_', ' ').title() for mo in modes], channel='Colour', columns=5, size=128, title='Mix node blend modes: A = bricks, B = blue-yellow noise, Factor 1')

# ---- colour adjusters --------------------------------------------------------------------------------------------
def painted_source(w):
    n = w.add(D + 'Noise', 'n', x=-1, Scale=3.0, Detail=5.0, Roughness=0.6); w.link('in', 'Vector', 'n', 'Vector')
    r = w.add('ShaderNodeValToRGB', 'r', x=0)
    cr = r.color_ramp
    cr.elements[0].color = (0.25, 0.08, 0.05, 1); cr.elements[0].position = 0.35
    cr.elements[1].color = (0.8, 0.35, 0.12, 1); cr.elements[1].position = 0.65
    e = cr.elements.new(0.5); e.color = (0.55, 0.45, 0.4, 1)
    w.link('n', 'Fac', 'r', 'Fac')
    return 'r'
if want('s06_color_adjusters'):
    cases = [('Source', None), ('Hue 0.3', ('hue', 0.3)), ('Hue 0.7', ('hue', 0.7)), ('Saturation 0', ('sat', 0.0)), ('Saturation 1.6', ('sat', 1.6)), ('Value 0.5', ('val', 0.5)),
             ('Bright -0.2', ('bright', -0.2)), ('Bright +0.2', ('bright', 0.2)), ('Contrast -0.5', ('contrast', -0.5)), ('Contrast +0.5', ('contrast', 0.5)),
             ('Gamma 0.5', ('gamma', 0.5)), ('Gamma 2', ('gamma', 2.0)), ('Invert', ('invert', 1.0)), ('Invert 0.5', ('invert', 0.5))]
    def body(w, c):
        name, spec = c
        src = painted_source(w)
        last, sock = src, 'Color'
        if spec:
            kind, val = spec
            if kind in ('hue', 'sat', 'val'):
                h = w.add('ShaderNodeHueSaturation', 'adj', x=1)
                h.inputs['Hue' if kind == 'hue' else 'Saturation' if kind == 'sat' else 'Value'].default_value = val
                w.link(src, 'Color', 'adj', 'Color'); last = 'adj'
            elif kind in ('bright', 'contrast'):
                h = w.add('ShaderNodeBrightContrast', 'adj', x=1)
                h.inputs['Bright' if kind == 'bright' else 'Contrast'].default_value = val
                w.link(src, 'Color', 'adj', 'Color'); last = 'adj'
            elif kind == 'gamma':
                h = w.add('ShaderNodeGamma', 'adj', x=1); h.inputs['Gamma'].default_value = val
                w.link(src, 'Color', 'adj', 'Color'); last = 'adj'
            elif kind == 'invert':
                h = w.add('ShaderNodeInvert', 'adj', x=1); h.inputs['Fac'].default_value = val
                w.link(src, 'Color', 'adj', 'Color'); last = 'adj'
        w.link(last, 'Color', 'out', 'Colour')
    sweep('s06_color_adjusters', body, cases, [c[0] for c in cases], channel='Colour', columns=7, size=128, title='Hue/Saturation/Value, Bright/Contrast, Gamma, Invert on one painted-looking colour')

# ---- mapping / vector rotate -------------------------------------------------------------------------------------
if want('s07_mapping'):
    cases = [('Point', 'POINT'), ('Texture', 'TEXTURE'), ('Vector', 'VECTOR'), ('Normal', 'NORMAL')]
    def body(w, c):
        label, vt = c
        mp = w.add('ShaderNodeMapping', 'mp', x=-1, vector_type=vt)
        mp.inputs[1].default_value = (0.35, 0.0, 0.0)      # Location (by position: its name is not found when Type hides it)
        mp.inputs[2].default_value = (0.0, 0.0, math.radians(30))
        mp.inputs[3].default_value = (1.0, 3.0, 1.0)
        w.link('in', 'Vector', 'mp', 'Vector')
        n = w.add(D + 'Noise', 'n', x=0, Scale=4.0, Detail=3.0)
        w.link('mp', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('s07_mapping', body, cases, ['Point', 'Texture', 'Vector (no move)', 'Normal (no move)'], stretch=True, columns=4, size=160, title='Mapping: type (Move x 0.35, Turn 30, Scale y x3)')
if want('s07b_mapping_basic'):
    cases = [('plain', None), ('Scale (1,4,1)', 's'), ('Rotate 45', 'r'), ('Move x 0.5', 't')]
    def body(w, c):
        mp = w.add('ShaderNodeMapping', 'mp', x=-1, vector_type='POINT')
        if c[1] == 's': mp.inputs['Scale'].default_value = (1.0, 4.0, 1.0)
        if c[1] == 'r': mp.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(45))
        if c[1] == 't': mp.inputs['Location'].default_value = (0.5, 0.0, 0.0)
        w.link('in', 'Vector', 'mp', 'Vector')
        n = w.add(D + 'Noise', 'n', x=0, Scale=4.0, Detail=3.0)
        w.link('mp', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('s07b_mapping_basic', body, cases, [c[0] for c in cases], stretch=True, columns=4, size=160, title='Mapping node (Point type) on noise')

# ---- domain warping with vector math -----------------------------------------------------------------------------
if want('s08_warp'):
    amounts = [0.0, 0.05, 0.12, 0.3]
    def body(w, a):
        wn = w.add(D + 'Noise', 'wn', x=-3, Scale=3.0, Detail=2.0, Roughness=0.5)
        w.link('in', 'Vector', 'wn', 'Vector')
        w.vector_math('c', 'SUBTRACT', x=-2); w.nodes['c'].inputs[1].default_value = (0.5, 0.5, 0.5); w.link('wn', 'Color', 'c', 0)
        w.vector_math('s', 'SCALE', x=-1); w.link('c', 0, 's', 0); w.nodes['s'].inputs['Scale'].default_value = a
        w.vector_math('add', 'ADD', x=0); w.link('in', 'Vector', 'add', 0); w.link('s', 0, 'add', 1)
        v = w.add(D + 'Voronoi', 'v', x=1, feature='DISTANCE_TO_EDGE', Scale=6.0)
        w.link('add', 0, 'v', 'Vector')
        w.math('lt', 'LESS_THAN', None, 0.06, x=2); w.link('v', 'Distance', 'lt', 0)
        w.link('lt', 0, 'out', 'Height')
    sweep('s08_warp', body, amounts, [f'warp {a}' for a in amounts], columns=4, size=192, title='Domain warping: coordinates + (noise - 0.5) x strength')

# ---- vector math snap / fraction ------------------------------------------------------------------------------
if want('s09_vector_math_tricks'):
    cases = ['plain', 'SNAP', 'FRACTION', 'WRAP', 'FLOOR', 'ABSOLUTE']
    def body(w, op):
        w.vector_math('sc', 'SCALE', x=-3); w.link('in', 'Vector', 'sc', 0); w.nodes['sc'].inputs['Scale'].default_value = 3.0
        w.add('ShaderNodeVectorMath', 'cen', x=-2, operation='SUBTRACT'); w.nodes['cen'].inputs[1].default_value = (1.5, 1.5, 0)
        w.link('sc', 0, 'cen', 0)
        last = 'cen'
        if op == 'SNAP':
            w.vector_math('v', 'SNAP', x=-1); w.nodes['v'].inputs[1].default_value = (0.25, 0.25, 0.25); w.link(last, 0, 'v', 0); last = 'v'
        elif op == 'FRACTION':
            w.vector_math('v', 'FRACTION', x=-1); w.link(last, 0, 'v', 0); last = 'v'
        elif op == 'WRAP':
            w.vector_math('v', 'WRAP', x=-1); w.nodes['v'].inputs[1].default_value = (-0.5, -0.5, -0.5); w.nodes['v'].inputs[2].default_value = (0.5, 0.5, 0.5); w.link(last, 0, 'v', 0); last = 'v'
        elif op == 'FLOOR':
            w.vector_math('v', 'FLOOR', x=-1); w.link(last, 0, 'v', 0); last = 'v'
        elif op == 'ABSOLUTE':
            w.vector_math('v', 'ABSOLUTE', x=-1); w.link(last, 0, 'v', 0); last = 'v'
        n = w.add(D + 'Noise', 'n', x=0, Scale=2.0, Detail=3.0)
        w.link(last, 0, 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('s09_vector_math_tricks', body, cases, ['no change', 'Snap 0.25 (pixelate)', 'Fraction (tile 3x3)', 'Wrap (tile 3x3)', 'Floor (flat: always 0.5)', 'Absolute (mirror)'], stretch=True, columns=3, size=160, title='Vector Math on the coordinates, then Noise')
print('done shaper pictures')
