"""What this does (inside Blender): APPLIES one variation to the open, finished scene and puts everything back afterwards, so one card job can draw many variations from one opened scene.
It changes only what the variation names (see keys.py): the strength of wear layers (master and amount.<layer> MULTIPLY the layer nodes' Amount input as the saved scene has it, so 1 is
the saved scene and 2 is twice as strong), a layer's dials (the node's own inputs, set to the variation's value in every material), the state (the wetness amount written on every object) and
the look (every layer's amount written on every object), or runs a script hook. It never saves the scene. saved_values() reads what the saved scene has for the dials a batch varies (lowest
and highest over the materials), so the sheet can show them and the next check before drawing can use them.

Putting back: every value it changes is written down first (which material, which node, which input, what it was; which object property, what it was). restore() writes them back, and
fingerprint() (a short hash of every wear-layer input and every pk_<layer>_amount on every object) says whether the scene is exactly as it was: the worker compares it with the fingerprint
taken before the first variation and REOPENS the scene when they differ, so a reset that did not work can never leak one variation into the next. A script hook can change anything, so after a
hook the worker always reopens.

A concrete example: apply({'set': {'amount.moss_and_algae': 1.6, 'dials.moss_and_algae.cover': 0.9}}) multiplies the Amount of every moss layer node by 1.6 (a node saved at 0.45 becomes
0.72), sets its Cover input to 0.9, and returns a note for any layer that is in no material of the scene (then the setting changed nothing there). It needs Blender (bpy).
"""
import hashlib
import importlib.util
import json
import traceback

import bpy

from .. import names, run_record
from ..wear import chain, dials as dials_module
from . import keys


class HookProblem(Exception):
    """A script hook is missing its apply(variation) function or failed (the variation is reported as failed; the batch goes on)."""


def _plain(value):
    try:
        return [round(float(v), 6) for v in value]
    except TypeError:
        return round(float(value), 6) if isinstance(value, (int, float)) else str(value)


