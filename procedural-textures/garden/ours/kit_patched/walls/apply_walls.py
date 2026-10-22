# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE WALLS LAYERS go into a scene through the kit's own hook and chain; this file is only the list and a few conveniences. Nothing here splices a material.
#     from walls import apply_walls
#     apply_walls.register(kit)                 # the harness does this by itself (harness/layers.py finds walls.apply_walls); safe to call twice
#     apply_walls.apply(kit, look='sooty_1926')  # puts every walls layer that exists into the materials of its roles, dial values from the look (kit.apply with the right order)
#     apply_walls.set_dials(kit, 'soot', film_mult=0.9)
#     apply_walls.show_mask(kit, 'soot.washed')  # one named PART of a layer in plain light; also kit.show_mask('soot.washed'); 'layer:soot' is the layer's own Mask;
#                                                # any other name is a bus mask (kit.show_mask as before)
#     apply_walls.remove(kit)                    # the walls layers out (kit.remove(layer) for each; twice is harmless)
# The layers and their slots (plan section 5.1): soot, runoff, foot, steps, paint in slot A (before the water layer); wallcracks in B (after water and joints, dull); wallgrowth in C
# (painted growth, after the cracks). Which roles each goes on is the SET's `apply` block; a layer whose block names no role simply goes into no material (a garden set has no doorsteps).
# Per-object values: besides the kit's own, the walls layers read `wk_walls_class` (0 wall, 1 chimney stack, 2 roof), written here from the role's own name when a layer goes in.
import importlib

from apply import chain as chain_module  # noqa: F401  (documents the dependency: slots come from the kit)

from . import dials_walls, walls_common

LAYER_TABLE = [('soot', 'soot', 'A'), ('runoff', 'runoff', 'A'), ('foot', 'foot', 'A'), ('steps', 'steps', 'A'), ('paint', 'paint', 'A'), ('wallcracks', 'wallcracks', 'B'),
               ('wallgrowth', 'wallgrowth', 'C')]
_PATCHED = {}


def available():
    """[(key, module, slot)] of the layers whose module exists."""
    found = []
    for key, module_name, slot in LAYER_TABLE:
        full = f'{__package__}.{module_name}'
        try:
            module = importlib.import_module(full)
        except ModuleNotFoundError as error:
            if error.name == full:              # the layer's own file does not exist yet: left out (any other missing module is a real error and is raised)
                continue
            raise
        found.append((key, module, slot))
    return found


def keys():
    return [k for k, _, _ in available()]


def _builder(module, kit=None):
    return lambda key: module.build(key)


def register(kit):
    """Registers every walls layer that exists with the kit (their slots as above), adds their finer dials to the dial table, and installs the small service that writes the
    object classes and the debug views of named parts. Safe to call twice."""
    dials_walls.register_all()
    for key, module, slot in available():
        if key not in kit.registry:
            kit.register_layer(key, _builder(module, kit), slot=slot)
    if _class_service not in kit.services:
        kit.services.append(_class_service)
    _patch_views(kit)
    _patch_materials(kit)
    return keys()


def apply(kit, look=None, layers=None, overrides=None):
    """Puts the walls layers in (the order above: slot A layers in list order). Returns {layer: [materials]}."""
    register(kit)
    wanted = [k for k in (layers or keys()) if k in kit.registry]
    return kit.apply(look=look, layers=wanted, overrides=overrides)


def remove(kit, layers=None):
    for key in (layers or keys()):
        kit.remove(key)


def set_dials(kit, layer, **values):
    kit.set_dials(layer, **values)


# ----------------------------------------------------------------------------------------------------------------------------- object classes
def role_class(role_name):
    """0 wall, 1 chimney stack, 2 roof, from the role's own name (the kit's role vocabulary: 'chimney', 'roof.*')."""
    if not role_name:
        return 0.0
    if role_name == 'chimney' or role_name.startswith('chimney'):
        return 1.0
    if role_name == 'roof' or role_name.startswith('roof'):
        return 2.0
    return 0.0


def write_classes(kit):
    import bpy
    count = 0
    for obj in bpy.context.scene.objects:
        if obj.type in ('MESH', 'CURVE', 'EMPTY', 'SURFACE', 'FONT', 'META'):
            obj[walls_common.OBJECT_CLASS_ATTR] = role_class(kit.role_map.primary.get(obj.name))
            count += 1
    kit._walls_classes_written = True
    return count


