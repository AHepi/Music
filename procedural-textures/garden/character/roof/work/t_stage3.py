import sys, json, time
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import stage_roof
rep=stage_roof.apply({'map_sizes':{'glaze':128,'plaster':128,'stone':128,'moss':128}})
print("LEAVES",rep.get('roof_leaves'), "caps",len(rep['moss_caps']), rep['walls']['Right wall behind hall']['plaster_loss_patches'])
rep=stage_roof.apply({'steps':[0,1,2],'mask_render':True,'debug':'masks','cameras':False,'map_sizes':{'glaze':128,'plaster':128,'stone':128,'moss':128}})
print("MASKOK")
