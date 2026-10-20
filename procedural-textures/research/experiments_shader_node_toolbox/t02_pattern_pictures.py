# What this does: renders the "pattern maker" pictures for the guide: every pattern node and what its main settings do.
# Run: blender -b --disable-autoexec -t 2 --python t02_pattern_pictures.py -- [only_name ...]    Pictures go to pictures/*.png
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import probe_tools as pt
from sweeps import sweep
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def want(n): return not only or n in only
D = 'ShaderNodeTex'

# ---- gradient types ---------------------------------------------------------------------------------------
if want('p01_gradient_types'):
    types = ['LINEAR', 'QUADRATIC', 'EASING', 'DIAGONAL', 'SPHERICAL', 'QUADRATIC_SPHERE', 'RADIAL']
    def body(w, t):
        w.add('ShaderNodeMapping', 'centre', x=-1, vector_type='POINT')
        w.nodes['centre'].inputs['Location'].default_value = (-0.5, -0.5, 0)   # move 0..1 to -0.5..0.5 so the middle is the origin
        w.link('in', 'Vector', 'centre', 'Vector')
        w.add(D + 'Gradient', 'g', x=0, gradient_type=t)
        if t in ('LINEAR', 'QUADRATIC', 'EASING', 'DIAGONAL'):
            w.nodes['centre'].inputs['Location'].default_value = (0, 0, 0)          # these start at x = 0
        w.link('centre', 'Vector', 'g', 'Vector')
        w.link('g', 'Fac', 'out', 'Height')
    sweep('p01_gradient_types', body, types, [t.replace('_', ' ').title() for t in types], columns=4, size=192,
          title='Gradient Texture: Gradient Type')

# ---- noise types ------------------------------------------------------------------------------------------
if want('p02_noise_types'):
    types = ['FBM', 'MULTIFRACTAL', 'RIDGED_MULTIFRACTAL', 'HYBRID_MULTIFRACTAL', 'HETERO_TERRAIN']
    def body(w, t):
        n = w.add(D + 'Noise', 'n', x=0, noise_type=t, Scale=5.0, Detail=6.0, Roughness=0.55)
        for s in n.inputs:
            if s.identifier == 'Offset' and s.enabled: s.default_value = 1.0
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('p02_noise_types', body, types, ['fBM', 'Multifractal', 'Ridged (Offs 1)', 'Hybrid (Offs 1)', 'Hetero (Offs 1)'],
          stretch=True, columns=5, size=192, title='Noise Texture: Noise Type (stretched)')
if want('p02b_noise_ridged_offset'):
    def body(w, off):
        n = w.add(D + 'Noise', 'n', x=0, noise_type='RIDGED_MULTIFRACTAL', Scale=4.0, Detail=6.0, Roughness=0.6)
        for s in n.inputs:
            if s.identifier == 'Offset': s.default_value = off
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('p02b_noise_ridged_offset', body, [0.0, 0.5, 1.0, 1.5], ['Offset 0 (default)', 'Offset 0.5', 'Offset 1', 'Offset 1.5'],
          stretch=True, columns=4, size=192, title='Ridged Multifractal: Offset')

def noise_sweep(name, socket, values, extra=None, labels=None, title=None, stretch=False, noise_type='FBM', **fixed):
    def body(w, v):
        n = w.add(D + 'Noise', 'n', x=0, noise_type=noise_type, normalize=True)
        for k, val in {**dict(Scale=5.0, Detail=4.0, Roughness=0.5, Lacunarity=2.0, Distortion=0.0), **(extra or {})}.items():
            n.inputs[k].default_value = val
        n.inputs[socket].default_value = v
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep(name, body, values, labels or [f'{socket} {v}' for v in values], columns=len(values), size=192,
          title=title or f'Noise Texture: {socket}', stretch=stretch)
if want('p03_noise_detail'): noise_sweep('p03_noise_detail', 'Detail', [0, 1, 2, 4, 8, 15], extra=dict(Roughness=0.6), stretch=True, title='Noise: Detail (fBM, Roughness 0.6)')
if want('p04_noise_roughness'): noise_sweep('p04_noise_roughness', 'Roughness', [0.0, 0.25, 0.5, 0.75, 1.0], extra=dict(Detail=6.0), stretch=True, title='Noise: Roughness (fBM, Detail 6)')
if want('p05_noise_lacunarity'): noise_sweep('p05_noise_lacunarity', 'Lacunarity', [1.2, 2.0, 3.0, 5.0], extra=dict(Detail=5.0, Roughness=0.6), stretch=True, title='Noise: Lacunarity (fBM, Detail 5)')
if want('p06_noise_distortion'): noise_sweep('p06_noise_distortion', 'Distortion', [0.0, 0.5, 1.0, 2.0, 4.0], extra=dict(Detail=2.0), stretch=True, title='Noise: Distortion (fBM, Detail 2)')
if want('p07_noise_scale'): noise_sweep('p07_noise_scale', 'Scale', [1, 3, 6, 12, 24], extra=dict(Detail=2.0), stretch=True, title='Noise: Scale (fBM, Detail 2)')
if want('p08_noise_4d_w'):
    def body(w, wv):
        n = w.add(D + 'Noise', 'n', x=0, noise_dimensions='4D', Scale=4.0, Detail=3.0)
        n.inputs[1].default_value = wv
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    sweep('p08_noise_4d_w', body, [0.0, 0.1, 0.25, 0.5, 1.0], ['W = 0', 'W = 0.1', 'W = 0.25', 'W = 0.5', 'W = 1'], stretch=True, size=192, title='Noise Texture 4D: the W input')

