# What this does: SIX quick "toolbox only" first attempts at our six surfaces (brick, slate, wood, metal, mud, gravel), each built from just the
# nodes the shader-toolbox guide describes (Brick, Noise, Voronoi, Wave, Mapping, Map Range, Math, Color Ramp, Mix). They exist to show that the
# recipe cards in the guide really run and to give a rough idea of how close plain nodes get. They are NOT seamless (plain tile coordinates) and
# not tuned; the real recipes are made elsewhere. Pick the surface with the parameter "surface".
# Use: blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- THIS_FILE OUT_FOLDER --size 1254 --normal-reference brick --params '{"surface": "brick"}'
import math
import bpy
import recipe_tools as rt

T = 'ShaderNodeTex'


class Kit:
    """tiny helpers on top of the NodeWriter so each surface reads as a list of steps"""
    def __init__(self, w):
        self.w = w
        self.n = 0

    def name(self, base):
        self.n += 1
        return f'{base}{self.n}'

    def noise(self, scale, detail=5.0, rough=0.55, stretch=None, offset=(0, 0, 0), distortion=0.0, vec=None):
        w = self.w
        src = vec or ('in', 'Vector')
        if stretch or any(offset):
            mp = self.name('map')
            node = w.add('ShaderNodeMapping', mp, vector_type='POINT')
            node.inputs[1].default_value = offset; node.inputs[3].default_value = stretch or (1, 1, 1)
            w.link(src[0], src[1], mp, 'Vector'); src = (mp, 'Vector')
        n = self.name('noise')
        w.add(T + 'Noise', n, Scale=scale, Detail=detail, Roughness=rough, Distortion=distortion)
        w.link(src[0], src[1], n, 'Vector')
        return (n, 'Fac')

    def remap(self, src, lo, hi, out_lo=0.0, out_hi=1.0, kind='LINEAR'):
        w = self.w
        n = self.name('remap')
        m = w.add('ShaderNodeMapRange', n, interpolation_type=kind)
        m.inputs[1].default_value = lo; m.inputs[2].default_value = hi; m.inputs[3].default_value = out_lo; m.inputs[4].default_value = out_hi
        w.link(src[0], src[1], n, 0)
        return (n, 'Result')

    def math(self, op, a, b=None, clamp=False):
        w = self.w
        n = self.name('m')
        node = w.add('ShaderNodeMath', n, operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, tuple): w.link(v[0], v[1], n, i)
            else: node.inputs[i].default_value = v
        return (n, 'Value')

    def ramp(self, src, stops, interp='LINEAR'):
        w = self.w
        n = self.name('ramp')
        r = w.add('ShaderNodeValToRGB', n); cr = r.color_ramp
        cr.interpolation = interp
        stops = sorted(stops, key=lambda s: s[0])
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = stops[0][1] + (1.0,)
        cr.elements[1].position = stops[-1][0]; cr.elements[1].color = stops[-1][1] + (1.0,)
        for pos, col in stops[1:-1]:
            e = cr.elements.new(pos); e.color = col + (1.0,)
        w.link(src[0], src[1], n, 'Fac')
        return (n, 'Color')

    def mix(self, fac, a, b, blend='MIX'):
        w = self.w
        n = self.name('mix')
        node = w.add('ShaderNodeMix', n, data_type='RGBA', blend_type=blend)
        if isinstance(fac, tuple): w.link(fac[0], fac[1], n, 'Factor')
        else: node.inputs['Factor'].default_value = fac
        for key, v in (('A', a), ('B', b)):
            if isinstance(v, tuple) and isinstance(v[0], str): w.link(v[0], v[1], n, key)
            else: node.inputs[key].default_value = tuple(v) + (1.0,) if len(v) == 3 else tuple(v)
        return (n, 'Result')

    def mix_float(self, fac, a, b):
        w = self.w
        n = self.name('mixf')
        node = w.add('ShaderNodeMix', n, data_type='FLOAT')
        if isinstance(fac, tuple): w.link(fac[0], fac[1], n, 'Factor')
        else: node.inputs['Factor'].default_value = fac
        for key, v in (('A', a), ('B', b)):
            if isinstance(v, tuple): w.link(v[0], v[1], n, key)
            else: node.inputs[key].default_value = v
        return (n, 'Result')

    def brick(self, scale, width, height, mortar, smooth=0.02, offset=0.5, c1=(1, 1, 1), c2=(0.6, 0.6, 0.6), cm=(0, 0, 0), freq=2, bias=0.0, vec=None):
        w = self.w
        n = self.name('brick')
        b = w.add(T + 'Brick', n, offset=offset, offset_frequency=freq)
        b.inputs['Scale'].default_value = scale; b.inputs['Brick Width'].default_value = width; b.inputs['Row Height'].default_value = height
        b.inputs['Mortar Size'].default_value = mortar; b.inputs['Mortar Smooth'].default_value = smooth; b.inputs['Bias'].default_value = bias
        b.inputs['Color1'].default_value = c1 + (1.0,); b.inputs['Color2'].default_value = c2 + (1.0,); b.inputs['Mortar'].default_value = cm + (1.0,)
        v = vec or ('in', 'Vector')
        w.link(v[0], v[1], n, 'Vector')
        return n

    def voronoi(self, scale, feature='F1', randomness=1.0, vec=None, detail=0.0, rough=0.5):
        w = self.w
        n = self.name('vor')
        v = w.add(T + 'Voronoi', n, feature=feature, Scale=scale, Randomness=randomness)
        if detail and feature != 'N_SPHERE_RADIUS':          # Detail is switched off (not found by name) for N-Sphere Radius
            v.inputs['Detail'].default_value = detail
        src = vec or ('in', 'Vector')
        w.link(src[0], src[1], n, 'Vector')
        return n

    def mapping(self, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), vec=None):
        w = self.w
        n = self.name('mapping')
        m = w.add('ShaderNodeMapping', n, vector_type='POINT')
        m.inputs[1].default_value = loc; m.inputs[2].default_value = rot; m.inputs[3].default_value = scale
        src = vec or ('in', 'Vector')
        w.link(src[0], src[1], n, 'Vector')
        return (n, 'Vector')


