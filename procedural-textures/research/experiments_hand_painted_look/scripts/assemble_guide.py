# What this does (plain python): joins the guide parts in ../guide_parts into the one guide file in the research folder, after applying the last
# corrections (section numbers, wording) and inserting the gravel table. Run: python3 -I assemble_guide.py
import os, re
BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.abspath(os.path.join(BASE, '..', '02 Research - getting a hand-painted stylised look.md'))
parts = [open(os.path.join(BASE, 'guide_parts', f'p{i}.md'), encoding='utf-8').read() for i in (1, 2, 3, 4)]
text = '\n'.join(parts)

def sub(old, new, count=1):
    global text
    assert old in text, 'missing: ' + old[:70]
    text = text.replace(old, new, count)

# --- section number fixes in the short version
sub('(TESTED, 4.1, 4.8)', '(TESTED, 4.1 and 4.10)')
sub('(TESTED, 4.6, calibration table)', '(TESTED, 4.7, calibration table)')
sub('They are shading tools, not outline makers. (TESTED, 4.6)', 'They are shading tools, not outline makers. (TESTED, 4.8)')
sub('classic takes 0.4 seconds. (TESTED, 4.8)', 'classic takes 0.4 seconds. (TESTED, 4.10)')
sub('The compositor\'s own "Extension: Repeat" did NOT fix it. (TESTED, 4.8)', 'The compositor\'s own "Extension: Repeat" did NOT fix it. (TESTED, 4.10)')
sub('(section 4.7: the hex numbers must be converted', '(section 4.9: the hex numbers must be converted')
sub('(put the palette in the stops, section 4.7)', '(put the palette in the stops, section 4.9)')
sub('| **Compositor:** Filter Sobel + threshold, then Dilate/Erode or Mask To SDF | see 4.9 |', '| **Compositor:** Filter Sobel + threshold, then Dilate/Erode or Mask To SDF | see 4.10 |')
# --- fact 12 and the height-smoothing statements
old12 = text[text.index('12. **Make the height from the lightness'):text.index('**The pipeline in seven steps**')]
new12 = ('12. **Make the height from the lightness of the FINISHED colour, blur it by about 0.8 pixel, then make the normal.** On the slate demo the blur took the '
         '"normal agrees with the height slope" score from 0.00 to 0.45 and the overall score from 0.51 to 0.55 (0.57 with the patch size tuned from the spec, section 5). '
         'The Kuwahara filter did not raise the score on an already flat picture (0.51 to 0.48). (TESTED, 4.11 and 5)\n\n')
text = text.replace(old12, new12)
sub('The reference\'s own height was smoothed 0.8 px; I copied that.', 'The uploaded height has edges 0.4 to 0.6 px softer than the colour\'s (section 2.6) and the README of the reference folder says the prepared copy was smoothed by 0.8 px, so I used 0.8 px (not fitted; other values not tried).')
sub('"normal agrees with the height slope" score goes from 0.00 to 0.73', '"normal agrees with the height slope" score goes from 0.00 to 0.73')
sub('(2.3 is the smallest difference an eye notices)', '(2.3 is the usual rule of thumb for a just-visible difference; from colour science, not checked here)')
sub('on a scale where 2.3 is "just visible"', 'on a scale where about 2.3 is "just visible" (a rule of thumb, not checked here)')
# --- remove the untested rule of thumb row
i = text.index('| darker by dL in lightness')
j = text.index('\n', i)
text = text[:i] + text[j + 1:]
# --- bilateral wording
old = text[text.index('- **Bilateral Blur** (Size 4 to 16)'):text.index('- **Filter:**')]
new = ('- **Bilateral Blur** (Size 4 to 16): it needs its **Determinator** socket connected to a picture that shows the edges. In my first sweep I left it unconnected (constant white) and got a plain blur. '
       'With the Determinator linked to the picture itself, Size 4 to 8 at Threshold 0.05 softens the grain and keeps the cell borders; Size 16 blurs the borders; it flattens less than Kuwahara (`pictures/c06_compositor/bilateral_determinator/strip.png`). TESTED\n')
text = text.replace(old, new)
# --- gravel table
gravel = '''| Variant | What it has | Overall | Colour | Height | Normal | Edge density (reference 22.9%) |
|---|---|---|---|---|---|---|
| g0 | earth speckle only (flat cells, 48 across) | 0.235 | 0.13 | 0.17 | 0.32 | 7.5% |
| g1 | + small stones (Scale 17, covering 60%) | 0.292 | 0.17 | 0.31 | 0.31 | 13.5% |
| g2 | + big stones (Scale 6, covering 45%), facets inside every stone | 0.346 | 0.25 | 0.36 | 0.32 | 10.8% |
| g3 | the same without facets | 0.336 | 0.24 | 0.34 | 0.32 | 8.4% |
| spec | stone sizes from the measurements: earth 110 across, stones 64 / 30 / 13 across (covering 62 / 50 / 40%), rims 1.5 / 2.5 / 4 px | **0.394** | 0.35 | 0.30 | 0.42 | 25.2% |
| spec + jitter | the same plus a brightness jitter of 0.35 per stone and a fine grain of 0.15 | **0.417** | 0.37 | 0.33 | 0.47 | 24.9% |

(All with the height blurred 0.8 px; picture `pictures/c17_gravel_demo_stages.png`; sheets in `data/gravel_demo/*_smooth/sheet.png`.)

Reading the table:
- **Taking the sizes from the measurements was the biggest step** (0.346 to 0.394): the correlation length fell from 24 px to 7 (reference 8) and the edge density rose from 11% to 25% (reference 23%). With the first guessed sizes the stones were far too big.
- **Facets inside the stones** were worth only +0.01 (g2 against g3), which is within the noise of one seed.
- **Variation inside the palette helped a little** (+0.023, colour distribution score 0.48 to 0.50, height gradient 0.19 to 0.36): the sheet's brightness curve for the flat version is a row of spikes (one per palette colour) where the reference's is smooth. The reference patches wobble 3 to 6 lightness units inside (section 2.3), so "flat" means "nearly flat".
- **How close is it?** The overall character is right (dark and blue-grey stones with rims, brown earth, patch sizes, edge density), but side by side it is clearly a Voronoi patchwork: the reference stones are angular crystals with lighter facets and sharp corners, brown appears as separate grains rather than inside the stones, and there are many more tiny stones. Colour spectrum and gradient scores stay at 0. Angular cells (Chebychev, Randomness 0.6 to 0.8, `pictures/c15_angular_cells_all.png`) and a bright facet edge are the next things to try; not done.
'''
sub('{{GRAVEL}}', gravel)
open(OUT, 'w', encoding='utf-8').write(text)
print('written', OUT, len(text.splitlines()), 'lines', len(text), 'characters')
# check picture references
refs = sorted(set(re.findall(r'`((?:pictures|data|scripts)/[^`\s,;)]+)', text)))
missing = [r for r in refs if not os.path.exists(os.path.join(BASE, r.split(' ')[0]))]
print('references:', len(refs), 'missing:', missing)
