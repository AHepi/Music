"""Replaces this machine's session-folder paths (and a few machine paths in fixture notes) in the plugin with plain words."""
import os, re, sys
ROOT = '/home/user/Music/plugins/explainer-film'
SESSION = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
changed = {}
for folder, folders, files in os.walk(ROOT):
    folders[:] = [f for f in folders if f not in ('node_modules', '__pycache__', '.git')]
    for name in files:
        path = os.path.join(folder, name)
        if name.endswith(('.gz', '.png', '.jpg', '.glb', '.whl', '.pyc', '.blend', '.mp3', '.mp4', '.wav')):
            continue
        try:
            text = open(path, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        original = text
        text = text.replace(f'(the log 34 working folder: {SESSION}/redesign/)', '')
        text = text.replace(f'SCRATCH is {SESSION}; FILM is /home/user/Music/austerity-explainer/film-kit.',
                            'WORKING is the project\'s working files from the redesign rounds (never in the repository; the tests read them '
                            'through FILM_WORKING_FILES); FILM is the project\'s film kit (austerity-explainer/film-kit).')
        text = text.replace('SCRATCH/', 'WORKING/')
        # a path quoted inside a recorded log line keeps its quote: '<working files>/...'
        text = re.sub(r"(['\"])" + re.escape(SESSION) + '/', lambda m: m.group(1) + '<working files>/', text)
        text = text.replace(SESSION + '/', 'working files ')
        text = text.replace(SESSION, 'the working files')
        text = re.sub(r'\bscratchpad (?=[A-Za-z(])', 'working files ', text)
        text = text.replace('(scratchpad\n', '(working files\n')
        if 'kit/calculators/tests/fixtures' in path or name in ('film-settings.json',):
            text = text.replace('/home/user/Music/austerity-explainer/', 'austerity-explainer/')
            text = text.replace('/home/user/work/blender-app/blender-5.2.2-linux-x64/', '<blender>/')
            text = text.replace('/home/user/work/paper-pop-up-film-kit/', '<the film kit as it was then>/')
            text = text.replace('/home/user/work/chapter-2/', 'the chapter 2 work folder\'s ')
        if text != original:
            changed[path] = (original.count(SESSION) + len(re.findall(r'\bscratchpad', original)))
            if '--dry' not in sys.argv:
                open(path, 'w', encoding='utf-8').write(text)
for path, n in sorted(changed.items()):
    print(n, path.replace(ROOT + '/', ''))
