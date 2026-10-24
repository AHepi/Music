import bpy, sys, time
print("BLENDER", bpy.app.version_string)
items = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
print("ENGINES", items)
try:
    import gpu
    print("GPU backend", gpu.platform.backend_type_get() if hasattr(gpu.platform,'backend_type_get') else '?')
    print("GPU vendor", gpu.platform.vendor_get(), "|", gpu.platform.renderer_get(), "|", gpu.platform.version_get())
except Exception as e:
    print("GPU info failed:", repr(e))
