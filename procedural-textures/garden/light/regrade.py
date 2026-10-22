# What this does (plain words): re-balances a finished picture AFTER it was drawn, for free. It reads the multi-layer EXR that render_job.py wrote (one layer per
# light group: sun, rim, sky, fill, hall, lantern, rest), multiplies each group by a gain you choose (a number, or three numbers to recolour a light), adds them
# up, then applies the same finish as the drawing (mild bloom, vignette, the same AgX view transform and exposure) and writes a new PNG. It takes about a second and
# does not touch the 3D scene or the graphics card, so turning the screen glow up or the sun down costs nothing.
# Run (headless, no xvfb needed):
#   blender -b --disable-autoexec -P regrade.py -- IN.exr OUT_BASE [--gain hall=0.6] [--gain sun=1.1,1.0,0.9] [--exposure X] [--vignette V] [--bloom B] [--no-denoise]
# Reads IN.json (next to the EXR) for the view transform, look and exposure of the original drawing when present.
import json
import os
import sys

import bpy

sys.dont_write_bytecode = True


def load_comp_asset(name):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    path = os.path.join(bpy.utils.system_resource('DATAFILES'), 'assets', 'nodes', 'compositing_nodes_essentials.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.node_groups = [name]
    return bpy.data.node_groups[name]


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    exr, out = argv[0], argv[1]
    gains, exposure, vignette, bloom, denoise = {}, None, 0.55, 0.05, True
    i = 2
    while i < len(argv):
        if argv[i] == '--gain':
            g, v = argv[i + 1].split('=')
            vals = [float(x) for x in v.split(',')]
            gains[g] = vals if len(vals) == 3 else [vals[0]] * 3
            i += 2
        elif argv[i] == '--exposure':
            exposure = float(argv[i + 1]); i += 2
        elif argv[i] == '--vignette':
            vignette = float(argv[i + 1]); i += 2
        elif argv[i] == '--bloom':
            bloom = float(argv[i + 1]); i += 2
        elif argv[i] == '--no-denoise':
            denoise = False; i += 1
        else:
            raise SystemExit('unknown option ' + argv[i])
    meta = {}
    jp = os.path.splitext(exr)[0] + '.json'
    if os.path.exists(jp):
        meta = json.load(open(jp))
    img = bpy.data.images.load(exr, check_existing=False)
    try:
        import OpenImageIO as oiio
        inp = oiio.ImageInput.open(exr)
        w, h = inp.spec().width, inp.spec().height
        inp.close()
    except Exception:
        w, h = img.size
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    vs = sc.view_settings
    vs.view_transform = meta.get('view_transform', 'AgX')
    try:
        vs.look = meta.get('look', 'AgX - Punchy')
    except Exception:
        pass
    vs.exposure = exposure if exposure is not None else meta.get('exposure', 0.5)
    try:
        sc.render.compositor_device = 'CPU'
    except Exception:
        pass
    tree = bpy.data.node_groups.new('regrade', 'CompositorNodeTree')
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    feed = tree.nodes.new('CompositorNodeImage')
    feed.image = img
    try:
        feed.layer = 'ViewLayer'          # the EXR also holds a 'Composite' part; the light groups live in 'ViewLayer'
    except Exception as e:
        print('layer not set:', e)
    feed.location = (-700, 0)
    outn = tree.nodes.new('NodeGroupOutput')
    outn.location = (1100, 0)
    groups = [o.name[len('Combined_'):] for o in feed.outputs if o.name.startswith('Combined_') and o.enabled]
    if not groups:
        raise SystemExit('no light-group layers in ' + exr)
    bad = [g for g in gains if g not in groups]
    if bad:
        raise SystemExit(f'unknown group {bad}; available {groups}')

    def mix(blend, a, b):
        m = tree.nodes.new('ShaderNodeMix')
        m.data_type, m.blend_type = 'RGBA', blend
        m.inputs['Factor'].default_value = 1.0
        tree.links.new(m.inputs[6], a)
        if isinstance(b, tuple):
            m.inputs[7].default_value = (*b, 1.0)
        else:
            tree.links.new(m.inputs[7], b)
        return m.outputs[2]
    acc = None
    for g in groups:
        term = mix('MULTIPLY', feed.outputs['Combined_' + g], tuple(gains.get(g, [1.0, 1.0, 1.0])))
        acc = term if acc is None else mix('ADD', acc, term)
    sock = acc
    if denoise:       # the light-group layers are not denoised by Cycles; one denoise of the re-balanced sum makes it match the drawn picture
        dn = tree.nodes.new('CompositorNodeDenoise')
        tree.links.new(dn.inputs['Image'], sock)
        sock = dn.outputs['Image']
    x = -300
    if bloom:
        gl = tree.nodes.new('CompositorNodeGlare')
        gl.inputs['Type'].default_value = 'Bloom'
        try:
            gl.inputs['Quality'].default_value = 'High'
        except Exception:
            pass
        gl.inputs['Threshold'].default_value = 2.0
        gl.inputs['Strength'].default_value = bloom
        gl.inputs['Size'].default_value = 0.5
        tree.links.new(gl.inputs['Image'], sock)
        sock = gl.outputs['Image']
    if vignette:
        v = tree.nodes.new('CompositorNodeGroup')
        v.node_tree = load_comp_asset('Vignette')
        v.inputs['Factor'].default_value = vignette
        v.inputs['Feather'].default_value = 0.4
        tree.links.new(v.inputs['Image'], sock)
        sock = v.outputs[0]
    tree.links.new(outn.inputs[0], sock)
    sc.compositing_node_group = tree
    sc.render.use_compositing = True
    ims = sc.render.image_settings
    ims.media_type = 'IMAGE'
    ims.file_format = 'PNG'
    ims.color_depth = '8'
    ims.color_mode = 'RGB'
    ims.color_management = 'FOLLOW_SCENE'
    sc.render.filepath = out + '.png'
    bpy.ops.render.render(write_still=True)
    print('REGRADE_DONE', out + '.png', 'groups', groups, 'gains', gains, 'exposure', vs.exposure)


main()
