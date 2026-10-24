import os, re, sys
skills, kit = sys.argv[1], sys.argv[2]
named, missing = set(), []
for folder, _, files in os.walk(skills):
    for name in files:
        if name.endswith('.md'):
            for text in re.findall(r'`([^`\n]+)`', open(os.path.join(folder, name), encoding='utf-8').read()):
                whole = re.sub(r'^(\$\{CLAUDE_PLUGIN_ROOT\}/)?(film-)?kit/', '', text.strip())
                # a whole name with spaces in it ("docs/paper-look - 07 Composing a shot.md"), else each word of a command
                words = [whole] if ' ' in whole and os.path.exists(os.path.join(kit, whole)) else text.split()
                for word in words:
                    word = word.strip('"\'(),;:')
                    word = re.sub(r'^(\$\{CLAUDE_PLUGIN_ROOT\}/)?(film-)?kit/', '', word)
                    if not re.match(r'(paper-film|narration-tools|examples|docs)/', word):
                        continue
                    if re.search(r'[<>*{}$]|\bN\b|NAME|CHAPTER|\.\.\.', word) or word.endswith('/') or word.startswith('paper-film/out/'):
                        continue   # a pattern, a folder or something a tool writes, not a kit file
                    named.add(word)
for path in sorted(named):
    if not os.path.exists(os.path.join(kit, path)):
        missing.append(path)
print(f'files the skills name: {len(named)} checked, {len(missing)} missing from the kit' + ('' if not missing else ':'))
for path in missing:
    print(f'  {path}')
