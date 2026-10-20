# What this does: measures EXACTLY which pattern nodes repeat perfectly when the tile coordinate goes up by 1 (the web claim "procedural
# nodes wrap seamlessly at whole-number UV values"). Each pattern is drawn at (u, v) and again at (u + 1, v) and (u, v + 1); if the two
# pictures are the same, the pattern tiles. Writes which_patterns_wrap.json
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
D = 'ShaderNodeTex'
R = {}
def test(make, channel='Height', size=160):
    """make(w, src) builds the pattern from coordinate source src = (node, socket) and links its result to out.Height"""
    def build(dx, dy):
        def body(w):
            w.add('ShaderNodeVectorMath', 'shift', x=-5, operation='ADD'); w.nodes['shift'].inputs[1].default_value = (dx, dy, 0.0)
            w.link('in', 'Vector', 'shift', 0)
            make(w, ('shift', 0))
        return body
    base = pt.render_float(build(0.0, 0.0), channel, size)
    sx = pt.render_float(build(1.0, 0.0), channel, size); sy = pt.render_float(build(0.0, 1.0), channel, size)
    return {'u+1': round(float(np.abs(base - sx).mean()), 4), 'v+1': round(float(np.abs(base - sy).mean()), 4), 'picture std': round(float(base.std()), 3)}
def tex(kind, outname, settings=None, inputs=None, src_name='Vector'):
    def make(w, src):
        n = w.add(D + kind, 'n', x=0, **(settings or {}))
        for k, v in (inputs or {}).items(): n.inputs[k].default_value = v
        w.link(src[0], src[1], 'n', src_name); w.link('n', outname, 'out', 'Height')
    return make
brick = lambda sc, bw, rh, out='Factor': tex('Brick', out, dict(offset=0.5), {'Scale': sc, 'Brick Width': bw, 'Row Height': rh, 'Mortar Size': 0.02, 'Mortar Smooth': 0.0})
R['noise Scale 5'] = test(tex('Noise', 'Fac', None, {'Scale': 5.0}))
R['noise Scale 8 (whole number)'] = test(tex('Noise', 'Fac', None, {'Scale': 8.0}))
R['noise 4D Scale 8'] = test(tex('Noise', 'Fac', dict(noise_dimensions='4D'), {'Scale': 8.0}))
R['voronoi Scale 5'] = test(tex('Voronoi', 'Distance', None, {'Scale': 5.0}))
R['voronoi Scale 8'] = test(tex('Voronoi', 'Distance', None, {'Scale': 8.0}))
R['gabor 2D Scale 4'] = test(tex('Gabor', 'Value', None, {'Scale': 4.0}))
R['magic Scale 4'] = test(tex('Magic', 'Fac', None, {'Scale': 4.0}))
R['wave bands X, Scale 4'] = test(tex('Wave', 'Fac', dict(wave_type='BANDS', bands_direction='X'), {'Scale': 4.0}))
R['wave bands X, Scale 4, Distortion 3'] = test(tex('Wave', 'Fac', dict(wave_type='BANDS', bands_direction='X'), {'Scale': 4.0, 'Distortion': 3.0}))
R['checker Scale 8'] = test(tex('Checker', 'Fac', None, {'Scale': 8.0}))
R['gradient linear (0..1 ramp)'] = test(tex('Gradient', 'Fac', dict(gradient_type='LINEAR')))
R['brick mortar, Scale 2, Width 0.5, Height 0.25 (4 x 8 whole)'] = test(brick(2.0, 0.5, 0.25))
R['brick colour, 4 x 8 whole'] = test(brick(2.0, 0.5, 0.25, 'Color'))
R['brick mortar, 3.4 x 12.1 (not whole)'] = test(brick(1.7, 0.5, 0.14))
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'which_patterns_wrap.json'), 'w'), indent=1)
for k, v in R.items(): print(k, v)
