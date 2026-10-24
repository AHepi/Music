import sys, json, bpy
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces')
import stage_surfaces as ss
def counts():
    return {'objects': len(bpy.data.objects), 'materials': len(bpy.data.materials), 'node_groups': len(bpy.data.node_groups), 'images': len(bpy.data.images), 'collections': len(bpy.data.collections)}
c0 = counts()
r1 = ss.apply({'look': 'real', 'weathering': True, 'verbose': False})
c1 = counts()
r2 = ss.apply({'look': 'real', 'weathering': True, 'verbose': False})
c2 = counts()
import weathering_stage
weathering_stage.remove()
c3 = counts()
print('IDEMPOTENT', json.dumps({'start': c0, 'after_first': c1, 'after_second': c2, 'after_kit_remove': c3, 'second_run_s': r2['seconds'], 'mask_pack_second': r2['weathering']['mask_pack']}))
