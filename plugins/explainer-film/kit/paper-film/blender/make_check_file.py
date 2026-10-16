"""What this does: writes a view's shot check file (the JSON that shot_facts.py, check_shot.py and the other tools read)
from the Blender scene, instead of by hand. Logs 31-34 wrote every one by hand and kept missing things: lettered drums
left out of must_read (round 3's 'SEL'/'DIE' fragments), seven men as one group, background near-touches never checked
(lesson 121), counter props on the street's ground test (the checkout's first check), a light prop chosen by distance.
The story choices come from a short shot list the author writes; everything else is measured from the scene:
  from the shot list   subject, support, story, work, and any group the author merges or splits (a gate and its chain;
                       the notice and its board) or adds for a landmark (a chimney); optional display names
  generated            one group per prop root (each imported model or built prop, copies with the same name together,
                       loose parts such as coals or a flame joined to the prop they sit in), one per figure, only those
                       in the camera's frame; must_read (every group with a lettering material); pairs_also (every group
                       not in the story); on_ground and stands_on (rays cast down from each group's lowest points: on the
                       set's ground outdoors, on a declared floor indoors, never on a counter); lights_in_story (story
                       groups that glow over a good share of their own surface: a lantern's glass, not a brazier's coals);
                       lines; eye_height, story_reaches_down and the sky pattern from the view's shot-kind profile; the
                       title zone (the largest rectangle of the words band that is sky) or "band": true where the profile
                       puts words over a soft dark band; match_excludes (dark, thin or lettered groups and repeated
                       figures, which fool the picture-match test); own_surface_materials; and the keys the plugin's
                       check_shot.py reads for kinds of shot: kind_of_shot, figures, fill, support_surfaces (indoors) and
                       accepted (the shot list's and the place facts' entries for this view).
Run it inside Blender, after the place's assemble script (as check-shot.sh does), or on a saved scene:
  blender -b BASE.blend --python ASSEMBLE.py --python make_check_file.py -- --shot-list SHOT.json --check-file OUT.json
        [--place-facts PLACE.json] [--compare HAND.json] [--out RESULT.json] [--report REPORT.txt] [assemble options]
  blender -b SCENE.blend --disable-autoexec --python make_check_file.py -- --shot-list SHOT.json --check-file OUT.json
The shot list (JSON): {"view": "w1", "kind_of_shot": ["crowd"], "subject": "no-1 gate", "support": null,
  "story": [...], "work": [...], "groups": {"no-1 gate": ["no-1-gate", "no-1-chain"]}, "names": {"man-1": "man 1"},
  "prop_collections": ["props", "signs", ...], "set_objects": ["counter*"], "fill": [...], "support_surfaces": [...], "accepted": [...]}
(kind_of_shot, support_surfaces and lines may come from --place-facts instead). With --compare it prints how the
generated file differs from a hand-made one, group by group (matched by the objects they hold) and role by role.
House numbers: kit/film-settings.json (views_and_models.check_file, frame, shot_kind_profiles); the report names them.
"""
import argparse
import fnmatch
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.abspath(os.path.join(HERE, '..', '..', 'calculators'))
for folder in (HERE, CALCULATORS):
    if folder not in sys.path:
        sys.path.insert(0, folder)
from settings import load_settings, resolve_profile  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402

SECTION = 'views_and_models.check_file'
COPY_NUMBER = re.compile(r'\.\d{3}$')
TRAILING_NUMBER = re.compile(r'\d+$')


def make_parser():
    parser = argparse.ArgumentParser(description='Writes a view\'s shot check file from the Blender scene (run inside Blender after '
                                                 'the place\'s assemble script). See the note at the top of this file.')
    parser.add_argument('--shot-list', required=True, help='the view\'s shot list (story choices) as JSON')
    parser.add_argument('--check-file', required=True, help='where to write the generated check file')
    parser.add_argument('--place-facts', help='the place facts file (kind of shot, support surfaces, lines, accepted)')
    parser.add_argument('--compare', help='a hand-made check file to compare with')
    add_output_options(parser)
    return parser


# ------------------------------------------------------------------------------------------------ small helpers
def matches(name, patterns):
    return any(fnmatch.fnmatch(name, p) for p in patterns)


def stem_of(name):
    return COPY_NUMBER.sub('', name)


def ancestors(o):
    while o.parent is not None:
        o = o.parent
        yield o


def root_of(o):
    while o.parent is not None:
        o = o.parent
    return o


def group_of(o, groups):
    """shot_facts.py's rule: the object's own name first, then what it hangs from, then that one's holder ..."""
    for name in [o.name] + [a.name for a in ancestors(o)]:
        for group, patterns in groups.items():
            if matches(name, patterns):
                return group
    return None


def compress_names(names, scene_names, claimed_elsewhere):
    """Patterns for a set of object names: a family 'brazier_coal_0..21' becomes 'brazier_coal_*' when every scene object
    of that family is in the set and no other group claims one."""
    patterns, left = [], set(names)
    families = {}
    for name in names:
        if TRAILING_NUMBER.search(name):
            families.setdefault(TRAILING_NUMBER.sub('*', name), []).append(name)
    for pattern, members in families.items():
        everyone = [n for n in scene_names if fnmatch.fnmatch(n, pattern)]
        if len(members) > 1 and set(everyone) <= set(names) and not any(n in claimed_elsewhere for n in everyone):
            patterns.append(pattern)
            left -= set(members)
    return patterns + sorted(left)


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


