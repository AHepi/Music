"""What this does: reads a Blender material's node tree and says, as plain facts, which surface treatments it really has: a real normal map
that reaches the Principled node's Normal (and how it is set up), roughness that varies, colour that varies, real displacement (method, depth),
and which wear layers are in it. It looks at what is WIRED, not at what was asked for, so a normal map that is made and then left
unplugged, or a displacement node on a material still set to Bump Only, is seen for what it is. Nothing is changed. Needs Blender (bpy).

A concrete example: inspect_material(material)['normal_map'] gives {'has': True, 'images': 1, 'space': 'TANGENT', 'colourspace': 'Non-Color',
'uv_map': 'UVMap', 'reaches_normal': True, 'strength': 0.9, 'bump_leftover': 0.0}.
How "varies" is decided: following the wire UPSTREAM from the Principled input (through group nodes along the same-named socket, since a
wear layer passes the surface through), the first texture, noise, image, ramp-from-texture or object property counts as variation; a plain
number, a plain colour or a Value node does not.
"""
import bpy

from .. import names

TEXTURE_TYPES = {'TEX_IMAGE', 'TEX_NOISE', 'TEX_VORONOI', 'TEX_WAVE', 'TEX_GRADIENT', 'TEX_MAGIC', 'TEX_BRICK', 'TEX_CHECKER', 'TEX_ENVIRONMENT',
                 'VERTEX_COLOR', 'ATTRIBUTE', 'OBJECT_INFO', 'TEX_WHITE_NOISE', 'TEX_GABOR'}
PASS_THROUGH_TYPES = {'GROUP', 'REROUTE', 'MIX', 'MIX_RGB', 'MATH', 'MAP_RANGE', 'VALTORGB', 'CURVE_RGB', 'HUE_SAT', 'BRIGHTCONTRAST', 'GAMMA', 'INVERT',
                      'SEPARATE_COLOR', 'COMBINE_COLOR', 'CLAMP', 'RGBTOBW', 'BUMP', 'NORMAL_MAP', 'DISPLACEMENT', 'VECTOR_MATH', 'MAPPING'}


def principled_of(material):
    """The Principled BSDF node that feeds the material output, or the first Principled node, or None."""
    tree = material.node_tree
    if tree is None:
        return None
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL' and node.is_active_output and node.inputs['Surface'].links:
            source = node.inputs['Surface'].links[0].from_node
            if source.type == 'BSDF_PRINCIPLED':
                return source
    return next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def upstream_nodes(socket, limit=400):
    """Every node feeding this input socket, following wires back; a group node is followed along the input of the same name as the output
    the wire came from (a wear layer passes the surface through), not through its inside."""
    seen, found, stack = set(), [], [socket]
    while stack and len(found) < limit:
        current = stack.pop()
        for link in current.links:
            node = link.from_node
            key = (node.name, link.from_socket.identifier)
            if key in seen:
                continue
            seen.add(key)
            found.append(node)
            if node.type == 'GROUP':
                same = node.inputs.get(link.from_socket.name)
                stack.extend([same] if same is not None else list(node.inputs))
            else:
                stack.extend(list(node.inputs))
    return found


def varies(socket):
    """True when something upstream of the socket is a texture, noise, image or object property (the surface has variation)."""
    return any(node.type in TEXTURE_TYPES for node in upstream_nodes(socket))


def reaches(start_socket, target_socket, limit=600):
    """True when a wire path leads from an output socket to an input socket, through any in-between nodes (a group along its same-named socket)."""
    seen, stack = set(), [start_socket]
    steps = 0
    while stack and steps < limit:
        steps += 1
        current = stack.pop()
        for link in current.links:
            if link.to_socket == target_socket:
                return True
            node = link.to_node
            if node.name in seen and node.type != 'GROUP':
                continue
            seen.add(node.name)
            if node.type == 'GROUP':
                outputs = [o for o in node.outputs if o.name == link.to_socket.name] or list(node.outputs)
            else:
                outputs = list(node.outputs)
            stack.extend(outputs)
    return False