def _class_service(kit, chain, node, key):
    """Run by the kit for every layer node it puts in: the first time after a prepare, writes the object classes (kit.remove() clears every wk_ value)."""
    if key not in keys():
        return
    import bpy
    sample = next((o for o in bpy.context.scene.objects if o.type == 'MESH'), None)
    if not getattr(kit, '_walls_classes_written', False) or (sample is not None and walls_common.OBJECT_CLASS_ATTR not in sample.keys()):
        write_classes(kit)


# ----------------------------------------------------------------------------------------------------------------------------- debug views
def part_socket_name(part):
    return 'Part ' + part.replace('_', ' ').title()


def show_part(kit, layer, part, raw=True):
    """One named part of a layer (the layer's 'Part <name>' output) as grey light on every material that has the layer; every other material black. Returns undo()."""
    import bpy
    from masks import debug
    scene = bpy.context.scene
    keep = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma)
    if raw:
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = 'Raw', 'None', 0.0, 1.0
    from apply import hook
    saved = []
    wanted = part_socket_name(part)
    for name in kit.hookable():
        chain = kit.chain_for(name)
        if chain is None:
            continue
        tree = chain.tree
        output = hook.active_output(tree)
        node = chain.node(layer)
        socket = node.outputs[wanted] if node is not None and wanted in node.outputs else None
        saved.append(debug._emit(tree, output, socket, socket, socket))
    saved += debug._blackout(kit, set(kit.hookable()) - set(kit.skipped))

    def undo():
        debug._undo(saved)
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = keep
    return undo


def show_mask(kit, name, **options):
    """kit.show_mask that also knows 'layer.part' (for example 'soot.washed') and 'layer:<key>'. Anything else is a bus mask."""
    kit.hide_mask()
    if name.startswith('layer:'):
        from masks import debug
        kit.shown_mask = debug.show_layer(kit, name.split(':', 1)[1])
    elif '.' in name and name.split('.', 1)[0] in keys():
        layer, part = name.split('.', 1)
        kit.shown_mask = show_part(kit, layer, part)
    else:
        kit.shown_mask = kit._orig_show_mask(name, **options) if hasattr(kit, '_orig_show_mask') else None
    return kit.shown_mask


def _patch_views(kit):
    """Makes kit.show_mask understand named parts (on this kit only), and lets the runner's 'layer:<key>.<part>' view show a part (a wrapper round masks.debug.show_layer that
    passes everything it does not know on)."""
    from masks import debug
    if not hasattr(kit, '_orig_show_mask'):
        kit._orig_show_mask = kit.show_mask

        def wrapped(name, **options):
            if name.startswith('layer:') or ('.' in name and name.split('.', 1)[0] in keys()):
                return show_mask(kit, name, **options)
            return kit._orig_show_mask(name, **options)
        kit.show_mask = wrapped
    if 'show_layer' not in _PATCHED:
        original = debug.show_layer
        _PATCHED['show_layer'] = original

        def show_layer(kit_, key):
            if '.' in key and key.split('.', 1)[0] in keys():
                layer, part = key.split('.', 1)
                return show_part(kit_, layer, part, raw=False)
            return original(kit_, key)
        debug.show_layer = show_layer


# ----------------------------------------------------------------------------------------------------------------------------- copies of materials
def _patch_materials(kit):
    """Kit.materials_for(layer) lists the materials of the layer's roles as they were when the set was read. The water layer's script then makes COPIES of the wall materials
    (one per door layout) and gives the wall objects the copies, so a layer put in afterwards would go into the originals nobody uses. This wrapper (on this kit only; the kit's
    own file is not changed, see REQUESTS.md) adds every material that is a copy of a listed one and that the kit can give a chain (the kit knows copies by their name's start)."""
    if getattr(kit, '_walls_orig_materials_for', None) is not None:
        return
    import bpy
    kit._walls_orig_materials_for = kit.materials_for

    def materials_for(key):
        names = list(kit._walls_orig_materials_for(key))
        if kit.registry.get(key) is not None and kit.registry[key].roles == 'all':
            return names
        have = set(names)
        for material in bpy.data.materials:
            if material.node_tree is None or material.users == 0 or material.name in have or material.name in kit.skipped:
                continue
            if any(material.name.startswith(base) and material.name != base for base in names):
                if kit.chain_for(material.name) is not None:
                    names.append(material.name)
                    have.add(material.name)
        return names
    kit.materials_for = materials_for
