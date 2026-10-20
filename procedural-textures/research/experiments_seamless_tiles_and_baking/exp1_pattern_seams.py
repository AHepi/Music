# What this does: experiment 1 of the seamless-tile research. It builds the same kind of pattern many different ways in Blender
# (raw Noise, Noise on a 4D donut, cross-fade repair, mirror tiling, Voronoi, Brick with whole and broken scales, a hand-made Brick
# whose random colours wrap around, Wave, Gradient, Magic, Gabor, Checker) and photographs each one flat from above as a grey picture.
# A second script (measure_seams.py, plain Python) then measures how big the jump is across the wrap-around edge.
# Run:  blender -b --disable-autoexec -t 2 --python exp1_pattern_seams.py -- [size]
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

size = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else 512


# ------------------------------------------------------------------ small helpers for writing math by name
def mth(w, name, op, a, b=None, clamp=False):
    """Adds a Math node. a and b are numbers or (node_name, socket) pairs. Returns (name, 0) to link further."""
    node = w.math(name, op, None, None, clamp=clamp)
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (int, float)):
            node.inputs[index].default_value = float(value)
        else:
            w.link(value[0], value[1], name, index)
    return (name, 0)


def combine_xy(w, name, x, y):
    w.add('ShaderNodeCombineXYZ', name)
    for socket, value in (('X', x), ('Y', y)):
        if isinstance(value, (int, float)):
            w.nodes[name].inputs[socket].default_value = float(value)
        else:
            w.link(value[0], value[1], name, socket)
    return (name, 'Vector')


def uv(w):
    w.add('ShaderNodeSeparateXYZ', 'uv', x=-3)
    w.link('in', 'Vector', 'uv', 'Vector')
    return ('uv', 'X'), ('uv', 'Y')


def tileable_noise_node(w, name, vec, scale, detail=4.0, distortion=0.0, seed=0.0):
    g = ec.rt.tileable_noise_group()
    node = w.add('ShaderNodeGroup', name)
    node.node_tree = g
    w.link(vec[0], vec[1], name, 'Vector')
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    node.inputs['Distortion'].default_value = distortion
    node.inputs['Seed'].default_value = seed
    return (name, 'Fac')


# ------------------------------------------------------------------ pattern functions: evaluate one pattern at a given vector
def raw_noise_fn(scale=5.0, detail=4.0):
    def fn(w, tag, vec):
        w.add('ShaderNodeTexNoise', 'n_' + tag, noise_dimensions='3D', noise_type='FBM', normalize=True, Scale=scale, Detail=detail)
        w.link(vec[0], vec[1], 'n_' + tag, 'Vector')
        return ('n_' + tag, 'Fac')
    return fn


def raw_gabor_fn(scale=6.0):
    def fn(w, tag, vec):
        w.add('ShaderNodeTexGabor', 'g_' + tag, gabor_type='2D', Scale=scale, Frequency=2.0, Anisotropy=1.0, Orientation=0.6)
        w.link(vec[0], vec[1], 'g_' + tag, 'Vector')
        half = mth(w, 'gh_' + tag, 'MULTIPLY_ADD', ('g_' + tag, 'Value'), 0.5)
        w.nodes['gh_' + tag].inputs[2].default_value = 0.5
        return half
    return fn


def raw_voronoi_fn(scale=6.0):
    def fn(w, tag, vec):
        w.add('ShaderNodeTexVoronoi', 'v_' + tag, voronoi_dimensions='3D', feature='F1', Scale=scale, Randomness=1.0)
        w.link(vec[0], vec[1], 'v_' + tag, 'Vector')
        return ('v_' + tag, 'Distance')
    return fn


# ------------------------------------------------------------------ builders (each returns build(w) for ec.pattern_group)
def build_plain(fn):
    def build(w):
        return fn(w, 'a', ('in', 'Vector'))
    return build


