# Does an Attribute node read an OBJECT custom property in EEVEE and Cycles? (and in what spelling)
import bpy, sys, json, numpy as np, os
out = sys.argv[sys.argv.index('--')+1]
scene = bpy.context.scene
road = bpy.data.objects['street_setts']
road['wk_seed'] = 0.37
road['wk_plain'] = 0.62
mat = bpy.data.materials.new('attr_probe'); mat.use_nodes = True
t = mat.node_tree; t.nodes.clear()
outn = t.nodes.new('ShaderNodeOutputMaterial'); em = t.nodes.new('ShaderNodeEmission'); comb = t.nodes.new('ShaderNodeCombineColor')
a1 = t.nodes.new('ShaderNodeAttribute'); a1.attribute_type = 'OBJECT'; a1.attribute_name = 'wk_seed'
a2 = t.nodes.new('ShaderNodeAttribute'); a2.attribute_type = 'OBJECT'; a2.attribute_name = '["wk_plain"]'
a3 = t.nodes.new('ShaderNodeAttribute'); a3.attribute_type = 'OBJECT'; a3.attribute_name = 'wk_missing'
t.links.new(a1.outputs['Fac'], comb.inputs['Red']); t.links.new(a2.outputs['Fac'], comb.inputs['Green']); t.links.new(a3.outputs['Fac'], comb.inputs['Blue'])
t.links.new(comb.outputs['Color'], em.inputs['Color']); t.links.new(em.outputs['Emission'], outn.inputs['Surface'])
bpy.context.view_layer.material_override = mat
scene.view_settings.view_transform = 'Raw'; scene.view_settings.look = 'None'
scene.render.resolution_x, scene.render.resolution_y = 96, 160
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_depth = '16'
bg = scene.world.node_tree.nodes['Background']; bg.inputs['Strength'].default_value = 0.0
res = {}
for eng in ('BLENDER_EEVEE', 'CYCLES'):
    scene.render.engine = eng
    if eng == 'CYCLES':
        scene.cycles.samples = 1; scene.cycles.device = 'CPU'; scene.cycles.use_denoising = False
    else:
        scene.eevee.taa_render_samples = 1
    p = os.path.join(out, eng + '.png'); scene.render.filepath = p
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p); img.colorspace_settings.name = 'Non-Color'
    px = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
    # centre-bottom area is road
    patch = px[20:60, 30:66, :3].reshape(-1, 3)
    res[eng] = [round(float(patch[:, i].mean()), 4) for i in range(3)]
    bpy.data.images.remove(img)
print('ATTR_RESULT', json.dumps(res))
json.dump(res, open(os.path.join(out, 'attr_result.json'), 'w'))
