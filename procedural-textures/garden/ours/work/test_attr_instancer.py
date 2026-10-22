# Does an Attribute node read a custom property of the INSTANCING object (a geometry-nodes parent) for instances of a prototype that is not in the scene?
import bpy, sys, numpy as np
engine = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'CYCLES'
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = engine
sc.render.resolution_x = 32; sc.render.resolution_y = 32; sc.render.resolution_percentage = 100
if engine == 'CYCLES':
    sc.cycles.device = 'CPU'; sc.cycles.samples = 1; sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0
else:
    sc.eevee.taa_render_samples = 1
sc.view_settings.view_transform = 'Standard'
# world black, no lights: emission only
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
def make_mat(name, attr_type):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = attr_type; at.attribute_name = 'wk_test'
    comb = nt.nodes.new('ShaderNodeCombineColor')
    for i in range(3): nt.links.new(at.outputs['Fac'], comb.inputs[i])
    nt.links.new(comb.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m
# prototype object: a quad, NOT linked to the scene
me = bpy.data.meshes.new('protoMesh'); me.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)], [], [(0,1,2,3)])
proto = bpy.data.objects.new('PROTO', me)
results = {}
for attr_type in ('OBJECT', 'INSTANCER'):
    for case in ('instancer_has_value', 'proto_has_value', 'neither', 'plain_object'):
        # clean scene objects
        for o in list(sc.objects): bpy.data.objects.remove(o, do_unlink=True)
        for k in list(proto.keys()): del proto[k]
        mat = make_mat('m_'+attr_type, attr_type)
        proto.data.materials.clear(); proto.data.materials.append(mat)
        cam_d = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam)
        cam.location = (0, 0, 3); cam.rotation_euler = (0, 0, 0); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 2.0; sc.camera = cam
        if case == 'plain_object':
            holder = bpy.data.objects.new('HOLDER', bpy.data.meshes.new('hm')); holder.data.from_pydata([(-.9,-.9,0),(.9,-.9,0),(.9,.9,0),(-.9,.9,0)], [], [(0,1,2,3)])
            holder.data.materials.append(mat); sc.collection.objects.link(holder); holder['wk_test'] = 0.8
        else:
            holder = bpy.data.objects.new('HOLDER', bpy.data.meshes.new('hm')); sc.collection.objects.link(holder)
            tree = bpy.data.node_groups.new('gn', 'GeometryNodeTree')
            tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry'); tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
            gi = tree.nodes.new('NodeGroupInput'); go = tree.nodes.new('NodeGroupOutput')
            pt = tree.nodes.new('GeometryNodeMeshGrid'); pt.inputs['Size X'].default_value = 0.0; pt.inputs['Size Y'].default_value = 0.0
            pt.inputs['Vertices X'].default_value = 1; pt.inputs['Vertices Y'].default_value = 1
            m2p = tree.nodes.new('GeometryNodeMeshToPoints')
            oi = tree.nodes.new('GeometryNodeObjectInfo'); oi.transform_space = 'RELATIVE'; oi.inputs['Object'].default_value = proto
            sc_ = tree.nodes.new('GeometryNodeScaleInstances') if False else None
            iop = tree.nodes.new('GeometryNodeInstanceOnPoints')
            tree.links.new(pt.outputs['Mesh'], m2p.inputs['Mesh'])
            tree.links.new(m2p.outputs['Points'], iop.inputs['Points'])
            tree.links.new(oi.outputs['Geometry'], iop.inputs['Instance'])
            tree.links.new(iop.outputs['Instances'], go.inputs['Geometry'])
            md = holder.modifiers.new('gn', 'NODES'); md.node_group = tree
            if case == 'instancer_has_value': holder['wk_test'] = 0.8
            if case == 'proto_has_value': proto['wk_test'] = 0.6
        bpy.context.view_layer.update()
        sc.render.filepath = '//t.png'
        img_path = bpy.app.tempdir + 'attr_test.png'
        sc.render.filepath = img_path
        sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(img_path)
        px = np.array(im.pixels[:]).reshape(32, 32, 4)
        results[(attr_type, case)] = round(float(px[16, 16, 0]), 3)
        bpy.data.images.remove(im)
for k, v in results.items(): print('RESULT', engine, k, v)
