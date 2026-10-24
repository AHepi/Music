# Style note: <PLACE NAME> (<date>)

What this is: the written rules of this place's art style, so that every later step (picture prompts, new geometry, new
textures, normal maps, wear) keeps it. The planner fills it in before anyone builds; every builder and every checker reads
it. Replace each <...> and delete the comments (lines that start with "Where the numbers come from"). If there is a
reference picture, measure it. If there is none, draw the first honest version, measure that
(`explainer-film-place measure PICTURE --make-guard`) and fill the numbers in from it: a style note made that way is
PROVISIONAL, and says so in its first line.

## 0. THE RULE FOR EVERY BUILDER
The film owner's rule, word for word: "These things need to be integrated into the style. So it's just part of design."

So: wear, moss, cracks, joinery, tufts, flowers, ripples, stains, chips and every other piece of character is a DESIGNED
ELEMENT of this place, drawn in its own visual language: the same simplified shapes, the same edge treatment, the same
palette and the same light as the rest of the picture, as if an art director had drawn each one on purpose. It is NOT
realistic detail laid on top. Test for any new element: could it sit in a hand-painted game level next to the biggest,
simplest thing in <PLACE> without looking as if it came from a more photographic picture? If it is finer, sharper,
noisier or more scan-like, make fewer, bigger, cleaner shapes (a moss patch is one soft rounded shape with a lighter top
edge, a crack is one clean dark line, a peg is one small round shape, a grass tuft is 5 to 9 simple blades).

## 1. Form
<How big and simple the shapes are, how chunky, how soft; what the silhouettes are, so that a viewer can name every
object from its outline when they squint; how bevels read (a generous 1 to 3 cm?). Repeats allowed? (rows of tiles, planks)>

## 2. Edges and surfaces
<How crisp the edges are; whether there is grain, blur, lens dirt; what the main surfaces look like up close (walls,
roofs, ground, timber, stone, water): mostly flat colour with soft large variation and a few clear marks?>

## 3. Palette
- The ten most common colours (hex): <#......, ... ten values>
- ONE hot accent, the only strongly saturated large area: <what it is, its colour range>
- Colours new detail may use, all from the same family: moss <hex range>, mould <...>, rust <...>, lichen <...>,
  water stain <...>, timber <...>, stone <...>.
Where the numbers come from: the ten colours from a palette reduction of the reference (or first honest) picture.

## 4. Value range and light
- Brightness percentiles (1, 5, 25, 50, 75, 95 and 99 percent): <seven numbers>; mean colour saturation <number>.
- The light: <direction, warmth, shadow colour, how long the shadows are>. New detail sits inside that light: a plank's
  moss is darker in shadow and warmer in sun, never a flat sticker.
Where the numbers come from: `explainer-film-place measure PICTURE` prints the percentiles and the saturation.

## 5. Detail per region
Fine contrast ("detail energy": the mean size of the contrast left after a 2 pixel blur, on a 0 to 255 scale) per kind of
surface: <region: number> (for example roof, ground, walls, timber, stone, plants). Roughly one readable feature per
5 to 10 cm on timber, 20 to 30 cm on ground, 50 cm on stone and walls. One small story per hand-span, never a hundred tiny
details of equal weight.
Where the numbers come from: `explainer-film-place measure` with a flat-colour picture of the role classes as the regions.
A painted, hand-drawn look measured 3.4 to 8.4 in one garden; photographs of the same things sit above 12. A region above 10
in the first picture means the picture is too photographic to be a guard.

## 6. What this style does NOT have (so do not add it)
<Photographic noise or grain; hair-level grass; pores; sharp glints on dust; wet shine except on <where>; lens flares;
dirt on the lens; people or animals; text; modern objects; ...>

## 7. Short checklist every later step must pass
0. Designed-in test (section 0): every mark is drawn in this place's own language, not layered-on realism.
1. Squint test: the same silhouettes and big shapes as the last picture (target 0.92).
2. Palette test: new colours come from the family in section 3.
3. Detail-energy test: a 100 percent crop of any new area has fine contrast near section 5's numbers, not above 10.
4. Light test: new detail is lit by the same light and shadows.
5. One story per hand-span, not noise.
