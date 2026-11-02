"""
What this file does:
Looks at a place the way the camera sees it, so that small details go where they will be seen, on whatever shapes a
builder made and whatever they are called.

It sends a grid of rays from the camera through the frame and keeps, for each ray, the first real surface it meets:
the point, which way the surface faces, the object and the object's role. From that grid it finds:

  - feet: where something standing (a timber wall, a post, a pile, a rock, a tree trunk, a boat, a step) meets the
    ground, as the camera sees it, with the way the standing surface faces;
  - the ground the camera sees (sand, earth, road, pavement, a deck), with its role.

    import survey
    seen = survey.Survey(scene, roles)
    for run in seen.foot_runs({'wood'}):          # each run: Foot after Foot, left to right along one object's foot
        for foot in run:
            foot.point, foot.base, foot.normal, foot.ground_role

Details are not part of the place: anything named "DETAIL • ..." or "LOOK • ..." is looked through.
"""

import math

import bpy
from mathutils import Vector

LOOKED_THROUGH = ('DETAIL •', 'LOOK •')
SEE_THROUGH_ROLES = {'smoke'}
NOT_GROUND = {'roof', 'window lit', 'window dim', 'window dark', 'lamp glass', 'flame', 'smoke', 'recess'}
STANDING = {'wood', 'rock', 'wall', 'plaster', 'trim', 'iron', 'rust', 'pavement', 'grime'}
UP = Vector((0, 0, 1))


class Hit:
    __slots__ = ('location', 'normal', 'obj', 'role')

    def __init__(self, location, normal, obj, role):
        self.location, self.normal, self.obj, self.role = location, normal, obj, role


class Foot:
    """Where a standing surface meets the ground.
    point: on the ground just in front of the surface; base: on the surface at ground level; normal: the way the
    surface faces (level, unit length); surface: where the camera's ray met the surface; lift: how far above the
    ground that was; obj, role: the standing thing; ground_obj, ground_role: what it stands on."""
    __slots__ = ('point', 'base', 'normal', 'surface', 'lift', 'obj', 'role', 'ground_obj', 'ground_role', 'column')


def role_of_object(obj, roles, role_from_name=None):
    if obj is None:
        return None
    if obj.get('place_role'):
        return obj['place_role']
    if obj.name in roles:
        return roles[obj.name]
    if '• laid setts' in obj.name:
        return 'road'
    if '• laid flags' in obj.name:
        return 'pavement'
    if obj.name.startswith('FACADE •'):
        return 'wall'
    return role_from_name(obj.name) if role_from_name else None


