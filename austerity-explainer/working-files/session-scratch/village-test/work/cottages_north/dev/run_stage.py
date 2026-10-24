import sys, time, importlib.util
t=time.time()
spec=importlib.util.spec_from_file_location('stage_cn','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_cottages_north.py')
st=importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
import bpy
made=st.apply({})
print('APPLY SECONDS', round(time.time()-t,1))
import numpy as np
tot=0
for o in bpy.data.objects:
    if o.get('place_owner')=='cottages_north':
        o.data.calc_loop_triangles(); n=len(o.data.loop_triangles); tot+=n
        print(f'{o.name:55s} {o.get("place_role"):18s} tris {n:6d}')
print('TOTAL TRIS', tot)
out=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else None
if out:
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
