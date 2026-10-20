# What this does: probes how Translate / Transform with Extension = Repeat behave when the scene canvas is bigger than the picture
# (can the compositor tile a picture by itself, so a filter can see neighbours?).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
OUT = os.path.join(hp.OUT, 'data', 'probe_pad'); os.makedirs(OUT, exist_ok=True)
# test picture 200 x 200: horizontal gradient in red, vertical gradient in green, a blue square in the corner (so wrapping is obvious)
n = 200
img = np.zeros((n, n, 3)); img[..., 0] = np.linspace(0, 1, n)[None, :]; img[..., 1] = np.linspace(0, 1, n)[:, None]; img[:30, :30, 2] = 1.0
src = os.path.join(OUT, 'src.png'); 
hp.bh.new_bake_scene(8)
hp.save(img, src)
def probe(name, make, canvas):
    path = os.path.join(OUT, name + '.png')
    hp.run_compositor(src, path, make, canvas=canvas, input_linear=True, output_linear=True)
    a = hp.load(path); print(name, 'canvas', canvas, '-> output', a.shape, 'share of black pixels %.3f' % ((a.sum(axis=2) < 0.01).mean()))
def tr(ext, dx=20, dy=20):
    def make(tree, image, extras):
        t = tree.nodes.new('CompositorNodeTranslate'); tree.links.new(image.outputs['Image'], t.inputs['Image'])
        hp.set_menu(t, 'Extension X', ext); hp.set_menu(t, 'Extension Y', ext); t.inputs['X'].default_value = float(dx); t.inputs['Y'].default_value = float(dy)
        return t.outputs['Image']
    return make
def tf(ext):
    def make(tree, image, extras):
        t = tree.nodes.new('CompositorNodeTransform'); tree.links.new(image.outputs['Image'], t.inputs['Image'])
        hp.set_menu(t, 'Extension X', ext); hp.set_menu(t, 'Extension Y', ext); t.inputs['Scale'].default_value = 1.0
        return t.outputs['Image']
    return make
probe('translate_repeat_canvas_same', tr('Repeat'), (200, 200))
probe('translate_repeat_canvas_bigger', tr('Repeat'), (280, 280))
probe('translate_clip_canvas_bigger', tr('Clip'), (280, 280))
probe('transform_repeat_canvas_bigger', tf('Repeat'), (280, 280))
probe('transform_extend_canvas_bigger', tf('Extend'), (280, 280))
