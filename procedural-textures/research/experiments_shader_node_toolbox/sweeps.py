# What this does: makes "what does this setting do" picture strips for the shader-toolbox guide (run inside Blender 5.2.2).
#   sweep(name, body, values, labels, channel='Height', ...) renders one small square per value. body(w, value) gets a NodeWriter w
#   that already holds 'in' (Group Input with the tile coordinate Vector, u and v from 0 to 1) and 'out' (Group Output with
#   'Colour' and 'Height'); it must link something to out's 'Colour' or 'Height'.
#   stretch=True spreads each grey picture over the full black-to-white range (so ridged or negative noise is visible); without it
#   grey level = the true number (0 black, 1 white; numbers outside 0..1 are clipped).
#   Pictures are joined into one labelled strip with lib/make_strip.py and saved in pictures/.
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
bh = pt.bh
HERE = os.path.dirname(os.path.abspath(__file__))
PICS = os.path.join(HERE, 'pictures')
os.makedirs(PICS, exist_ok=True)


def sweep(name, body, values, labels, channel='Height', size=192, stretch=False, columns=None, title=None, cell=None):
    folder = os.path.join(PICS, '_work', name)
    os.makedirs(folder, exist_ok=True)
    files = []
    scene, tile = bh.new_bake_scene(size)
    for i, v in enumerate(values):
        scene, tile = bh.new_bake_scene(size)
        group = pt.tree_from(f'{name}_{i}', lambda w, v=v: body(w, v))
        path = os.path.join(folder, f'tile_{i:02d}.png')
        if channel == 'Colour':
            material = bh.show_channel_material(group, 'Colour')
            tile.data.materials.append(material)
            bh.render_to(scene, path, False, False)
        else:
            a = pt.render_float_group(scene, tile, group, channel)
            if stretch:
                lo, hi = float(a.min()), float(a.max())
                a = (a - lo) / max(hi - lo, 1e-9)
            pt.save_png(a, path)
        files.append(os.path.basename(path))
    json.dump({'files': files, 'labels': [str(l) for l in labels]}, open(os.path.join(folder, 'sweep.json'), 'w'))
    out = os.path.join(PICS, name + '.png')
    cmd = ['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, out, '--title', title or name.replace('_', ' ')]
    cmd += ['--columns', str(columns or len(values))]
    cmd += ['--cell', str(cell or size)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def lit_sweep(name, setup, values, labels, size=224, columns=None, title=None, make_scene=None, linear=False):
    """Like sweep() but for scenes with real lighting. setup(scene, tile, value) builds the material / extra objects in a scene made by
    make_scene (default: pt.lit_scene with a low sun, overhead camera). The picture is the ordinary lit render (sRGB)."""
    folder = os.path.join(PICS, '_work', name)
    os.makedirs(folder, exist_ok=True)
    files = []
    for i, v in enumerate(values):
        scene, tile = (make_scene or pt.lit_scene)(size)
        setup(scene, tile, v)
        path = os.path.join(folder, f'tile_{i:02d}.png')
        pt.render_png(scene, path, linear)
        files.append(os.path.basename(path))
    json.dump({'files': files, 'labels': [str(l) for l in labels]}, open(os.path.join(folder, 'sweep.json'), 'w'))
    out = os.path.join(PICS, name + '.png')
    cmd = ['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, out, '--title', title or name.replace('_', ' '),
           '--columns', str(columns or len(values)), '--cell', str(size)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out
