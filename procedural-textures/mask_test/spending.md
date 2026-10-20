# Spending ledger - generated mask stamps test (hard limit US$1.00 for this whole test)

What this file is: every paid picture-generation call of this test, written BEFORE the call (the price lookup) and updated AFTER it.
Rule I follow: stop before the running total could pass US$1.00. I count each picture at the price rounded UP to a whole megapixel
(the price list says the price is per megapixel; a 1536 x 1536 picture is 2.36 megapixels, so I count 3 megapixels = US$0.075 as the safe upper figure),
and I also write the exact figure.

Price list looked up on 20 October 2026 with the Fal price tool (get_pricing), per megapixel (one megapixel = one million dots):
| model | price |
|---|---|
| fal-ai/flux/schnell | US$0.003 per megapixel |
| fal-ai/z-image/turbo | US$0.005 per megapixel |
| fal-ai/qwen-image | US$0.020 per megapixel |
| fal-ai/flux/dev | US$0.025 per megapixel |
| fal-ai/flux-pro/v1.1 | US$0.040 per megapixel |
| fal-ai/nano-banana | US$0.0398 per picture |
| fal-ai/recraft/v3/text-to-image | US$0.040 per picture |

The prices were looked up once, before the first paid call (the price tool caches for 5 minutes; the same model was used for all six calls and I checked the exact megapixel price again with the cost estimate tool: 2.359296 megapixels = US$0.0590).

Chosen: fal-ai/flux/dev (good at following a "sheet of separate shapes" wording, cheap). 1536 x 1536 = 2.359 megapixels = US$0.059 exact, US$0.075 safe upper figure.

## Calls (one row per paid call)
| # | model | what for | size | exact price | safe upper figure | running total (safe upper) |
|---|---|---|---|---|---|---|
| 1 | fal-ai/flux/dev | moss clump sheet A (seed 4101): 16 round fuzzy clumps, green on black | 1536 x 1536 | 0.059 | 0.075 | 0.075 |
| 2 | fal-ai/flux/dev | chip sheet A (seed 4102): 16 chunky cream flakes with ragged edges and pitted rims, on black | 1536 x 1536 | 0.059 | 0.075 | 0.150 |
| 3 | fal-ai/flux/dev | moss sheet B (seed 4103): 16 ink-splat style olive blots with drips, on a CREAM background (not black) | 1536 x 1536 | 0.059 | 0.075 | 0.225 |
| 4 | fal-ai/flux/dev | chips sheet B (seed 4104): asked for thin strips, got 16 squarish cream paper pieces (poor fit for chips) | 1536 x 1536 | 0.059 | 0.075 | 0.300 |
| 5 | fal-ai/flux/dev | chips sheet C (seed 4105): five long ragged cream strips of flaking paint on black (to be cut into short pieces) | 1536 x 1536 | 0.059 | 0.075 | 0.375 |
| 6 | fal-ai/flux/dev | moss sheet C (seed 4106): 16 hanging moss "curtains" with drips (a brown rod and a red scribble came with them; removed by colour) | 1536 x 1536 | 0.059 | 0.075 | 0.450 |

## Total (after the 6th and last picture)
Exact: 6 x US$0.059 = US$0.354 (price list: US$0.025 per megapixel; each picture is 2.359 megapixels). Safe upper figure (each picture counted as 3 megapixels): US$0.450.
Limit US$1.00. No further paid calls were made. Total spent is therefore at most US$0.45 (more likely US$0.35). I did not read the real account balance (no tool for it was used);
the figure above comes from the price list.
