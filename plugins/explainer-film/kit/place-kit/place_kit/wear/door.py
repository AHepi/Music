"""What this does: THE ONE DOOR for wear. age_place puts the nine wear layers into the materials of a place by role, in their fixed order, with amounts from the look (kept,
lived_in, neglected, derelict), the state (dry, damp, wet) and the role (a road gets more dirt, a wall less), and writes on every object the property pk_<layer>_amount for each
layer in its materials (an Attribute node on an object without the property reads 0 in every renderer, so a layer would silently do nothing: the audit checks these). It returns a
Wear handle with the master controls: set_master (one number that scales everything; 0 gives exactly the picture without any wear), set_layer_master, set_dials, layer_off and
layer_on (take a layer out of every chain and put it back), set_state, report and remove (everything off, every material as it was).
Layers a role does not need (rust on wood) are not put in; a layer the settings switch off with a reason (an 'off' entry) is not put in either and the audit shows it as KNOWN.
set_picture_size(camera, height_pixels) tells every layer how big one picture dot is in metres at that camera, so marks are sized in picture dots (a crack is never thinner
than three dots). It needs Blender (bpy).
A concrete example: wear = age_place(settings, look='neglected', state='damp'); wear.set_master(0.0) leaves the picture exactly as before; wear.set_state('wet') makes it wetter.
"""
import math

import bpy

from .. import names, roles as roles_module, run_record, scene_read, settings_file
from . import chain, dials as dials_module, hook, masks, plan_group, seed as seed_module


class Wear:
    """What age_place did, with the controls (see the note at the top)."""

    def __init__(self, settings, look_id, state):
        self.settings = settings
        self.look_id = look_id
        self.state = state
        self.master = 1.0
        self.layer_masters = {}
        self.layers_off = set()
        self.materials = {}             # material name -> list of layers wanted there
        self.dials = {}                 # material name -> {layer: {dial: value}}
        self.skipped = {}               # material name -> reason
        self.dot_metres = None

    # ---- the chain, rebuilt from the lists
    def rebuild(self, material_names=None):
        plan = masks.load_plan_masks()
        for name in material_names or list(self.materials):
            material = bpy.data.materials.get(name)
            if material is None:
                continue
            wanted = [k for k in self.materials[name] if k not in self.layers_off]
            inserted, reason = chain.insert_layers(material, wanted, self.dials.get(name, {}), plan, master=self.master, layer_masters=self.layer_masters, dot_metres=self.dot_metres)
            if reason:
                self.skipped[name] = reason

    def set_master(self, amount):
        """One number that scales every layer's amount (1 = the look as written, 0 = exactly nothing)."""
        self.master = float(amount)
        self._push_amounts()
        run_record.write(wear_master=self.master)

    def set_layer_master(self, layer, amount):
        self.layer_masters[layer] = float(amount)
        self._push_amounts()

    def _push_amounts(self):
        for name in self.materials:
            material = bpy.data.materials.get(name)
            for node in chain.layer_nodes(material) if material is not None else []:
                key = node[hook.TAG]
                node.inputs['Amount'].default_value = self.master * self.layer_masters.get(key, 1.0) * float(self.dials.get(name, {}).get(key, {}).get('amount', 1.0))

    def set_dials(self, layer, **values):
        """Changes dials of a layer that is already in (by dial name; an unknown name raises KeyError)."""
        table, _ = dials_module.table_defaults(layer)
        for dial, value in values.items():
            if dial not in table:
                raise KeyError(f'the layer "{layer}" has no dial "{dial}" (its dials: {", ".join(table)})')
        for name in self.materials:
            material = bpy.data.materials.get(name)
            for node in chain.layer_nodes(material, layer) if material is not None else []:
                for dial, value in values.items():
                    socket = node.inputs.get(dials_module.socket_name(dial))
                    if socket is not None and dial not in ('amount', 'seed'):
                        socket.default_value = float(value)
            self.dials.setdefault(name, {}).setdefault(layer, {}).update(values)

    def layer_off(self, layer):
        """Takes the layer out of every chain (the same picture as amount 0, quicker). The settings are kept."""
        self.layers_off.add(layer)
        self.rebuild([n for n, layers in self.materials.items() if layer in layers])

    def layer_on(self, layer):
        self.layers_off.discard(layer)
        self.rebuild([n for n, layers in self.materials.items() if layer in layers])

    def set_state(self, state):
        """dry, damp or wet: rewrites the wetness amount on every object (the layer stays in; at dry its amount is 0)."""
        if state not in names.STATES:
            raise ValueError(f'the state "{state}" is not one of {", ".join(names.STATES)}')
        self.state = state
        write_amounts(self.settings, self.look_id, state, self.layers_off, only_layers=['wetness'])
        run_record.write(state=state)

    def report(self):
        layers = sorted({k for ls in self.materials.values() for k in ls if k not in self.layers_off}, key=names.LAYER_ORDER.index)
        return {'look': self.look_id, 'state': self.state, 'master': self.master, 'layers_in': layers, 'materials': len(self.materials), 'skipped': dict(self.skipped),
                'layers_off': sorted(self.layers_off), 'dot_metres': self.dot_metres,
                'chains': {name: chain.chain_keys(bpy.data.materials[name]) for name in list(self.materials)[:20] if name in bpy.data.materials}}

    def remove(self):
        """Everything off: every material back as it was, the per-object amounts gone."""
        for name in list(self.materials):
            material = bpy.data.materials.get(name)
            if material is not None:
                hook.restore_base(material)
        for obj in bpy.context.scene.objects:
            for layer in names.LAYER_ORDER:
                key = names.layer_amount_name(layer)
                if key in obj.keys():
                    del obj[key]
        return True


