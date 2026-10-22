# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE ONE DOOR INTO THE WEATHERING KIT. Run it inside Blender with a scene open (the scene is changed in memory only, never saved):
#
#     import sys; sys.path.insert(0, '<kit folder>')
#     import apply_weathering as aw
#     w = aw.apply('<set id>', '<look id>', state='wet')   # the set's settings file (a set id from sets/ or a path), the look (a preset id from presets/ or a path), the picture state
#     w = aw.apply('<another set id>', '<another look id>')                         # another place, the same call
#     w.set_master(0.8)                          # every kit layer's master dial at once (0 = nothing, 1 = as the look says)
#     w.set_layer_master('soot', 0.5)            # one layer's master dial (any layer key: soot runoff foot steps wallcracks wallgrowth paint dirt groundcracks groundmoss iron growth)
#     w.set_master_of('joints', 0.0)             # the earlier layers' own dials too: 'wetness' (0 = dry ground), 'joints', 'rubbish' (the painted litter and the 3D pieces)
#     w.layer_off('growth'); w.layer_on('growth')          # take one layer out of the materials and put it back
#     w.set_dials('soot', film_mult=0.4)          # any dial of a layer that is on (names are in apply/dial_table.json and in the recipe note)
#     w.set_state(0.85, 0.5)                      # how wet the set is: wetness, puddles (the water layer, the litter pieces and the plants follow)
#     w.camera(cam_object, plate_height=<dots>)    # tell the layers the size of one plate dot for this camera (the harness does this for every picture; do it before your own render)
#     w.report()                                 # what is in which material, what was skipped, which dials are off the look
#     w.remove()   or   aw.remove()              # EVERYTHING off again, every material exactly as it was
#
# What apply() does, in this order (plan section 5.4):
#   1. reads the set's settings file and the look (changes nothing); finds the roles in the open scene; attaches the mask pack made for this scene file
#   2. registers the three builders' layers (walls, ground, growth) and their finer dials, then checks the look against them
#   3. writes the per-object values and takes a snapshot of every material (still no picture change)
#   4. the EARLIER layers, if the set has them (the set file's `legacy` block; a set that has none puts on none): WETNESS, then JOINTS, then RUBBISH, each by its own pinned
#      script (harness/legacy_stack.py), registered as stages of every material's chain
#   5. the kit's layers, each into the materials of its roles from the set's `apply` block, in the slot the chain gives it: A (before the water), B (after water and joints),
#      C (after B), and RUBBISH last; growth is separate 3D pieces on a hidden helper object
#   6. the picture state (wet, puddles)
# Nothing in here names a place: which layer goes on which object, and every number that belongs to one place, is in sets/<id>.json; every look (a sooty 1926 coal town,
# a mossy garden) is a file of dial values in presets/<id>.json. A new set is a new settings file (see "15 Recipe - weathering kit ... how it is made.md", section "Adding a new set").
# To draw plates with it (on the rented machine) use harness/run_testset.py (or a set's own wrapper).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import bpy  # noqa: E402

from apply import kit as kit_module, settings as settings_module  # noqa: E402

EARLIER = ('wetness', 'joints', 'rubbish')
_ACTIVE = []


