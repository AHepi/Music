"""Public Blender-only API. Lengths are metres; angles are radians.

Runtime evaluates in native Geometry Nodes after saving; this Python module is
needed only to create/edit through the validated interface, not to reopen a scene.
The validation contract does not extend to arbitrary edits in Blender's modifier UI.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import math
import json
import bpy
from mathutils import Vector, Quaternion, Euler

ASSET_NAMES = {'roof': 'CT / Complete ceramic roof', 'stone': 'CT / Seated chiseled stone'}
KIND = 'ct_component'
VERSION = '0.1.1'

@dataclass(frozen=True)
class RoofSpec:
    width: float = 4.2
    half_depth: float = 1.45
    rise: float = .75
    columns: int | None = None
    courses: int | None = None
    seed: int = 19
    surface_seed: int = 31

@dataclass(frozen=True)
class StoneSpec:
    length: float = 1.4
    width: float = .9
    height: float = 1.0
    upper_variation: float = .035
    seed: int = 19
    surface_seed: int = 31
    bevel: float = .02

def library_path():
    return Path(__file__).resolve().parent.parent / 'assets' / 'courtyard_components.blend'

def _between(x, lo, hi):
    # Inclusive engineering limits must survive ordinary decimal float roundoff.
    # This admits at most ~1e-12 relative error, not a material range expansion.
    return (x >= lo or math.isclose(x, lo, rel_tol=1e-12, abs_tol=1e-12)) and (x <= hi or math.isclose(x, hi, rel_tol=1e-12, abs_tol=1e-12))

def _number(x, name, lo, hi):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or not _between(x, lo, hi):
        raise ValueError(f'{name} must be finite in [{lo}, {hi}], got {x!r}')
    return float(x)

def _seed(x, name):
    if type(x) is not int or not 0 <= x <= 2**20:
        raise ValueError(f'{name} must be an integer in [0, 1048576]')

def _vec3(value, name):
    try:
        value = tuple(value)
    except TypeError:
        raise ValueError(f'{name} must contain three finite numbers')
    if len(value) != 3:
        raise ValueError(f'{name} must contain three finite numbers')
    for item in value:
        _number(item, name, -1e6, 1e6)
    return value

def validate_roof(spec):
    if not isinstance(spec, RoofSpec):
        raise TypeError('Expected RoofSpec')
    _number(spec.width, 'width', 2, 18)
    _number(spec.half_depth, 'half_depth', .8, 6)
    _number(spec.rise, 'rise', .2 * spec.half_depth, .65 * spec.half_depth)
    _seed(spec.seed, 'seed'); _seed(spec.surface_seed, 'surface_seed')
    columns = math.ceil(spec.width / .28) + 1 if spec.columns is None else spec.columns
    courses = math.ceil(spec.half_depth / .44) + 1 if spec.courses is None else spec.courses
    for name, value in [('columns', columns), ('courses', courses)]:
        if type(value) is not int or not 3 <= value <= 100:
            raise ValueError(f'{name} must be an integer in [3, 100]')
    dx = spec.width / (columns - 1)
    dy = spec.half_depth / (courses - 1)
    if not _between(dx, .20, .29):
        raise ValueError(f'Column center spacing {dx:.9g} m is outside [.20, .29]; use columns=None to choose automatically')
    if not _between(dy, .25, .46):
        raise ValueError(f'Course center spacing {dy:.9g} m is outside [.25, .46]; use courses=None to choose automatically')
    return {'Width': float(spec.width), 'Half Depth': float(spec.half_depth), 'Rise': float(spec.rise),
            'Columns': columns, 'Courses': courses, 'Seed': spec.seed}

def validate_stone(spec):
    if not isinstance(spec, StoneSpec):
        raise TypeError('Expected StoneSpec')
    for key in ('length', 'width', 'height'):
        _number(getattr(spec, key), key, .2, 5)
    if not _between(max(spec.length, spec.width, spec.height) / min(spec.length, spec.width, spec.height), 1, 6):
        raise ValueError('Stone aspect ratio must not exceed 6:1; a slab is a different component')
    _number(spec.upper_variation, 'upper_variation', 0, .06)
    _number(spec.bevel, 'bevel', 0, min(spec.length, spec.width, spec.height) * .08)
    _seed(spec.seed, 'seed'); _seed(spec.surface_seed, 'surface_seed')
    return {'Length': float(spec.length), 'Width': float(spec.width), 'Height': float(spec.height),
            'Upper Profile Variation': float(spec.upper_variation), 'Seed': spec.seed}

def _check_object(obj, kind=None):
    if obj.get(KIND) not in ASSET_NAMES or (kind is not None and obj.get(KIND) != kind):
        raise ValueError('Object is not the requested courtyard_tools component')
    if obj.parent is not None or any(abs(float(s) - 1) > 1e-7 for s in obj.scale):
        raise ValueError('Use an unparented, unit-scale component; resize through its spec, place through set_pose')
    return obj

def _append(kind, collection, asset_path):
    path = Path(asset_path) if asset_path else library_path()
    if not path.is_file():
        raise FileNotFoundError(f'Component asset library missing: {path}')
    name = ASSET_NAMES[kind]
    with bpy.data.libraries.load(str(path), link=False) as (available, requested):
        if name not in available.objects:
            raise ValueError(f'Not a courtyard_tools library; missing {name}')
        requested.objects = [name]
    obj = requested.objects[0]
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.hide_render = False; obj.hide_set(False)
    obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, 0); obj.scale = (1, 1, 1)
    obj[KIND] = kind; obj['ct_version'] = VERSION
    return obj

def _modifier(obj):
    name = 'CT / Shared roof controls' if obj.get(KIND) == 'roof' else 'CT / Anchored stone controls'
    mod = obj.modifiers.get(name)
    if mod is None or mod.type != 'NODES':
        raise ValueError('Component control modifier was removed or renamed')
    return mod

def _write_controls(obj, values):
    mod = _modifier(obj)
    sockets = {s.name: s.identifier for s in mod.node_group.interface.items_tree
               if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
    for name, value in values.items():
        mod[sockets[name]] = value
    obj.update_tag(refresh={'DATA'})

def _walk_groups(group, visited=None):
    visited = set() if visited is None else visited
    if group.as_pointer() in visited:
        return
    visited.add(group.as_pointer())
    yield group
    for node in group.nodes:
        if node.type == 'GROUP' and node.node_tree:
            yield from _walk_groups(node.node_tree, visited)

def _all_materials(obj):
    mats = set(obj.data.materials)
    for mod in obj.modifiers:
        if mod.type != 'NODES':
            continue
        for group in _walk_groups(mod.node_group):
            for node in group.nodes:
                if node.bl_idname == 'GeometryNodeSetMaterial' and node.inputs['Material'].default_value:
                    mats.add(node.inputs['Material'].default_value)
                if node.bl_idname == 'GeometryNodeObjectInfo':
                    source = node.inputs['Object'].default_value
                    if source and source.type == 'MESH':
                        mats.update(source.data.materials)
    return [m for m in mats if m]

def _surface_seed(obj, seed):
    # Library appends have separate ID blocks, so no other roof/stone is mutated.
    for mat in _all_materials(obj):
        mat['ct_surface_seed'] = seed
        for node in mat.node_tree.nodes:
            if node.get('ct_seed_control'):
                node.outputs[0].default_value = seed

def create_roof(name='Ceramic roof', spec=None, *, location=(0,0,0), rotation=(0,0,0), collection=None, asset_path=None):
    spec = RoofSpec() if spec is None else spec
    values = validate_roof(spec)
    _vec3(location, 'location'); _vec3(rotation, 'rotation')
    obj = _append('roof', collection, asset_path)
    obj.name = name
    _write_controls(obj, values); _surface_seed(obj, spec.surface_seed)
    obj['ct_spec'] = json.dumps(asdict(spec), sort_keys=True)
    set_pose(obj, location=location, rotation=rotation)
    return obj

def create_stone(name='Seated stone', spec=None, *, location=(0,0,0), normal=(0,0,1), yaw=0, collection=None, asset_path=None):
    spec = StoneSpec() if spec is None else spec
    values = validate_stone(spec)
    _vec3(location, 'location'); n = Vector(_vec3(normal, 'normal')); _number(yaw, 'yaw', -1e6, 1e6)
    if n.length < 1e-8:
        raise ValueError('normal must be nonzero')
    obj = _append('stone', collection, asset_path)
    obj.name = name
    _write_controls(obj, values); _surface_seed(obj, spec.surface_seed)
    obj.modifiers['CT / Chiseled arris'].width = spec.bevel
    obj['ct_spec'] = json.dumps(asdict(spec), sort_keys=True)
    set_pose(obj, location=location, normal=normal, yaw=yaw)
    return obj

def update_roof(obj, spec):
    _check_object(obj, 'roof'); values = validate_roof(spec)
    _write_controls(obj, values); _surface_seed(obj, spec.surface_seed)
    obj['ct_spec'] = json.dumps(asdict(spec), sort_keys=True)
    return obj

def update_stone(obj, spec):
    _check_object(obj, 'stone'); values = validate_stone(spec)
    _write_controls(obj, values); _surface_seed(obj, spec.surface_seed)
    obj.modifiers['CT / Chiseled arris'].width = spec.bevel
    obj['ct_spec'] = json.dumps(asdict(spec), sort_keys=True)
    return obj

def set_pose(obj, *, location=(0,0,0), rotation=None, normal=None, yaw=0):
    _check_object(obj); loc = _vec3(location, 'location')
    if rotation is not None and normal is not None:
        raise ValueError('Use rotation or normal, not both')
    if rotation is not None:
        rot = Euler(_vec3(rotation, 'rotation'), 'XYZ').to_quaternion()
    elif normal is not None:
        if obj.get(KIND) != 'stone':
            raise ValueError('Support-normal placement is for stones; roof uses Euler rotation')
        n = Vector(_vec3(normal, 'normal'))
        if n.length < 1e-8:
            raise ValueError('normal must be nonzero')
        _number(yaw, 'yaw', -1e6, 1e6)
        rot = Vector((0,0,1)).rotation_difference(n.normalized()) @ Quaternion((0,0,1), yaw)
    else:
        rot = Quaternion()
    obj.location = loc; obj.rotation_mode = 'QUATERNION'; obj.rotation_quaternion = rot
    obj.update_tag(refresh={'OBJECT'})
    return obj

def bind_material(obj, role, material):
    """Replace one explicit role on this appended component only.

    Caller-provided shader coordinates/seeding are caller's responsibility.
    Roles: roof 'ceramic'/'timber', stone 'stone'. No global material replacement.
    """
    _check_object(obj)
    roles = ('ceramic','timber') if obj.get(KIND) == 'roof' else ('stone',)
    if role not in roles or not isinstance(material, bpy.types.Material):
        raise ValueError(f'Expected role in {roles} and a bpy Material')
    replacements = 0
    for i, old in enumerate(obj.data.materials):
        if old and old.get('ct_material_role') == role:
            obj.data.materials[i] = material; replacements += 1
    for mod in obj.modifiers:
        if mod.type != 'NODES':
            continue
        for group in _walk_groups(mod.node_group):
            for node in group.nodes:
                if node.bl_idname == 'GeometryNodeSetMaterial':
                    old = node.inputs['Material'].default_value
                    if old and old.get('ct_material_role') == role:
                        node.inputs['Material'].default_value = material; replacements += 1
                elif node.bl_idname == 'GeometryNodeObjectInfo':
                    source = node.inputs['Object'].default_value
                    if source and source.type == 'MESH':
                        for i, old in enumerate(source.data.materials):
                            if old and old.get('ct_material_role') == role:
                                source.data.materials[i] = material; replacements += 1
    if not replacements:
        raise ValueError(f'No original material remains for role {role!r}')
    obj.update_tag(refresh={'DATA'})
    return replacements

def inspect_component(obj):
    _check_object(obj)
    mod = _modifier(obj)
    return {'name':obj.name, 'kind':obj[KIND], 'version':obj.get('ct_version'),
            'spec':json.loads(obj['ct_spec']), 'controls':{
                s.name:mod.get(s.identifier,s.default_value)
                for s in mod.node_group.interface.items_tree
                if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry'},
            'material_roles':sorted({m.get('ct_material_role','override') for m in _all_materials(obj)}),
            'runtime':'Native Geometry Nodes; no registered add-on or handler'}
