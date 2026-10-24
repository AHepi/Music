"""What this does: THE HOOK. It puts a wear layer into ANY material, whatever is wired into its Principled BSDF, by treating the surface as six values (the BUNDLE):
Colour (Base Color), Roughness, Specular IOR Level, Coat Weight, Normal and Metallic. For each of the six the material either has a wire into the plug or only a plain
number; the hook gives a layer "the wire, or a node that holds the plain number" (an RGB or Value node; for a Normal with no wire, the Geometry node's normal) and the
layer's outputs go back into the plugs. Nothing is changed in a material until a layer is put in. The material as it was (which node fed which plug, the plug numbers)
is written down once, as plain JSON on the material (pk_base), so everything the kit adds can be taken away and the original put back from that record alone,
even after the file is saved and opened again.
A material is skipped when it glows (emission strength above 0 with a colour that is not black: lit windows and lanterns must stay as they are) or has no Principled
box. It needs Blender (bpy). Carried from the project's weathering kit (own work), made generic and made to survive a save.
A concrete example: base = remember_base(material); ...layers go in...; restore_base(material) puts the six plugs and their numbers back exactly.
"""
import json

import bpy

BUNDLE = ('Colour', 'Roughness', 'Specular IOR Level', 'Coat Weight', 'Normal', 'Metallic')
PLUG = {'Colour': 'Base Color', 'Roughness': 'Roughness', 'Specular IOR Level': 'Specular IOR Level', 'Coat Weight': 'Coat Weight', 'Normal': 'Normal', 'Metallic': 'Metallic'}
TAG = 'pk_layer'              # on a node the kit added: the layer key ('origin' for a node that holds a plain number)
BASE_KEY = 'pk_base'          # on the material: the JSON record of how it was


def tag(node, key):
    node[TAG] = key
    return node


def tag_of(node):
    return node.get(TAG)


def kit_nodes(tree, key=None):
    return [n for n in tree.nodes if TAG in n.keys() and (key is None or n[TAG] == key)]


def active_output(tree):
    outputs = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL']
    for node in outputs:
        if node.is_active_output:
            return node
    return outputs[0] if outputs else None


def principled_of(material):
    tree = material.node_tree
    if tree is None:
        return None
    output = active_output(tree)
    if output is not None and output.inputs['Surface'].links:
        source = output.inputs['Surface'].links[0].from_node
        if source.type == 'BSDF_PRINCIPLED':
            return source
    return next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def glows(principled):
    strength, colour = principled.inputs['Emission Strength'], principled.inputs['Emission Color']
    if strength.links:
        return True
    return strength.default_value > 0.0 and (bool(colour.links) or max(colour.default_value[:3]) > 0.0)


def classify(material):
    """'ok', 'glow', 'no_surface' (no tree or no Principled box). Returns (reason, principled)."""
    if material is None or material.node_tree is None:
        return 'no_surface', None
    principled = principled_of(material)
    if principled is None:
        return 'no_surface', None
    if glows(principled):
        return 'glow', principled
    return 'ok', principled


def _socket_key(socket):
    return [socket.node.name, socket.identifier]


def _find_output(tree, key):
    node = tree.nodes.get(key[0])
    return next((s for s in node.outputs if s.identifier == key[1]), None) if node is not None else None


def remember_base(material, principled=None, force=False):
    """Writes the material's plain record (pk_base) the first time: for each of the six plugs the wire's source (node name and socket) or None, and every plug number.
    Does nothing when the record exists, unless force. Returns the record."""
    if BASE_KEY in material.keys() and not force:
        return json.loads(material[BASE_KEY])
    tree = material.node_tree
    principled = principled or principled_of(material)
    record = {'principled': principled.name, 'plugs': {}, 'defaults': {}, 'output_surface': None}
    for port in BUNDLE:
        socket = principled.inputs[PLUG[port]]
        record['plugs'][port] = _socket_key(socket.links[0].from_socket) if socket.links else None
        value = socket.default_value
        record['defaults'][port] = list(value) if hasattr(value, '__len__') else float(value)
    material[BASE_KEY] = json.dumps(record)
    return record


def restore_base(material):
    """Takes every node the kit added out of the material and puts the six plugs back as recorded. Safe to call when nothing was added."""
    tree = material.node_tree
    if tree is None:
        return False
    raw = material.get(BASE_KEY)
    for node in list(kit_nodes(tree)):
        tree.nodes.remove(node)
    if not raw:
        return False
    record = json.loads(raw)
    principled = tree.nodes.get(record['principled'])
    if principled is None:
        return False
    for port in BUNDLE:
        socket = principled.inputs[PLUG[port]]
        for link in list(socket.links):
            tree.links.remove(link)
        source = record['plugs'][port]
        found = _find_output(tree, source) if source else None
        if found is not None:
            tree.links.new(found, socket)
        elif source is None:
            try:
                socket.default_value = record['defaults'][port]
            except (TypeError, AttributeError):
                pass
    return True


class Origin:
    """What each of the six plugs was fed by before any layer: the wire, or a node holding the plain number (made when first asked)."""

    def __init__(self, material, record):
        self.material = material
        self.record = record

    def socket(self, port):
        tree = self.material.node_tree
        source = self.record['plugs'][port]
        found = _find_output(tree, source) if source else None
        if found is not None:
            return found
        principled = tree.nodes[self.record['principled']]
        existing = next((n for n in kit_nodes(tree, 'origin') if n.get('pk_port') == port), None)
        if existing is None:
            if port == 'Normal':
                existing = tree.nodes.new('ShaderNodeNewGeometry')
            elif port == 'Colour':
                existing = tree.nodes.new('ShaderNodeRGB')
                existing.outputs[0].default_value = tuple(self.record['defaults'][port])
            else:
                existing = tree.nodes.new('ShaderNodeValue')
                existing.outputs[0].default_value = float(self.record['defaults'][port])
            tag(existing, 'origin')
            existing['pk_port'] = port
            existing.label = f'origin {port}'
            existing.location = (principled.location.x - 900, principled.location.y - 200 - 120 * BUNDLE.index(port))
        return existing.outputs['Normal' if port == 'Normal' else 'Color' if port == 'Colour' else 'Value']
