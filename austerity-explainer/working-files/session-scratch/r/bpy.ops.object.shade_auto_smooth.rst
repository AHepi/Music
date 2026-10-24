.. function:: shade_auto_smooth(*, use_auto_smooth=True, angle=0.523599)

Add modifier to automatically set the sharpness of mesh edges based on the angle between the neighboring faces

:param use_auto_smooth: Auto Smooth, Add modifier to set edge sharpness automatically (optional)
:type use_auto_smooth: bool
:param angle: Angle, Maximum angle between face normals that will be considered as smooth (in [0, 3.14159], optional)
:type angle: float
:return: Result of the operator call.
:rtype: set[Literal[rna_enum_operator_return_items]]