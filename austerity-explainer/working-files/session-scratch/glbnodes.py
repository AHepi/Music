import json,struct,sys
for f in sys.argv[1:]:
    b=open(f,'rb').read(); n=struct.unpack('<I',b[12:16])[0]; j=json.loads(b[20:20+n])
    print('==',f)
    nodes=j['nodes']
    for s in j['scenes'][0]['nodes']:
        def walk(i,d):
            nd=nodes[i]; acc=''
            if 'mesh' in nd:
                m=j['meshes'][nd['mesh']]; p=m['primitives'][0]['attributes']['POSITION']; a=j['accessors'][p]; acc=f" min={[round(x,3) for x in a['min']]} max={[round(x,3) for x in a['max']]}"
            print('  '*d+nd.get('name','?'),'t',[round(x,3) for x in nd.get('translation',[0,0,0])],'r',[round(x,3) for x in nd.get('rotation',[0,0,0,1])],'s',nd.get('scale',''),acc)
            for c in nd.get('children',[]): walk(c,d+1)
        walk(s,0)
