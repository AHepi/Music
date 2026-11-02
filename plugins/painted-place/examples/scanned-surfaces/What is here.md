# Scanned surfaces: before and after

What this folder is: the same two places dressed twice, once with the plugin's code-made surfaces (`--no-scans`) and once with the free Poly Haven scans (`materials/textures/`), everything else the same: shapes, camera, details, dials. The owner's words that started it (2 November 2026, 22:38): "Just a hint. See if you can improve the look using PBR textures from poly haven."

## The pictures

| File | What it shows |
|---|---|
| `lane close look - code-made (left) and scanned (right).jpg` | The clearest difference. The flagstones become worn, pitted stone whose relief breaks up the lamps' reflections (left: smooth, plastic slabs); the wall stones get a real sandstone's mottling; the cart's boards become weathered wood. The setts are left as they were (the owner called the street's pavement great). |
| `lane from the camera - code-made (left) and scanned (right).jpg` | From the lane's own camera the change is small: the cart, the near walls a little darker and grainier. At this distance the setts and their reflections carry the picture either way. |
| `bach - code-made (left) and scanned (right).jpg` | The beach house: the walk planks in front show grain and weathering; the house's boards differ board by board and show grain under the old paint; the sand near the fire is barely changed. |
| `bach close look - code-made (top) and scanned (bottom).jpg` | The house close: more bare weathered wood showing, less paint. |

Close look camera: standing at (-2.7, 1.0, 1.3) looking at (-5.1, 7.5, 0.8), 32 mm, the lane's dials (exposure 0.3, window light 0.3, lamp light 0.6, sky light 1.6, no off-frame amber light). The lane's drawing took 194 seconds with the scans and 175 without (2-processor computer, 540 x 960, 32 samples).

## What was tried and changed on the way

- The sandstone grain first only multiplied the flags' colour: on wet, glossy flags it vanished under the reflections. Deeper relief on the flags (14 mm against 6 mm on walls) is what made them read as stone.
- The scanned wood first carried as much old paint as the code-made boards did, hiding the grain; the paint now holds on less.
- The sand scan is barely visible at 540 x 960; it shows in close views and at full size.

## Traps

- Judge scans close up and at full size. From the standing camera at 540 x 960 most of their detail is below what the paint filter keeps.
- A colour-only overlay disappears on a wet surface: relief is what shows in a reflection.
