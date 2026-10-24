"""Bounded Foundry Fabric COLOR-overlay recipe, not a generic shader modifier.

Only the explicit graph/socket contract below is supported. No install, handlers,
drivers, image assets or scene-wide lookup. Blender 5.1.2 is the tested target.
"""
import bpy
import json
import math

VERSION = '0.1.0'
GROUP_NODE = 'FOUNDRY surface controls'
OPACITY = 'Stroke opacity'
MIX = '07 / Angular dry brush over local color'
PIGMENT = '04 / Dominant base / sparse warm planes'
SHADER = 'Light-responsive layered pigment'
OUTPUT = 'Exportable material channels'

def _strength(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('overlay_strength must be a finite number in [0, 1]')

def _source(socket, node_name, output_name):
    if len(socket.links) != 1:
        raise ValueError('Expected exactly one link at ' + socket.node.name + ':' + socket.name)
    edge = socket.links[0]
    if edge.from_node.name != node_name or edge.from_socket.name != output_name:
        raise ValueError('Unsupported source at ' + socket.node.name + ':' + socket.name)

def validate_receiver(obj, slot_index, overlay_strength=0.0):
    """Read-only preflight. Graph names are necessary but never sufficient."""
    _strength(overlay_strength)
    if obj is None or obj.type != 'MESH' or obj.library is not None or obj.data.library is not None:
        raise ValueError('A local editable mesh object is required')
    if type(slot_index) is not int or not 0 <= slot_index < len(obj.material_slots):
        raise ValueError('Choose an existing material slot by nonnegative integer index')
    slot = obj.material_slots[slot_index]
    source = slot.material
    if source is None or not source.use_nodes or source.library is not None:
        raise ValueError('A local node material is required')
    if 'fo_handle' in source:
        raise ValueError('Already a Foundry overlay receiver; use set_overlay_strength or restore first')
    tree = source.node_tree
    outputs = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    if len(outputs) != 1:
        raise ValueError('Exactly one active Material Output is required')
    outer = tree.nodes.get(GROUP_NODE)
    if outer is None or outer.bl_idname != 'ShaderNodeGroup' or outer.node_tree is None:
        raise ValueError('The declared Foundry surface group is absent')
    _source(outputs[0].inputs['Surface'], GROUP_NODE, 'Shader')
    g = outer.node_tree
    if source.animation_data is not None or tree.animation_data is not None or g.animation_data is not None:
        raise ValueError('Animated material graphs are outside this static recipe')
    if outer.mute or outer.outputs['Albedo'].is_linked:
        raise ValueError('Muted groups or externally consumed Albedo outputs are unsupported')
    if outputs[0].inputs['Volume'].is_linked or outputs[0].inputs['Displacement'].is_linked:
        raise ValueError('The supported Fabric recipe has no volume or displacement route')
    shader_uses = [(l.to_node.name,l.to_socket.name) for l in outer.outputs['Shader'].links]
    if shader_uses != [(outputs[0].name,'Surface')]:
        raise ValueError('The group shader has an additional unsupported consumer')
    expected = {
        'Bounded art direction': 'NodeGroupInput',
        OPACITY: 'ShaderNodeMath',
        MIX: 'ShaderNodeMixRGB',
        PIGMENT: 'ShaderNodeMixRGB',
        'Grouped brush deposits': 'ShaderNodeMath',
        SHADER: 'ShaderNodeBsdfPrincipled',
        OUTPUT: 'NodeGroupOutput',
    }
    for name, kind in expected.items():
        n = g.nodes.get(name)
        if n is None or n.bl_idname != kind:
            raise ValueError('Unsupported graph role/type: ' + name)
    output = g.nodes[OUTPUT]
    if not output.is_active_output or sum(n.type == 'GROUP_OUTPUT' and n.is_active_output for n in g.nodes) != 1:
        raise ValueError('Exactly the declared active Group Output is required')
    op, mix, shader = (g.nodes[x] for x in (OPACITY, MIX, SHADER))
    if any(g.nodes[name].mute for name in expected):
        raise ValueError('Muted contract nodes are unsupported')
    if op.operation != 'MULTIPLY' or op.inputs[1].is_linked or op.use_clamp:
        raise ValueError('Stroke opacity must be an unclamped MULTIPLY with constant second input')
    if not math.isfinite(op.inputs[1].default_value) or not 0 <= op.inputs[1].default_value <= 1:
        raise ValueError('Original overlay multiplier is outside the supported range')
    if mix.blend_type != 'MIX' or mix.use_clamp:
        raise ValueError('The dry-brush color node must be an unclamped MixRGB MIX')
    _source(op.inputs[0], 'Grouped brush deposits', 'Value')
    _source(mix.inputs[0], OPACITY, 'Value')
    _source(mix.inputs[1], PIGMENT, 'Color')
    _source(mix.inputs[2], 'Bounded art direction', 'Highlight')
    _source(shader.inputs['Base Color'], MIX, 'Color')
    _source(output.inputs['Albedo'], MIX, 'Color')
    _source(output.inputs['Shader'], SHADER, 'BSDF')
    # These closed fan-outs certify that opacity cannot reach roughness/normal.
    targets = {(l.to_node.name, l.to_socket.identifier) for l in op.outputs[0].links}
    if targets != {(MIX, mix.inputs[0].identifier)} or len(op.outputs[0].links) != 1:
        raise ValueError('Opacity has an unsupported additional consumer')
    targets = {(l.to_node.name, l.to_socket.identifier) for l in mix.outputs['Color'].links}
    if targets != {(SHADER, shader.inputs['Base Color'].identifier), (OUTPUT, output.inputs['Albedo'].identifier)} or len(mix.outputs['Color'].links) != 2:
        raise ValueError('Dry-brush output reaches an unsupported non-color route')
    if not shader.inputs['Roughness'].is_linked or not shader.inputs['Normal'].is_linked:
        raise ValueError('Expected preserved Foundry roughness and normal branches')
    return {'object': obj.name, 'slot': slot_index, 'source_material': source.name,
            'source_group': g.name, 'link': slot.link, 'original_multiplier': op.inputs[1].default_value,
            'color_only_consumers': sorted(targets)}

def apply_overlay_strength(obj, slot_index, overlay_strength=0.0):
    """Validate, copy material + one group, then bind a private OBJECT override."""
    before = validate_receiver(obj, slot_index, overlay_strength)
    slot = obj.material_slots[slot_index]
    source = slot.material
    private = source.copy()
    private.name = 'Textile / ' + obj.name
    outer = private.node_tree.nodes[GROUP_NODE]
    outer.node_tree = outer.node_tree.copy()
    outer.node_tree.name = 'Textile Foundry / ' + obj.name
    handle = dict(before, private_material=private.name, private_group=outer.node_tree.name,
                  version=VERSION, overlay_strength=float(overlay_strength))
    private['fo_handle'] = json.dumps(handle)
    outer.node_tree.nodes[OPACITY].inputs[1].default_value = before['original_multiplier'] * overlay_strength
    slot.link = 'OBJECT'
    slot.material = private
    return handle

def set_overlay_strength(material, overlay_strength):
    _strength(overlay_strength)
    if material is None or 'fo_handle' not in material:
        raise ValueError('Not a private Foundry overlay material')
    h = json.loads(material['fo_handle'])
    if h['private_material'] != material.name:
        raise ValueError('Material identity differs from its recorded handle')
    outer = material.node_tree.nodes.get(GROUP_NODE)
    if outer is None or outer.node_tree.name != h['private_group']:
        raise ValueError('Private group identity differs from its recorded handle')
    outer.node_tree.nodes[OPACITY].inputs[1].default_value = h['original_multiplier'] * overlay_strength
    h['overlay_strength'] = float(overlay_strength)
    material['fo_handle'] = json.dumps(h)
    return h

def restore_receiver(obj, slot_index):
    if obj is None or obj.type != 'MESH' or type(slot_index) is not int or not 0 <= slot_index < len(obj.material_slots):
        raise ValueError('Choose an existing mesh material slot')
    slot = obj.material_slots[slot_index]
    material = slot.material
    if material is None or 'fo_handle' not in material:
        raise ValueError('Not a private Foundry overlay receiver')
    h = json.loads(material['fo_handle'])
    if h['object'] != obj.name or h['slot'] != slot_index or h['private_material'] != material.name:
        raise ValueError('The active receiver differs from its recorded handle')
    source = bpy.data.materials.get(h['source_material'])
    if source is None:
        raise ValueError('Original material is unavailable')
    if h['link'] == 'DATA' and obj.data.materials[slot_index] != source:
        raise ValueError('Mesh DATA binding changed; refusing to overwrite another edit')
    if h['link'] not in ('DATA', 'OBJECT'):
        raise ValueError('Unsupported original material binding')
    slot.material = source
    slot.link = h['link']
    return {'object': obj.name, 'slot': slot_index, 'link': slot.link, 'material': slot.material.name}
