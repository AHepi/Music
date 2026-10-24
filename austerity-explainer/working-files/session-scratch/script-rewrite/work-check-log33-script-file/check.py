import json, re, sys
md = open(sys.argv[1], encoding='utf-8').read()
js = json.load(open(sys.argv[2], encoding='utf-8'))
acc = js['accent_instruction'] + ' '
# extract md pages
pages = re.findall(r'^### Page (\d+) - (.*?)\n\n(.*?)\n\n', md, re.M|re.S)
mdp = {int(n): (t, body) for n, t, body in pages}
print("md pages:", len(mdp), "json pages:", len(js['pages']))
tot_words=0; tot_said=0; tot_pauses=0; tot_chars=0; tot_chars_noacc=0
sentences=[]
for p in js['pages']:
    n=p['page']; txt=p['text']
    if not txt.startswith(acc): print("page",n,"missing accent prefix")
    body = txt[len(acc):]
    if n not in mdp: print("page",n,"not in md"); continue
    if body != mdp[n][1]:
        print("DIFF page", n); print(" md:", mdp[n][1]); print(" js:", body)
    # count words: split on whitespace, treat "..." joined words
    w = re.sub(r'\.\.\.', ' ', body)
    words = re.findall(r"[A-Za-z0-9/ˈəɪ'’\-]+", w)
    words = [x for x in words if re.search(r'[A-Za-z0-9ə]', x)]
    nw=len(words)
    pauses = body.count('...')
    tot_words+=nw; tot_pauses+=pauses; tot_chars+=len(txt); tot_chars_noacc+=len(body)
    # sentences
    for s in re.split(r'(?<=[.?!])\s+(?=[A-Z])', body):
        s2=re.sub(r'\.\.\.',' ',s)
        sw=[x for x in re.findall(r"[A-Za-z0-9/ˈəɪ'’\-]+", s2) if re.search(r'[A-Za-z0-9ə]', x)]
        sentences.append((n,len(sw),s))
    print(f"page {n}: words {nw}, pauses {pauses}, chars {len(txt)}")
print("total words", tot_words, "pauses", tot_pauses, "chars with accent", tot_chars, "without", tot_chars_noacc)
print("sentences", len(sentences), "avg", tot_words/len(sentences))
for n,l,s in sorted(sentences, key=lambda x:-x[1])[:8]: print(n,l,s)
