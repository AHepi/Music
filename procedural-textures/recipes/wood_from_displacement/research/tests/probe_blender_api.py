# What this does: asks Blender 5.2 which shader nodes exist that matter for repeating-free textures (repeat zone, closures,
# white noise, image texture options). It only prints names; it makes no pictures.
import bpy
print('VERSION', bpy.app.version_string)
mat = bpy.data.materials.new('m'); mat.use_nodes = True
t = mat.node_tree
im = t.nodes.new('ShaderNodeTexImage')
print('IMAGE extension items', [i.identifier for i in im.bl_rna.properties['extension'].enum_items])
print('IMAGE interpolation items', [i.identifier for i in im.bl_rna.properties['interpolation'].enum_items])
print('IMAGE projection', [i.identifier for i in im.bl_rna.properties['projection'].enum_items])
print('IMAGE inputs', [s.name for s in im.inputs], 'outputs', [s.name for s in im.outputs])
print('TexImage props', [p.identifier for p in im.bl_rna.properties if p.identifier not in ('rna_type','name','label','location','width','height','dimensions','inputs','outputs','internal_links','select','show_options','show_preview','show_texture','hide','mute','parent','type','bl_idname','bl_label','bl_description','bl_icon','bl_static_type','bl_width_default','bl_width_min','bl_width_max','bl_height_default','bl_height_min','bl_height_max','color','use_custom_color','width_hidden','warning_propagation','location_absolute')])
names = [n for n in dir(bpy.types) if n.startswith('ShaderNode')]
print('SHADER NODE TYPES', len(names))
for n in names:
    if any(k in n for k in ('Repeat','Closure','Bundle','Tex','Menu','Radial','Raycast','Hash','Random','Switch','Index','Zone','Foreach','ForEach','Rotate')):
        print('  ', n)
print('other types', [n for n in dir(bpy.types) if ('Closure' in n or 'RepeatZone' in n or 'RepeatInput' in n or 'Bundle' in n)][:40])
# which math operations exist
mn = t.nodes.new('ShaderNodeMath')
print('MATH ops', [i.identifier for i in mn.bl_rna.properties['operation'].enum_items])
vm = t.nodes.new('ShaderNodeVectorMath')
print('VECTORMATH ops', [i.identifier for i in vm.bl_rna.properties['operation'].enum_items])
wn = t.nodes.new('ShaderNodeTexWhiteNoise')
print('WHITENOISE dims', [i.identifier for i in wn.bl_rna.properties['noise_dimensions'].enum_items], [s.name for s in wn.inputs], [s.name for s in wn.outputs])
print('GN node types with Repeat', [n for n in dir(bpy.types) if n.startswith('GeometryNodeRepeat')])
