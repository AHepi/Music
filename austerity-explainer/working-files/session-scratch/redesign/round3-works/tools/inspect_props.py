# Prints each prop's parts and their bounds (to place them), in a fresh scene.
import bpy, mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
P='/home/user/Music/austerity-explainer/film-kit/assets/models/'
for f in ['pit-village/props/handcart.glb','pit-village/props/gas-lamp-wall-bracket.glb','pit-village/props/gas-lamp-post.glb','pit-village/props/hurricane-lantern.glb','pit-village/props/brazier-drum.glb',
          'inflation-chapter-2-newcomers/props/bank-hanging-sign.glb','inflation-chapter-2-newcomers/props/jacket-and-cap-on-nail.glb','inflation-chapter-2-newcomers/props/hand-truck.glb',
          'inflation-chapter-2-newcomers/props/gate-board-no-1.glb','inflation-chapter-2-newcomers/props/tin-mug-and-wages-envelope.glb','inflation-chapter-2-newcomers/props/crate-this-way-up.glb','inflation-chapter-2-newcomers/props/steel-drum-petrol.glb','inflation-chapter-2-newcomers/props/bank-brass-plate.glb','inflation-chapter-2-newcomers/props/chain-and-padlock.glb']:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=P+f)
    new=[o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    pts=[o.matrix_world @ mathutils.Vector(c) for o in new if o.type=='MESH' for c in o.bound_box]
    lo=[round(min(p[i] for p in pts),3) for i in range(3)]; hi=[round(max(p[i] for p in pts),3) for i in range(3)]
    print('PROP', f.split('/')[-1], 'bounds', lo, hi)
    for o in new:
        if o.type=='MESH':
            pp=[o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
            print('    ', o.name, [round(min(p[i] for p in pp),2) for i in range(3)], [round(max(p[i] for p in pp),2) for i in range(3)], [m.name for m in o.data.materials])
        else:
            print('    ', o.name, o.type)
    for o in new:
        bpy.data.objects.remove(o)
