# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE PICTURE RUNNER (Blender side). Opens ONE scene file (read-only: it is never saved), loads the set, then draws a LIST of pictures from a job file, one after another, so
# Blender loads once.
#     blender -b --disable-autoexec SCENE.blend --python harness/runner.py -- JOBS.json OUT_FOLDER
# A job: {"name", "camera", "light" (rig A..E), "state" (dry, wet, heavy or w0.85p0.5), "size": [w, h, samples], "look", "view", "plate_height" (dots, default the plate's),
#         "keep_png", "dials": {layer: {dial: value}}, "master", "hide_roles": [...], "tag"}.
# LOOKS    today = the scene exactly as it is (the earlier layers and the kit not on); base = the earlier layers (WETNESS, JOINTS, RUBBISH) only, no kit layer;
#          kit_all = base plus every registered kit layer; kit:a,b = base plus only those layers; solo:a = base plus that one layer.
#          A scene whose set has no earlier layers draws base as today. Looks are drawn in the order today, base, kit (jobs are sorted, so 'today' always comes first); going back to
#          today takes everything off again from the snapshots (never the earlier scripts' own remove()).
# VIEWS    beauty; layer:<key> (that layer's own Mask output, plain light); mask:<name> (a bus mask, plain light; up to three names a+b+c go to R, G, B); class (a flat number per
#          role, 16 bit); puddles (the water layer's puddle mask, red); plan:<name> (a bus mask seen from above over the ground bounds, ground only);
#          plan:rubbish_heap (the earlier rubbish mask seen from above, for the habitat fields).
# OUTPUT   <name>.jpg (quality 90) and <name>.json (seconds, job hash, look, notes); the PNG too only when keep_png or the view needs exact numbers. A picture whose json has the
#          same job hash is SKIPPED; a picture left from another job (a different hash) is redrawn, so a stale picture on the rented machine can never come back as the answer.
import hashlib
import json
import math
import os
import sys
import time
import traceback

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import kit as kit_module  # noqa: E402
from harness import cameras, class_pass, layers, legacy_stack, lighting, render as render_module  # noqa: E402
from masks import bus as bus_module, debug, pack as pack_module, scale as scale_module  # noqa: E402

LOOK_RANK = {'today': 0, 'base': 1}
EXACT_VIEWS = ('class', 'depth', 'puddles', 'dirt', 'joint_mask')


def job_hash(job):
    keep = {k: v for k, v in job.items() if k not in ('name',)}
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:16]


def parse_state(state):
    table = {'dry': (0.0, 0.0), 'wet': (0.85, 0.5), 'heavy': (1.0, 0.8)}
    if state in table:
        return table[state]
    wet, pud = state[1:].split('p')
    return float(wet), float(pud)


