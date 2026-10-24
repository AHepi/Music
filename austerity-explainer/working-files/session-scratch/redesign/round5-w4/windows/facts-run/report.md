# Shot check: facts-run

2 problems found in 6 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (rule 1: aim the street at the story). Turning the camera won't help: it moves where the lines meet and the props together. Raise the camera about 4.53 m (no-2 windows 2 then drops on screen while where the lines meet stays put), or move no-2 windows 2 about 4.53 m lower; and move the camera about 0.55 m to the left, or move no-2 windows 2 about 0.55 m to the right.

## Problems

1. **rule 1: aim the street at the story.** The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 windows 2 is 0.222 of the frame width away (limit 0.03): 29 pixels to the left and 238 pixels above. (no-2 windows 2 spans 0.40 to 0.67 across, 0.30 to 0.38 down)
   - Fix: Turning the camera won't help: it moves where the lines meet and the props together. Raise the camera about 4.53 m (no-2 windows 2 then drops on screen while where the lines meet stays put), or move no-2 windows 2 about 4.53 m lower; and move the camera about 0.55 m to the left, or move no-2 windows 2 about 0.55 m to the right.
2. **rule 8: nothing big where the eye enters.** man 5 fills 1.0% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 5 out of the bottom-left quarter.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- rule 4: overlap clearly or leave a clear gap: No two of no-2 windows 2 just touch (overlaps at least 15 pixels deep, gaps at least 18).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are ().

## Notes

- rule 12: titles in dim sky: Not checked: the check file has no "title_zone".

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
