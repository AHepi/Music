import sys, re, os, glob, collections
sys.dont_write_bytecode = True
ROOT='/home/user/Music/plugins/explainer-film'
SP='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
def norm_lines(path):
    out=[]
    try:
        for ln in open(path, encoding='utf-8', errors='ignore'):
            s=re.sub(r'\s+',' ',ln.strip())
            if len(s)>=25 and not s.startswith('#') :
                out.append(s)
    except Exception: pass
    return out
def shingles(lines, k):
    return {' || '.join(lines[i:i+k]) for i in range(len(lines)-k+1)}
def collect(patterns):
    files=[]
    for p in patterns: files+=glob.glob(p, recursive=True)
    return [f for f in files if os.path.isfile(f) and '__pycache__' not in f]
plugin_files = collect([ROOT+'/kit/place-kit/**/*.py', ROOT+'/kit/calculators/place_audit_check.py', ROOT+'/kit/calculators/picture_measures.py', ROOT+'/kit/paper-film/blender/*.py', ROOT+'/kit/calculators/tests/*.py'])
def compare(label, src_files, k=3):
    bank=collections.defaultdict(set)
    for f in src_files:
        for s in shingles(norm_lines(f), k):
            bank[s].add(f)
    hits=collections.Counter()
    for f in plugin_files:
        for s in shingles(norm_lines(f), k):
            if s in bank:
                hits[f]+=1
    print(label, 'source files:', len(src_files), 'shingle bank:', len(bank))
    for f,c in hits.most_common(12):
        print('   ', c, os.path.relpath(f, ROOT))
    if not hits: print('    no overlap')
astra=collect([SP+'/astra-upload/**/*.py', SP+'/astra-upload-021/**/*.py', SP+'/astra-work/**/*.py'])
compare('ASTRA (3 consecutive identical code lines of >=25 chars)', astra, 3)
compare('ASTRA k=2', astra, 2)

print('--- words (8-gram) against Scenario skills')
def words(path):
    try: t=open(path,encoding='utf-8',errors='ignore').read().lower()
    except Exception: return []
    return re.findall(r"[a-z0-9']+", t)
def wsh(ws,k=8): return {' '.join(ws[i:i+k]) for i in range(len(ws)-k+1)}
sc_files = collect(['/home/user/Music/.claude/skills/scenario-*/**/*'])
sc_files=[f for f in sc_files if f.endswith(('.md','.py','.txt','.json'))]
bank=collections.defaultdict(set)
for f in sc_files:
    for s in wsh(words(f)): bank[s].add(f)
doc_files = collect([ROOT+'/skills/**/*.md', ROOT+'/agents/*.md', ROOT+'/kit/place-kit/**/*.md', ROOT+'/kit/place-kit/**/*.py', ROOT+'/kit/docs/*.md', ROOT+'/README.md', ROOT+'/kit/place-kit/data/**/*.json', ROOT+'/workflows/build-a-place.js'])
print('scenario files', len(sc_files), 'bank', len(bank))
hits=collections.Counter(); ex={}
for f in doc_files:
    for s in wsh(words(f)):
        if s in bank:
            hits[f]+=1; ex.setdefault(f,[]).append(s)
for f,c in hits.most_common(15):
    print('  ',c, os.path.relpath(f,ROOT), '| e.g.:', ex[f][0])
if not hits: print('   no 8-word overlap')
