"""What this does: plans a built set's lights before any picture is drawn, from distances, so a new place does not need
the 26 hand rounds the notice corner took (fire 900 -> 300 -> 220 -> 140 -> 70 W, lantern 60 -> 15 -> 5 -> 3 -> 2 -> 1 W).
It reads the place facts file (calculators/place_facts.py) and the house numbers in film-settings.json, and uses the
core's camera sums (frame_geometry.py) for every point on the frame. For one view it says, light by light:

  role and shadows  key, fire, lamp, doorway, rim, window, fill or sky; only the key, the fire, the lit doorways and the
                    sky cast shadows (round 3: a Works plate took 25 minutes with every light casting, 6 with these)
  starting watts    by the inverse square from a reference light (the subject's key): a lamp 0.12 m from the seat it
                    stands on starts at a few watts, not 60 (a Blender spot of P watts lights its target like a point
                    light of P watts; its cone only masks)
  reach             the farthest part of its target it lights + 0.2 m, and whether that stops short of the first surface
                    it should not light (from Blender ray hits made by paper-film/blender/set_measurements.py beam, or
                    from the place facts' boxes)
  cone              the cone that covers the target (aimed at its middle) and the one aimed at its bottom edge, for a
                    subject lit from below
  links             what it should skip (its own housing, props round a fire) or reach only (a key: the subject and its
                    support; a rim light: the figures), against what it does now
  surfaces          any camera-facing surface it lights more than it lights the subject (round 4: the gate lamp on the
                    pier's face made the pier the brightest thing in W1)
  lamps             set lamps that land on the subject's outline or where the lines meet, and lights just behind the
                    camera that flood the near ground (log 31)
  dark subject      for a dark subject (an iron gate, an opening) the plan does not try to make it the brightest thing
                    (round 5 raised the yard light 260 -> 900 W and the gate stayed at 0.85 times the frame's mean); it
                    lights what is behind it and judges it by its silhouette contrast instead
  EEVEE             the shadow memory settings, and render-log refuses a picture whose log shows a shadow fault
Other commands: exposure (per view, from the other views' brightness), contrast (a dark subject's silhouette contrast on
a picture), render-log (refuse a picture drawn with a shadow fault).
Not done here: tune_lights (a loop of small renders that changes one named light per round, judged by the shot
checker's light rules) is left for later; material and position changes stay with a person.

Use:
  python3 plan_lights.py plan --place-facts F --view V [--state S] [--reference LIGHT] [--role LIGHT=ROLE ...]
        [--beam-hits LIGHT=beam.json ...] [--surfaces surfaces.json] [--lamps lamps.json] [--plate-width 1536]
  python3 plan_lights.py exposure --mean w1=35 --mean w2=49 --mean w3=59     (levels on screen or on the pictures)
  python3 plan_lights.py exposure --picture w1=works-w1-painting.jpg --picture w2=...
  python3 plan_lights.py contrast --place-facts F --view V --picture works-w1-plate.jpg [--spot plate]
        [--subject-box-3d cx,cy,cz,width,depth,height]
  python3 plan_lights.py render-log RENDER.log [...]          exit 1 if a log shows "Shadow buffer full" or the like
Every command takes --json, --out FILE, --report FILE and --settings FILE and names the film-settings.json values used.
Places are Blender metres (x across, y forward, z up); on the frame across 0-1 left to right, down 0-1 top to bottom.
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings, MissingSetting, resolve_profile  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402
import frame_geometry as geometry  # noqa: E402

ROLES = ('key', 'accent', 'fire', 'lamp', 'doorway', 'rim', 'window', 'fill', 'sky')
RAY_RINGS, RAY_PER_RING = 6, 24     # rays spread over a cone for the box ray cast (as set_measurements.py beam)
FAR_METRES = 30.0                   # how far the box ray cast looks


# ------------------------------------------------------------------------------------------------ small sums
def distance_to_box(point, low, high):
    """Metres from a point to an upright box (0 inside)."""
    d = [max(low[i] - point[i], 0.0, point[i] - high[i]) for i in range(3)]
    return math.sqrt(sum(v * v for v in d))


def inside_box(point, low, high):
    return all(low[i] <= point[i] <= high[i] for i in range(3))


def prop_box(prop):
    size = prop.get('size') or [0.0, 0.0, 0.0]
    return geometry.box_from_centre(prop['at'], size)


def angle_between(a, b):
    na, nb = geometry.length(a), geometry.length(b)
    if na == 0 or nb == 0:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, geometry.dot(a, b) / (na * nb)))))


def ray_box(origin, direction, low, high):
    """Where a ray (unit direction) enters and leaves an upright box: (near, far) metres, or None."""
    near, far = -math.inf, math.inf
    for i in range(3):
        if abs(direction[i]) < 1e-12:
            if not low[i] <= origin[i] <= high[i]:
                return None
            continue
        t1, t2 = (low[i] - origin[i]) / direction[i], (high[i] - origin[i]) / direction[i]
        near, far = max(near, min(t1, t2)), min(far, max(t1, t2))
    if far < max(near, 0.0):
        return None
    return max(near, 0.0), far


def cone_directions(axis, cone_degrees, rings=RAY_RINGS, per_ring=RAY_PER_RING):
    """The axis and rings of directions out to the cone's edge (the same spread as set_measurements.py beam)."""
    axis = geometry.normalise(axis)
    helper = [0, 0, 1] if abs(axis[2]) < 0.9 else [1, 0, 0]
    side = geometry.normalise(geometry.cross(axis, helper))
    up = geometry.normalise(geometry.cross(side, axis))
    half = math.radians(cone_degrees / 2)
    directions = [(0.0, axis)]
    for ring in range(1, rings + 1):
        angle = half * ring / rings
        for k in range(per_ring):
            turn = 2 * math.pi * k / per_ring
            sideways = geometry.add(geometry.scale(side, math.cos(turn)), geometry.scale(up, math.sin(turn)))
            directions.append((math.degrees(angle), geometry.normalise(geometry.add(geometry.scale(axis, math.cos(angle)),
                                                                                    geometry.scale(sideways, math.sin(angle))))))
    return directions


