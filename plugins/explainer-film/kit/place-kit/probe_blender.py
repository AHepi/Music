"""What this does: a small probe of the installed Blender for two Blender 5.2 traps, run inside Blender by explainer-film-setup, so a model
writing its own Blender code knows which way works on THIS machine before it loses a round:
  1. Geometry Nodes modifier inputs. In Blender 5.2 they are set through mod.properties.inputs.<identifier>.value; the older
     mod[identifier] = value (Blender 4 and 5.1) stops with a TypeError. An add-on written for 5.1 broke this way.
  2. Light linking. In Blender 5.2 a collection's light-linking entries (collection.collection_objects) do not name their object: pair them
     with collection.objects in the same order.
It builds a tiny scene in memory (one triangle, one node group with one number input, one lamp, a collection of two objects), tries both
ways, reads what came back, prints plain lines and writes the same as JSON when an output file is given. It saves nothing.
Run: blender -b --disable-autoexec --python probe_blender.py -- [OUT.json]
A concrete example (Blender 5.2.2): "Geometry Nodes inputs: mod.properties.inputs.Socket_1.value works; mod['Socket_1'] does not (TypeError)".
"""
import json
import sys

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if '--help' in arguments or '-h' in arguments or (__name__ == '__main__' and ('--help' in sys.argv[1:] or '-h' in sys.argv[1:])):
    print(__doc__)                      # --help works inside Blender (after --) and with plain Python, where there is no bpy
    sys.exit(0)

import bpy  # noqa: E402  (only inside Blender)

out_path = next((a for a in arguments if not a.startswith('-')), None)
result = {'blender': bpy.app.version_string}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
mesh = bpy.data.meshes.new('probe triangle')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
probe = bpy.data.objects.new('probe', mesh)
scene.collection.objects.link(probe)

# 1. a Geometry Nodes modifier input, both ways
tree = bpy.data.node_groups.new('probe group', 'GeometryNodeTree')
tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
size = tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
group_in, group_out = tree.nodes.new('NodeGroupInput'), tree.nodes.new('NodeGroupOutput')
tree.links.new(group_in.outputs[0], group_out.inputs[0])
modifier = probe.modifiers.new('probe', 'NODES')
modifier.node_group = tree
identifier = size.identifier
ways = {}
try:
    getattr(modifier.properties.inputs, identifier).value = 2.5
    ways['properties'] = abs(getattr(modifier.properties.inputs, identifier).value - 2.5) < 1e-6
    ways['properties_note'] = '' if ways['properties'] else 'set, but the value did not come back'
except Exception as problem:            # noqa: BLE001  (any failure is the answer)
    ways['properties'], ways['properties_note'] = False, f'{type(problem).__name__}: {problem}'
try:
    modifier[identifier] = 3.5
    ways['item'] = abs(float(modifier[identifier]) - 3.5) < 1e-6
    ways['item_note'] = '' if ways['item'] else 'set, but the value did not come back'
except Exception as problem:            # noqa: BLE001
    ways['item'], ways['item_note'] = False, f'{type(problem).__name__}'
result['geometry_nodes_inputs'] = dict(ways, identifier=identifier)

# 2. a collection's light-linking entries: do they name their object?
receivers = bpy.data.collections.new('probe receivers')
scene.collection.children.link(receivers)
first, second = bpy.data.objects.new('probe A', mesh), bpy.data.objects.new('probe B', mesh)
receivers.objects.link(first)
receivers.objects.link(second)
lamp = bpy.data.objects.new('probe lamp', bpy.data.lights.new('probe lamp', 'POINT'))
scene.collection.objects.link(lamp)
linking = {}
try:
    lamp.light_linking.receiver_collection = receivers
    entries = list(receivers.collection_objects)
    entries[1].light_linking.link_state = 'EXCLUDE'
    named = [name for name in ('object', 'id', 'name') if hasattr(entries[0], name)]
    linking = {'entries': len(entries), 'entries_name_their_object': bool(named), 'fields': [a for a in dir(entries[0]) if not a.startswith('_')],
               'paired_by_order': [o.name for o in receivers.objects], 'states': [e.light_linking.link_state for e in entries],
               'second_object_excluded': entries[1].light_linking.link_state == 'EXCLUDE'}
except Exception as problem:            # noqa: BLE001
    linking = {'error': f'{type(problem).__name__}: {problem}'}
result['light_linking'] = linking

lines = [f'Blender 5.2 probe (Blender {result["blender"]}):']
gn = result['geometry_nodes_inputs']
works = [w for w, ok in ((f'mod.properties.inputs.{identifier}.value', gn['properties']), (f'mod[\'{identifier}\']', gn['item'])) if ok]
fails = [f'{w} ({note})' if note else w for w, ok, note in ((f'mod.properties.inputs.{identifier}.value', gn['properties'], gn['properties_note']),
                                                            (f'mod[\'{identifier}\']', gn['item'], gn['item_note'])) if not ok]
lines.append(f'  Geometry Nodes inputs: {" and ".join(works) or "neither way"} works' + (f'; {", ".join(fails)} does not' if fails else '')
             + ('. Write the first way.' if gn['properties'] and not gn['item'] else '.'))
if 'error' in linking:
    lines.append(f'  light linking: could not be tried ({linking["error"]})')
elif linking.get('entries_name_their_object'):
    lines.append('  light linking: a collection\'s light-linking entries name their object here')
else:
    lines.append(f'  light linking: a collection\'s light-linking entries do not name their object (they hold only {", ".join(f for f in linking["fields"] if f not in ("bl_rna", "rna_type", "bl_system_properties_get"))}): '
                 f'pair them with collection.objects in the same order ({", ".join(linking["paired_by_order"])} -> {", ".join(linking["states"])})')
print('\n'.join(lines))
if out_path:
    with open(out_path, 'w', encoding='utf-8') as handle:
        json.dump(dict(result, lines=lines), handle, indent=1)
