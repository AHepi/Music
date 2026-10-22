import bpy, sys
from mathutils import Vector
sc = bpy.context.scene
print("SCENE", sc.name, sc.render.engine, sc.render.resolution_x, sc.render.resolution_y, "frame", sc.frame_current)
for n in ['photo','veranda','Focus']:
    o = bpy.data.objects.get(n)
    if o and o.type=='CAMERA':
        c = o.data
        print("CAM", n, tuple(round(v,3) for v in o.location), tuple(round(v,3) for v in o.rotation_euler), "lens", c.lens, "sensor", c.sensor_width, c.sensor_fit, "dof", c.dof.use_dof)
names = ['Pond water','Basin water','Life / pond bed','Life / pond pebbles','Lily pads','Lotus blossoms','Life / iris clumps','Life / lily stems','Maple trunk','Maple branch','Maple inner mass','Maple leaves','Pine trunk','Pine limb','Pine pads','Bamboo stalks','Bamboo leaves','Bamboo fence','Basin bamboo spout','Basin ladle']
for n in names:
    o = bpy.data.objects.get(n)
    if o is None: print("MISSING", n); continue
    cols = [c.name for c in o.users_collection]
    d = o.data
    extra = ""
    if o.type=='MESH':
        extra = f"V{len(d.vertices)} F{len(d.polygons)} uv={[u.name for u in d.uv_layers]} attrs={[a.name for a in d.attributes if not a.name.startswith('.')]}"
    elif o.type=='CURVE':
        extra = f"splines {len(d.splines)} pts {[len(s.points) for s in d.splines]} bevel {d.bevel_depth} res {d.bevel_resolution}"
    print("OBJ", n, o.type, cols, "loc", tuple(round(v,2) for v in o.location), "dim", tuple(round(v,2) for v in o.dimensions), extra, "mats", [m.name if m else None for m in (d.materials if hasattr(d,'materials') else [])], "mods", [m.name for m in o.modifiers])
    print("   props", {k: o[k] for k in o.keys() if k in ('garden_owner','garden_role','garden_look')})
for c in bpy.data.collections:
    print("COLL", c.name, len(c.objects), "children", [x.name for x in c.children])
