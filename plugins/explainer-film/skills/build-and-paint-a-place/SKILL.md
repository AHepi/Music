---
name: build-and-paint-a-place
description: Build a place for a film in Blender by script (free Poly Haven models and surfaces, scripted props with real lettering, people), compose each view with the shot checker, draw a plate, have it painted over with an image-edit model on fal, line the painting up, and shine it back onto the 3D set in a page so the camera can hold or slide without tearing; with held shots, state pictures (people gone, a factory slowed) and the checks before filming. Use for the built-and-painted look (chapter 2 for newcomers), or whenever a page needs a place the camera moves in.
---

# Build a place in 3D and paint it over

What this is: the way the austerity project made its places from log 29 to log 34 (the pit village's notice
corner, the people test, the Works of chapter 2 for newcomers), as one set of steps. KIT = the folder made by
`explainer-film-setup`; every path below starts there. The rules for composing are in the kit's
`docs/paper-look - 07 Composing a shot.md`; read it before step 3.

**Example.** The notice corner (logs 31 and 32): the pit village street built in Blender from Poly Haven
surfaces and props, a lock-out notice on a board with a burning drum, an empty chair with a lit lantern on it
and a pail, composed until the shot checker passed 32 of 38 checks; a plate 1536 x 2730 drawn with EEVEE from
the start of the slide; Flux 3 edit painted it over and a second time with the near props painted out; both
lined up with the plate (the painter had stretched it 0.65% and shifted it 3 pixels); the page
`paper-film/scenes/notice-corner.js` shines the paintings back onto the set and slides 1.5 m toward the notice
without turning. Two paintings cost about 20 to 45 US cents.

## 1. Set up (once per machine)

- The full Blender program (5.2.2 was used), not only the `bpy` Python module: plates are drawn with EEVEE and
  the shot checker draws its flat-colour pictures in Blender. EEVEE runs without a graphics card under a
  virtual screen: `Xvfb :96 -screen 0 1920x1080x24 &`, then `DISPLAY=:96 blender -b ...`. (Cycles on the
  processor works too, but is far slower for plates.)
- `explainer-film-setup` checks for Blender and Xvfb and writes `machine-settings.env` in the kit (BLENDER,
  BLENDER_DISPLAY, PAPER_FILM_BROWSER); `check-shot.sh` and the checker's tests read it.
- Budget a set by how long a frame takes to film, not by a triangle count: on the Works a held frame took
  about 0.9 s and a sliding one about 4.3 s (round 4, one worker). Measure a slow page with
  `node paper-film/tools/profile_frame.mjs PAGE TIME` (or `PROFILE_SCENE=notice-corner ... - 9` for a scene).

## 2. Build the place by script

Copy the pit village as the pattern (`paper-film/blender/pit-village/`):
1. Surfaces and models from Poly Haven (free, CC0): `fetch_street_textures.py`; `props/poly_haven_choices.py`
   lists the models, `props/download_poly_haven.py` fetches them and `props/convert_poly_haven.py` makes the
   prop library (it can paint out a maker's label: `PAINT_OUT` in the choices file).
2. Props Poly Haven doesn't have are built by script (`props/build_scripted_props.py` with `scripted_kit.py`
   and `prop_library.py`). No blank signs, book covers or plain boxes: every sign carries real lettering
   (`props/paint_prop_pictures.py`; fonts and their OFL licences in `props/fonts/`), and the painter writes
   `lettering-sizes.json` before the builder runs. Check lettering reads at phone size
   (`props/readability_test.py`, `props/make_sheet.py`).
3. The street: `build_street.py --out FOLDER --name NAME` (it refuses to overwrite without `--replace`).
4. People: `paper-film/blender/figures/build_figures.py` (waiting men, walkers; cloth from
   `fetch_cloth_textures.py`). Check them lit by a lamp from the camera's side (`figure_sheet.py`): that light
   showed bald-looking heads. A waiting crowd stands across the line of sight, two deep, with gaps between
   shoulders; a single-file queue seen from behind is one dark column (lesson 132).
5. A second place's props: `paper-film/blender/inflation-chapter-2-newcomers/props/` (built with `--choices`,
   `--library` and `--scratch`).

