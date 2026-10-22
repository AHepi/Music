# What this does (plain words): the first round's regrade.py (re-balances a finished picture from its light-group EXR, no new drawing, about 3 seconds) with ONE
# addition for the fix round: an optional "shadow lift" (toe) after the vignette, tried here on the ALREADY DRAWN pictures so the lift can be tuned for a few cents
# of card time before anything is redrawn. Several lifts can be tried in one Blender start and each is written as a small JPG (default 1200 x 800).
# Run (headless): blender -b --disable-autoexec -P regrade_fix.py -- IN.exr OUT_FOLDER NAME1=T,L0,R,G,B [NAME2=...] [--full] [--crop x0,y0,x1,y1 (fractions)]
#   NAME=none=none      (spell it  name=none ) the picture as drawn (no lift)
#   NAME=T,L0,R,G,B    toe lift: out = in + tint * L0 * T / (T + luminance(in))   (linear scene colour; T = where the lift has dropped to half, L0 = size at pure black)
import json
import os
import sys

import bpy

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import stage_fix  # noqa: E402  (add_toe lives there so the scene and this tool use the very same nodes)


def load_comp_asset(name):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    path = os.path.join(bpy.utils.system_resource('DATAFILES'), 'assets', 'nodes', 'compositing_nodes_essentials.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.node_groups = [name]
    return bpy.data.node_groups[name]


def run_variant(exr, meta, w, h, name, toe, outdir, full):
    sc = bpy.context.scene
    for t in list(bpy.data.node_groups):
        if t.name.startswith('regrade'):
            bpy.data.node_groups.remove(t)
    img = bpy.data.images.get(os.path.basename(exr)) or bpy.data.images.load(exr, check_existing=False)
    vs = sc.view_settings
    vs.view_transform = meta.get('view_transform', 'AgX')
    try:
        vs.look = meta.get('look', 'AgX - Punchy')
    except Exception:
        pass
    vs.exposure = meta.get('exposure', 0.5)
    tree = bpy.data.node_groups.new('regrade ' + name, 'CompositorNodeTree')
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    feed = tree.nodes.new('CompositorNodeImage')
    feed.image = img
    feed.layer = 'ViewLayer'
    outn = tree.nodes.new('NodeGroupOutput')
    groups = [o.name[len('Combined_'):] for o in feed.outputs if o.name.startswith('Combined_') and o.enabled]

    def mix(blend, a, b):
        m = tree.nodes.new('ShaderNodeMix')
        m.data_type, m.blend_type = 'RGBA', blend
        m.inputs['Factor'].default_value = 1.0
        tree.links.new(m.inputs[6], a)
        tree.links.new(m.inputs[7], b)
        return m.outputs[2]
    acc = None
    for g in groups:
        acc = feed.outputs['Combined_' + g] if acc is None else mix('ADD', acc, feed.outputs['Combined_' + g])
    dn = tree.nodes.new('CompositorNodeDenoise')
    tree.links.new(dn.inputs['Image'], acc)
    sock = dn.outputs['Image']
    gl = tree.nodes.new('CompositorNodeGlare')
    gl.inputs['Type'].default_value = 'Bloom'
    try:
        gl.inputs['Quality'].default_value = 'High'
    except Exception:
        pass
    gl.inputs['Threshold'].default_value = 2.0
    gl.inputs['Strength'].default_value = 0.05
    gl.inputs['Size'].default_value = 0.5
    tree.links.new(gl.inputs['Image'], sock)
    sock = gl.outputs['Image']
    v = tree.nodes.new('CompositorNodeGroup')
    v.node_tree = load_comp_asset('Vignette')
    v.inputs['Factor'].default_value = 0.55
    v.inputs['Feather'].default_value = 0.4
    tree.links.new(v.inputs['Image'], sock)
    sock = v.outputs[0]
    if toe:
        sock = stage_fix.add_toe(tree, sock, *toe)
    tree.links.new(outn.inputs[0], sock)
    sc.compositing_node_group = tree
    sc.render.use_compositing = True
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'
    ims.file_format = 'PNG'
    ims.color_depth = '8'
    ims.color_mode = 'RGB'
    ims.color_management = 'FOLLOW_SCENE'
    tmp = os.path.join(outdir, f'_{name}.png')
    sc.render.filepath = tmp
    bpy.ops.render.render(write_still=True)
    # a small JPG for looking at
    pic = bpy.data.images.load(tmp)       # the PNG is already display-referred: scale it and save it as it is (save_render would tone-map it a second time)
    if not full:
        pic.scale(1200, 800)
    pic.filepath_raw = os.path.join(outdir, f'{name}.jpg')
    pic.file_format = 'JPEG'
    pic.save()
    bpy.data.images.remove(pic)
    os.remove(tmp)
    print('REGRADE_FIX_DONE', name, 'toe', toe, flush=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    exr, outdir = argv[0], argv[1]
    variants = [a for a in argv[2:] if '=' in a]
    full = '--full' in argv
    os.makedirs(outdir, exist_ok=True)
    meta = {}
    jp = os.path.splitext(exr)[0] + '.json'
    if os.path.exists(jp):
        meta = json.load(open(jp))
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(exr)
    w, h = inp.spec().width, inp.spec().height
    inp.close()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    try:
        sc.render.compositor_device = 'CPU'
    except Exception:
        pass
    for item in variants:
        name, spec = item.split('=', 1)
        toe = None if spec == 'none' else tuple(float(x) for x in spec.split(','))
        if toe is not None:
            toe = (toe[0], toe[1], toe[2:5] if len(toe) >= 5 else (1.0, 1.0, 1.0))
        run_variant(exr, meta, w, h, name, toe, outdir, full)


main()
