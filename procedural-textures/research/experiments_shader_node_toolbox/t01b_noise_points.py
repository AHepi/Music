# What this does: second round of Noise measurements. Round one showed that typing a value into an unconnected Vector socket does
# NOTHING (Blender uses the Generated coordinates instead), so here the exact test positions are fed in through a Combine XYZ node.
# Measures: which inputs each Dimensions setting uses; whether noise reads exactly one value at whole-number positions;
# ranges of Ridged / Hybrid / Hetero with Offset 0 vs 1. Writes noise_measurements_2.json
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
OUT = os.path.dirname(os.path.abspath(__file__))
R = {}

def point_body(dim, vec, wv, **kw):
    def body(w):
        w.add('ShaderNodeCombineXYZ', 'xyz', x=-1, X=vec[0], Y=vec[1], Z=vec[2])
        n = w.add('ShaderNodeTexNoise', 'n', x=0, noise_dimensions=dim, Scale=1.0, Detail=0.0, normalize=True, **kw)
        w.link('xyz', 'Vector', 'n', 0)
        n.inputs[1].default_value = wv
        w.link('n', 'Fac', 'out', 'Height')
    return body
def at(dim, vec, wv=0.0, **kw):
    return round(float(pt.render_float(point_body(dim, vec, wv, **kw), 'Height', 4).mean()), 4)

R['dimensions'] = {
    '2D, Z=0.1 vs Z=7.3 (same X,Y)': [at('2D', (0.31, 0.77, 0.1)), at('2D', (0.31, 0.77, 7.3))],
    '3D, Z=0.1 vs Z=7.3': [at('3D', (0.31, 0.77, 0.1)), at('3D', (0.31, 0.77, 7.3))],
    '3D, W=0 vs W=5': [at('3D', (0.31, 0.77, 0.1), 0.0), at('3D', (0.31, 0.77, 0.1), 5.0)],
    '4D, W=0 vs W=0.4': [at('4D', (0.31, 0.77, 0.1), 0.0), at('4D', (0.31, 0.77, 0.1), 0.4)],
    '1D, W=0.31 / W=0.37 (Vector changes ignored)': [at('1D', (0.5, 0.5, 0.5), 0.31), at('1D', (9.0, 9.0, 9.0), 0.31), at('1D', (0.5, 0.5, 0.5), 0.37)],
}
R['value_at_exact_points_Scale1_Detail0_normalized'] = {str(v): at('3D', v) for v in [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0), (2.0, 5.0, 1.0), (-4.0, 3.0, 8.0), (1.5, 2.5, 3.5), (0.31, 0.77, 0.1)]}
R['value_at_exact_points_2D_Scale1_Detail0'] = {str(v): at('2D', v) for v in [(0.0, 0.0, 0.0), (1.0, 2.0, 0.0), (3.0, 7.0, 0.0), (1.5, 2.5, 0.0)]}
R['value_at_whole_points_with_Detail2'] = {str(v): round(float(pt.render_float(lambda w, v=v: (w.add('ShaderNodeCombineXYZ', 'xyz', x=-1, X=v[0], Y=v[1], Z=v[2]),
                          w.add('ShaderNodeTexNoise', 'n', x=0, Scale=1.0, Detail=2.0, normalize=True), w.link('xyz', 'Vector', 'n', 0), w.link('n', 'Fac', 'out', 'Height')), 'Height', 4).mean()), 4)
                          for v in [(1.0, 2.0, 3.0), (2.0, 5.0, 1.0)]}

def rng(**kw):
    def body(w):
        w.add('ShaderNodeTexNoise', 'n', x=0, Scale=6.0, Roughness=0.5, **kw)
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    a = pt.render_float(body, 'Height', 96)
    return [round(float(a.min()), 3), round(float(a.mean()), 3), round(float(a.max()), 3)]
# offsets are inputs, not settings - set them through the input names
def rng2(t, off, gain, det):
    def body(w):
        n = w.add('ShaderNodeTexNoise', 'n', x=0, noise_type=t, Scale=6.0, Roughness=0.5, Detail=det)
        for sock in n.inputs:
            if sock.identifier == 'Offset' and sock.enabled: sock.default_value = off
            if sock.identifier == 'Gain' and sock.enabled: sock.default_value = gain
        w.link('in', 'Vector', 'n', 'Vector'); w.link('n', 'Fac', 'out', 'Height')
    a = pt.render_float(body, 'Height', 96)
    return [round(float(a.min()), 3), round(float(a.mean()), 3), round(float(a.max()), 3)]
R['ranges_by_type_offset_gain'] = {}
for t in ['RIDGED_MULTIFRACTAL', 'HYBRID_MULTIFRACTAL', 'HETERO_TERRAIN']:
    for off in (0.0, 1.0):
        for det in (2.0, 8.0):
            R['ranges_by_type_offset_gain'][f'{t} offset={off} gain=1 detail={det}'] = rng2(t, off, 1.0, det)
R['ranges_by_type_offset_gain']['RIDGED_MULTIFRACTAL offset=1 gain=2 detail=8'] = rng2('RIDGED_MULTIFRACTAL', 1.0, 2.0, 8.0)
json.dump(R, open(os.path.join(OUT, 'noise_measurements_2.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