class DataSnapshot:
    """What the scene held before anything was put on: the name of every material and which material sits in every mesh slot. The earlier water layer makes a COPY of each wall
    material per door layout and hands the copies to the meshes; the kit restores every material's graph but cannot know that, so remove() uses this to give the meshes their own
    materials back and to delete the copies, and deletes the kit's own leftovers (node groups and pictures whose names start with WK, with no user), so that apply() and remove() can
    be repeated without the scene growing. It deliberately leaves the earlier layers' own pieces (their meshes, materials and node groups) alone: their scripts keep module-level
    references to them and a deleted block would crash the next apply."""

    def __init__(self):
        self.materials = set(bpy.data.materials.keys())
        self.slots = {mesh.name: [m.name if m is not None else None for m in mesh.materials] for mesh in bpy.data.meshes}

    def mark_applied(self):
        """Called when apply() is done (kept so a later change can tell what apply() made from what the person made afterwards)."""
        self.after = set(bpy.data.materials.keys())

    def restore(self):
        """Returns {what: how many data blocks were deleted}."""
        for mesh in bpy.data.meshes:
            before = self.slots.get(mesh.name)
            if before is None:
                continue
            for index, name in enumerate(before):
                if index < len(mesh.materials) and name is not None and (mesh.materials[index] is None or mesh.materials[index].name != name):
                    original = bpy.data.materials.get(name)
                    if original is not None:
                        mesh.materials[index] = original
        deleted = dict(materials=0, node_groups=0, images=0)
        for material in list(bpy.data.materials):
            if material.name not in self.materials and material.users == 0:
                bpy.data.materials.remove(material)
                deleted['materials'] += 1
        for kind in ('node_groups', 'images'):
            collection = getattr(bpy.data, kind)
            while True:                                           # a group used only by another group becomes free when that one goes: go round until nothing more is free
                free = [item for item in collection if item.name.startswith('WK') and item.users == 0]
                if not free:
                    break
                for item in free:
                    collection.remove(item)
                    deleted[kind] += 1
        return deleted


def _kit_layers(kit):
    return [key for key in kit.registry if not key.startswith('template_')]


class Weathering:
    """What apply() returns: the kit, the earlier layers' stack, and the dials in one place."""

    def __init__(self, kit, stack, bus_attached, problems):
        self.kit = kit
        self.stack = stack
        self.bus_attached = bus_attached
        self.problems = problems                 # {what: text}: a builder that failed to register, a look dial that no layer knows ...
        self.applied = {}                        # {layer: [materials]}
        self.state = (0.0, 0.0)
        self.full_state = (0.0, 0.0)
        self.removed = False
        self.snapshot = None
        self.cleaned = {}

    # ---------------------------------------------------------------- dials
    @property
    def layers(self):
        return [key for key in self.kit.active]

    def set_master(self, amount):
        """The master dial of the whole kit (every kit layer's amount is multiplied by it). 0 = the kit's layers do nothing."""
        self.kit.set_master(amount)

    def set_layer_master(self, layer, amount):
        self.kit.set_dials(layer, amount=float(amount))

    def set_master_of(self, name, amount):
        """One master dial by name: a kit layer's key, or one of the earlier layers: 'wetness' (0 = dry), 'joints' (strength), 'rubbish' (amount of the painted litter and the pieces)."""
        if name in EARLIER:
            if not self.stack or not self.stack.present():
                raise KeyError(f'this set has no earlier layer {name!r}')
            if name == 'wetness':
                wetness, puddles = self.full_state
                self.set_state(wetness * float(amount), puddles * float(amount), _scaled=True)
            elif name == 'joints':
                self.stack.joints_dials(strength=float(amount))
            else:
                self.stack.rubbish_dials(amount=float(amount) * self.stack.piece_default_dials.get('amount', 1.0))
                self.stack.pieces(amount > 0)
        else:
            self.set_layer_master(name, amount)

    def set_dials(self, layer, **values):
        self.kit.set_dials(layer, **values)

    def layer_off(self, layer):
        self.kit.layer_off(layer)

    def layer_on(self, layer):
        self.kit.layer_on(layer)

    def set_state(self, wetness, puddles, _scaled=False):
        """How wet the set is. (The last state set is remembered as the 'full' state that set_master_of('wetness', x) scales.)"""
        self.state = (float(wetness), float(puddles))
        if not _scaled:
            self.full_state = self.state
        self.kit.set_state(wetness, puddles)

    def camera(self, camera=None, plate_height=None, painter_scale=None):
        """Tells the layers how large one plate dot is for this camera (marks are sized in plate dots). camera: an object (default the scene's camera)."""
        from harness import cameras
        from masks import scale as scale_module
        camera = camera or bpy.context.scene.camera
        bpy.context.scene.camera = camera
        plate = self.kit.settings.get('plate') or {}
        height = plate_height or plate['size'][1]
        widen = scale_module.painter_widen(painter_scale or plate.get('painter_scale', 0.45))
        scale_module.set_scale(self.kit, cameras.dot_angle(camera, height), widen)

    def show_mask(self, name, **options):
        return self.kit.show_mask(name, **options)

    def hide_mask(self):
        self.kit.hide_mask()

    # ---------------------------------------------------------------- reporting
    def report(self):
        info = self.kit.report()
        info['problems'] = dict(self.problems)
        info['earlier_layers'] = bool(self.stack and self.stack.applied)
        info['mask_pack'] = self.bus_attached
        info['pieces'] = self.stack.piece_count() if self.stack and self.stack.applied else 0
        return info

    # ---------------------------------------------------------------- off
    def remove(self):
        """Everything off: every material back as its snapshot says, the earlier layers' nodes and pieces gone, the per-object values cleared."""
        if self.removed:
            return
        self.kit.remove()
        if self.stack is not None:
            self.stack.reset()
        if self.snapshot is not None:
            self.cleaned = self.snapshot.restore()
        self.removed = True
        if self in _ACTIVE:
            _ACTIVE.remove(self)


