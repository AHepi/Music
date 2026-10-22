import bpy
for n in ["Pond edge stone %d"%i for i in range(15)]+["Rock 0","Rock 3","Lantern post","Basin drain pebbles"]:
    o=bpy.data.objects[n]
    print(n,"det",round(o.matrix_world.determinant(),3),"scale",tuple(round(x,3) for x in o.scale),"rot",tuple(round(x,3) for x in o.rotation_euler),"parent",o.parent)
