# What this does: reads a narration file (pages start with "## ") and lists things that trip the ear:
# spoken numbers per page and per sentence, sentence lengths, sentences starting with "So",
# "rise" and "raise" in the same sentence, the same content word twice within a few words,
# stock bridge phrases, and figurative uses of "cost".
import re, sys
NUM = r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|half|quarter|nineteen)\b"
STOCK = ["here's the question","here's the answer","here's the rule","hold on to that","look closer","the answer matters",
 "getting this right matters","it matters","this really happened","sees it differently","next time","remember the two",
 "back to the question","now test the warning","this one's ours","so were world events","not just","it's not","isn't just"]
STOP = set("the a an and of to in on it its it's is was were be that this there their they for with at by from as but so if not no more what who when then".split())
def pages(t):
    out=[];title=None;buf=[]
    for l in t.splitlines():
        if l.startswith("## "):
            if title: out.append((title," ".join(buf)))
            title=l[3:];buf=[]
        else: buf.append(l)
    if title: out.append((title," ".join(buf)))
    return out
def sents(t): return [s.strip() for s in re.split(r"(?<=[.?!])\s+", t.replace("..."," … ")) if s.strip()]
text=open(sys.argv[1],encoding="utf-8").read()
tot_nums=0; so_open=0; lens=[]
for title,body in pages(text):
    ss=sents(body); notes=[]
    # group number words into spoken figures: count runs
    figs=0
    for s in ss:
        runs=re.findall(r"(?:"+NUM+r"(?:[ -](?:and |point |in every |in |percent|a |of a )*)?)+", s.lower())
        n=len([r for r in runs if r.strip()])
        figs+=n
        if n>=2: notes.append(f"   {n} figures in one sentence: {s}")
        w=len(re.findall(r"[A-Za-z'/ˈə-]+",s)); lens.append(w)
        if w>=16: notes.append(f"   long ({w} words): {s}")
        if re.match(r"So\b",s): so_open+=1
        if re.search(r"\bris(e|es|ing)\b",s.lower()) and re.search(r"\brais(e|es|ed)\b",s.lower()): notes.append(f"   rise/raise in one sentence: {s}")
        if re.search(r"\bcost",s.lower()): notes.append(f"   'cost' here: {s}")
    words=[w.lower() for w in re.findall(r"[A-Za-z'-]+",body)]
    for i,w in enumerate(words):
        if w in STOP or len(w)<4: continue
        if w in words[i+1:i+6]: notes.append(f"   '{w}' twice within five words")
    for st in STOCK:
        if st in body.lower(): notes.append(f"   stock/bridge: '{st}'")
    tot_nums+=figs
    print(f"{title}: {len(ss)} sentences, ~{figs} spoken figures")
    for n in dict.fromkeys(notes): print(n)
print(f"TOTAL ~{tot_nums} spoken figures; sentences starting 'So': {so_open}; mean sentence {sum(lens)/len(lens):.1f} words; max {max(lens)}")
