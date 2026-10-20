# What this does: a small debugging check for c05: renders the 'Edge' (Voronoi Distance To Edge) output of the patch field group and prints its range, to find out why the first edge-distance outline mask was empty.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c05_outlines_in_shader.py')).read().split('results = {}')[0]
exec(compile(src, 'c05head', 'exec'))
hp.SAMPLES = 1
def b():
    tree, w = hp.new_group('dbg', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    hp.instance(w, field_group('cells'), 'f', x=0); w.link('in', 'Vector', 'f', 'Vector')
    w.link('f', 'Edge', 'out', 'Height'); return tree
hp.photograph_group(b, 'Height', '/tmp/dbg_edge.png', 256, sixteen=True)
a = hp.load('/tmp/dbg_edge.png')[..., 0]
print('field Edge output: min %.4f max %.4f mean %.4f' % (a.min(), a.max(), a.mean()))
