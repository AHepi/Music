# 07 Composing a shot

What this file is: the rules for placing props and the camera so a shot looks arranged rather than
scattered. They come from log 30 of the project story (the composition test). Nano Banana Pro, given our
empty pit village street and our props and free to choose its own camera, made a picture the user liked
("30 Test - composed by Nano Banana - own camera" in the austerity project's
`austerity-explainer/experiments/`; below, "the picture the user liked"). It was measured and taken apart by independent critics, and a skeptic checked each reason
against the picture and against our own clip 29, which the user found unarranged. Reasons were kept only
if they told the two apart, or (like balance, rule 10) were needed by both.

The comparison picture "30 Why it works - do the strongest things agree" shows the main rule at a glance.

Positions are fractions of the frame: 0 is the left or top edge, 1 the right or bottom edge. The tool
`paper-film/tools/measure_composition.py` gives most of the numbers below. Words used here:

- **The notice** is the printed sheet; **the board** is what it hangs on.
- **The drum** is the oil drum used for a fire.
- **Story props** are the props that tell the story (in the lockout street: the drum, the chair, the
  lantern, the pail, the board); **work props** are the rest (cart, sacks, coal tub, barrel, dustbins).
- **Where the lines meet** is the spot where the street's straight lines (kerbs, gutters, roof edges) run
  together in the distance.
- **The brightest parts** are the brightest 3 per cent of the frame after a slight blur.
- **Weight** is how strongly each part of a picture pulls the eye, from its size, brightness and detail.

## The main rule: every strong thing points at the same place

List where these fall in a test frame:

- where the lines meet,
- the brightest parts,
- the warm light,
- the biggest props near the camera,
- the story's cause and its effect (in the lockout street: the notice, and the drum's fire and the empty
  chair).

They must all fall in one part of the frame, the part that holds the subject. If one points elsewhere
(a bright sky, a big dark lump of sacks, lines meeting at a door), fix that first; it matters more than
any other adjustment.

Why: a picture feels balanced and "hard to vary" when its strong things agree. It is not an even weight
left and right: clip 29 is just as even (46 to 54 per cent) as the picture the user liked (43 to 57),
and still looks unarranged, because its lines meet at the colliery door, its brightest parts are
scattered over the sky, the fire's glow on the road and the lamps, and its biggest near prop is the
sacks: three different places.

Check: mark four spots on the test frame (where the lines meet, the centre of the brightest parts, the
centre of the warm light, the centre of the story props). All four fall inside one box at most 0.40 of
the frame wide and 0.50 tall that holds the subject.

## The rules that make it happen

1. **Aim the street at the story.** Turn the camera so the lines meet right at the edge of the subject,
   never on a doorway, a gap in the clouds or empty road. Where the lines meet depends only on which way
   the camera faces, not where it stands: set the turn first, then move the camera or the props for size
   and overlap. (In Blender, 1 degree of turn moves where the lines meet about 0.027 of the frame's width
   when the camera sees 60 degrees from the top to the bottom of the tall frame.)
   Check: all crossings of the kerb and gutter lines fall in one small box (about 0.10 of the frame wide,
   0.08 tall) beside the subject. If the tool finds fewer than about 15 of the street's straight lines,
   trace them by hand.

2. **Stand where a person would stand.** Put the camera where someone would stand to look at the subject
   (for the notice: on the pavement, an arm's length in from the kerb), at standing eye height, high
   enough to see into the drum and onto the chair seat. Keep it level, neither tipped up or down nor
   leaning to one side, so posts, drainpipes and chimneys stay upright. A camera in the middle of an empty
   road belongs to no one; use it only when the shot is about the road.
   Check: the drum's top shows as an oval; posts and drainpipes do not lean. In Blender the camera's X
   rotation is exactly 90 (level, not tipped up or down) and its Y rotation is 0 (not leaning).

3. **Build the story props as one touching group.** The story props touch or overlap. In the picture the
   user liked, the chair's back sits against the board and covers the bottom corner of the notice (only
   the signature, never the key words), the lantern stands on the seat, and the pail stands in front of
   the chair's legs; the drum's rim almost touches the board's corner (in the rebuild, overlap it
   clearly, rule 4). Props spaced apart on bare cobbles read like a list of things; props that touch read
   like a sentence ("someone sat here, by a fire, with a lamp, next to the notice").
   Check: every story prop touches or overlaps at least one other; together they fit in a box at most
   0.40 of the frame wide and 0.50 tall.

4. **Overlap clearly or leave a clear gap; never let two edges just touch.** Two edges at different
   distances that only just meet make near and far things look the same distance away, as if stuck
   together.
   Check: on a frame 1,536 pixels wide, overlaps of at least 20 pixels and gaps of at least 25. The
   picture the user liked has three pairs that just touch (the street lamp and a winding wheel, the drum
   and the board's corner, the lantern and the board's bottom): fix them in the rebuild.

