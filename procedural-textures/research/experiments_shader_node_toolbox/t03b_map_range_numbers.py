# What this does: measures Map Range (linear / stepped / smooth step, clamp on/off) with exact numbers by feeding it a plain left-to-right ramp.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
OUT = os.path.dirname(os.path.abspath(__file__))
R = {}
def run(interp, clamp, steps=4, frm=(0.4, 0.6), to=(0.0, 1.0), data_type='FLOAT'):
    def body(w):
        w.add('ShaderNodeSeparateXYZ', 'sx', x=-1); w.link('in', 'Vector', 'sx', 'Vector')
        m = w.add('ShaderNodeMapRange', 'm', x=0, interpolation_type=interp, clamp=clamp)
        m.inputs[1].default_value, m.inputs[2].default_value = frm
        m.inputs[3].default_value, m.inputs[4].default_value = to
        m.inputs[5].default_value = steps
        w.link('sx', 'X', 'm', 0); w.link('m', 0, 'out', 'Height')
    a = pt.render_float(body, 'Height', 100)
    row = a[50]
    xs = np.linspace(0.005, 0.995, 100)
    pick = lambda x: round(float(row[int(round(x * 100 - 0.5))]), 3)
    return {f'x={x}': pick(x) for x in (0.2, 0.4, 0.45, 0.5, 0.55, 0.6, 0.8)}
for interp in ('LINEAR', 'STEPPED', 'SMOOTHSTEP', 'SMOOTHERSTEP'):
    for clamp in (True, False):
        R[f'{interp} clamp={clamp}'] = run(interp, clamp)
R['LINEAR clamp=False, To -1..1'] = run('LINEAR', False, to=(-1.0, 1.0))
json.dump(R, open(os.path.join(OUT, 'map_range_numbers.json'), 'w'), indent=1)
for k, v in R.items(): print(k, v)
