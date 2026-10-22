import bpy, sys
p = sys.argv[sys.argv.index('--')+1]
r = bpy.data.images.load(p)
print('size', tuple(r.size), r.colorspace_settings.name, r.is_float)
px = list(r.pixels)
print(len(px), [round(x,5) for x in px[:64]])
