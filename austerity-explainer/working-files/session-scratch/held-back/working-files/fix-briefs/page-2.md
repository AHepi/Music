# Confirmed review findings for page 2

- [should fix] at 23.4-29.4 s: The heading OUT OF WORK sits directly over 99 bright amber dots. The one dot that means 'out of work' is a faint ring in the corner with no label, so at a glance the lit block reads as the unemployed, which is backwards. The UNDER 1% below and the narration partly rescue it.
  Suggested fix: page-2.js line 156: change the heading text to '100 WORKERS', and add a small callout 'OUT OF WORK' pointing at the last dot (x 342+9*44, y 360+9*44) from T.under.
  Evidence: critique/a-024.50.jpg and a-027.60.jpg; page-2.js lines 147 and 156.

- [nice to have] at 30.2-33 s: The paper boats are already on screen under NEW MONEY and then 'sink' into the dry floor.
  Suggested fix: page-2.js: pop the boats up at T.submarines and fade them rather than lowering them through the floor.
  Evidence: p2b/still-30.50.jpg and still-32.40.jpg

- (nice to have) The paper boats 'sink' into a dry concrete floor: optional - fade them out as they tip rather than lowering them through the floor.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
