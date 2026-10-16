---
name: paint-and-cut
description: Make the pictures for an explainer chapter with fal - painted backgrounds turned into rooms with depth (via a depth map), painted figures and objects cut out as paper pieces, and plates of places built in Blender painted over and lined up - with the style words, sizes, costs and checks that keep them consistent. Use after the script is final and before building pages.
---

# Paintings, rooms with depth, and cut-outs

Kit folder = the folder made by `explainer-film-setup`. Full detail on prompts, masks and the cut
list: `film-kit/docs/paper-look - 04 Painting prompts.md` and `... - 01 How to make a film with this kit.md`
(steps 6-8).

**Example.** Chapter 2 painted 11 new pictures (a checkout, a dusk skyline of chimneys, Glasgow
tenements, a noodle shop, a central bank, a steelworks in snow, a 1973 petrol station, a suburban
street, plus cut-out groups), made a depth map for each room and three cut-out masks: about US$1.06.
It reused four rooms from chapter 1.

## 1. Plan and confirm the cost

List every room (one per setting) and every cut-out (people, objects) the pages need. Reuse what
the project already has. Cost (chapter 2, October 2026): about 10 US cents per 2k picture, 2.5 cents
per 1k, about half a cent per depth map, a fifth of a cent per mask. Prices change between plan and
purchase (Flux 3 edit went from 2.4 to 4.8 US cents a megapixel in a day, lesson 139 of the austerity
project): check fal's estimate before each paid batch. Tell the user the total and confirm.

## 2. Paint (fal connector)

- Model `blackforestlabs/flux-3/text-to-image`, `output_format: "png"`.
- Rooms: `aspect_ratio: "9:16"`, `resolution: "2k"` (1536 x 2736), seen at standing eye level, "the
  lower quarter of the picture is the empty floor/street/counter", "No people".
- Cut-outs: `21:9` or `4:5` at 2k for groups and big figures, `1:1`/`4:5` at 1k for objects, "on a
  perfectly plain, flat, light grey background (#cfcfcf) with no floor, no cast shadow".
- Put the SAME style words at the end of every prompt (keeps pictures matching), e.g.: "Painterly 2D
  digital illustration, the look of a modern animated history documentary: semi-realistic with
  slightly stylised, expressive proportions, visible confident brush strokes, rich detail, cinematic
  lighting. Restrained palette: deep teal-blue shadows, cold blue-grey midtones, warm amber
  lamplight, with only small touches of dull brick red. Tense, uneasy mood. Absolutely no text,
  letters, numbers, logos, emblems or symbols anywhere."
- Never ask for real people's faces. Ask for blank placards and plain signs (models invent writing).
- Submit up to 8 at a time, collect, then save with their prompts:
  `python3 -I paper-film/tools/save_fal_paintings.py assets/paintings/<chapter> new-paintings.json`.
- **Look at every painting** on a contact sheet (`paper-film/tools/contact_sheet.py`): wrong era,
  writing, symbols, extra fingers, cut-off subjects. Re-paint failures.

## 3. Rooms with depth (cinema look)

1. Depth map per room with fal model `fal-ai/image-preprocessors/depth-anything/v2` (input
   `image_url` = the painting's fal address); download the result as `depth/NAME-depth.png` (light =
   near, dark = far).
2. Make the room: `python3 -I paper-film/tools/prepare_relief.py PAINTING.png depth/NAME-depth.png assets/reliefs/<chapter> NAME --blur 3`
   (writes `NAME.jpg` and a smoothed `NAME-depth.png`; `--blur 3` stops thin near things tearing).
3. Find where things can stand: `python3 -I paper-film/tools/relief_points.py assets/reliefs/<chapter> NAME --near 6 --far 70`
   prints a grid of 3D points (u across, v up); use the same near/far in `kit.relief`.
4. A plain backdrop (no depth) for far skies behind model sets: `kit.backdrop(NAME, {distance, fov})`,
   scaled up enough to fill the frame from the widest camera.

## 4. Cut-out pieces

1. Mask per cut-out painting with fal `fal-ai/birefnet/v2` (`model: "General Use (Dynamic)"`,
   `operating_resolution: "2304x2304"`, `mask_only: true`), saved with
   `python3 -I paper-film/tools/download_fal_masks.py assets/paintings/<chapter> NNN-name=MASK_URL ...`.
   Check: `python3 -I paper-film/tools/contact_sheet_masks.py assets/paintings/<chapter> masks-check.jpg`
   (missing parts show magenta).
2. Write `examples/<chapter>/cut-list.json` (copy the example's; options: margin, grade,
   longest_side, add_polygons to put back what a mask missed, labels to print words on an object,
   split_shapes, jaw for a speaking figure) and run
   `python3 -I paper-film/tools/prepare_paper_pieces.py examples/<chapter>/cut-list.json .`
3. Check: `python3 -I paper-film/tools/contact_sheet_pieces.py paper-film/pieces/<chapter> pieces-check.jpg`.

## 5. A place built in 3D, painted over (plate repaints)

For the built-and-painted look the painting is not made from words: Blender draws the place (the
"plate"), an image-edit model paints over it, and the page shines the painting back onto the 3D set. The
whole way is the `build-and-paint-a-place` skill. Three tools do the steps below with the project's
pass marks (see `kit/calculators/README.md`, "Painting tools"): `kit/calculators/paint_request.py request`
(the preflight, both prompts from the plate and a short brief, the price; it never sends),
`kit/calculators/after_painting.py check` (resize, line-up, figures, style, the behind painting) and
`kit/calculators/plan_states.py plan` (the helper plates and state pictures of a held shot). The painting
steps, in order:
1. Before paying: the plate renders cleanly (no "Shadow buffer full" in its log), passes the shot
   checker's light rules, has no faint glow inside a hollow (darken it first: the painter lifts it into a
   band), and its people cast no long shadows.
2. Flux 3 edit (`fal`), image 1 the plate, image 2 a style painting sent at about 1 million pixels; keep
   every element where it is, add no people, no flames, smoke, glows or new shadows round the near props;
   far walkers "flat dark shapes with no pale spots".
3. Resize to the plate's exact size and line it up: `paper-film/tools/align_painting.py` (the notice
   corner's painter had stretched it 0.65% and shifted it 3 pixels; lined up, 96% of the props' outlines
   sat on painted edges, against 70% before).
4. A "behind" painting (the near props painted out), lined up `--against` the first, with the first
   painting's shadows kept round the props (`paper-film/tools/keep_painted_shadows.py`); or, free,
   `paper-film/tools/make_behind_picture.py`.
5. State pictures (the same view with people gone or a factory slowed) change only what changed:
   `paper-film/tools/make_state_picture.py`.
6. Look at the painting against the plate before using it: the people test's men went from about 15% to
   about 50% of their surroundings' brightness when painted, and turned mid-grey on a phone.

Cost: about 4.8 US cents a megapixel of the returned picture plus every picture sent (October 2026),
so about 44 cents for a 2k repaint with a style picture. That rate was worked out from fal's price on the
day, not read from a bill: confirm it in fal's request history before relying on it.

## Traps

- Models add things nobody asked for (symbols, flags, writing, wrong-era machines): check every one.
- Pieces from an earlier chapter can be reused by copying their PNG and pieces.json entry.
- People in period clothes must not stand in present-day scenes; use a graphic instead (a hundred-dot
  panel for a share of people, for example).
