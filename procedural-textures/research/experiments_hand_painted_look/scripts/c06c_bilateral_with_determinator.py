# What this does: the Bilateral Blur node needs its "Determinator" socket connected to a picture that shows where the edges are. In c06 I left it unconnected
# (constant white = no edge information). Here the Determinator is the picture itself. Sizes 4, 8, 16, thresholds 0.05, 0.1, 0.3; strips of 300 px crops.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
BASE = os.path.join(hp.OUT, 'pictures', 'c06_compositor'); SRC = os.path.join(BASE, 'source_grainy.png')
OUT = os.path.join(BASE, 'bilateral_determinator'); os.makedirs(OUT, exist_ok=True)
def bil(size, thr, link=True):
    def make(tree, image, extras):
        n = tree.nodes.new('CompositorNodeBilateralblur'); tree.links.new(image.outputs['Image'], n.inputs['Image'])
        if link: tree.links.new(image.outputs['Image'], n.inputs['Determinator'])
        n.inputs['Size'].default_value = size; n.inputs['Threshold'].default_value = thr
        return n.outputs['Image']
    return make
items = [(4, 0.05), (8, 0.05), (8, 0.1), (16, 0.1), (16, 0.3)]
files, labels = [], []
S = hp.load(SRC)[420:840, 420:840]
hp.save(S, os.path.join(OUT, 'src_crop.png')); files.append('src_crop.png'); labels.append('source (before)')
for i, (s, t) in enumerate(items):
    p = os.path.join(OUT, f'full_{i}.png'); hp.run_compositor(SRC, p, bil(s, t, True))
    a = hp.load(p)[420:840, 420:840]; hp.save(a, os.path.join(OUT, f'crop_{i}.png')); files.append(f'crop_{i}.png'); labels.append(f'Determinator linked: Size {s} Thr {t}')
    os.remove(p)
json.dump({'files': files, 'labels': labels}, open(os.path.join(OUT, 'sweep.json'), 'w'))
import subprocess
subprocess.run(['python3', '-I', os.path.join(hp.LIB, 'make_strip.py'), OUT, os.path.join(OUT, 'strip.png'), '--columns', '6', '--title', 'Bilateral Blur WITH the Determinator linked to the picture', '--cell', '250'], check=True)