def build_crossfade(fn, mode='power'):
    """Offset-and-blend repair: g(u,v) = sum over a,b in {0,1} of weight_a(u) * weight_b(v) * f(u-a, v-b).
    mode 'linear': weights (1-u, u). mode 'power': weights (cos(pi/2 u), sin(pi/2 u)) which keep the contrast (cos^2 + sin^2 = 1)."""
    def build(w):
        u, v = uv(w)
        def weights(coord, label):
            if mode == 'linear':
                w0 = mth(w, f'w0{label}', 'SUBTRACT', 1.0, coord)
                w1 = (coord[0], coord[1])
            else:
                half_pi = mth(w, f'hp{label}', 'MULTIPLY', coord, math.pi / 2)
                w0 = mth(w, f'w0{label}', 'COSINE', half_pi)
                w1 = mth(w, f'w1{label}', 'SINE', half_pi)
            return w0, w1
        wu = weights(u, 'u')
        wv = weights(v, 'v')
        total = None
        for a in (0, 1):
            for b in (0, 1):
                su = mth(w, f'su{a}{b}', 'SUBTRACT', u, float(a))
                sv = mth(w, f'sv{a}{b}', 'SUBTRACT', v, float(b))
                vec = combine_xy(w, f'cv{a}{b}', su, sv)
                value = fn(w, f'{a}{b}', vec)
                centred = mth(w, f'c{a}{b}', 'SUBTRACT', value, 0.5)
                weight = mth(w, f'wt{a}{b}', 'MULTIPLY', wu[a], wv[b])
                term = mth(w, f't{a}{b}', 'MULTIPLY', centred, weight)
                total = term if total is None else mth(w, f'sum{a}{b}', 'ADD', total, term)
        return mth(w, 'recentre', 'ADD', total, 0.5)
    return build


def build_mirror(fn):
    """Mirror tiling: feed the pattern with a triangle wave of u and v so the picture is its own mirror image at every edge."""
    def build(w):
        u, v = uv(w)
        tu = mth(w, 'tu', 'PINGPONG', mth(w, 'u2', 'MULTIPLY', u, 2.0), 1.0)
        tv = mth(w, 'tv', 'PINGPONG', mth(w, 'v2', 'MULTIPLY', v, 2.0), 1.0)
        vec = combine_xy(w, 'mir', tu, tv)
        return fn(w, 'm', vec)
    return build


def build_donut_noise(scale=5.0, detail=4.0, distortion=0.0):
    def build(w):
        return tileable_noise_node(w, 'tn', ('in', 'Vector'), scale, detail, distortion)
    return build


def build_donut_voronoi(scale=6.0):
    def build(w):
        g = ec.rt.tileable_voronoi_group()
        w.add('ShaderNodeGroup', 'tv')
        w.nodes['tv'].node_tree = g
        w.link('in', 'Vector', 'tv', 'Vector')
        w.nodes['tv'].inputs['Scale'].default_value = scale
        return ('tv', 'Distance')
    return build


def build_brick_node(scale=4.0, offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2, output='Color', width=0.5, height=0.25, warp=0.0):
    def build(w):
        vec = ('in', 'Vector')
        if warp:
            u, v = uv(w)
            noise = tileable_noise_node(w, 'warpn', ('in', 'Vector'), 3.0, 3.0)
            du = mth(w, 'du', 'MULTIPLY_ADD', mth(w, 'nc', 'SUBTRACT', noise, 0.5), warp)
            w.nodes['du'].inputs[2].default_value = 0.0
            nu = mth(w, 'nu', 'ADD', u, du)
            vec = combine_xy(w, 'warped', nu, v)
        w.add('ShaderNodeTexBrick', 'brick', offset=offset, offset_frequency=offset_frequency, squash=squash, squash_frequency=squash_frequency,
              Scale=scale, Mortar__Size=0.03, Mortar__Smooth=0.0, Bias=0.0, Brick__Width=width, Row__Height=height,
              Color1=(0.1, 0.1, 0.1, 1), Color2=(0.9, 0.9, 0.9, 1), Mortar=(0.0, 0.0, 0.0, 1))
        w.link(vec[0], vec[1], 'brick', 'Vector')
        if output == 'Factor':
            return ('brick', 'Factor')
        w.add('ShaderNodeRGBToBW', 'bw')
        w.link('brick', 'Color', 'bw', 'Color')
        return ('bw', 'Val')
    return build