class Runner:
    def __init__(self, spec, out_folder):
        self.spec = spec
        self.out = out_folder
        os.makedirs(out_folder, exist_ok=True)
        self.scene = bpy.context.scene
        self.kit = kit_module.Kit.load(spec['set'], scene_id=spec.get('scene'), strict=False)
        self.settings = self.kit.settings
        self.has_pack = False
        try:
            bus_module.attach(self.kit)
            self.has_pack = True
        except (OSError, KeyError, FileNotFoundError):
            pass
        self.cams, self.cam_notes = cameras.make_all(self.settings, self.kit.scene_id, spec.get('feature_dirs', []))
        self.registered, self.register_errors = layers.register_builders(self.kit)
        layers.register_templates(self.kit)
        self.stack = None
        self.current_look = 'today'
        self.kit_applied = False
        self.timings = {}
        self.kit.prepare()
        self.plan_cam = None
        self.drawn = 0
        self.t_start = time.time()

    # ---------------------------------------------------------------- looks
    def reset_to_today(self):
        self.kit.remove()
        if self.stack is not None:
            self.stack.reset()
        self.stack = None
        self.kit_applied = False
        self.kit.prepare()
        self.current_look = 'today'

    def ensure_stack(self):
        if self.stack is None:
            self.stack = legacy_stack.LegacyStack(self.kit)
            self.stack.apply(pieces=True)
        return self.stack

    def set_look(self, look, dials=None, master=1.0):
        want_layers = None
        if look == 'today':
            if self.current_look != 'today':
                self.reset_to_today()
            return
        stack = self.ensure_stack()
        if stack.present():
            stack.look('rubbish')
        if look == 'base':
            want_layers = []
        elif look == 'kit_all':
            want_layers = [k for k in self.kit.registry if not k.startswith('template_')]
        elif look.startswith('kit:'):
            want_layers = look[4:].split(',')
        elif look.startswith('solo:'):
            want_layers = [look[5:]]
        else:
            raise ValueError('unknown look ' + look)
        # layers wanted but never applied: apply now; others: on or off
        new = [k for k in want_layers if k not in self.kit.active]
        if new:
            self.kit.apply(layers=new, overrides=dials)
        for key in list(self.kit.active):
            if key in want_layers:
                self.kit.layer_on(key)
            else:
                self.kit.layer_off(key)
        for layer, values in (dials or {}).items():
            if layer in self.kit.active:
                self.kit.set_dials(layer, **values)
        self.kit.set_master(master)
        self.current_look = look

    # ---------------------------------------------------------------- drawing
    def eevee(self, w, h, samples, exact=False):
        s = self.scene
        s.render.engine = 'BLENDER_EEVEE'
        s.render.resolution_x, s.render.resolution_y = w, h
        s.render.resolution_percentage = 100
        s.render.image_settings.file_format = 'PNG'
        s.render.image_settings.color_mode = 'RGB'
        s.render.image_settings.color_depth = '16' if exact else '8'
        s.eevee.taa_render_samples = samples
        s.eevee.use_raytracing = not exact
        s.eevee.shadow_ray_count, s.eevee.shadow_step_count = 4, 16
        if hasattr(s.eevee, 'shadow_pool_size') and w > 1080:
            s.eevee.shadow_pool_size = '1024'
            s.eevee.shadow_resolution_scale = min(1.0, 1080 / w)
        s.render.filter_size = 0.0 if exact else 1.5

    def raw_view(self, on):
        render_module.plain_light(on)

    def draw_job(self, job):
        name = job['name']
        json_path = os.path.join(self.out, name + '.json')
        digest = job_hash(job)
        jpg_path = os.path.join(self.out, name + '.jpg')
        png_path = os.path.join(self.out, name + '.png')
        if os.path.exists(json_path):
            try:
                old = json.load(open(json_path))
            except ValueError:
                old = {}
            if old.get('job_hash') == digest and (os.path.exists(jpg_path) or os.path.exists(png_path)):
                print('SKIP', name, flush=True)
                return
        started = time.time()
        self.drawn += 1
        view = job.get('view', 'beauty')
        w, h, samples = job.get('size', [540, 960, 16])
        exact = view in EXACT_VIEWS or view.startswith('plan') or view == 'class' or view.startswith('mask') or view.startswith('layer')
        self.set_look(job.get('look', 'today'), job.get('dials'), job.get('master', 1.0))
        t_look = time.time() - started
        wetness, puddles = parse_state(job.get('state', 'dry'))
        if self.current_look != 'today':
            self.kit.set_state(wetness, puddles)
        lighting.set_rig(self.settings, job.get('light', 'A'))
        camera_name = job.get('camera')
        undo_hidden = []
        for role in job.get('hide_roles', []):
            for obj_name in self.kit.role_map.objects_of([role]):
                obj = bpy.data.objects[obj_name]
                if not obj.hide_render:
                    obj.hide_render = True
                    undo_hidden.append(obj)
        undo_view = None
        plan_cam = None
        try:
            if view.startswith('plan'):
                plan_cam = debug.plan_camera(self.settings)
                self.scene.camera = plan_cam
                ground = self.kit.role_map.objects_of(self.settings.geometry['ground']['roles'])
                for obj in self.scene.objects:
                    if obj.type == 'MESH' and obj.name not in ground and not obj.hide_render:
                        obj.hide_render = True
                        undo_hidden.append(obj)
            elif camera_name:
                self.scene.camera = self.cams[camera_name]
            cam = self.scene.camera
            plate_h = job.get('plate_height') or self.settings.get('plate')['size'][1]
            if not view.startswith('plan'):
                scale_module.set_scale(self.kit, cameras.dot_angle(cam, plate_h), scale_module.painter_widen(job.get('painter_scale', (self.settings.get('plate') or {}).get('painter_scale', 0.45))))
            self.eevee(w, h, samples, exact)
            if view == 'beauty':
                pass
            elif view == 'class':
                self.raw_view(True)
                bpy.context.view_layer.material_override = class_pass.make_material()
                undo_view = ('override',)
            elif view == 'depth':
                self.raw_view(True)
                bpy.context.view_layer.material_override = class_pass.make_depth_material()
                undo_view = ('override',)
            elif view.startswith('mask:') or view.startswith('plan:') and view != 'plan:rubbish_heap':
                names = view.split(':', 1)[1].split('+')
                self.raw_view(True)
                undo_view = ('mask', debug.show_mask(self.kit, names[0] if len(names) == 1 else names))
            elif view == 'plan:rubbish_heap':
                self.raw_view(True)
                stack = self.ensure_stack()
                stack.look('rubbish')
                stack.pieces(False)
                undo_view = ('rubbish', stack.m['ar'].show_mask('total', raw=True))
            elif view.startswith('layer:'):
                self.raw_view(True)
                undo_view = ('mask', debug.show_layer(self.kit, view.split(':', 1)[1]))
            elif view == 'puddles':
                self.raw_view(True)
                undo_view = ('mask', debug.show_puddles(self.kit))
            elif view == 'dirt':
                self.raw_view(True)
                self.ensure_stack().pieces(False)
                undo_view = ('mask', debug.show_stage(self.kit, 'rubbish', 'Rubbish Mask'))
            elif view == 'joint_mask':
                undo_view = None
                self.draw_joint_mask(png_path, w, h)
            else:
                raise ValueError('unknown view ' + view)
            bpy.context.view_layer.update()
            t_draw = time.time()
            self.scene.render.filepath = png_path
            if view != 'joint_mask':
                bpy.ops.render.render(write_still=True)
            seconds = round(time.time() - t_draw, 2)
            if view in ('beauty',) or not exact:
                self.save_jpg(png_path, jpg_path)
            elif job.get('jpg'):
                self.save_jpg(png_path, jpg_path)
            if not (job.get('keep_png') or exact):
                os.remove(png_path)
            info = dict(name=name, job_hash=digest, look=job.get('look'), view=view, seconds=seconds, seconds_look_change=round(t_look, 2), seconds_job=round(time.time() - started, 2),
                        index=self.drawn, since_start=round(time.time() - self.t_start, 1), size=[w, h, samples],
                        camera=camera_name, light=job.get('light'), state=job.get('state'), notes=self.cam_notes.get(camera_name), pieces=self.piece_count())
            json.dump(info, open(json_path, 'w'), indent=1)
            print('DRAWN', name, seconds, 's', flush=True)
        except Exception:
            print('JOB FAILED', name, flush=True)
            traceback.print_exc()
            sys.stdout.flush()
            json.dump(dict(name=name, job_hash='FAILED', error=traceback.format_exc()), open(json_path, 'w'))
        finally:
            if undo_view:
                if undo_view[0] == 'override':
                    bpy.context.view_layer.material_override = None
                    self.raw_view(False)
                elif undo_view[0] in ('mask', 'rubbish'):
                    undo_view[1]()
                    self.raw_view(False)
            for obj in undo_hidden:
                obj.hide_render = False
            if plan_cam is not None:
                bpy.data.objects.remove(plan_cam)
            self.scene.render.filter_size = 1.5

    def draw_joint_mask(self, path, w, h):
        """R = joint, G = stone face, B = road for the sett joint measure (the earlier study's mask, Cycles, drawn through its own pinned helper)."""
        lv = legacy_stack.modules()['lv']
        # the earlier study drew this mask without the separate 3D litter pieces (they are left out of the joint measure by the rubbish mask anyway), so they are hidden here too
        stack = self.stack
        if stack is not None and stack.present():
            stack.pieces(False)
        try:
            lv.render_mask(path, w, h)
        finally:
            if stack is not None and stack.present():
                stack.look('rubbish')

    def piece_count(self):
        try:
            return self.stack.piece_count() if self.stack is not None else 0
        except Exception:
            return None

    def save_jpg(self, png_path, jpg_path):
        image = bpy.data.images.load(png_path)
        s = self.scene.render.image_settings
        keep = (s.file_format, s.color_depth, s.quality)
        s.file_format, s.quality = 'JPEG', 90
        image.save_render(jpg_path, scene=self.scene)
        s.file_format, s.color_depth, s.quality = keep[0], keep[1], keep[2]
        bpy.data.images.remove(image)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    spec = json.load(open(args[0]))
    out = args[1]
    t0 = time.time()
    runner = Runner(spec, out)
    jobs = sorted(enumerate(spec['jobs']), key=lambda it: (LOOK_RANK.get(it[1].get('look', 'today'), 2), it[0]))
    first_seconds = None
    for _, job in jobs:
        runner.draw_job(job)
    summary = dict(set=spec['set'], scene=runner.kit.scene_id, jobs=len(jobs), seconds_total=round(time.time() - t0, 1), registered=runner.registered,
                   register_errors=runner.register_errors, camera_notes=runner.cam_notes, kit_report=runner.kit.report() if runner.kit.prepared else {})
    json.dump(summary, open(os.path.join(out, 'run_summary.json'), 'w'), indent=1, default=str)
    print('ALL JOBS DONE', summary['seconds_total'], flush=True)


if __name__ == '__main__':
    main()
