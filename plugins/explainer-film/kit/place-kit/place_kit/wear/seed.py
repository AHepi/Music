"""What this does: writes the PER-OBJECT numbers every material and wear layer reads through an Attribute node (type Object): a random seed that comes from the
object's rounded position and its role (never its name, so a rename or a ".001" does not reshuffle it and a rebuild keeps it), the object's lowest and highest
point in world metres (a wall's foot starts at its own lowest point, not at the ground, because a stone plinth hides the foot), its height, and its box. It
also writes the layer amounts (pk_<layer>_amount) that say how strongly each layer acts on that object: an Attribute node on an object with NO such property
reads 0 in every renderer, so a missing amount silently switches a layer off; writing all of them here, and having the audit check them, is what stops that.
Plain Python (the hash) and Blender (the writing). A concrete example: object_seed((1.2, 3.4, 0.0), 'wall.plaster') is always the same number between 0 and 1.
"""
import hashlib

from .. import names


def hash01(*parts):
    """A repeatable number 0..1 from any parts (not Python's hash(), which changes from run to run)."""
    text = '|'.join(str(p) for p in parts)
    digest = hashlib.md5(text.encode()).digest()
    return int.from_bytes(digest[:8], 'big') / float(1 << 64)


def object_seed(position, role):
    x, y, z = (round(float(v), 2) for v in position)
    return hash01(x, y, z, role or '')


def write_object_values(objects=None):
    """Writes pk_seed, pk_zmin, pk_top_z and pk_height on every given mesh object (default: every mesh in the scene). The seed is kept if the object
    already has one, so a second run changes nothing. Returns how many objects were written."""
    import bpy
    from .. import scene_read
    count = 0
    for obj in objects if objects is not None else [o for o in bpy.context.scene.objects if o.type == 'MESH']:
        low, high = scene_read.world_bounds(obj)
        if names.SEED not in obj.keys():
            obj[names.SEED] = object_seed(obj.matrix_world.translation, obj.get(names.ROLE))
        obj[names.BOTTOM_Z] = float(low[2])
        obj[names.TOP_Z] = float(high[2])
        obj[names.HEIGHT] = float(high[2] - low[2])
        for axis, size in zip('xyz', high - low):
            obj[f'pk_size_{axis}'] = float(size)
        count += 1
    return count


def write_layer_amounts(obj, amounts):
    """amounts: {layer: number}. Writes pk_<layer>_amount for each."""
    for layer, value in amounts.items():
        obj[names.layer_amount_name(layer)] = float(value)


def clear_object_values(objects=None):
    """Takes the kit's per-object numbers off (used by undo): seeds, heights and layer amounts."""
    import bpy
    for obj in objects if objects is not None else list(bpy.context.scene.objects):
        for key in [k for k in obj.keys() if k in (names.SEED, names.BOTTOM_Z, names.TOP_Z, names.HEIGHT, 'pk_size_x', 'pk_size_y', 'pk_size_z') or (k.startswith('pk_') and (k.endswith('_amount')))]:
            del obj[key]
