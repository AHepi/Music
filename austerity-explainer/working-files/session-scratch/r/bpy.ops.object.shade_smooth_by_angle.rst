.. function:: shade_smooth_by_angle(*, angle=0.523599, keep_sharp_edges=True)

Set the sharpness of mesh edges based on the angle between the neighboring faces

:param angle: Angle, Maximum angle between face normals that will be considered as smooth (in [0, 3.14159], optional)
:type angle: float
:param keep_sharp_edges: Keep Sharp Edges, Only add sharp edges instead of clearing existing tags first (optional)
:type keep_sharp_edges: bool
:return: Result of the operator call.
:rtype: set[Literal[rna_enum_operator_return_items]]