## 3. Compose each view with the shot checker

1. Write the shot's assemble script (pattern: `pit-village/assemble_notice_corner.py`; shared steps in
   `pit-village/set_dressing.py`: `place_prop` stands a prop on the first surface a ray straight down meets,
   `light_reaches` limits a light to some objects, `glow_material`, `brazier_fire`, `render`,
   `export_for_film`). Stand the camera where a person would stand, at eye height (1.5 to 1.9 m), level; turn
   it to put where the lines meet beside the subject, then only slide it.
2. Write the check file (copy `examples/notice-corner/shot-check.json` for a still life, or
   `examples/inflation-chapter-2-newcomers/works-w1-shot-check.json` for a crowd): the subject, the story props,
   the work props, what stands on what, the words that must be read, and `"story_reaches_down": 0.70` so the
   story fills the frame's lower part.
3. Run the checker (about a minute):
   `BLEND=assets/models/<place>/<scene>.blend paper-film/tools/check-shot.sh SHOT_SCRIPT CHECK_FILE OUT_FOLDER -- --view end`
   then read `OUT_FOLDER/report.md` and look at `marked.jpg`. Fix the first problem only, then run it again:
   fix the camera first (it moves everything), then the props, then the light. Give a finished EEVEE still and
   its log (`RENDER_LOG=...`) to judge the light rules; a log with "Shadow buffer full" or "Could not allocate
   shadow atlas" means the light can't be judged.
4. The rules came from a still life. A crowd or an overview breaks some on purpose (the Works' accepted gate
   views still list 13 to 29 problems each). Nothing marks a problem as accepted yet: write down in the
   project's notes which ones you accept, why, and who agreed, and judge only new problems after that.
5. Before trusting a change to the checker itself, run its tests:
   `paper-film/blender/tests/run-checker-tests.sh OUT_FOLDER` (eleven faults planted on purpose; each report's
   first fix must name its fault; needs the pit village street, see the note in that file).

## 4. Draw the plate and export the set

- Draw the plate from the start of the slide, with a lens a little wider than the film's (the notice corner:
  64.4 degrees against the film's 60.4), 1536 x 2730, with EEVEE: about 10 minutes. A 540 x 960 preview takes
  about a minute.
- The plate must render cleanly (no shadow-memory faults in its log) and pass the light rules before anyone
  pays to paint it.
- Draw people so they cast no long shadows (only a small soft one under their feet): the painter leaves long
  shadows behind when asked to remove the people (lesson 135).
- Darken a faint glow inside a hollow (a drum's inner glow) before painting: the painter lifts it into a
  bright band (lesson 138).
- Export the set for the film: `assemble_notice_corner.py --plate PLATE --export` writes the set and signs as
  .glb and the camera as `notice-corner-camera.json` (`set_dressing.export_for_film` needs its folder).

## 5. Paint it over (paid: confirm the cost with the user first)

1. Flux 3 edit on fal: image 1 the plate, image 2 a painting in the film's style (send it at about 1 million
   pixels: the pictures sent are charged too). Ask it to keep every element where it is and to add no people;
   give it the critics' painter words (what to keep), and never let it add flames, smoke, glows or new shadows
   round the near props (they slide or blink out once the camera moves). For people: far walkers are "flat dark
   shapes with no pale spots"; a facing man's face is lost in shadow under his cap.
2. Resize the result to the plate's exact size, then line it up with the plate:
   `python3 -I paper-film/tools/align_painting.py CHECK_FILE PLATE_FACTS PAINTING OUT_PAINTING`, where
   PLATE_FACTS is `shot_facts.py`'s folder for the plate's own camera and lens (`--camera-at ... --fov PLATE_LENS`).
3. A "behind" painting for what the near props hide: ask Flux once more, with the lined-up painting as the
   only picture, to paint the near props out; line it up with `align_painting.py ... --against PAINTING`; then
   keep the first painting's shadows round them:
   `python3 -I paper-film/tools/keep_painted_shadows.py CHECK_FILE PLATE_FACTS PAINTING BEHIND OUT`.
   For a slide past people with no painting of them gone, `paper-film/tools/make_behind_picture.py` fills in
   their outlines from round about (free; look at its `--look` picture).
