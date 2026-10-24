import re, glob, os, collections
def words(path):
    t=open(path,encoding='utf-8',errors='ignore').read().lower()
    return re.findall(r"[a-z0-9']+", t)
def wsh(ws,k=8): return {' '.join(ws[i:i+k]) for i in range(len(ws)-k+1)}
sc=[f for f in glob.glob('/home/user/Music/.claude/skills/scenario-*/**/*',recursive=True) if os.path.isfile(f)]
bank=set()
for f in sc: bank|=wsh(words(f))
SP='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/review/'
old=wsh(words(SP+'old_notes.md'))
new=wsh(words('/home/user/Music/plugins/explainer-film/skills/make-3d-models/blender-mcp-notes.md'))
print('old overlap', len(old&bank), 'new overlap', len(new&bank), 'new-only overlap', len((new-old)&bank))
