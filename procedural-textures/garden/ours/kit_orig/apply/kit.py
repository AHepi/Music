# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE KIT: the one object everything else talks to.
#     import sys; sys.path.insert(0, KIT_ROOT); from apply import kit as wk
#     k = wk.Kit.load('<set id>', scene_id='<scene id>')     # reads and checks the set file, finds the roles in the open scene; changes nothing
#     k.prepare()                                                  # writes the per-object values and takes a snapshot of every material; still changes no picture
#     k.register_layer('soot', build_group, slot='A')              # a layer's builder (the builders' apply_*.py do this)
#     k.apply(look='sooty_1926', layers=['soot'])                  # puts the layers into the materials of their roles, dial values from the look
#     k.set_dials('soot', film_mult=0.5);  k.set_master(0.8)       # dials of a layer already in; the master amount multiplies every layer's Amount
#     k.layer_off('soot'); k.layer_on('soot')                      # take a layer out of the chain and put it back (same as Amount 0, faster)
#     k.set_state(0.85, 0.5)                                       # tells every part how wet the scene is (the water layer, rubbish pieces, growth pieces) through state hooks
#     k.show_mask('moss_site')                                     # a checking view: the mask as plain light (masks/debug.py); k.hide_mask()
#     k.report()                                                   # what is in which material, what was skipped and why
#     k.remove()                                                   # EVERYTHING off: every material back as its snapshot says (kit layers, earlier layers, adapter boxes, per-object values)
# The earlier layers (WETNESS, JOINTS, RUBBISH) are put on by their own pinned scripts (harness/legacy_stack.py) and then REGISTERED with register_legacy(); the kit never
# calls their own remove().
# Needs Blender (bpy).
import os
import sys

import bpy

from . import adapters, chain as chain_module, dials, hook, roles as roles_module, seed, settings as settings_module
from .layer_template import socket_name

sys.dont_write_bytecode = True


class LayerSpec:
    def __init__(self, key, builder, slot, roles=None):
        self.key = key
        self.builder = builder              # builder(key) -> node group tree
        self.slot = slot
        self.roles = roles                  # None: the set's apply.<key>.roles; 'all': every hookable material; or a list of role names / families
        self.tree = None


