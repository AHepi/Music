import bpy, sys
from mathutils import Vector
names = ["Astra / varied planks","Astra / varied planks.003","Astra / varied planks.006","Bridge pier 0","Bridge pier 1","Bridge stringers","Stone plinth","Hall posts","Hall beams","Eave soffit","Roof carrying frame","Gravel timber edge","Shoji bars","Veranda step","Veranda step, lower"]
for n in names:
    o = bpy.data.objects[n]
    me = o.data
    print("==", n, "verts", len(me.vertices), "polys", len(me.polygons), "uv", [u.name for u in me.uv_layers], "attrs", [a.name for a in me.attributes][:12])
    print("   parent", o.parent.name if o.parent else None, "mods", [(m.name, m.type) for m in o.modifiers], "mats", [s.material.name if s.material else None for s in o.material_slots][:8], "colls", [c.name for c in o.users_collection])
    print("   loc", tuple(round(v,3) for v in o.location), "rot", tuple(round(v,3) for v in o.rotation_euler), "scale", tuple(round(v,3) for v in o.scale), "props", {k: (v if not hasattr(v,'to_dict') else '...') for k,v in o.items() if k.startswith('garden') or k.startswith('astra')} )
    print("   matrix_world", [tuple(round(x,3) for x in r) for r in o.matrix_world])
