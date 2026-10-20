# IDEA - not started (the person asked not to launch more work for now)

What the person said (20 October, about 11:40): "You can create masking layers with generations. Then use the masks as a layer to engineer into a procedure."

What it would mean in this project: an image generator (fal) makes black-and-white MASKS (where moss grows, where paint has chipped, where rust blooms),
or sheets of separate shapes ("stamps": moss clumps, chips, cracks, stains on black). The Blender recipe uses them as the "where" of a layer, while the
layer still makes its own colour, height and roughness, and the layout still decides the rules (moss hangs from upper edges, chips sit on lower edges).
Stamps scattered per piece with random turn, size and place give endless new patterns from one generation.

Why it may help: the look checkers' main complaints were about SHAPES (paint "flame tongues", moss as khaki flakes, L-shaped chips). Shapes are what node
noise does worst and generators do best; colour, relief and control are what the recipe does well. It also keeps the separate layers the person asked for.

Problems to solve: masks must repeat without a seam; one fixed mask repeats over big areas (use stamps or cut-and-rearrange, as in the wood job);
generators may not give clean black-and-white (threshold in the recipe); a new seed only rearranges stamps, new shapes need a new paid generation.

Possible first test (paid, needs the person's yes and a limit, under US$1): two or three stamp sheets (moss clumps, chips) plugged into the slate's MOSS and
DAMAGE layers, compared with the current masks by the look checker's measures and by eye.

## Started as a test (20 October, about 13:20)
The person said: "Yeah do it as a test. But then move on to another set. Say, the street view test. Because it's going to need a specularity map to
mimick wetness." Approved spend for this test: up to US$1.00 in total (fal). Folder: mask_test/. The street work (wetness layer and specular map for the
pit village street set) runs alongside in street_wet/; it has no paid image generation.
