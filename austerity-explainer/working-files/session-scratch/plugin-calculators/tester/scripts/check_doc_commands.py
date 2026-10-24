"""Tester's scratch: read every command the plugin's docs and skills write, and check the tool, subcommand and each flag
against the tool's own --help."""
import glob, os, re, shlex, subprocess, sys, json
PLUGIN = '/home/user/Music/plugins/explainer-film'
KIT = PLUGIN + '/kit'
docs = glob.glob(PLUGIN + '/skills/**/*.md', recursive=True) + [PLUGIN + '/README.md', KIT + '/docs/LLM tips and tricks.md', KIT + '/calculators/README.md']
TOOL_RE = re.compile(r'((?:kit/)?(?:calculators|narration-tools|paper-film/tools|paper-film/blender)/[\w-]+\.(?:py|mjs|sh))|(explainer-film-preflight)')
help_cache = {}
def tool_help(tool, sub=None):
    key = (tool, sub)
    if key in help_cache: return help_cache[key]
    if tool == 'explainer-film-preflight':
        cmd = [PLUGIN + '/bin/explainer-film-preflight', '--help']
    else:
        path = os.path.join(KIT, tool.replace('kit/', '', 1))
        if not os.path.exists(path):
            help_cache[key] = None; return None
        if path.endswith('.py'):
            cmd = ['python3', path] + ([sub] if sub else []) + ['--help']
        elif path.endswith('.mjs'):
            cmd = ['node', path, '--help']
        else:
            help_cache[key] = ''; return ''
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=KIT)
        help_cache[key] = (r.stdout + r.stderr, r.returncode)
    except Exception as e:
        help_cache[key] = (str(e), 99)
    return help_cache[key]
problems = []
count = 0
for doc in docs:
    text = open(doc).read()
    # code spans and code block lines
    snippets = re.findall(r'`([^`\n]+)`', text)
    for block in re.findall(r'```[^\n]*\n(.*?)```', text, re.S):
        snippets += block.splitlines()
    for snip in snippets:
        m = TOOL_RE.search(snip)
        if not m: continue
        tool = m.group(1) or m.group(2)
        rest = snip[m.end():]
        try:
            words = shlex.split(rest.replace('...', ' '), posix=True)
        except ValueError:
            words = rest.split()
        sub = None
        if tool != 'explainer-film-preflight' and words and re.match(r'^[a-z][a-z-]+$', words[0]) and not words[0].startswith('-'):
            sub = words[0]
        flags = [w.split('=')[0] for w in words if w.startswith('--') and len(w) > 2]
        flags = [f.rstrip('.,;:)]') for f in flags]
        h = tool_help(tool, sub)
        count += 1
        if h is None:
            problems.append((os.path.basename(doc), tool, 'TOOL MISSING', snip[:120])); continue
        if h == '': continue
        out, code = h
        if code not in (0,) :
            # subcommand may not exist
            if sub:
                h2 = tool_help(tool, None)
                if h2 and sub not in h2[0]:
                    problems.append((os.path.basename(doc), tool, f'subcommand {sub!r} not in --help (exit {code})', snip[:140]))
                    continue
                out = h2[0] if h2 else out
            else:
                problems.append((os.path.basename(doc), tool, f'--help exit {code}', out[-200:])); continue
        for f in flags:
            if f in ('--help',): continue
            if re.search(re.escape(f) + r'(?![\w-])', out) is None:
                # Blender/node style flags after '--' belong to the inner tool; skip python/blender's own
                problems.append((os.path.basename(doc), tool + (' ' + sub if sub else ''), f'flag {f} not in --help', snip[:160]))
print('commands checked:', count)
seen=set()
for p in problems:
    k=(p[1],p[2])
    if k in seen: continue
    seen.add(k); print(' | '.join(p))
