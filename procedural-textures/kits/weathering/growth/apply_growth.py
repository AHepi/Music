# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GROWTH LAYER'S DOOR INTO THE KIT. The harness (harness/layers.py) finds this file by itself and calls register(kit), so the layer `growth` appears in every look
# (`kit_all`, `solo:growth`). Growth is not a material layer: it is a hidden host object with a Geometry Nodes modifier that stands small separate 3D weeds and moss cushions
# on the ground, so it does not touch any material. To the kit it looks like any other layer (apply, layer_on, layer_off, set_dials, set_master, remove, set_state), because
# register() wraps those six methods of the kit it is given so that they reach the host as well.
#   register(kit)                    makes the layer known; installs the wrappers, the wetness hook and the scale hook (the runner tells the scale helper the camera's dot size
#                                    for every picture; the pieces need the same number, so masks.scale.set_scale is wrapped once)
#   apply(kit, look=None, overrides=None)   kit.apply for the growth layer only
#   remove(kit)                      host, scatter, pieces, materials and private pictures out; nothing of the scene is left
#   set_dials(kit, **values)         dials of the layer (by name); weed_cover, the shares and the amounts re-count the plants (a few seconds at most)
#   set_state(kit, wetness, puddles) wet look of the pieces (kit.set_state reaches it too)
#   pieces(kit, visible)             show or hide the host (the earlier rubbish pieces have the same call)
#   show_layer(kit)                  the checking view `layer:growth`: every piece plain white light, everything else black; returns undo()
#   table(kit, camera=None)          every plant of the picture from a camera: position, kind, size (report_growth writes pieces.json from it)
# What the set provides (nothing of it is in this code): which roles are the ground the plants stand on (apply.growth.targets), which piece sets (apply.growth.piece_sets, species.json),
# the rest in the set's `growth` block (or the sidecar growth/growth_sets/<set id>.json until the integrator moves it): objects whose litter plants keep clear of, the gutter side,
# the wall-foot strip, the axis along which moss strings lie, the calibration camera.
# HOW MANY: the dials weed_cover (green cover of the ground inside the distance), gutter_tuft_share, wall_foot_share, cushion_cover and toadflax_clumps are TARGET counts for the
# window round the calibration camera (the set's default camera); calibrate() lays the plants once with test gains, counts, and sets the gains so the counts come out at the
# targets (never over max_pieces: all gains are scaled down together, the zones never move). A plant stands in the same place whichever camera draws the picture.
import copy
import json
import math
import os
import sys
import time

import bpy
import numpy as np

from apply import dials, kit as kit_module
from masks import scale as scale_module

from . import dials_growth, local_masks, pieces as pieces_module, scatter
from .growth_names import LAYER_KEY, MASK_NAMES, SECTION_DIR, LOOK_DIR, growth_section, look_extras, kinds_of_sets  # noqa: F401

HERE = os.path.dirname(os.path.abspath(__file__))
SITES_IMAGE = 'WKG sites'
WET_HOOKED = '_wkg_hooked'


