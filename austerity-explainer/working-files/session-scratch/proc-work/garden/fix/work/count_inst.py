import bpy, sys
sys.dont_write_bytecode=True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/fix/stage')
import stage_fix
look = sys.argv[sys.argv.index('--')+1]
def count():
    dg = bpy.context.evaluated_depsgraph_get()
    n = {}
    for inst in dg.object_instances:
        if inst.is_instance:
            nm = inst.parent.name if inst.parent else inst.object.name
            n[nm] = n.get(nm,0)+1
    return n
c0 = count()
print('BEFORE', {k:v for k,v in c0.items() if 'Maple' in k or 'tuft' in k or 'moss' in k or 'pebble' in k})
stage_fix.apply({'look': look})
bpy.context.view_layer.update()
c1 = count()
print('AFTER ', {k:v for k,v in c1.items() if 'Maple' in k or 'tuft' in k or 'moss' in k or 'pebble' in k})