# ---- voronoi ----------------------------------------------------------------------------------------------
def vor(w, **kw):
    v = w.add(D + 'Voronoi', 'v', x=0, **{k: val for k, val in kw.items() if k in ('feature', 'distance', 'voronoi_dimensions', 'normalize')})
    for k, val in kw.items():
        if k not in ('feature', 'distance', 'voronoi_dimensions', 'normalize'):
            v.inputs[k].default_value = val
    w.link('in', 'Vector', 'v', 'Vector')
    return v
if want('p10_voronoi_features'):
    feats = ['F1', 'F2', 'SMOOTH_F1', 'DISTANCE_TO_EDGE', 'N_SPHERE_RADIUS']
    def body(w, f):
        v = vor(w, feature=f, Scale=5.0)
        w.link('v', 'Radius' if f == 'N_SPHERE_RADIUS' else 'Distance', 'out', 'Height')
    sweep('p10_voronoi_features', body, feats, ['F1', 'F2', 'Smooth F1', 'Distance to Edge', 'N-Sphere Radius'], columns=5, size=192,
          title='Voronoi Texture: Feature (Distance out)', stretch=False)
if want('p10b_voronoi_features_color'):
    feats = [('F1', 'Color'), ('F2', 'Color'), ('SMOOTH_F1', 'Color'), ('F1', 'Position')]
    def body(w, fo):
        f, o = fo
        v = vor(w, feature=f, Scale=5.0)
        w.link('v', o, 'out', 'Colour')
    sweep('p10b_voronoi_features_color', body, feats, ['F1 Color', 'F2 Color', 'Smooth F1 Color', 'F1 Position'], channel='Colour', columns=4, size=192,
          title='Voronoi: Color and Position outputs')
if want('p11_voronoi_metrics'):
    cases = [('EUCLIDEAN', None), ('MANHATTAN', None), ('CHEBYCHEV', None), ('MINKOWSKI', 0.5), ('MINKOWSKI', 1.5), ('MINKOWSKI', 4.0)]
    def body(w, c):
        d, e = c
        v = vor(w, distance=d, Scale=5.0)
        if e is not None: v.inputs['Exponent'].default_value = e
        w.link('v', 'Distance', 'out', 'Height')
    sweep('p11_voronoi_metrics', body, cases, ['Euclidean', 'Manhattan', 'Chebychev', 'Mink 0.5', 'Mink 1.5', 'Mink 4'], columns=6, size=128,
          title='Voronoi: Distance Metric (F1 distance)')
if want('p12_voronoi_randomness'):
    def body(w, r):
        v = vor(w, Scale=5.0, Randomness=r)
        w.link('v', 'Distance', 'out', 'Height')
    sweep('p12_voronoi_randomness', body, [0.0, 0.25, 0.5, 1.0], ['Randomness 0', 'Randomness 0.25', 'Randomness 0.5', 'Randomness 1'], columns=4, size=192, title='Voronoi: Randomness')
if want('p13_voronoi_smoothness'):
    def body(w, s):
        v = vor(w, feature='SMOOTH_F1', Scale=5.0, Smoothness=s)
        w.link('v', 'Distance', 'out', 'Height')
    sweep('p13_voronoi_smoothness', body, [0.0, 0.25, 0.5, 1.0], ['Smoothness 0', 'Smoothness 0.25', 'Smoothness 0.5', 'Smoothness 1'], columns=4, size=192, title='Voronoi Smooth F1: Smoothness')
if want('p14_voronoi_detail'):
    def body(w, d):
        v = vor(w, Scale=4.0, Detail=d, Roughness=0.6)
        w.link('v', 'Distance', 'out', 'Height')
    sweep('p14_voronoi_detail', body, [0, 1, 2, 4], ['Detail 0', 'Detail 1', 'Detail 2', 'Detail 4'], columns=4, size=192, title='Voronoi: Detail (Roughness 0.6)')
