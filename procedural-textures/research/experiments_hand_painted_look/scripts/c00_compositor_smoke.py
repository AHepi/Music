# What this does: first check that the compositor route works headless in Blender 5.2.2: makes a seamless noise picture, pushes it through
# Kuwahara (classic and anisotropic), Posterize and Pixelate, and prints what happened (timings, sizes, any errors).
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

OUT = os.path.join(hp.OUT, 'data', 'smoke'); os.makedirs(OUT, exist_ok=True)

def build(_):
    tree, w = hp.new_group('smoke source', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    w.add('ShaderNodeGroup', 'noise', x=0); w.nodes['noise'].node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'noise', 'Vector'); w.nodes['noise'].inputs['Scale'].default_value = 5; w.nodes['noise'].inputs['Detail'].default_value = 4
    w.add('ShaderNodeValToRGB', 'ramp', x=1); w.link('noise', 'Fac', 'ramp', 'Fac')
    w.nodes['ramp'].color_ramp.elements[0].position = 0.3; w.nodes['ramp'].color_ramp.elements[1].position = 0.7
    w.nodes['ramp'].color_ramp.elements[0].color = (0.05, 0.02, 0.01, 1); w.nodes['ramp'].color_ramp.elements[1].color = (0.9, 0.5, 0.2, 1)
    w.link('ramp', 'Color', 'out', 'Colour')
    return tree
src = os.path.join(OUT, 'source.png')
hp.photograph_group(lambda: build(None), 'Colour', src, 512)
print('source saved', os.path.exists(src))

def kuwahara(kind, **kw):
    def make(tree, image, extras):
        node = tree.nodes.new('CompositorNodeKuwahara')
        tree.links.new(image.outputs['Image'], node.inputs['Image'])
        hp.set_menu(node, 'Type', kind)
        for k, v in kw.items():
            node.inputs[k].default_value = v
        return node.outputs['Image']
    return make

for label, fn in (('classic_6', kuwahara('Classic', Size=6.0)), ('aniso_6', kuwahara('Anisotropic', Size=6.0))):
    t0 = time.time()
    try:
        hp.run_compositor(src, os.path.join(OUT, label + '.png'), fn)
        print(label, 'ok', round(time.time() - t0, 1), 's')
    except Exception as e:
        print(label, 'FAILED', repr(e))

def posterize(steps):
    def make(tree, image, extras):
        node = tree.nodes.new('CompositorNodePosterize'); tree.links.new(image.outputs['Image'], node.inputs['Image']); node.inputs['Steps'].default_value = steps
        return node.outputs['Image']
    return make
hp.run_compositor(src, os.path.join(OUT, 'posterize_4.png'), posterize(4.0)); print('posterize ok')
def pixelate(size):
    def make(tree, image, extras):
        node = tree.nodes.new('CompositorNodePixelate'); tree.links.new(image.outputs['Image'], node.inputs['Color']); node.inputs['Size'].default_value = size
        return node.outputs['Color']
    return make
hp.run_compositor(src, os.path.join(OUT, 'pixelate_8.png'), pixelate(8)); print('pixelate ok')
for n in ('source', 'classic_6', 'aniso_6', 'posterize_4', 'pixelate_8'):
    a = hp.load(os.path.join(OUT, n + '.png')); print(n, a.shape, 'mean', a.mean(axis=(0, 1)).round(3), 'unique grey levels', len(np.unique((a.mean(axis=2) * 255).round())))
