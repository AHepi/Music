import os,sys,hashlib,json,collections
S='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/save-all'
AV={'.mp4','.webm','.mov','.mkv','.avi','.m4v','.mpg','.mpeg','.y4m','.mp3','.wav','.m4a','.aac','.flac','.ogg','.opus','.aif','.aiff','.wma'}
SKIP={'node_modules','.git','__pycache__','bvenv','.venv','venv','site-packages','.cache','.npm'}
def h(p):
    x=hashlib.sha1()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): x.update(b)
    return x.hexdigest()
known=set()
for base,dirs,files in os.walk('/home/user/Music'):
    dirs[:]=[d for d in dirs if d!='.git']
    for n in files:
        p=os.path.join(base,n)
        if os.path.isfile(p) and not os.path.islink(p): known.add(h(p))
plan=json.load(open(S+'/copy-plan.json'))
for s,t,n in plan['plan']:
    try: known.add(h(s))
    except Exception: pass
out=[]
for root in sys.argv[1:]:
    for base,dirs,files in os.walk(root):
        dirs[:]=[d for d in dirs if d not in SKIP]
        for n in files:
            p=os.path.join(base,n)
            if os.path.islink(p) or not os.path.isfile(p): continue
            e=os.path.splitext(n)[1].lower()
            if e in AV or e=='.pyc': continue
            if h(p) in known: continue
            out.append((p,os.path.getsize(p)))
json.dump(out,open(S+'/checker-tmp/extra.json','w'))
c=collections.Counter(); z=collections.Counter()
for p,s in out:
    k='/'.join(p.split('/')[:6]) if p.startswith('/tmp/claude-0') else '/'.join(p.split('/')[:4])
    c[k]+=1; z[k]+=s
for k,v in c.most_common(): print(v, round(z[k]/1e6,2),'MB',k)
