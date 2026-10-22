import bpy, math
m=bpy.data.materials['Pond water']; b=m.node_tree.nodes['Principled BSDF']
for i in b.inputs:
    if i.name in ('Transmission Weight','Coat Weight','Specular IOR Level','Roughness','IOR','Alpha','Emission Strength','Subsurface Weight'):
        print(i.name, i.default_value, i.is_linked)
print("attr node", m.node_tree.nodes['Attribute'].attribute_type, m.node_tree.nodes['Attribute'].attribute_name)
for n in ['Golden hour sun','Cool sky fill','Lantern light','Rim light (maple, hall edge)']:
    o=bpy.data.objects.get(n)
    if o:
        from mathutils import Vector
        d=o.matrix_world.to_quaternion()@Vector((0,0,-1))
        print(n, o.type, o.data.type, "energy", o.data.energy, "loc", tuple(round(v,2) for v in o.location), "dir travel", tuple(round(v,3) for v in d), "lg", o.lightgroup)
sc=bpy.context.scene
print("view", sc.view_settings.view_transform, sc.view_settings.look, sc.view_settings.exposure, "bounces", sc.cycles.max_bounces, sc.cycles.transmission_bounces, sc.cycles.transparent_max_bounces, "glossy", sc.cycles.glossy_bounces, sc.cycles.diffuse_bounces)
print("denoise", sc.cycles.use_denoising, sc.cycles.denoiser, "film transparent", sc.render.film_transparent)
vl=sc.view_layers[0]; print("passes", vl.use_pass_z, vl.use_pass_object_index, vl.use_pass_combined)
for o in bpy.data.objects:
    if o.name in ('Maple leaves','Maple trunk','Maple inner mass','Maple branch','Pine pads','Pine trunk','Bamboo leaves','Lily pads','Pond water','Fallen leaves'):
        print(o.name, "lightgroup:", repr(o.lightgroup))
import numpy as np
print(len(bpy.data.images), [ (i.name, i.size[:]) for i in bpy.data.images if 'bark' in i.name.lower() or 'pebb' in i.name.lower()])