def inspect_normal_map(material, principled):
    tree = material.node_tree
    normal_input = principled.inputs['Normal'] if principled is not None else None
    detail = {'images': 0, 'image_names': [], 'space': None, 'colourspace': None, 'uv_map': None, 'reaches_normal': False, 'strength': None,
              'bump_leftover': 0.0, 'has_uv_node': any(n.type == 'UVMAP' for n in tree.nodes)}
    nodes = [n for n in tree.nodes if n.type == 'NORMAL_MAP']
    images = {}
    best = None
    for node in nodes:
        sources = [n for n in upstream_nodes(node.inputs['Color']) if n.type == 'TEX_IMAGE' and n.image is not None]
        for source in sources:
            images[source.image.name] = source.image
        reaches_it = normal_input is not None and reaches(node.outputs['Normal'], normal_input)
        if sources and (best is None or (reaches_it and not best['reaches'])):
            best = {'node': node, 'reaches': reaches_it}
    if best is not None:
        node = best['node']
        detail.update(space=node.space, uv_map=node.uv_map or None, reaches_normal=bool(best['reaches']),
                      strength=None if node.inputs['Strength'].links else round(float(node.inputs['Strength'].default_value), 4))
    detail['images'] = len(images)
    detail['image_names'] = sorted(images)
    spaces = {img.colorspace_settings.name for img in images.values()}
    detail['colourspace'] = 'Non-Color' if spaces == {'Non-Color'} else (sorted(spaces)[0] if spaces else None)
    fed = {n.name for node in nodes for n in [node]}
    for bump in [n for n in tree.nodes if n.type == 'BUMP']:
        fed_by_map = any(link.from_node.type == 'NORMAL_MAP' for link in bump.inputs['Normal'].links)
        if not fed_by_map and bump.outputs['Normal'].links:
            strength = 0.0 if bump.inputs['Strength'].links else float(bump.inputs['Strength'].default_value)
            detail['bump_leftover'] = max(detail['bump_leftover'], strength)
    return {'has': best is not None and best['reaches'], 'detail': detail}


def inspect_displacement(material):
    detail = {'node': None, 'method': getattr(material, 'displacement_method', None), 'depth_metres': 0.0,
              'max_vertex_displacement': getattr(material, 'max_vertex_displacement', None), 'mesh': None}
    tree = material.node_tree
    has_node = False
    for output in [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL']:
        for link in output.inputs['Displacement'].links:
            node = link.from_node
            if node.type == 'DISPLACEMENT':
                has_node = True
                detail['node'] = node.name
                scale = node.inputs['Scale']
                detail['depth_metres'] = 0.0 if scale.links else float(scale.default_value)
                detail['has_height_input'] = bool(node.inputs['Height'].links)
    has = has_node and detail['method'] in ('DISPLACEMENT', 'BOTH') and detail['depth_metres'] > 0 and detail.get('has_height_input', False)
    return {'has': bool(has), 'detail': detail}


def layers_in(material):
    """The wear layers present in the material: {layer key: group node name}, found by the group's name."""
    found = {}
    for node in material.node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree is not None:
            group_name = node.node_tree.name
            for layer in names.LAYER_ORDER:
                if group_name == names.layer_group_name(layer) or group_name.startswith(names.layer_group_name(layer) + '.'):
                    found[layer] = node.name
    return found


def inspect_material(material):
    """Plain facts about one material's treatments (see the note at the top)."""
    result = {'name': material.name, 'has_tree': material.node_tree is not None, 'principled': False, 'glows': False}
    if material.node_tree is None:
        return result
    principled = principled_of(material)
    result['principled'] = principled is not None
    if principled is None:
        result.update(normal_map={'has': False, 'detail': {}}, displacement={'has': False, 'detail': {}}, roughness_variation=False, colour_variation=False, layers={})
        return result
    strength = principled.inputs['Emission Strength']
    colour = principled.inputs['Emission Color']
    result['glows'] = bool(strength.links) or (strength.default_value > 0 and (bool(colour.links) or max(colour.default_value[:3]) > 0))
    result['normal_map'] = inspect_normal_map(material, principled)
    result['displacement'] = inspect_displacement(material)
    result['roughness_variation'] = varies(principled.inputs['Roughness'])
    result['colour_variation'] = varies(principled.inputs['Base Color'])
    result['layers'] = layers_in(material)
    return result
