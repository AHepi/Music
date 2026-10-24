import mathutils.geometry as g
from mathutils import Vector
outer=[Vector((0,0,0)),Vector((10,0,0)),Vector((10,10,0)),Vector((0,10,0))]
hole_same=[Vector((3,3,0)),Vector((7,3,0)),Vector((7,7,0)),Vector((3,7,0))]
hole_opp=hole_same[::-1]
for name,h in (('same',hole_same),('opp',hole_opp)):
    tris=g.tessellate_polygon([outer,h])
    area=0
    allv=outer+h
    for t in tris:
        a,b,c=[allv[i] for i in t]
        area+=abs((b-a).cross(c-a).z)/2
    print(name,len(tris),'area',area)
