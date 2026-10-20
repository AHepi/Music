# What this does: looks at what the Voronoi "Distance To Edge" feature really outputs in our seamless 4D cells (range, units) and in plain 3D / 2D.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
hp.SAMPLES = 1
BASE = os.path.join(hp.OUT, 'pictures', 'c05c_edge_debug'); os.makedirs(BASE, exist_ok=True)
def b4():
    tree, w = hp.new_group('e4', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    hp.instance(w, hp.anisotropic_noise_group('e4g', cells=True, feature='DISTANCE_TO_EDGE'), 'c', x=0, **{'Scale__U': 6.0, 'Scale__V': 6.0})
    w.link('in', 'Vector', 'c', 'Vector'); w.link('c', 'Distance', 'out', 'Height'); return tree
def b3(dim):
    def b():
        tree, w = hp.new_group('e'+dim, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
        w.add('ShaderNodeTexVoronoi', 'v', x=0, voronoi_dimensions=dim, feature='DISTANCE_TO_EDGE', Scale=6.0)
        w.link('in', 'Vector', 'v', 'Vector'); w.link('v', 'Distance', 'out', 'Height'); return tree
    return b
for name, b in (('4D seamless', b4), ('3D', b3('3D')), ('2D', b3('2D'))):
    hp.photograph_group(b, 'Height', os.path.join(BASE, name.replace(' ', '_') + '.png'), 256, sixteen=True)
    a = hp.load(os.path.join(BASE, name.replace(' ', '_') + '.png'))[..., 0]
    print(name, 'min %.4f max %.4f mean %.4f  share<0.01: %.3f' % (a.min(), a.max(), a.mean(), (a < 0.01).mean()))
