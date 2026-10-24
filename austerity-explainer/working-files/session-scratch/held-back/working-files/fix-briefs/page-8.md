# Confirmed review findings for page 8

- [must fix] at 47-74 s (page 3); 181 s (page 8): The price counter, which carries the whole 'prices barely move vs prices climb' contrast, is cut off by the right edge of the frame in most factory close-ups ('£1.0' at 48.6 s, only '£' at 52.4 s, '£1' at 57.3 s, '£1.0' at 62.3 s, '£2.0' at 72.9 s). It sits in the right phone-button zone. At 72.9-74.2 s the WORKERS label is also clipped at the left edge and MACHINES runs into the right zone.
  Suggested fix: Smallest change: in page-3.js's shot list, move the factory close-up camera targets about 0.4-0.6 units to the right (+x), and ease the last shot back about 10% so WORKERS/MATERIALS/MACHINES fit between x 140 and 940. Don't move boardAt in two-factories-set.js: that set is shared with page 8. If you do move it, check page 8 too.
  Evidence: critique/p3sheet-0.jpg and p3sheet-10.jpg, frames pulled from the filmed chunks (48.6, 52.4, 53.8, 57.3, 62.3, 72.9 s).

- [should fix] at 193.2-195 s: The caption 'LOWEST SINCE 1986' can be read as if 1986 was lower. In fact 1986 is when the survey began, and she says 'since records began'. The ledger's approved wording is LOWEST ON RECORD.
  Suggested fix: page-8.js line 279: set the caption to 'Lowest on record' (or 'Lowest since records began').
  Evidence: p8-r/still-193.80.jpg; page-8.js line 279; ledger row 280.

- [should fix] at 195.3-198.6 s: The +30% house stands on a large flat, untextured grey-cream block with no shadow. It looks like a rendering fault, not 'prices rising'.
  Suggested fix: page-8.js lines ~120-129 and 235-243: remove the plinth, or give it the paper material plus a contact shadow. Drop the duplicate '+30%' tag.
  Evidence: p8-d/still-197.90.jpg

- (nice to have) The table seam shows at about 181 s: tilt the camera down slightly. Add a small credit line for the figures (e.g. 'Stats NZ; REINZ' at the 2021 beat, and 'Independent review, September 2026' already there).
- DECISION (from the lead) on the caption: show 'LOWEST ON RECORD' under 3.2%, and add a small separate line under it, 'Records began in 1986' (muted, about size 30), so it is both accurate and not misread.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
