# What this does (plain words): makes the "what does this setting do?" strips for the guide. For each setting it bakes the same small picture
# (384 dots) several times with only that setting changed and saves the tiles plus a sweep.json that lib/make_strip.py joins into one labelled strip.
# Use: blender -b --disable-autoexec -t 2 --python sweeps_for_guide.py -- OUT_FOLDER [only_sweep_name]
import copy, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import slate_generator as sg
import slate_layers as layers
import bake_harness as bh

SLATE = os.path.abspath(os.path.join(HERE, '..'))
arguments = sys.argv[sys.argv.index('--') + 1:]
out_root = arguments[0]
only = arguments[1] if len(arguments) > 1 else None
SIZE = 384
s1 = json.load(open(os.path.join(SLATE, 'description', 'S1_layout_stamps.json')))
s0 = json.load(open(os.path.join(SLATE, 'description', 'S0_layout_only.json')))
l_medium = json.load(open(os.path.join(SLATE, 'description', 'L_trace_medium.json')))


def render(description, path, channel='Colour', samples=8, gaussian_width=None, crop=None):
    scene, tile = bh.new_bake_scene(SIZE)
    bpy.data.objects.remove(tile)
    mesh, _ = sg.build_tile_mesh(layers.make_shape_list(description), description)
    obj = bpy.data.objects.new('shapes', mesh)
    scene.collection.objects.link(obj)
    linear = channel != 'Colour'
    sg.photograph(scene, obj, sg.channel_material(channel, description), path, linear, channel == 'Height', samples, gaussian_width)


def sweep(name, title, base, values, labels, change, channel='Colour', **kw):
    if only and only != name:
        return
    folder = os.path.join(out_root, name)
    os.makedirs(folder, exist_ok=True)
    files = []
    for i, value in enumerate(values):
        d = copy.deepcopy(base)
        extra = change(d, value) or {}
        path = os.path.join(folder, f'tile_{i:02d}.png')
        render(d, path, channel, **{**kw, **extra})
        files.append(os.path.basename(path))
    json.dump({'files': files, 'labels': labels, 'title': title}, open(os.path.join(folder, 'sweep.json'), 'w'))
    print('sweep done', name, flush=True)


# 1. Cycles pixel filter width on the HEIGHT picture = how much the height is blurred
sweep('height_filter_width', 'Height pass: Cycles Gaussian filter width', s1, [0, 1, 2, 4, 8], ['box (none)', 'width 1', 'width 2', 'width 4', 'width 8'],
      lambda d, v: {'gaussian_width': v or None}, channel='Height', samples=16)
# 2. anti-aliasing samples on the colour picture (a crop of the traced description)
sweep('samples', 'Colour pass: Cycles samples (edge softness)', l_medium, [1, 2, 4, 16], ['1 sample', '2 samples', '4 samples', '16 samples'], lambda d, v: {'samples': v})
# 3. corner radius of the slates
sweep('corner_radius', 'Layout: corner radius (dots)', s0, [0, 4, 8, 16, 30], ['0', '4', '8', '16', '30'], lambda d, v: d['layout'].__setitem__('corner', v))
# 4. edge raggedness
sweep('edge_roughness', 'Layout: edge raggedness (x fitted value)', s0, [0, 0.5, 1, 2, 4], ['0 (straight)', 'x0.5', 'x1 (fitted)', 'x2', 'x4'],
      lambda d, v: d['layout'].__setitem__('rough', {k: (x * v if k != 'scale' else x) for k, x in d['layout']['rough'].items()}))
# 5. how random the stamp tones are
sweep('stamp_tone_noise', 'Paint: how random each patch tone is', s1, [0.0, 0.25, 0.4, 0.8, 1.5], ['0', '0.25', '0.4 (used)', '0.8', '1.5'], lambda d, v: d['paint'].__setitem__('noise_scale', v))
# 6. smooth tone drift field
sweep('stamp_field_amplitude', 'Paint: strength of the smooth tone drift', s1, [0, 6, 12, 24, 40], ['0', '6', '12 (used)', '24', '40'],
      lambda d, v: d['paint']['model']['field'].__setitem__('amp', v))
# 7. stamp shape
sweep('stamp_shape', 'Paint: patch outline style', s1, ['blob', 'streak'], ['plain spiky blobs', 'upright drips (used)'], lambda d, v: d['paint'].__setitem__('shape', v))
# 8. how many small patches
sweep('small_patch_count', 'Paint: number of tiny and small patches', s1, [0.0, 0.5, 1.0, 2.0], ['none', 'x0.5', 'x1 (used)', 'x2'],
      lambda d, v: d['paint'].__setitem__('rate_scale', [a * (v if i < 2 else 1.0) for i, a in enumerate(d['paint']['rate_scale'])]))
