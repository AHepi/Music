"""What this does: adds the Blender 5.2 probe and the film-kit check to bin/explainer-film-setup (a one-off edit for the lessons round)."""
p = '/home/user/Music/plugins/explainer-film/bin/explainer-film-setup'
s = open(p).read()
old = '''  else
    echo "  blender's own Python has no Pillow: normal, the place kit and model_kit.py need none (a script that draws text with Pillow does: run that part outside Blender)"
  fi
else'''
new = '''  else
    echo "  blender's own Python has no Pillow: normal, the place kit and model_kit.py need none (a script that draws text with Pillow does: run that part outside Blender)"
  fi
  # Blender 5.2 traps: which way works in THIS Blender (a Geometry Nodes modifier input set both ways; one light-linking pairing read back)
  probe=$("$blender" -b --disable-autoexec --python "$HERE/kit/place-kit/probe_blender.py" 2>/dev/null | sed -n '/^Blender 5.2 probe/,/^  light linking/p')
  if [ -n "$probe" ]; then echo "$probe"; else echo "Blender 5.2 probe: it could not be run with $blender (see kit/place-kit/probe_blender.py)"; fi
else'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''echo "next: read the make-explainer-film skill; docs are in $TARGET/docs (start with 'paper-look - 00 START HERE.md')"'''
new = '''# the project's film kit, when it is on this machine (FILM_KIT, else FILM_PROJECT/film-kit, else the project folder next to the plugins folder,
# as the tests find it): its files changed after the plugin's last copy, by the newest date in kit/kit-sync-notes.md
python3 -I - "$HERE" <<'SYNC'
import datetime, os, re, sys
plugin = sys.argv[1]
project = os.environ.get('FILM_PROJECT') or os.path.normpath(os.path.join(plugin, '..', '..', 'austerity-explainer'))
film_kit = os.environ.get('FILM_KIT') or os.path.join(project, 'film-kit')
if not os.path.isdir(film_kit):
    print('film kit: not on this machine (set FILM_KIT to compare it with the plugin\\'s copy)')
    sys.exit(0)
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
dates = []
for line in open(os.path.join(plugin, 'kit', 'kit-sync-notes.md'), encoding='utf-8'):
    if line.startswith('#'):
        for day, month, year in re.findall(r'\\b(\\d{1,2}) (' + '|'.join(months) + r') (\\d{4})\\b', line):
            dates.append(datetime.datetime(int(year), months.index(month) + 1, int(day)))
if not dates:
    print('film kit: kit/kit-sync-notes.md names no copy date, so newer files cannot be listed')
    sys.exit(0)
last = max(dates)
after = (last + datetime.timedelta(days=1)).timestamp()
newer = []
for folder, folders, files in os.walk(film_kit):
    folders[:] = [f for f in folders if f not in ('node_modules', 'out', '.git', '__pycache__', 'assets')]
    for name in files:
        path = os.path.join(folder, name)
        if not name.endswith('.pyc') and os.path.getmtime(path) >= after:
            newer.append(os.path.relpath(path, film_kit))
print(f'film kit ({film_kit}): {len(newer)} file(s) changed after the plugin\\'s last copy ({last:%d %B %Y}, kit/kit-sync-notes.md)'
      + (':' if newer else '; nothing to copy'))
for path in sorted(newer)[:15]:
    print(f'  {path}')
if len(newer) > 15:
    print(f'  and {len(newer) - 15} more')
SYNC
echo "next: read the make-explainer-film skill; docs are in $TARGET/docs (start with 'paper-look - 00 START HERE.md')"'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''# checks that every kit file the plugin's skills name (paper-film, narration-tools, examples, docs, place-kit) is in the kit.'''
new = '''# checks that every kit file the plugin's skills name (paper-film, narration-tools, examples, docs, place-kit) is in the kit.
# With Blender found it prints a "Blender 5.2 probe" block: which way of setting a Geometry Nodes modifier input works in this Blender,
# and how a collection's light-linking entries pair with its objects (kit/place-kit/probe_blender.py). When the project's film kit
# is on this machine it lists the film kit files changed after the plugin's last copy (the newest date in kit/kit-sync-notes.md).'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, 'w').write(s)
print('ok')
