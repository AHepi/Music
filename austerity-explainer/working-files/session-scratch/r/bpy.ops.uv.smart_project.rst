.. function:: smart_project(*, angle_limit=1.15192, margin_method='SCALED', rotate_method='AXIS_ALIGNED_Y', island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)

Projection unwraps the selected faces of mesh objects

:param angle_limit: Angle Limit, Lower for more projection groups, higher for less distortion (in [0, 1.5708], optional)
:type angle_limit: float
:param margin_method: Margin Method, (optional)

SCALED
Scaled -- Use scale of existing UVs to multiply margin.

ADD
Add -- Just add the margin, ignoring any UV scale.

FRACTION
Fraction -- Specify a precise fraction of final UV output.
:type margin_method: Literal['SCALED', 'ADD', 'FRACTION']
:param rotate_method: Rotation Method, (optional)

AXIS_ALIGNED
Axis-aligned -- Rotated to a minimal rectangle, either vertical or horizontal.

AXIS_ALIGNED_X
Axis-aligned (Horizontal) -- Rotate islands to be aligned horizontally.

AXIS_ALIGNED_Y
Axis-aligned (Vertical) -- Rotate islands to be aligned vertically.
:type rotate_method: Literal['AXIS_ALIGNED', 'AXIS_ALIGNED_X', 'AXIS_ALIGNED_Y']
:param island_margin: Island Margin, Margin to reduce bleed from adjacent islands (in [0, 1], optional)
:type island_margin: float
:param area_weight: Area Weight, Weight projection's vector by faces with larger areas (in [0, 1], optional)
:type area_weight: float
:param correct_aspect: Correct Aspect, Map UVs taking aspect ratio of the image associated with the material into account (optional)
:type correct_aspect: bool
:param scale_to_bounds: Scale to Bounds, Scale UV coordinates to bounds after unwrapping (optional)
:type scale_to_bounds: bool
:return: Result of the operator call.
:rtype: set[Literal[rna_enum_operator_return_items]]