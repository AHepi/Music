import bpy
for n in ["Hall posts","Hall beams","Roof carrying frame","Gravel timber edge","Shoji bars","Eave soffit","Stone plinth","Veranda step","Bridge stringers","Astra / varied planks.005"]:
    o = bpy.data.objects[n]
    print("PROPS", n, {k: (round(o[k],3) if isinstance(o[k], float) else o[k]) for k in o.keys() if k.startswith('wk_') and k.endswith('_amount') and o[k] not in (0, 0.0)})
