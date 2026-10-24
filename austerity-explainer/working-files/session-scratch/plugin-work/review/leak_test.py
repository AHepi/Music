import sys, io, urllib.error
sys.dont_write_bytecode = True
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit.render import client as c
class P: pass
settings = c.RentSettings('FAKEKEY123456789', 'fakeendpointid99', '/workspace', '/workspace/blender/blender', 'test')
def opener(request, timeout=0):
    raise urllib.error.URLError('down')
t = c.WebTransport(settings, opener=opener, sleep=lambda s: None)
try:
    t.call('GET', '/health', attempts=2)
except c.RentFailed as e:
    print('MESSAGE:', e)
    print('leaks endpoint id:', 'fakeendpointid99' in str(e))
