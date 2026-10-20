# What this does (plain words): makes the "what does this setting do?" strips for the gravel guide. For each setting it bakes the same small picture (320 dots)
# several times with only that setting changed and saves the tiles plus a sweep.json that lib/make_strip.py joins into one labelled strip.
# Use: blender -b --disable-autoexec -t 2 --python sweeps_for_guide.py -- OUT_FOLDER [only_sweep_name]
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy
import gravel_generator as gg
import gravel_layers as layers
import bake_harness as bh

GRAVEL = os.path.abspath(os.path.join(HERE, '..'))
arguments = sys.argv[sys.argv.index('--') + 1:]
out_root = arguments[0]
only = arguments[1] if len(arguments) > 1 else None
SIZE = 640          # the whole tile is photographed at 640 dots and the top-left 320 x 320 is kept, so the stones are big enough to see the effect
base = json.load(open(os.path.join(GRAVEL, 'description', 'S_v4.json')))


def render(description, path, channel='Colour', samples=8, gaussian_width=None):
    scene, tile = bh.new_bake_scene(SIZE)
    bpy.data.objects.remove(tile)
    mesh, _ = gg.build_tile_mesh(layers.make_shape_list(description), description)
    obj = bpy.data.objects.new('shapes', mesh)
    scene.collection.objects.link(obj)
    gg.photograph(scene, obj, gg.channel_material(channel, description), path, channel != 'Colour', channel == 'Height', samples, gaussian_width)
    picture = bh.load_png_as_array(path)[:320, :320]
    bh.save_array_png(picture, path, channel == 'Height')


def sweep(name, title, values, labels, change, channel='Colour', **kw):
    if only and only != name:
        return
    folder = os.path.join(out_root, name)
    if os.path.exists(os.path.join(folder, 'sweep.json')):
        return                                  # already made: skip (lets the script be started again)
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


def all_classes(d, key, value):
    for c in d['stones']['classes']:
        c[key] = value


sweep('stone_sides', 'Corners per stone (all size classes)', [3, 4, 5, 7, 10], ['3 corners', '4 corners', '5 corners', '7 corners', '10 corners'],
      lambda d, v: all_classes(d, 'sides', [v, v]))
sweep('stone_chip', 'Edge chipping (share of the stone radius)', [0.0, 0.05, 0.12, 0.25, 0.4], ['0 (smooth)', '0.05', '0.12 (used)', '0.25', '0.4'],
      lambda d, v: d['stones'].__setitem__('chip', v))
sweep('stone_packing', 'Packing: spacing between stones (x the sum of radii)', [0.35, 0.5, 0.65, 0.8, 1.0], ['0.35', '0.5', '0.65 (used)', '0.8', '1.0'],
      lambda d, v: all_classes(d, 'spacing', v))
sweep('shadow_width', 'Shadow on the soil (dots)', [0.0, 3.0, 6.0, 10.0, 16.0], ['none', '3', '6 (used)', '10', '16'],
      lambda d, v: d['stones'].__setitem__('shadow', v))
sweep('light_direction', 'Light direction (where the light comes from)', [[0.0, -1.0], [-0.7, -0.7], [1.0, 0.0], [0.7, 0.7], [0.0, 1.0]],
      ['from the top (used)', 'top left', 'right', 'bottom right', 'from the bottom'], lambda d, v: d.__setitem__('light', v))
sweep('flaky_patches', 'Flaky light and dark patches on stones (per radius)', [0.0, 0.3, 0.7, 1.3, 2.2], ['none', '0.3', '0.7 (used)', '1.3', '2.2'],
      lambda d, v: d['stones'].__setitem__('mottle_per_radius', v))
sweep('soil_lumps', 'Soil lumps (count x used)', [0.0, 0.3, 1.0, 2.0, 3.5], ['none', 'x0.3', 'x1 (used)', 'x2', 'x3.5'],
      lambda d, v: [layer.__setitem__('count', int(layer['count'] * v)) for layer in d['soil']['layers'] + d['soil']['specks']] and None)
sweep('height_filter_width', 'Height picture: Cycles Gaussian filter width (blur)', [0, 1, 2, 4, 8], ['box (none)', 'width 1', 'width 2 (used)', 'width 4', 'width 8'],
      lambda d, v: {'gaussian_width': v or None}, channel='Height', samples=16)


def stage(d, v):
    keep = v
    d['soil']['layers'] = d['soil']['layers'] if keep >= 1 else []
    if keep < 1:
        d['soil']['specks'] = []
    if keep < 2:
        d['stones']['classes'] = []
    elif keep < 7:
        d['stones']['classes'] = d['stones']['classes'][::-1][: keep - 2]          # small classes first
sweep('layers_stage', 'Layers added one by one', [0, 1, 3, 5, 7], ['ground only', '+ soil lumps', '+ tiny + small stones', '+ medium stones', '+ big stones (all)'], stage)
