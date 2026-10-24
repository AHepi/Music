import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit.render import client as c
env = {'RENDER_SETTINGS_FILE': '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/review/cfg/settings.json'}
try:
    s = c.read_settings(env)
    print('missing:', s.missing(), '| store:', s.store_folder)
except Exception as e:
    print('error:', type(e).__name__, str(e)[:200])
