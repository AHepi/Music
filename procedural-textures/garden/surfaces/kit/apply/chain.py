# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE CHAIN: one ordered list of STAGES per material, from the photo to the Principled BSDF. A stage is one layer's node: a kit layer, or one of the three earlier layers
# (WETNESS, JOINTS, RUBBISH, "legacy stages", registered from the set's legacy.stage_ports and never edited or removed with their own scripts).
#   * Every wire between stages is made FROM THE LIST, never remembered: rebuild() walks the list in order and re-links everything it manages. Adding, removing or moving a
#     stage therefore cannot cut another stage out (the earlier scripts did: removing JOINTS silently cut RUBBISH out of the chain). Removing twice is harmless.
#   * The list's order: stages are sorted by a position: a legacy stage's position is its place in legacy.order (0, 1, 2 ...); a kit slot has a position too
#     (A before the first legacy stage, B after the second, C just after B), so A < WETNESS < JOINTS < B < C < RUBBISH on a material that has all of them, and A, B, C side
#     by side on a material that has none. Inside one slot, stages keep the order they were put in.
#   * Each stage says which of the seven ports it TAKES and GIVES: the six bundle ports (Colour, Roughness, Specular IOR Level, Coat Weight, Normal, Metallic) and Wet Normal
#     (the smoothed normal WETNESS uses when wet; a kit layer that carries a Wet Normal socket must change it the same way as Normal). A port a stage does not take goes
#     AROUND it. A legacy stage's own wires (a picture into WETNESS's Roughness, the height picture) are kept: the first taker of a port keeps its own source, and a kit layer
#     put in front of it reads that source, so a do-nothing layer changes nothing (tested: identical pictures).
#   * Masks: a stage can give masks (WETNESS: Wet Mask, Puddle Mask, Streak Mask). Kit layers positioned AFTER it get them wired by name; a layer positioned before it
#     reads 0 (the mask comes out of a node that depends on the layer: a loop). So slot A layers cannot see Wet Mask; the water layer wets them anyway.
#   * Every node the kit adds is tagged (node['wk'] = layer key, node['wk_slot'] = slot) and found by tag, so copies of a material are found too.
import bpy

from . import hook

PORTS = hook.BUNDLE + ('Wet Normal',)


def _find_socket(tree, key, output=True):
    node = tree.nodes.get(key[0])
    if node is None:
        return None
    sockets = node.outputs if output else node.inputs
    return next((s for s in sockets if s.identifier == key[1]), None)


def _sock_key(socket):
    return (socket.node.name, socket.identifier)


class Stage:
    def __init__(self, key, kind, node_name, position, seq, slot=None, takes=None, gives=None, own=None, provides=()):
        self.key = key
        self.kind = kind                        # 'kit' or 'legacy'
        self.node_name = node_name
        self.position = position
        self.seq = seq
        self.slot = slot
        self.takes = takes or {}                # port -> input socket name on the node
        self.gives = gives or {}                # port -> output socket name on the node
        self.own = own or {}                    # input socket name -> (node name, socket identifier): wires the earlier script made that are not chain wires
        self.provides = tuple(provides)         # mask names this stage gives (output socket names)

    @property
    def sort_key(self):
        return (self.position, self.seq)


