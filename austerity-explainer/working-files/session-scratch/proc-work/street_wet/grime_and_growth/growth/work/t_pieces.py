import sys, bpy
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
sys.dont_write_bytecode=True
from growth import pieces
lib=pieces.Library()
lib.build()
for k,v in lib.kinds.items():
    print(k, 'faces',min(v['faces']),max(v['faces']), 'width_cm',round(min(v['widths'])*100,1),round(max(v['widths'])*100,1),'height_cm',round(min(v['heights'])*100,1),round(max(v['heights'])*100,1), 'fp_cm2', round(v['mean_footprint']*1e4,1))
