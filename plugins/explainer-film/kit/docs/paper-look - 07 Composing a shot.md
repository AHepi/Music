# 07 Composing a shot

What this file is: the rules for placing props and the camera so a shot looks arranged rather than
scattered. They come from log 30 of the project story: a picture made by Nano Banana Pro from our empty
pit village street and our props ("30 Test - composed by Nano Banana - own camera" in the austerity project's
`austerity-explainer/experiments/`)
was measured and taken apart by independent critics, and each reason was checked against the picture
and against our own clip 29, which the user found unarranged. Only reasons that told the two apart
were kept.

The comparison picture "30 Why it works - do the strongest things agree" shows the main rule at a glance.

Positions are fractions of the frame: 0 is the left or top edge, 1 the right or bottom edge.
The tool `paper-film/tools/measure_composition.py` gives most of the numbers below.

## The main rule: every strong thing points at the same place

List where these fall in a test frame:

- where the street's straight lines meet (kerbs, gutters, roof edges),
- the largest bright shape,
- the warm light,
- the biggest things near the camera,
- the story's cause and its effect (in the lockout shot: the notice, and the fire and empty chair).

They must all fall in one part of the frame, the part that holds the subject. If one points elsewhere
(a bright sky, a big dark lump of sacks, lines meeting at a doorway), fix that first; it matters more
than any other adjustment.

Why: a picture feels balanced and "hard to change" when its strong signals agree. It is not an even
weight left and right: clip 29 is just as even (46 to 54 per cent) as the picture the user liked (43 to
57), and still looks unarranged, because its lines point at the colliery door, its brightest spot is a
cloud and its biggest prop is the sacks: three different places.

Check: mark four spots on the test frame (where the lines meet, the centre of the brightest 3 per cent,
the centre of the warm light, the centre of the near group). All four fall inside one box at most 0.40
of the frame wide and 0.50 tall that holds the subject.

## The rules that make it happen

1. **Aim the street at the story.** Turn the camera so the street's lines meet right at the edge of the
   subject, never on a doorway, a gap in the clouds or empty road. Where the lines meet depends only on
   which way the camera is turned, not where it stands: set the turn first, then move the camera or
   the props for size and overlap. (In Blender, 1 degree of turn moves the meeting point about 0.027 of
   the frame width with a 60-degree lens.)
   Check: all crossings of the kerb and gutter lines fall in one small box (about 0.10 wide, 0.08 tall)
   beside the subject. If the tool finds fewer than about 15 slanted lines, trace them by hand.

2. **Stand where a person would stand.** Put the camera where someone would stand to look at the
   subject (for the notice: on the pavement, an arm's length in from the kerb), at standing eye height,
   high enough to see into the drum and onto the chair seat, and keep it level: no tilt up or down, no
   roll, so posts, drainpipes and chimneys stay upright. A camera in the middle of an empty road belongs
   to no one; use it only when the shot is about the road.
   Check: the drum's top shows as an oval; posts and drainpipes do not lean; in Blender the camera's X
   rotation is exactly 90 and Y is 0.

3. **Build the story props as one touching group.** The props that tell the story touch or overlap:
   in the lockout picture the drum's rim covers the board's corner, the chair's back sits against the
   board and covers the bottom corner of the paper (only the signature, never the key words), the
   lantern stands on the seat, the pail in front of the chair's legs. Props spaced apart on bare
   cobbles read like a list of things; props that touch read like a sentence ("someone sat here, by a
   fire, with a lamp, next to the notice").
   Check: every story prop touches at least one other; the whole group fits in a box about a third of
   the frame wide.

4. **Overlap clearly or leave a clear gap; never let two edges just touch.** Two edges at different
   distances that only just meet flatten the depth and look stuck together.
   Check: on a 1536-wide frame, overlaps of at least 20 pixels, gaps of at least 25.

5. **Make the subject the biggest bright thing, and keep the sky dim.** The notice paper is the
   largest bright shape; nothing large in the top third is bright. Dim the sky rather than brightening
   everything else. A white chair may be the next brightest, but dirty it a little so it stays under
   the paper.
   Check: of the brightest 3 per cent of the frame (lightly blurred), at least three quarters lie in the
   story group and at least two fifths on the paper (the picture: 82 and 63 per cent; clip 29: about 20
   and 20). The paper is at least 1.8 times as bright as the frame's average.

6. **Light the subject from the people's own lights.** The fire and the lantern sit below the notice and
   warm it from below: the paper is cool at the top and warm at the bottom, with a little warm spill on
   the seat and the road. Do not spotlight particular words.
   Check: warm light covers about 1.5 to 3 per cent of the frame (the picture: 2.2; clip 29: 0.5), mostly
   round the group.

7. **Use the height of the tall frame.** Stack the story in upright columns so the eye travels from top
   to bottom. In the lockout picture: a "pit" column (winding wheels, shut gate, burning drum) beside a
   "notice" column (street lamp, notice, lantern on the chair, pail). The top third holds at least one
   story object, not just sky.

8. **Sort props by meaning.** The people's things (fire, chair, lantern, pail) go near: big, warm, lit,
   touching. The work things (cart, sacks, coal tub, barrel, dustbins) go back up the street: small, in
   shadow, in the middle band. Nothing big and dark sits in the bottom-left, where the eye enters the
   frame. Story props may be drawn somewhat bigger than life so they read on a phone; keep the same
   sizes in every shot of the place.

9. **Show the missing person with one empty object made for a person.** The empty chair with its back
   to the notice, its seat turned to the fire and a lit lantern on it says "someone sat here and has just
   stepped away". Move the lantern to the ground and the chair just looks free.

10. **Keep the far side quiet but not empty.** The side away from the subject is big, dim and finely
    detailed (brick, windows, cobbles, one or two small lights), and its lines point at the subject. This
    stops the frame tipping, but it is only needed, not enough on its own.

11. **Move the camera without turning it.** Slide it in a straight line toward the subject at a
    constant height, easing in and out, and stop on the composed frame. Because the meeting point of the
    street's lines depends only on the camera's turn, a move with no turn keeps the lines pointing at the
    subject in every frame. A turn during a move slides the meeting point across the frame: that is what
    made clip 29's move feel odd (the meeting point slid toward a doorway at the edge and the pithead
    slid out of frame, then a cut jumped to a flat close-up).
    Check: where the lines meet moves no more than 0.02 of the frame width between the first, middle and
    last frames; in Blender only the camera's position has keyframes, never its rotation.

12. **Leave room for phone buttons and titles.** Keep anything that must be read left of 0.90 across;
    only unimportant edges may reach 0.95. Video apps put their buttons down the right edge from a little
    above the middle to near the bottom. Put titles in dim sky, away from the brightest lamp.

## What a model can and can't do for you

Image models arrange props well when asked to choose their own camera (log 30). Use their pictures as a
sketch of the layout, then rebuild it with our own 3D set and props. Never use their lettering: every
model garbled the notice (one dated it 1756), and they redraw the street and props a little differently
each time, so their pictures can't be cut together with ours.