# ------------------------------------------------------------------------------------------------ the scene
class Scene:
    """What the generator needs from Blender: visible meshes, their world boxes and vertices, materials, the camera."""

    def __init__(self, bpy, settings):
        import numpy as np
        self.bpy, self.np, self.settings = bpy, np, settings
        self.scene = bpy.context.scene
        bpy.context.view_layer.update()
        self.depsgraph = bpy.context.evaluated_depsgraph_get()
        self.camera = self.scene.camera
        self.width = settings.value('frame.width_pixels')
        self.height = settings.value('frame.height_pixels')
        self.meshes = [o for o in self.scene.objects if o.type in ('MESH', 'CURVE', 'SURFACE', 'META', 'FONT') and not o.hide_render]
        self.names = [o.name for o in self.scene.objects]
        self._vertices, self._image_means = {}, {}

    def vertices(self, o):
        np = self.np
        if o.name not in self._vertices:
            evaluated = o.evaluated_get(self.depsgraph)
            mesh = evaluated.to_mesh()
            try:
                points = np.empty(len(mesh.vertices) * 3)
                mesh.vertices.foreach_get('co', points)
                points = points.reshape(-1, 3)
                matrix = np.array(o.matrix_world)
                points = points @ matrix[:3, :3].T + matrix[:3, 3]
                faces = []
                mesh.calc_loop_triangles()
                count = len(mesh.loop_triangles)
                if count:
                    tri = np.empty(count * 3, dtype=np.int64)
                    mesh.loop_triangles.foreach_get('vertices', tri)
                    slots = np.empty(count, dtype=np.int64)
                    mesh.loop_triangles.foreach_get('material_index', slots)
                    faces = (tri.reshape(-1, 3), slots)
            finally:
                evaluated.to_mesh_clear()
            self._vertices[o.name] = (points, faces)
        return self._vertices[o.name]

    def box(self, objects):
        np = self.np
        points = [self.vertices(o)[0] for o in objects if len(self.vertices(o)[0])]
        if not points:
            return None
        points = np.concatenate(points)
        return points.min(axis=0), points.max(axis=0)

    def project(self, point):
        from bpy_extras.object_utils import world_to_camera_view
        from mathutils import Vector
        v = world_to_camera_view(self.scene, self.camera, Vector(point))
        return float(v.x), float(1 - v.y), float(v.z)   # across, down, depth

    def frame_box(self, low, high):
        corners = [(x, y, z) for x in (low[0], high[0]) for y in (low[1], high[1]) for z in (low[2], high[2])]
        landed = [self.project(c) for c in corners]
        front = [p for p in landed if p[2] > 0]
        if not front:
            return None
        return [min(p[0] for p in front), min(p[1] for p in front), max(p[0] for p in front), max(p[1] for p in front)]

    def material_facts(self, material):
        """Glow and base brightness of a material (Principled BSDF or an Emission shader)."""
        facts = {'glows': False, 'base_brightness': None}
        if material is None or not material.use_nodes:
            return facts
        nodes = material.node_tree.nodes
        for node in nodes:
            if node.type == 'EMISSION':
                strength = node.inputs['Strength'].default_value
                colour = list(node.inputs['Color'].default_value)[:3]
                if strength > 0 and (max(colour) > 0 or node.inputs['Color'].is_linked):
                    facts['glows'] = True
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if principled is not None:
            colour_socket = principled.inputs.get('Emission Color')
            strength_socket = principled.inputs.get('Emission Strength')
            if colour_socket is not None and strength_socket is not None and strength_socket.default_value > 0 and \
                    (max(list(colour_socket.default_value)[:3]) > 0 or colour_socket.is_linked):
                facts['glows'] = True
            base = principled.inputs['Base Color']
            if base.is_linked:
                source = base.links[0].from_node
                if source.type == 'TEX_IMAGE' and source.image is not None:
                    facts['base_brightness'] = self.image_mean(source.image)
            else:
                facts['base_brightness'] = luminance(list(base.default_value)[:3])
        return facts

    def image_mean(self, image):
        np = self.np
        if image.name not in self._image_means:
            try:
                count = image.size[0] * image.size[1] * image.channels
                if count == 0:
                    raise ValueError
                pixels = np.empty(count, dtype=np.float32)
                image.pixels.foreach_get(pixels)
                pixels = pixels.reshape(-1, image.channels)[::7, :3]
                if image.colorspace_settings.name != 'Non-Color' and image.colorspace_settings.name.lower().startswith('srgb'):
                    pixels = np.where(pixels <= 0.04045, pixels / 12.92, ((pixels + 0.055) / 1.055) ** 2.4)
                self._image_means[image.name] = float(luminance(pixels.mean(axis=0)))
            except Exception:
                self._image_means[image.name] = None
        return self._image_means[image.name]

    def surface_shares(self, objects):
        """Area of each object's faces (world), split into glowing, lettered and the base brightness, area-weighted."""
        np = self.np
        lettering = [p.lower() for p in self.settings.value('views_and_models.lettering_material_patterns')]
        total = glowing = lettered = 0.0
        brightness_sum = brightness_area = 0.0
        facing = 0.0
        forward = np.array(self.camera.matrix_world.to_3x3() @ __import__('mathutils').Vector((0, 0, -1)))
        for o in objects:
            points, faces = self.vertices(o)
            if not len(faces):
                continue
            triangles, slots = faces
            corners = points[triangles]
            cross = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
            areas = 0.5 * np.linalg.norm(cross, axis=1)
            facing += float(np.abs(cross @ forward).sum() / 2)
            materials = [s.material for s in o.material_slots] or [None]
            for index in np.unique(slots):
                material = materials[index] if index < len(materials) else None
                area = float(areas[slots == index].sum())
                total += area
                facts = self.material_facts(material)
                if facts['glows']:
                    glowing += area
                if material is not None and matches(material.name.lower(), lettering):
                    lettered += area
                if facts['base_brightness'] is not None:
                    brightness_sum += facts['base_brightness'] * area
                    brightness_area += area
        return {'area': total, 'glowing_share': glowing / total if total else 0.0, 'lettered_area': lettered,
                'base_brightness': brightness_sum / brightness_area if brightness_area else None, 'facing_area': facing}

    def ray_down(self, x, y, z, own):
        """The first thing under (x, y, z) that is not one of `own` objects: (object, height) or (None, None)."""
        from mathutils import Vector
        start = z
        for _ in range(12):
            hit, location, _normal, _index, obj, _matrix = self.scene.ray_cast(self.depsgraph, Vector((x, y, start)), Vector((0, 0, -1)))
            if not hit:
                return None, None
            if obj.name in own:
                start = location.z - 1e-4
                continue
            return obj, location.z
        return None, None

    def ray_from_camera(self, across, down):
        """What the camera sees through a point of the frame: the object hit, or None (open sky)."""
        from mathutils import Vector
        frame = self.camera.data.view_frame(scene=self.scene)   # top right, bottom right, bottom left, top left (camera space)
        top_left, top_right, bottom_left = frame[3], frame[0], frame[2]
        local = top_left + (top_right - top_left) * across + (bottom_left - top_left) * down
        direction = (self.camera.matrix_world.to_3x3() @ local).normalized()
        origin = self.camera.matrix_world.translation
        hit, _location, _normal, _index, obj, _matrix = self.scene.ray_cast(self.depsgraph, origin, direction)
        return obj if hit else None


