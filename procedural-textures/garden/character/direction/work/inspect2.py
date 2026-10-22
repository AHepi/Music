import bpy, sys, json, mathutils
out=[]
def p(*a): out.append(" ".join(str(x) for x in a))
def bbox(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    mn=[min(c[i] for c in cs) for i in range(3)]; mx=[max(c[i] for c in cs) for i in range(3)]
    return tuple(round(v,2) for v in mn), tuple(round(v,2) for v in mx)
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    n=o.name
    if n.startswith("Astra / varied planks") or n.startswith("Bridge") or n in("Pond water","Life / pond bed","Stone plinth","Veranda step","Veranda step, lower","Hall roof","Hall posts","Hall beams","Raked gravel court","Astra / Courtyard receiving ground","Water basin","Gravel kerb","Roof carrying frame","Eave soffit"):
        p(n,o.type,"bbox",bbox(o),"coll",[c.name for c in o.users_collection])
for o in bpy.data.objects:
    if o.name.startswith("Astra / Planked run controls"):
        p("CTRL",o.name,o.location[:], o.rotation_euler[:], "coll",[c.name for c in o.users_collection])
        for k in o.keys():
            if k.startswith('_'): continue
            v=o[k]
            try: v=v.to_dict()
            except: pass
            s=json.dumps(v,default=str) if not isinstance(v,str) else v
            p("   ",k,s[:900])
# planks: count of separate pieces in first run
o=bpy.data.objects["Astra / varied planks"]
bm=o.data
p("first planks verts",len(bm.vertices),"polys",len(bm.polygons))
p("modifiers",[(m.name,m.type,getattr(m,'width',None),getattr(m,'segments',None)) for m in o.modifiers])
st=bpy.data.objects["Bridge stringers"]
p("stringers verts",[tuple(round(c,2) for c in (st.matrix_world@v.co)) for v in st.data.vertices][:48])
for o in bpy.data.objects:
    if o.name.startswith("Bridge pier"):
        p("PIER",o.name,bbox(o),len(o.data.vertices))
# pond water level and light list
for l in bpy.data.objects:
    if l.type=='LIGHT': p("LIGHT",l.name,l.data.type,round(l.data.energy,1),l.location[:])
w=bpy.data.worlds
p("worlds",[x.name for x in w])
r=bpy.context.scene.render
p("samples",bpy.context.scene.cycles.samples,"denoise",bpy.context.scene.cycles.use_denoising,"view",bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look,"exp",bpy.context.scene.view_settings.exposure)
p("cameras", [(c.name,c.location[:],c.data.lens) for c in bpy.data.objects if c.type=='CAMERA'])
open(sys.argv[-1],"w").write("\n".join(out))
