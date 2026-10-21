# Trial 22b: puts the finished renders into four small JPG sheets (plain Python, PIL; only reads pictures).
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = 'proc-work/22 Scenario Blender skills test - pictures'
os.makedirs(OUT, exist_ok=True)
O = 'out/'

def door(path, scale=0.75):
    im = Image.open(path).convert('RGB').crop((55, 0, 485, 960))
    return im.resize((int(430 * scale), int(960 * scale)), Image.LANCZOS)

def sheet(panels, labels, name, pad=6, bar=34, bg=(24, 24, 24)):
    w = sum(p.width for p in panels) + pad * (len(panels) + 1)
    h = max(p.height for p in panels) + bar + pad
    s = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(s)
    x = pad
    for p, l in zip(panels, labels):
        s.paste(p, (x, bar))
        for i, line in enumerate(l.split('\n')):
            d.text((x + 2, 3 + i * 13), line, fill=(235, 235, 235))
        x += p.width + pad
    path = os.path.join(OUT, name)
    s.save(path, quality=80, optimize=True)
    print(path, os.path.getsize(path) // 1024, 'KB', s.size)

# 1: the main before / after
sheet([door(O + 'r3/main_today_before_eevee.png'), door(O + 'r3/main_today_addwear_eevee.png'), door(O + 'r3/main_addwear_cycles.png'), door(O + 'r3/main_today_baked1024_eevee.png')],
      ['BEFORE (EEVEE)\nthe door as the street has it', 'add_wear, drawn in EEVEE\n(the film renderer): almost nothing', 'add_wear, drawn in Cycles\nedge chips and dirt show', 'add_wear BAKED to 1024 maps\nthen drawn in EEVEE: chips are back'],
      '22b-1 door before and after wear - add_wear shows in Cycles only, the bake carries it to EEVEE.jpg')

# 2: the bake ladder
sheet([door(O + 'r4/main_today_baked512_sharp30_eevee.png'), door(O + 'r3/main_today_baked512_eevee.png'), door(O + 'r3/main_today_baked1024_eevee.png'), door(O + 'r3/main_addwear_cycles.png')],
      ['test bake 512, the skill\'s first choice\n(30 deg seams + sharp flags): FAILED', 'test bake 512, fewer seams\n(60 deg, no sharp flags): soft but works', 'test bake 1024, same seams\nsharper', 'reference: add_wear live in Cycles'],
      '22b-2 test bake of the worn door - first try failed, fewer seams worked, 1024 sharper than 512.jpg')

# 3: masks and the curvature route
def mask(p):
    return Image.open(p).convert('RGB').resize((270, 480), Image.LANCZOS)
sheet([mask(O + 'checks/mask_Wear_BLENDER_EEVEE.png'), mask(O + 'checks/mask_Wear_CYCLES.png'), mask(O + 'checks/mask_Dirt_BLENDER_EEVEE.png'), mask(O + 'checks/mask_Dirt_CYCLES.png'),
       door(O + 'r3/main_today_curv_eevee.png', 0.5), door(O + 'r4/main_today_curv2_eevee.png', 0.5)],
      ['Wear mask, EEVEE\n(white = chipped): empty', 'Wear mask, Cycles\nfollows the edges', 'Dirt mask, EEVEE\nonly part of it', 'Dirt mask, Cycles', 'curvature route, EEVEE\ntry 1: blotchy', 'curvature route, EEVEE\ntry 2: still wrong'],
      '22b-3 wear and dirt masks in EEVEE and Cycles, and the curvature route that did not work.jpg')

# 4: the baked maps
def tile(p, size=340, gray=False):
    im = Image.open(p)
    if im.mode in ('RGBA',):
        bg = Image.new('RGB', im.size, (30, 30, 30)); bg.paste(im, mask=im.split()[3]); im = bg
    return im.convert('RGB').resize((size, size), Image.NEAREST if 'uv_layout' in p else Image.LANCZOS)
sheet([tile(O + 'bake512/door_uv_layout_512.png'), tile(O + 'bake1024_a60/door_uv_layout_1024.png'), tile(O + 'bake1024_a60/door_diffuse.png'), tile(O + 'bake1024_a60/door_roughness.png')],
      ['UV layout, first try (687 islands,\ncoverage 2 percent)', 'UV layout, 60 deg seams (138 islands,\ncoverage 29 percent)', 'baked colour map 1024\n(wear and dirt are in it)', 'baked roughness map 1024'],
      '22b-4 baked maps and UV layouts of the door test bake.jpg')