# ------------------------------------------------------------------------------------------------ groups
def build_groups(scene, shot, settings, place_facts):
    """Declared groups (shot list) first, then one per prop root (copies with one name together), loose parts joined to
    the prop whose box holds them. Returns ({name: patterns}, {name: [objects]}, notes)."""
    np = scene.np
    notes = []
    prop_collections = shot.get('prop_collections') or settings.value(f'{SECTION}.prop_collections')
    set_objects = shot.get('set_objects', [])
    declared = {name: list(patterns) for name, patterns in (shot.get('groups') or {}).items()}
    master = scene.scene.collection

    def in_props(o):
        return any(matches(c.name, prop_collections) for c in o.users_collection)

    claimed = {}
    for o in scene.meshes:
        g = group_of(o, declared)
        if g is not None:
            claimed[o.name] = g
    roots = {}
    loose = []
    for o in scene.meshes:
        if o.name in claimed:
            continue
        root = root_of(o)
        if matches(root.name, set_objects) or matches(o.name, set_objects):
            continue
        if root.name == o.name and not o.children and ([c.name for c in o.users_collection] == [master.name] or in_props(o)):
            loose.append(o)
            continue
        if in_props(root):
            roots.setdefault(root.name, []).append(o)
    # loose meshes inside a prop's box join it (coals in a brazier, a flame in a lantern); others in prop collections
    # stand as their own prop; loose meshes elsewhere are the set
    boxes = {name: scene.box(objects) for name, objects in roots.items()}
    # loose parts of one family (brazier_coal_0 .. 21) stay together and join the prop holding most of their box
    families = {}
    for o in loose:
        families.setdefault(TRAILING_NUMBER.sub('*', o.name), []).append(o)
    for family, objects in families.items():
        in_master = all([c.name for c in o.users_collection] == [master.name] for o in objects)
        if len(objects) == 1 and not in_master:
            roots[objects[0].name] = objects   # a lone prop of its own (a divider bar against a basket), not a part
            continue
        low, high = scene.box(objects)
        size = np.maximum(high - low, 1e-6)
        best, best_share, best_key = None, 0.0, None
        for name, b in boxes.items():
            if b is None:
                continue
            overlap = np.clip(np.minimum(high, b[1]) - np.maximum(low, b[0]), 0, None)
            share = float(np.prod(overlap) / np.prod(size))
            key = (round(share, 3), -float(np.prod(b[1] - b[0])))   # equally inside two: the smaller holder (a flame in the lantern, not the chair)
            if share > 0 and (best_key is None or key > best_key):
                best, best_share, best_key = name, share, key
        if best is not None and best_share >= 0.5:   # mostly inside it: coals heaped in a brazier, a flame in a lantern
            roots[best].extend(objects)
        elif any(in_props(o) for o in objects):
            roots[objects[0].name] = objects
    # copies with one name (brazier-drum.001 and brazier-drum) form one group
    by_stem = {}
    for name, objects in roots.items():
        by_stem.setdefault(stem_of(name), []).append((name, objects))
    generated = {}
    members = {}
    names = shot.get('names') or {}
    for stem, entries in by_stem.items():
        group = names.get(stem, stem)
        objects = [o for _, objects in entries for o in objects]
        own = {o.name for o in objects}
        root_names = [n for n, _ in entries]
        # 'brazier-drum*' if it catches no other drawn object (by its own name or what it hangs from), else the roots' names
        wide = stem + '*'
        catches_other = any(o.name not in own and (fnmatch.fnmatch(o.name, wide) or any(fnmatch.fnmatch(a.name, wide) for a in ancestors(o)))
                            for o in scene.meshes)
        patterns = [wide] if not catches_other else sorted(root_names)
        parts = [o.name for o in objects if root_of(o).name not in root_names]
        patterns += compress_names(parts, scene.names, claimed)
        # two names the author gives one display name (crate-1 and crate-2 as "crates") make one group
        generated[group] = generated.get(group, []) + [p for p in patterns if p not in generated.get(group, [])]
        members[group] = members.get(group, []) + objects
    for name, patterns in declared.items():
        members[name] = [o for o in scene.meshes if claimed.get(o.name) == name]
        if not members[name]:
            notes.append(f'declared group "{name}" ({", ".join(patterns)}) matches nothing that is drawn in this scene')
    return declared, generated, members, notes


