# Builds the pictures for the person from the RunPod previews. usage: make_pictures.py RUNFOLDER OUTFOLDER
import sys, os
from PIL import Image, ImageDraw, ImageFont
R, OUT = sys.argv[1], sys.argv[2]
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/light/'
try: F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
except Exception: F = ImageFont.load_default()
def tile(path, w, label):
    im = Image.open(path).convert('RGB'); h = int(im.height * w / im.width); im = im.resize((w, h), Image.LANCZOS)
    out = Image.new('RGB', (w, h + 22), (0, 0, 0))                 # label bar ABOVE the picture, never over it
    out.paste(im, (0, 22)); d = ImageDraw.Draw(out); d.text((6, 3), label, fill=(255, 255, 255), font=F); return out
def save(img, name, limit=400_000):
    p = os.path.join(OUT, name)
    for q in (88, 84, 80, 76, 72, 68, 62):
        img.save(p, 'JPEG', quality=q, optimize=True)
        if os.path.getsize(p) < limit: break
    print(name, os.path.getsize(p), 'bytes q', q)
# 1 whole view: original, realistic, painted (hero camera)
W = 640
a = tile(G + 'work/orig_960.jpg', W, 'BEFORE (original golden hour)')
b = tile(R + '/hero_real.png', W, 'AFTER, realistic look (light stage only)')
c = tile(R + '/hero_painted.png', W, 'AFTER, painted look (light stage only)')
s = Image.new('RGB', (W * 3, a.height), (0, 0, 0))
for i, t in enumerate((a, b, c)): s.paste(t, (i * W, 0))
save(s, '30 Light - whole view, before then realistic then painted.jpg')
# 2 veranda + evening, 2x2
W = 640
t = [tile(R + '/ver_real.png', W, 'Veranda view, realistic'), tile(R + '/ver_painted.png', W, 'Veranda view, painted'),
     tile(R + '/evening_real.png', W, 'Blue evening, lantern lit, realistic'), tile(R + '/evening_painted.png', W, 'Blue evening, lantern lit, painted')]
s = Image.new('RGB', (W * 2, t[0].height * 2), (0, 0, 0))
for i, im in enumerate(t): s.paste(im, ((i % 2) * W, (i // 2) * t[0].height))
save(s, '30 Light - veranda view and blue evening, realistic beside painted.jpg')
# 3 all the way round
W = 1200
a = tile(R + '/pano_real.png', W, 'All the way round (360 degrees from the gravel court), realistic, north in the middle')
b = tile(R + '/pano_painted.png', W, 'Same, painted look')
s = Image.new('RGB', (W, a.height + b.height + 4), (20, 20, 20)); s.paste(a, (0, 0)); s.paste(b, (0, a.height + 4))
save(s, '30 Light - hills and sky all the way round, realistic over painted.jpg')
