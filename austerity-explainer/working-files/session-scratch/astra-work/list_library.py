# What this does: lists what is inside the Astra courtyard component library file (read only).
import bpy, sys
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (src, dst):
    for kind in ('objects', 'materials', 'node_groups', 'meshes', 'images', 'collections', 'textures', 'worlds'):
        print(kind.upper(), len(getattr(src, kind)), list(getattr(src, kind))[:40])
