import bpy, re, collections, sys
out=[]
def p(*a): out.append(" ".join(str(x) for x in a))
sc=bpy.context.scene
p("scene",sc.name,"engine",sc.render.engine,"res",sc.render.resolution_x,sc.render.resolution_y,"unit",sc.unit_settings.system, sc.unit_settings.scale_length)
p("camera",sc.camera.name if sc.camera else None)
# collections
def walk(c,d=0):
    p("  "*d+"COLL",c.name,len(c.objects))
    for ch in c.children: walk(ch,d+1)
walk(sc.collection)
# group objects by name stem
groups=collections.OrderedDict()
for o in bpy.data.objects:
    stem=re.sub(r'[\s_.]*\d+$','',o.name)
    groups.setdefault(stem,[]).append(o)
p("N objects",len(bpy.data.objects))
for stem,objs in groups.items():
    o=objs[0]
    nv=0
    try:
        nv=len(o.data.vertices) if o.type=='MESH' else 0
    except: pass
    mats=sorted({s.material.name for ob in objs for s in ob.material_slots if s.material})
    mods=sorted({m.type+":"+m.name for ob in objs for m in ob.modifiers})
    p("OBJ",stem,"x%d"%len(objs),o.type,"verts(first)",nv,"loc",tuple(round(v,2) for v in o.location),"dim",tuple(round(v,2) for v in o.dimensions),"vis",not o.hide_render,"mods",mods[:4],"mats",mats[:6], "props", [k for k in o.keys() if not k.startswith('_')][:4])
p("MATERIALS",len(bpy.data.materials))
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree:
        types=collections.Counter(n.bl_idname.replace('ShaderNode','') for n in m.node_tree.nodes)
        imgs=[n.image.name for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image]
        p("MAT",m.name,"users",m.users,dict(types) if len(types)<14 else "nodes=%d"%len(m.node_tree.nodes),"imgs",imgs[:5])
p("IMAGES",len(bpy.data.images))
for im in bpy.data.images:
    p("IMG",im.name,im.size[:],im.colorspace_settings.name,im.filepath[:90],"packed" if im.packed_file else "")
p("NODEGROUPS",[g.name for g in bpy.data.node_groups])
open(sys.argv[-1],"w").write("\n".join(out))
