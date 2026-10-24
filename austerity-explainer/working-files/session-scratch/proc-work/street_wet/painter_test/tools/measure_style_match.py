"""What this file does (plain words): a rough number check of how close the new wet painting is to the series' hand, next to the existing paintings. It looks at
three things at 768 pixels wide: (1) ink lines: the share of pixels that are a thin dark line clearly darker than what is around them (the series draws dark
outlines); (2) flat colour: the share of pixels in flat patches with almost no texture (the series is flat shapes with visible strokes); (3) busy texture: the share
of pixels with strong fine detail (a 3D picture or a photograph is busier than a painting). Pictures: the series' style picture (Glasgow tenements, chapter 2),
the existing dry lockout painting, the notice corner painting (a Flux repaint of the same street), the new wet painting, and the wet plate. These numbers are rough
guides, not a judgement; the real test is looking at the pictures.
Run: python3 -I tools/measure_style_match.py
"""
import cv2, numpy as np, json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = '/home/user/Music/austerity-explainer/film-kit/assets/'
pics = {
 'series style picture (Glasgow tenements, chapter 2)': FILM + 'paintings/inflation-chapter-2/403-bg-glasgow-tenements.png',
 'existing dry lockout painting': FILM + 'models/pit-village/lockout-painted.jpg',
 'notice corner painting (same street, dry)': FILM + 'models/pit-village/notice-corner-painted.jpg',
 'NEW WET PAINTING': os.path.join(HERE, 'pictures/wet_painting_lined_up.png'),
 'wet plate (3D picture)': '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/work/r35/main_wet_plate.png',
}
out = {}
for name, path in pics.items():
    im = cv2.imread(path)
    h = int(round(im.shape[0] * 768 / im.shape[1]))
    im = cv2.resize(im, (768, h), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    ink = float(((bh > 0.07) & (g < 0.25)).mean())
    mean = cv2.blur(g, (7, 7)); sq = cv2.blur(g * g, (7, 7)); std = np.sqrt(np.maximum(sq - mean * mean, 0))
    flat = float((std < 0.012).mean())
    busy = float((std > 0.06).mean())
    out[name] = {'ink_line_share': round(ink, 4), 'flat_colour_share': round(flat, 4), 'busy_texture_share': round(busy, 4)}
    print(f'{name:55s} ink lines {ink:.3f}   flat colour {flat:.3f}   busy texture {busy:.3f}')
json.dump(out, open(os.path.join(HERE, 'numbers/style_match.json'), 'w'), indent=1)