class Survey:
    def __init__(self, scene, roles, role_from_name=None, columns=180, limit=120.0):
        self.scene = scene
        self.roles = roles
        self.role_from_name = role_from_name
        self.depsgraph = bpy.context.evaluated_depsgraph_get()
        self.camera = scene.camera
        self.limit = limit
        self.columns = columns
        self.grid = []
        if self.camera is None or self.camera.type != 'CAMERA':
            self.rows = 0
            self.origin = self.camera.matrix_world.translation.copy() if self.camera is not None else Vector((0, 0, 1.6))
            return
        frame = self.camera.data.view_frame(scene=scene)        # top-right, bottom-right, bottom-left, top-left
        width = (frame[0] - frame[3]).length
        height = (frame[0] - frame[1]).length
        self.rows = max(2, int(round(columns * height / max(width, 1e-6))))
        matrix = self.camera.matrix_world
        rotation = matrix.to_3x3()
        self.origin = matrix.translation.copy()
        for j in range(self.rows):
            row = []
            v = (j + 0.5) / self.rows
            for i in range(columns):
                u = (i + 0.5) / columns
                p = frame[2].lerp(frame[1], u).lerp(frame[3].lerp(frame[0], u), v)
                direction = (rotation @ p).normalized()
                row.append(self.first_surface(self.origin, direction, limit))
            self.grid.append(row)

    # ------------------------------------------------------------------------------------------- rays
    def role(self, obj):
        return role_of_object(obj, self.roles, self.role_from_name)

    def first_surface(self, origin, direction, limit, skip_names=()):
        """The first surface along a ray that is part of the place (details, the look and smoke are looked through)."""
        start = origin.copy()
        travelled = 0.0
        for _ in range(10):
            hit, location, normal, index, obj, matrix = self.scene.ray_cast(self.depsgraph, start, direction, distance=limit - travelled)
            if not hit:
                return None
            name = obj.name if obj is not None else ''
            role = self.role(obj)
            if name.startswith(LOOKED_THROUGH) or role in SEE_THROUGH_ROLES or name in skip_names:
                travelled += (location - start).length + 0.0001
                start = location + direction * 0.0001
                if travelled >= limit:
                    return None
                continue
            if normal.dot(direction) > 0:
                normal = -normal
            return Hit(location.copy(), normal.copy(), name, role)
        return None

    def is_ground(self, hit):
        if hit is None or hit.normal.z < 0.6 or hit.role in NOT_GROUND:
            return False
        if hit.role in ('iron', 'rust') and hit.location.z > self.origin.z - 0.3:
            return False      # a tin roof seen from above is not ground; a drain cover is
        return True

    def is_standing(self, hit, roles=None):
        if hit is None or abs(hit.normal.z) > 0.55:
            return False
        return hit.role in (roles or STANDING)

    def ground_under(self, point, above=0.6, depth=30.0):
        """(z, object name, role) of the ground straight below point (starting `above` metres higher), or None."""
        start = Vector((point.x, point.y, point.z + above))
        down = Vector((0, 0, -1))
        for _ in range(24):
            hit, location, normal, index, obj, matrix = self.scene.ray_cast(self.depsgraph, start, down, distance=depth)
            if not hit:
                return None
            name = obj.name if obj is not None else ''
            role = self.role(obj)
            if (name.startswith(LOOKED_THROUGH) or role in SEE_THROUGH_ROLES or role in NOT_GROUND or normal.z < 0.6):
                start = location - Vector((0, 0, 0.0001))
                continue
            return location.z, name, role
        return None

    # ------------------------------------------------------------------------------------------- what is seen
    def ground_seen(self, roles=None, limit=None):
        """Every ground hit the camera sees (optionally only these roles, only nearer than limit)."""
        found = []
        for row in self.grid:
            for hit in row:
                if self.is_ground(hit) and (roles is None or hit.role in roles):
                    if limit is None or (hit.location - self.origin).length < limit:
                        found.append(hit)
        return found

    def feet(self, roles=None, max_lift=0.45, limit=60.0):
        """Every place, column by column, where a standing surface the camera sees meets the ground below it."""
        found = []
        for i in range(self.columns):
            for j in range(1, self.rows):
                below, above = self.grid[j - 1][i], self.grid[j][i]
                if not self.is_standing(above, roles) or not self.is_ground(below):
                    continue
                if (above.location - self.origin).length > limit:
                    continue
                facing = Vector((above.normal.x, above.normal.y, 0))
                if facing.length < 1e-4:
                    continue
                facing.normalize()
                probe = above.location + facing * 0.04
                ground = self.ground_under(probe, above=0.02)
                if ground is None:
                    continue
                z, ground_obj, ground_role = ground
                lift = above.location.z - z
                if lift < -0.05 or lift > max_lift or ground_obj == above.obj:
                    continue
                foot = Foot()
                foot.point = Vector((probe.x, probe.y, z))
                foot.base = Vector((above.location.x, above.location.y, z))
                foot.normal = facing
                foot.surface = above.location
                foot.lift = lift
                foot.obj, foot.role = above.obj, above.role
                foot.ground_obj, foot.ground_role = ground_obj, ground_role
                foot.column = i
                found.append(foot)
        return found

    def foot_runs(self, roles=None, gap=0.6, max_lift=0.45, limit=60.0):
        """Feet grouped into runs: consecutive columns along one object's foot, broken where it jumps."""
        by_object = {}
        for foot in self.feet(roles, max_lift=max_lift, limit=limit):
            by_object.setdefault(foot.obj, []).append(foot)
        runs = []
        for obj, feet in by_object.items():
            feet.sort(key=lambda f: f.column)
            run = [feet[0]]
            for foot in feet[1:]:
                previous = run[-1]
                if foot.column - previous.column > 3 or (foot.point - previous.point).length > gap:
                    runs.append(run)
                    run = []
                if not run or foot.column != run[-1].column:
                    run.append(foot)
            if run:
                runs.append(run)
        return runs

    def surface_point(self, foot, height, strict=False):
        """The standing surface `height` metres above the ground at a foot (it follows a post's curve or a leaning
        rock). Where no surface of that object is found there: None if strict (the thing is lower than that), else
        straight above the foot's base."""
        origin = foot.base + UP * height + foot.normal * 0.5
        hit = self.first_surface(origin, -foot.normal, 0.9)
        if hit is not None and hit.obj == foot.obj:
            return hit.location
        return None if strict else foot.base + UP * height


