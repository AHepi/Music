# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Finds which objects and materials of a scene have which ROLE (a kind of surface: 'wall.masonry', 'ground.flag', 'iron' ...). The set file says how each role is found:
# by object name (regular expressions), by collection name, by material name, by a custom property on the object, its mesh or its materials.
#   Rule of finding: PASS 1 goes through the roles in the file's order and uses the object name, collection and custom property rules; an object takes the FIRST role that
#   matches. PASS 2 takes the objects that still have no role and tries the material rules, walking the object's material slots in order (the first slot a role claims decides). (So a chimney that shares a wall material keeps its own role.)
#   An object that is in the set's `never` list gets no role at all. A role can be limited to some scenes ("scenes": [...]).
#   `type` ("MESH", "EMPTY" ...) limits what an object may be; the default is MESH.
# The work is done on plain descriptions of objects (ObjDesc) so that it can be tested without Blender; describe_scene() makes them from a Blender scene.
import re

from .settings import Report

DEFAULT_TYPE = 'MESH'


class ObjDesc:
    __slots__ = ('name', 'type', 'collections', 'materials', 'props', 'hidden')

    def __init__(self, name, type='MESH', collections=(), materials=(), props=None, hidden=False):
        self.name = name
        self.type = type
        self.collections = tuple(collections)
        self.materials = tuple(materials)
        self.props = props or {}
        self.hidden = hidden


def describe_scene(scene=None, include_hidden=True):
    """ObjDesc for every object of a Blender scene. props = the object's custom properties plus its mesh's plus each material's, as {name: str(value)}."""
    import bpy
    scene = scene or bpy.context.scene
    result = []
    for obj in scene.objects:
        materials = []
        props = {}
        for source in (obj, getattr(obj, 'data', None)):
            if source is not None and hasattr(source, 'keys'):
                for key in source.keys():
                    value = source[key]
                    if isinstance(value, (str, int, float)):
                        props[key] = str(value)
        for slot in obj.material_slots:
            if slot.material is not None:
                materials.append(slot.material.name)
                for key in slot.material.keys():
                    value = slot.material[key]
                    if isinstance(value, (str, int, float)):
                        props.setdefault(key, str(value))
        hidden = obj.hide_render
        if hidden and not include_hidden:
            continue
        result.append(ObjDesc(obj.name, obj.type, [c.name for c in obj.users_collection], materials, props, hidden))
    return result


def _any(patterns, text):
    return any(re.match(p, text) for p in patterns)


def _in_scene(rule, scene_id):
    scenes = rule.get('scenes')
    return scenes is None or scene_id is None or scene_id in scenes


def _type_ok(rule, obj):
    wanted = rule.get('type', DEFAULT_TYPE)
    return wanted == 'ANY' or obj.type == wanted


def _props_ok(rule, obj):
    wanted = rule.get('custom_props')
    if not wanted:
        return False
    return all(obj.props.get(key) == str(value) for key, value in wanted.items())


class RoleMap:
    """The result: primary (object -> role), members (role -> objects), material_roles (material -> {role: object count}), never sets, notes."""

    def __init__(self, settings, scene_id):
        self.settings = settings
        self.scene_id = scene_id
        self.primary = {}
        self.also = {}
        self.members = {name: [] for name in settings.roles}
        self.material_roles = {}
        self.never_objects = set()
        self.never_materials = set()
        self.later_objects = set()
        self.unassigned = []
        self.objects = {}
        self.report = Report('roles')

    def role_of(self, name):
        return self.primary.get(name)

    def objects_of(self, role_names):
        """Object names with any of the roles (a name or a family)."""
        wanted = set(self.settings.expand_roles(role_names))
        return [n for n, r in self.primary.items() if r in wanted]

    def materials_of(self, role_names, exclude_never=True):
        wanted = set(self.settings.expand_roles(role_names))
        result = []
        for mat, roles in self.material_roles.items():
            if wanted & set(roles):
                if exclude_never and mat in self.never_materials:
                    continue
                result.append(mat)
        return sorted(result)

    def counts(self):
        return {role: len(objs) for role, objs in self.members.items()}

    def role_index(self, role):
        return list(self.settings.roles).index(role) + 1 if role in self.settings.roles else 0


