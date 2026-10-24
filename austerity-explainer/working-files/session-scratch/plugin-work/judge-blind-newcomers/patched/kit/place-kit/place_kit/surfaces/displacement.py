"""What this does: switches a material to REAL displacement where its role says so (roads, mud, thatch, rock ground), and makes sure the mesh under it is
fine enough to show it. A Displacement node reads the surface's height picture (mid level 0.5, scale = the true depth in metres) and feeds the material
output's Displacement; the material's method is set to "Displacement and Bump" (never Bump Only, where the node does nothing); the normal map's strength is
multiplied by 0.6 where displacement is on (decision D7 of the 1.4.0 design: an earlier test yard did this; the cookbook measured no doubling). If the mesh is
too coarse (edges longer than the house number) a ground object is regraded (ground_mesh.py) and anything else gets a Subdivision Surface modifier that
makes it dense enough. It refuses to claim displacement on a flat plane: the audit reads the same facts and fails it.
It needs Blender (bpy). A concrete example: set_displacement(material, height_node_output, depth=0.06) wires the node and sets the method to BOTH.
"""
import math

import bpy

from .. import house_numbers, names, scene_read

ENABLED_METHODS = ('DISPLACEMENT', 'BOTH')


def set_displacement(material, height_socket, depth_metres, tree=None):
    """Wires a Displacement node from a height socket into the material output and sets the method. Returns the node."""
    tree = tree or material.node_tree
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    for link in list(output.inputs['Displacement'].links):
        tree.links.remove(link)
    node = tree.nodes.new('ShaderNodeDisplacement')
    node.name = node.label = 'PK Displacement'
    node.inputs['Midlevel'].default_value = 0.5
    node.inputs['Scale'].default_value = float(depth_metres)
    tree.links.new(height_socket, node.inputs['Height'])
    tree.links.new(node.outputs['Displacement'], output.inputs['Displacement'])
    material.displacement_method = 'BOTH'
    material.max_vertex_displacement = float(depth_metres)
    return node


def levels_needed(mean_edge, limit):
    """How many Subdivision Surface levels bring an edge of mean_edge metres down to the limit (each level halves it)."""
    if mean_edge <= limit or mean_edge <= 0:
        return 0
    return int(min(6, math.ceil(math.log2(mean_edge / limit))))


def prepare_mesh(obj, near_xy=None):
    """Makes the mesh dense enough for displacement. Returns a short plain sentence saying what was done (or why nothing was)."""
    from . import ground_mesh
    limit = house_numbers.value('place_surfaces.displacement_mesh_edge_metres_max')
    if (obj.get(names.ROLE) or '').startswith('ground.'):
        report = ground_mesh.regrade_object(obj, near_xy)
        if report:
            return f'{obj.name}: regraded to {report["faces"]} faces (squares of {report["near_cell"]} m near the camera)'
        return f'{obj.name}: the ground mesh is already fine'
    mean_edge = scene_read.mean_edge_length(obj)
    levels = levels_needed(mean_edge, limit)
    for modifier in list(obj.modifiers):
        if modifier.name == names.DISPLACE_SUBDIVIDE_MODIFIER:
            obj.modifiers.remove(modifier)
    if levels == 0:
        return f'{obj.name}: already fine enough ({mean_edge:.2f} m edges)'
    modifier = obj.modifiers.new(names.DISPLACE_SUBDIVIDE_MODIFIER, 'SUBSURF')
    modifier.subdivision_type = 'SIMPLE'
    modifier.levels = min(levels, 2)
    modifier.render_levels = levels
    return f'{obj.name}: subdivided {levels} level(s) at render time ({mean_edge:.2f} m edges before)'
