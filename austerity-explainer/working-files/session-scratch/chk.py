import re,os,subprocess,glob,sys
R='/home/user/Music'
os.chdir(R)
tracked=set(subprocess.check_output(['git','ls-files'],text=True).splitlines())
dirs=set()
for t in tracked:
    p=t
    while '/' in p:
        p=p.rsplit('/',1)[0]; dirs.add(p)
A='austerity-explainer'
files=['README.md']+sorted(glob.glob(A+'/*.md')+glob.glob(A+'/project-notes/*.md')+glob.glob(A+'/chapter-2-inflation/*.md')+glob.glob(A+'/film-kit/*.md'))+[A+'/film-kit/assets/soundtrack/00 What goes here.md',A+'/film-kit/paper-film/pieces/00 What goes here.md','plugins/explainer-film/README.md']
bases=['', None, A, A+'/film-kit', A+'/film-kit/paper-film', A+'/film-kit/paper-film/scenes', A+'/film-kit/paper-film/tools', A+'/film-kit/narration-tools', A+'/chapter-2-inflation', A+'/chapter-2-inflation/film-code', A+'/film-kit/assets','plugins/explainer-film','plugins/explainer-film/kit/paper-film', A+'/project-notes', A+'/research', A+'/scripts-and-plans', A+'/film-kit/examples']
names={os.path.basename(t) for t in tracked}|{os.path.basename(d) for d in dirs}
def exists(s,f):
    s=s.strip().rstrip('/').strip()
    if s.startswith('./'): s=s[2:]
    for b in bases:
        b=os.path.dirname(f) if b is None else b
        p=os.path.normpath(os.path.join(b,s)) if b else os.path.normpath(s)
        if p in tracked or p in dirs: return 'ok'
        if os.path.exists(os.path.join(R,p)): return 'wt'
    if os.path.basename(s) in names: return 'name'
    if '*' in s or '<' in s or '{' in s: return 'pattern'
    return None
pathlike=re.compile(r'(/|\.(md|js|mjs|json|py|sh|mp3|mp4|flac|wav|png|jpg|glb|html|srt|vtt|txt|zip|blend|webm|mov)\b)')
for f in files:
    for i,line in enumerate(open(f),1):
        cands=re.findall(r'`([^`\n]+)`',line)+re.findall(r'"([^"\n]{3,120}\.(?:md|js|mjs|json|py|sh|mp3|mp4|flac|wav|png|jpg|glb|html|srt|vtt|txt|zip|blend|mov))"',line)+re.findall(r'\]\(([^)]+)\)',line)
        for c in cands:
            if not pathlike.search(c): continue
            if c.startswith('http'): continue
            r=exists(c,f)
            if r in ('ok',): continue
            print(f"{f}:{i}: [{r}] {c}")
