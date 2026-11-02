# 45 Brushstrokes: pictures to judge

What this folder is: the first try of the Blender Studio's Brushstroke Tools add-on on the plugin's tea house picture (log 45 in the project story; decision 58). Nothing here is in the `painted-place` plugin yet: the owner picks a version first.

## How the pieces fit

1. **The finished picture** (`/home/claude/blind-test-2/plugin-build/round-2.png`, the plugin builder's round 2, 540 x 960) and **its scene** (`DRESSED-4.blend` beside it) go in.
2. **`45 paint_over.py`** finds the big surfaces the camera sees, copies the faces that face the camera and lifts each to its own visible skin (in front of the ashlar, on top of the setts, behind the timbers), lays flow lines along them, and lets the add-on's fill grow strokes along the lines. Each stroke takes the picture's colour at its middle; strokes that start behind something, or would carry a lamp's colour, are dropped. Only the strokes are drawn (everything else hidden but still in front), and they are laid over the picture with lit windows and lamps kept clear. It hands on one picture, and the strokes alone beside it.
3. **`45 run_variations.sh`** runs it six ways (B to G); **`45 make_judging_set.py`** stamps each with its letter and makes the close-up sheet.

| Letter | What changes |
|---|---|
| A | No strokes: the plugin's picture as it was |
| B | Fine strokes: 0.25 m wide, 0.7 m long, 4.5 per metre each way |
| C | Medium strokes: 0.45 m wide, 1.1 m long, 3 per metre each way, the "fat (loaded)" oil brush |
| D | Large strokes: 0.8 m wide, 1.8 m long, 1.8 per metre each way |
| E | As C, with the "dry (loaded)" brush |
| F | As C, with the "feathery" brush |
| G | As C, with no strokes nearer the camera than 7 m |

Each took about 2 minutes on top of the picture (2 processors, 24 samples).

## The improved script

`45 paint_over - improved after the pictures were sent.py` is the same idea, changed after B to G were made, on the tea house and the beach house:
each surface's copy stays joined (sharp corners split) so curved ground works; ground gets flow lines laid from above so strokes follow rises
and ripples; strokes are lifted onto the bumps of their own surface (ashlar, setts); rays pass through smoke; a stroke is dropped only if
something off its own plane stands in front of its middle, or its middle shows a glowing surface; big faces are cut up and what the camera
cannot see is left out. On the tea house it keeps 3,487 strokes where the first kept about 2,400, most of the gain on the side walls.
On the beach house's smooth sand the strokes barely show: a stroke in the sand's own colour on smooth sand looks like the sand.

## The add-on

Brushstroke Tools 1.2.3, Blender Studio, GPL 3.0 or later: https://extensions.blender.org/add-ons/brushstroke-tools/ (file checked: sha256 `b66728b70b2d6af5ad942b5aa27fcc540db0972c22169480aa552d1e22061fe4`). Its node groups (`assets/core/brushstroke_tools-resources.blend`) and oil brushes (`assets/styles/brushstroke_tools-oil_brushes.blend`) are loaded as data; none of its code is run. It is not stored here.

## Not tried

Strokes lit by the scene's own lamps (the add-on's usual way, slower); the full size; another place; the sky.

## Traps

- Without flow lines the add-on points every stroke a random way; the surface's flat map does not steer it.
- The add-on's fill grows on a mesh object; on a curves object the strokes cannot be turned into a mesh.
- A stroke's colour must come from where the stroke is actually seen: probes that hit windows or timbers in front of a wall lift the strokes over them.
- `45 paint_over.py` reads the add-on from `/home/claude/downloads/brushstroke-tools/extracted/`; download and unpack it there (into its own folder) first.