# ------------------------------------------------------------------------------------------------ the generator
def generate(scene, shot, settings, place_facts=None):
    np = scene.np
    notes = []
    view_name = shot.get('view')
    view = next((v for v in (place_facts or {}).get('views', []) if v.get('name') == view_name), {}) if place_facts else {}
    kinds = shot.get('kind_of_shot') or view.get('kind_of_shot') or ['still_life']
    profile = resolve_profile(settings, kinds)
    interior = bool(shot.get('interior', (place_facts or {}).get('interior', False)) or 'interior' in kinds)
    declared, generated, members, group_notes = build_groups(scene, shot, settings, place_facts)
    notes += group_notes

    # only groups that land in the camera's frame
    in_frame, boxes, frame_boxes = {}, {}, {}
    for name, objects in members.items():
        if not objects:
            continue
        box = scene.box(objects)
        if box is None:
            continue
        boxes[name] = box
        frame_box = scene.frame_box(*box)
        frame_boxes[name] = frame_box
        in_frame[name] = frame_box is not None and frame_box[2] >= 0 and frame_box[0] <= 1 and frame_box[3] >= 0 and frame_box[1] <= 1
    story_roles = [shot.get('subject'), shot.get('support')] + list(shot.get('story', [])) + list(shot.get('work', []))
    for role in [r for r in story_roles if r]:
        if role not in members:
            raise SystemExit(f'make_check_file: the shot list names "{role}", which is no group in this scene (groups: '
                             f'{", ".join(sorted(members))}); name a prop root, or declare it in "groups"')
    keep = [g for g in list(declared) + list(generated) if in_frame.get(g) or g in story_roles]
    dropped = sorted(g for g in members if g not in keep and members[g])
    limit = settings.value('composing.shot_facts_groups_max')
    if len(keep) > limit:
        camera_at = np.array(scene.camera.matrix_world.translation)
        optional = [g for g in keep if g not in story_roles and g not in declared]
        optional.sort(key=lambda g: -float(np.linalg.norm((boxes[g][0] + boxes[g][1]) / 2 - camera_at)))
        cut = optional[:len(keep) - limit]
        keep = [g for g in keep if g not in cut]
        notes.append(f'more than {limit} groups (shot_facts.py\'s colours): left out the farthest: {", ".join(cut)}')
    # declared groups first (shot_facts takes the first group whose pattern matches), then story groups, then the rest
    order = list(declared) + [g for g in story_roles if g in generated] + [g for g in generated if g not in story_roles]
    groups = {g: (declared.get(g) or generated.get(g)) for g in dict.fromkeys(order) if g in keep}

    surfaces = {g: scene.surface_shares(members[g]) for g in groups}
    lettering_patterns = [p.lower() for p in settings.value('views_and_models.lettering_material_patterns')]
    must_read = [g for g in groups if surfaces[g]['lettered_area'] > 0]
    own_surface = sorted({s.material.name for g in must_read for o in members[g] for s in o.material_slots
                          if s.material is not None and matches(s.material.name.lower(), lettering_patterns)})

    story = [g for g in shot.get('story', []) if g in groups]
    core = [g for g in [shot.get('subject'), shot.get('support')] + story if g]
    # a group of lettered faces only (a label split from its basket) is words, not a prop: no near-touch pairs
    words_only = [g for g in groups if surfaces[g]['lettered_area'] > 0 and surfaces[g]['lettered_area'] >= 0.999 * surfaces[g]['area']]
    pairs_also = [g for g in groups if g not in core and g not in words_only]

    # light props: story groups that glow over a good share of their own surface
    glow_share = settings.value(f'{SECTION}.light_prop_glow_share')
    lights_in_story = [g for g in story if surfaces[g]['glowing_share'] >= glow_share]

    # resting: rays down from each group's lowest points
    within = settings.value(f'{SECTION}.on_ground_within_metres')
    ground_kinds = settings.value(f'{SECTION}.ground_kinds')
    declared_surfaces = shot.get('support_surfaces') or (place_facts or {}).get('support_surfaces', [])
    floors = [s for s in declared_surfaces if s.get('kind') in ground_kinds]
    raised = [s for s in declared_surfaces if s.get('kind') not in ground_kinds]
    if interior and not floors:
        notes.append('an interior with no declared floor: on_ground left empty (declare the floor in support_surfaces)')
    owner = {o.name: g for g, objects in members.items() for o in objects}
    on_ground, stands_on, resting = [], {}, {}
    for g in groups:
        if g in declared and g not in story_roles:
            continue   # a landmark the author added (a chimney): not a prop that rests anywhere
        objects = members[g]
        points = np.concatenate([scene.vertices(o)[0] for o in objects if len(scene.vertices(o)[0])])
        lowest = float(points[:, 2].min())
        foot = points[points[:, 2] <= lowest + 0.05]
        samples = [foot.mean(axis=0)] + [foot[foot[:, axis].argmin()] for axis in (0, 1)] + [foot[foot[:, axis].argmax()] for axis in (0, 1)]
        own = {o.name for o in objects}
        votes = []
        for x, y, _z in samples:
            obj, height = scene.ray_down(float(x), float(y), lowest + 0.05, own)
            if obj is None:
                votes.append(('nothing', None, None))
                continue
            gap = lowest - height
            other = owner.get(obj.name)
            if other is not None and other != g:
                votes.append(('group', other, gap))
            else:
                votes.append(('set', obj.name, gap))
        resting[g] = {'lowest': lowest, 'votes': [(kind, what, None if gap is None else round(gap, 3)) for kind, what, gap in votes]}
        close = [v for v in votes if v[2] is not None and abs(v[2]) <= within]
        if len(close) * 2 <= len(votes):
            continue
        kinds_seen = [v[0] for v in close]
        if kinds_seen.count('group') > kinds_seen.count('set'):
            support = max(set(v[1] for v in close if v[0] == 'group'), key=[v[1] for v in close].count)
            if support in groups:
                stands_on[g] = support
            continue
        height = lowest - float(np.median([v[2] for v in close if v[0] == 'set']))
        if any(abs(surface_height(s, points.mean(axis=0)) - height) <= within for s in raised):
            continue   # on a counter, shelf or sill: not the ground (the checkout's first check)
        if interior and not any(abs(surface_height(s, points.mean(axis=0)) - height) <= within for s in floors):
            continue
        on_ground.append(g)

    # lines, eye range, reach, sky, words band
    lines = shot.get('lines') or (place_facts or {}).get('lines')
    lines_key = shot.get('lines_key') or (place_facts or {}).get('lines_key')
    if not lines:
        slope = next((s.get('slope') for s in declared_surfaces if s.get('slope')), None)
        lines = {'street': [0, 1, round(slope[1], 6) if slope else 0], 'level': [0, 1, 0]}
        lines_key = 'street'
    eye_rule = profile['rule2_eye_height']
    reach_rule = profile['rule7_story_reaches_down']
    title_rule = profile['rule12_title_zone_sky_share']
    sky_rule = profile.get('rule5_top_third_brightness', {})
    sky = shot.get('sky') or sky_rule.get('sky_pattern') or settings.value(f'{SECTION}.sky_pattern_outdoors')
    check = {'about': f'What this file is: the shot check for view {view_name or "(no name)"} ({", ".join(kinds)}), written by '
                      f'make_check_file.py from the Blender scene and the shot list (subject, support, story and work are the '
                      f'author\'s; groups, must_read, pairs_also, on_ground, stands_on, lights_in_story, the title zone and the '
                      f'rest are measured). Used by shot_facts.py and check_shot.py.',
             'size': [scene.width, scene.height], 'groups': groups}
    if shot.get('subject'):
        check['subject'] = shot['subject']
    if shot.get('support'):
        check['support'] = shot['support']
    check['story'] = story
    check['lights_in_story'] = lights_in_story
    check['pairs_also'] = pairs_also
    check['work'] = [g for g in shot.get('work', []) if g in groups]
    check['on_ground'] = on_ground
    if stands_on:
        check['stands_on'] = stands_on
    check['must_read'] = must_read
    support = shot.get('support')
    subject = shot.get('subject')
    if support and subject and support in boxes and subject in boxes and boxes[support][1][2] > boxes[subject][1][2]:
        check['box_excludes'] = [support]
    check['lines'] = lines
    check['lines_key'] = lines_key
    check['eye_height'] = eye_rule['value']
    zone, zone_note = None, None
    if title_rule.get('applies', True):
        zone, zone_note = find_title_zone(scene, settings, sky, title_rule['value'])
    else:
        check['band'] = True
        zone_note = f'the view\'s kind of shot puts the words over a soft dark band ({title_rule.get("replaced_by", "")})'
    check['title_zone'] = zone or settings.value(f'{SECTION}.title_zone_fallback')
    if sky != 'sky_dome*':
        check['sky'] = sky
    check['story_reaches_down'] = reach_rule['value']
    # the keys the plugin's check_shot.py reads for the view's kinds of shot (written by the shot planner helper, log 35)
    check['kind_of_shot'] = kinds
    figure_patterns = settings.value(f'{SECTION}.figure_collections')
    check['figures'] = [g for g in groups if any(matches(c.name, figure_patterns) for o in members[g][:1] for c in root_of(o).users_collection)]
    if shot.get('fill'):
        check['fill'] = [g for g in shot['fill'] if g in groups]
    if interior and raised:
        check['support_surfaces'] = [{'name': s.get('name', s.get('kind')), 'height': s['height']} for s in raised]
    check['match_excludes'], exclude_reasons = picture_match_excludes(scene, settings, groups, members, frame_boxes, surfaces, must_read)
    check['own_surface_materials'] = own_surface
    accepted = list(shot.get('accepted', [])) + [{k: v for k, v in a.items() if k != 'view'} for a in (place_facts or {}).get('accepted', [])
                                                 if a.get('view') == view_name]
    check['accepted'] = accepted
    if zone_note:
        notes.append(f'title zone: {zone_note}')
    if dropped:
        notes.append(f'out of the frame, left out: {", ".join(dropped)}')
    facts = {'kinds_of_shot': kinds, 'interior': interior, 'resting': resting, 'surfaces': surfaces, 'frame_boxes': frame_boxes,
             'match_exclude_reasons': exclude_reasons, 'declared_groups': list(declared), 'generated_groups': [g for g in groups if g not in declared]}
    return check, facts, notes


