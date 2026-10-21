# What this does: prints the socket names of the geometry-node types I plan to use in an empty scene (so I do not guess names). Changes nothing on disk.
import sys
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bpy
import bx_gn as G
print('VERSION', bpy.app.version_string)
b = G.Builder('probe')
for kind, props in [('Proximity', {}), ('DistributePointsOnFaces', {}), ('DeleteGeometry', {}), ('InstanceOnPoints', {}), ('MapRange', {}),
                    ('NoiseTexture', {}), ('RandomValue', {'data_type': 'FLOAT'}), ('CollectionInfo', {}), ('ObjectInfo', {}), ('Math', {}),
                    ('Compare', {'data_type': 'VECTOR', 'mode': 'DIRECTION', 'operation': 'LESS_EQUAL'}), ('Mix', {'data_type': 'FLOAT'}), ('RealizeInstances', {}),
                    ('StoreNamedAttribute', {'data_type': 'FLOAT', 'domain': 'INSTANCE'}), ('Switch', {'input_type': 'GEOMETRY'})]:
    n = b.node(kind, **props)
    print(kind, n.bl_idname, 'IN', [(s.name, s.identifier) for s in n.inputs if s.enabled], 'OUT', [s.name for s in n.outputs if s.enabled])
    for p in ('target_element', 'transform_space', 'distribute_method'):
        if hasattr(n, p):
            print('   prop', p, getattr(n, p), [i.identifier for i in n.bl_rna.properties[p].enum_items])
