import sys, time, traceback
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/wood'
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import bpy
t = time.time()
import stage_wood
try:
    rep = stage_wood.apply({})
    print('APPLY_OK', round(time.time() - t, 1), {k: (len(v) if isinstance(v, list) else v) for k, v in rep.items() if k in ('created', 'changed', 'deleted', 'seconds')})
    rep2 = stage_wood.apply({})
    print('APPLY2_OK', {k: (len(v) if isinstance(v, list) else v) for k, v in rep2.items() if k in ('created', 'changed', 'deleted', 'seconds')})
    print('objects', len(bpy.data.objects), 'materials', len(bpy.data.materials), 'verts', sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH'))
except Exception:
    traceback.print_exc()
