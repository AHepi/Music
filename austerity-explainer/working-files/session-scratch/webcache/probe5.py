import bpy
sc=bpy.context.scene
print([ (p.identifier) for p in sc.render.bl_rna.properties if 'compos' in p.identifier])
for p in sc.render.bl_rna.properties:
    if 'compositor' in p.identifier and p.type=='ENUM': print(p.identifier,[i.identifier for i in p.enum_items], getattr(sc.render,p.identifier))
