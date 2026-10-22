import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 1; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = 400
sc.view_settings.view_transform = 'Raw'
me = bpy.data.meshes.new('p'); me.from_pydata([(-6,-6,0),(6,-6,0),(6,6,0),(-6,6,0)], [], [(0,1,2,3)])
ob = bpy.data.objects.new('p', me); sc.collection.objects.link(ob)
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.ortho_scale = 12
co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); co.location = (0, 0, 5); sc.camera = co
sc.world = bpy.data.worlds.new('w')
def stats(scale, detail, rough):
    m = bpy.data.materials.new('m'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail; nz.inputs['Roughness'].default_value = rough
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], em.inputs['Color']); nt.links.new(em.outputs[0], out.inputs['Surface'])
    me.materials.clear(); me.materials.append(m)
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.filepath = '/tmp/_ns.exr'
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load('/tmp/_ns.exr')
    a = np.empty(400 * 400 * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    a = a.reshape(400, 400, 4)[..., 0]
    return np.percentile(a, [1, 5, 25, 50, 75, 90, 95, 99]).round(3), a.mean().round(3), a.std().round(3)
for (s, d, r) in ((1.9, 1.0, 0.55), (6.5, 2.0, 0.55), (1.5, 1.0, 0.55), (1.7, 1.0, 0.5), (4.2, 2.0, 0.5), (3.0, 3.0, 0.6)):
    print('NOISE', s, d, r, stats(s, d, r))
