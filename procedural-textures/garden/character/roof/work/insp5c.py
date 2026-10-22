import bpy
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
pr=m.properties
for k in ("Socket_2","Socket_3","Socket_4","Socket_5","Socket_6","Socket_7"):
    print(k, pr.inputs[k].to_dict())
    print([a for a in dir(pr.inputs[k])][:0], pr.inputs.Socket_2 if hasattr(pr.inputs,'Socket_2') else None)
try: print(pr.inputs.Socket_2.value)
except Exception as e: print("ERR",e)
print(m.keys() if hasattr(m,'keys') else '')