def build_brick_wrapped(bricks_across=8, rows=16, mortar=0.006, offset=0.5):
    """A brick wall made from plain maths so that the random value of each brick wraps around with the tile:
    the brick number across is taken 'modulo bricks_across', so the half brick on the right edge gets the same random value as the half
    brick on the left edge. rows must be even when the offset is 0.5."""
    def build(w):
        u, v = uv(w)
        y = mth(w, 'y', 'MULTIPLY', v, float(rows))
        row = mth(w, 'row', 'FLOOR', y)
        fy = mth(w, 'fy', 'FRACT', y)
        odd = mth(w, 'odd', 'FLOORED_MODULO', row, 2.0)
        shift = mth(w, 'shift', 'MULTIPLY', odd, offset)
        x = mth(w, 'x', 'MULTIPLY', u, float(bricks_across))
        xs = mth(w, 'xs', 'ADD', x, shift)
        col = mth(w, 'col', 'FLOOR', xs)
        fx = mth(w, 'fx', 'FRACT', xs)
        col_wrapped = mth(w, 'colw', 'FLOORED_MODULO', col, float(bricks_across))
        w.add('ShaderNodeCombineXYZ', 'id')
        w.link(col_wrapped[0], col_wrapped[1], 'id', 'X')
        row_wrapped = mth(w, 'roww', 'FLOORED_MODULO', row, float(rows))
        w.link(row_wrapped[0], row_wrapped[1], 'id', 'Y')
        w.nodes['id'].inputs['Z'].default_value = 3.7
        w.add('ShaderNodeTexWhiteNoise', 'rand', noise_dimensions='3D')
        w.link('id', 'Vector', 'rand', 'Vector')
        # distance to the nearest brick edge, in tile units (so mortar has the same width in both directions)
        dx = mth(w, 'dx', 'DIVIDE', mth(w, 'mx', 'MINIMUM', fx, mth(w, 'ifx', 'SUBTRACT', 1.0, fx)), float(bricks_across))
        dy = mth(w, 'dy', 'DIVIDE', mth(w, 'my', 'MINIMUM', fy, mth(w, 'ify', 'SUBTRACT', 1.0, fy)), float(rows))
        edge = mth(w, 'edge', 'MINIMUM', dx, dy)
        mask = mth(w, 'mask', 'GREATER_THAN', edge, mortar)
        shade = mth(w, 'shade', 'MULTIPLY_ADD', ('rand', 'Value'), 0.7)
        w.nodes['shade'].inputs[2].default_value = 0.2
        return mth(w, 'brickvalue', 'MULTIPLY', mask, shade)
    return build


def build_wave(scale=1.0, wave_type='BANDS', profile='SIN', direction='X', distortion=0.0, detail=2.0, warp_tileable=0.0, rings_direction='X'):
    def build(w):
        vec = ('in', 'Vector')
        if warp_tileable:
            u, v = uv(w)
            noise = tileable_noise_node(w, 'warpn', ('in', 'Vector'), 3.0, 3.0)
            du = mth(w, 'du', 'MULTIPLY', mth(w, 'nc', 'SUBTRACT', noise, 0.5), warp_tileable)
            vec = combine_xy(w, 'warped', mth(w, 'nu', 'ADD', u, du), v)
        w.add('ShaderNodeTexWave', 'wave', wave_type=wave_type, bands_direction=direction, rings_direction=rings_direction, wave_profile=profile,
              Scale=scale, Distortion=distortion, Detail=detail, Detail__Scale=1.0, Detail__Roughness=0.5, Phase__Offset=0.0)
        w.link(vec[0], vec[1], 'wave', 'Vector')
        return ('wave', 'Factor')
    return build


def build_gradient(kind='LINEAR', pingpong=False):
    def build(w):
        vec = ('in', 'Vector')
        w.add('ShaderNodeTexGradient', 'grad', gradient_type=kind)
        w.link(vec[0], vec[1], 'grad', 'Vector')
        if pingpong:
            return mth(w, 'pp', 'PINGPONG', mth(w, 'x2', 'MULTIPLY', ('grad', 'Factor'), 2.0), 1.0)
        return ('grad', 'Factor')
    return build


def build_magic(scale=2.0, depth=2, distortion=1.0):
    def build(w):
        w.add('ShaderNodeTexMagic', 'magic', turbulence_depth=depth, Scale=scale, Distortion=distortion)
        w.link('in', 'Vector', 'magic', 'Vector')
        return ('magic', 'Factor')
    return build


def build_checker(scale=8.0):
    def build(w):
        w.add('ShaderNodeTexChecker', 'chk', Scale=scale, Color1=(1, 1, 1, 1), Color2=(0, 0, 0, 1))
        w.link('in', 'Vector', 'chk', 'Vector')
        return ('chk', 'Factor')
    return build