# ------------------------------------------------------------------------------------------------------------------------------ the system
class GrowthSystem:
    def __init__(self, kit):
        self.kit = kit
        self.species = pieces_module.load_species()
        self.library = None
        self.engine = None
        self.host = None
        self.values = {}
        self.attached = False
        self.on = True
        self.arrays = None
        self.sites = None
        self.stats = None
        self.calibration = {}
        self.kind_specs = []
        self.targets = []
        self.section = {}
        self.wet = 0.0
        self.notes = []
        self.timings = {}
        self._cal_key = None
        self._struct_key = None

    # ---------------------------------------------------------------- the pieces and the tree
    def _target_objects(self):
        roles = self.section['targets'].get('roles', [])
        names = self.kit.role_map.objects_of(self.kit.settings.expand_roles(roles)) if roles else []
        objs = [bpy.data.objects[n] for n in names if n in bpy.data.objects and bpy.data.objects[n].type in ('MESH', 'CURVE', 'SURFACE')]
        return objs

    def _max_face_extent(self, objects):
        """The biggest face (bounding box diagonal, metres) of the targets: faces within the pieces distance plus this margin get candidate points."""
        biggest = 1.0
        for obj in objects:
            mesh = obj.data
            if not hasattr(mesh, 'polygons') or len(mesh.polygons) == 0:
                continue
            co = np.empty(len(mesh.vertices) * 3, np.float32)
            mesh.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            loops = np.empty(len(mesh.loops), np.int32)
            mesh.loops.foreach_get('vertex_index', loops)
            start = np.empty(len(mesh.polygons), np.int32)
            mesh.polygons.foreach_get('loop_start', start)
            pts = co[loops]
            lo = np.minimum.reduceat(pts, start, axis=0)
            hi = np.maximum.reduceat(pts, start, axis=0)
            scale = np.abs(np.array(obj.matrix_world.to_scale()))
            biggest = max(biggest, float(np.linalg.norm((hi - lo) * scale, axis=1).max()))
        return biggest

    def _weight_variants(self, kind_name, info, flower_share):
        """Dandelions: the collection holds the plain variants repeated and the flowering ones, so a uniform pick gives a flower_share of flowering plants. Returns the child count."""
        spec = info['spec']
        objs = info['objects']
        if spec['builder'] != 'rosette_toothed':
            return len(objs)
        col = info['collection']
        for obj in list(col.objects):
            col.objects.unlink(obj)
        plain, flower, seed = objs[:-2], objs[-2], objs[-1]
        total = 24
        n_flowers = int(round(flower_share * total))
        n_flower, n_seed = (n_flowers + 1) // 2, n_flowers // 2
        children = [flower] * n_flower + [seed] * n_seed
        i = 0
        while len(children) < total:
            children.append(plain[i % len(plain)])
            i += 1
        made = 0
        counts = {}
        for obj in children:
            counts[obj.name] = counts.get(obj.name, 0) + 1
            if counts[obj.name] == 1:
                col.objects.link(obj)
            else:
                copy_obj = bpy.data.objects.new(f'{obj.name}_c{counts[obj.name]}', obj.data)
                for key in ('wk_kind', 'wk_variant', 'wk_size_m', 'wk_width_m', 'wk_height_m'):
                    copy_obj[key] = obj[key]
                col.objects.link(copy_obj)
                self.library.objects.append(copy_obj)
            made += 1
        return made

    def _kind_specs(self):
        v = self.values
        shares = {}
        weed_total = 0.0
        for name in self.kind_names:
            spec = self.species['kinds'][name]
            if spec['group'] == 'weed' and spec.get('count_dial') is None:
                weed_total += spec['share']
        dead = float(v.get('dead_grass_share', 0.15))
        specs = []
        for name in self.kind_names:
            sp = self.species['kinds'][name]
            info = self.library.kinds[name]
            share = sp['share']
            if name == 'grass':
                share = (self.species['kinds']['grass']['share'] + self.species['kinds'].get('dead_grass', {'share': 0})['share']) * (1.0 - dead)
            elif name == 'dead_grass':
                share = (self.species['kinds']['grass']['share'] + sp['share']) * dead
            pop = 'moss' if sp['group'] == 'moss' else ('toad' if sp.get('count_dial') else 'weed')
            width = info['mean_width']
            spacing = sp.get('spacing_m') or (0.07 if pop == 'moss' else min(0.20, max(0.08, 0.6 * width)))
            children = self._children[name]
            specs.append(dict(name=name, group=sp['group'], pop=pop, collection=info['collection'], variants=children, scale=tuple(sp['scale']), min_dots=sp['min_dots'],
                              width_m=width, footprint_m2=info['mean_footprint'], upright=sp['upright'], spacing=spacing, density_max=(30.0 if pop == 'moss' else (4.0 if pop == 'toad' else 8.0)),
                              yaw=('axis' if pop == 'moss' else 'free'), prefer=sp['prefer'], share_dial=f'share_{name}', share=share))
        return specs

    def build(self):
        """Pieces, private pictures, the tree and the host (everything but the dial values)."""
        t0 = time.time()
        kit = self.kit
        self.section = growth_section(kit.settings)
        set_names = self.section.get('piece_sets') or ['weeds', 'moss_cushions']
        self.kind_names = kinds_of_sets(self.species, set_names)
        if self.library is None:
            self.library = pieces_module.Library(self.species)
            self.library.build(self.kind_names)
        self._children = {name: self._weight_variants(name, self.library.kinds[name], float(self.values.get('flower_share', 0.08))) for name in self.kind_names}
        pack = kit.mask_pack
        if pack is None:
            raise RuntimeError('the growth layer needs the scene\'s mask pack (masks/packs/<set>/<scene>): the kit has none loaded')
        masks = local_masks.read_masks(pack, MASK_NAMES)
        ground_z, has_ground, role_id = local_masks.read_ground(pack)
        grid = pack.manifest['ground']
        role_names = pack.manifest['stats']['ground']['role_names']
        wall_reach = float(kit.settings.geometry.get('wall_reach_m', 1.275))
        sites = local_masks.make_sites(masks, has_ground, role_id, role_names, grid, self.section, wall_reach)
        self.arrays = dict(masks=masks, ground_z=ground_z, has_ground=has_ground, grid=grid, wall_reach=wall_reach)
        self.sites = sites
        image = local_masks.make_image(SITES_IMAGE, sites)
        mask_images = {}
        for name in MASK_NAMES:
            entry = pack.entry('GP', name)
            if entry is not None and not entry['picture'].startswith('tx:'):
                mask_images[name] = (pack.image(entry['picture']), entry['channel'])
        litter = pack.entry('GP', 'litter_dist')
        litter_max = None
        if litter is not None:                          # the baked distance to the nearest litter piece (masks/stamp_pack.py --litter): no 3D proximity search at drawing time
            mask_images['litter_dist'] = (pack.image(litter['picture']), litter['channel'])
            litter_max = float(pack.manifest['pictures'][litter['picture']].get('max_m', 0.25))
        mask_images['gutter_strip'] = (image, 'R')
        mask_images['wall_strip'] = (image, 'G')
        mask_images['has_ground'] = (image, 'B')
        self.targets = self._target_objects()
        avoid = [bpy.data.objects[n] for n in (self.section.get('avoid_pieces_of') or {}).get('objects', []) if n in bpy.data.objects]
        if litter_max is not None:
            avoid = []
        options = dict(avoid=avoid, litter_max_m=litter_max or 0.25, yaw_axis=self.section.get('yaw_axis'), align_normal=float(self.section['targets'].get('align_normal', 0.0)), realise_targets=True)
        self.kind_specs = self._kind_specs()
        self.engine = scatter.Engine()
        self.engine.build(self.kind_specs, self.targets, mask_images, grid, options)
        self.engine.set_dial('select_margin', max(3.0, 1.1 * self._max_face_extent(self.targets)))
        self.engine.set_dial('wall_reach_m', wall_reach)
        water = (kit.settings.geometry.get('water') or {})
        if water.get('level_z') is not None:
            self.engine.set_dial('water_z', float(water['level_z']))
        self.host = self.engine.add_host(bpy.context.scene)
        self.timings['build_s'] = round(time.time() - t0, 2)
        self.attached = True

    # ---------------------------------------------------------------- attach, sync, calibrate
    def attach(self, values):
        self.values = dict(values)
        self.build()
        self.sync(calibrate=True)
        self.kit.add_state_hook(self.set_state)
        self.set_state(*getattr(self.kit, 'state', (0.0, 0.0)))

    def effective(self):
        return dials.effective_amount(self.values, self.kit.master)

    def _push(self):
        v, e = self.values, self.engine
        amount = self.effective() if self.on else 0.0
        e.set_dial('cull_cos', self.cone_cos(e.get_dial('dot_angle')))
        e.set_dials(seed=float(v.get('seed', 0.0)), amount=amount, weeds_amount=v['weeds_amount'], cushions_amount=v['cushions_amount'], distance=v['distance'],
                    distance_fade=v['distance_fade'], piece_size=v['piece_size'], min_spacing=v['min_spacing'], inflate_limit=v['piece_inflate_limit'], tilt_random=v['tilt_random'],
                    rubbish_thin_max=v['rubbish_thin_max'], rubbish_heap_min=v['rubbish_heap_min'], moss_smother_from=v['moss_smother_from'], moss_smother_to=v['moss_smother_to'],
                    existing_avoid=v['existing_avoid'], avoid_m=v['avoid_m'], max_pieces=v['max_pieces'], realise=v['realise'], mask_only_kind=v['show_kind'], min_dots_scale=v['min_dots_scale'])
        for spec in self.kind_specs:
            e.set_dial(spec['share_dial'], spec['share'])
        pieces_module.set_value_node('GAIN', v['colour_gain'] * float(self.species['material'].get('albedo_gain', 1.0)))
        pieces_module.set_value_node('SAT', v['colour_sat'] * float(self.species['material'].get('saturation_gain', 1.0)))
        pieces_module.set_value_node('WET_DARK', v['wet_dark'])
        cal = self.calibration
        if cal:
            e.set_dials(g_bg=cal['g_bg'], g_wall=cal['g_wall'], g_gut=cal['g_gut'], g_moss=cal['g_moss'], g_toad=cal['g_toad'], scale_total=cal['scale_total'])

    def _structural_key(self):
        v = self.values
        return (round(float(v.get('flower_share', 0.0)), 4),)

    def _count_key(self):
        v = self.values
        keys = ('weed_cover', 'gutter_tuft_share', 'wall_foot_share', 'cushion_cover', 'toadflax_clumps', 'min_spacing', 'distance', 'distance_fade', 'max_pieces', 'dead_grass_share',
                'rubbish_thin_max', 'rubbish_heap_min', 'moss_smother_from', 'moss_smother_to', 'existing_avoid', 'avoid_m', 'seed', 'weeds_amount', 'cushions_amount')
        return tuple(round(float(v.get(k, 0.0)), 5) for k in keys)

    def sync(self, calibrate=False):
        """Pushes every dial value into the tree; rebuilds when the flower share changed; re-counts when a count dial changed (or calibrate=True)."""
        if not self.attached:
            return
        if self._struct_key is not None and self._struct_key != self._structural_key():
            self.rebuild()
        self._struct_key = self._structural_key()
        self._push()
        if calibrate or self._cal_key != self._count_key():
            if self.effective() > 0.0 and self.on:
                self.calibrate()
            self._cal_key = self._count_key()
            self._push()

    def rebuild(self):
        """Tree and host again (pieces kept)."""
        self.remove_tree()
        self.build()

    def calibration_camera(self):
        """(position, forward unit vector, field of view in degrees) of the camera the counts are made from: the set's `growth.calibration_camera` (a name of the set's camera table;
        a camera 'from_file' is the scene's own camera), else the scene's camera."""
        scene = bpy.context.scene
        name = self.section.get('calibration_camera')
        cam_obj, fov = None, 40.0
        for spec in (self.kit.settings.get('cameras') or []):
            if spec.get('name') == name:
                fov = float(spec.get('fov_v', 40.0))
                if spec.get('location') and spec.get('quaternion_wxyz') and not spec.get('from_file'):
                    from mathutils import Quaternion, Vector
                    q = Quaternion(spec['quaternion_wxyz'])
                    fwd = q @ Vector((0.0, 0.0, -1.0))
                    return tuple(spec['location']), (fwd.x, fwd.y, fwd.z), fov
                if spec.get('from_file'):
                    cam_obj = scene.camera
        cam_obj = cam_obj or scene.camera
        if cam_obj is None:
            raise RuntimeError('no camera to count plants from')
        from mathutils import Vector
        fwd = cam_obj.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        if cam_obj.type == 'CAMERA':
            fov = math.degrees(cam_obj.data.angle_y)
        return tuple(cam_obj.matrix_world.translation), (fwd.x, fwd.y, fwd.z), fov

    def plate_height(self):
        """The plate's height in dots (the set's plate.size), the height the runner's dot angle is made for."""
        size = (self.kit.settings.get('plate') or {}).get('size')
        return float(size[1]) if size else 2000.0

    def cone_cos(self, dot_angle, plate_h=None):
        """Cosine of the half angle of the cone round the camera's axis inside which plants are made: the picture's half height angle (from the dot angle and the plate height, a
        taller or wider picture is never cut) plus a margin of 12 degrees, at most 75 degrees."""
        plate_h = plate_h or self.plate_height()
        half = math.atan(dot_angle * plate_h / 2.0)
        return math.cos(min(math.radians(75.0), half + math.radians(12.0)))

    def count_in_window(self, cam, fwd, cull):
        """Plant counts by kind inside the distance of `cam` (the scatter is pinned to cam for the count)."""
        e = self.engine
        e.set_dials(cam_override_on=1.0, cam_x=cam[0], cam_y=cam[1], cam_z=cam[2], cam_fx=fwd[0], cam_fy=fwd[1], cam_fz=fwd[2], cull_cos=cull)
        mats, kind, extra = scatter.evaluated_instances(self.host)
        e.set_dial('cam_override_on', 0.0)
        if len(kind) == 0:
            return {}, 0
        pos = mats[:, 3, :3]
        rel = pos - np.array(cam)
        d = np.sqrt((rel ** 2).sum(axis=1))
        inside = (d < self.values['distance']) & ((rel @ np.array(fwd)) > cull * np.maximum(d, 1e-6))
        out = {}
        for k, spec in enumerate(self.kind_specs):
            out[spec['name']] = int(((kind == k) & inside).sum())
        return out, int(inside.sum())

    def calibrate(self):
        """Sets the gains so the counts inside the window round the calibration camera come out at the targets of the share dials."""
        t0 = time.time()
        v, e = self.values, self.engine
        cam, fwd, fov = self.calibration_camera()
        a = self.arrays
        grid = a['grid']
        cull = self.cone_cos(2.0 * math.tan(math.radians(fov) / 2.0) / self.plate_height())
        window = local_masks.window_mask(grid, a['ground_z'], a['has_ground'], cam, v['distance'], fwd, cull)
        stats = local_masks.window_stats(a['masks'], self.sites, grid, a['ground_z'], window)
        self.stats = dict(stats, camera=list(cam), forward=list(fwd), cone_cos=cull)
        weed = [s for s in self.kind_specs if s['pop'] == 'weed']
        moss = [s for s in self.kind_specs if s['pop'] == 'moss']
        weed_share = sum(s['share'] for s in weed) or 1.0
        mean_fp = sum(s['share'] * s['footprint_m2'] for s in weed) / weed_share
        mean_w = sum(s['share'] * s['width_m'] for s in weed) / weed_share
        moss_share = sum(s['share'] for s in moss) or 1.0
        moss_fp = sum(s['share'] * s['footprint_m2'] for s in moss) / moss_share
        target = {}
        n_total = v['weed_cover'] * stats['area_m2'] / max(mean_fp, 1e-6)
        n_wall = v['wall_foot_share'] * stats['wall_foot_m'] / max(mean_w, 1e-6)
        n_gut = v['gutter_tuft_share'] * stats['gutter_side_m'] / max(mean_w, 1e-6)
        n_bg = max(n_total - n_wall - n_gut, 0.3 * n_total)
        target.update(bg=n_bg if weed else 0.0, wall=n_wall if weed else 0.0, gut=n_gut if weed else 0.0, moss=(v['cushion_cover'] * stats['area_m2'] / max(moss_fp, 1e-6)) if moss else 0.0,
                      toad=float(v['toadflax_clumps']) if any(s['pop'] == 'toad' for s in self.kind_specs) else 0.0)
        # count what a gain of 1 gives for every population alone (amounts forced to 1, the window pinned)
        keep = {k: e.get_dial(k) for k in ('amount', 'weeds_amount', 'cushions_amount', 'scale_total', 'g_bg', 'g_wall', 'g_gut', 'g_moss', 'g_toad', 'mask_only_kind', 'cull_cos')}
        e.set_dials(amount=1.0, weeds_amount=1.0, cushions_amount=1.0, scale_total=1.0, mask_only_kind=-1.0)
        gains, counts, notes = {}, {}, []
        for pop, key in (('bg', 'g_bg'), ('wall', 'g_wall'), ('gut', 'g_gut'), ('moss', 'g_moss'), ('toad', 'g_toad')):
            if target[pop] <= 0.0:
                gains[key] = 0.0
                counts[pop] = 0
                continue
            probe_gain, total = 1.0, 0
            for probe_gain in (1.0, 8.0, 64.0):
                e.set_dials(g_bg=0.0, g_wall=0.0, g_gut=0.0, g_moss=0.0, g_toad=0.0)
                e.set_dial(key, probe_gain)
                by_kind, total = self.count_in_window(cam, fwd, cull)
                if pop == 'moss':
                    total = sum(c for n_, c in by_kind.items() if self.species['kinds'][n_]['group'] == 'moss')
                elif pop == 'toad':
                    total = by_kind.get('toadflax', 0)
                else:
                    total = sum(c for n_, c in by_kind.items() if self.species['kinds'][n_]['group'] == 'weed' and not self.species['kinds'][n_].get('count_dial'))
                if total > 0:
                    break
            counts[pop] = total
            if total <= 0:
                gains[key] = 1.0
                notes.append(f'population {pop}: no plants even at gain {probe_gain:g}, target {target[pop]:.1f} not reachable (no site for it in the window)')
            else:
                gains[key] = min(probe_gain * target[pop] / total, 200.0)
        grand = sum(target.values())
        scale_total = 1.0
        if grand > v['max_pieces']:
            scale_total = v['max_pieces'] / grand
            notes.append(f'targets {grand:.0f} plants exceed max_pieces {v["max_pieces"]:.0f}: every gain scaled by {scale_total:.3f}')
        for k_, val in keep.items():
            e.set_dial(k_, val)
        self.calibration = dict(gains, scale_total=scale_total, target=target, one_gain_counts=counts, notes=notes, seconds=round(time.time() - t0, 2))
        self.notes = notes
        self.timings['calibrate_s'] = self.calibration['seconds']
        return self.calibration

    # ---------------------------------------------------------------- the kit's calls
    def set_state(self, wetness, puddles=0.0):
        self.wet = float(wetness)
        pieces_module.set_wetness(self.wet)

    def visible(self, flag):
        """Shows or hides the host (and so every plant) in the picture."""
        self.on = bool(flag)
        if self.host is not None:
            self.host.hide_render = not flag
            self.host.hide_viewport = not flag
            for modifier in self.host.modifiers:
                modifier.show_render = bool(flag)
                modifier.show_viewport = bool(flag)

    def table(self, camera=None, kinds_only=None):
        """Every plant of the picture (from `camera`, default the scene's): [{x, y, z, kind, species, size_m, height_m, scale, distance}] and the kind table."""
        scene = bpy.context.scene
        if not self.on or self.host is None:
            return []
        if camera is not None:
            keep_cam, scene.camera = scene.camera, camera
        try:
            mats, kind, extra = scatter.evaluated_instances(self.host)
            cam = np.array(scene.camera.matrix_world.translation) if scene.camera is not None else np.zeros(3)
        finally:
            if camera is not None:
                scene.camera = keep_cam
        rows = []
        for i in range(len(kind)):
            spec = self.kind_specs[int(kind[i])]
            m = mats[i]
            pos = m[3, :3]
            s = float(np.linalg.norm(m[:3, 0]))
            rows.append(dict(x=round(float(pos[0]), 4), y=round(float(pos[1]), 4), z=round(float(pos[2]), 4), kind=('weed_' + spec['name']) if spec['group'] == 'weed' else 'moss_cushion',
                             species=spec['name'], size_m=round(float(spec['width_m'] * s), 4), scale=round(s, 3), distance=round(float(np.linalg.norm(pos - cam)), 3)))
        return rows

    def remove_tree(self):
        if self.host is not None:
            tree = self.engine.tree if self.engine else None
            for modifier in list(self.host.modifiers):
                self.host.modifiers.remove(modifier)
            mesh = self.host.data
            bpy.data.objects.remove(self.host)
            if bpy.data.meshes.get(mesh.name) is mesh:
                bpy.data.meshes.remove(mesh)
            if tree is not None and bpy.data.node_groups.get(tree.name) is tree:
                bpy.data.node_groups.remove(tree)
            kind_tree = getattr(self.engine, 'kind_tree', None)
            if kind_tree is not None and bpy.data.node_groups.get(kind_tree.name) is kind_tree:
                bpy.data.node_groups.remove(kind_tree)
        self.host = None
        image = bpy.data.images.get(SITES_IMAGE)
        if image is not None:
            bpy.data.images.remove(image)
        self.attached = False

    def remove(self):
        self.remove_tree()
        if self.library is not None:
            self.library.remove()
            self.library = None
        for obj in [o for o in bpy.data.objects if o.name.startswith(pieces_module.OBJECT_PREFIX)]:
            bpy.data.objects.remove(obj)
        if self.set_state in self.kit.state_hooks:
            self.kit.state_hooks.remove(self.set_state)
        self.calibration = {}
        self._cal_key = None
        self._struct_key = None
        self.values = {}
        self.on = True


