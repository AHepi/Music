# What this does: looks at every `code` span in the guides that looks like a file or folder path and reports the ones that cannot be found under
# any of the usual starting folders (the guide's folder, proc-work, recipes/<surface>, cookbook/checks/...). Placeholders such as NAME are reported too,
# so read the output by eye. Usage (from proc-work): python3 -I cookbook/checks/independent_check/check_code_paths.py . GUIDE.md [GUIDE.md ...]
import re, sys, os, glob
ROOT=os.path.abspath(sys.argv[1])
guides=sys.argv[2:]
surfaces=['brick','slate','wood','metal','mud','gravel','slate_layers']
EXT=r'\.(json|py|png|jpg|jpeg|exr|blend|md|sh|log|txt|flag|npy|csv)$'
res={}
for g in guides:
    folder=os.path.dirname(os.path.abspath(g))
    text=open(g,encoding='utf-8').read()
    for m in re.finditer(r'`([^`\n]+)`',text):
        t=m.group(1).strip()
        if ' ' in t and not re.search(EXT,t): continue
        if not ('/' in t or re.search(EXT,t)): continue
        if re.search(r'[=(){}\[\]*<>]',t) and '<surface>' not in t: continue
        if t.startswith('-') or t.startswith('python') : continue
        cand=t.rstrip('/').rstrip(',').rstrip('.')
        if '/.../' in cand: cand=cand.replace('/.../','/**/')
        if re.match(r'^lib/[\w/]+\.\w+$',cand) and not re.search(EXT,cand): cand=cand.rsplit('.',1)[0]+'.py'
        bases=[folder,ROOT,os.path.join(ROOT,'cookbook'),os.path.join(ROOT,'lib')]
        bases+= [os.path.join(ROOT,'recipes',s) for s in surfaces]
        bases+= [os.path.join(ROOT,'cookbook','checks'),os.path.join(ROOT,'recipes')]+glob.glob(os.path.join(ROOT,'cookbook','checks','*'))+glob.glob(os.path.join(ROOT,'research','*'))+glob.glob(os.path.join(ROOT,'research','*','*'))+glob.glob(os.path.join(ROOT,'recipes','*','*'))
        found=False
        if '<surface>' in cand:
            found=any(os.path.exists(os.path.join(ROOT,cand.replace('<surface>',s))) or os.path.exists(os.path.join(ROOT,'recipes',s,cand.replace('recipes/<surface>/',''))) for s in surfaces)
        else:
            for b in bases:
                p=os.path.join(b,cand)
                if os.path.exists(p) or glob.glob(p,recursive=True): found=True;break
            if not found and '/' not in cand:
                # bare filename: search anywhere
                hits=glob.glob(os.path.join(ROOT,'**',cand),recursive=True)
                found=bool(hits)
        if not found:
            line=text.count('\n',0,m.start())+1
            res.setdefault(os.path.relpath(g,ROOT),[]).append((line,t))
tot=0
for g,l in res.items():
    print('==',g,len(l))
    for line,t in l: print('   %d: %s'%(line,t)); tot+=1
print('unresolved',tot)