class Kit:
    def __init__(self, settings, scene_id):
        self.settings = settings
        self.scene_id = scene_id
        self.look = None
        self.role_map = None
        self.registry = {}
        self.chains = {}                    # material name -> Chain
        self._snap = {}                     # material name -> (Snapshot, principled name or None, adapter spec, group node name)
        self.skipped = {}                   # material name -> reason
        self.forced = {}                    # material name -> why the policy would have skipped it (prepare(policy=False))
        self.active = {}                    # layer key -> dict(on, values, materials)
        self.master = 1.0
        self.prepared = False
        self.state_hooks = []
        self.services = []                  # callables(kit, chain, node, key) run once for every layer node put in (the bus wires masks and scale by name)
        self.mask_pack = None
        self.validation = None
        self.shown_mask = None
        self.log = []

    # ---------------------------------------------------------------- loading
    @classmethod
    def load(cls, set_ref, scene_id=None, look=None, scene=None, strict=True):
        settings = settings_module.load_set(set_ref)
        validation = settings_module.validate_set(settings, check_files=False)
        validation.extend(dials.validate_role_dials(settings))
        if strict and not validation.ok:
            raise ValueError(str(validation))
        if scene_id is None:
            scene_id = cls.guess_scene_id(settings)
        kit = cls(settings, scene_id)
        kit.validation = validation
        name = look or settings.default_look()
        kit.look = settings_module.load_look(name) if name else None
        if kit.look is not None:
            kit.validation.extend(settings_module.validate_look(kit.look, settings))
        kit.refresh_roles(scene)
        return kit

    @staticmethod
    def guess_scene_id(settings):
        path = os.path.abspath(bpy.data.filepath) if bpy.data.filepath else ''
        for entry in settings.scenes:
            if os.path.abspath(entry['file']) == path:
                return entry['id']
        for entry in settings.scenes:
            if os.path.basename(entry['file']) == os.path.basename(path):
                return entry['id']
        return settings.scenes[0]['id']

    def refresh_roles(self, scene=None):
        objects = roles_module.describe_scene(scene)
        self.role_map = roles_module.find(self.settings, self.scene_id, objects)
        self.validation.extend(self.role_map.report)
        return self.role_map

    # ---------------------------------------------------------------- layers
    def register_layer(self, key, builder, slot='A', roles=None):
        if slot not in settings_module.SLOTS:
            raise ValueError(f'slot {slot!r} is not one of {settings_module.SLOTS}')
        self.registry[key] = LayerSpec(key, builder, slot, roles)
        return self.registry[key]

    def layer_role_names(self, key):
        spec = self.registry.get(key)
        if spec is not None and spec.roles is not None:
            if spec.roles == 'all':
                return list(self.settings.roles)
            return self.settings.expand_roles(spec.roles)
        return self.settings.layer_roles(key)

    # ---------------------------------------------------------------- snapshots and chains
    def prepare(self, layers=None, policy=True):
        """Writes the per-object values and takes a snapshot of every material that has a node tree. Changes no picture. policy=False ignores the never list and the glow rule
        (the hook test uses it to prove the splice works mechanically on every material; the reasons are still listed in self.forced)."""
        if self.role_map is None:
            self.refresh_roles()
        frame_ids = None
        if self.mask_pack is not None:
            frame_ids = self.mask_pack.manifest['frames'].get('frame_of_object', {})
        seed.write_object_values(self.settings, self.role_map, layers=list(set(self.settings.layer_keys()) | set(self.registry)), frame_ids=frame_ids)
        for material in bpy.data.materials:
            if material.node_tree is None or material.users == 0 or material.name in self._snap:
                continue
            reason, principled = hook.classify(material, self.settings, self.role_map if policy else None)
            if not policy and reason == 'glow':
                self.forced[material.name] = reason
                reason = 'ok'
            if not policy and reason in ('ok', 'ok_mixed') and material.name in self.role_map.never_materials:
                self.forced[material.name] = 'never'
            if reason in ('ok', 'ok_mixed'):
                self._snap[material.name] = (hook.Snapshot(material, principled), principled.name, None, None)
            elif reason == 'group':
                spec, node = adapters.match_adapter(material, self.settings)
                if spec is not None:
                    self._snap[material.name] = (hook.Snapshot(material, None), None, spec, node.name)
                else:
                    self.skipped[material.name] = 'group without an adapter'
            else:
                self.skipped[material.name] = reason
        self.prepared = True
        return len(self._snap)

    def chain_for(self, material_name):
        """The material's chain (made on first use: the adapter box is built only now), or None when the material is skipped."""
        chain = self.chains.get(material_name)
        if chain is not None:
            return chain
        entry = self._snap.get(material_name)
        if entry is None:
            return self._chain_of_copy(material_name)
        snapshot, principled_name, adapter_spec, group_name = entry
        material = bpy.data.materials[material_name]
        if principled_name is None:
            box = adapters.apply(material, adapter_spec, material.node_tree.nodes[group_name])
            principled_name = box.name
        principled = material.node_tree.nodes[principled_name]
        chain = chain_module.Chain(material, snapshot, hook.Origin(material, principled, snapshot.plugs if snapshot.principled else None), principled_name)
        self.chains[material_name] = chain
        return chain

    def _chain_of_copy(self, material_name):
        """A material made after prepare() by copying another (the water layer's script copies the wall materials per door layout): its snapshot is the original's."""
        material = bpy.data.materials.get(material_name)
        if material is None or material.node_tree is None:
            return None
        candidates = [n for n in self._snap if material_name.startswith(n) and n != material_name]
        for proto_name in sorted(candidates, key=len, reverse=True):
            snapshot, principled_name, adapter_spec, group_name = self._snap[proto_name]
            if principled_name is None or not snapshot.nodes <= {n.name for n in material.node_tree.nodes}:
                continue
            self._snap[material_name] = (snapshot.clone_for(material), principled_name, None, None)
            principled = material.node_tree.nodes[principled_name]
            chain = chain_module.Chain(material, self._snap[material_name][0], hook.Origin(material, principled, snapshot.plugs), principled_name)
            self.chains[material_name] = chain
            return chain
        self.skipped.setdefault(material_name, 'a copy whose original is not known')
        return None

    def hookable(self):
        """Names of the materials the kit can put a layer into."""
        return sorted(self._snap)

    def materials_for(self, key):
        """The materials a layer goes into: those used by objects of the layer's roles (never-listed and glowing materials left out)."""
        if self.registry.get(key) is not None and self.registry[key].roles == 'all':
            return [m for m in self.hookable() if m not in self.skipped]
        wanted = self.layer_role_names(key)
        names = self.role_map.materials_of(wanted)
        return [m for m in names if m in self._snap and m not in self.skipped]

    # ---------------------------------------------------------------- putting layers in
    def apply(self, look=None, layers=None, overrides=None):
        """Puts the layers into the materials of their roles. look: a look name or file (default: the one already loaded). layers: keys (default: every registered layer).
        overrides: {layer: {dial: value}}. Returns {layer: [materials it went into]}."""
        if not self.prepared:
            self.prepare()
        if look is not None:
            self.look = settings_module.load_look(look)
        keys = list(layers) if layers is not None else list(self.registry)
        result = {}
        for key in keys:
            spec = self.registry.get(key)
            if spec is None:
                self.log.append(f'layer {key!r} has no builder: left out')
                continue
            if key in self.active and self.active[key]['on']:
                continue
            values = dials.resolve(key, self.look, self.settings, (overrides or {}).get(key), strict=False)
            if spec.tree is None:
                spec.tree = spec.builder(key)
            materials = self.materials_for(key)
            self.active[key] = dict(on=True, values=values, materials=[])
            self._write_layer_amount(key)
            for name in materials:
                if self._insert(key, name):
                    self.active[key]['materials'].append(name)
            self._push_dials(key)
            result[key] = list(self.active[key]['materials'])
        return result

    def _write_layer_amount(self, key):
        """wk_<key>_amount on every object: 1 where the object's role is one of the layer's, 0 elsewhere (layers not named in the set's apply block)."""
        wanted = set(self.layer_role_names(key))
        name = dials.object_attribute_name(key, 'amount')
        everything = self.registry.get(key) is not None and self.registry[key].roles == 'all'
        for obj in bpy.context.scene.objects:
            if obj.type in ('MESH', 'CURVE', 'EMPTY', 'SURFACE', 'FONT', 'META'):
                obj[name] = 1.0 if (everything or self.role_map.primary.get(obj.name) in wanted) else 0.0

    def _insert(self, key, material_name):
        spec = self.registry[key]
        chain = self.chain_for(material_name)
        if chain is None:
            return False
        if chain.stage(key) is not None:
            return True
        tree = chain.tree
        node = tree.nodes.new('ShaderNodeGroup')
        node.node_tree = spec.tree
        node.name = f'WK {key}'
        node.label = f'WK {key} ({spec.slot})'
        principled = chain.principled
        node.location = (principled.location.x - 500 - 40 * len(chain.stages), principled.location.y + 400)
        chain.add_kit_stage(key, node, spec.slot, self.settings.slot_positions())
        chain.rebuild()
        for service in self.services:
            service(self, chain, node, key)
        return True

    def _push_dials(self, key, only_material=None):
        state = self.active.get(key)
        if state is None:
            return
        for name in (state['materials'] if only_material is None else [only_material]):
            chain = self.chains.get(name)
            node = chain.node(key) if chain else None
            if node is None:
                continue
            for dial, value in state['values'].items():
                socket = node.inputs.get(socket_name(dial))
                if socket is None:
                    continue
                socket.default_value = dials.effective_amount(state['values'], self.master) if dial == 'amount' else float(value)

    def set_dials(self, layer, **values):
        """Changes dials of a layer already in (by dial name; unknown names raise). 'amount' is multiplied by the master."""
        state = self.active[layer]
        table = dials.TABLE.layers.get(layer)
        for dial, value in values.items():
            if table is not None and table.row(dial) is None:
                raise KeyError(f'{layer}: unknown dial {dial!r}')
            state['values'][dial] = value
        self._push_dials(layer)

    def set_master(self, amount):
        self.master = float(amount)
        for key in self.active:
            self._push_dials(key)

    def layer_off(self, key):
        """Takes the layer's nodes out of every chain (the same picture as Amount 0, faster). The look values are kept."""
        state = self.active.get(key)
        if state is None or not state['on']:
            return
        for name in state['materials']:
            chain = self.chains.get(name)
            if chain is not None:
                chain.remove_stage(key)
        state['on'] = False

    def layer_on(self, key):
        state = self.active.get(key)
        if state is None or state['on']:
            return
        state['on'] = True
        for name in state['materials']:
            self._insert(key, name)
        self._push_dials(key)

    def remove(self, layer=None):
        """With a layer: takes that layer out of every chain (twice is harmless). Without: EVERYTHING off, every material back as its snapshot says, per-object values cleared."""
        if layer is not None:
            state = self.active.pop(layer, None)
            for chain in self.chains.values():
                chain.remove_stage(layer)
            return state is not None
        self.hide_mask()
        for chain in list(self.chains.values()):
            chain.restore()
        for name, entry in self._snap.items():                       # materials that never got a chain may still carry an earlier layer's nodes
            material = bpy.data.materials.get(name)
            if material is not None and material.node_tree is not None:
                entry[0].restore(material)
        self.chains.clear()
        self.active.clear()
        self._snap.clear()
        self.skipped.clear()
        self.forced.clear()
        seed.clear_object_values()
        self.prepared = False
        return True

    # ---------------------------------------------------------------- the earlier layers
    def register_legacy(self):
        """After the earlier layers were put on by their own scripts: finds their nodes by name in every material and registers them as stages. Returns {stage: [materials]}."""
        legacy = self.settings.legacy()
        found = {}
        if not legacy:
            return found
        for index, stage in enumerate(legacy.get('order', [])):
            ports = legacy['stage_ports'][stage]
            found[stage] = []
            for material in list(bpy.data.materials):
                if material.node_tree is None:
                    continue
                node = material.node_tree.nodes.get(ports['node'])
                if node is None or node.type != 'GROUP':
                    continue
                chain = self.chain_for(material.name)
                if chain is None:
                    continue
                chain.add_legacy_stage(stage, node, ports, index)
                found[stage].append(material.name)
        for chain in self.chains.values():
            if chain.stages:
                chain.rebuild()
        return found

    def add_state_hook(self, function):
        """function(wetness, puddles) is called by set_state (the water layer's, the rubbish pieces', the growth pieces')."""
        self.state_hooks.append(function)

    def set_state(self, wetness, puddles):
        self.state = (wetness, puddles)
        for function in self.state_hooks:
            function(wetness, puddles)

    # ---------------------------------------------------------------- looking
    def show_mask(self, name, **options):
        from masks import debug
        self.hide_mask()
        self.shown_mask = debug.show_mask(self, name, **options)
        return self.shown_mask

    def hide_mask(self):
        if self.shown_mask is not None:
            self.shown_mask()
            self.shown_mask = None

    def verify(self):
        """Problems in every chain's wiring (an empty list means every chain is exactly what its list says)."""
        problems = []
        for name, chain in self.chains.items():
            problems += [f'{name}: {p}' for p in chain.verify()]
        return problems

    def report(self):
        by_reason = {}
        for name, reason in self.skipped.items():
            by_reason.setdefault(reason, []).append(name)
        return dict(set=self.settings.id, scene=self.scene_id, look=(self.look or {}).get('id'), master=self.master,
                    roles=self.role_map.counts() if self.role_map else {}, hookable=len(self._snap), skipped={k: sorted(v) for k, v in by_reason.items()},
                    chains={name: chain.keys() for name, chain in self.chains.items() if chain.stages},
                    layers={k: dict(on=v['on'], materials=len(v['materials']), values=v['values']) for k, v in self.active.items()},
                    unassigned_objects=len(self.role_map.unassigned) if self.role_map else 0, log=list(self.log))