# ------------------------------------------------------------------------------------------------ the place
class Place:
    """The place facts with the bits the light planner keeps asking for."""

    def __init__(self, facts, view_name, settings, state=None):
        self.facts, self.settings = facts, settings
        views = {v['name']: v for v in facts['views']}
        if view_name not in views:
            raise SystemExit(f'plan_lights: no view "{view_name}" (views: {", ".join(views)})')
        self.view = views[view_name]
        self.props = {p['name']: p for p in facts.get('props', [])}
        self.figures = facts.get('figures', [])
        self.emitters = facts.get('emitters', [])
        self.lights = [l for l in facts.get('lights', []) if self.in_state(l, view_name, state)]
        self.camera = geometry.camera_from_place_facts(facts, settings, view_name, 'composed', 'film')
        subject = self.view['subject']
        self.subject_name = subject['name']
        self.subject_prop = self.props.get(subject['name']) or next((p for p in self.props.values() if p.get('role') == 'subject'), None)
        self.subject_point = self.subject_prop['at'] if self.subject_prop else subject['point']
        self.support_prop = next((p for p in self.props.values() if p.get('role') == 'support'), None)
        self.dark = bool(subject.get('dark'))

    @staticmethod
    def in_state(light, view_name, state):
        states = light.get('in_states')
        if not states:
            return True
        if state:
            return state in states
        return any(s == view_name or s.startswith(view_name + '-') or s.startswith(view_name + ' ') for s in states) or \
            not any('-' in s or ' ' in s for s in states)

    def figure_names(self):
        names = set()
        for f in self.figures:
            names.add(f['name'])
            names.add(f['name'].replace('-', ' '))
            if f.get('group'):
                names.add(f['group'])
        return names

    def subject_names(self):
        names = {self.subject_name}
        if self.subject_prop:
            names.add(self.subject_prop['name'])
        return names


# ------------------------------------------------------------------------------------------------ light by light
def light_role(place, light, overrides):
    if light['name'] in overrides:
        return overrides[light['name']], 'given'
    name = light['name'].lower()
    if light.get('kind') == 'SUN' or 'sky' in name:
        return 'sky', 'a sun light'
    reaches = set(light.get('reaches_only') or [])
    emitters = sorted(place.emitters, key=lambda e: geometry.length(geometry.subtract(light['at'], e['at'])))
    if emitters and emitters[0].get('kind') == 'lamp':
        gap = geometry.length(geometry.subtract(light['at'], emitters[0]['at']))
        if gap < 0.4:
            return 'lamp', f'{gap:.2f} m from {emitters[0]["name"]}'
    if reaches and reaches & place.subject_names():
        return 'accent', f'reaches only {", ".join(sorted(reaches))} (the subject\'s own light)'
    if light.get('target') and place.subject_prop:
        low, high = prop_box(place.subject_prop)
        if distance_to_box(light['target'], low, high) < 0.3:
            return 'accent', 'aimed at the subject'
    if reaches and reaches <= place.figure_names():
        return 'rim', 'reaches only figures'
    if emitters:
        emitter = emitters[0]
        gap = geometry.length(geometry.subtract(light['at'], emitter['at']))
        if emitter.get('kind') == 'fire' and gap < 1.0:
            return 'fire', f'{gap:.2f} m from {emitter["name"]}'
    for word, role in (('doorway', 'doorway'), ('gateway', 'doorway'), ('spill', 'doorway'), ('room', 'doorway'), ('window', 'window'),
                       ('rim', 'rim'), ('fire', 'fire'), ('brazier', 'fire'), ('lamp', 'lamp'), ('lantern', 'lamp')):
        if word in name:
            return role, f'its name says "{word}"'
    return 'fill', 'none of the above'


def housing_of(place, light, role, settings):
    """What a light should skip (lesson 120; log 32): its housing (the smallest prop box it stands in, else the nearest
    prop within the container distance), and, for a fire, every prop within the container distance (the drum it burns in
    and the chair beside it). Returns (must_skip, near): lists of (name, metres, inside)."""
    container = settings.value('light_planner.container_skip_within_metres')
    found = []
    for prop in place.props.values():
        if not prop.get('size') or prop['name'] in place.subject_names() or prop.get('role') == 'support':
            continue
        low, high = prop_box(prop)
        found.append((prop['name'], distance_to_box(light['at'], low, high), inside_box(light['at'], low, high),
                      prop['size'][0] * prop['size'][1] * prop['size'][2]))
    if role == 'fire':
        must = [(n, g, i) for n, g, i, _ in found if g <= container]
        return sorted(must, key=lambda x: x[1]), []
    containing = sorted((f for f in found if f[2]), key=lambda f: f[3])
    close = sorted((f for f in found if f[1] <= container and not f[2]), key=lambda f: f[1])
    if containing:
        must = [containing[0][:3]]
    elif close:
        must = [close[0][:3]]
    else:
        must = []
    near = [f[:3] for f in close if f[0] not in {m[0] for m in must}]
    return must, near


def nearest_lit_surface(place, light, housing):
    """The nearest surface a light shines on, leaving out its housing and any prop whose box it stands inside (a lamp
    standing on a chair is inside the chair's box): support surfaces under it, and prop boxes."""
    skip = {name for name, _, _ in housing}
    best = None
    notes = []
    for surface in place.facts.get('support_surfaces', []):
        height = surface['height']
        xr, yr = surface.get('x_range'), surface.get('y_range')
        where = surface.get('at')
        if xr and not xr[0] <= light['at'][0] <= xr[1]:
            continue
        if yr and not yr[0] <= light['at'][1] <= yr[1]:
            continue
        if where and not (xr or yr) and math.hypot(where[0] - light['at'][0], where[1] - light['at'][1]) > 1.0:
            continue
        if surface.get('slope') and where:
            height += surface['slope'][0] * (light['at'][0] - where[0]) + surface['slope'][1] * (light['at'][1] - where[1])
        gap = light['at'][2] - height
        if gap > 0 and (best is None or gap < best[1]):
            best = (f'{surface["name"]} (surface below)', gap)
    for prop in place.props.values():
        if prop['name'] in skip or not prop.get('size'):
            continue
        low, high = prop_box(prop)
        if inside_box(light['at'], low, high):
            notes.append(f'it stands inside {prop["name"]}\'s box (measured to the surface under it instead)')
            continue
        gap = distance_to_box(light['at'], low, high)
        if best is None or gap < best[1]:
            best = (prop['name'], gap)
    return best, notes


def subject_corners(place):
    """The subject's corners (its prop box), for cones."""
    if not place.subject_prop or not place.subject_prop.get('size'):
        return [place.subject_point]
    low, high = prop_box(place.subject_prop)
    return geometry.box_corners(low, high)


def cones_for(place, light, settings):
    """Cones that just cover the subject from this light: aimed at its middle (even light) and at its bottom edge's middle
    (lit from below, rule 6): 2 x the largest angle from the aim to the corners it must cover (add a soft edge: the blend)."""
    corners = subject_corners(place)
    centre = place.subject_point
    if len(corners) == 1:
        return None
    even_axis = geometry.subtract(centre, light['at'])
    even = 2 * max(angle_between(even_axis, geometry.subtract(c, light['at'])) for c in corners)
    bottom_z = min(c[2] for c in corners)
    bottom_centre = [centre[0], centre[1], bottom_z]
    bottom_corners = [c for c in corners if abs(c[2] - bottom_z) < 1e-9]
    low_axis = geometry.subtract(bottom_centre, light['at'])
    below = 2 * max(angle_between(low_axis, geometry.subtract(c, light['at'])) for c in bottom_corners)
    top_outside = max(angle_between(low_axis, geometry.subtract(c, light['at'])) for c in corners) > below / 2
    return {'even_cone_degrees': even, 'even_aim': centre, 'from_below_cone_degrees': below, 'from_below_aim': bottom_centre,
            'from_below_leaves_top_unlit': top_outside}