def surface_height(surface, at):
    height = surface['height']
    slope = surface.get('slope')
    if slope and surface.get('at'):
        height += slope[0] * (at[0] - surface['at'][0]) + slope[1] * (at[1] - surface['at'][1])
    return height


def find_title_zone(scene, settings, sky_pattern, sky_share):
    """The largest rectangle of the words band (0.05-0.90 across, 0.02-0.22 down: the text margins and the title band)
    that is at least `sky_share` open sky as the camera sees it (rays through a grid), and holds no light."""
    np = scene.np
    left, right = settings.value('safe_area.text_left_pixels') / scene.width, settings.value('safe_area.text_right_pixels') / scene.width
    band = settings.value('safe_area.title_band_down')
    top, bottom = max(0.02, band[0] - 0.03), band[1]
    step = 0.01
    columns = np.arange(left + step / 2, right, step)
    rows = np.arange(top + step / 2 * 1080 / 1920, bottom, step * scene.width / scene.height)
    sky = np.zeros((len(rows), len(columns)), dtype=bool)
    for i, down in enumerate(rows):
        for j, across in enumerate(columns):
            obj = scene.ray_from_camera(float(across), float(down))
            sky[i, j] = obj is None or fnmatch.fnmatch(obj.name, sky_pattern)
    blocked = np.zeros_like(sky)
    for light in [o for o in scene.scene.objects if o.type == 'LIGHT' and not o.hide_render and o.data.type != 'SUN']:
        across, down, depth = scene.project(tuple(light.matrix_world.translation))
        if depth > 0 and 0 <= across <= 1 and 0 <= down <= 1:
            near = (np.abs(rows[:, None] - down) < 0.05) & (np.abs(columns[None, :] - across) < 0.05 * scene.height / scene.width)
            blocked |= near
    total = np.pad(np.cumsum(np.cumsum(sky, 0), 1), ((1, 0), (1, 0)))
    lit = np.pad(np.cumsum(np.cumsum(blocked, 0), 1), ((1, 0), (1, 0)))
    best, best_area = None, 0
    for i0 in range(len(rows)):
        for i1 in range(i0 + 1, len(rows) + 1):
            for j0 in range(len(columns)):
                for j1 in range(j0 + 1, len(columns) + 1):
                    cells = (i1 - i0) * (j1 - j0)
                    if cells <= best_area:
                        continue
                    if lit[i1, j1] - lit[i0, j1] - lit[i1, j0] + lit[i0, j0] > 0:
                        continue   # no light in the zone, nor within 5% of the frame of it
                    count = total[i1, j1] - total[i0, j1] - total[i1, j0] + total[i0, j0]
                    if count >= sky_share * cells:
                        best, best_area = (i0, i1, j0, j1), cells
    if best is None:
        return None, f'no part of the words band is {sky_share:.0%} sky: the fallback zone is written; put the words over a soft dark band'
    i0, i1, j0, j1 = best
    zone = [round(max(left, float(columns[j0] - step / 2)), 3), round(max(top, float(rows[i0] - step / 2 * scene.width / scene.height)), 3),
            round(min(right, float(columns[j1 - 1] + step / 2)), 3), round(min(bottom, float(rows[i1 - 1] + step / 2 * scene.width / scene.height)), 3)]
    share = float(sky.mean())
    return zone, f'the largest {sky_share:.0%}-sky rectangle of the words band ({share:.0%} of the band is sky)'


