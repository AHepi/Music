import sys, importlib.util, numpy as np
spec=importlib.util.spec_from_file_location('st','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_cottages_north.py')
st=importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
def manifold(V,F):
    from collections import Counter
    c=Counter()
    for f in F:
        for k in range(len(f)): c[(f[k],f[(k+1)%len(f)])]+=1
    bad=[e for e in c if c[e]>1 or c.get((e[1],e[0]),0)!=1]
    return len(bad), st._signed_volume(np.asarray(V),F)
for name,(V,F) in {
 'box':st.box(0,1,0,2,0,3),
 'post':st.lofted_post(0,0,0,2,.14,.14,(0.01,0.0),0.1,0.95),
 'extrude_x':st.extrude_x([(0,0),(1,0),(1,1),(0.5,0.3),(0,1)],0,2),
 'loft':st.loft_rings([[(x,0,0),(x,1,0),(x,1,1),(x,0,1)] for x in (0,1,2)]),
 'bowed':st.bowed_bar_x(0,3,1,0.16,0,0.12,0.01),
}.items():
    print(name,manifold(V,F))
# slab
us=st.subdivide_lines([0,0.5,1.0,2.0],0.25); vs=st.subdivide_lines([0,0.5,1.0,2.0],0.25)
for e_n,e_u in (((0,-1,0),(1,0,0)),((0,1,0),(-1,0,0)),((1,0,0),(0,1,0))):
    V,F,C=st.relief_slab((0,0,0),e_u,e_n,us,vs,0.1,lambda U,V:0.01*np.sin(U*7)*np.cos(V*5),None,holes=[(0.5,1.0,0.5,1.0)])
    print('slab',e_n,manifold(V,F),len(F),len(C))
