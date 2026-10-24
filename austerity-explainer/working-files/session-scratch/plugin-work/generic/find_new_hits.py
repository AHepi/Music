"""What this does: lists, for every file the 1.4.0 work added or changed, the lines (added ones only) that hold a word tied to the one-request test."""
import re, subprocess, sys, os
os.chdir('/home/user/Music/plugins/explainer-film')
pat = re.compile(sys.argv[1] if len(sys.argv) > 1 else r'forest|village|cottage|stable|horse|carriage|\bcarts?\b|hoof|hoov|thatch|wattle|manger|dung|straw|\blanes?\b|\bruts?\b|mediaeval|medieval|peasant|cobble|timber|daub|barn|\bhay\b|cattle|\bcows?\b|donkey|wagon|\bcarr', re.I)
tracked = subprocess.run(['git','diff','--name-only','25df5a4','--','.'],capture_output=True,text=True).stdout.split()
tracked = [t.replace('plugins/explainer-film/','') for t in tracked]
untracked = subprocess.run(['git','ls-files','--others','--exclude-standard','.'],capture_output=True,text=True).stdout.split()
out = {}
for f in tracked:
    if not os.path.exists(f): continue
    d = subprocess.run(['git','diff','-U0','25df5a4','--',f],capture_output=True,text=True).stdout
    for line in d.splitlines():
        if line.startswith('+') and not line.startswith('+++') and pat.search(line):
            out.setdefault(f,[]).append(line[1:])
for f in untracked:
    try:
        for i,line in enumerate(open(f,errors='replace')):
            if pat.search(line): out.setdefault(f,[]).append(line.rstrip('\n'))
    except Exception: pass
for f in sorted(out):
    print(f'{f}: {len(out[f])}')
if len(sys.argv) > 2:
    for f in sorted(out):
        print('=====',f)
        for l in out[f]: print('   ', l[:220])