def beam_from_hits(path):
    with open(path) as handle:
        return json.load(handle)


def beam_from_boxes(place, light, axis, cone):
    """The box ray cast: rays over the cone against the place facts' prop boxes and support surfaces (planes), each ray
    keeping every box it passes (entry distance, facing the light), as set_measurements.py beam does with real meshes."""
    rays = []
    surfaces = place.facts.get('support_surfaces', [])
    for angle, direction in cone_directions(axis, cone):
        hits = []
        for prop in place.props.values():
            if not prop.get('size'):
                continue
            low, high = prop_box(prop)
            found = ray_box(light['at'], direction, low, high)
            if found and found[0] > 0:
                hits.append({'distance': found[0], 'object': prop['name'], 'group': prop['name'], 'facing_light': True})
        for surface in surfaces:
            if direction[2] >= -1e-9:
                continue
            t = (surface['height'] - light['at'][2]) / direction[2]
            if 0 < t < FAR_METRES:
                p = geometry.add(light['at'], geometry.scale(direction, t))
                xr, yr = surface.get('x_range'), surface.get('y_range')
                if (not xr or xr[0] <= p[0] <= xr[1]) and (not yr or yr[0] <= p[1] <= yr[1]):
                    hits.append({'distance': t, 'object': surface['name'], 'group': surface['name'], 'facing_light': True})
        rays.append({'off_axis_degrees': angle, 'direction': direction, 'hits': sorted(hits, key=lambda h: h['distance'])})
    return {'light': light['name'], 'at': light['at'], 'cone_degrees': cone, 'rays': rays, 'from': 'place facts boxes'}


def reach_from_beam(beam, targets, excluded, casts_shadow, settings):
    """Reach = the farthest light-facing hit on a target + the margin; it must stop before the nearest surface that is
    not a target and not linked out (every hit along a ray for a light without shadow, the first hit for one with)."""
    margin = settings.value('light_planner.reach_margin_metres')
    farthest, nearest_other, other_name = None, None, None
    for ray in beam['rays']:
        for order, hit in enumerate(ray['hits']):
            group = hit.get('group') or hit.get('object')
            if group in targets:
                if hit.get('facing_light', True) and (farthest is None or hit['distance'] > farthest):
                    farthest = hit['distance']
                continue
            if group in excluded or hit.get('object') in excluded:
                continue
            if casts_shadow and order > 0:
                continue
            if nearest_other is None or hit['distance'] < nearest_other:
                nearest_other, other_name = hit['distance'], group
    result = {'farthest_target_metres': farthest, 'nearest_other_metres': nearest_other, 'nearest_other': other_name}
    if farthest is not None:
        result['reach_metres'] = farthest + margin
        result['clear'] = nearest_other is None or result['reach_metres'] < nearest_other
    return result


def irradiance(power, light_at, point, normal):
    """Light falling on a surface point from a point light (or a spot, whose cone only masks): P cos(theta) / (4 pi r^2)."""
    d = geometry.subtract(light_at, point)
    r = geometry.length(d)
    if r < 1e-6:
        return math.inf
    cos = geometry.dot(normal, d) / r
    return power * max(0.0, cos) / (4 * math.pi * r * r)


def rectangle_points(surface, steps=9):
    """Sample points over a rectangle {centre, normal, along, width, height} (along: the width's direction; height runs
    along normal x along)."""
    centre, normal = surface['centre'], geometry.normalise(surface['normal'])
    along = surface.get('along') or geometry.cross([0, 0, 1], normal)
    along = geometry.normalise(along if geometry.length(along) > 1e-9 else [1, 0, 0])
    up = geometry.normalise(geometry.cross(normal, along))
    points = []
    for i in range(steps):
        for j in range(steps):
            u = (i / (steps - 1) - 0.5) * surface['width']
            v = (j / (steps - 1) - 0.5) * surface['height']
            points.append(geometry.add(centre, geometry.add(geometry.scale(along, u), geometry.scale(up, v))))
    return points


def box_faces(prop):
    """An upright prop box's five outer faces (not its bottom) as rectangles."""
    low, high = prop_box(prop)
    c = prop['at']
    size = prop['size']
    faces = []
    for axis, sign in ((0, -1), (0, 1), (1, -1), (1, 1)):
        normal = [0.0, 0.0, 0.0]
        normal[axis] = float(sign)
        centre = list(c)
        centre[axis] = high[axis] if sign > 0 else low[axis]
        along = [0.0, 0.0, 0.0]
        along[1 - axis] = 1.0
        faces.append({'name': prop['name'], 'face': f'{"-+"[sign > 0]}{"xy"[axis]}', 'centre': centre, 'normal': normal, 'along': along,
                      'width': size[1 - axis], 'height': size[2], 'role': prop.get('role', 'other')})
    faces.append({'name': prop['name'], 'face': '+z', 'centre': [c[0], c[1], high[2]], 'normal': [0, 0, 1], 'along': [1, 0, 0],
                  'width': size[0], 'height': size[1], 'role': prop.get('role', 'other')})
    return faces


def lit_by(light, surface_name):
    """Whether light linking lets this light reach a surface (by its name or group)."""
    if light.get('reaches_only'):
        return surface_name in light['reaches_only']
    return surface_name not in (light.get('skips') or [])


def surfaces_check(place, light, surfaces, settings):
    """A lamp lights the face it hangs on (round 4: the gate lamp turned No. 1's pier into the brightest thing in W1):
    the brightest camera-facing point of each surface near the light (and in the frame) that the light reaches, against
    the brightest point of the subject that the same light gives. Story props (by role, or carrying a sign) are left to
    the shot checker."""
    near = settings.value('light_planner.near_surface_within_metres')
    camera = place.camera
    signs = {s['name'] for s in place.facts.get('signs', [])}
    rows = []
    for surface in surfaces:
        name = surface['name']
        if not lit_by(light, name) and not lit_by(light, surface.get('group', name)):
            continue
        normal = geometry.normalise(surface['normal'])
        if geometry.dot(normal, geometry.subtract(camera['position'], surface['centre'])) <= 0:
            continue
        points = rectangle_points(surface)
        is_subject = name in place.subject_names() or surface.get('role') == 'subject'
        if not is_subject:
            closest = min(geometry.length(geometry.subtract(p, light['at'])) for p in points)
            if closest > near:
                continue
            landed = geometry.project_box(camera, points)
            box = landed['box']
            if not box or box[2] < 0 or box[0] > 1 or box[3] < 0 or box[1] > 1:
                continue
        best = max(irradiance(light['watts'] or 0.0, light['at'], p, normal) for p in points)
        story = surface.get('role') in ('support', 'story') or name in signs
        rows.append({'surface': name + (f' ({surface["face"]})' if surface.get('face') else ''), 'name': name,
                     'role': 'subject' if is_subject else ('story' if story else surface.get('role', 'other')), 'brightest': best})
    subject = [r for r in rows if r['role'] == 'subject']
    others = [r for r in rows if r['role'] not in ('subject', 'story')]
    on_subject = max((r['brightest'] for r in subject), default=0.0)
    worse = sorted((r for r in others if r['brightest'] > on_subject), key=lambda r: -r['brightest'])
    return {'on_subject': on_subject, 'brighter_than_subject': worse, 'all': rows}


