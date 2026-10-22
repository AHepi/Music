import sys, json, time
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import stage_roof
t=time.time()
rep=stage_roof.apply({'steps':[0,1,2,3,4,5,6],'map_sizes':{'glaze':256,'plaster':256,'stone':256,'moss':256}})
print("T",time.time()-t)
print(json.dumps({k:v for k,v in rep.items() if k not in('new_objects','new_materials','tile_plan','drip_tiles')},default=str)[:3500])
print("NEWOBJ",len(rep['new_objects']),rep['new_objects'][:60])
print("NEWMAT",len(rep['new_materials']))
