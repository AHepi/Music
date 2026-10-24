# Confirmed review findings for page 1

- [should fix] at 7.4-10.3 s; 55.3 s; 67.4 s: The callout leader lines end in the middle of the price digits, so they read like strike-throughs: through $100.00 and $104.10 on page 1, through £1.00 at 55.3 s and £1.60 at 67.4 s on page 3.
  Suggested fix: Aim the callouts at the tag or board's top rim instead of its centre: on page 1 a point on the tag's upper edge; on page 3 boardAt with setY at about 1.17 plus the board's half-height.
  Evidence: critique/c-8.00.jpg, c-9.73.jpg; p3sheet-0.jpg at 55.3 s; p3sheet-10.jpg at 67.4 s.

- [nice to have] at 15.7-17.6 s: THE WHOLE BASKET spans to about x 1010, into the right button zone, and the shelf tags at the right edge are cut.
  Suggested fix: page-1.js: hook size 92 → 78; move the shelf spots at u > 0.86 inward.
  Evidence: p1-c/still-16.00.jpg

- (nice to have) THE WHOLE BASKET runs into the right button zone: hook size 92 -> about 78; move the shelf tag spots with u > 0.86 inward so none is cut at the right edge.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