def lamps_check(place, lamps, settings, roles=None):
    """Set lamps on the frame: near the subject's outline (with its support) or where the lines meet, and lights just
    behind the camera."""
    camera = place.camera
    width, height = camera['frame']
    gap_pixels = settings.value('light_planner.lamp_clear_of_subject_pixels')
    meeting_gap = settings.value('camera.meeting_point_gap_share_of_width')
    ground_max = settings.value('light_planner.near_ground_light_max')
    near_ground = bottom_edge_ground(place)
    boxes = []
    for prop in (place.subject_prop, place.support_prop):
        if prop and prop.get('size'):
            landed = geometry.project_box(camera, geometry.box_corners(*prop_box(prop)))
            if landed['box']:
                boxes.append((prop['name'], landed['box']))
    lines = place.facts.get('lines', {})
    direction = lines.get(place.facts.get('lines_key')) if place.facts.get('lines_key') else None
    meeting = geometry.project_direction(camera, direction) if direction else None
    story = [prop_box(p) for p in place.props.values() if p.get('role') in ('subject', 'support', 'story') and p.get('size')]
    found = []
    for name, lamp in lamps.items():
        where = lamp.get('at') or [(a + b) / 2 for a, b in zip(lamp['box_low'], lamp['box_high'])]
        if any(distance_to_box(where, low, high) <= 0.2 for low, high in story):
            continue   # a story prop's own lamp (the lantern): the shot checker judges it with the story
        if 'box_low' in lamp:
            landed = geometry.project_box(camera, geometry.box_corners(lamp['box_low'], lamp['box_high']))
            box = landed['box']
            depth = landed['nearest_depth']
        else:
            point = geometry.project_point(camera, lamp['at'])
            box = [point['across'], point['down'], point['across'], point['down']] if point['in_front'] else None
            depth = point['depth']
        row = {'lamp': name, 'box': box, 'depth': depth, 'problems': []}
        if box is None:
            d = geometry.dot(geometry.subtract(lamp.get('at') or lamp['box_low'], camera['position']), camera['forward'])
            role = (roles or {}).get(name, 'lamp')
            if d <= 0 and lamp.get('watts') and near_ground and role in ('lamp', 'fill', 'fire', 'key'):
                on_ground = irradiance(lamp['watts'], lamp['at'], near_ground, [0, 0, 1])
                row['near_ground_light'] = on_ground
                if on_ground > ground_max:
                    row['problems'].append(f'a light {abs(d):.1f} m behind the camera puts {on_ground:.3f} W/m2 on the ground at the frame\'s bottom '
                                           f'edge (at most {ground_max}): it floods the near ground where the eye enters; dim it to about '
                                           f'{lamp["watts"] * ground_max / on_ground:.0f} W or remove it')
            found.append(row)
            continue
        if box[2] < 0 or box[0] > 1 or box[3] < 0 or box[1] > 1:
            found.append(row)
            continue
        for prop_name, prop_box_on_frame in boxes:
            dx = max(prop_box_on_frame[0] - box[2], box[0] - prop_box_on_frame[2], 0.0) * width
            dy = max(prop_box_on_frame[1] - box[3], box[1] - prop_box_on_frame[3], 0.0) * height
            gap = math.hypot(dx, dy)
            if gap < gap_pixels:
                row['problems'].append(f'{gap:.0f} px from the {prop_name}\'s outline (needs {gap_pixels}): move or remove it')
        if meeting:
            dx = max(box[0] - meeting['across'], meeting['across'] - box[2], 0.0)
            dy = max(box[1] - meeting['down'], meeting['down'] - box[3], 0.0) * height / width
            if math.hypot(dx, dy) < meeting_gap:
                row['problems'].append(f'on where the lines meet ({math.hypot(dx, dy):.3f} of the width away; needs {meeting_gap}): move or remove it')
        found.append(row)
    return found, meeting


def subject_light_balance(place, reference):
    """The most light each light gives any of 27 points over the subject's box (W/m2), respecting links, a spot's cone and
    the subject's facing when it is a sign: a point or spot light P cos / (4 pi r^2); an area light at most P cos / (pi r^2)
    (face-on)."""
    target = place.subject_point
    points = [target]
    if place.subject_prop and place.subject_prop.get('size'):
        low, high = prop_box(place.subject_prop)
        points += [[low[0] + (high[0] - low[0]) * i / 2, low[1] + (high[1] - low[1]) * j / 2, low[2] + (high[2] - low[2]) * k / 2]
                   for i in range(3) for j in range(3) for k in range(3)]
    sign = next((s for s in place.facts.get('signs', []) if s['name'] in place.subject_names()), None)
    by_light = {}
    for light in place.lights:
        if light.get('kind') == 'SUN' or not light.get('watts'):
            continue
        if not (lit_by(light, place.subject_name) or (place.subject_prop and lit_by(light, place.subject_prop['name']))):
            continue
        best = 0.0
        for point in points:
            d = geometry.subtract(light['at'], point)
            r = geometry.length(d)
            if r < 1e-6:
                continue
            cos = geometry.dot(geometry.normalise(sign['normal']), d) / r if sign else 1.0
            if cos <= 0:
                continue
            if light.get('kind') == 'SPOT' and light.get('cone_degrees'):
                axis = geometry.subtract(light['target'], light['at']) if light.get('target') else light.get('aim')
                if axis and angle_between(axis, geometry.scale(d, -1)) > light['cone_degrees'] / 2:
                    continue
            spread = math.pi if light.get('kind') == 'AREA' else 4 * math.pi
            best = max(best, light['watts'] * cos / (spread * r * r))
        if best > 0:
            by_light[light['name']] = best
    return {'points': len(points), 'by_light': by_light}