class Chain:
    def __init__(self, material, snapshot, origin, principled_name):
        self.material_name = material.name
        self.snapshot = snapshot
        self.origin = origin
        self.principled_name = principled_name
        self.stages = []
        self._seq = 0

    # ---------------------------------------------------------------- access
    @property
    def material(self):
        return bpy.data.materials[self.material_name]

    @property
    def tree(self):
        return self.material.node_tree

    @property
    def principled(self):
        return self.tree.nodes[self.principled_name]

    def stage(self, key):
        return next((s for s in self.stages if s.key == key), None)

    def keys(self):
        return [s.key for s in sorted(self.stages, key=lambda s: s.sort_key)]

    def node(self, key):
        stage = self.stage(key)
        return self.tree.nodes.get(stage.node_name) if stage else None

    def ordered(self):
        return sorted(self.stages, key=lambda s: s.sort_key)

    # ---------------------------------------------------------------- adding and removing
    def _ports_of(self, node):
        takes = {p: p for p in PORTS if p in node.inputs}
        gives = {p: p for p in PORTS if p in node.outputs}
        return takes, gives

    def add_kit_stage(self, key, node, slot, slot_positions):
        if self.stage(key):
            raise ValueError(f'{self.material_name}: the layer {key!r} is already in the chain')
        takes, gives = self._ports_of(node)
        self._seq += 1
        stage = Stage(key, 'kit', node.name, slot_positions[slot], self._seq, slot=slot, takes=takes, gives=gives)
        self.stages.append(stage)
        hook.tag(node, key, slot)
        return stage

    def add_legacy_stage(self, key, node, ports, index):
        """Registers an earlier layer's node. ports: the set's legacy.stage_ports entry (takes, gives, masks). Its own wires (not from the origin side of another stage) are
        recorded so that the chain keeps them."""
        if self.stage(key):
            return self.stage(key)
        stage_nodes = {s.node_name for s in self.stages}
        takes = {name: name for name in ports['takes'] if name in PORTS}
        gives = {name: name for name in ports['gives'] if name in PORTS}
        own = {}
        for name in takes:
            socket = node.inputs.get(name)
            if socket is not None and socket.links:
                source = socket.links[0].from_node
                if source.name not in stage_nodes and not hook.tag_of(source):
                    own[name] = _sock_key(socket.links[0].from_socket)
        self._seq += 1
        stage = Stage(key, 'legacy', node.name, float(index), self._seq, takes=takes, gives=gives, own=own, provides=ports.get('masks', []))
        self.stages.append(stage)
        hook.tag(node, 'legacy:' + key)
        return stage

    def remove_stage(self, key, delete_node=True):
        stage = self.stage(key)
        if stage is None:
            return False
        self.stages.remove(stage)
        node = self.tree.nodes.get(stage.node_name)
        if node is not None and delete_node:
            self.tree.nodes.remove(node)
        self.rebuild()
        return True

    # ---------------------------------------------------------------- the one place wires are made
    def plan(self):
        """What the wiring should be: ({(node, input identifier): socket key} for stage inputs, {port: socket key or None} for the Principled plugs).
        None for a plug means 'the plug has no wire (it keeps its own number)'. Only the ports some stage takes or gives are touched; the others are put back as the snapshot
        says (the wire, or no wire). Constant nodes for plain numbers are made only here, only for a port a stage takes. rebuild() applies the plan."""
        tree = self.tree
        stages = self.ordered()
        taken = {p for s in stages for p in s.takes}
        init = {}
        for port in PORTS:
            if port not in taken:
                continue
            first = next((s for s in stages if port in s.takes and s.kind == 'legacy'), None)       # a kit layer in front of an earlier layer reads what that layer was fed by
            own = first.own.get(port) if first is not None else None
            found = _find_socket(tree, own) if own is not None else None
            if port == 'Wet Normal':
                init[port] = found
                continue
            init[port] = found if found is not None else self.origin.socket(port)
        if 'Wet Normal' in init and init['Wet Normal'] is None:
            init['Wet Normal'] = init['Normal'] if 'Normal' in init else self.origin.socket('Normal')
        cur = dict(init)
        stage_links = {}
        for stage in stages:
            node = tree.nodes.get(stage.node_name)
            if node is None:
                continue
            for port, input_name in stage.takes.items():
                source = cur.get(port)
                if source is None:
                    continue
                own = stage.own.get(input_name) if stage.kind == 'legacy' else None
                if own is not None and init.get(port) is not None and _sock_key(source) == _sock_key(init[port]):
                    own_socket = _find_socket(tree, own)
                    if own_socket is not None:
                        source = own_socket
                target = node.inputs.get(input_name)
                if target is not None:
                    stage_links[(node.name, target.identifier)] = _sock_key(source)
            for port, output_name in stage.gives.items():
                socket = node.outputs.get(output_name)
                if socket is not None:
                    cur[port] = socket
        plugs = {}
        for port in hook.BUNDLE:
            if port in cur:
                value = cur[port]
                plugs[port] = None if (self.origin.is_constant(port) and value.node.get(hook.TAG) == 'origin') else _sock_key(value)
            else:
                plugs[port] = self.origin.links[port]            # untouched: the wire it had, or none
        return stage_links, plugs

    def rebuild(self):
        """Makes every wire the plan says and removes the wires it replaces. Safe to call any number of times."""
        tree = self.tree
        stage_links, plugs = self.plan()
        for (node_name, input_id), source in stage_links.items():
            node = tree.nodes[node_name]
            target = next(s for s in node.inputs if s.identifier == input_id)
            socket = _find_socket(tree, source)
            if socket is not None:
                tree.links.new(socket, target)
        principled = self.principled
        for port, source in plugs.items():
            target = principled.inputs[hook.PLUG[port]]
            if source is None:
                for link in list(target.links):
                    tree.links.remove(link)
            else:
                socket = _find_socket(tree, source)
                if socket is not None:
                    tree.links.new(socket, target)
        self._wire_masks()

    def _wire_masks(self):
        tree = self.tree
        stages = self.ordered()
        for index, stage in enumerate(stages):
            if stage.kind != 'kit':
                continue
            node = tree.nodes.get(stage.node_name)
            if node is None:
                continue
            earlier = {}
            for other in stages[:index]:
                provider = tree.nodes.get(other.node_name)
                for name in other.provides:
                    if provider is not None and name in provider.outputs and name not in earlier:
                        earlier[name] = provider.outputs[name]
            later = {name for other in stages[index + 1:] for name in other.provides}
            for socket in node.inputs:
                if socket.name in earlier:
                    tree.links.new(earlier[socket.name], socket)
                elif socket.name in later and socket.links and socket.links[0].from_node.name in {o.node_name for o in stages[index + 1:]}:
                    tree.links.remove(socket.links[0])

    # ---------------------------------------------------------------- checks
    def verify(self):
        """A list of problems (empty = the wiring is exactly what the list says)."""
        problems = []
        tree = self.tree
        stage_links, plugs = self.plan()
        for (node_name, input_id), source in stage_links.items():
            node = tree.nodes[node_name]
            target = next(s for s in node.inputs if s.identifier == input_id)
            if not target.links or _sock_key(target.links[0].from_socket) != source:
                problems.append(f'{node_name}.{target.name} is not fed by {source}')
        principled = self.principled
        for port, source in plugs.items():
            target = principled.inputs[hook.PLUG[port]]
            if source is None:
                if target.links:
                    problems.append(f'plug {port} should keep its own number but has a wire')
            elif not target.links or _sock_key(target.links[0].from_socket) != source:
                problems.append(f'plug {port} is not fed by {source}')
        for stage in self.stages:
            if stage.node_name not in tree.nodes:
                problems.append(f'stage {stage.key} has no node {stage.node_name}')
        return problems

    def signature(self):
        """A sorted list describing every wire of the material (node names and socket identifiers) plus the node names: two equal signatures mean the same graph."""
        tree = self.tree
        links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in tree.links)
        return dict(nodes=sorted(n.name for n in tree.nodes), links=links)

    def restore(self):
        """Takes everything the kit and the earlier layers added away and puts the material back as the snapshot says."""
        self.stages.clear()
        self.snapshot.restore(self.material)


def graph_signature(material):
    """The same as Chain.signature() for any material (used to compare before and after)."""
    tree = material.node_tree
    links = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in tree.links)
    defaults = {}
    for n in tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            for i in n.inputs:
                v = getattr(i, 'default_value', None)
                try:
                    v = tuple(round(float(x), 6) for x in v)
                except TypeError:
                    v = round(float(v), 6) if isinstance(v, (int, float)) else v
                defaults[i.identifier] = v
    return dict(nodes=sorted(n.name for n in tree.nodes), links=links, principled=defaults)
