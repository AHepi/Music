# What this does: builds the four labelled JPG pictures for trial 22a from the downloaded renders. Reads PNGs, writes JPGs into the pictures folder.
from PIL import Image, ImageDraw, ImageFont
import os
W='proc-work/skills_test/22a/_dl/out_machine'; P='proc-work/22 Scenario Blender skills test - pictures'
font = ImageFont.load_default(size=22)
def banner(img, text, h=34):
    out = Image.new('RGB', (img.width, img.height + h), (24, 24, 24))
    out.paste(img, (0, h))
    ImageDraw.Draw(out).text((8, 5), text, fill=(240, 240, 240), font=font)
    assert ImageDraw.Draw(out).textlength(text, font=font) < img.width - 16, text
    return out
def label(d, x, y, text, dark=True):
    w = d.textlength(text, font=font)
    d.rectangle((x - 6, y - 2, x + w + 6, y + 26), fill=(24, 24, 24) if dark else (240, 240, 240))
    d.text((x, y), text, fill=(240, 240, 240) if dark else (0, 0, 0), font=font)
def save(img, name):
    path = os.path.join(P, name); q = 88
    while True:
        img.save(path, 'JPEG', quality=q, optimize=True)
        if os.path.getsize(path) < 380_000 or q < 40: break
        q -= 6
    print(name, img.size, os.path.getsize(path) // 1024, 'KB')
a = Image.open(W + '/camera/main_camera_sheet.png').convert('RGB').resize((1620, 720), Image.LANCZOS)
d = ImageDraw.Draw(a)
for i, t in enumerate(('shape only', 'clay', 'face direction colours', 'wireframe')): label(d, i * 405 + 10, 6, t)
save(banner(a, '22a  The street from the film main camera, with the expert skill review looks'), '22a-1 street from the main camera - shape, clay, face direction and wireframe looks.jpg')
off = Image.open(W + '/cull_off/matcap_threequarter.png').convert('RGB'); on = Image.open(W + '/cull_on/matcap_threequarter.png').convert('RGB')
w, h = off.size
both = Image.new('RGB', (w * 2 + 8, h), (24, 24, 24)); both.paste(off, (0, 0)); both.paste(on, (w + 8, 0))
d = ImageDraw.Draw(both)
label(d, 10, 6, 'back faces shown (as drawn now)'); label(d, w + 18, 6, 'back faces hidden (game style)')
save(banner(both, '22a  Pit headframe: audit flags 69 bars as inside-out'), '22a-2 headframe inside-out parts - fine now, see-through if back faces hidden.jpg')
m = Image.open(W + '/eevee/main_today.png').convert('RGB'); l = Image.open(W + '/eevee/wall_lamp_today.png').convert('RGB')
both = Image.new('RGB', (m.width + l.width + 8, m.height), (24, 24, 24)); both.paste(m, (0, 0)); both.paste(l, (m.width + 8, 0))
d = ImageDraw.Draw(both)
label(d, 10, 6, 'main camera plate'); label(d, m.width + 18, 6, 'wall foot by lamp: flagged plinth')
save(banner(both, '22a  Real EEVEE plate: no speckle at the flagged overlaps'), '22a-3 real EEVEE plate at the flagged places - no speckle visible.jpg')
s = Image.open(W + '/stock/review_sheet.png').convert('RGB'); d = ImageDraw.Draw(s)
for i, t in enumerate(('front', 'right', 'three-quarter', 'back')): label(d, i * 400 + 10, 6, t, dark=False)
save(banner(s, '22a  The skill review sheet as shipped: too small and squashed for a street'), '22a-4 skill review sheet as shipped - not made for a long street.jpg')