K_WAVE = math.pi / 10.0   # Wave Texture: one band = 2*pi/20 in scaled units, so scale = k * pi / 10 puts k whole bands across the tile (tested below)
K_MAGIC = 2.0 * math.pi / 5.0

patterns = {
    # noise
    'noise_raw3d': build_plain(raw_noise_fn(5.0)),
    'noise_donut4d': build_donut_noise(5.0, 4.0, 0.0),
    'noise_donut4d_distortion1': build_donut_noise(5.0, 4.0, 1.0),
    'noise_crossfade_linear': build_crossfade(raw_noise_fn(5.0), 'linear'),
    'noise_crossfade_power': build_crossfade(raw_noise_fn(5.0), 'power'),
    'noise_mirror': build_mirror(raw_noise_fn(2.5)),
    # voronoi
    'voronoi_raw3d': build_plain(raw_voronoi_fn(6.0)),
    'voronoi_donut_s6': build_donut_voronoi(6.0),
    'voronoi_donut_s2': build_donut_voronoi(2.0),
    # brick
    'brick_color_scale4': build_brick_node(4.0),
    'brick_factor_scale4': build_brick_node(4.0, output='Factor'),
    'brick_color_scale4p3': build_brick_node(4.3),
    'brick_factor_scale4p3': build_brick_node(4.3, output='Factor'),
    'brick_color_offset0': build_brick_node(4.0, offset=0.0),
    'brick_factor_squash_bad': build_brick_node(4.0, squash=0.62, squash_frequency=3, output='Factor'),
    'brick_factor_squash_ok': build_brick_node(3.0, squash=0.62, squash_frequency=3, output='Factor'),
    'brick_factor_squash_whole': build_brick_node(3.0, squash=0.75, squash_frequency=3, output='Factor'),
    'brick_color_squash_whole': build_brick_node(3.0, squash=0.75, squash_frequency=3, output='Color'),
    'brick_factor_warped': build_brick_node(4.0, output='Factor', warp=0.15),
    'brick_wrapped_hash': build_brick_wrapped(8, 16),
    # wave
    'wave_bands_scale3': build_wave(3.0),
    'wave_bands_whole_k3': build_wave(3 * K_WAVE),
    'wave_bands_whole_k3_distortion2': build_wave(3 * K_WAVE, distortion=2.0),
    'wave_bands_whole_k3_tileable_warp': build_wave(3 * K_WAVE, warp_tileable=0.15),
    'wave_saw_whole_k3': build_wave(3 * K_WAVE, profile='SAW'),
    'wave_rings': build_wave(1.0, wave_type='RINGS', rings_direction='SPHERICAL'),
    # gradient
    'gradient_linear': build_gradient('LINEAR'),
    'gradient_linear_pingpong': build_gradient('LINEAR', pingpong=True),
    'gradient_spherical': build_gradient('SPHERICAL'),
    'gradient_radial_angle': build_gradient('RADIAL'),
    # magic
    'magic_scale2': build_magic(2.0),
    'magic_whole_k2': build_magic(2 * K_MAGIC),
    # gabor
    'gabor_raw': build_plain(raw_gabor_fn(6.0)),
    'gabor_crossfade_power': build_crossfade(raw_gabor_fn(6.0), 'power'),
    # checker
    'checker_even8': build_checker(8.0),
    'checker_odd7': build_checker(7.0),
}

only = [a for a in sys.argv[sys.argv.index('--') + 1:] if a.startswith('only=')] if '--' in sys.argv else []
if only:
    keep = only[0][5:].split(',')
    patterns = {k: v for k, v in patterns.items() if k in keep}

folder = os.path.join(ec.OUT, 'patterns')
paths = ec.render_patterns(patterns, folder, size=size, sixteen=True)
print('[exp1] wrote', len(paths), 'pictures to', folder)
if 'shift' in sys.argv:
    # the exact test: the same pattern with its coordinates moved by one whole tile in x, in y and in both
    offsets = {'plus_x': (1.0, 0.0, 0.0), 'plus_y': (0.0, 1.0, 0.0), 'plus_xy': (1.0, 1.0, 0.0), 'minus_xy_3_2': (-3.0, 2.0, 0.0)}
    ec.render_patterns_shifted(patterns, os.path.join(ec.OUT, 'patterns_shift'), offsets, size=size, sixteen=True)
    print('[exp1] wrote shifted pictures')
