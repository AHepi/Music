# Confirmed review findings for page 7

- [should fix] at 170.35-171.2 s, and 168-171 s: COSTS, the lesson of test three, is on screen for under a second (from 170.35 s until cut - 0.2 = 171.19 s). Also, without her 'sometimes', NOT SPENDING → COSTS reads as a general rule, which pages 6 and 8 contradict.
  Suggested fix: page-7.js lines ~247-248: change until: cut - 0.2 to until: cut + 0.1 for both, so the words fade with the dip. Add a small muted 'SOMETIMES' (size about 48, y about 220) at T.sometimes.
  Evidence: page-7.js lines 57 and 247-248; word times: sometimes 168.07, costs 170.35, And 171.34; critique/p7/still-170.70.jpg.

- [should fix] at 161.0-161.4 s: The oil counter's starting price, $2.90, never reads. It is scheduled at 161.01 s while the counter is still springing up, and the count starts at 161.04 s. By 161.40 s it already shows $4.27, so '×4' has no visible 'before'.
  Suggested fix: page-7.js lines 79-81: bring the counter up at T.oil + 0.05 and start the countSchedule at T.quadruples, so $2.90 holds for about 1 s.
  Evidence: page-7.js lines 79-81; word times oil 160.67, nearly 160.99, quadruples 161.35; p7-c/still-161.40.jpg shows $4.27.

- (nice to have) A BARREL is printed over the red barrel: move it just below the counter so it reads.
- NEW SHARED OPTION: callout(..., { plate: true }) draws a dark rounded plate behind a label's text, for labels over pale or busy areas.
