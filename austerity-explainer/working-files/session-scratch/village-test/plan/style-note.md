PROVISIONAL: this style note was made without a reference picture. Every number in it is judged or invented (none is measured); the first honest picture will make the style guard, and this note is then corrected from it.

# Style note: forest village (2026-10-23)

What this is: the written rules of this place's art style, so that every later step (new geometry, new textures, normal maps, wear, pictures) keeps it. The planner wrote it before anyone builds; every builder and every checker reads it.

The person's request, word for word: "Now build a village in the forest. Needs unkept dirt roads like they're been driven down by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props."

How the person's words became a look and a state (the table in the skill `surfaces-wear-and-construction`):
- "unkept dirt roads" (unkempt) gives the look `neglected` for every ground role (`look_by_role` "ground.*": roads, mud, forest floor, grass and plain ground).
- Nothing was said about the cottages, the stable or the props, so they get the default look `lived_in`. "Empty" stable means no horse, no hay and no people in it; it does not mean ruined, so it is not `derelict`.
- A village in the forest has shaded, damp ground under trees, so the state is `damp` (not `wet`: no rain and no standing water is asked for; puddles come from hollows in the ruts and the yard).
- Place type: `village` (the nearest preset). Its own start was look `lived_in`, state `dry`; the settings change the state to `damp`.
- The person gave no words about the look of the shapes in this request, so no faceted or painted look is assumed: the rule below (section 0) and the real-size facts decide.

## 0. THE RULE FOR EVERY BUILDER
The film owner's rule, word for word: "These things need to be integrated into the style. So it's just part of design."

So: wear, moss, cracks, joinery, tufts, flowers, ripples, stains, chips and every other piece of character is a DESIGNED ELEMENT of this place, drawn in its own visual language: the same simplified shapes, the same edge treatment, the same palette and the same light as the rest of the picture, as if an art director had drawn each one on purpose. It is NOT realistic detail laid on top. Test for any new element: could it sit in a hand-painted game level next to the biggest, simplest thing in the forest village without looking as if it came from a more photographic picture? If it is finer, sharper, noisier or more scan-like, make fewer, bigger, cleaner shapes (a moss patch is one soft rounded shape with a lighter top edge, a crack is one clean dark line, a peg is one small round shape, a grass tuft is 5 to 9 simple blades).

