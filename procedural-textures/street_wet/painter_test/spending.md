<!-- NOTE (plain words): the money ledger for the wet street painter test. Every paid call is written here BEFORE it is made (what and the worst-case price) and AFTER (what came back). Hard limit for the whole job: US$0.30. The person approved ONE repaint (about 10 US cents when they said yes). -->
# Spending ledger - wet street painter test

Limit: US$0.30 in total. Approved: ONE repaint. A second call only if the first fails for a technical reason (error, timeout, empty or broken picture), never for a nicer picture.

## Price looked up (20 October 2026)
* Model: blackforestlabs/flux-3/edit-image (Flux 3 edit on fal). Price list: US$0.048 per megapixel (4.8 US cents), looked up with fal's price tool (get_pricing). fal's estimate tool gave no total ("quantity unavailable"), so the totals below are my own sums of price x megapixels.
* **The price is twice what the plan said** (the project's own lesson 139: 2.4 cents a megapixel then, 4.8 now). So "about 10 US cents" is no longer what a 2k repaint costs.
* A 2k picture is about 4.0 megapixels (earlier outputs were 1504 x 2672 = 4.02 MP).
  * If only the returned picture is charged: 4.02 MP x 0.048 = **US$0.193**.
  * If the pictures sent are charged too (the project's own log 32 and 34 assumed so; fal does not show the exact charge, so I cannot tell): output plus both inputs. Sent at their old sizes (1536x2730 plate, about 4 MP after fal's own shrink to 4 MP; style 768x1368 = 1.05 MP) that would be 9.07 MP = US$0.435, **over the limit**.
* What I did about it: sent the pictures SMALL (plate 810x1440 = 1.166 MP, style 504x896 = 0.452 MP; total 1.618 MP) and kept the old output setting (2k, png). Worst case, if every sent megapixel is charged and the output is as large as 4.2 MP: (4.2 + 1.618) x 0.048 = **US$0.279**, under the limit. Best case (output only): **US$0.193**.
* Not covered: if fal rounds each picture UP to a whole megapixel, the worst case would be higher (output 5 MP + 2 + 1 = 8 MP = US$0.384). I judged that unlikely, could not rule it out, and could not check the real charge (the fal tools show no balance or bill). If the first call fails for a technical reason, the second call is only made if (worst case of the first, unknown) + (the second) still stays below US$0.30, otherwise I stop and say so.

## Calls
| # | when (UTC) | what | settings | worst-case price | best-case price | request id | running total (worst / best) |
|---|---|---|---|---|---|---|---|
| 0 | 2026-10-20 | price look-ups, history look-up, uploads of the two pictures | free | 0 | 0 | - | 0.000 / 0.000 |
| 1 | 2026-10-20 19:02 | the ONE repaint of the wet plate (image 1 = wet plate shrunk to 810x1440, image 2 = style picture shrunk to 504x896; new wet brief, briefs/brief_new_wet.txt) | resolution 2k, aspect_ratio auto, output_format png, safety_tolerance 2, prompt expansion off (same as the earlier paintings) | US$0.277 (returned 1520x2704 = 4.11 MP; plus both pictures sent, 1.618 MP, if they are charged) | US$0.197 (returned picture only) | 01a15ab1-7875-7200-b5e1-fb73c814521c (finished first time, no error) | **0.277 / 0.197** |

## Result
* One call, finished first time: no technical failure, so NO second call was allowed or made. **Calls made: 1.**
* **Spent: between US$0.197 and US$0.277** (fal does not show the exact charge; I cannot tell which). Limit US$0.30: not exceeded in either case (unless fal rounds every picture up to a whole megapixel, which I could not check; then it could have been up to about US$0.38 - see the note above).
* Compared with what the person approved ("about 10 US cents"): it cost about twice that or more, because the painter's price doubled since the plan (lesson 139) and the pictures are 4 megapixels. I stayed under the hard limit as instructed, but the person should know the real figure.
* Nothing else in this job costs money (Blender and the stage run on this machine).
