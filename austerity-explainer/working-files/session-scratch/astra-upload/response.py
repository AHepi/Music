"""Opt-in Cycles response adapter for one direct opaque Principled surface.

Adapted from the project's schema-3 response: retained original shader,
stored local coordinates and bounded normal perturbation. This is deliberately
a smaller contract: no registered groups, compositor, AOV, sky or pigment authoring.
The implementation is tested here; numerical/source inheritance is not art approval.
"""
import hashlib
import json

REST_ATTRIBUTE = "astra_style_rest_v1"
RESPONSE_VERSION = "1.0.0"


def _source(socket):
    seen = set()
    while socket.node.type == "REROUTE" and socket.node.inputs[0].is_linked:
        key = socket.as_pointer()
        if key in seen:
            raise ValueError("Cyclic reroute graph")
        seen.add(key)
        socket = socket.node.inputs[0].links[0].from_socket
    return socket


def inspect_material(mat):
    if mat is None:
        return False, "Empty slot"
    if mat.library or mat.override_library:
        return False, "Linked or overridden material is outside this adapter"
    if mat.get("paint_module_version") is not None or mat.get("astra_response_version"):
        return False, "Already styled material: rebuild from an unmodified baseline"
    if not mat.use_nodes or not mat.node_tree:
        return False, "Non-node material is preserved"
    if mat.node_tree.animation_data or mat.animation_data:
        return False, "Animated/driven materials require a dedicated adapter"
    outputs = [n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output]
    if len(outputs) != 1:
        return False, "Requires one active Material Output"
    out = outputs[0]
    if out.inputs["Volume"].is_linked:
        return False, "Volume is excluded"
    if not out.inputs["Surface"].is_linked:
        return False, "No connected surface"
    try:
        p = _source(out.inputs["Surface"].links[0].from_socket).node
    except ValueError as exc:
        return False, str(exc)
    if p.type != "BSDF_PRINCIPLED":
        return False, "Only a direct Principled surface is supported; groups/mixes are preserved"
    alpha, trans = p.inputs["Alpha"], p.inputs["Transmission Weight"]
    if alpha.is_linked or alpha.default_value < .999 or trans.is_linked or trans.default_value > .001:
        return False, "Transparent/transmissive surfaces are excluded"
    emission = p.inputs.get("Emission Strength")
    if emission and (emission.is_linked or emission.default_value > .001):
        # Principled defaults can have strength 1 but an exactly black emission.
        col = p.inputs.get("Emission Color")
        if not col or col.is_linked or any(v > .001 for v in col.default_value[:3]):
            return False, "Emissive surfaces are excluded"
    if out.inputs["Displacement"].is_linked:
        return False, "Displacement requires an independently validated adapter"
    return True, "Direct opaque Principled; original color, roughness and normal retained"


def bind_rest_coordinates(mesh, metre_scale):
    """Only called on a private mesh copy; static bind coordinates in metres."""
    old = mesh.attributes.get(REST_ATTRIBUTE)
    if old:
        mesh.attributes.remove(old)
    attr = mesh.attributes.new(REST_ATTRIBUTE, "FLOAT_VECTOR", "POINT")
    values = [v.co[i] * metre_scale[i] for v in mesh.vertices for i in range(3)]
    attr.data.foreach_set("vector", values)
    mesh.update()