HEIGHT_FROM_COLOUR = {'on': False}


def finish(w, colour, height, rough=0.8, metal=0.0):
    if HEIGHT_FROM_COLOUR['on']:
        # the reference height maps follow the brightness of the colour picture: Gamma (linear -> screen brightness), then RGB to BW
        g = w.add('ShaderNodeGamma', 'h_gamma'); g.inputs['Gamma'].default_value = 0.4545
        w.link(colour[0], colour[1], 'h_gamma', 'Color')
        w.add('ShaderNodeRGBToBW', 'h_bw'); w.link('h_gamma', 'Color', 'h_bw', 'Color')
        height = ('h_bw', 'Val')
    for key, src in (('Colour', colour), ('Height', height), ('Roughness', rough), ('Metallic', metal)):
        if isinstance(src, tuple): w.link(src[0], src[1], 'out', key)
        else:
            c = w.add('ShaderNodeValue', f'const_{key}'); c.outputs[0].default_value = src; w.link(c.name, 0, 'out', key)


def build_node_group(parameters):
    surface = parameters.get('surface', 'brick')
    HEIGHT_FROM_COLOUR['on'] = bool(parameters.get('height_from_colour', False))
    tree, w = rt.make_group_tree(f'toolbox demo {surface}', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    k = Kit(w)
    globals()['make_' + surface](k, w)
    return tree


# ------------------------------------------------------------------------------------------------------------- brick
def make_brick(k, w):
    b = k.brick(1.7, 0.5, 0.14, 0.017, smooth=0.04, c1=(1.0, 1.0, 1.0), c2=(0.62, 0.62, 0.62), cm=(0, 0, 0))
    blotch = k.noise(7.0, 6.0, 0.6)
    r = k.remap(blotch, 0.38, 0.62)
    body = k.ramp(r, [(0.0, (0.075, 0.04, 0.029)), (0.3, (0.159, 0.048, 0.027)), (0.62, (0.247, 0.057, 0.026)), (1.0, (0.352, 0.076, 0.027))])
    tinted = k.mix(0.8, body, (b, 'Color'), 'MULTIPLY')
    # long dark soot stains running down the wall
    stain = k.noise(2.5, 5.0, 0.6, stretch=(1.0, 0.18, 1.0))
    s = k.remap(stain, 0.55, 0.75)
    sooty = k.mix(s, tinted, (0.025, 0.02, 0.018))
    # mortar: tan with a little noise
    mn = k.noise(30.0, 3.0, 0.5)
    mortar = k.ramp(mn, [(0.3, (0.12, 0.078, 0.048)), (0.7, (0.235, 0.136, 0.078))])
    colour = k.mix((b, 'Factor'), sooty, mortar)
    fine = k.noise(60.0, 4.0, 0.6)
    height = k.math('ADD', k.math('MULTIPLY', k.math('SUBTRACT', 1.0, (b, 'Factor')), 0.35), k.math('MULTIPLY', fine, 0.12))
    height = k.math('ADD', height, 0.3)
    finish(w, colour, height, rough=0.85)


# ------------------------------------------------------------------------------------------------------------- slate
def make_slate(k, w):
    b = k.brick(1.0, 0.17, 0.125, 0.012, smooth=0.01, c1=(1.0, 1.0, 1.0), c2=(0.7, 0.7, 0.7), cm=(0, 0, 0), offset=0.5)
    streak = k.noise(7.0, 6.0, 0.62, stretch=(14.0, 1.2, 1.0))
    sr = k.remap(streak, 0.35, 0.65)
    paint = k.ramp(sr, [(0.0, (0.018, 0.019, 0.02)), (0.3, (0.046, 0.054, 0.056)), (0.65, (0.065, 0.076, 0.078)), (1.0, (0.1, 0.11, 0.107))])
    moss_n = k.noise(4.0, 4.0, 0.6, stretch=(6.0, 0.6, 1.0), offset=(3.1, 1.7, 0.0))
    moss = k.remap(moss_n, 0.58, 0.72)
    mossy = k.mix(k.math('MULTIPLY', moss, 0.7), paint, (0.07, 0.075, 0.03))
    body = k.mix(0.8, mossy, (b, 'Color'), 'MULTIPLY')
    colour = k.mix((b, 'Factor'), body, (0.006, 0.006, 0.006))
    fine = k.noise(50.0, 3.0, 0.5)
    height = k.math('ADD', k.math('MULTIPLY', k.math('SUBTRACT', 1.0, (b, 'Factor')), 0.4), k.math('ADD', k.math('MULTIPLY', fine, 0.1), 0.3))
    finish(w, colour, height, rough=0.6)


# ------------------------------------------------------------------------------------------------------------- wood
def make_wood(k, w):
    b = k.brick(1.0, 1.0, 0.155, 0.006, smooth=0.01, offset=0.0, c1=(1.0, 1.0, 1.0), c2=(0.7, 0.7, 0.7), cm=(0, 0, 0))
    # long grain: wave bands that run along x, bent by noise, plus a stretched noise for streaks
    mp = k.mapping(scale=(0.6, 1.0, 1.0))
    wave = w.add(T + 'Wave', 'grain', wave_type='BANDS', bands_direction='Y', wave_profile='SAW')
    wave.inputs['Scale'].default_value = 24.0; wave.inputs['Distortion'].default_value = 5.0; wave.inputs['Detail'].default_value = 3.0; wave.inputs['Detail Scale'].default_value = 1.2
    w.link(mp[0], mp[1], 'grain', 'Vector')
    streak = k.noise(6.0, 6.0, 0.6, stretch=(0.5, 14.0, 1.0))
    mixg = k.mix_float(0.5, ('grain', 'Fac'), streak)
    r = k.remap(mixg, 0.2, 0.8)
    wood = k.ramp(r, [(0.0, (0.022, 0.013, 0.009)), (0.3, (0.074, 0.043, 0.029)), (0.6, (0.14, 0.079, 0.051)), (0.85, (0.218, 0.115, 0.064)), (1.0, (0.07, 0.075, 0.08))])
    # grey weathering patches
    pat = k.noise(3.0, 5.0, 0.6, stretch=(0.7, 3.0, 1.0), offset=(2.2, 5.1, 0.0))
    grey = k.remap(pat, 0.5, 0.65)
    weathered = k.mix(k.math('MULTIPLY', grey, 0.6), wood, (0.07, 0.07, 0.075))
    body = k.mix(0.85, weathered, (b, 'Color'), 'MULTIPLY')
    # cracks: thin cell borders stretched along x
    mpc = k.mapping(scale=(0.18, 1.0, 1.0), loc=(0.3, 0, 0))
    v = k.voronoi(14.0, 'DISTANCE_TO_EDGE', 0.9, vec=mpc)
    crack = k.math('LESS_THAN', (v, 'Distance'), 0.012)
    colour = k.mix(k.math('MULTIPLY', crack, 0.8), body, (0.01, 0.007, 0.005))
    colour = k.mix((b, 'Factor'), colour, (0.008, 0.006, 0.005))
    height = k.math('ADD', k.math('MULTIPLY', k.math('SUBTRACT', 1.0, (b, 'Factor')), 0.3), k.math('ADD', k.math('MULTIPLY', mixg, 0.35), k.math('MULTIPLY', crack, -0.25)))
    height = k.math('ADD', height, 0.25)
    finish(w, colour, height, rough=0.9)


# ------------------------------------------------------------------------------------------------------------- metal
def make_metal(k, w):
    b = k.brick(1.0, 0.5, 0.5, 0.012, smooth=0.006, offset=0.0, c1=(1.0, 1.0, 1.0), c2=(0.85, 0.85, 0.85), cm=(0, 0, 0))
    streak = k.noise(8.0, 6.0, 0.6, stretch=(10.0, 1.0, 1.0))
    base = k.ramp(k.remap(streak, 0.35, 0.65), [(0.0, (0.02, 0.022, 0.026)), (0.5, (0.036, 0.036, 0.04)), (1.0, (0.06, 0.06, 0.058))])
    rust_n = k.noise(7.0, 8.0, 0.62)
    drip = k.noise(5.0, 5.0, 0.6, stretch=(9.0, 0.7, 1.0), offset=(1.0, 2.0, 0))
    rust_field = k.math('ADD', k.math('MULTIPLY', rust_n, 0.65), k.math('MULTIPLY', drip, 0.35))
    rust_mask = k.remap(rust_field, 0.5, 0.62, 0.0, 1.0, 'SMOOTHSTEP')
    rust = k.ramp(k.remap(k.noise(25.0, 4.0, 0.6), 0.3, 0.7), [(0.0, (0.049, 0.023, 0.015)), (0.5, (0.097, 0.042, 0.02)), (1.0, (0.19, 0.08, 0.03))])
    painted = k.mix(rust_mask, base, rust)
    # rivets on a regular grid: Voronoi with Randomness 0
    v = k.voronoi(5.0, 'F1', 0.0)
    rivet = k.math('LESS_THAN', (v, 'Distance'), 0.09)
    rivet_shade = k.remap((v, 'Distance'), 0.0, 0.09, 0.9, 0.2)
    rivet_col = k.mix(rivet_shade, (0.03, 0.028, 0.026), (0.11, 0.085, 0.07))
    colour = k.mix(rivet, painted, rivet_col)
    colour = k.mix((b, 'Factor'), colour, (0.006, 0.006, 0.006))
    height = k.math('ADD', k.math('ADD', k.math('MULTIPLY', k.math('SUBTRACT', 1.0, (b, 'Factor')), 0.25), k.math('MULTIPLY', rivet, 0.25)), k.math('ADD', k.math('MULTIPLY', rust_mask, -0.1), 0.4))
    rough = k.math('ADD', 0.45, k.math('MULTIPLY', rust_mask, 0.4))
    metal = k.math('SUBTRACT', 0.9, k.math('MULTIPLY', rust_mask, 0.9))
    finish(w, colour, height, rough=rough, metal=metal)


# ------------------------------------------------------------------------------------------------------------- mud
def make_mud(k, w):
    warp = k.noise(3.0, 3.0, 0.5)
    # ruts: wave bands bent by noise
    mp = k.mapping(scale=(0.7, 0.7, 1.0), rot=(0, 0, math.radians(35)))
    ruts = w.add(T + 'Wave', 'ruts', wave_type='BANDS', bands_direction='X', wave_profile='SIN')
    ruts.inputs['Scale'].default_value = 3.0; ruts.inputs['Distortion'].default_value = 6.0; ruts.inputs['Detail'].default_value = 2.0; ruts.inputs['Detail Scale'].default_value = 1.0
    w.link(mp[0], mp[1], 'ruts', 'Vector')
    grain = k.noise(14.0, 6.0, 0.62)
    base_t = k.mix_float(0.4, ('ruts', 'Fac'), grain)
    mud = k.ramp(k.remap(base_t, 0.25, 0.75), [(0.0, (0.035, 0.02, 0.017)), (0.35, (0.081, 0.04, 0.025)), (0.7, (0.142, 0.064, 0.035)), (1.0, (0.225, 0.106, 0.058))])
    # puddles: low parts of a big soft noise, cut with a hard edge, filled with a flat blue-grey
    pn = k.noise(2.8, 4.0, 0.55, vec=k.mapping(loc=(5.3, 1.1, 0.0)))
    puddle = k.remap(pn, 0.46, 0.50, 1.0, 0.0, 'LINEAR')
    puddle = k.math('GREATER_THAN', puddle, 0.5)
    water = k.ramp(k.remap(k.noise(5.0, 3.0, 0.5), 0.3, 0.7), [(0.0, (0.096, 0.088, 0.092)), (0.5, (0.138, 0.165, 0.182)), (1.0, (0.2, 0.23, 0.25))])
    # stones: Voronoi cells, only those with a big enough N-sphere radius become stones
    cell = k.voronoi(13.0, 'F1', 1.0)
    rad = k.voronoi(13.0, 'N_SPHERE_RADIUS', 1.0)
    inside = k.math('LESS_THAN', (cell, 'Distance'), k.math('MULTIPLY', (rad, 'Radius'), 1.6))
    big = k.math('GREATER_THAN', (rad, 'Radius'), 0.36)
    stone_mask = k.math('MULTIPLY', inside, big)
    stone = k.ramp((cell, 'Color'), [(0.0, (0.02, 0.022, 0.03)), (0.5, (0.058, 0.067, 0.073)), (1.0, (0.1, 0.07, 0.05))]) if False else k.ramp(k.remap(k.noise(18.0, 3.0, 0.5), 0.3, 0.7), [(0.0, (0.014, 0.015, 0.02)), (0.6, (0.04, 0.045, 0.055)), (1.0, (0.12, 0.12, 0.13))])
    surface = k.mix(puddle, mud, water)
    colour = k.mix(stone_mask, surface, stone)
    height = k.math('ADD', k.math('ADD', k.math('MULTIPLY', base_t, 0.25), k.math('MULTIPLY', puddle, -0.2)), k.math('ADD', k.math('MULTIPLY', stone_mask, 0.25), 0.45))
    rough = k.math('SUBTRACT', 0.85, k.math('MULTIPLY', puddle, 0.7))
    finish(w, colour, height, rough=rough)


# ------------------------------------------------------------------------------------------------------------- gravel
def make_gravel(k, w):
    soil_n = k.noise(40.0, 5.0, 0.65)
    soil = k.ramp(k.remap(soil_n, 0.3, 0.7), [(0.0, (0.05, 0.026, 0.015)), (0.5, (0.071, 0.037, 0.021)), (1.0, (0.139, 0.072, 0.039))])
    bigc = k.voronoi(8.0, 'F1', 0.9)
    bigr = k.voronoi(8.0, 'N_SPHERE_RADIUS', 0.9)
    bige = k.voronoi(8.0, 'DISTANCE_TO_EDGE', 0.9)
    # each cell: a random grey/blue/brown value from the cell colour red channel
    sep = w.add('ShaderNodeSeparateColor', 'cellrgb'); w.link(bigc, 'Color', 'cellrgb', 'Color')
    shade = ('cellrgb', 'Red')
    stone_col = k.ramp(shade, [(0.0, (0.014, 0.013, 0.013)), (0.3, (0.029, 0.029, 0.03)), (0.55, (0.058, 0.067, 0.073)), (0.8, (0.124, 0.134, 0.132)), (1.0, (0.139, 0.072, 0.039))], 'CONSTANT')
    # texture on each stone: fine noise
    tex = k.noise(60.0, 3.0, 0.6)
    stone_col = k.mix(0.25, stone_col, k.mix(k.remap(tex, 0.3, 0.7), (0.6, 0.6, 0.62), (1.4, 1.4, 1.4)), 'MULTIPLY')
    # smaller pebbles
    smallc = k.voronoi(26.0, 'F1', 1.0)
    smalle = k.voronoi(26.0, 'DISTANCE_TO_EDGE', 1.0)
    sep2 = w.add('ShaderNodeSeparateColor', 'cell2rgb'); w.link(smallc, 'Color', 'cell2rgb', 'Color')
    pebble_col = k.ramp(('cell2rgb', 'Red'), [(0.0, (0.02, 0.02, 0.022)), (0.5, (0.058, 0.067, 0.073)), (1.0, (0.139, 0.072, 0.039))], 'CONSTANT')
    big_mask = k.remap((bige, 'Distance'), 0.02, 0.05)
    small_mask = k.remap((smalle, 'Distance'), 0.015, 0.035)
    # only about 60% of cells hold a stone: use the cell colour green channel as a dice roll
    dice = k.math('GREATER_THAN', ('cellrgb', 'Green'), 0.35)
    big_on = k.math('MULTIPLY', big_mask, dice)
    base = k.mix(small_mask, soil, pebble_col)
    colour = k.mix(big_on, base, stone_col)
    height = k.math('ADD', k.math('ADD', k.math('MULTIPLY', big_on, 0.4), k.math('MULTIPLY', small_mask, 0.12)), k.math('ADD', k.math('MULTIPLY', soil_n, 0.06), 0.25))
    finish(w, colour, height, rough=0.85)
