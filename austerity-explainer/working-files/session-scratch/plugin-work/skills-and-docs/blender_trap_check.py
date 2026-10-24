import bpy, numpy as np, sys
print('VERSION', bpy.app.version_string)
# 1. colour space order
img = bpy.data.images.new('a', 4, 4)
img.colorspace_settings.name = 'Non-Color'
buf = np.full((4,4,4), 0.5, np.float32)
img.pixels.foreach_set(buf.ravel())
print('A set space first then pixels:', round(sum(img.pixels[:])/len(img.pixels),3))
img2 = bpy.data.images.new('b', 4, 4)
img2.pixels.foreach_set(buf.ravel())
img2.colorspace_settings.name = 'Non-Color'
print('B pixels then set space:', round(sum(img2.pixels[:])/len(img2.pixels),3))
# 2. auto smooth
me = bpy.data.meshes.new('m')
print('has use_auto_smooth:', hasattr(me, 'use_auto_smooth'))
# 3. numpy / PIL / cv2
for mod in ('numpy','PIL','cv2','scipy'):
    try:
        __import__(mod); print('import', mod, 'ok')
    except Exception as e:
        print('import', mod, 'FAILED', type(e).__name__)