if want('p15_voronoi_edge'):
    def body(w, thr):
        v = vor(w, feature='DISTANCE_TO_EDGE', Scale=5.0)
        w.math('lt', 'LESS_THAN', None, thr, x=1); w.link('v', 'Distance', 'lt', 0)
        w.link('lt', 0, 'out', 'Height')
    sweep('p15_voronoi_edge', body, [0.02, 0.05, 0.1, 0.2], ['edge < 0.02', 'edge < 0.05', 'edge < 0.1', 'edge < 0.2'], columns=4, size=192, title='Distance to Edge + Less Than')

# ---- brick ------------------------------------------------------------------------------------------------
if want('p20_brick_settings'):
    base = dict(Scale=5.0, Mortar_Size=0.03, Mortar_Smooth=0.0, Bias=0.0)
    cases = [('Mortar Size', 0.0), ('Mortar Size', 0.02), ('Mortar Size', 0.05), ('Mortar Size', 0.1),
             ('Mortar Smooth', 0.0), ('Mortar Smooth', 0.25), ('Mortar Smooth', 0.5), ('Mortar Smooth', 1.0),
             ('Bias', -1.0), ('Bias', -0.4), ('Bias', 0.0), ('Bias', 0.6),
             ('offset', 0.0), ('offset', 0.25), ('offset', 0.5), ('offset', 0.75)]
    def body(w, c):
        name, val = c
        b = w.add(D + 'Brick', 'b', x=0, offset=0.5)
        b.inputs['Scale'].default_value = 3.0; b.inputs['Mortar Size'].default_value = 0.03; b.inputs['Mortar Smooth'].default_value = 0.0
        b.inputs['Color1'].default_value = (0.8, 0.8, 0.8, 1); b.inputs['Color2'].default_value = (0.25, 0.25, 0.25, 1); b.inputs['Mortar'].default_value = (0.02, 0.02, 0.02, 1)
        if name == 'offset': b.offset = val
        else: b.inputs[name].default_value = val
        w.link('in', 'Vector', 'b', 'Vector'); w.link('b', 'Color', 'out', 'Colour')
    sweep('p20_brick_settings', body, cases, [f'{n} {v}' for n, v in cases], channel='Colour', columns=4, size=192,
          title='Brick: Mortar Size / Smooth / Bias / Offset')
if want('p21_brick_layout'):
    cases = [('squash', 1.0, 2), ('squash', 0.5, 2), ('squash', 1.5, 3), ('Row Height', 0.15, 2), ('Brick Width', 0.8, 2), ('offset_frequency', 3, 2)]
    def body(w, c):
        name, val, freq = c
        b = w.add(D + 'Brick', 'b', x=0)
        b.inputs['Scale'].default_value = 3.0; b.inputs['Mortar Size'].default_value = 0.03
        b.inputs['Color1'].default_value = (0.8, 0.8, 0.8, 1); b.inputs['Color2'].default_value = (0.25, 0.25, 0.25, 1); b.inputs['Mortar'].default_value = (0.02, 0.02, 0.02, 1)
        if name == 'squash':
            b.squash = val; b.squash_frequency = freq
        elif name == 'offset_frequency': b.offset_frequency = val
        else: b.inputs[name].default_value = val
        w.link('in', 'Vector', 'b', 'Vector'); w.link('b', 'Color', 'out', 'Colour')
    sweep('p21_brick_layout', body, cases, ['Squash 1 (default)', 'Squash 0.5, freq 2', 'Squash 1.5, freq 3', 'Row Height 0.15', 'Brick Width 0.8', 'Offset Frequency 3'], channel='Colour', columns=3, size=192, title='Brick: layout settings')

# ---- checker / magic / wave / white noise / gabor ---------------------------------------------------------
if want('p30_magic'):
    cases = [(0, 1.0), (1, 1.0), (2, 1.0), (5, 1.0), (2, 4.0), (10, 4.0)]
    def body(w, c):
        m = w.add(D + 'Magic', 'm', x=0, turbulence_depth=c[0], Scale=3.0, Distortion=c[1])
        w.link('in', 'Vector', 'm', 'Vector'); w.link('m', 'Color', 'out', 'Colour')
    sweep('p30_magic', body, cases, [f'Depth {d}, Distort {x}' for d, x in cases], channel='Colour', columns=3, size=192, title='Magic Texture')