def bottom_edge_ground(place):
    """Where the frame's bottom edge (its middle) meets the ground the camera stands on, or None."""
    camera = place.camera
    floor = place.view['camera'].get('floor_height')
    if floor is None:
        return None
    half = math.tan(math.radians(camera['vertical_fov_degrees']) / 2)
    direction = geometry.subtract(camera['forward'], geometry.scale(camera['up'], half))
    if direction[2] >= 0:
        return None
    t = (floor - camera['position'][2]) / direction[2]
    return geometry.add(camera['position'], geometry.scale(direction, t))


def lamps_from(place, path):
    """Lamps to check: a set_measurements.py objects file (meshes' boxes and lights), plus the place's lamp emitters and
    lights."""
    lamps = {}
    if path:
        with open(path) as handle:
            lamps.update(json.load(handle)['objects'])
    for emitter in place.emitters:
        if emitter.get('kind') == 'lamp':
            lamps.setdefault(emitter['name'], {'type': 'EMITTER', 'at': emitter['at']})
    for light in place.lights:
        if light.get('kind') != 'SUN':
            lamps.setdefault(light['name'], {'type': 'LIGHT', 'at': light['at'], 'watts': light.get('watts')})
    return lamps


# ------------------------------------------------------------------------------------------------ the plan command
def parse_pairs(items, what):
    pairs = {}
    for item in items or []:
        name, _, value = item.partition('=')
        if not value:
            raise SystemExit(f'plan_lights: {what} "{item}" should be NAME=VALUE')
        pairs[name] = value
    return pairs


