# What this does (plain words): the honesty checker opens the recipe's node group inside Blender (it only builds it, no picture is made) and reports
# (1) which picture FILES the Image Texture nodes read, (2) whether any node type that could hide an outside picture or a program is used,
# (3) for every height-map reading, whether the colour-map reading takes its position from exactly the same place (same arrangement).
# Use: blender -b --disable-autoexec -t 2 --python inspect_nodes.py -- OUT.json
import collections
import json
import os
import sys

import bpy

CK = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(CK, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402

out_path = sys.argv[sys.argv.index('--') + 1]
recipe = bh.load_recipe(os.path.join(PROC, 'recipes', 'wood_from_displacement', 'recipe', 'wood_from_maps_recipe.py'))
result = {}
for label, params in (('default_tile_main', {}), ('area_4x4_main', {'recipe.tiles_across': 4}), ('default_tile_comparison', {'colour.source': 'height_palette'})):
    bh.new_bake_scene(64)
    group = recipe.build_node_group(dict(params))
    types = collections.Counter(n.bl_idname for n in group.nodes)
    files = collections.Counter()
    tex_nodes = [n for n in group.nodes if n.bl_idname == 'ShaderNodeTexImage']
    for n in tex_nodes:
        files[(os.path.relpath(bpy.path.abspath(n.image.filepath), PROC), n.image.colorspace_settings.name, n.interpolation, n.extension)] += 1

    def source_of(socket):
        """The (node name, output index) feeding this input socket, looking through the divide/subtract Math node that scales the position."""
        if not socket.links:
            return ('constant', float(socket.default_value) if hasattr(socket, 'default_value') else None)
        frm = socket.links[0].from_socket
        node = socket.links[0].from_node
        return (node.name, [o.identifier for o in node.outputs].index(frm.identifier))

    def origin(socket, depth=0):
        """Follow a socket upstream through the plain scaling steps (divide by the picture size, 1 - y) to the first node that is not such a step."""
        if not socket.links:
            return ('constant', round(float(socket.default_value), 6))
        node = socket.links[0].from_node
        frm = socket.links[0].from_socket
        if node.bl_idname == 'ShaderNodeMath' and node.operation in ('DIVIDE', 'SUBTRACT') and depth < 3:
            a, b = node.inputs[0], node.inputs[1]
            # divide: (position) / size ; subtract: 1 - (position / size). Keep the side that is a link or the non-trivial one.
            if node.operation == 'DIVIDE':
                return ('div', origin(a, depth + 1), round(float(b.default_value), 3) if not b.links else 'linked')
            return ('sub', round(float(a.default_value), 3) if not a.links else origin(a, depth + 1), origin(b, depth + 1))
        return (node.name, [o.identifier for o in node.outputs].index(frm.identifier))

    def position_key(tex):
        vec = tex.inputs['Vector'].links[0].from_node          # a Combine XYZ
        return (origin(vec.inputs['X']), origin(vec.inputs['Y']))

    pairs = collections.defaultdict(list)
    for tex in tex_nodes:
        pairs[json.dumps(position_key(tex))].append((os.path.basename(tex.image.filepath), tex.image.colorspace_settings.name))
    shared = [{'files_read_at_this_one_place': v} for k, v in pairs.items()]
    result[label] = {'nodes': len(group.nodes), 'node_types': dict(types), 'image_texture_nodes': len(tex_nodes),
                     'picture_files_read': [{'file': k[0], 'colour_space': k[1], 'interpolation': k[2], 'extension': k[3], 'nodes': v} for k, v in files.items()],
                     'places_read': len(pairs), 'places_where_height_and_colour_are_both_read': sum(1 for v in pairs.values() if len(v) == 2),
                     'places_read_by_only_one_map': [v for v in pairs.values() if len(v) != 2], 'script_nodes': types.get('ShaderNodeScript', 0),
                     'all_images_in_blend_data': sorted(os.path.relpath(bpy.path.abspath(i.filepath), PROC) for i in bpy.data.images if i.filepath)}
with open(out_path, 'w') as handle:
    json.dump(result, handle, indent=1)
print('[inspect] done')
