import sys, re, os, glob, argparse
sys.dont_write_bytecode = True
ROOT = '/home/user/Music/plugins/explainer-film'
sys.path.insert(0, ROOT + '/kit/place-kit')
from place_kit import cli
parser = cli.build_parser()
sub = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][0]
verbs = {}
for name, p in sub.choices.items():
    opts = set()
    for a in p._actions:
        opts.update(a.option_strings)
    verbs[name] = opts
files = []
for pat in ('**/*.md', '**/*.js', '**/*.json', '**/*.py', '**/*.sh', 'bin/*'):
    files += glob.glob(os.path.join(ROOT, pat), recursive=True)
files = [f for f in set(files) if '__pycache__' not in f and '/tests/fixtures/works' not in f and 'examples/' not in f.split('kit/')[-1][:9]]
pat = re.compile(r'explainer-film-place\s+([a-z][a-z-]*)((?:[^`\n"\']|\\\n)*)')
problems = []
count = 0
for f in sorted(files):
    try:
        text = open(f, encoding='utf-8').read()
    except Exception:
        continue
    for m in pat.finditer(text):
        verb = m.group(1)
        if verb in ('is', 'the', 'a', 'and', 'or', 'to', 'for', 'verb', 'in', 'as', 'then', 'with', 'when', 'it', 'do', 'on', 'does', 'says', 'has', 'can', 'that', 'was', 'will', 'must', 'never', 'only', 'runs', 'which', 'also', 'if', 'not', 'one', 'finish', 'prints'):
            if verb not in verbs:
                continue
        count += 1
        if verb not in verbs:
            problems.append((os.path.relpath(f, ROOT), 'unknown verb', verb, m.group(0)[:100]))
            continue
        rest = m.group(2)
        for o in re.findall(r'(?<![\w-])(--[a-z][a-z0-9-]*)', rest):
            if o not in verbs[verb]:
                problems.append((os.path.relpath(f, ROOT), 'unknown option for ' + verb, o, m.group(0)[:100].replace('\n', ' ')))
print('commands checked:', count)
for p in problems:
    print(p)