5. **Make the subject the biggest bright thing, and keep the sky dim.** The notice is the largest bright
   shape; nothing large in the top third is bright. Dim the sky rather than brightening everything else.
   A white chair may be the next brightest, but dirty it a little so it stays darker than the notice.
   Check: at least three quarters of the brightest parts lie in the story props' box and at least two
   fifths on the notice (the picture the user liked: about 80 per cent, and half to two thirds; clip 29:
   about a fifth for each). The notice is at least 1.8 times as bright as the frame's average.

6. **Light the subject from the people's own lights.** The drum's fire and the lantern sit below the
   notice and warm it from below: the notice is cool at the top and warm at the bottom, with a little
   warm spill on the seat and the road. Do not spotlight particular words.
   Check: the tool's warm light share is about 1.5 to 3 per cent of the frame (the picture the user
   liked: 2.3; clip 29: 0.5), most of it round the story props.

7. **Use the height of the tall frame.** Stack the story in upright columns so the eye travels from top
   to bottom. In the picture the user liked: a "pit" column (winding wheels, shut gate, the drum) beside a
   "notice" column (street lamp, the notice, the lantern on the chair, the pail). The top third holds at
   least one story object, not just sky.
   Check: each column has something in the top, middle and bottom thirds of the frame, lined up within
   about 0.07 of the frame's width.

8. **Sort props by meaning.** Story props go near: big, warm, lit, touching. Work props go back up the
   street: small, in shadow, in the middle band of the frame. Nothing big and dark sits in the bottom
   left, where the eye enters the frame. Story props may be drawn somewhat bigger than life so they read
   on a phone; keep the same sizes in every shot of the place.
   Check: each work prop covers at most 2 per cent of the frame and is darker than the frame's average;
   nothing in the bottom-left quarter covers more than 1 per cent (clip 29's sacks cover about 7).

9. **Show the missing person with one empty prop made for a person.** The empty chair with its back to
   the notice, its seat turned to the fire and a lit lantern on it says "someone sat here and has just
   stepped away". Move the lantern to the ground and the chair just looks free.
   Check: the chair stands directly below the notice, its seat visible, the lantern lit on the seat.

10. **Keep the side of the frame away from the subject quiet but not empty.** That side is big, dim and
    finely detailed (brick, windows, cobbles, one or two small lights), and its lines point at the
    subject. This keeps the frame from feeling lopsided, but it does not make the shot work on its own.
    Check: the tool's weight split is between 40 to 60 and 48 to 52 per cent; no light on the quiet side
    is as bright as the notice, and no prop there covers more than 2 per cent of the frame.

11. **Move the camera without turning it.** Slide it in a straight line toward the subject at a constant
    height, starting and stopping gently, and stop on the composed frame. Because where the lines meet
    depends only on which way the camera faces, a move with no turn keeps the lines pointing at the
    subject in every frame. A turn during a move slides where the lines meet across the frame: that is
    what made clip 29's move feel odd (where the lines meet slid toward the colliery door at the frame's
    edge and the pithead slid out of frame; then a cut jumped to a close-up of the notice seen straight
    on, with no street or fire).
    Check: where the lines meet moves no more than 0.02 of the frame's width between the first, middle
    and last frames. In Blender only the camera's position is set to change during the move (those
    settings are called keyframes), never which way it faces.

12. **Leave room for phone buttons and titles.** Keep anything that must be read left of 0.90 across;
    only unimportant edges may reach 0.95. Video apps put their buttons down the right edge, from a little
    above the middle to near the bottom. Put titles in dim sky, away from the brightest lamp.
    Check: the notice's right edge is at or left of 0.90 (the picture the user liked: 0.91, with the
    chair and pail at 0.96 to 0.97, so fix it in the rebuild).

## What a picture-making program can and can't do for you

In one run, Nano Banana Pro arranged the props well when it was free to choose the camera (log 30); with
our camera it spread them like a catalogue. Use such a picture as a sketch of the composition, then
rebuild it with our own 3D set and props. Never use a program's lettering: Nano Banana Pro and Seedance
garbled the notice (1756, 1828) and Flux's looks wrong too. Nano Banana Pro and Seedance also redraw the
street, and every program redraws the props, so their pictures can't be cut together with ours.

## Traps

- Never put a program's lettering on screen; use our own 3D notice.
- A turn during a move slides where the lines meet: check the first, middle and last frames.
- The measuring tool needs crisp lines: if it finds fewer than about 15, trace them by hand.
- Copy a sketch's composition, never its faults: check rules 4 and 12 on the rebuild, not on the sketch.
