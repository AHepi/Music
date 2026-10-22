import bpy, sys
sys.path.insert(0,'proc-work/garden/life')
import stage_life as SL
dg=bpy.context.evaluated_depsgraph_get()
for n in ['Maple leaves','Life / moss at feet and damp edges','Life / tufts','Life / pebble fringe']:
    ob=bpy.data.objects.get(n)
    if ob is None: print('RT missing',n); continue
    print('RT',n,SL.count_instances(ob))
print('RT collections', [c.name for c in bpy.data.collections if c.name.startswith('Life') or c.name.startswith('G2')], 'users', {c.name:c.users for c in bpy.data.collections if c.name.startswith('Life')})
print('RT unlinked leaf sources in scene?', 'Maple leaf source 0' in bpy.context.scene.objects)
