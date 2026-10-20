# What this does: lists the ready-made node groups ("assets") that ship inside Blender 5.2.2's asset files.
import bpy, sys
for path in sys.argv[sys.argv.index('--')+1:]:
    with bpy.data.libraries.load(path) as (src, dst):
        print('==', path.split('/')[-1], len(src.node_groups))
        for n in sorted(src.node_groups): print('  ', n)
