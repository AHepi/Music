# Shot check: w2-slowed-light

14 problems found in 29 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 3: story props together in the street). Move hand truck about 0.42 m right (across the street) and 2.90 m down the street, toward petrol drum.

## Problems

1. **rule 3: story props together in the street.** hand truck stands 3.04 m from the nearest other story prop (petrol drum) in the street: the group should stand together.
   - Fix: Move hand truck about 0.42 m right (across the street) and 2.90 m down the street, toward petrol drum.
2. **rule 5: nothing in the story group as bright as no-2 gateway.** the brightest parts of petrol drum reach 0.26, as bright as no-2 gateway (0.14); the brightest parts of diesel drum reach 0.35, as bright as no-2 gateway (0.14); the brightest parts of man 1 reach 0.47, as bright as no-2 gateway (0.14); the brightest parts of man 2 reach 0.50, as bright as no-2 gateway (0.14); the brightest parts of man 3 reach 0.39, as bright as no-2 gateway (0.14); the brightest parts of man 4 reach 0.31, as bright as no-2 gateway (0.14).
   - Fix: Make petrol drum darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make diesel drum darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 1 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 2 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 3 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 4 darker (its own colour) or move it further from the light on it (no-2-gateway-beam).
3. **rule 6: lit from below.** The bottom of no-2 gateway is -0.11 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give no-2 gateway's bottom more warm light than its top: add a warm light below it, aimed at its bottom edge; or dim or whiten the light from above (dusk_skylight, no-2-gate-lamp-light). Then check again.
4. **rule 3: story props close together.** The story props (leaving out no-2 board) fill a box 0.52 of the frame wide and 0.34 tall (limit 0.40 x 0.50). Its edges: man 8's left side (0.21 across), petrol drum's right side (0.74), no-2 gateway's top (0.43 down) and man 8's bottom (0.77).
   - Fix: Move man 8 about 0.51 m to the right.
5. **rule 5: no-2 gateway is bright.** no-2 gateway is 0.89 times as bright as the frame's average (need 1.8).
   - Fix: Light no-2 gateway more, or darken what is around it.
6. **rule 3: one touching group.** Standing apart from the others: petrol drum.
   - Fix: Move petrol drum about 0.33 m to the left so it overlaps hand truck.
7. **rule 5: no-2 gateway is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 20% lie on no-2 gateway (need 40%) and 51% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-2 gateway more.
8. **rule 4: overlap clearly or leave a clear gap.** no-2 gateway's edge runs right along petrol drum's edge for 96 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.58 to 0.61 down, around 0.65 across; petrol drum is nearer the camera)
   - Fix: The move in problem 6 (bringing petrol drum into the group) fixes this too, if it ends in a clear overlap; check again after it.
9. **rule 8: nothing big where the eye enters.** man 8 fills 2.1% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 8 out of the bottom-left quarter.
10. **rule 10: nothing on the quiet side outshines the subject.** A light in the left half (at 0.46 across, 0.42 down) is 0.81 bright, as bright as no-2 gateway (0.19).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
11. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 4's edge for 38 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.62 to 0.64 down, around 0.42 across; man 4 is nearer the camera)
   - Fix: Move man 3 about 0.11 m to the left so man 3 clearly passes behind man 4, or move man 3 about 0.13 m to the right to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** man 6's edge runs right along man 7's edge for 32 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.54 to 0.55 down, around 0.33 across; man 7 is nearer the camera)
   - Fix: Move man 6 about 0.08 m to the right so man 6 clearly passes behind man 7, or move man 6 about 0.10 m to the left to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** man 4's edge runs right along man 5's edge for 29 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.52 to 0.53 down, around 0.38 across; man 5 is nearer the camera)
   - Fix: Move man 4 about 0.10 m to the right so man 4 clearly passes behind man 5, or move man 4 about 0.12 m to the left to leave a clear gap.
14. **rule 12: titles in dim sky.** Only 49% of the title area is sky (need 85%). (49% of the title area is sky; its brightness 0.23)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, hand truck, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gateway is 0.019 of the frame width away (limit 0.03).
- rule 3: nothing hides the words: 0% of no-2 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of petrol drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of diesel drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (petrol drum 0.74, diesel drum 0.62, hand truck 0.63, man 1 0.50, man 2 0.46, man 3 0.45, man 4 0.43, man 5 0.42, man 6 0.39, man 7 0.38, man 8 0.34, no-2 board 0.57).
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.4% of the frame (limit 1%): brightness 0.11 against 0.25 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.20, 0.25, 0.17 (limit 0.36).
- rule 6: warm light from the people's own lights: Warm light covers 2.9% of the frame, 65% of it round the story props.
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- rule 10: the quiet side keeps the frame from tipping: The left half (away from no-2 gateway) holds 47% of the weight (aim for 40 to 48%).
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.48 across, 0.44 down; centre of the warm light 0.47 across, 0.43 down; centre of the story props 0.43 across, 0.59 down; centre of no-2 gateway 0.53 across, 0.53 down. Together they span 0.11 of the frame wide and 0.17 tall (limit 0.40 x 0.50, holding no-2 gateway).

## Notes

- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.15 across, 0.71 down (1.4% of the frame; lit most by no-2-gateway-beam); at 0.51 across, 0.67 down (0.5% of the frame; lit most by no-2-gateway-beam); at 0.60 across, 0.33 down (0.4% of the frame). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
