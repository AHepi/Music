# Shot check: w2-plate-facts

9 problems found in 16 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (rule 3: story props in the frame). Move hand truck out from behind no-2 gateway, or in front of it.

## Problems

1. **rule 3: story props in the frame.** hand truck is in the frame but hidden behind no-2 gateway.
   - Fix: Move hand truck out from behind no-2 gateway, or in front of it.
2. **rule 3: story props together in the street.** hand truck stands 3.00 m from the nearest other story prop (man 1) in the street: the group should stand together.
   - Fix: Move hand truck about 0.64 m left (across the street) and 2.83 m down the street, toward man 1.
3. **rule 3: story props close together.** The story props (leaving out no-2 board) fill a box 0.44 of the frame wide and 0.27 tall (limit 0.40 x 0.50). Its edges: man 8's left side (0.23 across), petrol drum's right side (0.67), no-2 gateway's top (0.44 down) and man 8's bottom (0.71).
   - Fix: Move man 8 about 0.25 m to the right.
4. **rule 4: overlap clearly or leave a clear gap.** man 7's edge runs right along man 8's edge for 43 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.53 to 0.54 down, around 0.30 across; man 8 is nearer the camera)
   - Fix: Move man 7 about 0.09 m to the left so man 7 clearly passes behind man 8, or move man 7 about 0.11 m to the right to leave a clear gap.
5. **rule 4: overlap clearly or leave a clear gap.** man 3 and man 5 almost touch: 15 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.45 across, 0.55 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 0.21 m to the right so it clearly overlaps man 3, or move man 5 about 0.04 m to the left to leave a clear gap.
6. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 4's edge for 36 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.60 to 0.61 down, around 0.48 across; man 4 is nearer the camera)
   - Fix: Move man 3 about 0.13 m to the left so man 3 clearly passes behind man 4, or move man 3 about 0.15 m to the right to leave a clear gap.
7. **rule 8: nothing big where the eye enters.** man 8 fills 1.3% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 8 out of the bottom-left quarter.
8. **rule 4: overlap clearly or leave a clear gap.** man 3 and man 6 almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.44 across, 0.62 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.19 m to the right and about 0.40 m nearer to the camera (but man 7 stands there) so it clearly overlaps man 3, or move man 6 about 0.02 m to the left and about 0.05 m further from the camera to leave a clear gap.
9. **rule 12: titles in dim sky.** Only 55% of the title area is sky (need 85%). (55% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, hand truck, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gateway is 0.005 of the frame width away (limit 0.03).
- rule 3: one touching group: Every story prop that shows touches or overlaps another. Not showing at all: hand truck (problem 1).
- rule 3: nothing hides the words: 0% of no-2 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (petrol drum 0.70, diesel drum 0.71, man 1 0.49, man 2 0.52, man 3 0.53, man 4 0.48, man 5 0.44, man 6 0.44, man 7 0.39, man 8 0.33, no-2 board 0.52).

## Notes

- rule 4: overlap clearly or leave a clear gap: man 6 overlaps man 1 by 18 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
