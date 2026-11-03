"""
What this file does: brings the store's materials and parts into a Blender scene, from your own script. Nothing here
decides where anything goes: you say where.

    import sys
    sys.path.insert(0, '/path/to/brief/store/tools')
    import store

    store.names('materials')                                  # every ready material, by name
    store.names('parts')                                      # every ready part
    mat = store.material('SURFACE • brown_mud')               # brought in from materials/Materials.blend, its pictures found on the shelf
    store.use_material(obj, 'SURFACE • brown_mud')            # put a material on an object (every slot)
    tent = store.add_part('bell_tent', location=(2, 8, 0), turn=30, seed=4)   # build a part where you say; returns its root
    store.prepare_for_render(bpy.context.scene)               # just before drawing: every object's real scale and ground height recorded
    store.fit_stone_pictures(bpy.context.scene)                # the street's stone materials: their one big picture stretched over your place

Conventions every part follows: metres; Z up; the part's foot at its origin (it stands on the ground at z = 0); its
front (a door, a muzzle, a lamp's face) towards -Y, which is Blender's front view; turn it with `turn` (degrees about Z).
The surface materials read two numbers per object: its real scale (so a picture is never stretched by an unapplied
scale) and the height of the ground under it (for the mud dial). `add_part` records both; for your own objects call
`use_material` or, once, `prepare_for_render` before drawing.

    python3 store.py --list            (prints what the store holds)
"""

import importlib.util
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.dirname(TOOLS)
BRIEF = os.path.dirname(STORE)
SHELF = os.path.join(BRIEF, 'surfaces')
PARTS_SOURCE = os.path.join(STORE, 'parts', 'src')
MATERIALS_BLEND = os.path.join(STORE, 'materials', 'Materials.blend')

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

_part_modules = {}


# ----------------------------------------------------------------------------------------------- what there is

def names(kind):
    """'materials', 'parts' or 'tools': the names the store holds of that kind."""
    if kind == 'materials':
        with bpy.data.libraries.load(MATERIALS_BLEND, link=False) as (source, _):
            return sorted(source.materials)
    if kind == 'parts':
        return sorted(f[:-3] for f in os.listdir(PARTS_SOURCE) if f.endswith('.py') and not f.startswith('_'))
    if kind == 'tools':
        return sorted(f[:-3] for f in os.listdir(TOOLS) if f.endswith('.py') and not f.startswith('_') and f not in ('store.py', 'card.py', 'catalogue.py'))
    raise ValueError("kind is 'materials', 'parts' or 'tools'")


def part_card(name):
    """The part's own description: what it is, its options, where it came from (its module's CARD)."""
    return dict(getattr(_part_module(name), 'CARD', {}))


# ----------------------------------------------------------------------------------------------- materials

def _shelf_file(basename):
    for root, _, files in os.walk(SHELF):
        if basename in files:
            return os.path.join(root, basename)
    return None


def find_shelf_pictures():
    """Every picture the scene uses that is not where its path says: looked for on the shelf by its file name."""
    fixed = 0
    for image in bpy.data.images:
        if image.source != 'FILE' or image.packed_file is not None or not image.filepath:
            continue
        if os.path.exists(bpy.path.abspath(image.filepath)):
            continue
        found = _shelf_file(os.path.basename(bpy.path.abspath(image.filepath)))
        if found:
            image.filepath = found
            image.reload()
            fixed += 1
    return fixed


def material(name):
    """The named material: already in the scene, or brought in from the store's Materials.blend (once)."""
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    with bpy.data.libraries.load(MATERIALS_BLEND, link=False) as (source, target):
        if name not in source.materials:
            close = [n for n in source.materials if name.lower() in n.lower()][:8]
            raise KeyError('no material %r in the store%s' % (name, ('; did you mean: ' + ', '.join(close)) if close else ''))
        target.materials = [name]
    find_shelf_pictures()
    return bpy.data.materials[name]


def mark(obj, ground=None):
    """Record the object's real scale (and, if given, the ground height under it) for the surface materials."""
    obj['pp_scale'] = tuple(obj.matrix_world.to_scale())
    if ground is not None:
        obj['pp_ground'] = float(ground)


def use_material(obj, name_or_material, ground=None):
    """Put a material on every slot of an object (adding a slot if it has none), and mark the object."""
    mat = material(name_or_material) if isinstance(name_or_material, str) else name_or_material
    if obj.data is not None and hasattr(obj.data, 'materials'):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            for index in range(len(obj.data.materials)):
                obj.data.materials[index] = mat
    mark(obj, ground)
    return mat


