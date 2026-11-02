# Tea house lessons (0.5.0)

What this folder is: a look by eye at what the tea house blind test (log 44) added to the plugin, on a small tea-room corner built by `build_check_scene.py`, dressed by `materials/apply_by_role.py` and drawn by `stage/render_small.py` at 540 x 960, 24 samples (94 s).

## What the picture shows

- A plaster wall's two windows, each given a painted casing, a sill with its drip line, and a sash with glazing bars and a meeting rail (the builder made only the glass).
- A brass urn and its tap, a copper kettle, and a china teapot and cups, each with its own made material (old brass with tarnish patches, copper, glossy glaze).
- The new warning fired: glowing glass and the lamp take 5.5 percent of this close frame, and the picture is indeed too bright and warm. That is what the warning is for; the scene was left as built to show it.

## Not shown

- The materials in the blue-hour street light at a distance (the tea house itself was built with 0.4.1).
- The plaster here shows streaks: the street bundle's plaster picture is stretched over the place's size, and this place is only 6 m wide. Not part of 0.5.0.

## Traps

- A close interior with a lit window and a lamp fills more than 2 percent of the frame with glow: expect the warning, and make the window `window dim` or move the camera back.