def picture_match_excludes(scene, settings, groups, members, frame_boxes, surfaces, must_read):
    """Groups the picture-match test misreads (rounds 3-5): dark ones, thin ones (narrow, or bars with little fill),
    lettered boards and signs (their borders are their strongest edges), and figures that repeat one model."""
    thin_pixels = settings.value(f'{SECTION}.thin_pixels')
    dark = settings.value(f'{SECTION}.dark_base_brightness')
    fill = settings.value(f'{SECTION}.thin_fill_share')
    reasons = {}
    figure_patterns = settings.value(f'{SECTION}.figure_collections')
    figures = [g for g in groups if any(matches(c.name, figure_patterns) for o in members[g][:1] for c in root_of(o).users_collection)]
    for g in groups:
        why = []
        box = frame_boxes.get(g)
        if box is not None:
            width_pixels = (min(box[2], 1) - max(box[0], 0)) * scene.width
            height_pixels = (min(box[3], 1) - max(box[1], 0)) * scene.height
            if 0 < min(width_pixels, height_pixels) < thin_pixels:
                why.append(f'thin ({min(width_pixels, height_pixels):.0f} px)')
            low, high = scene.box(members[g])
            extent = (high - low)
            seen_area = max(extent[0] * extent[2], extent[1] * extent[2], 1e-9)
            fill_share = surfaces[g]['facing_area'] / 2 / seen_area
            if fill_share < fill:
                why.append(f'bars ({fill_share:.2f} of its outline filled)')
        brightness = surfaces[g]['base_brightness']
        if brightness is not None and brightness < dark:
            why.append(f'dark (base colour {brightness:.3f})')
        if g in must_read:
            why.append('lettered (a board\'s border is its strongest edge)')
        if g in figures and len(figures) > 1:
            why.append(f'one of {len(figures)} alike figures (slid, it lines up with a neighbour: round 3-5)')
        if why:
            reasons[g] = why
    return [g for g in groups if g in reasons], reasons


