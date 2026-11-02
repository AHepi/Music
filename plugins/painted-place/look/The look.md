# The look

What this file is: the target. One page a builder reads before building and a judge reads before judging. The pictures in `reference/` are the authority; this page says in words and numbers what they have in common. Written from the pictures, not from earlier lessons.

## The pictures

| File | What it is |
|---|---|
| `painting - Britain 1915 munitions hall.jpg` | A series painting: daylight shafts through tall windows, brass shells, rust, grime |
| `painting - rainy tenement street at dusk.jpg` | A series painting: gas lamps and lit windows in rain, wet cobbles mirroring them |
| `painting - pithead at sunset.jpg` | A series painting: the headframe dark against the last light, lit windows answering it |
| `render - Rain on the Old Curve street.jpg` | A Blender render (Cycles) the owner called close enough: the look stage's numbers come from its scene |
| `render - coal mine with the look stage.jpg` | The coal mine after the look stage and one fix pass (the transfer test, 2 November 2026). A reference for light, colour and air only: its smoke is balloon-shaped, which is a shape fault, not the look |

The two paintings with words in them carry their captions baked in; a built place never has words in it.

## What they have in common

1. **A dark picture in which light is rare and precious.** Most of the frame is shadow. The warm light (lamps, lit windows, a low sun, brass) covers only a small part of the frame and carries the whole picture.
2. **Two colour families.** Cool shadow: teal-blue to slate (`#0d2637`, `#3c4a51`, `#6e8c8a`). Warm light: amber (`#d2a76b`, `#dbad72`). Rust-orange on iron and brick is the bridge between them. Blacks are never pure: warm-brown near light, blue-black away from it.
3. **One dominant light source, always doing something to the air.** A beam through dust, a pool on wet stone, a glow on the nearest wall, a reflection in a puddle. Light has a direction and a consequence. There is never flat, even light.
4. **Air between here and there.** Far things are lighter and bluer than near things; the haze gives the place depth.
5. **Everything old and used.** Rust on every iron edge, peeling paint, grime in corners, soot, mud, puddles. A clean new surface breaks the look at once.
6. **Framing.** Tall frame, 9 by 16. Strong single-point perspective: an aisle, a street, a rail pulls the eye to a vanishing point in the upper middle. One hero subject, centred or near it. A detailed foreground along the bottom edge. The eye at a standing person's height.
7. **Scale from things people use,** not from people: benches, lamps, carts, doorways. No people, no hands.
8. **Period and place.** Industrial Britain around 1915: brick, iron, gas lamps, cobbles, tenements, pitheads. A new subject keeps this material world (a tea house is brass, dark wood and steamed glass, not chrome).
9. **Finish.** Brushy but legible: you can count the cobbles. Crisp edges on built things, soft edges in air and smoke. Not a cartoon, not flat vector, not a photograph.

## The measured bands

Measured with `measure.py` on the reference pictures (the munitions hall is brighter than the rest; the bands hold all five).

| Measure | Band | What it catches |
|---|---|---|
| Brightness (0 black, 1 white) | 0.14 to 0.35 | A washed-out or a crushed picture |
| Warm share of the frame | 15 to 35 percent | A picture gone cold and blue all over, or orange all over |
| Cool share of the frame | 30 to 60 percent | Same, the other way |
| Warm light coverage (bright warm dots) | 0.4 to 3.0 percent | Flat light with no lamps doing anything (too low); a blown-out picture (too high) |

A picture inside every band can still be wrong (the bands cannot see a balloon-shaped cloud of smoke or a toy-like tree). That is what the judge is for. A picture outside a band is wrong in a way one dial usually fixes.

## What the look is not

Cartoon, flat vector, clean 3D render, photograph, noon daylight, pastel colours, modern materials, clean new surfaces, people in frame, text in the picture, smoke or clouds made of balloons, trees made of blobs, lamps that glow without lighting anything.

## Traps

- The munitions hall is a daylight picture; its light is still one source with a consequence (the beams). The look stage as it stands makes a blue hour; a daylight variant does not exist yet.
- The bands were measured on five pictures. A sixth reference that sits outside them should widen the band, not be forced in.