## 1. Form
Hand-built, chunky and simple, at real size. Nothing is square or ruler-straight: posts a little out of plumb, ridges sagging between their trusses, boards of different widths (9 to 17 cm) with a bow here and a replaced board there, shingles of different tones with a few slipped or missing. Bevels 1 to 3 cm on timber and stone edges a hand could touch (the kit's own sizes are in `place-kit/data/surfaces.json`). Thatch is a thick, lumpy, slightly shaggy slab 0.25 to 0.4 m thick with a rolled eave and a ridge capped in a darker band, never a thin sheet. Every building is carried from the ground up (stone footing or sleeper wall, sill, posts, wall plate, rafters, roof): nothing floats and nothing hangs from nowhere.
Silhouettes must tell the buildings apart at a glance, also when squinting (section 8 says how). Trees are big simple masses: a trunk with 3 to 5 chunky crown lumps (broadleaf) or 4 to 6 stacked cones (pine), not hundreds of leaves.
Repeats are allowed only where the real thing repeats (thatch, shingles, boards, stall partitions); no two neighbours are exact copies.

## 2. Edges and surfaces
Edges are soft and slightly chunky, never knife-sharp, never photographic. Up close, every surface is mostly one calm colour with soft large variation and a few clear designed marks:
- Dirt roads and mud: a low, lumpy, damp surface; two wheel ruts a cart's gauge apart (1.4 m) with a bank beside each rut, a trampled middle strip with a line of hoof prints and a few clumps of grass, puddle hollows in the rut bottoms and in two or three potholes; the colour is dark wet brown in the ruts and lighter dry brown on the banks and crown.
- Forest floor and clearing grass: matted leaf brown with moss and a few ferns; unkept tufts of olive grass in the clearing.
- Thatch: warm straw gold when newer, grey-green and mossy when old; shaggy but with large clean bands, not strands.
- Plaster (limewash) panels between timbers: cream or red ochre, soft, with a few big chips showing the wattle underneath and a darker splash band at the foot.
- Stone (cottage B, wells, footings, chimney): rough grey rubble in big uneven blocks with mortar lines, moss in the damp low corners.
- Dark upright boards (the stable): near-black brown, silvered at the edges, a few boards replaced in a fresher colour.
- Shingles: silver-grey wood, mossy on the shaded slope.
- Iron (hinges, bands, rings): dull dark with rust runs below the fixings.
Wear follows use and damp: mud splash at the foot of every wall, a darker drip line under the eaves, moss on the shaded and north sides and on the lower thatch, nothing grows where wheels, feet and hooves go.

## 3. Palette (all judged; replace after the first honest picture)
- The ten most common colours (hex): #5B4A34 leaf and forest floor, #6E5638 wet mud, #8B7653 dry road bank, #6F7A3E clearing grass, #3F5A32 dark leaf, #5A4C40 weathered timber, #3E3128 old oak frame and stable boards, #CDBE9A limewash cream, #9C7A3F thatch gold, #7C7A73 stone and shingle grey.
- ONE hot accent, the only strongly saturated large area: the red-ochre daub of cottage C, about #9C4F36 (saturation about 0.65, under the 0.70 limit). Nothing else in the place is that saturated.
- Colours new detail may use, all from the same family: moss #5E8236 to #7C9A44; mould and algae #4F6B3A; rust #8A4B2C to #A8643A; lichen #A9AE7A; water stain on plaster #8C7B5C; fresh replacement timber #8A6A45; wet mud #4F3E2C; hoof and rut shadow #3F3223.
- Backdrop hills: from #4F6A4A (near ring) to #8FA6B5 (far ring), lighter and bluer with distance. Sky: soft blue, #9DB7CC at the zenith to #D9E2E6 at the horizon.

## 4. Value range and light
- Brightness percentiles (1, 5, 25, 50, 75, 95 and 99 percent), invented targets for a first picture: 0.05, 0.08, 0.17, 0.29, 0.45, 0.68, 0.80; mean colour saturation about 0.27. A forest village is darker than an open field: the forest shade is dark, the clearing is the bright part.
- The light: one sun lamp, warm, from the south-east (compass 135 degrees, the direction it shines from), about 50 degrees up (the wear layers assume 135 degrees and 45 up when there is no single sun lamp; the audit prints which it used). Shadows are about 0.84 times the height of what throws them (1 / tan 50 degrees), pointing north-west. Fill: a soft cool light from the sky and one wide area lamp on the camera side; never a second sun lamp. Shadow colour is cool blue-green from the leaves. No lamps, no lit windows, no fire, no glowing material (so the renderer rule gives EEVEE; see the facts in `renderer_hint`).
- New detail sits inside that light: moss is darker in shadow and warmer in sun, never a flat sticker.
- No tree throws its shadow onto a road, a doorway or a wall inside the clearing (the audit's check "place: sun" reports the shadowed share of the ground a view sees; more than half is a LOOK).

## 5. Detail per region (fine contrast on a 0 to 255 scale; invented targets from the garden's 3.4 to 8.4 band; photographs sit above 12)
road and mud 5 to 8; forest floor and clearing grass 5 to 8; thatch 6 to 9; plaster 3 to 5; stone 5 to 8; timber and boards 5 to 8; shingles 5 to 8; foliage 4 to 7; backdrop hills 1 to 3 (smooth, but see the next lines). Roughly one readable feature per 5 to 10 cm on timber, 20 to 30 cm on ground, 50 cm on stone and walls. One small story per hand-span, never a hundred tiny details of equal weight.
Flat-window rule: no 96 x 96 pixel window below the sky may be flat (luminance spread under 0.010). The backdrop hills therefore carry 3 to 5 tone steps each (tree-line bands, ridge shading), not one flat fill, and the far ground carries soft large colour variation.

## 6. What this style does NOT have (so do not add it)
Photographic noise or grain; hair-level grass; pores; sharp glints; lens flares; dirt on the lens; haze or fog volumes; any water surface (a pond, stream or trough of water makes the renderer rule choose Cycles; puddles are hollows in the ground, not water objects); lamps, lit windows, fire or smoke; people or animals (the stable is EMPTY: no horse, no person, no hay piled in the stalls, only a few loose straws); text, signs, notices or lettering of any kind (the audit's check "place: lettering"); anything modern (wire, plastic, concrete, tarmac, sheet-metal roofs, glass panes, machine-cut nails showing, tyres); straight paved roads, kerbs or road markings; fences of sawn rail and post (only wattle hurdles and split timber).

## 7. Short checklist every later step must pass
0. Designed-in test (section 0): every mark is drawn in this place's own language, not layered-on realism.
1. Squint test: the same silhouettes and big shapes as the last picture (target 0.92).
2. Palette test: new colours come from the family in section 3; only cottage C is hot.
3. Detail-energy test: a 100 percent crop of any new area has fine contrast near section 5's numbers, not above 10.
4. Light test: new detail is lit by the same sun and shadows.
5. One story per hand-span, not noise.
6. The road reads as driven on by horse and cart (ruts a gauge apart, hoof prints down the middle, grass on the crown, puddles in the hollows) and as unkept.
7. The stable reads as EMPTY (open doors, bare stalls and mangers, a few loose straws, an empty trough, a bare hitching rail).
8. The cottages are tellable apart (section 8).

## 8. The place: parts, layout and how things are told apart (for builders and checkers)
Coordinates are metres, x east, y north, z up, origin in the middle of the village. The village clearing is about x -50 to 60, y -32 to 50. The forest closes in round it.
- The main road (the "high road") runs west to east through the village, 5.0 m wide, bending away at both ends so the trees hide where it goes. A side lane (3.4 m wide) leaves it at (20, 2) and runs north to the stable yard (trodden mud, about x 14 to 34, y 24 to 36).
- Cottage A (north side of the road, centre -32, 10): the longest, 11.1 x 4.8 m, dark oak frame with CREAM limewash panels, golden thatch, a log store lean-to at its west end.
- Cottage B (north side, centre -6, 9.5): small and heavy, 6.4 x 4.6 m, grey RUBBLE STONE walls, old grey-green mossy thatch, the only STONE CHIMNEY in the village.
- Cottage C (south side, centre -26, -10.5): 7.4 x 4.6 m, black-brown frame with RED-OCHRE panels (the one hot accent), pale new straw thatch, a taller door.
- Cottage D (south side, centre 4, -8): the smallest, 3.7 x 4.4 m, pale clay (cob) walls with no frame showing, light SILVER SHINGLE roof, one low door.
- The stable (centre 24, 39, facing south onto the yard): 9.8 x 6.0 m, near-black UPRIGHT BOARDS, dark mossy shingle roof, a very wide open double doorway (2.4 m), three empty box stalls inside with empty mangers, an empty trough made from a hollowed log and a bare hitching rail outside. Nothing else in the village has dark boarding or a doorway that wide.
- A well with a wooden windlass, barrels, crates, sacks, buckets, a parked two-wheeled cart with its shafts down, a woodpile with a chopping block, a haystack, wattle hurdles, a bench, jugs, baskets: scattered around the doors and the road edges, outside every wheel track.
- The forest: trees all round from about 30 m out to 150 m, trunks with moss, ferns and bushes at the rim; beyond them rings of hills (the backdrop) all the way round.
Things that look alike must still be told apart: three thatched cottages (A cream and long, B stone and chimney, C red and tall-doored), and two shingled buildings (D small and pale, the stable long and dark with the wide door). The hills look like none of the buildings.
Views (cameras "View <name>", each 1200 x 800): `wide` (the whole place from the south-west edge, camera high), `road_eye` (eye height on the road at the west entrance, ruts leading to the cottages), `stable_close` (across the yard at the open stable), `cottage_close` (cottage A, the well and its props from the road).

## 9. Not tested, not measured
Nothing here is measured. The colours, the percentiles and the detail numbers are invented first targets; the sizes in the facts table are judged from the sources it names, most of them weak (see `open_questions`).

Card time: the person set a total of 150 card minutes for the whole run, written into the ledger with `explainer-film-place card-time start --team-minutes 150`; the planner used 0 of it, every helper makes each change in one sweep and tries an unsure change as about 10 far-apart variations in ONE batch, at most one more.
