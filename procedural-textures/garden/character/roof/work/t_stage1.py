import sys, json
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import stage_roof
rep=stage_roof.apply({'steps':[0,1,2],'map_sizes':{'glaze':256,'plaster':256,'stone':256,'moss':256}})
print(json.dumps({k:v for k,v in rep.items() if k not in('new_objects','new_materials')},default=str)[:2500])
print("NEW",rep['new_objects'],rep['new_materials'])
rep2=stage_roof.apply({'steps':[0,1,2],'map_sizes':{'glaze':256,'plaster':256,'stone':256,'moss':256}})
print("second run new objects equal:", rep['new_objects']==rep2['new_objects'], "mat equal", rep['new_materials']==rep2['new_materials'], "tiles",rep2['step0_uv'])