if want('p31_wave'):
    cases = [('BANDS', 'SIN', 0.0), ('BANDS', 'SAW', 0.0), ('BANDS', 'TRI', 0.0), ('RINGS', 'SIN', 0.0), ('BANDS', 'SIN', 5.0), ('BANDS', 'SAW', 12.0)]
    def body(w, c):
        wt, prof, dist = c
        n = w.add(D + 'Wave', 'wv', x=0, wave_type=wt, wave_profile=prof, bands_direction='Y' if wt == 'BANDS' else 'X', rings_direction='SPHERICAL')
        n.inputs['Scale'].default_value = 3.0; n.inputs['Distortion'].default_value = dist; n.inputs['Detail'].default_value = 3.0; n.inputs['Detail Scale'].default_value = 1.5
        if wt == 'RINGS':
            w.add('ShaderNodeMapping', 'centre', x=-1); w.nodes['centre'].inputs['Location'].default_value = (-0.5, -0.5, 0)
            w.link('in', 'Vector', 'centre', 'Vector'); w.link('centre', 'Vector', 'wv', 'Vector')
        else:
            w.link('in', 'Vector', 'wv', 'Vector')
        w.link('wv', 'Fac', 'out', 'Height')
    sweep('p31_wave', body, cases, ['Bands, Sine', 'Bands, Saw', 'Bands, Triangle', 'Rings, Sine', 'Distort 5, Sine', 'Distort 12, Saw'], columns=3, size=192, title='Wave Texture')
if want('p32_white_noise'):
    def body(w, d):
        n = w.add(D + 'WhiteNoise', 'n', x=0, noise_dimensions=d)
        w.add('ShaderNodeVectorMath', 'snap', x=-1, operation='SNAP'); w.nodes['snap'].inputs[1].default_value = (1/24, 1/24, 1/24)
        w.link('in', 'Vector', 'snap', 0); w.link('snap', 0, 'n', 0)
        w.link('n', 'Value', 'out', 'Height')
    sweep('p32_white_noise', body, ['3D'], ['White Noise on Snapped coordinates'], columns=1, size=192, title='White Noise on snapped blocks')
if want('p33_gabor'):
    cases = [('Value', 2.0, 1.0, 0.7854), ('Phase', 2.0, 1.0, 0.7854), ('Intensity', 2.0, 1.0, 0.7854), ('Value', 5.0, 1.0, 0.7854), ('Value', 2.0, 0.4, 0.7854), ('Value', 2.0, 0.0, 0.0), ('Value', 2.0, 1.0, 1.5708)]
    def body(w, c):
        out, freq, an, ori = c
        g = w.add(D + 'Gabor', 'g', x=0, gabor_type='2D')
        g.inputs['Scale'].default_value = 6.0; g.inputs['Frequency'].default_value = freq; g.inputs['Anisotropy'].default_value = an
        for s in g.inputs:
            if s.identifier.startswith('Orientation') and s.enabled and s.type == 'VALUE': s.default_value = ori
        w.link('in', 'Vector', 'g', 'Vector'); w.link('g', out, 'out', 'Height')
    sweep('p33_gabor', body, cases, ['Value', 'Phase', 'Intensity', 'Frequency 5', 'Anisotropy 0.4', 'Anisotropy 0', 'Orientation 90'], stretch=True, columns=4, size=192, title='Gabor Texture (2D, stretched)')
if want('p34_checker'):
    def body(w, s):
        c = w.add(D + 'Checker', 'c', x=0, Scale=s)
        c.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1); c.inputs['Color2'].default_value = (0.1, 0.1, 0.1, 1)
        w.link('in', 'Vector', 'c', 'Vector'); w.link('c', 'Color', 'out', 'Colour')
    sweep('p34_checker', body, [4, 8, 16], ['Scale 4', 'Scale 8', 'Scale 16'], channel='Colour', columns=3, size=192, title='Checker Texture: Scale')
if want('p35_radial_tiling'):
    cases = [(5.0, 0.0), (5.0, 1.0), (6.0, 0.5), (5.5, 0.0), (8.0, 0.0)]
    def body(w, c):
        sides, rnd = c
        w.add('ShaderNodeMapping', 'centre', x=-2); w.nodes['centre'].inputs['Location'].default_value = (-0.5, -0.5, 0)
        w.link('in', 'Vector', 'centre', 'Vector')
        r = w.add('ShaderNodeRadialTiling', 'r', x=-1, Sides=sides, Roundness=rnd, normalize=True)
        w.link('centre', 'Vector', 'r', 0)
        k = w.add(D + 'Checker', 'k', x=0, Scale=6.0)
        k.inputs['Color1'].default_value = (0.9, 0.9, 0.9, 1); k.inputs['Color2'].default_value = (0.15, 0.15, 0.15, 1)
        w.link('r', 'Segment Coordinates', 'k', 'Vector'); w.link('k', 'Color', 'out', 'Colour')
    sweep('p35_radial_tiling', body, cases, ['Sides 5', 'Sides 5, Round 1', 'Sides 6, Round 0.5', 'Sides 5.5', 'Sides 8'], channel='Colour', columns=5, size=192, title='Radial Tiling: a Checker inside each segment')
print('done pictures')
