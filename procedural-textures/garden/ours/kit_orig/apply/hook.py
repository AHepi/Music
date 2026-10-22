# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE HOOK: how a layer is put into ANY material, whatever is wired into its Principled BSDF (Blender's all-purpose surface shader).
# A surface is described to the Principled box by SIX values, the BUNDLE: Colour (Base Color), Roughness, Specular IOR Level, Coat Weight, Normal and Metallic.
# For each of the six, the material either has a wire into the plug or only a plain number. The hook takes "the wire, OR a node that holds the plain number" (a Value or
# RGB node; for a Normal with no wire the Geometry node's Normal) so the layer always has something to read, and the layer's outputs go back into the plugs.
#   * Nothing is changed in the material until a layer is put in (the constant nodes are made only when needed); a plug nobody changes keeps its own wire or number.
#   * A material is SKIPPED when it is in the set's `never` list, when it glows (emission strength above 0 with a colour that is not black), or when it has no Principled box
#     (then the adapter, adapters.py, may build one from the add-on's shader group).
#   * The SNAPSHOT records the material as it was (node names, the Principled box's numbers, its six plug wires, the wire into the Material Output) so everything the kit
#     adds can be taken away and the original put back from the snapshot alone.
# Needs Blender (bpy).
import bpy

BUNDLE = ('Colour', 'Roughness', 'Specular IOR Level', 'Coat Weight', 'Normal', 'Metallic')
PLUG = {'Colour': 'Base Color', 'Roughness': 'Roughness', 'Specular IOR Level': 'Specular IOR Level', 'Coat Weight': 'Coat Weight', 'Normal': 'Normal', 'Metallic': 'Metallic'}
TAG = 'wk'
TAG_SLOT = 'wk_slot'


def tag(node, key, slot=None):
    node[TAG] = key
    if slot:
        node[TAG_SLOT] = slot
    return node


def tag_of(node):
    return node.get(TAG)


def nodes_tagged(tree, key=None):
    """The nodes of a tree the kit added (tag 'wk'); with a key only that layer's."""
    return [n for n in tree.nodes if TAG in n and (key is None or n[TAG] == key)]


def active_output(tree):
    outputs = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL']
    for n in outputs:
        if n.is_active_output and n.target in ('ALL', 'EEVEE'):
            return n
    for n in outputs:
        if n.is_active_output:
            return n
    return outputs[0] if outputs else None


def _upstream_shaders(socket, seen=None):
    """Every node that makes a shader reaching this socket, through mix and add shader nodes and reroutes."""
    seen = seen if seen is not None else set()
    result = []
    for link in socket.links:
        node = link.from_node
        if node.name in seen:
            continue
        seen.add(node.name)
        if node.type in ('MIX_SHADER', 'ADD_SHADER'):
            for inp in node.inputs:
                if inp.type == 'SHADER':
                    result += _upstream_shaders(inp, seen)
        elif node.type == 'REROUTE':
            result += _upstream_shaders(node.inputs[0], seen)
        else:
            result.append(node)
    return result


def find_surface(material):
    """(principled, kind): kind is 'principled', 'mixed' (a Mix or Add Shader after the box; still fine), 'group' (a shader group that makes the shader: the adapter's job),
    'emission' or 'none'. principled is None unless one Principled box feeds the output."""
    tree = material.node_tree
    if tree is None:
        return None, 'none'
    output = active_output(tree)
    if output is None or not output.inputs['Surface'].links:
        return None, 'none'
    direct = output.inputs['Surface'].links[0].from_node
    shaders = _upstream_shaders(output.inputs['Surface'])
    principled = [n for n in shaders if n.type == 'BSDF_PRINCIPLED']
    if len(principled) == 1 and len(shaders) == 1:
        return principled[0], 'principled'
    if len(principled) == 1:
        others = [n for n in shaders if n.type != 'BSDF_PRINCIPLED']
        if any(n.type == 'EMISSION' for n in others):
            return principled[0], 'emission'
        return principled[0], 'mixed'
    if len(principled) > 1:
        return None, 'ambiguous'
    if any(n.type == 'GROUP' for n in shaders):
        return None, 'group'
    if any(n.type == 'EMISSION' for n in shaders):
        return None, 'emission'
    return None, 'none' if direct is None else 'other'


def emission_active(principled, threshold=0.0):
    """True when the box really glows: Emission Strength above the threshold and an Emission Color that is wired or not black."""
    strength = principled.inputs['Emission Strength']
    colour = principled.inputs['Emission Color']
    if strength.links:
        return True
    if strength.default_value <= threshold:
        return False
    return bool(colour.links) or max(colour.default_value[:3]) > 0.0


def _socket_key(socket):
    return (socket.node.name, socket.identifier, socket.is_output)


