import bpy, sys, json, os, numpy as np
out=sys.argv[sys.argv.index('--')+1]; os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=1024; sc.render.resolution_y=1
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'; sc.render.image_settings.color_depth='32' if False else '16'
sc.view_settings.view_transform='Raw'; sc.view_settings.look='None'; sc.eevee.taa_render_samples=1
bpy.ops.mesh.primitive_plane_add(size=2); plane=bpy.context.object
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=2; co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); co.location=(0,0,5); sc.camera=co
mat=bpy.data.materials.new('m'); mat.use_nodes=True; plane.data.materials.append(mat); t=mat.node_tree; t.nodes.clear()
geo=t.nodes.new('ShaderNodeNewGeometry'); sep=t.nodes.new('ShaderNodeSeparateXYZ')
m1=t.nodes.new('ShaderNodeMath'); m1.operation='MULTIPLY'; m1.inputs[1].default_value=512.0   # x in -1..1 -> -512..512
m2=t.nodes.new('ShaderNodeMath'); m2.operation='FLOOR'
add=t.nodes.new('ShaderNodeMath'); add.operation='ADD'; add.inputs[1].default_value=512.0   # 0..1024: whole numbers
wn=t.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions='1D'
comb=t.nodes.new('ShaderNodeCombineColor'); sepc=t.nodes.new('ShaderNodeSeparateColor')
em=t.nodes.new('ShaderNodeEmission'); o=t.nodes.new('ShaderNodeOutputMaterial')
L=t.links
L.new(geo.outputs['Position'],sep.inputs[0]); L.new(sep.outputs['X'],m1.inputs[0]); L.new(m1.outputs[0],add.inputs[0]); L.new(add.outputs[0],m2.inputs[0]); L.new(m2.outputs[0],wn.inputs['W'])
L.new(wn.outputs['Value'],comb.inputs['Red']); L.new(sepc.outputs['Red'],comb.inputs['Green'])
L.new(wn.outputs['Color'],sepc.inputs['Color']); L.new(sepc.outputs['Green'],comb.inputs['Blue'])
L.new(comb.outputs['Color'],em.inputs['Color']); L.new(em.outputs[0],o.inputs['Surface'])
sc.render.filepath=f'{out}/w.png'; bpy.ops.render.render(write_still=True)
img=bpy.data.images.load(f'{out}/w.png'); img.colorspace_settings.name='Non-Color'
a=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)
v=a[:,0]; g=a[:,1]; b=a[:,2]
def ac(x): 
    x=x-x.mean(); return float((x[:-1]*x[1:]).mean()/x.var())
print('WHITE value mean %.3f sd %.3f lag1 autocorr %.3f ; first 24:'%(v.mean(),v.std(),ac(v)), np.round(v[:24],2).tolist())
print('WHITE green  mean %.3f sd %.3f lag1 %.3f ; blue mean %.3f lag1 %.3f'%(g.mean(),g.std(),ac(g),b.mean(),ac(b)))
print('corr value-green %.3f value-blue %.3f'%(np.corrcoef(v,g)[0,1], np.corrcoef(v,b)[0,1]))
# runs of v<0.1 (selection 10%)
sel=(v<0.1).astype(int); runs=np.diff(np.where(np.diff(np.r_[0,sel,0])!=0)[0])[::2]
print('selected share %.3f, mean run length of selected %.2f (random would be ~1.1)'%(sel.mean(), runs.mean() if len(runs) else 0))