def find(settings, scene_id, objects):
    """Finds the roles of `objects` (a list of ObjDesc) for the scene named scene_id. Returns a RoleMap; map.report holds errors and warnings."""
    result = RoleMap(settings, scene_id)
    roles = settings.roles
    never = settings.never
    never_obj = never.get('objects', [])
    never_mat = never.get('materials', [])
    result.objects = {o.name: o for o in objects}
    for o in objects:
        if _any(never_obj, o.name):
            result.never_objects.add(o.name)
    for o in objects:
        if _any(never.get('own_layer_later', []), o.name):
            result.later_objects.add(o.name)
        for m in o.materials:
            if _any(never_mat, m):
                result.never_materials.add(m)
    # pass 1: name, collection, custom property
    for obj in objects:
        if obj.name in result.never_objects or obj.name in result.later_objects:
            continue
        matched = []
        for role, rule in roles.items():
            if not _in_scene(rule, scene_id) or not _type_ok(rule, obj):
                continue
            hit = _any(rule.get('objects', []), obj.name) or any(_any(rule.get('collections', []), c) for c in obj.collections) or _props_ok(rule, obj)
            if hit:
                matched.append(role)
        if matched:
            result.primary[obj.name] = matched[0]
            if len(matched) > 1:
                result.also[obj.name] = matched[1:]
    # pass 2: material rules for the rest
    for obj in objects:
        if obj.name in result.never_objects or obj.name in result.later_objects or obj.name in result.primary:
            continue
        done = False
        for material in obj.materials:                                  # the first material slot that some role claims decides
            for role, rule in roles.items():
                if not _in_scene(rule, scene_id) or not _type_ok(rule, obj):
                    continue
                if _any(rule.get('materials', []), material):
                    result.primary[obj.name] = role
                    done = True
                    break
            if done:
                break
    for obj in objects:
        role = result.primary.get(obj.name)
        if role:
            result.members[role].append(obj.name)
            for m in obj.materials:
                result.material_roles.setdefault(m, {}).setdefault(role, 0)
                result.material_roles[m][role] += 1
        elif obj.name not in result.never_objects and obj.name not in result.later_objects and obj.type == DEFAULT_TYPE:
            result.unassigned.append(obj.name)
    # warnings: a role that matches nothing in a scene that should have it
    for role, rule in roles.items():
        if _in_scene(rule, scene_id) and not result.members[role]:
            result.report.warn(f'role {role!r} matches no object in scene {scene_id!r}')
    for key in ('objects', 'materials'):
        names = [o.name for o in objects] if key == 'objects' else sorted({m for o in objects for m in o.materials})
        for pattern in never.get(key, []):
            if not any(re.match(pattern, n) for n in names):
                result.report.warn(f'never.{key}: the pattern {pattern!r} matches nothing')
    return result


def check_matches(settings, scene_id, objects):
    """Pattern by pattern: which regexes of the set's roles match nothing in these objects (warnings). Returns a Report."""
    report = Report('patterns')
    names = [o.name for o in objects]
    collections = sorted({c for o in objects for c in o.collections})
    materials = sorted({m for o in objects for m in o.materials})
    for role, rule in settings.roles.items():
        if not _in_scene(rule, scene_id):
            continue
        for key, pool in (('objects', names), ('collections', collections), ('materials', materials)):
            for pattern in rule.get(key, []):
                if not any(re.match(pattern, n) for n in pool):
                    report.warn(f'role {role!r}: {key} pattern {pattern!r} matches nothing in scene {scene_id!r}')
    return report


def two_roles_check(role_map):
    """Rule for a clean set file: no object may be in two roles. Objects whose name matches two roles are listed (the first one wins, but the set file should be tightened)."""
    return {name: [role_map.primary[name]] + others for name, others in role_map.also.items()}