def command_plan(args, settings):
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    place = Place(facts, args.view, settings, args.state)
    roles = parse_pairs(args.role, '--role')
    beams = parse_pairs(args.beam_hits, '--beam-hits')
    for role in roles.values():
        if role not in ROLES:
            raise SystemExit(f'plan_lights: role "{role}" is not one of {", ".join(ROLES)}')
    casting = settings.value('light_planner.shadow_casting_kinds')
    foot = settings.value('light_planner.foot_patch_metres')
    lines = [f'Lights of {facts["place"]} for view {place.view["name"]} (subject: {place.subject_name}'
             + (', DARK' if place.dark else '') + f'): {len(place.lights)} light(s).']
    result = {'place': facts['place'], 'view': place.view['name'], 'subject': place.subject_name, 'dark_subject': place.dark, 'lights': []}
    # the reference light for the inverse square
    described = {}
    for light in place.lights:
        role, why = light_role(place, light, roles)
        described[light['name']] = (role, why)
    reference = None
    if args.reference:
        reference = next((l for l in place.lights if l['name'] == args.reference), None)
        if reference is None:
            raise SystemExit(f'plan_lights: no light "{args.reference}" (lights: {", ".join(l["name"] for l in place.lights)})')
    elif not place.dark:
        reference = next((l for l in place.lights if described[l['name']][0] == 'accent' and l.get('watts')), None)
    reference_distance = geometry.length(geometry.subtract(reference['at'], place.subject_point)) if reference else None
    if reference:
        lines.append(f'Reference: {reference["name"]} ({reference["watts"]} W, {reference_distance:.2f} m from the subject\'s middle): it '
                     f'gives the subject {irradiance(reference["watts"], reference["at"], place.subject_point, geometry.normalise(geometry.subtract(reference["at"], place.subject_point))):.1f} W/m2.')
    elif place.dark:
        lines.append('A dark subject: no starting watts from a light on the subject (see the dark-subject plan below; give --reference to '
                     'start from a light anyway).')
    else:
        lines.append('No key light found for the subject (a light whose reaches_only names it, or that is aimed at it): give --reference.')
    surfaces = []
    for prop in place.props.values():
        if prop.get('size') and all(s > 0 for s in prop['size']):
            surfaces += box_faces(prop)
    if args.surfaces:
        with open(args.surfaces) as handle:
            surfaces += json.load(handle)['surfaces']
    problems = []
    for light in place.lights:
        role, why = described[light['name']]
        row = {'light': light['name'], 'kind': light.get('kind'), 'watts': light.get('watts'), 'role': role, 'role_because': why,
               'casts_shadow': role in casting, 'problems': [], 'notes': []}
        lines.append('')
        lines.append(f'{light["name"]} ({light.get("kind", "?")}, {light.get("watts")} W): {role} ({why}); '
                     + ('casts shadows' if row['casts_shadow'] else 'no shadows'))
        if role == 'sky':
            result['lights'].append(row)
            continue
        housing, nearby = housing_of(place, light, role, settings)
        if housing:
            row['housing'] = [h[0] for h in housing]
            missing = [h for h in row['housing'] if lit_by(light, h)]
            what = 'props round the fire' if role == 'fire' else 'housing'
            lines.append(f'  {what}: {", ".join(f"{n} ({g:.2f} m{", inside" if i else ""})" for n, g, i in housing)}'
                         + (f'; it still lights {", ".join(missing)}: add them to its skips' if missing else ' (linked out)'))
            if missing:
                row['problems'].append(f'lights {", ".join(missing)} (its {what}; lesson 120, log 32): skip them')
        if nearby:
            row['near'] = [h[0] for h in nearby]
            lit = [n for n in row['near'] if lit_by(light, n)]
            if lit:
                row['notes'].append(f'close to {", ".join(lit)}: skip them if they come out as bright as the subject')
                lines.append(f'  close: {", ".join(f"{n} ({g:.2f} m)" for n, g, _ in nearby)}: skip them if they come out as bright as the subject')
        if role == 'accent':
            wanted = {place.subject_name} | ({place.support_prop['name']} if place.support_prop else set())
            if not light.get('reaches_only'):
                row['notes'].append(f'a key light should reach only {", ".join(sorted(wanted))} (light linking)')
                lines.append(f'  link: let it reach only {", ".join(sorted(wanted))}')
        if role == 'rim' and not set(light.get('reaches_only') or []) <= place.figure_names():
            row['notes'].append('a rim light should reach only the figures')
        # starting watts by the inverse square
        if light.get('kind') == 'AREA' and reference and light is not reference:
            lines.append('  start: an area light (it shines from one face, not like a point): not planned by the inverse square')
        elif reference and light is not reference and role in ('lamp', 'fire', 'fill', 'window', 'key'):
            nearest, notes = nearest_lit_surface(place, light, housing)
            if nearest and nearest[1] > reference_distance:
                lines.append(f'  start: not by the inverse square (its nearest lit surface, {nearest[0]}, is {nearest[1]:.2f} m away, farther '
                             f'than the reference\'s {reference_distance:.2f} m): set it by the light rules')
            elif nearest:
                start = reference['watts'] * (nearest[1] / reference_distance) ** 2
                row.update({'nearest_lit': nearest[0], 'nearest_lit_metres': nearest[1], 'start_watts': start})
                ratio = (light['watts'] / start) if light.get('watts') and start > 0 else None
                lines.append(f'  start: {start:.1f} W (its nearest lit surface, {nearest[0]}, is {nearest[1]:.2f} m away; so it lights that no '
                             f'more than the key lights the subject)' + (f'; it has {light["watts"]} W ({ratio:.1f} times that)' if ratio else ''))
                for note in notes:
                    lines.append(f'  ({note})')
        # reach and cone for a light aimed at its target
        if (light.get('kind') == 'SPOT' and role in ('accent', 'key')) or light['name'] in beams:
            axis = None
            if light.get('target'):
                axis = geometry.subtract(light['target'], light['at'])
            elif light.get('aim'):
                axis = light['aim']
            cone = light.get('cone_degrees') or 60.0
            if light['name'] in beams:
                beam = beam_from_hits(beams[light['name']])
                source = f'Blender ray hits ({os.path.basename(beams[light["name"]])})'
            elif axis:
                beam = beam_from_boxes(place, light, axis, cone)
                source = 'the place facts\' boxes (rough: walls are not in them; use set_measurements.py beam)'
            else:
                beam = None
            if beam:
                targets = set(light.get('reaches_only') or []) & place.subject_names() if role in ('key', 'accent') else set(light.get('reaches_only') or [])
                targets = targets or (place.subject_names() if role in ('key', 'accent') else set())
                excluded = set(row.get('housing', [])) | set(light.get('skips') or []) | set(light.get('reaches_only') or [])
                if role in ('key', 'accent') and place.support_prop:
                    excluded.add(place.support_prop['name'])     # a subject's own light may light its support (the board round a notice)
                linked = bool(light.get('reaches_only'))
                if targets:
                    found = reach_from_beam(beam, targets, excluded, row['casts_shadow'], settings)
                    row['reach'] = dict(found, source=source)
                    if found.get('farthest_target_metres') is not None:
                        text = (f'  reach: {found["reach_metres"]:.2f} m (the farthest lit part of {", ".join(sorted(targets))} is '
                                f'{found["farthest_target_metres"]:.2f} m away, from {source})')
                        if light.get('reach_metres'):
                            text += f'; it has {light["reach_metres"]:.2f} m'
                        lines.append(text)
                        if found['nearest_other'] is not None:
                            lines.append(f'  first surface it should not light: {found["nearest_other"]} at {found["nearest_other_metres"]:.2f} m'
                                         + (' (linked out: its reaches_only list keeps the light off it)' if linked else
                                            (' (the reach stops short of it)' if found['clear'] else '')))
                        if not found['clear'] and not linked:
                            row['problems'].append(f'{found["nearest_other"]} at {found["nearest_other_metres"]:.2f} m lies inside the cone before the '
                                                   f'reach ends ({found["reach_metres"]:.2f} m): link the light to its target (reaches only) or aim it '
                                                   'away; a shorter reach would leave the target\'s far part dark')
                    else:
                        lines.append(f'  reach: no ray of its cone meets {", ".join(sorted(targets))} ({source})')
                        row['problems'].append(f'its cone misses {", ".join(sorted(targets))}')
            if role in ('key', 'accent'):
                cones = cones_for(place, light, settings)
                if cones:
                    row['cones'] = cones
                    lines.append(f'  cone that just covers it: {cones["even_cone_degrees"]:.0f} degrees aimed at the subject\'s middle (even light), or '
                                 f'{cones["from_below_cone_degrees"]:.0f} degrees aimed at its bottom edge (lit from below'
                                 + ('; its top stays outside the cone, warm bottom and cool top' if cones['from_below_leaves_top_unlit'] else '')
                                 + f'); blend {settings.value("light_planner.cone_blend")}' + (f'; it has {light["cone_degrees"]:.0f}' if light.get('cone_degrees') else ''))
        # camera-facing surfaces it lights more than the subject
        if surfaces and light.get('watts') and role not in ('rim',):
            found = surfaces_check(place, light, surfaces, settings)
            if found['brighter_than_subject']:
                worst = found['brighter_than_subject'][0]
                row['brighter_than_subject'] = [{'surface': r['surface'], 'brightest': r['brightest']} for r in found['brighter_than_subject'][:3]]
                scale = found['on_subject'] / worst['brightest'] if worst['brightest'] > 0 else 0
                row['problems'].append(f'it lights {worst["surface"]} (facing the camera) {worst["brightest"]:.2f} W/m2 against the subject\'s '
                                       f'{found["on_subject"]:.2f}: move it behind that face (to an inner face), or link it to skip it; at the '
                                       f'same place it would need {scale * 100:.0f}% of its watts')
        for problem in row['problems']:
            lines.append(f'  PROBLEM {problem}')
            problems.append(f'{light["name"]}: {problem}')
        result['lights'].append(row)
    # how much light reaches the subject from each light, against its own key (a burnt-out risk, rule 5)
    if reference:
        balance = subject_light_balance(place, reference)
        result['subject_light'] = balance
        over = settings.value('light_planner.subject_light_over_key_max')
        key = balance['by_light'].get(reference['name'], 0.0)
        total = sum(balance['by_light'].values())
        if key <= 0:
            problem = f'the key ({reference["name"]}) does not reach the subject: its cone misses it, or a link keeps it off'
            lines.append('')
            lines.append(f'Light on the subject: PROBLEM {problem}')
            problems.append(problem)
        else:
            ratio = total / key
            result['subject_light_over_key'] = ratio
            top = sorted(balance['by_light'].items(), key=lambda kv: -kv[1])[:3]
            lines.append('')
            lines.append(f'Light on the subject (its brightest point for each light): {total:.1f} W/m2 in all, {ratio:.1f} times what its key ({reference["name"]}) gives it; most from '
                         + ', '.join(f'{n} {v:.1f}' for n, v in top) + ' (area lights counted at their face-on most).')
            if ratio > over:
                problem = (f'the subject gets {ratio:.0f} times its key light (at most {over}), mostly from {top[0][0]}: its colour will burn out (rule 5); '
                           'turn that light down or move it away')
                lines.append(f'  PROBLEM {problem}')
                problems.append(problem)
    # lamps on the frame
    lamps = lamps_from(place, args.lamps)
    lamp_rows, meeting = lamps_check(place, lamps, settings, {name: role for name, (role, _) in described.items()})
    flagged = [r for r in lamp_rows if r['problems']]
    lines.append('')
    lines.append(f'Lamps on the frame ({len(lamps)} checked' + (f'; the lines meet at {meeting["across"]:.3f} across, {meeting["down"]:.3f} down' if meeting else '')
                 + '): ' + ('none in the way.' if not flagged else f'{len(flagged)} in the way.'))
    for r in flagged:
        for problem in r['problems']:
            lines.append(f'  PROBLEM {r["lamp"]}: {problem}')
            problems.append(f'{r["lamp"]}: {problem}')
    result['lamps'] = lamp_rows
    # shadows, foot patches and EEVEE
    casters = [r['light'] for r in result['lights'] if r['casts_shadow']]
    plate_width = args.plate_width or settings.value('frame.plate_width_pixels')
    reference_width = settings.value('light.shadow_resolution_reference_width')
    pool = settings.value('light.shadow_pool_size')
    result['shadow_casters'] = casters
    result['eevee'] = {'shadow_pool_size': str(pool), 'shadow_resolution_scale': min(1.0, reference_width / plate_width)}
    lines.append('')
    lines.append(f'Shadows: only {", ".join(casters) if casters else "(none: name a key, fire, doorway or sky light)"} cast shadows; every other '
                 f'light none. Figures: visible_shadow off, each with a soft foot patch {foot[0]} x {foot[1]} m.')
    lines.append(f'EEVEE for a {plate_width}-wide plate: shadow_pool_size \'{pool}\', shadow_resolution_scale {result["eevee"]["shadow_resolution_scale"]:.3f}. '
                 f'After every render run plan_lights.py render-log on its log; a shadow fault draws false black wedges (lesson 110).')
    lines.append('Plate time: measure and record it (round 3: about 25 minutes with every light casting, about 6 with three).')
    # the dark subject
    if place.dark:
        profile = resolve_profile(settings, place.view.get('kind_of_shot') or ['still_life'])
        contrast = profile.get('silhouette_contrast', {}).get('value')
        behind = []
        for light in place.lights:
            depth_light = geometry.project_point(place.camera, light['at'])['depth']
            depth_subject = geometry.project_point(place.camera, place.subject_point)['depth']
            if depth_light > depth_subject and described[light['name']][0] not in ('sky', 'rim'):
                behind.append(light['name'])
        result['dark_subject_plan'] = {'silhouette_contrast_min': contrast, 'lights_behind_subject': behind}
        lines.append('')
        lines.append(f'Dark subject ({place.subject_name}): do not try to make it the brightest thing (round 5 raised the yard light 260 -> 900 W '
                     f'and the gate stayed at 0.85 times the frame\'s mean). Light what is behind it, rim-light the figures, and judge it by its '
                     f'silhouette contrast, at least {contrast} (plan_lights.py contrast on the plate or painting). Lights behind it now: '
                     + (', '.join(behind) if behind else 'none: add one (a cool yard or room light behind the subject, no shadow)') + '.')
    result['problems'] = problems
    lines.append('')
    lines.append(f'{len(problems)} problem(s).' + (' Tuning by small renders (tune_lights) is not built yet: change one named light at a time and '
                                                   're-run the shot checker.' if problems else ''))
    return result, lines


