# Film code for chapter 2

What this folder is: the code that draws chapter 2 in the cinema look (log 19), kept here so the film
can be made again. It sits on top of the paper pop-up film kit ("14 Paper pop-up film kit", the three
zip files): copy these files over a fresh copy of the kit, keeping the same folders.

- `stage/cinema-stage.js`, `stage/cinema-stage.html`: the cinema stage. Draws one page's 3D scene
  with lens blur, glow and a film finish (tint, grain, soft dark corners), lays the page's flat
  graphics on top, and joins pages with a page peel, a dissolve or a dip to black.
- `scenes/cinema-kit.js`: what a page builds with: lamp and haze, painted rooms with depth, flat
  painted backdrops, paper cut-outs, 3D words and printed cards, a speaking figure, camera paths,
  shakes, and the narrator's word times.
- `scenes/models.js`: card models (factory, house, shell, coin, banknote bundle, price tag, flip
  counter, dial, oil barrel, paper boat, bar columns, thread chart).
- `scenes/effects.js`: dust in the light, light beams, dust bursts, smoke, falling coins.
- `scenes/graphics.js`: the flat documentary graphics (place-and-year titles, hooks, counters,
  labels pointing at things, line charts, bars, credits).
- `scenes/cinema-chapter.js`: joins the ten pages into one chapter.
- `scenes/inflation-chapter-2.js` and `scenes/inflation-chapter-2/page-1.js` to `page-10.js`: the
  chapter and its pages (`two-factories-set.js` is the model set used on pages 3 and 8).
- `scenes/cinema-test-pages.js`: draws chosen pages on their own, for checking stills.
- `tools/render-paper-film.mjs`: films a scene or draws stills (patched to use the small headless
  browser and the cinema stage). `tools/film-chapter-parallel.sh`: films a chapter two stretches at
  a time. `tools/prepare_relief.py`: turns a painting and its distance picture into a painted room
  with depth. `tools/relief_points.py`: says where a spot on a painted room sits in 3D.
- `examples/`: the chapter's timeline (every word's time), word times and cut list.

Pictures are in `../pictures/` (paintings, painted rooms with depth, cut-out pieces); sound is in
`../narration/` and `../mix/`.