def object_layers(settings, role, look_override, rules, table):
    """The layers a role gets (in order), with their amount multipliers: from the role's requirements, minus layers the settings switch off, minus layers whose role multiplier is 0."""
    req = roles_module.requirements(role, table, rules)
    wanted = set(req['required']) | set(req['wanted'])
    spec = table['roles'].get(role, {})
    result = {}
    for layer in names.LAYER_ORDER:
        if layer not in wanted:
            continue
        if roles_module.off_entries_for(role, layer, rules):
            continue
        multiplier = float(spec.get('dials', {}).get(layer, 1.0))
        if multiplier <= 0.0:
            continue
        result[layer] = multiplier
    return result


def write_amounts(settings, look_override, state, layers_off, only_layers=None, owner=None):
    """Writes pk_<layer>_amount on every object for each layer in its materials. Returns how many numbers were written."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    count = 0
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    for obj in objects:
        info = tagged[obj.name]
        if info['role'] is None or roles_module.is_never(info['role']):
            continue
        if owner is not None and obj.get(names.OWNER) != owner and not (obj.get(names.ROLE) or '').startswith('ground.'):
            continue
        best = {}
        for slot_role in set(info['slot_roles']):
            if roles_module.is_never(slot_role):
                continue
            look_id = look_override or settings.look_for_role(slot_role)
            look_data = settings_file.look(look_id)
            for layer, multiplier in object_layers(settings, slot_role, look_override, rules, table).items():
                if only_layers and layer not in only_layers:
                    continue
                if layer in layers_off:
                    continue
                best[layer] = max(best.get(layer, 0.0), dials_module.layer_amount(layer, look_data, state, multiplier))
        for layer, value in best.items():
            obj[names.layer_amount_name(layer)] = float(value)
            count += 1
    return count


def age_place(settings, look=None, state=None, owner=None, layers=None, layers_off=None, master=None):
    """Puts the wear layers into the materials of the place (see the note at the top). Returns the Wear handle."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    look_id = look or settings.look_id
    state = state or settings.state
    if look:
        settings.data['look'] = look
    if state:
        settings.data['state'] = state
    plan = masks.load_plan_masks()
    if plan is None:
        plan, record = masks.build_plan_masks(settings, quick=bool(run_record.read().get('quick')), only_owner=owner)
        masks.write_plan_images(plan)
        masks.forget_loaded()
        run_record.write(mask=record, masks_from=record['source'])
    plan_group.build_plan_group()
    wear = Wear(settings, look_id, state)
    wear.layers_off = set(layers_off or [])
    wanted_filter = set(layers) if layers else None
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    settings_dials = settings.get('dials') or {}
    for obj in objects:
        info = tagged[obj.name]
        if info['role'] is None or roles_module.is_never(info['role']):
            continue
        if owner is not None and obj.get(names.OWNER) != owner and not (obj.get(names.ROLE) or '').startswith('ground.'):
            continue
        slot_materials = [s.material for s in obj.material_slots if s.material is not None]
        for index, material in enumerate(slot_materials):
            slot_role = info['slot_roles'][index] if index < len(info['slot_roles']) else info['role']
            if roles_module.is_never(slot_role):
                continue
            look_data = settings_file.look(look or settings.look_for_role(slot_role))
            klass = roles_module.role_class(slot_role)
            for layer in object_layers(settings, slot_role, look, rules, table):
                if wanted_filter is not None and layer not in wanted_filter:
                    continue
                wear.materials.setdefault(material.name, [])
                if layer not in wear.materials[material.name]:
                    wear.materials[material.name].append(layer)
                wear.dials.setdefault(material.name, {})[layer] = dials_module.dial_values(layer, klass, look_data, settings_dials)
    seed_module.write_object_values([o for o in objects if tagged[o.name]['role'] and not roles_module.is_never(tagged[o.name]['role'])])
    write_amounts(settings, look, state, wear.layers_off, owner=owner)
    wear.rebuild()
    if master is not None:
        wear.set_master(master)
    picture = settings.picture
    if picture.get('camera') and picture.get('height_pixels'):
        set_picture_size(picture['camera'], picture['height_pixels'], wear)
    run_record.write(look=look_id, state=state, wear_layers=sorted({k for ls in wear.materials.values() for k in ls}))
    return wear


