import bpy
from collections import Counter
g=bpy.data.node_groups["WK MASKS CT / Ceramic painterly surface"]
print(Counter(n.bl_idname for n in g.nodes))
for n in g.nodes:
    if n.bl_idname in("ShaderNodeAttribute","ShaderNodeBevel","ShaderNodeAmbientOcclusion","ShaderNodeNewGeometry","ShaderNodeObjectInfo","ShaderNodeTexCoord","ShaderNodeVertexColor","ShaderNodeUVMap","ShaderNodeLightPath"):
        print(n.bl_idname,n.name,getattr(n,'attribute_name',''),getattr(n,'attribute_type',''),[o.name for o in n.outputs if o.is_linked])
print([ (i.name,i.in_out) for i in g.interface.items_tree if i.item_type=='SOCKET'])