# ------------------------------------------------------------------------------------------------------------------------------ the checking view
def show_layer(kit, key=LAYER_KEY, black_others=True):
    """Every piece plain white light, every other material plain black (the runner's `layer:growth` view). Returns undo()."""
    from masks import debug
    saved = debug._blackout(kit, set()) if black_others else []
    pieces_module.set_mask_view(True)

    def undo():
        pieces_module.set_mask_view(False)
        debug._undo(saved)
    return undo


# ------------------------------------------------------------------------------------------------------------------------------ register and the wrappers
def _install_scale_hook():
    if getattr(scale_module, WET_HOOKED, False):
        return
    original = scale_module.set_scale

    def set_scale(kit, dot_angle_value=None, painter_widen_value=None):
        result = original(kit, dot_angle_value, painter_widen_value)
        system = getattr(kit, 'growth', None)
        if system is not None and system.attached:
            if dot_angle_value is not None:
                system.engine.set_dial('dot_angle', dot_angle_value)
                system.engine.set_dial('cull_cos', system.cone_cos(dot_angle_value))
            if painter_widen_value is not None:
                system.engine.set_dial('painter_widen', painter_widen_value)
        return result
    scale_module.set_scale = set_scale
    scale_module.set_scale_original = original
    setattr(scale_module, WET_HOOKED, True)