def indoors_probe(scene, roles, role_from_name=None, reach=12.0):
    """indoors(point): True when the point has something built overhead (more than 1 m up, lying flat or sloping) and is walled
    in on most sides (five of eight level directions blocked within `reach` metres). A room counts even with the
    camera's wall left out; a street under a cornice, an alley and a verandah do not. Foliage, smoke and details do not
    block. Answers are kept per half-metre cell."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    cache = {}
    open_roles = {'weed', 'leaf', 'smoke', 'flame', 'lamp glass'}

    def blocked(start, direction, minimum, walls_only=False):
        travelled = 0.0
        origin = start.copy()
        for _ in range(8):
            hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, origin, direction, distance=reach - travelled)
            if not hit:
                return None
            name = obj.name if obj is not None else ''
            role = role_of_object(obj, roles, role_from_name)
            # rising ground, a table top or a step is not a wall: only a steep surface walls a point in
            if (name.startswith(LOOKED_THROUGH) or role in open_roles or (location - start).length < minimum
                    or (walls_only and abs(normal.z) >= 0.5)):
                travelled += (location - origin).length + 0.001
                origin = location + direction * 0.001
                if travelled >= reach:
                    return None
                continue
            return normal
        return None

    def indoors(point):
        key = (round(point[0] / 0.5), round(point[1] / 0.5), round(point[2] / 0.5))
        if key in cache:
            return cache[key]
        base = Vector((point[0], point[1], point[2] + 0.3))
        overhead = blocked(base, UP, 1.0)
        result = False
        if overhead is not None and abs(overhead.z) > 0.3:      # a ceiling, a roof or a floor above (either way up)
            walls = 0
            for k in range(8):
                a = math.tau * k / 8
                if blocked(base, Vector((math.cos(a), math.sin(a), 0.0)), 0.05, walls_only=True) is not None:
                    walls += 1
            result = walls >= 5
        cache[key] = result
        return result
    return indoors


def steady_seed(text, spread=1000):
    """A number from a name that is the same in every run (Python's own hash() changes each time it starts)."""
    import zlib
    return zlib.crc32(text.encode('utf-8')) % spread


def smooth_wave(t, seed, scale=1.0):
    """A smooth value between -1 and 1 that wanders as t moves (for ragged edges that are not random noise)."""
    return (0.55 * math.sin(t * 1.7 * scale + seed) + 0.3 * math.sin(t * 4.3 * scale + seed * 1.9)
            + 0.15 * math.sin(t * 9.1 * scale + seed * 3.1))


def run_length(run):
    total = 0.0
    out = [0.0]
    for a, b in zip(run, run[1:]):
        total += (b.point - a.point).length
        out.append(total)
    return out
