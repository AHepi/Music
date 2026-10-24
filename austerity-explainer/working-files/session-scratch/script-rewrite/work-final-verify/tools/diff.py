import re, sys, difflib
def pages(md):
    t = open(md).read()
    out = {}
    for m in re.finditer(r'^### Page (\d+) - [^\n]*\n\n([^\n]+)\n', t, re.M):
        out[int(m.group(1))] = m.group(2)
    return out
def txtpages(p):
    t = open(p).read()
    out = {}
    for m in re.finditer(r'^## Page (\d+) - [^\n]*\n([^\n]+)', t, re.M):
        out[int(m.group(1))] = m.group(2)
    return out
def sents(s):
    return [x.strip() for x in re.split(r'(?<=[.?!])\s+', s) if x.strip()]
a = pages(sys.argv[1]); b = pages(sys.argv[2]); c = txtpages(sys.argv[3])
for k in sorted(b):
    if b[k] != c.get(k): print("MISMATCH md vs txt page", k)
tot=0
for k in sorted(b):
    sa, sb = sents(a[k]), sents(b[k])
    sm = difflib.SequenceMatcher(None, sa, sb)
    print(f"=== Page {k}: words {len(a[k].split())} -> {len(b[k].split())}")
    for op,i1,i2,j1,j2 in sm.get_opcodes():
        if op=='equal': continue
        for x in sa[i1:i2]: print("  - ", x)
        for x in sb[j1:j2]: print("  + ", x, f"[{len(x.split())}w]"); tot+=1
print("changed/new sentences:", tot)
wa = sum(len(v.split()) for v in a.values()); wb = sum(len(v.split()) for v in b.values())
print("words", wa, wb)
print("pauses", sum(v.count('...') for v in b.values()))
for k in sorted(b):
    for s in sents(b[k]):
        n=len(s.split())
        if n>=16: print("long", k, n, s)
