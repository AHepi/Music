"""What this does: builds the shader node group "PK Plan", the ONE place where a material asks "what is here?": it turns the world position of the spot being
shaded into a look-up in the five plan-mask pictures (lowness, crown, footfall, keep-clear, distance to walls and props, sheltered, shade, dampness, above water,
distance to litter, wheel track, distance to a verge and to a joint, and how much of another ground surface is near with its colour) and adds the facts only the object itself knows: how high the spot is above the object's OWN lowest point (a wall's foot starts at
its own base, not at the ground: a stone plinth 15 to 46 cm high once hid the foot band), how far up the object it is (a share of its height), how far it is from the
object's own edges (from the object's bounds: no Bevel or Ambient Occlusion node, which differ or fail in EEVEE), and whether the surface faces up.
Every wear layer reads these through its mask inputs; each material has one Plan node and the chain wires the masks by name. Needs Blender (bpy).
A concrete example: the layer "grime" asks for "M Sheltered" and "M Height Share"; the chain links them from the Plan node's outputs "Sheltered" and "Height Share".
"""
import bpy

from .. import names
from . import masks
from .nodes import Net, new_group

OUTPUTS = ['Lowness', 'Crown', 'Footfall', 'Keepclear', 'Wall Dist', 'Prop Dist', 'Sheltered', 'Shade', 'Dampness', 'Above Water', 'Litter Dist', 'Track',
           'Height Above Foot', 'Height Share', 'Edge Dist', 'Up', 'Verge Dist', 'Joint Dist', 'Seam Blend', 'Seam R', 'Seam G', 'Seam B']
SOCKET_OF_MASK = {'lowness': 'Lowness', 'crown': 'Crown', 'footfall': 'Footfall', 'keepclear': 'Keepclear', 'wall_dist': 'Wall Dist', 'prop_dist': 'Prop Dist', 'sheltered': 'Sheltered',
                  'shade': 'Shade', 'dampness': 'Dampness', 'above_water': 'Above Water', 'litter_dist': 'Litter Dist', 'track': 'Track', 'verge_dist': 'Verge Dist',
                  'joint_dist': 'Joint Dist', 'seam_blend': 'Seam Blend', 'seam_r': 'Seam R', 'seam_g': 'Seam G', 'seam_b': 'Seam B'}
PICTURE_CHANNELS = (('a', ('Lowness', 'Crown', 'Footfall', 'Keepclear')), ('b', ('Wall Dist', 'Prop Dist', 'Sheltered', 'Shade')),
                    ('c', ('Dampness', 'Above Water', 'Litter Dist', 'Track')), ('d', ('Verge Dist', 'Joint Dist', 'Seam Blend', 'Grows')),
                    ('e', ('Seam R', 'Seam G', 'Seam B', 'Unpaved')))
BOUND_INPUTS = ['Min X', 'Min Y', 'Size X', 'Size Y']