class Snapshot:
    """A material as it was: node names, the wire into the Material Output, the Principled box (name, numbers, six plug wires)."""

    def __init__(self, material, principled=None):
        tree = material.node_tree
        self.material_name = material.name
        self.nodes = {n.name for n in tree.nodes}
        output = active_output(tree)
        self.output_name = output.name if output else None
        self.surface = None
        if output is not None and output.inputs['Surface'].links:
            link = output.inputs['Surface'].links[0]
            self.surface = (link.from_node.name, link.from_socket.identifier)
        self.principled = principled.name if principled is not None else None
        self.defaults = {}
        self.plugs = {}
        if principled is not None:
            for inp in principled.inputs:
                value = getattr(inp, 'default_value', None)
                if value is not None:
                    try:
                        value = tuple(value)
                    except TypeError:
                        pass
                    self.defaults[inp.identifier] = value
            for port in BUNDLE:
                socket = principled.inputs[PLUG[port]]
                self.plugs[port] = (socket.links[0].from_node.name, socket.links[0].from_socket.identifier) if socket.links else None
            # every wire into the Principled box (not only the six), so the box is put back exactly
            self.all_links = [(l.from_node.name, l.from_socket.identifier, l.to_socket.identifier) for l in tree.links if l.to_node == principled]
        else:
            self.all_links = []

    def clone_for(self, material):
        """For a copy of a material made after the snapshot (same node names): the same snapshot under the copy's name."""
        other = Snapshot.__new__(Snapshot)
        other.__dict__.update(self.__dict__)
        other.material_name = material.name
        return other

    def restore(self, material):
        """Deletes every node that was not there, puts back the wire into the Material Output and the Principled box's numbers and wires."""
        tree = material.node_tree
        for node in list(tree.nodes):
            if node.name not in self.nodes:
                tree.nodes.remove(node)
        output = tree.nodes.get(self.output_name) if self.output_name else None
        if output is not None and self.surface:
            source = tree.nodes.get(self.surface[0])
            if source is not None:
                socket = next((s for s in source.outputs if s.identifier == self.surface[1]), None)
                if socket is not None:
                    tree.links.new(socket, output.inputs['Surface'])
        principled = tree.nodes.get(self.principled) if self.principled else None
        if principled is not None:
            for inp in principled.inputs:
                for link in list(inp.links):
                    tree.links.remove(link)
            for from_name, from_id, to_id in self.all_links:
                source = tree.nodes.get(from_name)
                target = next((s for s in principled.inputs if s.identifier == to_id), None)
                socket = next((s for s in source.outputs if s.identifier == from_id), None) if source is not None else None
                if socket is not None and target is not None:
                    tree.links.new(socket, target)
            for inp in principled.inputs:
                if inp.identifier in self.defaults:
                    try:
                        inp.default_value = self.defaults[inp.identifier]
                    except (TypeError, AttributeError):
                        pass


class Origin:
    """What each of the six plugs was fed by before any layer: the wire, or a node holding the plain number (made when first asked)."""

    def __init__(self, material, principled, links=None):
        """links: {port: (node name, socket identifier) or None} as the SNAPSHOT recorded them (taken before any earlier layer was put on); without it the box is read now."""
        self.material = material
        self.principled = principled.name
        if links is not None:
            self.links = dict(links)
        else:
            self.links = {}
            for port in BUNDLE:
                socket = principled.inputs[PLUG[port]]
                self.links[port] = (socket.links[0].from_node.name, socket.links[0].from_socket.identifier) if socket.links else None
        self.constants = {}

    def is_constant(self, port):
        return self.links[port] is None

    def socket(self, port):
        tree = self.material.node_tree
        found = self.links[port]
        if found is not None:
            node = tree.nodes.get(found[0])
            if node is not None:
                socket = next((s for s in node.outputs if s.identifier == found[1]), None)
                if socket is not None:
                    return socket
        socket_name = {'Normal': 'Normal', 'Colour': 'Color'}.get(port, 'Value')
        name = self.constants.get(port)
        node = tree.nodes.get(name) if name else None
        if node is None:
            principled = tree.nodes[self.principled]
            plug = principled.inputs[PLUG[port]]
            if port == 'Normal':
                node = tree.nodes.new('ShaderNodeNewGeometry')
            elif port == 'Colour':
                node = tree.nodes.new('ShaderNodeRGB')
                node.outputs[0].default_value = tuple(plug.default_value)
            else:
                node = tree.nodes.new('ShaderNodeValue')
                node.outputs[0].default_value = float(plug.default_value)
            tag(node, 'origin')
            node.label = f'origin {port}'
            node.location = (principled.location.x - 900, principled.location.y - 200 - 120 * BUNDLE.index(port))
            self.constants[port] = node.name
        return node.outputs[socket_name]

    def clone_for(self, material):
        other = Origin.__new__(Origin)
        other.__dict__.update(self.__dict__)
        other.material = material
        other.constants = {}
        return other


def classify(material, settings=None, role_map=None):
    """Why a material is (not) hooked: 'ok', 'ok_mixed', 'never', 'glow', 'group' (needs the adapter), 'no_surface', 'ambiguous'. Returns (reason, principled)."""
    if material.node_tree is None:
        return 'no_surface', None
    if role_map is not None and material.name in role_map.never_materials:
        return 'never', None
    principled, kind = find_surface(material)
    if kind == 'group':
        return 'group', None
    if principled is None:
        return {'ambiguous': 'ambiguous'}.get(kind, 'no_surface'), None
    threshold = 0.0
    if settings is not None:
        threshold = (settings.get('hook') or {}).get('skip_if_emission_strength_above', 0.0)
    if kind == 'emission' or emission_active(principled, threshold):
        return 'glow', principled
    return ('ok' if kind == 'principled' else 'ok_mixed'), principled
