# What this does: asks Blender 5.2.2 itself for a list of every shader node and every Geometry Nodes texture/converter node,
# with its settings (and the allowed values of each setting) and its input and output sockets. Writes nodes_shader.json,
# nodes_geometry.json and a short readable summary to nodes_summary.txt. Run: blender -b --disable-autoexec -t 2 --python introspect_nodes.py
import bpy, json, os, sys
OUT = os.path.dirname(os.path.abspath(__file__))

def describe(tree, idname):
    try:
        node = tree.nodes.new(idname)
    except Exception as exc:
        return {'error': str(exc)}
    info = {'bl_idname': idname, 'label': node.bl_label, 'settings': {}, 'inputs': [], 'outputs': []}
    skip = {'rna_type', 'name', 'label', 'location', 'width', 'height', 'dimensions', 'select', 'show_options', 'show_preview', 'hide',
            'mute', 'show_texture', 'bl_idname', 'bl_label', 'bl_description', 'bl_icon', 'bl_static_type', 'bl_width_default',
            'bl_width_min', 'bl_width_max', 'bl_height_default', 'bl_height_min', 'bl_height_max', 'type', 'inputs', 'outputs',
            'internal_links', 'parent', 'color', 'use_custom_color', 'width_hidden', 'location_absolute', 'warning_propagation', 'panel_states', 'color_tag'}
    for prop in node.bl_rna.properties:
        if prop.identifier in skip or prop.identifier.startswith('bl_'):
            continue
        entry = {'type': prop.type}
        try:
            value = getattr(node, prop.identifier)
        except Exception:
            continue
        if prop.type == 'ENUM':
            entry['options'] = [item.identifier for item in prop.enum_items]
            entry['value'] = sorted(value) if isinstance(value, set) else value
        elif prop.type in ('FLOAT', 'INT', 'BOOLEAN', 'STRING'):
            try:
                entry['value'] = list(value) if hasattr(value, '__len__') and not isinstance(value, str) else value
            except Exception:
                pass
        elif prop.type == 'POINTER':
            continue
        info['settings'][prop.identifier] = entry
    for kind, sockets in (('inputs', node.inputs), ('outputs', node.outputs)):
        for socket in sockets:
            item = {'name': socket.name, 'identifier': socket.identifier, 'type': socket.bl_idname.replace('NodeSocket', ''), 'enabled': socket.enabled}
            if hasattr(socket, 'default_value'):
                try:
                    v = socket.default_value
                    item['default'] = [round(x, 4) for x in v] if hasattr(v, '__len__') and not isinstance(v, str) else (round(v, 4) if isinstance(v, float) else v)
                except Exception:
                    pass
            info[kind].append(item)
    tree.nodes.remove(node)
    return info

def all_node_idnames(tree_type_prefix, tree):
    names = []
    for name in dir(bpy.types):
        if name.startswith(tree_type_prefix):
            cls = getattr(bpy.types, name)
            if hasattr(cls, 'bl_rna'):
                names.append(name)
    return sorted(names)

shader_tree = bpy.data.node_groups.new('probe_shader', 'ShaderNodeTree')
geo_tree = bpy.data.node_groups.new('probe_geo', 'GeometryNodeTree')
shader, geometry = {}, {}
for name in all_node_idnames('ShaderNode', shader_tree):
    if name in ('ShaderNode', 'ShaderNodeCustomGroup', 'ShaderNodeTree', 'ShaderNodeOutputAOV'):
        pass
    shader[name] = describe(shader_tree, name)
for name in all_node_idnames('GeometryNode', geo_tree) + all_node_idnames('FunctionNode', geo_tree) + all_node_idnames('ShaderNode', geo_tree):
    geometry[name] = describe(geo_tree, name)
# in a geometry tree only keep what it accepts
json.dump(shader, open(os.path.join(OUT, 'nodes_shader.json'), 'w'), indent=1, default=str)
json.dump(geometry, open(os.path.join(OUT, 'nodes_geometry.json'), 'w'), indent=1, default=str)
lines = [f'Blender {bpy.app.version_string}', '', 'SHADER NODES (shader editor)']
for name, info in sorted(shader.items()):
    if 'error' in info:
        lines.append(f'  {name}: not creatable here ({info["error"][:60]})'); continue
    lines.append(f'  {name}  "{info["label"]}"')
    for key, entry in info['settings'].items():
        lines.append(f'      setting {key} [{entry["type"]}] = {entry.get("value")}' + (f'  options: {entry["options"]}' if 'options' in entry else ''))
    lines.append('      in : ' + ', '.join(f'{s["name"]}({s["type"]}{"" if s["enabled"] else ",hidden"})' for s in info['inputs']))
    lines.append('      out: ' + ', '.join(f'{s["name"]}({s["type"]})' for s in info['outputs']))
lines += ['', 'GEOMETRY NODES: nodes that exist there']
for name, info in sorted(geometry.items()):
    if 'error' in info:
        continue
    lines.append(f'  {name}  "{info["label"]}"')
open(os.path.join(OUT, 'nodes_summary.txt'), 'w').write('\n'.join(lines))
print('shader nodes:', len(shader), 'ok:', sum('error' not in v for v in shader.values()))
print('geometry nodes ok:', sum('error' not in v for v in geometry.values()))
