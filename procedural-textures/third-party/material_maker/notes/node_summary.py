# Plain note: one-line-per-item summary of Material Maker node types: settings (name default [min..max]), input ports (index name type), output ports (index type).
# Usage: python3 -I node_summary.py TYPE [TYPE ...]
import json,sys
B='proc-work/third-party/material_maker/app/material_maker_1_7_linux/nodes/'
for t in sys.argv[1:]:
    d=json.load(open(B+t+'.mmg'))
    if 'nodes' in d and 'shader_model' not in d:
        print(f'## {t}  [GROUP of {len(d["nodes"])} sub-nodes]'); 
        print('   params:', json.dumps(d.get('parameters'))[:400]); 
        for n in d['nodes']:
            if n['type'] in ('remote','comment'): continue
            print('     sub:',n['name'],n['type'])
        continue
    sm=d['shader_model']
    print(f'## {t}  -- {sm.get("shortdesc")}')
    print('   params:', '; '.join(f'{p["name"]}={p.get("default")}'+(f'[{p.get("min")}..{p.get("max")}]' if 'min' in p else '')+(f'{{{",".join(str(v["name"]) for v in p["values"])}}}' if p.get('type')=='enum' else '') for p in sm.get('parameters',[])))
    print('   inputs:', '; '.join(f'{i}:{x["name"]}({x["type"]})' for i,x in enumerate(sm.get('inputs',[]))))
    print('   outputs:', '; '.join(f'{i}:{x.get("shortdesc","")}({x["type"]})' for i,x in enumerate(sm.get('outputs',[]))))