# ------------------------------------------------------------------------------------------------ other commands
def picture_mean_levels(path):
    import numpy as np
    from PIL import Image
    picture = np.asarray(Image.open(path).convert('RGB')).astype(float)
    return float((picture @ [0.2126, 0.7152, 0.0722]).mean())


def command_exposure(args, settings):
    low, high = settings.value('light_planner.exposure_range')
    means = {k: float(v) for k, v in parse_pairs(args.mean, '--mean').items()}
    for view, path in parse_pairs(args.picture, '--picture').items():
        means[view] = picture_mean_levels(path)
    if len(means) < 2:
        raise SystemExit('plan_lights exposure: give at least two views (--mean VIEW=LEVELS or --picture VIEW=FILE)')
    lines = ['Exposure per view: each view brought to the mean of the other views (measure on the paintings when they exist, '
             'not the plates), within ' + f'{low} to {high}; check the result once on screen (the stage\'s tone curve is not straight).']
    rows = {}
    for view, mean in means.items():
        others = [m for v, m in means.items() if v != view]
        target = sum(others) / len(others)
        exposure = min(high, max(low, target / mean)) if mean > 0 else high
        rows[view] = {'mean_levels': mean, 'others_mean': target, 'exposure': exposure}
        lines.append(f'  {view}: {mean:.0f} levels against the others\' {target:.0f}: exposure {exposure:.2f}')
    return {'views': rows}, lines


# The silhouette contrast is measured the way the people test measured the 2.2 it is judged against (working files
# redesign/people-paint/check-figures/scripts/films.py lines 7-24): relative luminance (sRGB made linear), the subject's
# mask shrunk by 2 pixels, against a ring from 2 to 12 pixels outside it, on the 1920-row film frame.
INNER_SHRINK, RING_FROM, RING_TO = 2, 2, 12


def linear_luminance(picture):
    """Relative luminance (0 to 1) of an sRGB picture (levels 0 to 255)."""
    import numpy as np
    c = picture / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def grow(mask, pixels):
    """The mask grown (pixels > 0) or shrunk (pixels < 0) by a square of that many pixels each way."""
    import numpy as np
    import cv2
    if pixels == 0:
        return mask.copy()
    kernel = np.ones((2 * abs(pixels) + 1, 2 * abs(pixels) + 1), np.uint8)
    action = cv2.dilate if pixels > 0 else cv2.erode
    return action(mask.astype(np.uint8), kernel) > 0


