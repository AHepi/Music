# What this does: tests the "hand-painted / flat-colour patches" tricks that artists and tutorials mention, on one and the same seamless noise:
#   (1) Map Range with Interpolation 'Stepped' and 2, 3, 4, 6, 10 steps (the nearest thing Blender has to a Posterize node),
#   (2) six ways to turn a smooth noise into painted flat patches side by side: Color Ramp Constant, Map Range Stepped, Math Snap, Math Round,
#       a narrow Map Range window (hard mask), and Shader to RGB (EEVEE-only toon trick; expected to fail in Cycles).
# Writes small pictures and strips into out/posterize/. Run: blender -b --disable-autoexec -t 2 --python sweep_posterize.py
import os
import subprocess
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'lib')))
import builder as bd  # noqa: E402
import sweep_tools as st  # noqa: E402

OUT = os.path.join(HERE, 'out', 'posterize')
os.makedirs(OUT, exist_ok=True)
PALETTE = [(0.0, '#1f1a18'), (0.33, '#5a3a28'), (0.66, '#93603f'), (1.0, '#c98d5a')]


def base_noise(b):
    noise = b.tnoise(4, 4, detail=5, roughness=0.6, distortion=0.2, seed=2.0)
    return b.maprange(noise, 0.3, 0.7)


def stepped(steps):
    b = bd.Builder(f'stepped {steps}')
    value = base_noise(b)
    node = b.node('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='STEPPED', clamp=True)
    b._put(node, 0, value)
    node.inputs['Steps'].default_value = float(steps)
    colour = b.ramp(node.outputs[0], PALETTE, 'LINEAR')
    return b.finish(colour, node.outputs[0])


def kinds(kind):
    b = bd.Builder('kind ' + kind)
    value = base_noise(b)
    if kind == 'smooth ramp (no steps)':
        colour = b.ramp(value, PALETTE, 'LINEAR')
    elif kind == 'Color Ramp: Constant':
        colour = b.ramp(value, PALETTE, 'CONSTANT')
    elif kind == 'Map Range: Stepped 4':
        node = b.node('ShaderNodeMapRange', data_type='FLOAT', interpolation_type='STEPPED', clamp=True)
        b._put(node, 0, value)
        node.inputs['Steps'].default_value = 4.0
        colour = b.ramp(node.outputs[0], PALETTE, 'LINEAR')
    elif kind == 'Math: Snap 0.25':
        snapped = b.math('SNAP', value, 0.25)
        colour = b.ramp(snapped, PALETTE, 'LINEAR')
    elif kind == 'Math: Round':
        colour = b.ramp(b.math('ROUND', b.mul(value, 3.0)) , [(0.0, '#1f1a18'), (1.0, '#5a3a28'), (2.0, '#93603f'), (3.0, '#c98d5a')], 'LINEAR')
        colour = b.ramp(b.div(b.math('ROUND', b.mul(value, 3.0)), 3.0), PALETTE, 'LINEAR')
    elif kind == 'narrow window mask':
        colour = b.mix('#5a3a28', '#c98d5a', b.maprange(value, 0.48, 0.5))
    elif kind == 'Shader to RGB (EEVEE trick)':
        diffuse = b.node('ShaderNodeBsdfDiffuse')
        b._put(diffuse, 'Color', bd.as_colour('#93603f'))
        s2r = b.node('ShaderNodeShaderToRGB')
        b.tree.links.new(diffuse.outputs[0], s2r.inputs[0])
        colour = b.ramp(b.brightness(s2r.outputs['Color']), PALETTE, 'CONSTANT')
    else:
        raise KeyError(kind)
    return b.finish(colour, value)


# (1) steps sweep
st.render_sweep(lambda v: stepped(v), [2, 3, 4, 6, 10], os.path.join(OUT, 'steps'), 'Colour', 256, [f'Stepped, steps = {v}' for v in (2, 3, 4, 6, 10)])
names = ['smooth ramp (no steps)', 'Color Ramp: Constant', 'Map Range: Stepped 4', 'Math: Snap 0.25', 'Math: Round', 'narrow window mask', 'Shader to RGB (EEVEE trick)']
st.render_sweep(lambda n: kinds(n), names, os.path.join(OUT, 'kinds'), 'Colour', 256, names)
