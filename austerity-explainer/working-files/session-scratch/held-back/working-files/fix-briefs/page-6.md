# Confirmed review findings for page 6

- [should fix] at 151-156 s ('less and less was being made'): The only picture of falling output is a small girder pile in the bottom-right corner, inside the button zones. By 155.9 s it is a scrap, while the two big money stacks dominate the frame, so the visual says 'money → prices up' (the hook text carries the rest).
  Suggested fix: page-6.js: move the steel pile to centre-right (about x 600-850, y 1250-1450 on screen), level with the stacks, and start it bigger so it visibly shrinks.
  Evidence: p6-d/still-153.80.jpg and still-155.90.jpg

- [should fix] at about 144-156 s: The fallen loose notes land face-down, so the snow in front of the stacks shows flat tan paper shapes that read as smudges, not money.
  Suggested fix: page-6.js lines 215-216: land the notes face-up (fold -(Math.PI/2 - 0.02), with the tumble easing toward a negative fold) and check that dy clears the snow. Or simply hide the landed notes.
  Evidence: p6-d/still-148.40.jpg (tan shapes on the snow), critique/p6-floor-compare.jpg; page-6.js lines 213-216.

- [nice to have] at 131-133 s: The racing counter settles on a crisp, unlabelled number (20,762) that she never says.
  Suggested fix: Show MARKS FOR ONE DOLLAR from the counter's first appearance, or blur the digits while they race.
  Evidence: p6-d/still-131.60.jpg

- (nice to have) LESS AND LESS MADE sits over the winding tower: move the hook block up about 100 px. (nice to have) The racing counter at 131-133 s settles on crisp unlabelled numbers (e.g. 20,762) she never says: keep the digits rolling (never resting on a number) or show a caption such as PRICES RACING right on the counter.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
