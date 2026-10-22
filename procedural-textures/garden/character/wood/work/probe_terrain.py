import bpy, math
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
names = ["Astra / Courtyard receiving ground","Life / pond bed","Life / pond pebbles","Astra / pebbles grouped bodies","Astra / moss grouped bodies"]
for n in names:
    o = bpy.data.objects.get(n)
    print(n, o and len(o.data.vertices), o and [round(x,2) for x in o.bound_box[0]], o and [round(x,2) for x in o.bound_box[6]])
def cast(name, x, y):
    o = bpy.data.objects[name].evaluated_get(dg)
    mw = o.matrix_world; inv = mw.inverted()
    org = inv @ Vector((x, y, 3.0)); d = (inv.to_3x3() @ Vector((0,0,-1))).normalized()
    ok, loc, nrm, idx = o.ray_cast(org, d)
    return (mw @ loc).z if ok else None
N = {"N3":(-5.95,1.55),"N2":(-3.90,0.15),"N1":(-2.00,1.00),"N0":(-0.55,-0.60)}
import itertools
pts = []
keys = ["N3","N2","N1","N0"]
for a,b in zip(keys[:-1], keys[1:]):
    pa, pb = N[a], N[b]
    for i in range(0, 11):
        t = i/10
        pts.append(("%s-%s %.1f" % (a,b,t), pa[0]+(pb[0]-pa[0])*t, pa[1]+(pb[1]-pa[1])*t))
for lab, x, y in pts:
    g = cast("Astra / Courtyard receiving ground", x, y); b = cast("Life / pond bed", x, y); p = cast("Life / pond pebbles", x, y)
    f = lambda v: "None" if v is None else "%.3f" % v
    print(lab, "(%.2f,%.2f)" % (x,y), "ground", f(g), "bed", f(b), "pebbles", f(p))
# lateral offsets across the arm at middle
import math
for a,b in zip(keys[:-1], keys[1:]):
    pa, pb = N[a], N[b]; dx, dy = pb[0]-pa[0], pb[1]-pa[1]; L = math.hypot(dx,dy); ux, uy = dx/L, dy/L; nx, ny = -uy, ux
    for t in (0.5,):
        cx, cy = pa[0]+dx*t, pa[1]+dy*t
        for off in (-0.8,-0.62,-0.42,0,0.42,0.62,0.8):
            x, y = cx+nx*off, cy+ny*off
            print(a,b,"mid off %.2f" % off, "ground", cast("Astra / Courtyard receiving ground", x,y), "bed", cast("Life / pond bed", x,y))
