# Changes made to the layer files during integration (every one listed, newest last)

| # | file | change | why |
|---|---|---|---|
| 1 | layers/colour_and_fade.py | new control `mottle_tallness` (socket `Mottle Tallness`, default 2.2 = the old fixed value, range 0.5 to 6) | the flat patches inside a slate ran the whole slate height, so slates looked like corrugated sheets of stripes; the reference has strokes that stop part way. Default is unchanged so nothing else moves. |
| 2 | layers/combine.py | new control `tone_blend` (socket `Tone Blend`, default 0 = old behaviour, range 0 to 1): mixes the real relief with a height made from the finished colour's brightness (the reference's own formula, 2.5 x (brightness - 9.5)) | the reference height maps were made from the colour, ours is real relief (chips sunk); the "same kind" height measures reward the colour-made height. One honest knob lets a person choose. |