# ------------------------------------------------------------------------------------------------ comparing with a hand-made file
def compare(scene, generated, hand):
    """Matches each hand group to the generated group holding most of the same drawn objects, then compares roles."""
    hand_members, generated_members = {}, {}
    for o in scene.meshes:
        h = group_of(o, hand['groups'])
        if h:
            hand_members.setdefault(h, set()).add(o.name)
        g = group_of(o, generated['groups'])
        if g:
            generated_members.setdefault(g, set()).add(o.name)
    mapping, rows = {}, []
    for h, objects in hand_members.items():
        best, score = None, 0.0
        for g, others in generated_members.items():
            jaccard = len(objects & others) / len(objects | others)
            if jaccard > score:
                best, score = g, jaccard
        mapping[h] = best if score > 0 else None
        rows.append({'hand': h, 'generated': best, 'same_objects_share': round(score, 3), 'hand_objects': len(objects),
                     'generated_objects': len(generated_members.get(best, ())) if best else 0})
    missing_in_scene = [h for h in hand['groups'] if h not in hand_members]
    extra = [g for g in generated['groups'] if g not in set(mapping.values())]
    roles = {}
    for key in ('subject', 'support', 'story', 'work', 'pairs_also', 'on_ground', 'must_read', 'lights_in_story', 'box_excludes'):
        hand_value = hand.get(key)
        mine = generated.get(key)
        if isinstance(hand_value, str) or isinstance(mine, str):
            mapped = mapping.get(hand_value) if hand_value else None
            roles[key] = {'hand': hand_value, 'hand_as_generated': mapped, 'generated': mine, 'same': mapped == mine}
            continue
        hand_set = {mapping.get(h) or f'(hand only) {h}' for h in (hand_value or [])}
        mine_set = set(mine or [])
        roles[key] = {'hand': sorted(hand_value or []), 'same': hand_set == mine_set,
                      'only_hand': sorted(hand_set - mine_set), 'only_generated': sorted(mine_set - hand_set)}
    hand_stands = {mapping.get(k) or k: mapping.get(v) or v for k, v in (hand.get('stands_on') or {}).items()}
    roles['stands_on'] = {'hand': hand_stands, 'generated': generated.get('stands_on', {}),
                          'hand_pairs_found': all(generated.get('stands_on', {}).get(k) == v for k, v in hand_stands.items())}
    keys = {}
    for key in ('size', 'lines', 'lines_key', 'eye_height', 'title_zone', 'story_reaches_down', 'sky'):
        keys[key] = {'hand': hand.get(key, 'sky_dome*' if key == 'sky' else None), 'generated': generated.get(key, 'sky_dome*' if key == 'sky' else None)}
        keys[key]['same'] = keys[key]['hand'] == keys[key]['generated']
    return {'groups': rows, 'hand_groups_drawing_nothing': missing_in_scene, 'generated_only': extra, 'roles': roles, 'keys': keys,
            'mapping': mapping}


