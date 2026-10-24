# Confirmed review findings for page 3

- [must fix] at 47-74 s (page 3); 181 s (page 8): The price counter, which carries the whole 'prices barely move vs prices climb' contrast, is cut off by the right edge of the frame in most factory close-ups ('£1.0' at 48.6 s, only '£' at 52.4 s, '£1' at 57.3 s, '£1.0' at 62.3 s, '£2.0' at 72.9 s). It sits in the right phone-button zone. At 72.9-74.2 s the WORKERS label is also clipped at the left edge and MACHINES runs into the right zone.
  Suggested fix: Smallest change: in page-3.js's shot list, move the factory close-up camera targets about 0.4-0.6 units to the right (+x), and ease the last shot back about 10% so WORKERS/MATERIALS/MACHINES fit between x 140 and 940. Don't move boardAt in two-factories-set.js: that set is shared with page 8. If you do move it, check page 8 too.
  Evidence: critique/p3sheet-0.jpg and p3sheet-10.jpg, frames pulled from the filmed chunks (48.6, 52.4, 53.8, 57.3, 62.3, 72.9 s).

- [must fix] at 52.4-54.2 s, 59-67.5 s: The page-3 callouts are thin light-grey text with nothing behind them, drawn over the ivory walls and grey roofs. MORE SHELLS at 53.8 s is invisible (only its leader line shows), NO MORE SHELLS at 63.8 s and PRICES CLIMB at 67.4 s are faint, and FLAT OUT is weak. These words are the on-screen summary of the central contrast.
  Suggested fix: page-3.js draw2D lines ~141-146: give these callouts a dark backing (the dark wash or pill used on page 1, or a strong text shadow) and set size to about 52. Point NO MORE SHELLS at b.shellAt(6) or shellAt(7), which stay in frame.
  Evidence: p3sheet-0.jpg at 53.8 s (MORE SHELLS missing), p3sheet-10.jpg at 63.8 s and 67.4 s; page-3.js lines 141-146.

- [should fix] at 7.4-10.3 s; 55.3 s; 67.4 s: The callout leader lines end in the middle of the price digits, so they read like strike-throughs: through $100.00 and $104.10 on page 1, through £1.00 at 55.3 s and £1.60 at 67.4 s on page 3.
  Suggested fix: Aim the callouts at the tag or board's top rim instead of its centre: on page 1 a point on the tag's upper edge; on page 3 boardAt with setY at about 1.17 plus the board's half-height.
  Evidence: critique/c-8.00.jpg, c-9.73.jpg; p3sheet-0.jpg at 55.3 s; p3sheet-10.jpg at 67.4 s.

- [should fix] at 70.9-74.5 s: BRITAIN AT WAR fades at 70.7 s, then WORKERS / MATERIALS / MACHINES appear with their props, but nothing says they are in short supply, so it reads as an inventory.
  Suggested fix: page-3.js draw2D: add hook(ctx, t, { at: T.short, until: T.end + 1.2, text: 'SHORT OF', y: 330, size: 80 }).
  Evidence: p3sheet-10.jpg at 71.6 and 72.9 s; page-3.js line ~147.

- [should fix] at 43-74 s: The £1.00 → £2.00 shell prices carry no 'Example prices' label, unlike page 1. In a 1915 setting, with page 2's real ×2 just before, they can pass for historical figures.
  Suggested fix: page-3.js draw2D: add credit(ctx, t, { at: T.first, until: T.britain, text: 'Example prices', y: 1460, size: 28 }).
  Evidence: page-3.js lines 139-148 (no credit call); p3sheet-10.jpg.

- [should fix] at 63.8 s, 67.4 s (and the backdrop seam at 43-46 s): Black void shows in the top-left corner past the painted skyline on the close shots, and the skyline's hard bottom edge is visible. It reads as a rendering fault.
  Suggested fix: two-factories-set.js: raise backdrop.scale from 1.65 to about 2.0 (or lower it slightly) and check that page 8's wide shots still look right.
  Evidence: p3sheet-10.jpg at 63.8 and 67.4 s (black block top left); p3sheet-0.jpg at 43.0 s.
- NOTE: you own `two-factories-set.js` for this round (page 8 uses the same set; its helper will not edit it). If you change the set (e.g. backdrop scale about 2.0 to remove the black corners, or the board position), draw 2 stills of page 8 (at 181.3 and 187.3 s) to check its wide shots still look right, and say what you changed.
- NEW SHARED OPTION: callout(..., { plate: true }) now draws a dark rounded plate behind the label text (graphics.js). Use it for MORE SHELLS / NO MORE SHELLS / PRICES CLIMB / IDLE / FLAT OUT / BARELY MOVE, with size about 52.
