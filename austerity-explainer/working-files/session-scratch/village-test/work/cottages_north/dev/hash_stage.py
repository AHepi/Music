import sys, importlib.util, hashlib, numpy as np, bpy
spec=importlib.util.spec_from_file_location('stage_cn','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_cottages_north.py')
st=importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
st.apply({})
h=hashlib.sha1()
for o in sorted([o for o in bpy.data.objects if o.get('place_owner')=='cottages_north'], key=lambda o:o.name):
    v=np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get('co',v)
    h.update(o.name.encode()); h.update(np.round(v,5).tobytes()); h.update(np.round(np.array(o.location),5).tobytes())
print('STAGEHASH',h.hexdigest())
