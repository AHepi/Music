# Shot check: w3-h

23 problems found in 31 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move man 2 off brazier and place it again from just above the pavement.

## Problems

1. **props rest where they should.** man 2 rests on brazier, not on the ground (at Blender x -4.64, y 21.27).
   - Fix: Move man 2 off brazier and place it again from just above the pavement.
2. **rule 3: one touching group.** Standing apart from the others: gate boards, no-2 crates.
   - Fix: Move gate boards about 2.60 m lower so it overlaps man 1; move gate boards toward no-2 crates until they overlap.
3. **rule 3: story props together in the street.** no-2 crates stands 1.92 m from the nearest other story prop (gate boards) in the street: the group should stand together.
   - Fix: Move no-2 crates about 1.57 m left (across the street) and 0.94 m down the street, toward gate boards.
4. **rule 1: aim the street at the story.** The street's lines meet at 0.500 across, 0.500 down; the nearest edge of both gates is 0.150 of the frame width away (limit 0.03): 111 pixels to the right and 118 pixels below. (both gates spans 0.25 to 0.75 across, 0.55 to 0.63 down)
   - Fix: Turning the camera won't help: it moves where the lines meet and the props together. Lower the camera about 2.22 m (both gates then rises on screen while where the lines meet stays put), or move both gates about 2.22 m higher; and move the camera about 2.09 m to the right, or move both gates about 2.09 m to the left.
5. **rule 3: story props close together.** The story props fill a box 0.52 of the frame wide and 0.16 tall (limit 0.40 x 0.50). Its edges: brazier's left side (0.23 across), both gates's right side (0.75), gate boards's top (0.50 down) and man 7's bottom (0.66).
   - Fix: Move both gates about 2.48 m to the left.
6. **rule 4: overlap clearly or leave a clear gap.** both gates and man 1 almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.60 down; man 1 is nearer the camera)
   - Fix: Move man 1 about 0.34 m to the right so it clearly overlaps both gates, or move man 1 about 0.36 m to the left to leave a clear gap.
7. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 2: it reaches 1 pixel into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.28 across, 0.62 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.24 m to the left and about 0.83 m further from the camera (but man 5 stands there) so it clearly overlaps man 2, or move man 6 about 0.31 m to the right and about 1.00 m nearer to the camera (but man 7 stands there) to leave a clear gap.
8. **rule 4: overlap clearly or leave a clear gap.** man 2 and man 4 almost touch: 2 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.27 across, 0.61 down; man 4 is nearer the camera)
   - Fix: Move man 4 about 0.33 m to the left so it clearly overlaps man 2, or move man 4 about 0.31 m to the right to leave a clear gap.
9. **rule 4: overlap clearly or leave a clear gap.** brazier and lantern almost touch: 2 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.23 across, 0.61 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.30 m to the right and about 0.15 m higher so it clearly overlaps brazier, or move lantern about 0.28 m to the left and about 0.14 m lower to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** man 1 and man 3 almost touch: 4 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.60 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.37 m to the right so it clearly overlaps man 1, or move man 3 about 0.29 m to the left to leave a clear gap.
11. **rule 4: overlap clearly or leave a clear gap.** both gates and man 7 almost touch: 6 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.61 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.25 m to the right and about 2.15 m further from the camera so it clearly overlaps both gates, or move man 7 about 0.16 m to the left and about 1.22 m nearer to the camera to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** brazier and man 3 almost touch: 6 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.27 across, 0.62 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.35 m to the left and about 1.53 m further from the camera (but man 1 stands there) so it clearly overlaps brazier, or move man 3 about 0.22 m to the right and about 0.89 m nearer to the camera (but man 4 stands there) to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** man 7 only just overlaps man 3: it reaches 6 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.62 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.14 m to the left and about 0.92 m further from the camera (but man 6 stands there) so it clearly overlaps man 3, or move man 7 about 0.30 m to the right and about 1.82 m nearer to the camera to leave a clear gap.
14. **rule 4: overlap clearly or leave a clear gap.** man 3 and no-1 drums almost touch: 10 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.26 across, 0.62 down; no-1 drums is nearer the camera)
   - Fix: Move no-1 drums about 0.43 m to the right and about 1.28 m nearer to the camera so it clearly overlaps man 3, or move no-1 drums about 0.17 m to the left and about 0.55 m further from the camera (but man 2 stands there) to leave a clear gap.