def register(kit):
    """Makes the growth layer known to the kit. Returns {'registered': [...], 'problems': {...}}."""
    dials_growth.ensure()
    look_id = ((kit.look or {}).get('id') if isinstance(kit.look, dict) else None) or (kit.settings.default_look() if hasattr(kit.settings, 'default_look') else None)
    for dial, value in look_extras(look_id).items():
        row = dials.TABLE.layers[LAYER_KEY].row(dial)
        if row is not None:
            row['default'] = value
    system = GrowthSystem(kit)
    kit.growth = system
    _install_scale_hook()
    kit.register_layer(LAYER_KEY, lambda key: 'growth-host', slot='C', roles=[])

    original = {name: getattr(kit, name) for name in ('apply', 'layer_on', 'layer_off', 'set_dials', 'set_master', 'remove')}

    def apply(look=None, layers=None, overrides=None):
        result = original['apply'](look=look, layers=layers, overrides=overrides)
        state = kit.active.get(LAYER_KEY)
        if state is not None and state['on'] and not system.attached:
            system.on = True
            system.attach(state['values'])
        return result

    def layer_on(key):
        original['layer_on'](key)
        if key == LAYER_KEY and LAYER_KEY in kit.active:
            system.visible(True)
            if not system.attached:
                system.attach(kit.active[LAYER_KEY]['values'])
            else:
                system.values = dict(kit.active[LAYER_KEY]['values'])
                system.sync()

    def layer_off(key):
        original['layer_off'](key)
        if key == LAYER_KEY:
            system.visible(False)

    def set_dials(layer, **values):
        original['set_dials'](layer, **values)
        if layer == LAYER_KEY and system.attached:
            system.values = dict(kit.active[LAYER_KEY]['values'])
            system.sync()

    def set_master(amount):
        original['set_master'](amount)
        if system.attached and LAYER_KEY in kit.active:
            system.sync()

    def remove(layer=None):
        if layer is None or layer == LAYER_KEY:
            system.remove()
        return original['remove'](layer)

    kit.apply, kit.layer_on, kit.layer_off, kit.set_dials, kit.set_master, kit.remove = apply, layer_on, layer_off, set_dials, set_master, remove
    return dict(registered=[LAYER_KEY], problems={})


def apply(kit, look=None, overrides=None):
    return kit.apply(look=look, layers=[LAYER_KEY], overrides=overrides)


def remove(kit):
    return kit.remove(LAYER_KEY)


def set_dials(kit, **values):
    return kit.set_dials(LAYER_KEY, **values)


def set_state(kit, wetness, puddles=0.0):
    kit.growth.set_state(wetness, puddles)


def pieces(kit, visible):
    kit.growth.visible(visible)


def table(kit, camera=None):
    return kit.growth.table(camera)
