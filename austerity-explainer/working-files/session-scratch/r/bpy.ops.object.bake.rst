.. function:: bake(*, type='COMBINED', pass_filter=set(), filepath="", width=512, height=512, margin=16, margin_type='EXTEND', use_selected_to_active=False, max_ray_distance=0.0, cage_extrusion=0.0, cage_object="", normal_space='TANGENT', normal_r='POS_X', normal_g='POS_Y', normal_b='POS_Z', target='IMAGE_TEXTURES', save_mode='INTERNAL', use_clear=False, use_cage=False, use_split_materials=False, use_automatic_name=False, uv_layer="")

Bake image textures of selected objects

:param type: Type, Type of pass to bake, some of them may not be supported by the current render engine (optional)
:type type: Literal[rna_enum_bake_pass_type_items]
:param pass_filter: Pass Filter, Filter to combined, diffuse, glossy, transmission and subsurface passes (optional)
:type pass_filter: set[Literal[rna_enum_bake_pass_filter_type_items]]
:param filepath: File Path, Image filepath to use when saving externally (optional, never None)
:type filepath: str
:param width: Width, Horizontal dimension of the baking map (external only) (in [1, inf], optional)
:type width: int
:param height: Height, Vertical dimension of the baking map (external only) (in [1, inf], optional)
:type height: int
:param margin: Margin, Extends the baked result as a post process filter (in [0, inf], optional)
:type margin: int
:param margin_type: Margin Type, Which algorithm to use to generate the margin (optional)
:type margin_type: Literal[rna_enum_bake_margin_type_items]
:param use_selected_to_active: Selected to Active, Bake shading on the surface of selected objects to the active object (optional)
:type use_selected_to_active: bool
:param max_ray_distance: Max Ray Distance, The maximum ray distance for matching points between the active and selected objects. If zero, there is no limit (in [0, inf], optional)
:type max_ray_distance: float
:param cage_extrusion: Cage Extrusion, Inflate the active object by the specified distance for baking. This helps matching to points nearer to the outside of the selected object meshes (in [0, inf], optional)
:type cage_extrusion: float
:param cage_object: Cage Object, Object to use as cage, instead of calculating the cage from the active object with cage extrusion (optional, never None)
:type cage_object: str
:param normal_space: Normal Space, Choose normal space for baking (optional)
:type normal_space: Literal[rna_enum_normal_space_items]
:param normal_r: R, Axis to bake in red channel (optional)
:type normal_r: Literal[rna_enum_normal_swizzle_items]
:param normal_g: G, Axis to bake in green channel (optional)
:type normal_g: Literal[rna_enum_normal_swizzle_items]
:param normal_b: B, Axis to bake in blue channel (optional)
:type normal_b: Literal[rna_enum_normal_swizzle_items]
:param target: Target, Where to output the baked map (optional)
:type target: Literal[rna_enum_bake_target_items]
:param save_mode: Save Mode, Where to save baked image textures (optional)
:type save_mode: Literal[rna_enum_bake_save_mode_items]
:param use_clear: Clear, Clear images before baking (only for internal saving) (optional)
:type use_clear: bool
:param use_cage: Cage, Cast rays to active object from a cage (optional)
:type use_cage: bool
:param use_split_materials: Split Materials, Split baked maps per material, using material name in output file (external only) (optional)
:type use_split_materials: bool
:param use_automatic_name: Automatic Name, Automatically name the output file with the pass type (optional)
:type use_automatic_name: bool
:param uv_layer: UV Layer, UV layer to override active (optional, never None)
:type uv_layer: str
:return: Result of the operator call.
:rtype: set[Literal[rna_enum_operator_return_items]]