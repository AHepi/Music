# 55 Store helper for the street ground tools - what it reported

What this file is: what the helper that made the street's ground tools for the store said it made (5 November 2026). Its report reached the session but was not saved word for word before the session's notes were shortened, so this is written from those notes and checked against the files it left.

## What it made

- **lay_kerb** (new tool, `store/tools/lay_kerb.py`): hand-dressed kerbstones along a line or curve you give, the line being the kerb's top edge on the road side. Each stone its own length and shade, tipped and settled a little, gaps at the joints, worn round edges, chips knocked off the road-side edge where cart wheels hit. A row of dished channel (gutter) stones along the kerb's foot as an option. Call: `lay_kerb.lay(line, road='left', height=0.13, channel=0.3, seed=1)`; it gives back the kerb and the channel.
- **joint_weeds** (new tool, `store/tools/joint_weeds.py`): sparse tufts of grass and small flat weeds growing out of the joints of the setts or flags that lay_cobbles laid, inside an area you give, never in the wheel lines you give. Call: `joint_weeds.grow(setts, area, wheel_lines, amount=1.0, seed=4)`.
- **lay_cobbles, new options, all off unless asked**: each sett its own shade (`shades`), setts from two quarries (`quarries`), rocked setts sunk and tipped (`rocked`, `rocked_area`), missing setts with water standing in the holes (`holes`, `hole_water`), a relaid patch of paler new setts with shiny pitch in the joints (`patch`), grit packed in the joints (`grit`) and moss in them (`moss`). With none of these the tool lays exactly what it laid before: the test holds a fingerprint of the old setts and flags and compares.
- **Test**: `tests/test_store_street_ground.py` (9 PASS lines when the session saw it).
- **Cards**: `cards/tools/lay_kerb.png`, `joint_weeds.png`, and `lay_cobbles.png` redrawn to show the new options.

## Traps

- This is not the helper's own wording. The session checked the tools by running the store's tests (project story, log 55), not by rereading the lost report.
