# What this does: checks that probe_tools works (noise range, seam) - the first measurements.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt

def body(w):
    w.add('ShaderNodeTexNoise', 'n', x=0, noise_dimensions='3D', noise_type='FBM', normalize=True, Scale=5.0, Detail=2.0)
    w.link('in', 'Vector', 'n', 'Vector')
    w.link('n', 'Fac', 'out', 'Height')
a = pt.render_float(body, 'Height', 128)
print('noise default: min %.3f max %.3f mean %.3f seam_ratio %.2f' % (a.min(), a.max(), a.mean(), pt.seam_ratio(a)))