def build_plan_group():
    """(Re)builds the group in place so material nodes that use it keep working. Returns the group's node tree."""
    group = bpy.data.node_groups.get(names.PLAN_GROUP)
    if group is None:
        tree, group_in, group_out = new_group(names.PLAN_GROUP, [(b, 'NodeSocketFloat', 0.0) for b in BOUND_INPUTS], [(o, 'NodeSocketFloat') for o in OUTPUTS])
    else:
        tree = group
        tree.nodes.clear()
        have = {item.name for item in tree.interface.items_tree if getattr(item, 'in_out', None) == 'OUTPUT'}
        for name in OUTPUTS:                     # a group made by an older kit lacks the newer outputs: they are added, the old wires keep working
            if name not in have:
                tree.interface.new_socket(name, in_out='OUTPUT', socket_type='NodeSocketFloat')
        group_in = tree.nodes.new('NodeGroupInput')
        group_out = tree.nodes.new('NodeGroupOutput')
        group_in.location, group_out.location = (-400, 0), (3200, 0)
    net = Net(tree)
    def group_input(name):
        return group_in.outputs[name]
    geometry = net.geometry()
    x, y, z = net.separate(geometry.outputs['Position'])
    u = net.math('DIVIDE', net.math('SUBTRACT', x, group_input('Min X')), net.math('MAXIMUM', group_input('Size X'), 0.001))
    v = net.math('DIVIDE', net.math('SUBTRACT', y, group_input('Min Y')), net.math('MAXIMUM', group_input('Size Y'), 0.001))
    coordinate = net.combine(u, v, 0.0)
    values = {}
    for which, channels in PICTURE_CHANNELS:
        image = bpy.data.images.get(names.plan_image_name(which))
        node = net.new('ShaderNodeTexImage')
        node.image = image
        node.interpolation = 'Linear'
        node.extension = 'EXTEND'
        tree.links.new(coordinate, node.inputs['Vector'])
        red, green, blue = net.sep_rgb(node.outputs['Color'])
        for name, socket in zip(channels, (red, green, blue, node.outputs['Alpha'])):
            values[name] = socket
    # distances are stored as shares of their longest distance
    out = {name: values[name] for name in ('Lowness', 'Crown', 'Footfall', 'Keepclear', 'Sheltered', 'Shade', 'Dampness', 'Above Water', 'Track', 'Seam Blend', 'Seam R', 'Seam G', 'Seam B')}
    out['Verge Dist'] = net.math('MULTIPLY', values['Verge Dist'], masks.DISTANCE_SCALE['verge_dist'])
    out['Joint Dist'] = net.math('MULTIPLY', values['Joint Dist'], masks.DISTANCE_SCALE['joint_dist'])
    out['Wall Dist'] = net.math('MULTIPLY', values['Wall Dist'], masks.DISTANCE_SCALE['wall_dist'])
    out['Prop Dist'] = net.math('MULTIPLY', values['Prop Dist'], masks.DISTANCE_SCALE['prop_dist'])
    out['Litter Dist'] = net.math('MULTIPLY', values['Litter Dist'], masks.DISTANCE_SCALE['litter_dist'])
    # the object's own facts
    zmin, height = net.attr(names.BOTTOM_Z), net.attr(names.HEIGHT)
    above_foot = net.math('MAXIMUM', net.math('SUBTRACT', z, zmin), 0.0)
    out['Height Above Foot'] = above_foot
    out['Height Share'] = net.clamp01(net.math('DIVIDE', above_foot, net.math('MAXIMUM', height, 0.01)))
    generated = net.new('ShaderNodeTexCoord')
    gx, gy, gz = net.separate(generated.outputs['Generated'])
    nx, ny, nz = net.separate(generated.outputs['Normal'])
    sizes = [net.attr('pk_size_x'), net.attr('pk_size_y'), net.attr('pk_size_z')]
    distances = []
    for coordinate_value, normal_component, size in zip((gx, gy, gz), (nx, ny, nz), sizes):
        to_edge = net.math('MULTIPLY', net.math('MINIMUM', coordinate_value, net.math('SUBTRACT', 1.0, coordinate_value)), net.math('MAXIMUM', size, 0.001))
        ignore = net.math('MULTIPLY', net.math('MULTIPLY', normal_component, normal_component), 100.0)         # an axis the face looks along says nothing about its edges
        distances.append(net.math('ADD', to_edge, ignore))
    out['Edge Dist'] = net.math('MINIMUM', distances[0], net.math('MINIMUM', distances[1], distances[2]))
    world_normal = net.separate(geometry.outputs['Normal'])
    out['Up'] = net.clamp01(world_normal[2])
    for name in OUTPUTS:
        tree.links.new(out[name], group_out.inputs[name])
    return tree


def set_bounds(node, plan_masks):
    """Writes the plan masks' bounds into a Plan group node's inputs."""
    x0, y0, x1, y1 = plan_masks.bounds
    for name, value in (('Min X', x0), ('Min Y', y0), ('Size X', x1 - x0), ('Size Y', y1 - y0)):
        node.inputs[name].default_value = float(value)
