import bpy
print("BLENDER", bpy.app.version_string)
want = {
 "export_scene.fbx": "use_selection apply_unit_scale use_mesh_modifiers mesh_smooth_type add_leaf_bones path_mode embed_textures axis_forward axis_up object_types use_armature_deform_only bake_anim bake_anim_use_all_actions bake_anim_use_nla_strips apply_scale_options bake_space_transform".split(),
 "export_scene.gltf": "export_format use_selection export_yup export_apply export_image_format export_meshopt_compression_enable".split(),
 "wm.usd_export": "selected_objects_only usdz_downscale_size".split(),
 "wm.stl_export": "export_selected_objects apply_modifiers global_scale".split(),
 "import_scene.gltf": [], "import_scene.fbx": [], "wm.obj_import": [], "wm.stl_import": [], "wm.ply_import": [], "wm.usd_import": [],
 "wm.read_factory_settings": ["use_empty"],
}
for path, props in want.items():
    mod, name = path.split(".")
    try:
        op = getattr(getattr(bpy.ops, mod), name)
        keys = set(op.get_rna_type().properties.keys())
        missing = [p for p in props if p not in keys]
        print("OK " if not missing else "BAD", path, "missing:", missing)
    except Exception as e:
        print("ERR", path, type(e).__name__, e)
# USD texture-related options, to see what a plain usd preset writes beside the file
try:
    keys = bpy.ops.wm.usd_export.get_rna_type().properties
    for k in keys.keys():
        if "textur" in k:
            p = keys[k]
            print("USD", k, "default=", getattr(p, "default", None))
except Exception as e:
    print("ERR usd props", e)
try:
    keys = bpy.ops.export_scene.fbx.get_rna_type().properties
    print("FBX path_mode default:", keys["path_mode"].default, "embed_textures default:", keys["embed_textures"].default)
except Exception as e:
    print("ERR fbx props", e)
