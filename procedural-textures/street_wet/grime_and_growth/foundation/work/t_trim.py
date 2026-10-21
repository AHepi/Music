import bpy, re
print('TRIMS', [o.name for o in bpy.data.objects if re.match(r'^(left|right)_row_[ab]_cottage_\d+_trim$', o.name) or re.match(r'.*_trim$', o.name)][:60])
print('IRON', [(o.name, [s.material.name for s in o.material_slots if s.material]) for o in bpy.data.objects if any(s.material and s.material.name in ('cast_iron','wheel_iron','headframe_steel','wire_rope') for s in o.material_slots)][:60])