def prepare_for_render(scene):
    """Just before drawing: every mesh's real scale recorded (objects scaled after their material was set included)."""
    bpy.context.view_layer.update()
    for obj in scene.objects:
        if obj.type in ('MESH', 'CURVE'):
            obj['pp_scale'] = tuple(obj.matrix_world.to_scale())


def fit_projection(mat, low, high):
    """The street's stone materials project one unique sandstone picture over a box in the world; stretch it over
    the box from low to high (each a 3-number corner). Returns how many picture axes were fitted."""
    if not mat.use_nodes:
        return 0
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    picture_nodes = [n for n in nodes if n.type == 'TEX_IMAGE' and n.name.startswith('Unique world-projected')]
    if not picture_nodes:
        return 0
    combine = next((l.from_node for l in links if l.to_node in picture_nodes and l.from_node.type == 'COMBXYZ'), None)
    if combine is None:
        return 0
    changed = 0
    for link in links:
        if link.to_node == combine and link.from_node.type == 'MATH' and link.from_node.operation == 'MULTIPLY_ADD':
            math_node = link.from_node
            source = [l for l in links if l.to_socket == math_node.inputs[0]]
            if not source or source[0].from_node.type != 'SEPXYZ':
                continue
            axis = 'xyz'.index(source[0].from_socket.name.lower())
            span = max(high[axis] - low[axis], 1.0)
            math_node.inputs[1].default_value = 1.0 / span
            math_node.inputs[2].default_value = -low[axis] / span
            changed += 1
    return changed


def fit_stone_pictures(scene, backdrop_limit=400.0):
    """Stretch every street stone material's picture over the place's own extent (backdrops over 400 m left out)."""
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    bpy.context.view_layer.update()
    for obj in scene.objects:
        if obj.type != 'MESH' or max(obj.dimensions) > backdrop_limit:
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low = Vector(tuple(map(min, low, world)))
            high = Vector(tuple(map(max, high, world)))
    if low.x > high.x:
        return 0
    return sum(fit_projection(m, low, high) for m in bpy.data.materials)


# ----------------------------------------------------------------------------------------------- parts

def _part_module(name):
    if name in _part_modules:
        return _part_modules[name]
    path = os.path.join(PARTS_SOURCE, name + '.py')
    if not os.path.exists(path):
        raise KeyError('no part %r in the store; there are: %s' % (name, ', '.join(names('parts'))))
    spec = importlib.util.spec_from_file_location('store_part_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _part_modules[name] = module
    return module


def add_part(name, location=(0.0, 0.0, 0.0), turn=0.0, scale=1.0, seed=0, collection=None, **options):
    """
    Build the named part and stand it where you say: its foot at `location`, turned `turn` degrees about Z (its front
    faces -Y before turning), `scale` times its real size (leave it at 1 for things people use). `seed` picks its
    variation; `options` are the part's own (see `part_card(name)`). Returns the part's root (an empty); every object
    of the part is its child, in a collection of its own.
    """
    module = _part_module(name)
    scene = bpy.context.scene
    target = collection or scene.collection
    holder = bpy.data.collections.new('%s %d' % (name, len([c for c in bpy.data.collections if c.name.startswith(name + ' ')]) + 1))
    target.children.link(holder)
    made = module.build(holder, seed=seed, **options)
    objects = list(holder.all_objects) if made is None else list(made)
    root = bpy.data.objects.new(holder.name, None)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.5
    holder.objects.link(root)
    for obj in objects:
        if obj is root or obj.parent is not None:
            continue
        obj.parent = root
        obj.matrix_parent_inverse = Matrix.Identity(4)
    root.location = Vector(location)
    root.rotation_euler = (0.0, 0.0, math.radians(turn))
    root.scale = (scale, scale, scale)
    root['store_part'] = name
    root['store_seed'] = seed
    bpy.context.view_layer.update()
    for obj in holder.all_objects:
        if obj.type in ('MESH', 'CURVE'):
            mark(obj, ground=location[2])
    return root


def save_part_file(name, seed=0, **options):
    """Build the part alone in an empty file and save it as parts/<name>.blend (pictures kept as paths to the shelf)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    add_part(name, seed=seed, **options)
    path = os.path.join(STORE, 'parts', name + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=path, relative_remap=True)
    return path


if __name__ == '__main__':
    if '--list' in sys.argv:
        for kind in ('parts', 'tools', 'materials'):
            items = names(kind)
            print('%s (%d): %s' % (kind, len(items), ', '.join(items)))
    else:
        print(__doc__)
