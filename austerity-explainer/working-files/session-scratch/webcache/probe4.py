import bpy
t=bpy.data.node_groups.new('c','CompositorNodeTree')
n=t.nodes.new('CompositorNodeTranslate')
for name in ('Interpolation','Extension X','Extension Y'):
    s=n.inputs[name]
    print(name,'default',repr(s.default_value))
    try:
        items=[i.identifier for i in s.bl_rna.properties['default_value'].enum_items]
        print('  items',items)
    except Exception as e:
        print('  no enum_items',e)
        for cand in ('Repeat','REPEAT','Wrap','WRAP','Extend','Clip','Mirror','Nearest','Bilinear'):
            try:
                s.default_value=cand; print('  accepted',cand); 
            except Exception as e2: pass
f=t.nodes.new('CompositorNodeFilter')
s=f.inputs['Type']; print('filter type default',repr(s.default_value))
try: print([i.identifier for i in s.bl_rna.properties['default_value'].enum_items])
except Exception as e: print('no items',e)
