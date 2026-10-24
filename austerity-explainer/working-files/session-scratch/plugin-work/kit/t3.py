import bpy, sys, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
print('engines', [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
bpy.ops.mesh.primitive_cube_add(size=2)
ob = bpy.context.active_object
me = ob.data
print('has loop_triangles', hasattr(me, 'loop_triangles'), 'corner_tris', hasattr(me, 'corner_tris'))
me.calc_loop_triangles()
print('tris', len(me.loop_triangles) if hasattr(me,'loop_triangles') else None)
mat = bpy.data.materials.new('m'); mat.use_nodes = True
print('disp method attr', hasattr(mat, 'displacement_method'), hasattr(mat.cycles, 'displacement_method') if hasattr(mat,'cycles') else None)
print([a for a in dir(mat) if 'disp' in a.lower()])
print('cycles mat', [a for a in dir(mat.cycles) if 'disp' in a.lower()] if hasattr(mat,'cycles') else None)
img = bpy.data.images.new('t', 8, 8, alpha=False, float_buffer=False)
img.colorspace_settings.name = 'Non-Color'
img.pixels.foreach_set(np.ones(8*8*4, np.float32)*0.5)
try:
    img.pack(); print('pack ok', img.packed_file is not None)
except Exception as e: print('pack failed', e)
b = ob.modifiers.new('b', 'BEVEL')
print('bevel attrs', [a for a in dir(b) if 'harden' in a or 'normal' in a or 'segments' in a or 'limit' in a])
w = ob.modifiers.new('w','WEIGHTED_NORMAL'); print('wn ok', w.type)
print('subsurf', [a for a in dir(ob.modifiers.new('s','SUBSURF')) if 'level' in a or 'subsurf' in a])
print('cycles', [a for a in dir(sc.cycles) if a in ('device','samples','use_denoising','denoiser','adaptive_threshold','use_adaptive_sampling','feature_set','use_light_tree','denoising_input_passes')])
print('eevee', [a for a in dir(sc.eevee) if 'shadow' in a or 'taa' in a or 'ray' in a][:20])
print('view_settings', sc.view_settings.view_transform, [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items])
n = mat.node_tree.nodes
for t in ('ShaderNodeNormalMap','ShaderNodeDisplacement','ShaderNodeBump','ShaderNodeTexVoronoi','ShaderNodeMix','ShaderNodeMapRange','ShaderNodeAttribute','ShaderNodeTexCoord','ShaderNodeUVMap','ShaderNodeMapping','ShaderNodeTexNoise','ShaderNodeTexImage','ShaderNodeTexWave','ShaderNodeValToRGB','ShaderNodeGroup','ShaderNodeCombineXYZ','ShaderNodeSeparateXYZ','ShaderNodeVectorMath','ShaderNodeMath','ShaderNodeNewGeometry','ShaderNodeObjectInfo','ShaderNodeRGB','ShaderNodeValue','ShaderNodeBsdfPrincipled','ShaderNodeOutputMaterial','ShaderNodeEmission','ShaderNodeLightPath','ShaderNodeHueSaturation','ShaderNodeBrightContrast','ShaderNodeTexGradient'):
    try:
        nn = n.new(t); print('ok', t, [i.identifier for i in nn.inputs][:6])
    except Exception as e:
        print('NO', t, e)
vor = [x for x in n if x.bl_idname=='ShaderNodeTexVoronoi'][0]
print('voronoi features', [i.identifier for i in vor.bl_rna.properties['feature'].enum_items], vor.voronoi_dimensions if hasattr(vor,'voronoi_dimensions') else vor.bl_rna.properties.keys())
print('math ops sample', 'GREATER_THAN' in [i.identifier for i in n['Math'].bl_rna.properties['operation'].enum_items])
