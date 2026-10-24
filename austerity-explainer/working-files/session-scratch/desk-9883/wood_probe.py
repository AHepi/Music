import sys, types, math
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/blender')
import textures as tx, numpy as np
from PIL import Image
src = open('/home/user/work/paper-pop-up-film-kit/paper-film/blender/build_desk.py').read()
start = src.index('def desk_wood_pictures'); end = src.index('def leather_pictures')
ns = {'tx': tx, 'np': np, 'math': math, 'Image': Image}
exec(src[start:end], ns)
c, n, r = ns['desk_wood_pictures']()
c.crop((0, 0, 512, 512)).save('wood_c.png'); n.crop((0, 0, 512, 512)).save('wood_n.png')
