# Plain note: prints a Material Maker node definition (.mmg file) in readable form: settings, inputs, outputs, and the
# shader code that makes the picture. Usage: python3 -I show_node.py NODE_TYPE [NODE_TYPE ...]
import json,sys
B='proc-work/third-party/material_maker/app/material_maker_1_7_linux/nodes/'
for t in sys.argv[1:]:
    d=json.load(open(B+t+'.mmg'))
    print('='*100); print('NODE', t, '| keys:', list(d.keys()))
    if d.get('type')=='graph' or 'nodes' in d:
        print('(group node: made of sub-nodes)'); 
        for n in d['nodes']: print('   sub-node', n['name'], n['type'], json.dumps(n.get('parameters',{}))[:200])
        print('   connections', json.dumps(d['connections'])[:800]); print('   parameters', json.dumps(d.get('parameters'))[:300]); continue
    sm=d.get('shader_model',d)
    print('desc:', sm.get('shortdesc'),'|',sm.get('longdesc'))
    print('params:')
    for p in sm.get('parameters',[]): print('   ',{k:v for k,v in p.items() if k not in ('widget',)})
    print('defaults:', json.dumps(d.get('parameters'))[:600])
    print('inputs:', json.dumps(sm.get('inputs'))[:600])
    print('outputs:', json.dumps(sm.get('outputs'))[:900])
    print('global:'); g=sm.get('global',''); print('\n'.join(g) if isinstance(g,list) else g)
    print('instance:'); print(sm.get('instance',''))
    print('code:'); print(sm.get('code',''))
