# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PLAN VIEWS OF THE GROUND LAYERS (Blender side): draws a layer's own Mask output (the whole, or one named part) seen STRAIGHT FROM ABOVE over the whole ground picture area, as
# 8-bit grey pictures, plus a "class" picture (one flat number per role) so a measure can say how much of the road, the flags or the kerb a mark covers. These are the numbers
# for the period caps (share of flags with a crack, share of the road under tar, share of joint length with moss ...) and for the zones test (nothing green on the crown or in
# the traffic lanes): they do not depend on a camera.
#     blender -b --disable-autoexec SCENE.blend --python ground/plan_views.py -- SET SCENE OUT_FOLDER LOOK ITEMS [WIDTHxHEIGHT] [--hide-today]
#   ITEMS: comma separated 'layer' or 'layer:part' (part = a name from apply_ground.PARTS or a number), e.g. dirt:tar,groundmoss:joint_moss,class
# From above the camera is 200 m away, so the layers' distance fades are switched off for the view (fade and handover distances 10 km, near_only 10 km) and the size of a plate
# dot is set to a typical near-camera value (dot_mm, default 2.5 mm), so a crack is drawn at the width it has near the camera and the shares do not depend on the view.
# Everything that is not ground is hidden. Nothing is saved; the scene is read only.
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

import bpy  # noqa: E402

from harness import class_pass, runner as runner_module  # noqa: E402
from masks import debug, scale as scale_module  # noqa: E402
from ground import apply_ground  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
set_id, scene_id, out, look, items = args[0], args[1], args[2], args[3], args[4].split(',')
size = tuple(int(v) for v in args[5].split('x')) if len(args) > 5 and 'x' in args[5] else (450, 4200)
DOT_MM = 2.5
os.makedirs(out, exist_ok=True)


def main():
    spec = dict(set=set_id, scene=scene_id, pack=True, feature_dirs=[], jobs=[])
    r = runner_module.Runner(spec, out)
    kit = r.kit
    r.set_look(look)
    r.kit.set_state(float(os.environ.get('WK_WET', '0.85')), float(os.environ.get('WK_PUDDLES', '0.5')))
    scene = bpy.context.scene
    # plan camera over the ground bounds, only the ground visible
    plan = debug.plan_camera(kit.settings)
    scene.camera = plan
    ground = set(kit.role_map.objects_of(kit.settings.geometry['ground']['roles']))
    for obj in scene.objects:
        if obj.type == 'MESH' and obj.name not in ground:
            obj.hide_render = True
    # no distance fades, a plate dot of DOT_MM at every point
    widen = scale_module.painter_widen((kit.settings.get('plate') or {}).get('painter_scale', 0.45))
    for material in bpy.data.materials:
        tree = material.node_tree
        if tree is None:
            continue
        for node in tree.nodes:
            if node.get('wk') == 'scale':
                node.inputs['Fade Start'].default_value = 1e4
                node.inputs['Fade End'].default_value = 2e4
                node.inputs['Handover Start'].default_value = 1e4
                node.inputs['Handover End'].default_value = 2e4
                node.inputs['Dot Angle'].default_value = (DOT_MM / 1000.0) / (200.0 * widen)
    for key in kit.active:
        if 'near_only' in apply_dials(key):
            kit.set_dials(key, near_only=1e4)
    s = scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y = size
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'BW'
    s.render.image_settings.color_depth = '8'
    s.eevee.taa_render_samples = 1
    s.eevee.use_raytracing = False
    s.render.filter_size = 0.0
    s.render.dither_intensity = 0.0
    stats = {}
    for item in items:
        t = time.time()
        name = item.replace(':', '_').replace('+', '-')
        path = os.path.join(out, f'plan_{name}.png')
        r.raw_view(True)
        try:
            if item == 'class':
                bpy.context.view_layer.material_override = class_pass.make_material()
                s.render.image_settings.color_depth = '16'
                s.render.image_settings.color_mode = 'BW'
                undo = None
            elif item.startswith('bus:'):
                names = item[4:].split('+')
                s.render.image_settings.color_depth = '8'
                s.render.image_settings.color_mode = 'RGB' if len(names) > 1 else 'BW'
                undo = debug.show_mask(kit, names[0] if len(names) == 1 else names)
                from ground import ground_common as gc
                for chain in kit.chains.values():
                    gc.make_tx_repeat(chain)
            else:
                layer, _, part = item.partition(':')
                s.render.image_settings.color_depth = '8'
                undo = apply_ground.show_layer(kit, layer, part or None)
            s.render.filepath = path
            bpy.context.view_layer.update()
            bpy.ops.render.render(write_still=True)
            if undo:
                undo()
            bpy.context.view_layer.material_override = None
        except Exception:
            traceback.print_exc()
            bpy.context.view_layer.material_override = None
        r.raw_view(False)
        stats[item] = round(time.time() - t, 1)
        print('PLAN', item, stats[item], flush=True)
    json.dump(dict(size=list(size), seconds=stats, look=look, ground_bounds=kit.settings.geometry['ground']['bounds'], dot_mm=DOT_MM), open(os.path.join(out, 'plan_info.json'), 'w'))


def apply_dials(key):
    from apply import dials
    spec = dials.TABLE.layers.get(key)
    return spec.names() if spec else []


main()
