# Shot check: w4 (light rules, the men, gates and sign boards left out of the picture-match test)

19 problems found in 30 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 3: one touching group). Move jacket and cap about 0.47 m to the left so it overlaps man 8; move upturned crate about 0.28 m further from the camera so it overlaps mug and wages; move upturned crate (with mug and wages on it) about 0.29 m further from the camera so it overlaps upturned crate.

## Problems

1. **rule 3: one touching group.** Standing apart from the others: jacket and cap, upturned crate, mug and wages.
   - Fix: Move jacket and cap about 0.47 m to the left so it overlaps man 8; move upturned crate about 0.28 m further from the camera so it overlaps mug and wages; move upturned crate (with mug and wages on it) about 0.29 m further from the camera so it overlaps upturned crate.
2. **rule 6: warm light from the people's own lights.** Warm light covers 12.1% of the frame, 4.0 times the most allowed (3%). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Most of it is round the story props: shorten how far the fire's and the lantern's light reaches, or lower the lantern's strength a little (the fire's light also lights the notice from below). 46% of the warm light is away from the story props; the largest patch is on the house walls at 0.63 across, 0.16 down (marked). The warm lights lighting it most: none found. Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
3. **rule 5: nothing in the story group as bright as no-2 gate.** the brightest parts of jacket and cap reach 0.29, as bright as no-2 gate (0.18); the brightest parts of upturned crate reach 0.44, as bright as no-2 gate (0.18); the brightest parts of mug and wages reach 0.69, as bright as no-2 gate (0.18); the brightest parts of man 1 reach 0.29, as bright as no-2 gate (0.18); the brightest parts of man 2 reach 0.31, as bright as no-2 gate (0.18); the brightest parts of man 3 reach 0.33, as bright as no-2 gate (0.18); the brightest parts of man 4 reach 0.17, as bright as no-2 gate (0.18); the brightest parts of man 6 reach 0.19, as bright as no-2 gate (0.18).
   - Fix: Make jacket and cap darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make upturned crate darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make mug and wages darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make man 1 darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make man 2 darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make man 3 darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make man 4 darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make man 6 darker (its own colour) or move it further from the light on it (no-2-gateway-spill).
4. **rule 3: story props close together.** The story props fill a box 0.73 of the frame wide and 0.52 tall (limit 0.40 x 0.50). Its edges: man 2's left side (0.01 across), jacket and cap's right side (0.74), no-2 gate's top (0.29 down) and upturned crate's bottom (0.81).
   - Fix: Move jacket and cap about 1.21 m to the left; move no-2 gate about 0.12 m lower.
5. **rule 5: no-2 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on no-2 gate (need 40%) and 68% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-2 gate more.
6. **rule 5: no-2 gate is bright.** no-2 gate is 0.68 times as bright as the frame's average (need 1.8).
   - Fix: Light no-2 gate more, or darken what is around it.
7. **rule 4: overlap clearly or leave a clear gap.** man 4 and man 6 almost touch: 4 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.25 across, 0.60 down; man 4 is nearer the camera)
   - Fix: Move man 4 about 0.12 m to the right so it clearly overlaps man 6, or move man 4 about 0.09 m to the left to leave a clear gap.
8. **rule 8: nothing big where the eye enters.** no-2 gate fills 2.5% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move no-2 gate out of the bottom-left quarter.
9. **rule 5: keep the sky dim.** The top third's brightness, left to right: 0.20, 0.42, 0.28 (limit 0.36).
   - Fix: Darken the sky (or ask the painter for a darker sky).
10. **rule 4: overlap clearly or leave a clear gap.** man 1's edge runs right along no-2 gate's edge for 63 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.62 to 0.65 down, around 0.17 across; no-2 gate is nearer the camera)
   - Fix: Move man 1 about 0.07 m to the right so man 1 clearly passes behind no-2 gate, or move man 1 about 0.09 m to the left to leave a clear gap.
11. **rule 10: nothing on the quiet side outshines the subject.** A light in the right half (at 0.53 across, 0.34 down) is 0.69 bright, as bright as no-2 gate (0.20).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
12. **rule 8: nothing big where the eye enters.** man 1 fills 2.0% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 1 out of the bottom-left quarter.
13. **rule 10: the quiet side keeps the frame from tipping.** The right half (away from no-2 gate) holds 53% of the weight (aim for 40 to 48%).
   - Fix: The right half is too busy: dim or remove some of its detail.
14. **rule 4: overlap clearly or leave a clear gap.** man 6 and man 8 almost touch: 14 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.62 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.12 m to the right and about 1.18 m further from the camera (but man 7 stands there) so it clearly overlaps man 8, or move man 6 about 0.03 m to the left and about 0.24 m nearer to the camera to leave a clear gap.
15. **rule 4: overlap clearly or leave a clear gap.** man 5's edge runs right along man 4's edge for 38 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.58 to 0.59 down, around 0.24 across; man 4 is nearer the camera)
   - Fix: Move man 5 about 0.10 m to the left so man 5 clearly passes behind man 4, or move man 5 about 0.12 m to the right to leave a clear gap.
16. **rule 6: lit from below.** The bottom of no-2 gate is 0.08 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give no-2 gate's bottom more warm light than its top: dim or whiten the light from above (dusk_skylight, no-2-gateway-spill); or add a warm light below it, aimed at its bottom edge. Then check again.
17. **rule 8: nothing big where the eye enters.** upturned crate fills 1.1% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move upturned crate out of the bottom-left quarter.
18. **rule 4: overlap clearly or leave a clear gap.** man 2's edge runs right along man 1's edge for 29 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.66 to 0.67 down, around 0.11 across; man 1 is nearer the camera)
   - Fix: Move man 2 about 0.08 m to the left so man 2 clearly passes behind man 1, or move man 2 about 0.09 m to the right to leave a clear gap.
19. **rule 12: titles in dim sky.** Only 28% of the title area is sky (need 85%). (28% of the title area is sky; its brightness 0.33)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: upturned crate, crates, handcart, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- props rest where they should: mug and wages rests on upturned crate.
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gate is 0.006 of the frame width away (limit 0.03).
- rule 3: story props together in the street: upturned crate, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand in front of None and within 0.3 m of each other.
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (jacket and cap 0.74, upturned crate 0.58, mug and wages 0.58, man 1 0.18, man 2 0.14, man 3 0.17, man 4 0.25, man 5 0.33, man 6 0.32, man 7 0.38, man 8 0.41).
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.7% of the frame (limit 1%): brightness 0.14 against 0.44 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.58 across, 0.34 down; centre of the warm light 0.61 across, 0.33 down; centre of the story props 0.33 across, 0.60 down; centre of no-2 gate 0.31 across, 0.56 down. Together they span 0.30 of the frame wide and 0.27 tall (limit 0.40 x 0.50, holding no-2 gate).

## Notes

- rule 4: overlap clearly or leave a clear gap: man 1 overlaps man 4 by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.46 across, 0.89 down (20.2% of the frame; lit most by no-2-gateway-spill); at 0.66 across, 0.34 down (9.1% of the frame); at 0.93 across, 0.96 down (0.2% of the frame; lit most by no-2-doorway-spill). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
