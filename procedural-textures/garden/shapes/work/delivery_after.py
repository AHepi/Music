# usage: blender -b courtyard_final.blend -P delivery_after.py -- LOOK OUT.json APPLY(1/0)
import sys
sys.dont_write_bytecode = True
HERE = 'proc-work/garden'
sys.path.insert(0, HERE + '/shapes')
import bpy, stage_shapes
a = sys.argv[sys.argv.index('--') + 1:]
if len(a) < 3 or a[2] == '1':
    stage_shapes.apply({'look': a[0]})
bpy.context.view_layer.update()
sys.argv = ['x', '--', a[1]]
src = open(HERE + '/ours/work/delivery_check.py').read()
# the groups of the team's own delivery check, plus our new objects joined to the group they belong to
src = src.replace("'bridge': pick(r'^Astra / varied planks\\.00[3-7]$', r'^Bridge pier \\d+$'),", "'bridge': pick(r'^Astra / varied planks\\.00[3-7]$', r'^Bridge pier \\d+$', r'^Bridge stringers$'),")
src = src.replace("'hall': pick(r'^Hall posts$',", "'hall': pick(r'^Roof carrying frame$', r'^Hall posts$',")
exec(compile(src, 'delivery_check.py', 'exec'))
