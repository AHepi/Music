import json, re, sys
js = json.load(open(sys.argv[1], encoding='utf-8'))
acc = js['accent_instruction'] + ' '
allt = ' '.join(p['text'][len(acc):] for p in js['pages'])
print("hyphenated:", re.findall(r"\b\w+-\w+\b", allt))
print("digits:", re.findall(r"\d", allt))
print("brackets:", re.findall(r"[\[\]\(\)\{\}]", allt))
print("caps words:", [w for w in re.findall(r"\b[A-Z]{2,}\b", allt)])
print("exclaim:", allt.count('!'))
print("MMT:", 'MMT' in allt, "Mattei plain:", 'Mattei' in allt)
for w in ['rise','rising','raise','raised','raises','cost','unemployment','central bank','rates','spending','printing','fuel','not enough','shock','pay ','sellers','dearer','heartland','modern monetary']:
    print(w, [m.start() for m in re.finditer(re.escape(w), allt, re.I)][:10])
# text of every accent line
for p in js['pages']:
    t=p['text']
    if t.count('[')!=1: print('page',p['page'],'bracket count',t.count('['))
