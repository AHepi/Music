import sys, time, importlib.util, json
t=time.time()
spec=importlib.util.spec_from_file_location('stage_props','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_props.py')
st=importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
import bpy
opts={}
if '--opts' in sys.argv: opts=json.loads(sys.argv[sys.argv.index('--opts')+1])
made=st.apply(opts)
print('APPLY SECONDS', round(time.time()-t,1), 'STRAW', made.get('straw'), 'LADDER TOP', made.get('ladder_top'), 'FLOOR', made.get('stable_floor_z'))
tot=0; rows=[]
for o in bpy.data.objects:
    if o.get('place_owner')=='props':
        o.data.calc_loop_triangles(); n=len(o.data.loop_triangles); tot+=n
        rows.append((o.name,o.get('place_role'),n,len(o.data.vertices)))
for r in rows: print(f'{r[0]:32s} {r[1]:16s} tris {r[2]:6d}')
print('TOTAL TRIS', tot, 'OBJECTS', len(rows))
out=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else None
if out and not out.startswith('--'):
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
