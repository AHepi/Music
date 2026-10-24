import bpy, numpy as np
m=bpy.data.meshes.new('t'); m.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0)],[],[(0,1,2,3)])
a=m.color_attributes.new('Col','FLOAT_COLOR','CORNER'); print('attr',a.name, len(a.data))
a.data.foreach_set('color',[1,0,0,1]*4)
try:
    m.shade_smooth(); print('shade_smooth ok')
except Exception as e: print('ss fail',e)
mat=bpy.data.materials.new('x'); mat.use_nodes=True; nt=mat.node_tree
print([n.bl_idname for n in nt.nodes])
for idn in ('ShaderNodeVertexColor','ShaderNodeMix','ShaderNodeTexImage','ShaderNodeMixRGB','ShaderNodeTexCoord','ShaderNodeMapping','ShaderNodeAttribute'):
    try:
        n=nt.nodes.new(idn); print(idn,'ok',[ (i.name) for i in n.inputs][:9],[o.name for o in n.outputs])
    except Exception as e: print(idn,'FAIL',e)
img=bpy.data.images.new('t',8,8); img.colorspace_settings.name='Non-Color'; img.pixels=[0.9]*(8*8*4); img.pack(); print('packed',img.packed_file is not None)
print(bpy.app.version_string)
