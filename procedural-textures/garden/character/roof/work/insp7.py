import bpy
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
pr=m.properties
for k in ("Socket_2","Socket_3","Socket_4","Socket_5","Socket_6","Socket_7"):
    x=pr.inputs[k]
    print(k, x.to_dict(), x.keys(), list(x.values()))
