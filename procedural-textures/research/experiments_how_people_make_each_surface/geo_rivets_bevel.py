# What this does: TEST of the geometry route for riveted metal that many artists describe: real boxes for the straps, real domed rivets placed
# with Mesh Line points + Instance on Points, then the Bevel shader node as the "edge wear" mask (the mask is where the bevelled shading normal
# differs from the true normal). Photographs the plate from straight above as: height (Z), edge-wear mask, and a plain "is it a rivet" mask.
# Run: blender -b --disable-autoexec -t 2 --python geo_rivets_bevel.py -- OUT_FOLDER [--size 512]
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
size = int(args[args.index('--size') + 1]) if '--size' in args else 512
os.makedirs(out, exist_ok=True)
scene = gh.new_overhead_scene(size)
g = gh.GeoBuilder('rivets')
# straps: two boxes (vertical strap and horizontal strap), each 0.01 thick
v_box = g.make('GeometryNodeMeshCube', 'Mesh', Size=(0.11, 1.4, 0.012))
v_strap = g.make('GeometryNodeTransform', 'Geometry', Geometry=v_box, Translation=(0.30, 0.5, 0.006))
h_box = g.make('GeometryNodeMeshCube', 'Mesh', Size=(1.4, 0.09, 0.012))
h_strap = g.make('GeometryNodeTransform', 'Geometry', Geometry=h_box, Translation=(0.5, 0.62, 0.0075))
# rivet: a flattened UV sphere
sphere = g.make('GeometryNodeMeshUVSphere', 'Mesh', Radius=0.019, Segments=16, Rings=8)
dome = g.make('GeometryNodeTransform', 'Geometry', Geometry=sphere, Scale=(1.0, 1.0, 0.6))
rivet = g.make('GeometryNodeSetMaterial', 'Geometry', Geometry=dome)
# rows of rivets along the straps (Mesh Line points)
line_v = g.make('GeometryNodeMeshLine', 'Mesh', Count=8, Start__Location=(0.30, 0.0625, 0.014), Offset=(0.0, 0.125, 0.0))
line_h = g.make('GeometryNodeMeshLine', 'Mesh', Count=8, Start__Location=(0.0625, 0.62, 0.0145), Offset=(0.125, 0.0, 0.0))
join_lines = g.node('GeometryNodeJoinGeometry')
g.tree.links.new(line_v, join_lines.inputs['Geometry'])
g.tree.links.new(line_h, join_lines.inputs['Geometry'])
points = g.make('GeometryNodeMeshToPoints', 'Points', Mesh=join_lines.outputs['Geometry'], Radius=0.01)
rivets = g.make('GeometryNodeInstanceOnPoints', 'Instances', Points=points, Instance=rivet)
realized = g.make('GeometryNodeRealizeInstances', 'Geometry', Geometry=rivets)
straps_set = g.node('GeometryNodeSetMaterial')
join_straps = g.node('GeometryNodeJoinGeometry')
g.tree.links.new(v_strap, join_straps.inputs['Geometry'])
g.tree.links.new(h_strap, join_straps.inputs['Geometry'])
g.tree.links.new(join_straps.outputs['Geometry'], straps_set.inputs['Geometry'])
everything = g.node('GeometryNodeJoinGeometry')
g.tree.links.new(straps_set.outputs['Geometry'], everything.inputs['Geometry'])
g.tree.links.new(realized, everything.inputs['Geometry'])
tree = g.finish(everything.outputs['Geometry'])
obj, modifier = gh.add_object_with_tree('plate parts', tree)
plane_mesh = bpy.data.meshes.new('plate')
plane_mesh.from_pydata([(-1, -1, 0), (2, -1, 0), (2, 2, 0), (-1, 2, 0)], [], [(0, 1, 2, 3)])
plane = bpy.data.objects.new('plate', plane_mesh)
scene.collection.objects.link(plane)


def edge_mask_material(radius):
    def build(tree):
        bevel = tree.nodes.new('ShaderNodeBevel')
        bevel.inputs['Radius'].default_value = radius
        bevel.samples = 16
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        dot = tree.nodes.new('ShaderNodeVectorMath')
        dot.operation = 'DOT_PRODUCT'
        tree.links.new(bevel.outputs['Normal'], dot.inputs[0])
        tree.links.new(geometry.outputs['True Normal'], dot.inputs[1])
        invert = tree.nodes.new('ShaderNodeMath')
        invert.operation = 'SUBTRACT'
        invert.inputs[0].default_value = 1.0
        tree.links.new(dot.outputs['Value'], invert.inputs[1])
        scale = tree.nodes.new('ShaderNodeMath')
        scale.operation = 'MULTIPLY'
        scale.use_clamp = True
        scale.inputs[1].default_value = 14.0
        tree.links.new(invert.outputs[0], scale.inputs[0])
        grey = tree.nodes.new('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            tree.links.new(scale.outputs[0], grey.inputs[socket])
        return grey.outputs[0]
    return gh.emission_material('edge mask %.4f' % radius, build)


facts = {}
height = gh.height_material(0.0, 0.03)
for target in (straps_set.outputs[0], rivet):
    pass
# materials: straps via the Set Material node on the strap group, rivets via the one on the dome, plate via the object slot
for name, material in (('height', height), ('edge_mask_r004', edge_mask_material(0.004)), ('edge_mask_r010', edge_mask_material(0.010))):
    straps_set.inputs['Material'].default_value = material
    gh.use_material(rivet, material)
    gh.set_material(plane, material)
    gh.render_picture(scene, os.path.join(out, name + '.png'), sixteen_bit=(name == 'height'), linear=True)
print('FACTS ok')