def command_contrast(args, settings):
    """A dark subject's silhouette contrast: (surround + 0.05) / (subject + 0.05) in relative luminance, the surround a ring
    round the subject (its shot_facts solo mask when given, else its box on the frame), as the people test measured it."""
    import numpy as np
    from PIL import Image
    with open(args.place_facts) as handle:
        facts = json.load(handle)
    place = Place(facts, args.view, settings)
    picture = np.asarray(Image.open(args.picture).convert('RGB')).astype(float)
    rows, cols = picture.shape[:2]
    luma = linear_luminance(picture)
    full_rows = args.frame_height or rows     # a crop of a frame: the ring is measured in the full frame's pixels
    scale = full_rows / settings.value('frame.height_pixels')
    inner_shrink, ring_from, ring_to = (max(1, int(round(v * scale))) for v in (INNER_SHRINK, RING_FROM, RING_TO))
    needed = resolve_profile(settings, ['dark_subject'])['silhouette_contrast']['value']
    if args.subject_mask:
        drawn = np.asarray(Image.open(args.subject_mask).convert('RGB')).astype(int)
        if drawn.shape[:2] != (rows, cols):
            raise SystemExit(f'plan_lights contrast: the mask is {drawn.shape[1]} x {drawn.shape[0]}, the picture {cols} x {rows}')
        mask = drawn.sum(axis=2) > 30
        how = f'its solo mask {os.path.basename(args.subject_mask)} ({int(mask.sum())} pixels)'
        box = None
    else:
        camera = geometry.camera_from_place_facts(facts, settings, args.view, args.spot, 'plate' if args.spot == 'plate' else 'film')
        camera = geometry.with_lens(camera, camera['vertical_fov_degrees'], cols, rows)
        if args.subject_box_3d:
            values = [float(v) for v in args.subject_box_3d.split(',')]
            low, high = geometry.box_from_centre(values[:3], values[3:])
        elif place.subject_prop and place.subject_prop.get('size'):
            low, high = prop_box(place.subject_prop)
        else:
            raise SystemExit('plan_lights contrast: give --subject-mask (a shot_facts solo picture) or --subject-box-3d cx,cy,cz,width,depth,height')
        box = geometry.project_box(camera, geometry.box_corners(low, high))['box']
        mask = np.zeros((rows, cols), bool)
        mask[max(0, int(box[1] * rows)):int(box[3] * rows), max(0, int(box[0] * cols)):int(box[2] * cols)] = True
        how = f'its box on the frame ({box[0]:.3f}-{box[2]:.3f} across, {box[1]:.3f}-{box[3]:.3f} down; a box mixes in what shows between its parts)'
    inner = grow(mask, -inner_shrink)
    band = grow(mask, ring_to) & ~grow(mask, ring_from)
    subject, surround = float(luma[inner].mean()), float(luma[band].mean())
    contrast = (surround + 0.05) / (subject + 0.05)
    frame_mean = float(luma.mean())
    lines = [f'{place.subject_name} on {os.path.basename(args.picture)}, by {how}: relative luminance {subject:.4f} '
             f'({subject / frame_mean:.2f} times the frame\'s mean), a ring {ring_from}-{ring_to} px round it {surround:.4f}: silhouette contrast '
             f'(surround + 0.05) / (subject + 0.05) = {contrast:.2f} (a dark subject needs {needed}, measured the same way on the people test\'s '
             f'painted figures)' + ('.' if contrast >= needed else
             ': light what is behind it (a cool yard or room light, no shadow) or darken the subject; brightening the subject itself will not get there.')]
    return {'box': box, 'subject_luminance': subject, 'surround_luminance': surround, 'subject_over_frame_mean': subject / frame_mean,
            'contrast': contrast, 'needed': needed, 'passes': contrast >= needed}, lines


def clock_seconds(text):
    """Blender's log time stamp (MM:SS.mmm or H:MM:SS.mmm) in seconds."""
    parts = [float(p) for p in text.split(':')]
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def saved_pictures(text):
    """Each picture a Blender log says it saved, with the minutes since the one before (the plate's drawing time)."""
    saved = []
    for match in re.finditer(r'^\s*([\d:.]+)\s+render\s+\|\s+Saved:\s+\'([^\']+)\'', text, re.M):
        saved.append((clock_seconds(match.group(1)), os.path.basename(match.group(2))))
    rows = []
    for (before, _), (at, name) in zip(saved, saved[1:]):
        rows.append({'picture': name, 'minutes': (at - before) / 60})
    return rows


def command_render_log(args, settings):
    """Refuses a picture whose render log shows a shadow fault (lesson 110), and reads how long each picture took to draw
    (the skeptic of log 35: measure and record plate times rather than predict them)."""
    faults = settings.value('light.render_faults')
    rows, lines = [], []
    for path in args.logs:
        with open(path, errors='replace') as handle:
            text = handle.read()
        found = [f for f in faults if f in text]
        count = sum(text.count(f) for f in found)
        times = saved_pictures(text)
        rows.append({'log': path, 'faults': found, 'fault_lines': count, 'drawing_minutes': times})
        lines.append(f'{os.path.basename(path)}: ' + ('REFUSE the picture: ' + '; '.join(f'"{f}"' for f in found) + f' ({count} times; shadow memory '
                                                       'ran out: false black wedges or no shadows. Lower the shadow resolution scale or cast '
                                                       'fewer shadows, then draw it again)' if found else 'no shadow fault'))
        for row in times:
            lines.append(f'  {row["picture"]}: drawn in {row["minutes"]:.1f} min')
    return {'logs': rows, 'refused': [r['log'] for r in rows if r['faults']]}, lines


def main(argv=None):
    parser = argparse.ArgumentParser(description='Plans a built set\'s lights from distances before any render (see the note at the top).')
    commands = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(commands.add_parser('plan', help='light by light: role, shadows, starting watts, reach, cone, links, surfaces, lamps'))
    p.add_argument('--place-facts', required=True)
    p.add_argument('--view', required=True)
    p.add_argument('--state', help='only lights of this state (a light\'s in_states)')
    p.add_argument('--reference', help='the light the inverse square starts from (default: the subject\'s key light)')
    p.add_argument('--role', action='append', help='LIGHT=ROLE: say a light\'s role (key, fire, lamp, doorway, rim, window, fill, sky)')
    p.add_argument('--beam-hits', action='append', help='LIGHT=FILE: Blender ray hits for that light (set_measurements.py beam)')
    p.add_argument('--surfaces', help='a JSON {"surfaces": [{name, centre, normal, along, width, height, role}]} of faces the boxes miss (walls, piers)')
    p.add_argument('--lamps', help='a set_measurements.py objects file of the set\'s lamps (their boxes and lights)')
    p.add_argument('--plate-width', type=int, help='the plate\'s width in pixels (default film-settings.json frame.plate_width_pixels)')
    p = add_output_options(commands.add_parser('exposure', help='exposure per view from the other views\' brightness'))
    p.add_argument('--mean', action='append', help='VIEW=LEVELS (mean brightness, 0-255)')
    p.add_argument('--picture', action='append', help='VIEW=FILE (its mean brightness is measured)')
    p = add_output_options(commands.add_parser('contrast', help='a dark subject\'s silhouette contrast on a picture'))
    p.add_argument('--place-facts', required=True)
    p.add_argument('--view', required=True)
    p.add_argument('--picture', required=True)
    p.add_argument('--spot', default='plate', choices=['plate', 'composed'])
    p.add_argument('--subject-mask', help='the subject\'s solo picture from shot_facts.py (facts/solo/NAME.png), the same size as the picture')
    p.add_argument('--subject-box-3d', help='cx,cy,cz,width,depth,height (Blender metres), when there is no mask and the subject has no box')
    p.add_argument('--frame-height', type=int, help='when the picture is cut from a frame: that frame\'s height in pixels (the band scales with it)')
    p = add_output_options(commands.add_parser('render-log', help='refuse a picture whose render log shows a shadow fault'))
    p.add_argument('logs', nargs='+')
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    runner = {'plan': command_plan, 'exposure': command_exposure, 'contrast': command_contrast, 'render-log': command_render_log}[args.command]
    try:
        result, lines = runner(args, settings)
    except MissingSetting as problem:
        raise SystemExit(f'plan_lights: {problem}')
    full = finish(f'plan_lights {args.command}', result, lines, settings, args)
    failed = (args.command == 'render-log' and full['refused']) or (args.command == 'contrast' and not full['passes'])
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