def apply(set_settings, look=None, scene_id=None, layers=None, dials=None, master=None, earlier=True, state='dry', pieces=True, strict=True, **layer_dials):
    """Puts the weathering on the open scene. See the header.
    set_settings: a set id (a file in sets/) or the path of a settings file. look: a preset id or path (default: the set's own default look).
    scene_id: which of the set's scenes this is (default: guessed from the open file). layers: a list of layer keys (default: every layer of the kit).
    dials: {layer: {dial: value}} on top of the look (a layer's dials may also be given as keyword arguments: apply(set, look, soot={'film_mult': 0.4}, growth={'amount': 0}). master: the master dial of the whole kit (default 1). earlier: put the set's earlier layers (water, joints, litter) on first.
    state: 'dry', 'wet', 'heavy', 'today'-less names as in the harness, or (wetness, puddles). pieces: the separate 3D litter pieces on or off."""
    if _ACTIVE:
        raise RuntimeError('weathering is already on in this Blender session: call remove() first')
    from harness import layers as layers_module, legacy_stack
    from masks import bus as bus_module

    dials = {**(dials or {}), **layer_dials}
    snapshot = DataSnapshot()
    kit = kit_module.Kit.load(set_settings, scene_id=scene_id, look=look, strict=strict)
    problems = {}
    attached = False
    try:
        bus_module.attach(kit)
        attached = True
    except (OSError, KeyError, FileNotFoundError) as error:
        problems['mask pack'] = f'not attached ({error}): layers that read the bus get their defaults'
    found, errors = layers_module.register_builders(kit)
    for module, text in errors.items():
        problems[module] = text
    # the extra dials the builders added are known now: check the look again against the full table
    again = settings_module.validate_look(kit.look, kit.settings) if kit.look is not None else None
    if again is not None and not again.ok:
        problems['look'] = str(again)
    kit.prepare()
    stack = legacy_stack.LegacyStack(kit)
    handle = Weathering(kit, stack, attached, problems)
    handle.snapshot = snapshot
    if earlier and stack.present():
        stack.apply(pieces=pieces)
        stack.look('rubbish')
        if not pieces:
            stack.pieces(False)
    wanted = [key for key in (layers if layers is not None else _kit_layers(kit)) if key in kit.registry]
    handle.applied = kit.apply(look=look, layers=wanted, overrides=dials)
    if master is not None:
        kit.set_master(master)
    if state not in (None, 'today'):
        wetness, puddles = _parse_state(state)
        handle.set_state(wetness, puddles)
    snapshot.mark_applied()
    _ACTIVE.append(handle)
    return handle


def _parse_state(state):
    if isinstance(state, (tuple, list)):
        return float(state[0]), float(state[1])
    table = {'dry': (0.0, 0.0), 'wet': (0.85, 0.5), 'heavy': (1.0, 0.8)}
    if state in table:
        return table[state]
    wet, pud = str(state)[1:].split('p')
    return float(wet), float(pud)


def current():
    return _ACTIVE[-1] if _ACTIVE else None


def remove():
    """Takes the weathering off the open scene (everything: kit layers, earlier layers, adapter boxes, per-object values). Twice is harmless."""
    handle = current()
    if handle is not None:
        handle.remove()
    return handle is not None