def metres_per_dot(camera, height_pixels):
    """How many metres one picture dot covers at the distance of the middle of the place, for this camera and picture height."""
    objects = scene_read.mesh_objects(only_visible=True)
    lows, highs = [], []
    for obj in objects:
        low, high = scene_read.world_bounds(obj)
        lows.append(low)
        highs.append(high)
    if not lows:
        return 0.01
    import numpy as np
    centre = (np.min(lows, axis=0) + np.max(highs, axis=0)) / 2
    distance = float(np.linalg.norm(np.array(camera.matrix_world.translation) - centre))
    sensor = camera.data.sensor_height if camera.data.sensor_fit == 'VERTICAL' else camera.data.sensor_width * bpy.context.scene.render.resolution_y / max(bpy.context.scene.render.resolution_x, 1)
    fov = 2.0 * math.atan((sensor / 2.0) / camera.data.lens)
    return max(2.0 * distance * math.tan(fov / 2.0) / float(height_pixels), 0.0005)


def set_picture_size(camera_name, height_pixels, wear=None):
    """Tells every layer how big one picture dot is in metres at that camera (see the note at the top). Returns the metres per dot."""
    camera = bpy.data.objects.get(camera_name) if isinstance(camera_name, str) else camera_name
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(f'there is no camera called "{camera_name}" to size the picture dots from')
    dot = metres_per_dot(camera, height_pixels)
    for material in bpy.data.materials:
        for node in chain.layer_nodes(material):
            node.inputs['Dot Metres'].default_value = dot
    if wear is not None:
        wear.dot_metres = dot
    run_record.write(picture={'camera': camera.name, 'height_pixels': int(height_pixels), 'set': True, 'dot_metres': dot})
    return dot
