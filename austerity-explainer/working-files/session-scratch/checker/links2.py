# Independent link checker: finds [text](target) and ![alt](target) with balanced parentheses, <img src>, and reference-style links.
import re, sys, os, urllib.parse
def find_links(text):
    out=[]
    i=0
    n=len(text)
    while True:
        j=text.find('](',i)
        if j<0: break
        # find the matching '[' backwards (allow nested)
        k=j+2; depth=1; m=k
        if k<n and text[k]=='<':
            e=text.find('>',k)
            tgt=text[k+1:e]; out.append((text.count('\n',0,j)+1,tgt)); i=e; continue
        while m<n and depth>0:
            if text[m]=='(': depth+=1
            elif text[m]==')': depth-=1
            elif text[m]=='\n': break
            m+=1
        tgt=text[k:m-1] if depth==0 else text[k:m]
        tgt=re.sub(r'\s+"[^"]*"$','',tgt)
        out.append((text.count('\n',0,j)+1,tgt)); i=m
    for mm in re.finditer(r'<img[^>]+src="([^"]+)"',text):
        out.append((text.count('\n',0,mm.start())+1,mm.group(1)))
    for mm in re.finditer(r'^\[[^\]]+\]:\s*(\S+)',text,re.M):
        out.append((text.count('\n',0,mm.start())+1,mm.group(1)))
    return out
bad=0; total=0
for g in sys.argv[1:]:
    folder=os.path.dirname(os.path.abspath(g))
    text=open(g,encoding='utf-8').read()
    for line,t in find_links(text):
        if re.match(r'^[a-z]+://',t) or t.startswith('#') or t.startswith('mailto:'): continue
        fp=urllib.parse.unquote(t.split('#')[0])
        if not fp: continue
        total+=1
        if not os.path.exists(os.path.join(folder,fp)):
            bad+=1; print('BROKEN %s:%d: %s'%(os.path.relpath(g),line,t))
print('checked',total,'broken',bad)
