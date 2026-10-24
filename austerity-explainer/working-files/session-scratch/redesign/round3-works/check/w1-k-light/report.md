# Shot check: w1 (light rules)

20 problems found in 33 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (props rest where they should). Move brazier off man 2 and place it again from just above the pavement.

## Problems

1. **props rest where they should.** brazier rests on man 2, not on the ground (at Blender x -4.88, y 21.52).
   - Fix: Move brazier off man 2 and place it again from just above the pavement.
2. **props rest where they should.** man 2 rests on brazier, not on the ground (at Blender x -4.64, y 21.27).
   - Fix: Move man 2 off brazier and place it again from just above the pavement.
3. **rule 5: nothing in the story group as bright as no-1 gate.** the brightest parts of brazier reach 0.81, as bright as no-1 gate (0.09); the brightest parts of diesel drum reach 0.29, as bright as no-1 gate (0.09); the brightest parts of man 1 reach 0.26, as bright as no-1 gate (0.09); the brightest parts of man 2 reach 0.28, as bright as no-1 gate (0.09); the brightest parts of man 3 reach 0.28, as bright as no-1 gate (0.09); the brightest parts of man 4 reach 0.16, as bright as no-1 gate (0.09); the brightest parts of man 5 reach 0.16, as bright as no-1 gate (0.09); the brightest parts of man 6 reach 0.12, as bright as no-1 gate (0.09); the brightest parts of man 7 reach 0.11, as bright as no-1 gate (0.09).
   - Fix: Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Make diesel drum darker (its own colour) or move it further from the light on it (lantern_light). Make man 1 darker (its own colour) or move it further from the light on it (brazier_light). Make man 2 darker (its own colour) or move it further from the light on it (brazier_light). Make man 3 darker (its own colour) or move it further from the light on it (brazier_light). Make man 4 darker (its own colour) or move it further from the light on it (brazier_light). Make man 5 darker (its own colour) or move it further from the light on it (brazier_light). Make man 6 darker (its own colour) or move it further from the light on it (brazier_light). Make man 7 darker (its own colour) or move it further from the light on it (no-2-doorway-spill).
4. **rule 6: lit from below.** The bottom of no-1 gate is -0.10 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give no-1 gate's bottom more warm light than its top: bring the warm light below it closer under its bottom edge, or aim it there (lantern_light); or dim or whiten the light from above (dusk_skylight, no-1-gate-lamp-light, brazier_light). Then check again.
5. **rule 5: no-1 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on no-1 gate (need 40%) and 44% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-1 gate more.
6. **rule 5: no-1 gate is bright.** no-1 gate is 0.70 times as bright as the frame's average (need 1.8).
   - Fix: Light no-1 gate more, or darken what is around it.
7. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.49 of the frame wide and 0.30 tall (limit 0.40 x 0.50). Its edges: lantern's left side (0.28 across), man 7's right side (0.78), no-1 gate's top (0.42 down) and man 7's bottom (0.72).
   - Fix: Move lantern about 0.68 m to the right.
8. **rule 5: no burnt-out colour.** Colour at its limit (pure white, or one colour at full strength), where all detail is lost: brazier (6% of it).
   - Fix: Dim the light on it, or darken its own colour or glow, until nothing but a lamp's flame reaches the limit.
9. **rule 4: overlap clearly or leave a clear gap.** diesel drum and lunch tin almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.28 across, 0.56 down; diesel drum is nearer the camera)
   - Fix: Move diesel drum about 1.97 m further from the camera so it clearly overlaps lunch tin, or move diesel drum about 1.50 m nearer to the camera to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps lunch tin: it reaches 7 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.07 m higher so it clearly overlaps lunch tin, or move lantern about 0.18 m lower to leave a clear gap.
11. **rule 10: nothing on the quiet side outshines the subject.** A light in the left half (at 0.36 across, 0.52 down) is 0.72 bright, as bright as no-1 gate (0.10).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
12. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps diesel drum: it reaches 8 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.06 m lower so it clearly overlaps diesel drum, or move lantern about 0.18 m higher to leave a clear gap.
13. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from no-1 gate) holds 52% of the weight (aim for 40 to 48%).
   - Fix: The left half is too busy: dim or remove some of its detail.
14. **rule 4: overlap clearly or leave a clear gap.** man 3 and man 6 almost touch: 14 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.57 across, 0.64 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.15 m to the left so it clearly overlaps man 3, or move man 6 about 0.03 m to the right to leave a clear gap.
15. **rule 4: overlap clearly or leave a clear gap.** man 2's edge runs right along man 3's edge for 37 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.57 to 0.59 down, around 0.47 across; man 3 is nearer the camera)
   - Fix: Move man 2 about 0.12 m to the right so man 2 clearly passes behind man 3, or move man 2 about 0.14 m to the left to leave a clear gap.
16. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 4's edge for 37 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.62 to 0.63 down, around 0.53 across; man 4 is nearer the camera)
   - Fix: Move man 3 about 0.11 m to the right so man 3 clearly passes behind man 4, or move man 3 about 0.13 m to the left to leave a clear gap.
17. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps petrol drum: it reaches 13 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.03 m lower so it clearly overlaps petrol drum, or move lantern about 0.22 m higher to leave a clear gap.
18. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 1.2% of the frame (limit 1%): brightness 0.09 against 0.17 for the lit ground around it. It is not a prop: probably a shadow cast across the ground. (from 0.00 to 0.09 across, 0.65 to 0.95 down)
   - Fix: First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.
19. **rule 4: overlap clearly or leave a clear gap.** brazier and petrol drum almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.56 down; petrol drum is nearer the camera)
   - Fix: Move petrol drum about 0.24 m to the right so it clearly overlaps brazier, or move petrol drum about 0.03 m to the left to leave a clear gap.
20. **rule 12: titles in dim sky.** Only 39% of the title area is sky (need 85%). (39% of the title area is sky; its brightness 0.21)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, man 1, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.004 of the frame width away (limit 0.03).
- rule 3: story props together in the street: brazier, diesel drum, man 1, man 2, man 3, man 4, man 5, man 6, man 7 stand in front of None and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.43, lantern 0.30, diesel drum 0.33, man 1 0.59, man 2 0.47, man 3 0.54, man 4 0.61, man 5 0.67, man 6 0.68, man 7 0.77, no-1 board 0.67).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.19, 0.17, 0.19 (limit 0.36).
- rule 6: warm light from the people's own lights: Warm light covers 1.8% of the frame, 64% of it round the story props.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.38 across, 0.33 down; centre of the warm light 0.30 across, 0.41 down; centre of the story props 0.57 across, 0.59 down; centre of no-1 gate 0.59 across, 0.48 down. Together they span 0.29 of the frame wide and 0.26 tall (limit 0.40 x 0.50, holding no-1 gate).

## Notes

- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.34 across, 0.50 down (1.1% of the frame; lit most by no-2-doorway-spill); at 0.14 across, 0.06 down (1.0% of the frame); at 0.38 across, 0.65 down (0.4% of the frame; lit most by brazier_light). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
