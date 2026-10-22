import bpy
m=bpy.data.materials['Maple leaves']
for n in m.node_tree.nodes:
    if n.bl_idname in ('ShaderNodeBsdfPrincipled','ShaderNodeEmission','ShaderNodeBsdfTranslucent','ShaderNodeMixShader','ShaderNodeAddShader'):
        print('NODE',n.name,n.bl_idname)
        for s in n.inputs:
            if hasattr(s,'default_value') and s.name in ('Emission Strength','Strength','Emission Color','Factor','Fac','Transmission Weight','Weight'):
                v=s.default_value
                print('   ',s.name, tuple(v) if hasattr(v,'__len__') else v, 'linked' if s.is_linked else '')