def comparison_lines(result):
    lines = ['', 'Against the hand-made check file:']
    same = [r for r in result['groups'] if r['same_objects_share'] == 1.0]
    lines.append(f'  groups: {len(same)} of {len(result["groups"])} hand groups hold exactly the same drawn objects as a generated group')
    for r in result['groups']:
        if r['same_objects_share'] < 1.0:
            lines.append(f'    {r["hand"]} -> {r["generated"]} ({r["same_objects_share"]:.0%} the same objects: hand {r["hand_objects"]}, '
                         f'generated {r["generated_objects"]})')
    if result['generated_only']:
        lines.append(f'  generated only: {", ".join(result["generated_only"])}')
    if result['hand_groups_drawing_nothing']:
        lines.append(f'  hand groups that match nothing drawn: {", ".join(result["hand_groups_drawing_nothing"])}')
    for key, row in result['roles'].items():
        if key == 'stands_on':
            lines.append(f'  stands_on: hand {row["hand"] or "{}"}, generated {row["generated"] or "{}"}'
                         + ('' if row['hand_pairs_found'] else ' (a hand pair is missing)'))
            continue
        if 'only_hand' in row:
            text = 'same' if row['same'] else (f'only in the hand file: {", ".join(row["only_hand"]) or "-"}; only generated: '
                                               f'{", ".join(row["only_generated"]) or "-"}')
        else:
            text = 'same' if row['same'] else f'hand {row["hand"]} ({row["hand_as_generated"]}), generated {row["generated"]}'
        lines.append(f'  {key}: {text}')
    for key, row in result['keys'].items():
        lines.append(f'  {key}: {"same" if row["same"] else "hand " + json.dumps(row["hand"]) + ", generated " + json.dumps(row["generated"])}')
    return lines


# ------------------------------------------------------------------------------------------------ run
def main():
    parser = make_parser()
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    try:
        import bpy
    except ImportError:
        args = parser.parse_args(argv)   # --help works outside Blender
        raise SystemExit('make_check_file: run this inside Blender (see the note at the top of this file)')
    args, _others = parser.parse_known_args(argv)
    settings = load_settings(args.settings)
    with open(args.shot_list) as handle:
        shot = json.load(handle)
    place_facts = None
    if args.place_facts:
        with open(args.place_facts) as handle:
            place_facts = json.load(handle)
    scene = Scene(bpy, settings)
    if scene.camera is None:
        raise SystemExit('make_check_file: the scene has no camera (the assemble script leaves one at the view)')
    scene.scene.render.resolution_x, scene.scene.render.resolution_y, scene.scene.render.resolution_percentage = scene.width, scene.height, 100
    bpy.context.view_layer.update()
    check, facts, notes = generate(scene, shot, settings, place_facts)
    os.makedirs(os.path.dirname(os.path.abspath(args.check_file)), exist_ok=True)
    with open(args.check_file, 'w') as handle:
        json.dump(check, handle, indent=1)
    lines = [f'make_check_file: wrote {args.check_file} for view {shot.get("view")} ({", ".join(facts["kinds_of_shot"])}), camera '
             f'"{scene.camera.name}"',
             f'  groups ({len(check["groups"])}): {", ".join(check["groups"])}',
             f'    declared in the shot list: {", ".join(facts["declared_groups"]) or "none"}',
             f'  story (shot list): {", ".join(check["story"])}; subject {check.get("subject")}; support {check.get("support")}',
             f'  must_read: {", ".join(check["must_read"]) or "none"}',
             f'  on_ground: {", ".join(check["on_ground"]) or "none"}; stands_on: {check.get("stands_on", {})}',
             f'  lights_in_story: {", ".join(check["lights_in_story"]) or "none"} '
             f'(glowing share of each story group: ' + ', '.join(f'{g} {facts["surfaces"][g]["glowing_share"]:.2f}' for g in check['story']) + ')',
             f'  pairs_also: {", ".join(check["pairs_also"])}',
             f'  eye_height {check["eye_height"]}, story_reaches_down {check["story_reaches_down"]}, sky "{check.get("sky", "sky_dome*")}", '
             f'title_zone {check["title_zone"]}' + (', band: true' if check.get('band') else ''),
             f'  match_excludes: ' + ('; '.join(f'{g} ({", ".join(facts["match_exclude_reasons"][g])})' for g in check['match_excludes']) or 'none'),
             f'  figures: {", ".join(check["figures"]) or "none"}; kind_of_shot {check["kind_of_shot"]}; accepted: {len(check["accepted"])}'
             + (f'; support_surfaces {check["support_surfaces"]}' if check.get('support_surfaces') else ''),
             '  (check_shot.py reads kind_of_shot, figures, fill, support_surfaces and accepted; "band", "match_excludes" and '
             '"own_surface_materials" are for the next tools and the page)']
    lines += [f'  note: {n}' for n in notes]
    result = {'check_file': args.check_file, 'check': check, 'facts': facts, 'notes': notes}
    if args.compare:
        with open(args.compare) as handle:
            hand = json.load(handle)
        result['comparison'] = compare(scene, check, hand)
        lines += comparison_lines(result['comparison'])
    finish('make_check_file', result, lines, settings, args)


if __name__ == '__main__':
    main()