def apply_material(mat, spec):
    if spec["blend"] == 0:
        return {"status": "identity", "nodes_added": 0}
    ok, reason = inspect_material(mat)
    if not ok:
        raise ValueError(reason)
    t = mat.node_tree
    out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
    original = out.inputs["Surface"].links[0].from_socket
    p = _source(original).node
    count = len(t.nodes)

    def node(kind, label):
        n = t.nodes.new(kind)
        n.name = n.label = "Astra | " + label
        return n

    def connect(value, socket):
        if hasattr(value, "is_output"):
            t.links.new(value, socket)
        else:
            socket.default_value = value

    geo = node("ShaderNodeNewGeometry", "original shading normal")
    normal_input = p.inputs["Normal"]
    normal = normal_input.links[0].from_socket if normal_input.is_linked else geo.outputs["Normal"]
    if spec["tilt"] > 0:
        attr = node("ShaderNodeAttribute", "stored rest coordinates in metres")
        attr.attribute_name = REST_ATTRIBUTE
        scale = node("ShaderNodeVectorMath", "material-specific mark dimensions")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = spec["scale"]
        t.links.new(attr.outputs["Vector"], scale.inputs[0])
        cells = node("ShaderNodeTexVoronoi", "coherent response planes")
        cells.inputs["Scale"].default_value = 1
        cells.inputs["Randomness"].default_value = .72
        t.links.new(scale.outputs[0], cells.inputs["Vector"])
        centered = node("ShaderNodeVectorMath", "centred bounded local vector")
        centered.operation = "SUBTRACT"
        centered.inputs[1].default_value = (.5, .5, .5)
        t.links.new(cells.outputs["Color"], centered.inputs[0])
        transform = node("ShaderNodeVectorTransform", "asset-attached normal direction")
        transform.vector_type = "NORMAL"
        transform.convert_from, transform.convert_to = "OBJECT", "WORLD"
        t.links.new(centered.outputs[0], transform.inputs[0])
        direction = node("ShaderNodeVectorMath", "unit perturbation direction")
        direction.operation = "NORMALIZE"
        t.links.new(transform.outputs[0], direction.inputs[0])
        length = node("ShaderNodeVectorMath", "bounded local magnitude")
        length.operation = "LENGTH"
        t.links.new(centered.outputs[0], length.inputs[0])
        amplitude = node("ShaderNodeMath", "limited tilt")
        amplitude.operation = "MULTIPLY"
        amplitude.inputs[1].default_value = spec["tilt"]
        t.links.new(length.outputs["Value"], amplitude.inputs[0])
        small = node("ShaderNodeVectorMath", "bounded perturbation")
        small.operation = "SCALE"
        t.links.new(direction.outputs[0], small.inputs[0])
        t.links.new(amplitude.outputs[0], small.inputs["Scale"])
        add = node("ShaderNodeVectorMath", "preserve authored relief")
        add.operation = "ADD"
        t.links.new(normal, add.inputs[0])
        t.links.new(small.outputs[0], add.inputs[1])
        norm = node("ShaderNodeVectorMath", "unit response normal")
        norm.operation = "NORMALIZE"
        t.links.new(add.outputs[0], norm.inputs[0])
        normal = norm.outputs[0]
    diffuse = node("ShaderNodeBsdfToon", "shadow receiving diffuse response")
    diffuse.component = "DIFFUSE"
    base = p.inputs["Base Color"]
    connect(base.links[0].from_socket if base.is_linked else tuple(base.default_value), diffuse.inputs["Color"])
    diffuse.inputs["Size"].default_value = spec["size"]
    diffuse.inputs["Smooth"].default_value = spec["smooth"]
    t.links.new(normal, diffuse.inputs["Normal"])
    painted = diffuse.outputs[0]
    if spec["gloss"] > 0:
        glossy = node("ShaderNodeBsdfToon", "restrained broad highlight")
        glossy.component = "GLOSSY"
        glossy.inputs["Color"].default_value = (.28, .31, .33, 1)
        glossy.inputs["Size"].default_value = .09
        glossy.inputs["Smooth"].default_value = .14
        t.links.new(normal, glossy.inputs["Normal"])
        mix = node("ShaderNodeMixShader", "limited painted highlight")
        mix.inputs[0].default_value = spec["gloss"]
        t.links.new(painted, mix.inputs[1])
        t.links.new(glossy.outputs[0], mix.inputs[2])
        painted = mix.outputs[0]
    hybrid = node("ShaderNodeMixShader", "retain original Cycles shader")
    hybrid.inputs[0].default_value = spec["blend"]
    t.links.new(original, hybrid.inputs[1])
    t.links.new(painted, hybrid.inputs[2])
    t.links.new(hybrid.outputs[0], out.inputs["Surface"])
    mat["astra_response_version"] = RESPONSE_VERSION
    mat["astra_family"] = spec["family"]
    mat["astra_art_status"] = "experimental"
    mat["astra_response_config"] = json.dumps(spec, sort_keys=True)
    mat["astra_response_sha256"] = hashlib.sha256(mat["astra_response_config"].encode()).hexdigest()
    return {"status": "applied", "nodes_added": len(t.nodes) - count,
            "art_status": "experimental", "normal_addition_bound": 3 ** .5 * .5 * spec["tilt"]}
