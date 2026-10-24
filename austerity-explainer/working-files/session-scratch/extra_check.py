import hashlib,os,sys
def fp(p):
    h=hashlib.sha1()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
repo=sys.argv[1]; held=sys.argv[2]
idx={}
for d,ds,fs in os.walk(repo):
    ds[:]=[x for x in ds if x not in {'.git','node_modules'}]
    for n in fs:
        p=os.path.join(d,n)
        if os.path.isfile(p) and not os.path.islink(p): idx.setdefault(fp(p),p)
hidx={}
for d,ds,fs in os.walk(held):
    for n in fs: p=os.path.join(d,n); hidx.setdefault(fp(p),p)
for p in sys.argv[3:]:
    if os.path.isdir(p):
        files=[os.path.join(d,n) for d,ds,fs in os.walk(p) for n in fs]
    else: files=[p]
    for f in files:
        if os.path.getsize(f)>200e6: print('BIG',f); continue
        h=fp(f)
        print('REPO' if h in idx else ('HELD' if h in hidx else 'MISSING'), os.path.getsize(f), f, idx.get(h,''))
