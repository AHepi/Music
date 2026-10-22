# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Writes the PER-OBJECT values every layer can read through an Attribute node (type Object; tested: EEVEE and Cycles read an object's custom property equally, a missing
# property reads 0). The kit never edits meshes or material slots; everything per object is a custom property on the object:
#   wk_seed        a number 0..1 that comes from the object's ROUNDED world position (1 cm) and its role, so renamed objects ('.001') and rebuilds do not reshuffle
#   wk_role_id     1, 2, 3 ... = the place of the role in the set's role list (0 = no role)
#   wk_frame_id    which wall sheet the object reads (0 = none); written when a mask pack is loaded (masks/bus.py)
#   wk_zmin, wk_zmax   the object's own height range in world z (iron layers: how far up the object is)
#   wk_<flag>      per-object facts a picture cannot know, from the set's `flags` block ({"stepped": {"attribute": "wk_stepped", "objects": [name prefixes]}})
#   wk_<layer>_amount   1 on objects whose role the layer acts on, 0 on every other object (so a material shared by two kinds of object is only weathered where the set says)
#   wk_<layer>_<dial>   the role's multiplier for a dial the set varies by role (apply.<layer>.role_dials), 1 where the role has none
# Plain hashing here; the writing needs Blender (bpy).
import hashlib

from . import dials


def hash01(*parts):
    """A repeatable number 0..1 from any parts (no Python hash(), which changes from run to run)."""
    text = '|'.join(str(p) for p in parts)
    digest = hashlib.md5(text.encode()).digest()
    return int.from_bytes(digest[:8], 'big') / float(1 << 64)


def object_seed(position, role):
    x, y, z = (round(float(v), 2) for v in position)
    return hash01(x, y, z, role or '')


def flag_attributes(settings):
    """[(attribute name, [object name prefixes])] from settings.flags; entries without an 'attribute' are notes."""
    result = []
    for key, spec in (settings.get('flags') or {}).items():
        if isinstance(spec, dict) and 'attribute' in spec:
            result.append((spec['attribute'], list(spec.get('objects', []))))
    return result


def object_values(settings, role_map, name, position, zrange, layers=None):
    """The dict of custom properties for one object (pure Python; write_object_values puts them on the Blender objects)."""
    role = role_map.primary.get(name)
    values = {'wk_seed': object_seed(position, role), 'wk_role_id': float(role_map.role_index(role)) if role else 0.0,
              'wk_zmin': float(zrange[0]), 'wk_zmax': float(zrange[1])}
    for attribute, prefixes in flag_attributes(settings):
        values[attribute] = 1.0 if any(name.startswith(p) for p in prefixes) else 0.0
    for layer in (layers if layers is not None else settings.layer_keys()):
        acts = role in settings.layer_roles(layer) if role else False
        values[dials.object_attribute_name(layer, 'amount')] = 1.0 if acts else 0.0
        if acts:
            for r, table in dials.role_multipliers(settings, layer).items():
                if r == role:
                    for dial, mult in table.items():
                        values[dials.object_attribute_name(layer, dial)] = max(float(mult), dials.MIN_ROLE_MULT)
            for dial in {d for t in dials.role_multipliers(settings, layer).values() for d in t}:
                values.setdefault(dials.object_attribute_name(layer, dial), 1.0)
    return values


def write_object_values(settings, role_map, scene=None, layers=None, frame_ids=None):
    """Puts the values on every mesh, curve and empty of the Blender scene. Returns the number of objects written."""
    import bpy
    scene = scene or bpy.context.scene
    count = 0
    for obj in scene.objects:
        if obj.type not in ('MESH', 'CURVE', 'EMPTY', 'SURFACE', 'FONT', 'META', 'POINTCLOUD', 'CURVES', 'VOLUME'):
            continue
        matrix = obj.matrix_world
        position = tuple(matrix.translation)
        if obj.type == 'EMPTY' or not getattr(obj, 'bound_box', None):
            zrange = (position[2], position[2])
        else:
            zs = [(matrix @ __import__('mathutils').Vector(c)).z for c in obj.bound_box]
            zrange = (min(zs), max(zs))
        values = object_values(settings, role_map, obj.name, position, zrange, layers)
        if frame_ids and obj.name in frame_ids:
            values['wk_frame_id'] = float(frame_ids[obj.name])
        elif 'wk_frame_id' not in values:
            values['wk_frame_id'] = 0.0
        for key, value in values.items():
            obj[key] = value
        count += 1
    return count


def clear_object_values(scene=None):
    """Takes every wk_ property off the scene's objects (used by Kit.remove)."""
    import bpy
    scene = scene or bpy.context.scene
    for obj in scene.objects:
        for key in [k for k in obj.keys() if k.startswith('wk_')]:
            del obj[key]