4. Look at the painting against the plate: the people test's men went from about 15% to about 50% of their
   surroundings' brightness when painted (a must-fix: on a phone they turned mid-grey), and painted figures
   match the street's brushwork where dark figures laid over it read as shadow puppets (lesson 137).
5. Prices (lesson 139): Flux 3 edit was 2.4 US cents a megapixel when the plan was written and 4.8 a day later,
   counting the returned picture and every picture sent: about 44 cents for a 2k repaint with a style picture.
   That figure was worked out from fal's price on the day, not read from a bill; check fal's estimate (or its
   request history) before each paid batch.

## 6. The page: shine the painting back onto the set

```js
import { loadProjector, projectPaintingOnto, skyCard } from '../projected-set.js';
const projector = await loadProjector('/assets/models/<place>/<view>-camera.json');
const projection = projectPaintingOnto(kit, set, painting, projector, { behind: { painting: behind, hide: nearProps } });
const sky = skyCard(kit, projection, painting, projector);   // the painted sky on a far card
```
- Lettered materials keep their own sharp surfaces (`ownSurface`): the painter garbles small print.
- Soft contact shadows under the near props, faded in as the camera starts to move
  (`contactShadow` in `pit-village-effects.js`); flames and sparks drawn live (`Flames`, `Sparks`).
- One slide per shot, never a turn (`skills/build-cinema-page/camera-and-framing.md` section 1a); lens blur
  `aperture: 4.0, maxBlur: 2`.
- While the camera holds, return `still: true` and mark flames, smoke and flicker with `kit.moving(...)`: the
  stage draws the painted set once.
- State changes on a held shot: `projection.setPainting(picture)` (a time cut), `projection.blendTo(picture,
  amount)` (a short blend), `projection.setView(projector, picture)` (another view of the same set). A state
  picture changes only where something changed: `paper-film/tools/make_state_picture.py` builds it from the two
  plates' difference and the changed things' outlines. When only people vanish at a cut, change something else
  with them (the fire lower, the light later), or it reads as a glitch (lesson 136).
- Long chapters of heavy sets: `buildCinemaChapter({ ..., lazy: true })`; each page exports its `join`.

## 7. Check before filming

1. Four stills: the projector's own view (it must match the painting), the end of the move, a middle moment,
   and the `weights` view (orange wears the painting, blue its own surface; blue at a frame edge means the
   camera left the painted area).
2. The shot checker on the page's own end frame, independent critics on the stills, then film
   (`skills/film-and-finish`), and look at the film in motion: `paper-film/tools/find_jumps.py` lists sudden
   jumps between frames (give it the planned cut times), and a clip without narration gets music with
   `paper-film/tools/add_music_bed.sh`.

## Worked examples in the kit

- The notice corner: `paper-film/blender/pit-village/assemble_notice_corner.py`, `examples/notice-corner/`,
  `paper-film/scenes/notice-corner.js`.
- The people test (painted men leaving): `pit-village/assemble_people_test.py`, `examples/people-test/`,
  `paper-film/scenes/people-test.js`.
- The first built test (log 29): `pit-village/assemble_lockout.py`, `paper-film/scenes/lockout-test.js`.
- The Works (chapter 2 for newcomers, pages 3 to 5): `paper-film/scenes/inflation-chapter-2-newcomers/` with
  `works-effects.js`, its check files in `examples/inflation-chapter-2-newcomers/`, state changes in
  `paper-film/scenes/works-states-test.js`. Its Blender scripts are still being changed in the austerity
  project and come in a later copy (`kit-sync-notes.md`).
- None of the pictures or models are in the plugin; the scripts rebuild the pit village, and the austerity
  project's film kit has everything.

## Traps

- Never put a picture program's lettering on screen; use the set's own lettered props.
- A turn during a move slides where the lines meet across the frame: slide only.
- A full-frame helper pass must not test depth (`runPass` turns it off).
- Smoke blown away from the camera piles up into rings: blow it across the view (lesson 134).
- The main rule can pass while the bottom of the frame is empty: a story object must reach about 0.70 down
  (lesson 133; `story_reaches_down` in the check file).
- Line up every painting with its plate, and keep the painted shadows in the props-removed copy (lessons 122,
  123).
