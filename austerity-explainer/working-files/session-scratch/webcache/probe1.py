import bpy
sc=bpy.context.scene
print('SCENE attrs with node:', [a for a in dir(sc) if 'node' in a.lower() or 'compos' in a.lower()])
print('GN bake nodes:', [n for n in dir(bpy.types) if 'Bake' in n])
print('Compositor nodes:', sorted([n for n in dir(bpy.types) if n.startswith('CompositorNode')]))
m=bpy.types.SubsurfModifier.bl_rna.properties
print('Subsurf props:', [p.identifier for p in m])
print('Object cycles props:', [p.identifier for p in bpy.types.Object.bl_rna.properties if 'adaptive' in p.identifier or 'dicing' in p.identifier])
ob=bpy.data.objects.new('x', None)
try:
    print('ob.cycles', [p.identifier for p in ob.cycles.bl_rna.properties])
except Exception as e: print('no ob.cycles', e)