15. **rule 4: overlap clearly or leave a clear gap.** no-1 drums only just overlaps man 2: it reaches 9 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.25 across, 0.62 down; no-1 drums is nearer the camera)
   - Fix: Move no-1 drums about 0.12 m to the right and about 0.60 m further from the camera (but man 2 stands there) so it clearly overlaps man 2, or move no-1 drums about 0.42 m to the left and about 1.87 m nearer to the camera to leave a clear gap.
16. **rule 4: overlap clearly or leave a clear gap.** man 2 and lantern almost touch: 11 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.23 across, 0.61 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.48 m to the right so it clearly overlaps man 2, or move lantern about 0.16 m to the left to leave a clear gap.
17. **rule 4: overlap clearly or leave a clear gap.** man 3 only just overlaps man 2: it reaches 10 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.27 across, 0.62 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.10 m to the left and about 0.60 m nearer to the camera (but man 4 stands there) so it clearly overlaps man 2, or move man 3 about 0.41 m to the right and about 2.66 m further from the camera to leave a clear gap.
18. **rule 4: overlap clearly or leave a clear gap.** brazier and man 4 almost touch: 13 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.27 across, 0.61 down; man 4 is nearer the camera)
   - Fix: Move man 4 about 0.51 m to the left so it clearly overlaps brazier, or move man 4 about 0.13 m to the right to leave a clear gap.
19. **rule 4: overlap clearly or leave a clear gap.** man 2 and man 7 almost touch: 13 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.62 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.47 m to the left so it clearly overlaps man 2, or move man 7 about 0.12 m to the right to leave a clear gap.
20. **rule 4: overlap clearly or leave a clear gap.** man 2 only just overlaps brazier: it reaches 12 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.26 across, 0.62 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.75 m nearer to the camera (but man 3 stands there) so it clearly overlaps brazier, or move man 2 about 5.05 m further from the camera to leave a clear gap.
21. **rule 4: overlap clearly or leave a clear gap.** brazier and man 6 almost touch: 15 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.28 across, 0.61 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.52 m to the left so it clearly overlaps brazier, or move man 6 about 0.09 m to the right to leave a clear gap.
22. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 3: it reaches 15 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.28 across, 0.62 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.03 m to the left and about 0.29 m further from the camera so it clearly overlaps man 3, or move man 6 about 0.36 m to the right and about 2.79 m nearer to the camera to leave a clear gap.
23. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 4: it reaches 15 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.62 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.02 m to the left and about 0.30 m further from the camera so it clearly overlaps man 4, or move man 6 about 0.26 m to the right and about 3.24 m nearer to the camera to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 0.91 m above the pavement under it (a standing person: 0.80 to 7.00 m).
- props rest where they should: brazier, no-1 drums, no-2 drums, no-2 crates, handcart, man 1, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 3: nothing hides the words: 0% of gate boards's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 1% of bank sign's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (gate boards 0.72, brazier 0.26, no-2 crates 0.75, man 1 0.33, man 2 0.28, man 3 0.29, man 4 0.31, man 5 0.32, man 6 0.31, man 7 0.32, bank sign 0.21).
- rule 12: titles in dim sky: The title area (0.06 to 0.90 across, 0.05 to 0.22 down) is dim, empty sky.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- rule 4: overlap clearly or leave a clear gap: both gates and man 5 are 21 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: both gates and man 6 are 23 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 1 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 2 and man 5 are 19 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 4 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 4 and no-1 drums are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 5 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 6 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 6 and no-1 drums are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
