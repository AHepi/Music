# The style rule and the picture measures

What this is: the one rule that stops wear and detail from turning a designed picture into a noisy photographic one,
how to write a style note for a place, and the measures that check a picture against it. Each number says what kind it
is: **measured** (from a picture or a test), **judged** (chosen from evidence) or **invented** (a guess). The house
numbers are in `film-settings.json`, section `place_measures`.

## The rule

The film owner said it in these words, and it applies to every builder and every checker:

> "These things need to be integrated into the style. So it's just part of design."

In plain terms: every wear mark, moss patch, crack, joint, tuft, flower and ripple is a DESIGNED element in the place's
own visual language: the same simplified, slightly chunky shapes, the same edge treatment, the same palette and the same
light as the rest of the picture, as if an art director had drawn each one on purpose. It is not realistic detail laid on
top.

**The test for any new element:** could it sit in a hand-painted game level next to the biggest, simplest thing in the
place without looking as if it came from a more photographic picture? If it is finer, sharper, noisier or more scan-like,
make fewer, bigger, cleaner shapes: a moss patch is one soft rounded shape with a lighter top edge, a crack is one clean
dark line, a peg is one small round shape, a grass tuft is 5 to 9 simple blades.

**How much.** One small story per hand-span, never a hundred tiny details of equal weight. About one readable feature
per 5 to 10 cm on timber, per 20 to 30 cm on ground, per 50 cm on stone and walls (judged, garden style note). For
normal maps the same rule: soft, large relief (grain grooves, plank edges, tile ridges), no micro-pore noise.

## Writing a style note (use `place-kit/data/templates/style_note.md`)

Write it before anyone builds, and give it to every builder and every checker. It has these parts:
0. the rule, word for word, above;
1. form: big simple shapes, how chunky, how soft, what the silhouettes are;
2. edges and surfaces: how crisp, whether there is grain, what the walls, roofs and ground look like up close;
3. palette: the ten most common colours as hex values, ONE hot accent (the only strongly saturated large area), and the
   colours new detail may use, all from the same family;
4. value range: the brightness percentiles (1, 5, 25, 50, 75, 95, 99 percent) and the mean saturation;
5. detail per region: the fine-contrast number for each kind of surface (see "detail energy" below);
6. what the style does NOT have (photographic noise, hair-level grass, pores, glints, lens dirt, text, modern things);
7. a checklist: designed-in test, squint test, palette test, detail-energy test, light test, one story per hand-span.

Where the numbers come from: from a reference picture if there is one. For a new place with no reference, draw the first
honest version, measure it (`explainer-film-place measure PICTURE --make-guard --out style-guard.json`) and make the guard
from it. That guard is PROVISIONAL: it locks in whatever the first picture looked like, so a bland first picture makes a
bland guard. Look at the detail-energy numbers it recorded. The garden's hand-painted look measured 3.4 to 8.4 on a
0 to 255 scale (judged), and photographs of the same things sit above 12. A first picture with regions above 10 is too
photographic to be a guard; fix the picture first. A budget-gated concept step (a picture from an image model as a target,
with the person's yes) is the better start when money allows; the garden's came from paid concept pictures.

## The measures (all computed by `explainer-film-place measure`)

Each says its check name in the preflight (`place pictures: ...`).

| Measure | What it is | The line |
|---|---|---|
| value range | luminance (0.2126 R + 0.7152 G + 0.0722 B) percentiles 1, 5, 25, 50, 75, 95, 99; mean saturation | each percentile within 0.03 of the guard; the 99th not above 0.92; saturation within 0.04 (judged) |
| detail energy | mean absolute difference between the 8-bit luminance and its 2 px blur, per region | at least 0.9 times the guard and at most the smaller of 1.4 times and 10 (judged); regions come from a flat-colour picture of the role classes, not hand-drawn boxes |
| flat windows | 96 x 96 windows (step 48) below the sky | no window with luminance spread under 0.010; under 2 percent under 0.014 (judged) |
| palette | strongly saturated and turquoise pixels | at most 1 percent over saturation 0.70 outside the accent; at most 0.3 percent turquoise (hue 160 to 210, saturation over 0.35); no pure white patch over 30 pixels (judged) |
| squint | structural similarity of 12 px blurred luminance, against the previous round's picture | target 0.92 (judged); a LOOK, never a fail, unless the guard says squint_gate true |
| silhouette overlap | overlap of each group's outline with the previous round's | at least 0.85 (judged); two yardsticks disagreed in the garden, say which you used |
| light groups | the separately drawn light layers add up to the picture | within 2 percent (measured) |
| reading test | at half size, how many of the planned features a reviewer who has not seen the list names | at least 12 of 16 (share 0.75: judged) |

The squint test missed in the garden: 0.883 and 0.873 against 0.92, because the new pond and maple followed the concept
pictures, and the fix round made it worse. It is reported with the region that loses the most. Never remove character to
chase the number; the person decides.

Readability under three lights: the street's joints passed only 6 of 22 test lightings before a fix and 21 of 22 after
(18 of 22 counting every dot). Look at the first preview flat, from the side and (if the place is wet) wet; a mark that
vanishes under one of them is not carrying the place.

## What the measures cannot judge

A measure is not a look. The eye decides whether a worn road reads as worn by use and not as noise, whether wear reads as designed and not photographic, whether a mark that
passes the dot-size rule still reads at phone size, and whether a squint miss is acceptable. The tips guide (section 19)
lists them for critics. The reading test (a reviewer names the features at half size) was never run with a truly blind
reviewer before this version; the workflow `build-a-place` runs it blind, and its 12-of-16 line is a judgement.

## The painter template conflict

If the place goes on to be painted over, the painter's template says "matte painted finish" and "never puddles or
reflections". On a wet street the painter removed the wet ground exactly as told (it came back dry). For a wet or dusk
place change those words for that view: say the painted finish keeps the sheen of wet ground, its puddles, mirrored lights,
joints and gutters. Wet places keep the sheen.
