# What this does: MEASURES what Noise Texture settings do (numbers, not just pictures) in Blender 5.2.2 and writes noise_measurements.json:
#  1. does Noise wrap seamlessly at whole-number UV values? (a web claim)   2. value range of each noise type with Normalize on and off
#  3. does fractional Detail blend two octave counts?   4. which inputs each Dimensions setting really uses
#  5. does Noise read 0.5 at whole-number positions (a manual note)?   6. what an unconnected Vector input does
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
OUT = os.path.dirname(os.path.abspath(__file__))
R = {}
S = 96

def noise_body(**kw):
    scale_uv = kw.pop('uv_scale', None)
    const_vec = kw.pop('const_vec', None)
    wlink = kw.pop('w', None)
    no_vector = kw.pop('no_vector', False)
    def body(w):
        n = w.add('ShaderNodeTexNoise', 'n', x=0, **kw)
        if scale_uv is not None:
            w.vector_math('mul', 'SCALE', x=-1); w.link('in', 'Vector', 'mul', 0); w.nodes['mul'].inputs['Scale'].default_value = scale_uv
            w.link('mul', 0, 'n', 'Vector')
        elif const_vec is not None:
            n.inputs[0].default_value = const_vec
        elif not no_vector:
            w.link('in', 'Vector', 'n', 'Vector')
        if wlink is not None:
            n.inputs[1].default_value = wlink   # by position: n.inputs['W'] raises KeyError when the Dimensions setting hides W
        w.link('n', 'Fac', 'out', 'Height')
    return body

# 1. seam test ---------------------------------------------------------------------------------------------
seam = {}
for label, kw in [('Scale 5 on UV (default)', dict(Scale=5.0)), ('Scale 1', dict(Scale=1.0)), ('Scale 2', dict(Scale=2.0)),
                  ('Scale 8 (whole number)', dict(Scale=8.0)), ('Scale 8, Detail 0, Roughness 0', dict(Scale=8.0, Detail=0.0)),
                  ('Scale 7.5', dict(Scale=7.5)), ('UV x 8 into Vector, Scale 1', dict(Scale=1.0, uv_scale=8.0)),
                  ('Scale 8 4D', dict(Scale=8.0, noise_dimensions='4D'))]:
    a = pt.render_float(noise_body(noise_dimensions=kw.pop('noise_dimensions', '3D'), **kw), 'Height', S)
    seam[label] = round(pt.seam_ratio(a), 2)
R['1_seam_ratio_(1.0 = seamless)'] = seam

# 2. value range per type and Normalize --------------------------------------------------------------------
rng = {}
for t in ['FBM', 'MULTIFRACTAL', 'RIDGED_MULTIFRACTAL', 'HYBRID_MULTIFRACTAL', 'HETERO_TERRAIN']:
    for norm in (True, False):
        for detail in (2.0, 8.0):
            a = pt.render_float(noise_body(noise_type=t, normalize=norm, Scale=6.0, Detail=detail, Roughness=0.5), 'Height', S)
            rng[f'{t} normalize={norm} detail={detail}'] = [round(float(a.min()), 3), round(float(a.mean()), 3), round(float(a.max()), 3)]
R['2_range_min_mean_max'] = rng

# 3. fractional detail --------------------------------------------------------------------------------------
vals = {}
for d in (2.0, 2.5, 3.0):
    vals[d] = pt.render_float(noise_body(Scale=6.0, Detail=d, Roughness=0.7, normalize=False), 'Height', S)
blend = 0.5 * (vals[2.0] + vals[3.0])
R['3_fractional_detail'] = {'max |Detail2.5 - mean(Detail2, Detail3)|': round(float(np.abs(vals[2.5] - blend).max()), 5),
                           'max |Detail2.5 - Detail2|': round(float(np.abs(vals[2.5] - vals[2.0]).max()), 5),
                           'max |Detail2.5 - Detail3|': round(float(np.abs(vals[2.5] - vals[3.0]).max()), 5)}
# also test fBM Detail 0 vs 1 (is Detail 0 one octave?)
a0 = pt.render_float(noise_body(Scale=6.0, Detail=0.0, normalize=True), 'Height', S)
a1 = pt.render_float(noise_body(Scale=6.0, Detail=1.0, normalize=True), 'Height', S)
R['3_fractional_detail']['std Detail 0 / Detail 1 (normalized)'] = [round(float(a0.std()), 4), round(float(a1.std()), 4)]

# 4. dimensions ---------------------------------------------------------------------------------------------
def vec_const_body(dim, vec, wv):
    return noise_body(noise_dimensions=dim, Scale=1.0, Detail=0.0, const_vec=vec, w=wv)
dims = {}
def one(dim, vec, wv):
    a = pt.render_float(vec_const_body(dim, vec, wv), 'Height', 8)
    return round(float(a.mean()), 4)
dims['2D: Z=0.1 vs Z=7.3 (same X,Y)'] = [one('2D', (0.31, 0.77, 0.1), 0.0), one('2D', (0.31, 0.77, 7.3), 0.0)]
dims['3D: Z=0.1 vs Z=7.3'] = [one('3D', (0.31, 0.77, 0.1), 0.0), one('3D', (0.31, 0.77, 7.3), 0.0)]
dims['3D: W=0 vs W=5 (W ignored?)'] = [one('3D', (0.31, 0.77, 0.1), 0.0), one('3D', (0.31, 0.77, 0.1), 5.0)]
dims['4D: W=0 vs W=0.4'] = [one('4D', (0.31, 0.77, 0.1), 0.0), one('4D', (0.31, 0.77, 0.1), 0.4)]
dims['1D: W=0.31 vs W=0.37 (Vector ignored)'] = [one('1D', (0.5, 0.5, 0.5), 0.31), one('1D', (9.0, 9.0, 9.0), 0.31), one('1D', (0.5, 0.5, 0.5), 0.37)]
R['4_dimensions_value_at_one_point'] = dims

# 5. integer positions give 0.5? ----------------------------------------------------------------------------
ints = {}
for vec in [(1.0, 2.0, 3.0), (0.0, 0.0, 0.0), (2.0, 5.0, 1.0), (1.5, 2.5, 3.5), (0.31, 0.77, 0.1)]:
    ints[str(vec)] = round(float(pt.render_float(noise_body(Scale=1.0, Detail=0.0, normalize=True, const_vec=vec), 'Height', 8).mean()), 4)
R['5_value_at_exact_points_(Scale 1, Detail 0)'] = ints
ints2 = {}
for vec in [(1.0, 2.0, 3.0), (2.0, 5.0, 1.0)]:
    ints2[str(vec)] = round(float(pt.render_float(noise_body(Scale=1.0, Detail=2.0, normalize=True, const_vec=vec), 'Height', 8).mean()), 4)
R['5b_same_points_with_Detail_2'] = ints2

# 6. unconnected Vector -------------------------------------------------------------------------------------
a = pt.render_float(noise_body(no_vector=True, Scale=5.0), 'Height', S)
R['6_unconnected_Vector_input'] = {'std across the picture (0 would mean a constant)': round(float(a.std()), 4), 'min': round(float(a.min()), 3), 'max': round(float(a.max()), 3)}
json.dump(R, open(os.path.join(OUT, 'noise_measurements.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