class Applier:
    def __init__(self, settings_path=None):
        self.settings_path = settings_path
        self._settings = None
        self.sockets = []              # (material name, node name, input name, old value): what to write back
        self.props = {}                # object name -> {property name: old value or None when it was not there}
        self.remembered_props = False

    # ------------------------------------------------------------ finding things
    def settings(self):
        if self._settings is None:
            if not self.settings_path:
                raise HookProblem('a variation sets "state" or "look", which need the place settings, and none were given (the variations file\'s "settings", or --settings)')
            from .. import commands
            self._settings = commands.read_settings(self.settings_path)
        return self._settings

    @staticmethod
    def layer_nodes(layer):
        return [(material, node) for material in bpy.data.materials for node in chain.layer_nodes(material, layer)]

    def _set_input(self, material, node, input_name, value, scale=False):
        """Sets one input (scale=True multiplies what is there instead). The old value is written down first, so restore() can put it back."""
        socket = node.inputs.get(input_name)
        if socket is None:
            return False
        self.sockets.append((material.name, node.name, input_name, _plain(socket.default_value)))
        socket.default_value = float(socket.default_value) * float(value) if scale else float(value)
        return True

    def saved_values(self, key_list):
        """{key: [lowest, highest]} over the materials, for every dial key in key_list, as the scene has it NOW (call it before applying anything). A layer in no material gives None."""
        found = {}
        for key in key_list:
            info = keys.describe_key(key)
            if info['kind'] != 'dial':
                continue
            socket_name = 'Seed' if info['dial'] == 'seed' else dials_module.socket_name(info['dial'])
            values = [float(node.inputs[socket_name].default_value) for _, node in self.layer_nodes(info['layer']) if node.inputs.get(socket_name) is not None]
            found[key] = [round(min(values), 6), round(max(values), 6)] if values else None
        return found

    def _remember_props(self):
        if self.remembered_props:
            return
        for obj in bpy.data.objects:
            old = {}
            for layer in names.LAYER_ORDER:
                key = names.layer_amount_name(layer)
                old[key] = float(obj[key]) if key in obj.keys() else None
            if any(v is not None for v in old.values()):
                self.props[obj.name] = old
        self.remembered_props = True

    # ------------------------------------------------------------ the fingerprint
    @staticmethod
    def fingerprint():
        """A short hash of every wear-layer input in every material and every pk_<layer>_amount on every object."""
        parts = []
        for material in sorted(bpy.data.materials, key=lambda m: m.name):
            for node in sorted(chain.layer_nodes(material), key=lambda n: n.name):
                parts.append([material.name, node.name, [[socket.name, _plain(socket.default_value)] for socket in node.inputs if hasattr(socket, 'default_value') and not socket.is_linked]])
        for obj in sorted(bpy.data.objects, key=lambda o: o.name):
            row = [[names.layer_amount_name(layer), _plain(obj[names.layer_amount_name(layer)])] for layer in names.LAYER_ORDER if names.layer_amount_name(layer) in obj.keys()]
            if row:
                parts.append([obj.name, row])
        return hashlib.sha1(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:16]

    # ------------------------------------------------------------ applying
    def apply(self, variation):
        """Applies the variation's settings and script hook. Returns a list of plain notes (what changed nothing, what was clamped)."""
        notes = []
        values = variation.get('set') or {}
        master = values.get('master')
        for layer in names.LAYER_ORDER:
            amount = values.get(f'amount.{layer}')
            if master is None and amount is None:
                continue
            factor = (1.0 if master is None else master) * (1.0 if amount is None else amount)
            found = self.layer_nodes(layer)
            if not found and amount is not None:
                notes.append(f'the layer {layer} is in no material of this scene, so its amount changed nothing')
            for material, node in found:
                self._set_input(material, node, 'Amount', factor, scale=True)
        if master is not None and not any(self.layer_nodes(layer) for layer in names.LAYER_ORDER):
            notes.append('no wear layer is in any material of this scene, so "master" changed nothing (was the scene finished?)')
        for key, value in values.items():
            info = keys.describe_key(key)
            if info['kind'] != 'dial':
                continue
            found = self.layer_nodes(info['layer'])
            if not found:
                notes.append(f'the layer {info["layer"]} is in no material of this scene, so {key} changed nothing')
            socket_name = 'Seed' if info['dial'] == 'seed' else dials_module.socket_name(info['dial'])
            for material, node in found:
                if not self._set_input(material, node, socket_name, value):
                    notes.append(f'the layer node in {material.name} has no input {socket_name}')
                    break
        if 'state' in values or 'look' in values:
            from ..wear import door
            settings = self.settings()
            self._remember_props()
            look = values.get('look')
            state = values.get('state') or run_record.read().get('state') or settings.state
            if look is None:
                written = door.write_amounts(settings, None, state, set(), only_layers=['wetness'])
            else:
                written = door.write_amounts(settings, look, state, set())
            if not written:
                notes.append('state and look wrote no amount on any object (no object has a role that takes wear?)')
        if variation.get('script'):
            self.run_hook(variation)
        return notes

    @staticmethod
    def run_hook(variation):
        spec = importlib.util.spec_from_file_location('pk_variation_hook', variation['script'])
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as problem:   # noqa: BLE001 - a broken hook is a failed variation, not a stopped batch
            raise HookProblem(f'the script hook {variation["script"]} could not be loaded: {problem}')
        if not hasattr(module, 'apply'):
            raise HookProblem(f'the script hook {variation["script"]} has no function apply(variation)')
        try:
            module.apply({'name': variation['name'], 'args': dict(variation.get('args') or {}), 'set': dict(variation.get('set') or {})})
        except Exception as problem:   # noqa: BLE001
            tail = ' | '.join(traceback.format_exc().strip().splitlines()[-3:])
            raise HookProblem(f'the script hook {variation["script"]} stopped with an error: {problem} ({tail})')

    # ------------------------------------------------------------ putting back
    def restore(self):
        """Writes every changed value back. Returns how many were put back."""
        count = 0
        for material_name, node_name, input_name, old in reversed(self.sockets):
            material = bpy.data.materials.get(material_name)
            node = material.node_tree.nodes.get(node_name) if material is not None and material.node_tree else None
            socket = node.inputs.get(input_name) if node is not None else None
            if socket is None:
                continue
            socket.default_value = old
            count += 1
        self.sockets = []
        for obj_name, old in self.props.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                continue
            for key, value in old.items():
                if value is None:
                    if key in obj.keys():
                        del obj[key]
                else:
                    obj[key] = value
                    count += 1
        return count
