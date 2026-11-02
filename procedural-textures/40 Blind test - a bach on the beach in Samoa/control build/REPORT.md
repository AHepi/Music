# Control build: a bach on the beach in Samoa, modern day

Work folder: /home/claude/blind-test/control-build
Work time: about 1 hour 35 minutes (started 16:11, final picture finished 17:45). No plugin, no skill, no outside folder read, no internet. Everything is Blender (bpy 5.1.2, Cycles on the CPU) plus numpy for placing things.

## Final picture
/home/claude/blind-test/control-build/pic_final_1080x1920.png  (1080 x 1920, 96 samples, drawn in 1886 seconds, about 31 minutes)
The scene file it came from is bach.blend (same folder). Scripts: build_scene.py (main), terrain.py, world.py, bach.py, plants.py, props.py, lib.py, comp.py, render.py. To redraw: `python3 build_scene.py` then `python3 render.py bach.blend out.png 1080 1920 96`.

## What I built (all by script, no outside assets)
- Beach and sea: a land and sea-floor mesh from one height formula (sand beach, lawn, hills rising behind, a lagoon floor, a reef crest far out). Sand is a procedural material (grain, ripples, a wet band at the water line, a dark tide line, lace foam). The sea floor shows dark coral patches through the water. A separate water sheet whose colour comes from depth (aqua near the shore, deep blue far out), with sky reflection, wave bumps, foam at the shore and a white breaking band at the reef. Two dark hazy islands on the horizon.
- The bach: small timber house on concrete piles (about 6 m by 3.6 m plus a front veranda). Weatherboard walls (cream, grooved, grubby near the bottom), turquoise trim, louvre windows and door, corrugated red iron roof (real ridged geometry, rust and sheet-to-sheet variation), three solar panels on the roof, a gutter and downpipe, veranda posts and rails, steps, a warm string of lights along the eave, a rain tank behind, plastic chairs and a table, two surfboards leaning on a post, a cooler, a red bucket, flip-flops on the steps. Warm lamp glow behind the louvres.
- Around it: 10 hero coconut palms plus 16 distant ones (curved ringed trunks, instanced fronds with leaflets, coconuts), 90 jungle trees (lumpy canopy blobs), banana clumps, hibiscus shrubs with red flowers, about 26,000 grass tufts on the lawn, beach grass clumps, black lava rocks at the water line, a blue outrigger canoe with paddle on the sand, driftwood, fallen fronds, pebbles and shells, coconut husks, tide-line debris, a trail of footprints.
- Sky: Blender's physical sky (sun low in the west), a blue tint that gets deeper higher up, clouds I made with noise in the world shader (lit warm on the sun side), a trace of haze in the air.

## Light and camera
- Light: golden hour. Sun 10 degrees above the horizon, off the left edge of the frame, warm orange (a sun lamp that matches the sky's sun). The sky gives the blue fill. Shadows fall to the lower right, so the palm trunk at the left throws a long band across the sand. Sky strength 0.5, sun strength 6, exposure -0.8, AgX with the High Contrast look.
- Camera: 1080 x 1920 portrait, 31 mm lens, 1.55 m above the sand (standing eye height), tilted up 6 degrees, looking along the beach a little to the right so the sea is at the left and the bach in the right half. Shallow depth of field (f/9, focus 13 m) so the nearest sand is a touch soft. Shoreline and reef lines lead toward the horizon. A big palm trunk and crown frame the left and top.
- Finishing (Blender compositor): a light bloom on the brightest glow and a soft dark vignette.

## Pictures drawn (all in the work folder; times are the Blender render time)
Tests while building (small, low samples, names t_*):
- t_a.png 270x480, 24 samples: sky, sand, sea only. Rewritten several times: 27 to 60 s each. The first try came out black (a world-wide haze swallowed the sky), the next two were washed out (sun behind the camera, wrong exposure); the last one kept is 25.5 s.
- t_b.png 270x480, 32 samples, 35.8 s: first bach.
- t_c.png 43.1 s: first palms. t_d.png 47.6 s: trees, canoe, rocks, grass.
- t_close.png 540x960, 32 samples, 194 s: close-up of the bach from a test camera (found the stair rails flopped and a shrub in the way).
- t_aer.png (about 300x400 / 400x300, 12 samples, 27 and 28 s): two high views of the bach to check the roof (the second overwrote the first).
- t_e.png 360x640, 80 s; t_f.png 85 s; t_g.png 119 s; t_h.png 79 s: full-frame compositions as I changed bach angle, canoe, sky, camera.
- t_i.png 180x320, 8 samples, 14 s: test of the bloom and vignette.
- t_sky_a to t_sky_f.png and t_sky_cmp.png: six 150x267 sky and haze tests at 8 samples (21 to 24 s each) and a side-by-side sheet.
- t_crop.png 300x300, 12 samples, 23 s: close look at the dark shape at the right edge (it was the water tank).
- _dbg.png, _pano.png, _d3.png: tiny debugging renders (sun direction test, sky test).
Review pictures at the real tall frame, half size, 40 samples: pic_540_v1.png (202 s), pic_540_v2.png (205 s), pic_540_v3.png (201 s).
Final: pic_final_1080x1920.png (1886 s).
Total drawing time was roughly 1 hour 20 minutes, of which 31 minutes is the final. Scene build takes about 40 seconds each time.

## What I tested
- Every script ran to the end and the pictures above exist; I looked at each review picture and the final one.
- Found and fixed from looking: black sky from a world haze; sun behind the camera (found its true direction by rendering the sky at four headings); washed-out exposure; the sun-side facade being hidden by a palm and a big shrub; stair rails lying flat; white-looking metal roof; pale sea; tank showing as a green slab; overlapping canoe and steps; the canoe float sticking out as a stray blue stick.
- Looked at the house from a high view on the sea side (t_aer.png) to check roof, solar panels and veranda from outside the main camera view.
- The roof is visible from the main camera, red with the solar panels dark on it.

## What I did not test or do
- Only one view was judged closely at full size; I did not look at the back of the house, the tank, the clothes line (I built a laundry line but removed it because it falls outside the frame), or the other sides.
- I did not render a second full-size picture or try other times of day, weather or camera moves.
- I did not check geometry for production use (no UV unwrapping, no scale or normal checks, no export). It is a single rendered picture, not a game asset.
- No people, animals or moving things. Water is still (no waves in 3D, only surface bumps).

## What I am unsure of or know is weak
- The white painted parts (posts, rails, steps, trim) come out mottled and slightly metallic, like galvanized steel, not painted timber. The roof edge and the stair treads show this most.
- The footprints read as leaf-shaped marks, not feet. The tide-line debris and pebbles are small dark/white dots that look a bit like scattered seeds.
- The canoe: the outrigger float sits behind the hull and reads as a second blue shape; the hull's inside is plain.
- The sand has a faint smeared look in places from the noise remover; the foreground is large and quiet.
- The sea is more pale blue-white than strong turquoise because it is reflecting a bright low sky; the lagoon colour shows mostly near the left shore. A real Samoan lagoon photo would probably be more saturated.
- Samoan accuracy: the house is my own idea of a modern bach (timber, louvres, red iron roof, rain tank, solar). I did not build a traditional open fale, and the house is a little tidy and new-looking. The reef and island shapes are invented.
- The sand and ground materials are procedural and the scale of the texture detail was judged only by eye.
